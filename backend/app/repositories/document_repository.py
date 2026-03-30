from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from ..db.mongodb import get_database


class DocumentRepository:
    """MongoDB document repository."""

    def __init__(self) -> None:
        self.collection_name = "documents"

    async def create_document(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        owner_id: Optional[str] = None,
        storage_path: Optional[str] = None,
    ) -> dict:
        """Create a new document metadata record."""
        db = get_database()
        collection = db[self.collection_name]

        doc_data = {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "owner_id": owner_id,
            "storage_path": storage_path,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await collection.insert_one(doc_data)
        doc_data["id"] = str(result.inserted_id)
        return doc_data

    async def get_document_by_id(self, document_id: str) -> Optional[dict]:
        """Get document by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            doc = await collection.find_one({"_id": ObjectId(document_id)})
            if doc:
                doc["id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete document by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.delete_one({"_id": ObjectId(document_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def list_user_documents(self, owner_id: str) -> list[dict]:
        """List all documents uploaded by a user."""
        db = get_database()
        collection = db[self.collection_name]

        docs = []
        async for doc in collection.find({"owner_id": owner_id}):
            doc["id"] = str(doc["_id"])
            docs.append(doc)
        return docs
