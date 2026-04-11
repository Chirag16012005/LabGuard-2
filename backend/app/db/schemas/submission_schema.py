from __future__ import annotations

from datetime import datetime
from enum import Enum

from typing import Optional

from pydantic import Field

from .base_schema import APIModel


class SubmissionStatus(str, Enum):
    submitted = "submitted"
    processing = "processing"
    failed = "failed"
    not_submitted = "not_submitted"


class SubmissionSummary(APIModel):
    id: Optional[str] = None
    assignment_id: str
    student_id: str
    student_name: str
    document_id: Optional[str] = None
    status: SubmissionStatus = SubmissionStatus.submitted
    submitted_at: Optional[datetime] = None

class AssignmentSubmissionsResponse(APIModel):
    assignment_id: str
    submissions: list[SubmissionSummary]
