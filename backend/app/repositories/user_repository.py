from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from ..db.mongodb import get_database
from ..db.schemas.auth_schema import UserRole


class UserRepository:
    """MongoDB user repository for authentication and user management."""

    def __init__(self) -> None:
        self.collection_name = "users"

    async def create_user(
        self,
        email: str,
        full_name: str,
        password_hash: str,
        role: UserRole,
    ) -> dict:
        """Create a new user."""
        db = get_database()
        collection = db[self.collection_name]

        user_data = {
            "email": email,
            "full_name": full_name,
            "password_hash": password_hash,
            "role": role.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await collection.insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        return user_data

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        db = get_database()
        collection = db[self.collection_name]

        user = await collection.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            user = await collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
            return user
        except Exception:
            return None

    async def user_exists(self, email: str) -> bool:
        """Check if user exists."""
        db = get_database()
        collection = db[self.collection_name]
        user = await collection.find_one({"email": email})
        return user is not None
