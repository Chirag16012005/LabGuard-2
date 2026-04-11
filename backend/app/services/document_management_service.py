from __future__ import annotations

import logging
import os
from uuid import uuid4
from typing import Optional

from ..repositories.document_repository import DocumentRepository
from ..services.document_service import Document, InMemoryDocumentStore
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

    _shared_store = InMemoryDocumentStore()

    def __init__(self) -> None:
        self.doc_repo = DocumentRepository()
        # Keep one shared in-memory store so uploads from different service instances
        # can be downloaded through the documents endpoints.
        self.store = self._shared_store

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
            Document metadata dict with id, filename, content_type, size_bytes, storage_path

        Raises:
            ValueError: If file cannot be parsed or is unsupported
        """
        if not file_content:
            raise ValueError("File content is empty")

        size_bytes = len(file_content)
        safe_filename = os.path.basename(filename)
        storage_path = os.path.join(".storage", "documents", f"{uuid4()}_{safe_filename}")

        # Parse document content using production-grade parser
        try:
            parser = get_parser()
            extracted_text = parser.parse(file_content, safe_filename)
            logger.info("Successfully parsed document %s", safe_filename)
        except UnsupportedFileTypeError as e:
            logger.error("Unsupported file type: %s", e)
            raise ValueError(f"Unsupported file type: {str(e)}") from e
        except CorruptedFileError as e:
            logger.error("File appears to be corrupted: %s", e)
            raise ValueError(f"File is corrupted or invalid: {str(e)}") from e
        except EmptyFileError as e:
            logger.error("File contains no readable content: %s", e)
            raise ValueError(f"File contains no readable content: {str(e)}") from e
        except FileParseError as e:
            logger.error("Error parsing file: %s", e)
            raise ValueError(f"Error reading file: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error parsing document %s: %s", safe_filename, e)
            raise ValueError(f"Unexpected error processing file: {str(e)}") from e

        # Save metadata to database
        doc_metadata = await self.doc_repo.create_document(
            filename=safe_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            owner_id=owner_id,
            storage_path=storage_path,
        )

        # Store extracted text in memory under the document ID
        self.store.add_document(
            doc_metadata["id"],
            safe_filename,
            extracted_text,
        )

        # Persist file bytes to disk for recovery and audit trail
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        try:
            with open(storage_path, "wb") as f:
                f.write(file_content)
            logger.debug("Saved document file to disk: %s", storage_path)
        except Exception as e:
            logger.warning("Failed to persist document to disk %s: %s", storage_path, e)
            # Don't fail the upload if persistence fails; document is in memory
            # Database record is created, so it's still retrievable

        logger.info(
            "Document uploaded: %s (id=%s, size=%d bytes, parsed_text=%d chars)",
            safe_filename,
            doc_metadata["id"],
            size_bytes,
            len(extracted_text),
        )

        return doc_metadata

    async def get_document(self, document_id: str) -> Optional[dict]:
        """Get document metadata."""
        return await self.doc_repo.get_document_by_id(document_id)

    async def get_document_content(self, document_id: str) -> Optional[str]:
        """Get document content from store."""
        doc = self.store.get_document(document_id)
        if doc:
            return doc.content
        return None

    async def get_document_binary_content(self, document_id: str) -> Optional[bytes]:
        """Get document binary content from memory or persistent storage."""
        doc = self.store.get_document(document_id)
        if doc:
            return doc.content.encode("utf-8")

        metadata = await self.get_document(document_id)
        if not metadata:
            return None

        storage_path = metadata.get("storage_path")
        if storage_path and os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                content = f.read()
            # Warm cache for downstream services expecting text store entries.
            self.store.add_document(
                metadata["id"],
                metadata.get("filename", "document"),
                content.decode("utf-8", errors="replace"),
            )
            return content
        return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        metadata = await self.get_document(document_id)
        # Remove from store
        self.store.remove_document(document_id)
        if metadata:
            storage_path = metadata.get("storage_path")
            if storage_path and os.path.exists(storage_path):
                os.remove(storage_path)
        # Remove from database
        return await self.doc_repo.delete_document(document_id)

    async def list_user_documents(self, owner_id: str) -> list[dict]:
        """List all documents uploaded by a user."""
        return await self.doc_repo.list_user_documents(owner_id)

