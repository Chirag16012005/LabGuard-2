from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .base_schema import APIModel


class ReportSummary(APIModel):
    id: str
    assignment_id: str
    generated_at: datetime
    average_similarity: float = Field(ge=0.0, le=100.0)
    max_similarity: float = Field(ge=0.0, le=100.0)


class ReportMatch(APIModel):
    source_submission_id: str
    target_submission_id: str
    similarity: float = Field(ge=0.0, le=1.0)
    start_pos: int = Field(ge=0)
    end_pos: int = Field(ge=0)


class HighlightedPassage(APIModel):
    submission_id: str
    text: str
    start_pos: int = Field(ge=0)
    end_pos: int = Field(ge=0)
    similarity: float = Field(ge=0.0, le=1.0)


class ReportDetailResponse(APIModel):
    report: ReportSummary


class ReportMatchesResponse(APIModel):
    report_id: str
    matches: list[ReportMatch]


class ReportWithHighlightsResponse(APIModel):
    report_id: str
    highlighted: list[HighlightedPassage]


class AssignmentReportsResponse(APIModel):
    assignment_id: str
    reports: list[ReportSummary]
