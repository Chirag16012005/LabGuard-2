from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from ..db.mongodb import get_database


class DetectionRepository:
    """MongoDB repository for detection results."""

    def __init__(self) -> None:
        self.collection_name = "detections"

    async def create_detection_job(
        self, assignment_id: str, status: str = "pending"
    ) -> dict:
        """Create a new detection job."""
        db = get_database()
        collection = db[self.collection_name]

        job_data = {
            "assignment_id": assignment_id,
            "status": status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await collection.insert_one(job_data)
        job_data["id"] = str(result.inserted_id)
        return job_data

    async def get_detection_job(self, job_id: str) -> Optional[dict]:
        """Get detection job by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            job = await collection.find_one({"_id": ObjectId(job_id)})
            if job:
                job["id"] = str(job["_id"])
            return job
        except Exception:
            return None

    async def update_detection_job(
        self, job_id: str, status: str, report_id: Optional[str] = None
    ) -> bool:
        """Update detection job status."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": status,
                        "report_id": report_id,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception:
            return False
