from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from ...services.document_management_service import DocumentManagementService
except ModuleNotFoundError:  # keep API importable even if service isn't present
    DocumentManagementService = None  # type: ignore[assignment]
from ...repositories.assignment_repository import AssignmentRepository
from ...repositories.class_repository import ClassRepository
from ...repositories.submission_repository import SubmissionRepository

router = APIRouter()
if DocumentManagementService is not None:
    doc_service = DocumentManagementService()
else:
    doc_service = None
bearer_scheme = HTTPBearer()
assignment_repo = AssignmentRepository()
submission_repo = SubmissionRepository()
class_repo = ClassRepository()


def _decode_token_payload(credentials: HTTPAuthorizationCredentials) -> dict:
    try:
        payload_segment = credentials.credentials.split(".")[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")


async def _get_requester_context(
    credentials: HTTPAuthorizationCredentials,
) -> tuple[str, str]:
    token_payload = _decode_token_payload(credentials)
    requester_id = token_payload.get("user_id") or token_payload.get("sub")
    role = token_payload.get("role")
    if not requester_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return requester_id, role or "student"


async def _can_access_document(document_id: str, requester_id: str, role: str) -> bool:
    """Check whether requester can access given document id."""
    if role == "admin":
        return True

    assignment = await assignment_repo.get_assignment_by_document_id(document_id)
    if assignment:
        class_doc = await class_repo.get_class_by_id(assignment.get("class_id", ""))
        if not class_doc:
            return False
        if role == "teacher":
            return class_doc.get("teacher_id") == requester_id
        if role == "student":
            return requester_id in class_doc.get("students", [])
        return False

    submission = await submission_repo.get_submission_by_document_id(document_id)
    if submission:
        if submission.get("student_id") == requester_id:
            return True
        if role == "teacher":
            assignment = await assignment_repo.get_assignment_by_id(
                submission.get("assignment_id", "")
            )
            if not assignment:
                return False
            class_doc = await class_repo.get_class_by_id(assignment.get("class_id", ""))
            return bool(class_doc and class_doc.get("teacher_id") == requester_id)
        return False

    # For standalone documents, only owner can access.
    return False


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    owner_id, _ = await _get_requester_context(credentials)

    try:
        content = await file.read()
        doc = await doc_service.upload_document(
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
            file_content=content,
            owner_id=owner_id,
        )
        return {"message": "Document uploaded", "data": {"document_id": doc["id"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    requester_id, role = await _get_requester_context(credentials)

    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("owner_id") != requester_id and not await _can_access_document(
        document_id,
        requester_id,
        role,
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this document"
        )
    return {"message": "Document retrieved", "data": doc}


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    requester_id, role = await _get_requester_context(credentials)

    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("owner_id") != requester_id and role != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this document"
        )

    success = await doc_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")
    return {"message": "Document deleted", "data": {"document_id": document_id}}


@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_document(
    document_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Response:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    requester_id, role = await _get_requester_context(credentials)

    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("owner_id") != requester_id and not await _can_access_document(
        document_id,
        requester_id,
        role,
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to download this document"
        )

    content = await doc_service.get_document_binary_content(document_id)
    if not content:
        raise HTTPException(status_code=500, detail="Document content not available")

    filename = Path(doc.get("filename", "document")).name
    media_type = doc.get("content_type") or "application/octet-stream"

    response = Response(content=content, media_type=media_type)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


__all__ = ["router"]
