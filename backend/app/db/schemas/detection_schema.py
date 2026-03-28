from __future__ import annotations

from pydantic import Field

from .base_schema import APIModel


class DetectionRunRequest(APIModel):
    assignment_id: str | None = None
    submission_ids: list[str] = Field(default_factory=list)
    force_recompute: bool = False


class MatchedPassage(APIModel):
    source_doc: str = Field(description="Compared document id")
    start_pos: int = Field(ge=0)
    end_pos: int = Field(ge=0)
    similarity: float = Field(ge=0.0, le=1.0)


class PerDocumentDetectionResult(APIModel):
    document_id: str
    plagiarism_score: float = Field(ge=0.0, le=100.0)
    matched_passages: list[MatchedPassage] = Field(default_factory=list)


class DetectionRunResponse(APIModel):
    report_id: str | None = None
    assignment_id: str | None = None
    results: list[PerDocumentDetectionResult] = Field(default_factory=list)
