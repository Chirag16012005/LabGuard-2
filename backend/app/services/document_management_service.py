from __future__ import annotations

import os
from uuid import uuid4
from typing import Optional

from ..repositories.document_repository import DocumentRepository
from ..services.document_service import Document, InMemoryDocumentStore


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
        """Upload and store a document."""
        size_bytes = len(file_content)
        safe_filename = os.path.basename(filename)
        storage_path = os.path.join(".storage", "documents", f"{uuid4()}_{safe_filename}")

        # Save metadata to database
        doc_metadata = await self.doc_repo.create_document(
            filename=safe_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            owner_id=owner_id,
            storage_path=storage_path,
        )

        # Store file content in memory under the same ID returned by the database.
        self.store.add_document(
            doc_metadata["id"],
            safe_filename,
            file_content.decode("utf-8", errors="replace"),
        )

        # Persist bytes to disk so content remains available after process restarts.
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(file_content)

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

