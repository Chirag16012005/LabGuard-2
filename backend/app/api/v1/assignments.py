from __future__ import annotations

import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...db.schemas.assignment_schema import (
    AssignmentDetails,
    AssignmentSummary,
)
from ...services.auth_service import AuthService
from ...services.assignment_service import AssignmentService
from ...services.class_service import ClassService

router = APIRouter()
assignment_service = AssignmentService()
auth_service = AuthService()
class_service = ClassService()
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


# ---------------------------------------------------------------------------
# POST /classes/{class_id}/assignments — Teacher creates an assignment
# ---------------------------------------------------------------------------
@router.post("/classes/{class_id}/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(
    class_id: str,
    file: Annotated[UploadFile, File(...)],
    description: Annotated[str | None, Form()] = None,
    due_date: Annotated[str | None, Form()] = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    requester_id, role = await _get_requester_context(credentials)

    if role not in {"teacher", "admin"}:
        raise HTTPException(
            status_code=403, detail="Only teachers can create assignments"
        )

    class_doc = await class_service.get_class(class_id)
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    if role == "teacher" and class_doc.get("teacher_id") != requester_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to create assignments for this class",
        )

    try:
        content = await file.read()
        raw = await assignment_service.create_assignment(
            class_id=class_id,
            filename=file.filename or "assignment",
            content_type=file.content_type or "application/octet-stream",
            file_content=content,
            teacher_id=requester_id,
            description=description,
            due_date=due_date,
        )
        # Validate via Pydantic, then return in the standard envelope
        assignment = AssignmentDetails.model_validate(raw)
        return {
            "message": "Assignment created",
            "data": {"assignment": assignment.model_dump()},
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create assignment")


# ---------------------------------------------------------------------------
# GET /classes/{class_id}/assignments — List assignments (teacher or enrolled student)
# ---------------------------------------------------------------------------
@router.get("/classes/{class_id}/assignments", status_code=status.HTTP_200_OK)
async def list_assignments(
    class_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    requester_id, role = await _get_requester_context(credentials)

    class_doc = await class_service.get_class(class_id)
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    is_teacher = class_doc.get("teacher_id") == requester_id
    is_student = requester_id in class_doc.get("students", [])

    if not (is_teacher or is_student or role == "admin"):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view assignments for this class",
        )

    raw_assignments = await assignment_service.list_assignments(class_id)
    # Validate each via Pydantic — raises if data is bad, strips unknown fields
    validated = [AssignmentSummary.model_validate(a).model_dump() for a in raw_assignments]
    return {
        "message": "Assignments retrieved",
        "data": {"class_id": class_id, "assignments": validated},
    }


# ---------------------------------------------------------------------------
# GET /assignments/{assignment_id} — Get single assignment (SECURED)
# ---------------------------------------------------------------------------
@router.get("/assignments/{assignment_id}", status_code=status.HTTP_200_OK)
async def get_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    requester_id, role = await _get_requester_context(credentials)

    raw = await assignment_service.get_assignment(assignment_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify the requester belongs to the assignment's class
    class_doc = await class_service.get_class(raw["class_id"])
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    is_teacher = class_doc.get("teacher_id") == requester_id
    is_student = requester_id in class_doc.get("students", [])

    if not (is_teacher or is_student or role == "admin"):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this assignment",
        )

    assignment = AssignmentDetails.model_validate(raw)
    return {
        "message": "Assignment retrieved",
        "data": {"assignment": assignment.model_dump()},
    }


# ---------------------------------------------------------------------------
# DELETE /assignments/{assignment_id} — Teacher deletes assignment
# ---------------------------------------------------------------------------
@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_200_OK)
async def delete_assignment(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    requester_id, role = await _get_requester_context(credentials)
    if role not in {"teacher", "admin"}:
        raise HTTPException(
            status_code=403, detail="Only teachers can delete assignments"
        )

    raw = await assignment_service.get_assignment(assignment_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Teacher can only delete their own class's assignments
    if role == "teacher":
        class_doc = await class_service.get_class(raw["class_id"])
        if not class_doc or class_doc.get("teacher_id") != requester_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this assignment",
            )

    success = await assignment_service.delete_assignment(assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Assignment deleted", "data": {"assignment_id": assignment_id}}
