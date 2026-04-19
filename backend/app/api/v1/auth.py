from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, field_validator

from ...db.schemas.auth_schema import UserRole
from ...services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()
bearer_scheme = HTTPBearer()
revoked_tokens: set[str] = set()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        AuthService.validate_password(value)
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str
    role: str = "student"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        AuthService.validate_password(value)
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        AuthService.validate_password(value)
        return value


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> dict:
    try:
        user = await auth_service.register_user(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role=UserRole(payload.role),
        )
        token = auth_service.generate_token(
            user["id"],
            user["email"],
            user.get("role"),
        )
        return {
            "message": "User registered successfully",
            "data": {
                "user_id": user["id"],
                "email": user["email"],
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user.get("full_name"),
                    "role": user.get("role"),
                },
                "access_token": token,
                "token_type": "bearer",
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest) -> dict:
    user = await auth_service.login_user(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth_service.generate_token(
        user["id"],
        user["email"],
        user.get("role"),
    )
    return {
        "message": "Login successful",
        "data": {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "role": user.get("role"),
            },
            "access_token": token,
            "token_type": "bearer",
        },
    }


@router.post("/google-login", status_code=status.HTTP_200_OK)
async def google_login(payload: GoogleLoginRequest) -> dict:
    try:
        user = await auth_service.login_with_google(
            google_token=payload.id_token,
            role=UserRole(payload.role),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not user:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    token = auth_service.generate_token(
        user["id"],
        user["email"],
        user.get("role"),
    )
    return {
        "message": "Google login successful",
        "data": {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "role": user.get("role"),
            },
            "access_token": token,
            "token_type": "bearer",
        },
    }


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        token = credentials.credentials
        if token in revoked_tokens:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        try:
            payload_segment = token.split(".")[1]
            payload_segment += "=" * (-len(payload_segment) % 4)
            payload = json.loads(
                base64.urlsafe_b64decode(payload_segment).decode("utf-8")
            )
        except (IndexError, ValueError, json.JSONDecodeError):
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await auth_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Format user response, excluding password_hash
        user_data = {
            "id": user.get("id") or str(user.get("_id")),
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": user.get("role"),
        }

        return {
            "message": "Current user retrieved successfully",
            "data": {"user": user_data},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve user information"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    revoked_tokens.add(credentials.credentials)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(payload: ForgotPasswordRequest) -> dict:
    # Intentionally return the same response for unknown emails to avoid user enumeration.
    await auth_service.request_password_reset(payload.email)
    return {
        "message": "If an account exists, a password reset link has been sent",
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest) -> dict:
    success = await auth_service.reset_password(payload.token, payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password reset successful"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload_segment = credentials.credentials.split(".")[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        token_payload = json.loads(
            base64.urlsafe_b64decode(payload_segment).decode("utf-8")
        )
    except (IndexError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = token_payload.get("user_id") or token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        success = await auth_service.change_password(
            user_id=user_id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not success:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    revoked_tokens.add(credentials.credentials)
    return {
        "message": "Password changed successfully. Please login again.",
        "data": {"logged_out": True},
    }
