from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base_schema import APIModel


class DocumentType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    other = "other"


class DocumentUploadRequest(APIModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)
    size_bytes: int = Field(gt=0)


class DocumentMetadata(APIModel):
    id: str
    owner_id: str | None = None
    filename: str
    content_type: str
    document_type: DocumentType = DocumentType.other
    size_bytes: int = Field(ge=0)
    storage_path: str | None = None
    sha256: str | None = None
    created_at: datetime


class DocumentUploadResponse(APIModel):
    document: DocumentMetadata


class DocumentDownloadResponse(APIModel):
    document_id: str
    filename: str
    content_type: str
    download_url: str


class DocumentDeleteResponse(APIModel):
    message: str = "Document deleted"
    document_id: str
