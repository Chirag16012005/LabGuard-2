from __future__ import annotations

import io
import logging
import os
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from ..repositories.document_repository import DocumentRepository
from ..storage.docx_parser import (
    DocumentParser,
    FileParseError,
    UnsupportedFileTypeError,
    CorruptedFileError,
    EmptyFileError,
    get_parser,
)

logger = logging.getLogger(__name__)


class DocumentManagementService:
    """Document upload, retrieval, and management service."""

    def __init__(self) -> None:
        self.doc_repo = DocumentRepository()
        self.parser = get_parser()

    @staticmethod
    def _get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
        from ..db.mongodb import get_database

        return AsyncIOMotorGridFSBucket(get_database(), bucket_name="documents")

    async def upload_document(
        self,
        filename: str,
        content_type: str,
        file_content: bytes,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Upload and store a document.

        Supports: PDF, DOCX, DOC, TXT

        Args:
            filename: Original filename with extension
            content_type: MIME type of the file
            file_content: Raw file bytes
            owner_id: Optional ID of the document owner

        Returns:
            Document metadata dict with id, filename, content_type, size_bytes, file_id

        Raises:
            ValueError: If file cannot be parsed or is unsupported
        """
        if not file_content:
            raise ValueError("File content is empty")

        size_bytes = len(file_content)
        safe_filename = os.path.basename(filename)

        bucket = self._get_gridfs_bucket()
        try:
            file_id = await bucket.upload_from_stream(
                safe_filename,
                io.BytesIO(file_content),
                metadata={
                    "filename": safe_filename,
                    "content_type": content_type,
                    "owner_id": owner_id,
                },
            )
            logger.info("Stored document %s in GridFS", safe_filename)
        except Exception as e:
            logger.error("Failed to store document bytes for %s: %s", safe_filename, e)
            raise ValueError(f"Failed to store file: {str(e)}") from e

        # Save metadata to database
        doc_metadata = await self.doc_repo.create_document(
            filename=safe_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            owner_id=owner_id,
            file_id=str(file_id),
            storage_path=None,
        )

        logger.info(
            "Document uploaded: %s (id=%s, size=%d bytes, file_id=%s)",
            safe_filename,
            doc_metadata["id"],
            size_bytes,
            file_id,
        )

        return doc_metadata

    async def get_document(self, document_id: str) -> Optional[dict]:
        """Get document metadata."""
        return await self.doc_repo.get_document_by_id(document_id)

    async def get_document_content(self, document_id: str) -> Optional[str]:
        """Load a document from GridFS and extract text on demand."""
        metadata = await self.get_document(document_id)
        if not metadata:
            return None

        file_bytes = await self.get_document_binary_content(document_id)
        if not file_bytes:
            return None

        try:
            return self.parser.parse(file_bytes, metadata.get("filename", "document"))
        except (
            UnsupportedFileTypeError,
            CorruptedFileError,
            EmptyFileError,
            FileParseError,
        ) as e:
            logger.error("Failed to extract text for document %s: %s", document_id, e)
            raise

    async def get_document_binary_content(self, document_id: str) -> Optional[bytes]:
        """Get original document bytes from GridFS for download."""
        metadata = await self.get_document(document_id)
        if not metadata:
            return None

        file_id = metadata.get("file_id")
        if file_id:
            try:
                bucket = self._get_gridfs_bucket()
                grid_out = await bucket.open_download_stream(ObjectId(str(file_id)))
                return await grid_out.read()
            except Exception as e:
                logger.warning(
                    "Failed to read document %s from GridFS: %s", document_id, e
                )

        storage_path = metadata.get("storage_path")
        if storage_path and os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                return f.read()

        return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        metadata = await self.get_document(document_id)
        if metadata:
            file_id = metadata.get("file_id")
            if file_id:
                try:
                    bucket = self._get_gridfs_bucket()
                    await bucket.delete(ObjectId(str(file_id)))
                except Exception as e:
                    logger.warning(
                        "Failed to delete GridFS file for document %s: %s",
                        document_id,
                        e,
                    )

            storage_path = metadata.get("storage_path")
            if storage_path and os.path.exists(storage_path):
                os.remove(storage_path)
        # Remove from database
        return await self.doc_repo.delete_document(document_id)

    async def list_user_documents(self, owner_id: str) -> list[dict]:
        """List all documents uploaded by a user."""
        return await self.doc_repo.list_user_documents(owner_id)
