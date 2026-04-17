from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from ..db.mongodb import get_database


class DocumentRepository:
    """MongoDB document repository."""

    def __init__(self) -> None:
        self.collection_name = "documents"

    @staticmethod
    def _serialize_document(doc: dict) -> dict:
        """Convert MongoDB document into JSON-safe payload."""
        serialized = dict(doc)
        serialized["id"] = str(serialized.get("_id"))
        serialized.pop("_id", None)
        return serialized

    async def create_document(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        owner_id: Optional[str] = None,
        file_id: Optional[str] = None,
        storage_path: Optional[str] = None,
    ) -> dict:
        """Create a new document metadata record."""
        db = get_database()
        collection = db[self.collection_name]

        # Keep a stable explicit `id` field because documents collection has a unique index on `id`.
        doc_object_id = ObjectId()

        doc_data = {
            "_id": doc_object_id,
            "id": str(doc_object_id),
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "owner_id": owner_id,
            "file_id": file_id,
            "storage_path": storage_path,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        await collection.insert_one(doc_data)
        return self._serialize_document(doc_data)

    async def get_document_by_id(self, document_id: str) -> Optional[dict]:
        """Get document by ID.

        Supports both Mongo _id(ObjectId) and explicit string id field for
        compatibility with older records.
        """
        try:
            db = get_database()
            collection = db[self.collection_name]

            normalized_id = str(document_id).strip()
            doc = None

            # Primary lookup path for current records.
            try:
                doc = await collection.find_one({"_id": ObjectId(normalized_id)})
            except Exception:
                doc = None

            # Backward-compatible fallback for records keyed by explicit string id.
            if not doc:
                doc = await collection.find_one({"id": normalized_id})

            if doc:
                return self._serialize_document(doc)
            return None
        except Exception:
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete document by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]

            normalized_id = str(document_id).strip()
            result = None

            try:
                result = await collection.delete_one({"_id": ObjectId(normalized_id)})
            except Exception:
                result = None

            if result is not None and result.deleted_count > 0:
                return True

            # Backward-compatible fallback delete path.
            fallback = await collection.delete_one({"id": normalized_id})
            return fallback.deleted_count > 0
        except Exception:
            return False

    async def list_user_documents(self, owner_id: str) -> list[dict]:
        """List all documents uploaded by a user."""
        db = get_database()
        collection = db[self.collection_name]

        docs = []
        async for doc in collection.find({"owner_id": owner_id}):
            docs.append(self._serialize_document(doc))
        return docs
