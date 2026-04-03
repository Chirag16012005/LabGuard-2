from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator

from .base_schema import APIModel


class AssignmentStatus(str, Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class AssignmentFileType(str, Enum):
    pdf = "pdf"
    doc = "doc"
    docx = "docx"
    txt = "txt"
    ppt = "ppt"
    pptx = "pptx"
    xls = "xls"
    xlsx = "xlsx"
    csv = "csv"
    image = "image"
    other = "other"


class AssignmentCreateRequest(APIModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)
    size_bytes: int = Field(gt=0, le=104857600)
    file_type: AssignmentFileType = AssignmentFileType.other
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        normalized = value.lower().strip()
        allowed_content_types = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/rtf",
            "text/plain",
            "text/csv",
        }

        if normalized in allowed_content_types:
            return normalized

        if normalized.startswith("image/"):
            return normalized

        raise ValueError("Unsupported assignment file type")


class AssignmentSummary(APIModel):
    assignment_id: str
    class_id: str
    filename: str
    content_type: str
    file_type: AssignmentFileType = AssignmentFileType.other
    size_bytes: int = Field(ge=0)
    status: AssignmentStatus
    submission_count: int = 0
    created_at: datetime


class AssignmentDetails(AssignmentSummary):
    description: str | None = None
    storage_path: str | None = None


class AssignmentCreateResponse(APIModel):
    assignment: AssignmentDetails


class AssignmentListResponse(APIModel):
    class_id: str
    assignments: list[AssignmentSummary]


class AssignmentDetailResponse(APIModel):
    assignment: AssignmentDetails
