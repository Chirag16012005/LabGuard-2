from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...services.detection_service import PlagiarismConfig, PlagiarismDetector
from ...services.detection_orchestration_service import DetectionOrchestrationService

router = APIRouter()
detection_service = DetectionOrchestrationService()


class DetectionRunRequest(BaseModel):
    assignment_id: str


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_detection(payload: DetectionRunRequest) -> dict:
    try:
        result = await detection_service.run_detection(payload.assignment_id)
        return {"message": "Detection started", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Detection failed")


__all__ = ["router", "PlagiarismConfig", "PlagiarismDetector"]
