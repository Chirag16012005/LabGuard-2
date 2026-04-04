from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
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


class DetectionRunRequest(BaseModel):
    assignment_id: str


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_detection(payload: DetectionRunRequest) -> dict:
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


__all__ = ["router", "PlagiarismConfig", "PlagiarismDetector"]
