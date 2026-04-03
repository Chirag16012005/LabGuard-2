from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..repositories.assignment_repository import AssignmentRepository
from ..repositories.submission_repository import SubmissionRepository
from .document_management_service import DocumentManagementService


class AssignmentService:
    """Assignment management service."""

    def __init__(self) -> None:
        self.assignment_repo = AssignmentRepository()
        self.submission_repo = SubmissionRepository()
        self.document_service = DocumentManagementService()

    async def create_assignment(
        self,
        class_id: str,
        filename: str,
        content_type: str,
        file_content: bytes,
        teacher_id: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> dict:
        """Create a new assignment from an uploaded file."""
        if not file_content:
            raise ValueError("Assignment file is required")

        uploaded_doc = await self.document_service.upload_document(
            filename=filename,
            content_type=content_type,
            file_content=file_content,
            owner_id=teacher_id,
        )

        title = Path(filename).stem or "assignment"
        return await self.assignment_repo.create_assignment(
            class_id=class_id,
            title=title,
            description=description,
            due_date=due_date,
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_content),
            assignment_file_document_id=uploaded_doc["id"],
            storage_path=uploaded_doc.get("storage_path"),
        )

    async def get_assignment(self, assignment_id: str) -> Optional[dict]:
        """Get assignment details."""
        return await self.assignment_repo.get_assignment_by_id(assignment_id)

    async def list_assignments(self, class_id: str) -> list[dict]:
        """List all assignments for a class."""
        return await self.assignment_repo.list_class_assignments(class_id)

    async def delete_assignment(self, assignment_id: str) -> bool:
        """Delete an assignment and cascade delete linked documents/submissions."""
        assignment = await self.assignment_repo.get_assignment_by_id(assignment_id)
        if not assignment:
            return False

        assignment_document_id = assignment.get("assignment_file_document_id")
        if assignment_document_id:
            await self.document_service.delete_document(assignment_document_id)

        submissions = await self.submission_repo.list_assignment_submissions(assignment_id)
        for submission in submissions:
            submission_document_id = submission.get("document_id")
            if submission_document_id:
                await self.document_service.delete_document(submission_document_id)

        await self.submission_repo.delete_submissions_by_assignment(assignment_id)
        return await self.assignment_repo.delete_assignment(assignment_id)
