from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base_schema import APIModel


class SubmissionStatus(str, Enum):
    submitted = "submitted"
    processing = "processing"
    failed = "failed"


class SubmissionSummary(APIModel):
    id: str
    assignment_id: str
    student_id: str
    document_id: str
    status: SubmissionStatus = SubmissionStatus.submitted
    submitted_at: datetime

class AssignmentSubmissionsResponse(APIModel):
    assignment_id: str
    submissions: list[SubmissionSummary]
