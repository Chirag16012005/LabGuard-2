from __future__ import annotations

from ..repositories.submission_repository import SubmissionRepository
from ..services.document_service import Document
from ..services.document_management_service import DocumentManagementService
from ..services.detection_service import PlagiarismDetector, PlagiarismConfig
from ..repositories.report_repository import ReportRepository
from ..repositories.detection_repository import DetectionRepository


class DetectionOrchestrationService:
    """Orchestrate plagiarism detection pipeline for assignments."""

    def __init__(self) -> None:
        self.submission_repo = SubmissionRepository()
        self.report_repo = ReportRepository()
        self.detection_repo = DetectionRepository()
        self.document_service = DocumentManagementService()
        self.detector = PlagiarismDetector(PlagiarismConfig())

    async def run_detection(self, assignment_id: str) -> dict:
        """Run plagiarism detection on all submissions for an assignment."""
        # Create detection job
        job = await self.detection_repo.create_detection_job(assignment_id, "processing")

        try:
            # Get all submissions for the assignment
            submissions = await self.submission_repo.list_assignment_submissions(assignment_id)

            if len(submissions) < 2:
                # Not enough submissions to compare
                await self.detection_repo.update_detection_job(job["id"], "completed")
                return {
                    "job_id": job["id"],
                    "status": "completed",
                    "message": "Less than 2 submissions. Skipping detection.",
                }

            # Build Document objects from submissions
            documents = []
            for sub in submissions:
                content = await self.document_service.get_document_content(
                    sub["document_id"]
                )
                doc = Document(
                    id=sub["document_id"],
                    filename=f"submission_{sub['student_id']}",
                    content=content or "",
                )
                documents.append(doc)

            # Run detection pipeline
            detection_results = self.detector.detect(documents)

            # Save report
            report = await self.report_repo.create_report(
                assignment_id=assignment_id,
                results=detection_results,
                average_similarity=self._calculate_average_similarity(detection_results),
                max_similarity=self._calculate_max_similarity(detection_results),
            )

            # Update job status
            await self.detection_repo.update_detection_job(
                job["id"], "completed", report["id"]
            )

            return {
                "job_id": job["id"],
                "report_id": report["id"],
                "status": "completed",
                "message": "Detection completed successfully",
            }

        except Exception as e:
            await self.detection_repo.update_detection_job(job["id"], "failed")
            raise e

    async def get_detection_job_status(self, job_id: str) -> dict | None:
        """Get detection job status and associated report id."""
        job = await self.detection_repo.get_detection_job(job_id)
        if not job:
            return None

        return {
            "job_id": job.get("id"),
            "assignment_id": job.get("assignment_id"),
            "status": job.get("status"),
            "report_id": job.get("report_id"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
        }

    @staticmethod
    def _calculate_average_similarity(results: dict) -> float:
        """Calculate average similarity from detection results."""
        if not results:
            return 0.0

        total = 0.0
        count = 0
        for doc_id, (_, doc_group, score) in results.items():
            total += score
            count += 1

        return total / count if count > 0 else 0.0

    @staticmethod
    def _calculate_max_similarity(results: dict) -> float:
        """Calculate max similarity from detection results."""
        if not results:
            return 0.0

        max_score = 0.0
        for doc_id, (_, doc_group, score) in results.items():
            max_score = max(max_score, score)

        return max_score
