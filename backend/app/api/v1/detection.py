from __future__ import annotations

import base64
import json

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ...services.detection_service import PlagiarismConfig, PlagiarismDetector
try:
    from ...services.detection_orchestration_service import DetectionOrchestrationService
except ModuleNotFoundError:  # keep API importable even if orchestration isn't present
    DetectionOrchestrationService = None  # type: ignore[assignment]

router = APIRouter()
if DetectionOrchestrationService is not None:
    detection_service = DetectionOrchestrationService()
else:
    detection_service = None
    
bearer_scheme = HTTPBearer()

class DetectionRunRequest(BaseModel):
    assignment_id: str


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_detection(
    payload: DetectionRunRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload_segment = credentials.credentials.split(".")[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        token_payload = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    if not token_payload.get("user_id") and not token_payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        if detection_service is None:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Detection orchestration service is not available",
            )
        result = await detection_service.run_detection(payload.assignment_id)
        return {"message": "Detection started", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Detection failed")


@router.get("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_detection_job(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload_segment = credentials.credentials.split(".")[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        token_payload = json.loads(base64.urlsafe_b64decode(payload_segment).decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    if not token_payload.get("user_id") and not token_payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        result = await detection_service.get_detection_job_status(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="Detection job not found")
        return {"message": "Detection job retrieved", "data": result}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve detection job")


__all__ = ["router", "PlagiarismConfig", "PlagiarismDetector"]
