from __future__ import annotations

import hashlib
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

import jwt
from google.auth.transport import requests as google_requests  # type: ignore[import-not-found]
from google.oauth2 import id_token as google_id_token  # type: ignore[import-not-found]

from ..core.settings import get_settings
from ..db.schemas.auth_schema import UserRole
from .email_service import EmailService
from ..repositories.user_repository import UserRepository


class AuthService:
    """Authentication and user management service."""

    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.email_service = EmailService()

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
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            auth_provider="local",
        )

        return user

    async def login_user(self, email: str, password: str) -> Optional[dict]:
        email = email.lower().strip()

        user = await self.user_repo.get_user_by_email(email)

        if not user:
            return None
        db_hash = user.get("password_hash", "")

        if not self.verify_password(password, db_hash):
            return None
        return user

    async def login_with_google(
        self,
        google_token: str,
        role: UserRole = UserRole.student,
    ) -> Optional[dict]:
        """Authenticate using a Google ID token and provision user on first login."""
        settings = get_settings()
        if not settings.google_oauth_client_id:
            raise ValueError("Google OAuth is not configured")

        try:
            token_payload = google_id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.google_oauth_client_id,
            )
        except ValueError:
            return None

        if not token_payload.get("email_verified", False):
            raise ValueError("Google account email is not verified")

        email = str(token_payload.get("email", "")).lower().strip()
        if not email:
            return None

        existing_user = await self.user_repo.get_user_by_email(email)
        if existing_user:
            return existing_user

        full_name = str(token_payload.get("name") or email.split("@")[0]).strip()
        random_password = secrets.token_urlsafe(32)
        password_hash = self.hash_password(random_password)
        return await self.user_repo.create_user(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            auth_provider="google",
            google_sub=str(token_payload.get("sub") or "") or None,
        )

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

    async def request_password_reset(self, email: str) -> bool:
        """Create and persist a password reset token for an existing account."""
        normalized_email = email.lower().strip()
        user = await self.user_repo.get_user_by_email(normalized_email)
        if not user:
            return False

        token = secrets.token_urlsafe(32)
        token_hash = self.hash_password(token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        await self.user_repo.set_password_reset_token(
            email=normalized_email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        sent = await asyncio.to_thread(
            self.email_service.send_password_reset_email,
            normalized_email,
            token,
        )
        if not sent:
            await self.user_repo.clear_password_reset_token(user["id"])
            return False
        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using a valid, non-expired reset token."""
        self.validate_password(new_password)
        token_hash = self.hash_password(token)
        user = await self.user_repo.get_user_by_password_reset_token(token_hash)
        if not user:
            return False

        expires_at = user.get("password_reset_expires_at")
        if not expires_at:
            await self.user_repo.clear_password_reset_token(user["id"])
            return False

        # Handle both timezone-aware and naive stored datetime values.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            await self.user_repo.clear_password_reset_token(user["id"])
            return False

        new_hash = self.hash_password(new_password)
        return await self.user_repo.set_password_hash(user["id"], new_hash)

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change password for an authenticated user after current password check."""
        self.validate_password(new_password)
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            return False

        if not self.verify_password(current_password, user.get("password_hash", "")):
            return False

        if current_password == new_password:
            raise ValueError("New password must be different from current password")

        new_hash = self.hash_password(new_password)
        return await self.user_repo.set_password_hash(user_id, new_hash)
