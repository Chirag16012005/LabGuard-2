from typing import Optional

from ..repositories.submission_repository import SubmissionRepository
from ..repositories.assignment_repository import AssignmentRepository
from ..repositories.class_repository import ClassRepository
from ..repositories.user_repository import UserRepository
from .document_management_service import DocumentManagementService


class SubmissionService:
    """Submission management and tracking service."""

    def __init__(self) -> None:
        self.submission_repo = SubmissionRepository()
        self.assignment_repo = AssignmentRepository()
        self.class_repo = ClassRepository()
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

        # Fetch student name to include in returned submission
        student = await self.user_repo.get_user_by_id(student_id)
        student_name = student.get("full_name", "Unknown Student") if student else "Unknown Student"

        submission = await self.submission_repo.create_submission(
            assignment_id=assignment_id,
            student_id=student_id,
            document_id=document_id,
            notes=notes,
        )
        submission["student_name"] = student_name
        return submission

    async def get_submission(self, submission_id: str) -> Optional[dict]:
        """Get submission details."""
        submission = await self.submission_repo.get_submission_by_id(submission_id)
        if submission:
            student = await self.user_repo.get_user_by_id(submission["student_id"])
            submission["student_name"] = student.get("full_name", "Unknown Student") if student else "Unknown Student"
        return submission

    async def list_submissions(self, assignment_id: str) -> list[dict]:
        """List all submissions for an assignment with enrollment join."""
        # 1. Fetch assignment to get class_id
        assignment = await self.assignment_repo.get_assignment_by_id(assignment_id)
        if not assignment:
            return []
        
        class_id = assignment["class_id"]
        
        # 2. Fetch class to get enrolled students
        class_doc = await self.class_repo.get_class_by_id(class_id)
        if not class_doc:
            return []
        
        enrolled_student_ids = class_doc.get("students", [])
        
        # 3. Fetch all existing submissions for this assignment
        actual_submissions = await self.submission_repo.list_assignment_submissions(assignment_id)
        submissions_map = {s["student_id"]: s for s in actual_submissions}
        
        # 4. Fetch all student user profiles in batch
        student_metadata = await self.user_repo.get_users_by_ids(enrolled_student_ids)
        metadata_map = {u["id"]: u for u in student_metadata}
        
        # 5. Merge enrollment with submission data
        enriched_submissions = []
        for student_id in enrolled_student_ids:
            student_profile = metadata_map.get(student_id)
            student_name = student_profile.get("full_name", "Unknown Student") if student_profile else "Unknown Student"
            
            existing = submissions_map.get(student_id)
            
            if existing:
                # Student has submitted
                enriched_submissions.append({
                    **existing,
                    "student_name": student_name
                })
            else:
                # Student has NOT submitted
                enriched_submissions.append({
                    "id": None,
                    "assignment_id": assignment_id,
                    "student_id": student_id,
                    "student_name": student_name,
                    "document_id": None,
                    "status": "not_submitted",
                    "submitted_at": None
                })
        
        return enriched_submissions

    async def get_student_submission(
        self, assignment_id: str, student_id: str
    ) -> Optional[dict]:
        """Get a specific student's submission."""
        submission = await self.submission_repo.get_student_submission(assignment_id, student_id)
        if submission:
            student = await self.user_repo.get_user_by_id(student_id)
            submission["student_name"] = student.get("full_name", "Unknown Student") if student else "Unknown Student"
        return submission

    async def delete_submission(self, submission_id: str) -> bool:
        """Delete a submission and its linked document if present."""
        submission = await self.submission_repo.get_submission_by_id(submission_id)
        if not submission:
            return False

        document_id = submission.get("document_id")
        if document_id:
            await self.document_service.delete_document(document_id)

        return await self.submission_repo.delete_submission(submission_id)
