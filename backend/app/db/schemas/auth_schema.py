from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import EmailStr, Field, SecretStr

from .base_schema import APIModel


class UserRole(str, Enum):
    teacher = "teacher"
    student = "student"
    admin = "admin"


class RegisterRequest(APIModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.student


class LoginRequest(APIModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)


class AuthTokens(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class UserPublic(APIModel):
    id: str = Field(description="User id")
    full_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class RegisterResponse(APIModel):
    user: UserPublic
    tokens: AuthTokens


class LoginResponse(APIModel):
    user: UserPublic
    tokens: AuthTokens


class MeResponse(APIModel):
    user: UserPublic


class LogoutResponse(APIModel):
    message: str = "Logged out successfully"
