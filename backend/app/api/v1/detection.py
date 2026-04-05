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


@router.get("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_detection_job(job_id: str) -> dict:
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
