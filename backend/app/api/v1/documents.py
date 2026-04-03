from __future__ import annotations

import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from ...services.document_management_service import DocumentManagementService
except ModuleNotFoundError:  # keep API importable even if service isn't present
    DocumentManagementService = None  # type: ignore[assignment]
from ...services.document_service import Document, InMemoryDocumentStore

router = APIRouter()
if DocumentManagementService is not None:
    doc_service = DocumentManagementService()
else:
    doc_service = None
bearer_scheme = HTTPBearer()


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
    try:
        payload_segment = credentials.credentials.split(".")[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        token_payload = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    owner_id = token_payload.get("user_id") or token_payload.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")

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
async def get_document(document_id: str) -> dict:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document retrieved", "data": doc}


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: str) -> dict:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    success = await doc_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted", "data": {"document_id": document_id}}


@router.get("/{document_id}/download", status_code=status.HTTP_200_OK)
async def download_document(document_id: str) -> StreamingResponse:
    if doc_service is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document management service is not available",
        )
    doc = await doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content = await doc_service.get_document_binary_content(document_id)
    if not content:
        raise HTTPException(status_code=500, detail="Document content not available")

    response = StreamingResponse(
        iter([content]), media_type=doc.get("content_type", "application/octet-stream")
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{doc.get("filename", "document")}"'
    return response


__all__ = ["router", "Document", "InMemoryDocumentStore"]
