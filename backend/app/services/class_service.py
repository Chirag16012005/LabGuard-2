from __future__ import annotations

from typing import Optional

from ..repositories.class_repository import ClassRepository
from ..repositories.user_repository import UserRepository


class ClassService:
    """Class management service."""

    def __init__(self) -> None:
        self.class_repo = ClassRepository()
        self.user_repo = UserRepository()

    async def create_class(
        self,
        name: str,
        teacher_id: str,
        class_code: str,
        description: str,
        section: Optional[str] = None,
    ) -> dict:
        """Create a new class."""
        normalized_class_code = class_code.strip().upper()
        existing_class = await self.class_repo.get_class_by_class_code(
            normalized_class_code
        )
        if existing_class:
            raise ValueError(f"Class code {normalized_class_code} already exists")

        return await self.class_repo.create_class(
            name=name,
            teacher_id=teacher_id,
            class_code=normalized_class_code,
            description=description,
            section=section,
        )

    async def get_class(self, class_id: str) -> Optional[dict]:
        """Get class details."""
        return await self.class_repo.get_class_by_id(class_id)

    async def list_my_classes(self, user_id: str) -> list[dict]:
        """List classes for a user without role-based filtering."""
        return await self.class_repo.list_user_classes(user_id)

    async def delete_class(self, class_id: str) -> bool:
        """Delete a class."""
        return await self.class_repo.delete_class(class_id)

    async def join_class(self, class_id: str, join_code: str, student_id: str) -> bool:
        """Join a class using join code."""
        normalized_code = join_code.strip().upper()
        class_doc = await self.class_repo.get_class_by_join_code(normalized_code)
        if not class_doc:
            raise ValueError("Invalid join code")

        if class_doc["class_id"] != class_id:
            raise ValueError("Join code does not match this class")

        return await self.class_repo.add_student_to_class(class_id, student_id)

    async def leave_class(self, class_id: str, student_id: str) -> bool:
        """Leave a class by removing enrolled student."""
        class_doc = await self.class_repo.get_class_by_id(class_id)
        if not class_doc:
            raise ValueError("Class not found")

        if student_id not in class_doc.get("students", []):
            raise ValueError("Student is not enrolled in this class")

        return await self.class_repo.remove_student_from_class(class_id, student_id)

    async def list_class_students(self, class_id: str) -> list[dict]:
        """List all students in a class with safe profile fields."""
        class_doc = await self.class_repo.get_class_by_id(class_id)
        if not class_doc:
            return []

        students: list[dict] = []
        for student_id in class_doc.get("students", []):
            user = await self.user_repo.get_user_by_id(student_id)
            if not user:
                continue
            students.append(
                {
                    "id": user.get("id") or str(user.get("_id")),
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                }
            )
        return students
