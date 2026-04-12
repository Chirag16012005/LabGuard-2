from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from ..db.mongodb import get_database


class AssignmentRepository:
    """MongoDB assignment repository."""

    def __init__(self) -> None:
        self.collection_name = "assignments"

    @staticmethod
    def _serialize_assignment(doc: dict) -> dict:
        """Convert MongoDB assignment document into JSON-safe payload."""
        serialized = dict(doc)
        serialized["assignment_id"] = serialized.get("assignment_id") or str(
            serialized.get("_id")
        )
        serialized.pop("_id", None)
        serialized.pop("id", None)
        return serialized

    async def create_assignment(
        self,
        class_id: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
        assignment_file_document_id: Optional[str] = None,
        storage_path: Optional[str] = None,
    ) -> dict:
        """Create a new assignment."""
        db = get_database()
        collection = db[self.collection_name]

        assignment_data = {
            "class_id": class_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "assignment_file_document_id": assignment_file_document_id,
            "storage_path": storage_path,
            "submissions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        object_id = ObjectId()
        assignment_data["_id"] = object_id
        assignment_data["assignment_id"] = str(object_id)
        await collection.insert_one(assignment_data)
        return self._serialize_assignment(assignment_data)

    async def get_assignment_by_id(self, assignment_id: str) -> Optional[dict]:
        """Get assignment by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            assignment = await collection.find_one({"_id": ObjectId(assignment_id)})
            if assignment:
                return self._serialize_assignment(assignment)
            return None
        except Exception:
            return None

    async def list_class_assignments(self, class_id: str) -> list[dict]:
        """List all assignments for a class."""
        db = get_database()
        collection = db[self.collection_name]

        assignments = []
        async for doc in collection.find({"class_id": class_id}):
            assignments.append(self._serialize_assignment(doc))
        return assignments

    async def delete_assignment(self, assignment_id: str) -> bool:
        """Delete assignment by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.delete_one({"_id": ObjectId(assignment_id)})
            return result.deleted_count > 0
        except Exception:
            return False
