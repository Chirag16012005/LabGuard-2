from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIModel(BaseModel):
    """Base model with project-wide config defaults."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class TimestampedModel(APIModel):
    created_at: datetime
    updated_at: datetime


class MessageResponse(APIModel):
    message: str


class ErrorResponse(APIModel):
    detail: str


class PaginatedResponse(APIModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    next_page: Optional[int] = None
