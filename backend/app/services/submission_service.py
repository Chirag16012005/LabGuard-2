from __future__ import annotations

from typing import Optional

from ..repositories.submission_repository import SubmissionRepository
from ..repositories.user_repository import UserRepository
from .document_management_service import DocumentManagementService


class SubmissionService:
    """Submission management and tracking service."""

    def __init__(self) -> None:
        self.submission_repo = SubmissionRepository()
        self.user_repo = UserRepository()
        self.document_service = DocumentManagementService()

    async def submit_assignment(
        self,
        assignment_id: str,
        student_id: str,
        document_id: str,
        notes: Optional[str] = None,
    ) -> dict:
        """Submit an assignment."""
        existing = await self.submission_repo.get_student_submission(
            assignment_id, student_id
        )
        if existing:
            raise ValueError("Only one submission per student is allowed for this assignment")

        return await self.submission_repo.create_submission(
            assignment_id=assignment_id,
            student_id=student_id,
            document_id=document_id,
            notes=notes,
        )

    async def get_submission(self, submission_id: str) -> Optional[dict]:
        """Get submission details."""
        return await self.submission_repo.get_submission_by_id(submission_id)

    async def list_submissions(self, assignment_id: str) -> list[dict]:
        """List all submissions for an assignment."""
        submissions = await self.submission_repo.list_assignment_submissions(assignment_id)
        if not submissions:
            return []

        student_ids = list(
            {
                str(item.get("student_id"))
                for item in submissions
                if item.get("student_id")
            }
        )

        users = await self.user_repo.get_users_by_ids(student_ids) if student_ids else []
        names_by_id = {
            str(user.get("id")): (user.get("full_name") or user.get("email") or "Unknown student")
            for user in users
        }

        for submission in submissions:
            student_id = str(submission.get("student_id") or "")
            submission["student_name"] = names_by_id.get(student_id, "Unknown student")

        return submissions

    async def get_student_submission(
        self, assignment_id: str, student_id: str
    ) -> Optional[dict]:
        """Get a specific student's submission."""
        return await self.submission_repo.get_student_submission(assignment_id, student_id)

    async def delete_submission(self, submission_id: str) -> bool:
        """Delete a submission and its linked document if present."""
        submission = await self.submission_repo.get_submission_by_id(submission_id)
        if not submission:
            return False

        document_id = submission.get("document_id")
        if document_id:
            await self.document_service.delete_document(document_id)

        return await self.submission_repo.delete_submission(submission_id)
