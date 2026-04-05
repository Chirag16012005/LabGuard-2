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


def _decode_token_payload(credentials: HTTPAuthorizationCredentials) -> dict:
    try:
        payload_segment = credentials.credentials.split(".")[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


async def _get_requester_context(
    credentials: HTTPAuthorizationCredentials,
) -> tuple[str, str]:
    token_payload = _decode_token_payload(credentials)
    requester_id = token_payload.get("user_id") or token_payload.get("sub")
    role = token_payload.get("role")
    if not requester_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not role:
        requester = await auth_service.get_user(requester_id)
        role = requester.get("role") if requester else None
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")

    return requester_id, role


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
    teacher_id, role = await _get_requester_context(credentials)
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
    token_payload = _decode_token_payload(credentials)
    user_id = token_payload.get("user_id") or token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    classes = await class_service.list_my_classes(user_id)
    return {"message": "Classes retrieved", "data": classes}


@router.post("/join", status_code=status.HTTP_200_OK)
async def join_class_by_code(
    payload: JoinClassRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Join a class using only the join code (no class_id needed)."""
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
        result = await class_service.join_class_by_code(payload.join_code, student_id)
        return {"message": "Joined class successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to join class")


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
    requester_id, role = await _get_requester_context(credentials)
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


@router.delete("/{class_id}/leave", status_code=status.HTTP_200_OK)
async def leave_class(
    class_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    student_id, role = await _get_requester_context(credentials)
    if role != "student":
        raise HTTPException(status_code=403, detail="Only students can leave class")

    try:
        success = await class_service.leave_class(class_id, student_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to leave class")
        return {"message": "Left class successfully", "data": {"class_id": class_id}}
    except ValueError as e:
        detail = str(e)
        if detail == "Class not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to leave class")


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
    if not requester_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    class_doc = await class_service.get_class(class_id)
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    students = await class_service.list_class_students(class_id)
    return {
        "message": "Students retrieved",
        "data": {"class_id": class_id, "students": students},
    }
