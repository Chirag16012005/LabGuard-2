from __future__ import annotations

from pydantic import Field

from .base_schema import APIModel


class ClusterMember(APIModel):
    submission_id: str
    student_id: str
    similarity_to_centroid: float = Field(ge=0.0, le=1.0)


class SimilarityCluster(APIModel):
    cluster_id: str
    centroid_submission_id: str
    mean_similarity: float = Field(ge=0.0, le=1.0)
    members: list[ClusterMember]


class AssignmentClustersResponse(APIModel):
    assignment_id: str
    clusters: list[SimilarityCluster]
