from __future__ import annotations

from pydantic import Field

from .base_schema import APIModel


class ComparisonPassage(APIModel):
    start_pos_1: int = Field(ge=0)
    end_pos_1: int = Field(ge=0)
    start_pos_2: int = Field(ge=0)
    end_pos_2: int = Field(ge=0)
    similarity: float = Field(ge=0.0, le=1.0)


class ComparisonResponse(APIModel):
    submission_id_1: str
    submission_id_2: str
    overall_similarity: float = Field(ge=0.0, le=100.0)
    matched_passages: list[ComparisonPassage]
