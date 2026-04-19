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
        auth_provider: str = "local",
        google_sub: str | None = None,
    ) -> dict:
        """Create a new user."""
        db = get_database()
        collection = db[self.collection_name]

        user_data = {
            "email": email,
            "full_name": full_name,
            "password_hash": password_hash,
            "role": role.value,
            "auth_provider": auth_provider,
            "google_sub": google_sub,
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

    async def get_users_by_ids(self, user_ids: list[str]) -> list[dict]:
        """Get multiple users by their IDs."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            object_ids = [ObjectId(uid) for uid in user_ids]

            users = []
            async for user in collection.find({"_id": {"$in": object_ids}}):
                user["id"] = str(user["_id"])
                users.append(user)
            return users
        except Exception:
            return []

    async def user_exists(self, email: str) -> bool:
        """Check if user exists."""
        db = get_database()
        collection = db[self.collection_name]
        user = await collection.find_one({"email": email})
        return user is not None

    async def set_password_hash(self, user_id: str, password_hash: str) -> bool:
        """Update a user's password hash and clear any reset token state."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "updated_at": datetime.utcnow(),
                    },
                    "$unset": {
                        "password_reset_token_hash": "",
                        "password_reset_expires_at": "",
                    },
                },
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def set_password_reset_token(
        self,
        email: str,
        token_hash: str,
        expires_at: datetime,
    ) -> bool:
        """Store hashed reset token and expiry for a user identified by email."""
        db = get_database()
        collection = db[self.collection_name]
        result = await collection.update_one(
            {"email": email},
            {
                "$set": {
                    "password_reset_token_hash": token_hash,
                    "password_reset_expires_at": expires_at,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def get_user_by_password_reset_token(self, token_hash: str) -> Optional[dict]:
        """Resolve a user by reset token hash."""
        db = get_database()
        collection = db[self.collection_name]
        user = await collection.find_one({"password_reset_token_hash": token_hash})
        if user:
            user["id"] = str(user["_id"])
        return user

    async def clear_password_reset_token(self, user_id: str) -> bool:
        """Clear reset token fields for a user."""
        try:
            db = get_database()
            collection = db[self.collection_name]
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$unset": {
                        "password_reset_token_hash": "",
                        "password_reset_expires_at": "",
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            return result.modified_count > 0
        except Exception:
            return False
