from __future__ import annotations

from fastapi import APIRouter

from .v1 import (
    assignments,
    auth,
    classes,
    clusters,
    detection,
    documents,
    reports,
    submissions,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(classes.router, prefix="/classes", tags=["Classes"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(submissions.router, tags=["Submissions"])
router.include_router(detection.router, prefix="/detection", tags=["Detection"])
router.include_router(assignments.router, tags=["Assignments"])
router.include_router(reports.router, tags=["Reports"])
router.include_router(clusters.router, tags=["Clusters"])
