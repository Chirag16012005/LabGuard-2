from __future__ import annotations

from fastapi import APIRouter, status

from ...services.cluster_service import ClusteringService

router = APIRouter()
clustering_service = ClusteringService()


@router.get("/assignments/{assignment_id}/clusters", status_code=status.HTTP_200_OK)
async def get_assignment_clusters(assignment_id: str) -> dict:
    result = await clustering_service.get_assignment_clusters(assignment_id)
    return {"message": "Clusters retrieved", "data": result}
