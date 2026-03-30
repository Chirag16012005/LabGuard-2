from __future__ import annotations

from datetime import datetime
import re
from typing import Optional
from uuid import uuid4

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from ..db.mongodb import get_database


class ClassRepository:
    """MongoDB class repository for classroom management."""

    def __init__(self) -> None:
        self.collection_name = "classes"

    @staticmethod
    def _serialize_class_doc(doc: dict) -> dict:
        """Convert MongoDB document into JSON-safe class payload."""
        serialized = dict(doc)
        serialized["class_id"] = str(serialized.get("_id"))
        serialized.pop("_id", None)
        if "class_code" not in serialized and "course_code" in serialized:
            serialized["class_code"] = serialized.get("course_code")
        serialized.setdefault("description", "")
        return serialized

    async def create_class(
        self,
        name: str,
        teacher_id: str,
        class_code: str,
        description: str,
        section: Optional[str] = None,
    ) -> dict:
        """Create a new class."""
        db = get_database()
        collection = db[self.collection_name]

        class_data = {
            "name": name,
            "section": section,
            "class_code": class_code,
            "description": description,
            "teacher_id": teacher_id,
            "join_code": str(uuid4())[:12].upper(),
            "students": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        try:
            result = await collection.insert_one(class_data)
            class_data["class_id"] = str(result.inserted_id)
            return class_data
        except DuplicateKeyError as exc:
            raise ValueError(f"Class code {class_code} already exists") from exc

    async def get_class_by_id(self, class_id: str) -> Optional[dict]:
        """Get class by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            class_doc = await collection.find_one({"_id": ObjectId(class_id)})
            if class_doc:
                return self._serialize_class_doc(class_doc)
            return None
        except Exception:
            return None

    async def list_teacher_classes(self, teacher_id: str) -> list[dict]:
        """List all classes for a teacher."""
        db = get_database()
        collection = db[self.collection_name]

        classes = []
        async for doc in collection.find({"teacher_id": teacher_id}):
            classes.append(self._serialize_class_doc(doc))
        return classes

    async def list_student_classes(self, student_id: str) -> list[dict]:
        """List all classes a student is enrolled in."""
        db = get_database()
        collection = db[self.collection_name]

        classes = []
        async for doc in collection.find({"students": student_id}):
            classes.append(self._serialize_class_doc(doc))
        return classes

    async def add_student_to_class(self, class_id: str, student_id: str) -> bool:
        """Add student to class."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.update_one(
                {"_id": ObjectId(class_id)},
                {
                    "$addToSet": {"students": student_id},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            return result.matched_count > 0
        except Exception:
            return False

    async def get_class_by_join_code(self, join_code: str) -> Optional[dict]:
        """Get class by join code."""
        db = get_database()
        collection = db[self.collection_name]
        class_doc = await collection.find_one({"join_code": join_code})
        if class_doc:
            return self._serialize_class_doc(class_doc)
        return None

    async def get_class_by_class_code(self, class_code: str) -> Optional[dict]:
        """Get class by class code (case-insensitive)."""
        db = get_database()
        collection = db[self.collection_name]
        pattern = f"^{re.escape(class_code)}$"
        class_doc = await collection.find_one(
            {"class_code": {"$regex": pattern, "$options": "i"}}
        )
        if class_doc:
            return self._serialize_class_doc(class_doc)
        return None

    async def delete_class(self, class_id: str) -> bool:
        """Delete class by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.delete_one({"_id": ObjectId(class_id)})
            return result.deleted_count > 0
        except Exception:
            return False
