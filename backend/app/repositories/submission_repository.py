from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from ..db.mongodb import get_database


class SubmissionRepository:
    """MongoDB submission repository."""

    def __init__(self) -> None:
        self.collection_name = "submissions"

    @staticmethod
    def _serialize_submission(doc: dict) -> dict:
        """Convert MongoDB submission document into JSON-safe payload."""
        serialized = dict(doc)
        serialized["id"] = str(serialized.get("_id"))
        serialized.pop("_id", None)
        return serialized

    async def create_submission(
        self,
        assignment_id: str,
        student_id: str,
        document_id: str,
        notes: Optional[str] = None,
    ) -> dict:
        """Create a new submission."""
        db = get_database()
        collection = db[self.collection_name]

        submission_data = {
            "assignment_id": assignment_id,
            "student_id": student_id,
            "document_id": document_id,
            "notes": notes,
            "status": "submitted",
            "submitted_at": datetime.utcnow(),
        }

        result = await collection.insert_one(submission_data)
        submission_data["id"] = str(result.inserted_id)
        return submission_data

    async def get_submission_by_id(self, submission_id: str) -> Optional[dict]:
        """Get submission by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            submission = await collection.find_one({"_id": ObjectId(submission_id)})
            if submission:
                return self._serialize_submission(submission)
            return None
        except Exception:
            return None

    async def list_assignment_submissions(self, assignment_id: str) -> list[dict]:
        """List all submissions for an assignment."""
        db = get_database()
        collection = db[self.collection_name]

        submissions = []
        async for doc in collection.find({"assignment_id": assignment_id}):
            submissions.append(self._serialize_submission(doc))
        return submissions

    async def get_student_submission(
        self, assignment_id: str, student_id: str
    ) -> Optional[dict]:
        """Get a specific student's submission for an assignment."""
        db = get_database()
        collection = db[self.collection_name]
        submission = await collection.find_one(
            {"assignment_id": assignment_id, "student_id": student_id}
        )
        if submission:
            return self._serialize_submission(submission)
        return None

    async def get_submission_by_document_id(self, document_id: str) -> Optional[dict]:
        """Get submission by linked document id."""
        db = get_database()
        collection = db[self.collection_name]
        submission = await collection.find_one({"document_id": document_id})
        if submission:
            return self._serialize_submission(submission)
        return None

    async def delete_submission(self, submission_id: str) -> bool:
        """Delete submission by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.delete_one({"_id": ObjectId(submission_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def delete_submissions_by_assignment(self, assignment_id: str) -> int:
        """Delete all submissions for an assignment and return deleted count."""
        db = get_database()
        collection = db[self.collection_name]
        result = await collection.delete_many({"assignment_id": assignment_id})
        return result.deleted_count
