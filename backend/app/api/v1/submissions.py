from __future__ import annotations

import base64
import json
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...services.auth_service import AuthService
from ...services.assignment_service import AssignmentService
from ...services.class_service import ClassService
from ...services.document_management_service import DocumentManagementService
from ...services.submission_service import SubmissionService
<<<<<<< HEAD
from ...db.schemas.submission_schema import (
    SubmissionSummary,
    AssignmentSubmissionsResponse,
)
=======
>>>>>>> upstream/main

router = APIRouter()
submission_service = SubmissionService()
auth_service = AuthService()
assignment_service = AssignmentService()
class_service = ClassService()
document_service = DocumentManagementService()
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


@router.post("/assignments/{assignment_id}/submit", status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: str,
    file: Annotated[UploadFile, File(...)],
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token_payload = _decode_token_payload(credentials)
    student_id = token_payload.get("user_id") or token_payload.get("sub")
    if not student_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    assignment = await assignment_service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    class_doc = await class_service.get_class(assignment.get("class_id", ""))
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    if student_id not in class_doc.get("students", []):
        raise HTTPException(
            status_code=403,
            detail="You have to first join class then can submit the assignment",
        )

    due_date_raw = assignment.get("due_date")
    if due_date_raw:
        try:
            due_date_str = str(due_date_raw).strip()
            # Support both date-only and datetime formats.
            if len(due_date_str) == 10:
                due_dt = datetime.fromisoformat(due_date_str + "T23:59:59")
            else:
                due_dt = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) > due_dt.astimezone(timezone.utc):
                raise HTTPException(
                    status_code=403,
                    detail="Submission deadline has passed",
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid assignment due_date format")

    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Submission file is required")

        doc = await document_service.upload_document(
            filename=file.filename or "submission",
            content_type=file.content_type or "application/octet-stream",
            file_content=file_content,
            owner_id=student_id,
        )

        submission = await submission_service.submit_assignment(
            assignment_id=assignment_id,
            student_id=student_id,
            document_id=doc["id"],
        )
<<<<<<< HEAD
        
        validated = SubmissionSummary.model_validate(submission)
        return {
            "message": "Submission created",
            "data": {
                "submission_id": validated.id,
                "submission": validated.model_dump()
            }
        }
=======
        return {"message": "Submission created", "data": {"submission_id": submission["id"]}}
>>>>>>> upstream/main
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Submission failed")


@router.get("/assignments/{assignment_id}/submissions", status_code=status.HTTP_200_OK)
<<<<<<< HEAD
async def list_submissions(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    requester_id, role = await _get_requester_context(credentials)
    
    assignment = await assignment_service.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    class_doc = await class_service.get_class(assignment["class_id"])
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
        
    if class_doc.get("teacher_id") != requester_id and role != "admin":
        raise HTTPException(status_code=403, detail="Only the class teacher can view submissions")

    submissions = await submission_service.list_submissions(assignment_id)
    validated = [SubmissionSummary.model_validate(s).model_dump() for s in submissions]
    return {
        "message": "Submissions retrieved",
        "data": {
            "assignment_id": assignment_id,
            "submissions": validated
        }
    }


@router.get("/assignments/{assignment_id}/my-submission", status_code=status.HTTP_200_OK)
async def get_my_submission(
    assignment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    student_id, _ = await _get_requester_context(credentials)
    
    submission = await submission_service.get_student_submission(assignment_id, student_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    validated = SubmissionSummary.model_validate(submission)
    return {
        "message": "Submission retrieved",
        "data": validated.model_dump()
    }


@router.get("/submissions/{submission_id}", status_code=status.HTTP_200_OK)
async def get_submission(
    submission_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    # Need auth to ensure requester is teacher or owner
    requester_id, role = await _get_requester_context(credentials)
    
    submission = await submission_service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    # Check if owner or teacher
    assignment = await assignment_service.get_assignment(submission["assignment_id"])
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    class_doc = await class_service.get_class(assignment["class_id"])
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    is_owner = submission["student_id"] == requester_id
    is_teacher = class_doc["teacher_id"] == requester_id
    
    if not (is_owner or is_teacher or role == "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view this submission")

    validated = SubmissionSummary.model_validate(submission)
    return {"message": "Submission retrieved", "data": validated.model_dump()}
=======
async def list_submissions(assignment_id: str) -> dict:
    submissions = await submission_service.list_submissions(assignment_id)
    return {"message": "Submissions retrieved", "data": submissions}


@router.get("/submissions/{submission_id}", status_code=status.HTTP_200_OK)
async def get_submission(submission_id: str) -> dict:
    submission = await submission_service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Submission retrieved", "data": submission}
>>>>>>> upstream/main


@router.delete("/submissions/{submission_id}", status_code=status.HTTP_200_OK)
async def delete_submission(
    submission_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
<<<<<<< HEAD
    requester_id, role = await _get_requester_context(credentials)
=======
    token_payload = _decode_token_payload(credentials)
    requester_id = token_payload.get("user_id") or token_payload.get("sub")
>>>>>>> upstream/main
    if not requester_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    submission = await submission_service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # No role-based checks: submission owner can delete only before due date.
<<<<<<< HEAD
    if submission.get("student_id") != requester_id and role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this submission")

    if role != "admin":
        assignment = await assignment_service.get_assignment(submission.get("assignment_id", ""))
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        due_date_raw = assignment.get("due_date")
        if due_date_raw:
            try:
                due_date_str = str(due_date_raw).strip()
                # Support both date-only and datetime formats.
                if len(due_date_str) == 10:
                    due_dt = datetime.fromisoformat(due_date_str + "T23:59:59")
                else:
                    due_dt = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) > due_dt.astimezone(timezone.utc):
                    raise HTTPException(
                        status_code=403,
                        detail="Submission can be deleted only before due date",
                    )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid assignment due_date format")
=======
    if submission.get("student_id") != requester_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this submission")

    assignment = await assignment_service.get_assignment(submission.get("assignment_id", ""))
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    due_date_raw = assignment.get("due_date")
    if due_date_raw:
        try:
            due_date_str = str(due_date_raw).strip()
            # Support both date-only and datetime formats.
            if len(due_date_str) == 10:
                due_dt = datetime.fromisoformat(due_date_str + "T23:59:59")
            else:
                due_dt = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) > due_dt.astimezone(timezone.utc):
                raise HTTPException(
                    status_code=403,
                    detail="Submission can be deleted only before due date",
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid assignment due_date format")
>>>>>>> upstream/main

    success = await submission_service.delete_submission(submission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Submission deleted", "data": {"submission_id": submission_id}}
