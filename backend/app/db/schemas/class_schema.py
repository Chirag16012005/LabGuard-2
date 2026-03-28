from __future__ import annotations

from datetime import datetime
from pydantic import Field

from .auth_schema import UserPublic
from .base_schema import APIModel


class ClassCreateRequest(APIModel):
    name: str = Field(min_length=2, max_length=120)
    section: str | None = Field(default=None, max_length=50)
    course_code: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, max_length=1000)


class ClassSummary(APIModel):
    id: str
    name: str
    section: str | None = None
    course_code: str | None = None
    teacher_id: str
    student_count: int = 0
    created_at: datetime


class ClassDetails(ClassSummary):
    description: str | None = None


class ClassListResponse(APIModel):
    items: list[ClassSummary]
    total: int


class ClassCreateResponse(APIModel):
    class_: ClassDetails = Field(alias="class")


class ClassDetailResponse(APIModel):
    class_: ClassDetails = Field(alias="class")


class JoinClassRequest(APIModel):
    join_code: str = Field(min_length=4, max_length=24)


class JoinClassResponse(APIModel):
    class_id: str
    student_id: str
    joined_at: datetime


class ClassStudentsResponse(APIModel):
    class_id: str
    students: list[UserPublic]
