from __future__ import annotations

from typing import Optional
import hashlib

from ..repositories.detection_repository import DetectionRepository
from ..repositories.report_repository import ReportRepository
from ..repositories.submission_repository import SubmissionRepository


class ReportService:
    """Report generation and retrieval service."""

    def __init__(self) -> None:
        self.report_repo = ReportRepository()
        self.detection_repo = DetectionRepository()
        self.submission_repo = SubmissionRepository()

    @staticmethod
    def _student_report_id(report_id: str, document_id: str) -> str:
        """Create deterministic student_report_id for a document in a report."""
        return hashlib.md5(f"{report_id}_{document_id}".encode()).hexdigest()[:16]

    @staticmethod
    def _build_student_report_entry(
        report: dict, document_id: str, student_report_id: str
    ) -> dict:
        """Build one student-facing report entry from a report and document id."""
        results = report.get("results", {})
        document_ids = sorted(results.keys())
        _, doc_group, plagiarism_score = results.get(
            document_id, [document_id, {}, 0.0]
        )

        comparisons = []
        for target_doc_id in document_ids:
            if document_id != target_doc_id:
                passages_list, similarity_score = doc_group.get(
                    target_doc_id, [[], 0.0]
                )
                comparisons.append(
                    {
                        "document_id": target_doc_id,
                        "similarity": similarity_score,
                        "matched_passages": len(passages_list),
                    }
                )

        return {
            "student_report_id": student_report_id,
            "report_id": report.get("report_id"),
            "assignment_id": report.get("assignment_id"),
            "document_id": document_id,
            "plagiarism_score": plagiarism_score,
            "comparisons": comparisons,
        }

    async def list_assignment_reports(self, assignment_id: str) -> list[dict]:
        """List all reports for an assignment with formatted matrix data."""
        reports = await self.report_repo.list_assignment_reports(assignment_id)
        formatted_reports = []

        for report in reports:
            # Transform each report into matrix format for better readability
            results = report.get("results", {})
            matrix = []
            document_ids = sorted(results.keys())

            for doc_id in document_ids:
                doc_id_ref, doc_group, plagiarism_score = results.get(
                    doc_id, [doc_id, {}, 0.0]
                )

                # Generate deterministic student_report_id from report_id + document_id
                student_report_id = self._student_report_id(
                    report.get("report_id", ""), doc_id
                )
                row = {
                    "student_report_id": student_report_id,  # ← Persistent ID for this student in this report
                    "document_id": doc_id,
                    "plagiarism_score": plagiarism_score,
                    "comparisons": [],
                }

                for target_doc_id in document_ids:
                    if doc_id != target_doc_id:
                        passages_list, similarity_score = doc_group.get(
                            target_doc_id, [[], 0.0]
                        )
                        row["comparisons"].append(
                            {
                                "document_id": target_doc_id,
                                "similarity": similarity_score,
                                "matched_passages": len(passages_list),
                            }
                        )

                matrix.append(row)

            formatted_report = {
                "report_id": report.get("report_id"),
                "assignment_id": report.get("assignment_id"),
                "generated_at": report.get("generated_at"),
                "is_published": bool(report.get("is_published", False)),
                "average_similarity": report.get("average_similarity", 0.0),
                "max_similarity": report.get("max_similarity", 0.0),
                "documents": document_ids,
                "matrix": matrix,
            }
            formatted_reports.append(formatted_report)

        return formatted_reports

    async def get_student_report_entry_by_id(
        self,
        student_report_id: str,
        include_unpublished: bool = False,
    ) -> Optional[dict]:
        """Get one student report entry using only student_report_id."""
        reports = await self.report_repo.list_all_reports()

        for report in reports:
            if not include_unpublished and not report.get("is_published", False):
                continue

            results = report.get("results", {})
            document_ids = sorted(results.keys())

            for document_id in document_ids:
                expected_id = self._student_report_id(
                    report.get("report_id", ""), document_id
                )
                if expected_id != student_report_id:
                    continue
                return self._build_student_report_entry(
                    report=report,
                    document_id=document_id,
                    student_report_id=student_report_id,
                )

        return None

    async def get_student_report_entry_for_student(
        self,
        report_id: str,
        student_id: str,
        include_unpublished: bool = False,
    ) -> Optional[dict]:
        """Resolve a student's entry when caller passes report_id instead of student_report_id."""
        report = await self.report_repo.get_report_by_id(report_id)
        if not report:
            return None

        if not include_unpublished and not report.get("is_published", False):
            return None

        assignment_id = report.get("assignment_id")
        if not assignment_id:
            return None

        submission = await self.submission_repo.get_student_submission(
            assignment_id,
            student_id,
        )
        if not submission:
            return None

        document_id = submission.get("document_id")
        results = report.get("results", {})
        if not document_id or document_id not in results:
            return None

        resolved_student_report_id = self._student_report_id(
            report.get("report_id", ""),
            document_id,
        )
        return self._build_student_report_entry(
            report=report,
            document_id=document_id,
            student_report_id=resolved_student_report_id,
        )

    async def publish_latest_assignment_report(
        self, assignment_id: str
    ) -> Optional[dict]:
        """Publish latest report and map generated student reports to student submissions."""
        report = await self.report_repo.publish_latest_report(assignment_id)
        if not report:
            return None

        results = report.get("results", {})
        submissions = await self.submission_repo.list_assignment_submissions(
            assignment_id
        )
        dispatched_reports = []

        for submission in submissions:
            document_id = submission.get("document_id")
            if not document_id or document_id not in results:
                continue

            dispatched_reports.append(
                {
                    "student_id": submission.get("student_id"),
                    "submission_id": submission.get("id"),
                    "student_report_id": self._student_report_id(
                        report.get("report_id", ""), document_id
                    ),
                }
            )

        return {
            "report_id": report.get("report_id"),
            "assignment_id": assignment_id,
            "is_published": True,
            "published_at": report.get("published_at"),
            "dispatched_reports": dispatched_reports,
            "dispatched_count": len(dispatched_reports),
        }

    async def get_report_matches(self, report_id: str) -> Optional[dict]:
        """Get all plagiarism matches from a report with full passage details."""
        report = await self.report_repo.get_report_by_id(report_id)

        if not report:
            return None

        results = report.get("results", {})
        matches = []

        for doc_id, (_, doc_group, plagiarism_score) in results.items():
            for target_doc_id, (passages_list, similarity_score) in doc_group.items():
                if passages_list:  # Only include if there are actual matches
                    match = {
                        "source_document_id": doc_id,
                        "target_document_id": target_doc_id,
                        "similarity": similarity_score,
                        "plagiarism_score": plagiarism_score,
                        "passages": passages_list,
                    }
                    matches.append(match)

        return {
            "report_id": report.get("report_id"),
            "assignment_id": report.get("assignment_id"),
            "total_matches": len(matches),
            "matches": matches,
        }

    async def create_report(
        self,
        assignment_id: str,
        results: dict,
        average_similarity: float = 0.0,
        max_similarity: float = 0.0,
    ) -> dict:
        """Create a new report."""
        return await self.report_repo.create_report(
            assignment_id=assignment_id,
            results=results,
            average_similarity=average_similarity,
            max_similarity=max_similarity,
        )
