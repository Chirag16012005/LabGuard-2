from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from ..core.settings import get_settings
from ..db.schemas.auth_schema import UserRole
from ..repositories.user_repository import UserRepository


class AuthService:
    """Authentication and user management service."""

    def __init__(self) -> None:
        self.user_repo = UserRepository()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password complexity requirements."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("Password must include at least one letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must include at least one digit")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValueError("Password must include at least one special character")

    async def register_user(
        self,
        email: str,
        full_name: str,
        password: str,
        role: UserRole = UserRole.student,
    ) -> dict:
        """Register a new user."""
        self.validate_password(password)

        # Check if user already exists
        if await self.user_repo.user_exists(email):
            raise ValueError(f"User with email {email} already exists")

        # Hash password
        password_hash = self.hash_password(password)

        # Create user
        user = await self.user_repo.create_user(
            email=email, full_name=full_name, password_hash=password_hash, role=role
        )

        return user

    async def login_user(self, email: str, password: str) -> Optional[dict]:
        email = email.lower().strip()

        user = await self.user_repo.get_user_by_email(email)

        print("=== LOGIN DEBUG ===")
        print("INPUT EMAIL:", repr(email))
        print("INPUT PASSWORD:", repr(password))
        print("USER FOUND:", user)

        if not user:
            print("❌ USER NOT FOUND")
            return None

        input_hash = self.hash_password(password)
        db_hash = user.get("password_hash", "")

        print("INPUT HASH:", input_hash)
        print("DB HASH:", db_hash)

        if not self.verify_password(password, db_hash):
            print("❌ PASSWORD MISMATCH")
            return None

        print("✅ LOGIN SUCCESS")
        return user

    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        return await self.user_repo.get_user_by_id(user_id)

    def generate_token(self, user_id: str, email: str, role: str | None = None) -> str:
        """Generate a JWT token for the user."""
        settings = get_settings()
        payload = {
            "sub": user_id,
            "user_id": user_id,
            "email": email,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=settings.jwt_expiration_hours),
        }
        if role:
            payload["role"] = role
        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        return token
