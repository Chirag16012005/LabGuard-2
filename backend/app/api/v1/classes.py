from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ...services.auth_service import AuthService
from ...services.class_service import ClassService

router = APIRouter()
class_service = ClassService()
auth_service = AuthService()
bearer_scheme = HTTPBearer()


class CreateClassRequest(BaseModel):
    name: str
    class_code: str
    description: str
    section: str | None = None
    semester: str | None = None


class JoinClassRequest(BaseModel):
    join_code: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: CreateClassRequest,
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

    teacher_id = token_payload.get("user_id") or token_payload.get("sub")
    role = token_payload.get("role")
    if not teacher_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not role:
        user = await auth_service.get_user(teacher_id)
        role = user.get("role") if user else None
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")

    if role not in {"teacher", "admin"}:
        raise HTTPException(status_code=403, detail="Only teacher can create class")

    try:
        class_doc = await class_service.create_class(
            name=payload.name,
            teacher_id=teacher_id,
            class_code=payload.class_code,
            description=payload.description,
            section=payload.section,
        )
        return {"message": "Class created", "data": {"class_id": class_doc["class_id"]}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create class")


@router.get("/", status_code=status.HTTP_200_OK)
async def list_my_classes(
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
    role = token_payload.get("role")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not role:
        user = await auth_service.get_user(user_id)
        role = user.get("role") if user else None
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")

    classes = await class_service.list_my_classes(user_id, role)
    return {"message": "Classes retrieved", "data": classes}


@router.get("/{class_id}", status_code=status.HTTP_200_OK)
async def get_class_details(class_id: str) -> dict:
    class_doc = await class_service.get_class(class_id)
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class retrieved", "data": class_doc}


@router.delete("/{class_id}", status_code=status.HTTP_200_OK)
async def delete_class(
    class_id: str,
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

    requester_id = token_payload.get("user_id") or token_payload.get("sub")
    role = token_payload.get("role")
    if not requester_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not role:
        requester = await auth_service.get_user(requester_id)
        role = requester.get("role") if requester else None
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")

    if role not in {"teacher", "admin"}:
        raise HTTPException(status_code=403, detail="Only teacher can delete class")

    class_doc = await class_service.get_class(class_id)
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    if role == "teacher" and class_doc.get("teacher_id") != requester_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this class"
        )

    success = await class_service.delete_class(class_id)
    if not success:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class deleted", "data": {"class_id": class_id}}


@router.post("/{class_id}/join", status_code=status.HTTP_200_OK)
async def join_class(
    class_id: str,
    payload: JoinClassRequest,
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

    student_id = token_payload.get("user_id") or token_payload.get("sub")
    if not student_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        success = await class_service.join_class(
            class_id, payload.join_code, student_id
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to join class")
        return {"message": "Joined class successfully", "data": {"class_id": class_id}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to join class")


@router.get("/{class_id}/students", status_code=status.HTTP_200_OK)
async def list_class_students(
    class_id: str,
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

    requester_id = token_payload.get("user_id") or token_payload.get("sub")
    role = token_payload.get("role")
    if not requester_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not role:
        requester = await auth_service.get_user(requester_id)
        role = requester.get("role") if requester else None
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")

    class_doc = await class_service.get_class(class_id)
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    # Allow access for admin, class teacher, or enrolled student.
    is_admin = role == "admin"
    is_teacher = class_doc.get("teacher_id") == requester_id
    is_enrolled_student = requester_id in class_doc.get("students", [])
    if not (is_admin or is_teacher or is_enrolled_student):
        raise HTTPException(
            status_code=403, detail="Not authorized to view class students"
        )

    students = await class_service.list_class_students(class_id)
    return {
        "message": "Students retrieved",
        "data": {"class_id": class_id, "students": students},
    }
