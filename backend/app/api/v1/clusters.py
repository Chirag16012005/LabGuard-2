from __future__ import annotations

import base64
import json

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...services.cluster_service import ClusteringService

router = APIRouter()
clustering_service = ClusteringService()
bearer_scheme = HTTPBearer()


@router.get("/assignments/{assignment_id}/clusters", status_code=status.HTTP_200_OK)
async def get_assignment_clusters(
    assignment_id: str,
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

    if not assignment_id or not assignment_id.strip():
        raise HTTPException(status_code=400, detail="Assignment ID is required")

    try:
        result = await clustering_service.get_assignment_clusters(assignment_id)
        return {"message": "Clusters retrieved", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve clusters")
