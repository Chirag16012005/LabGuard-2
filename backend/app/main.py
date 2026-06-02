from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .api.router import router as api_router
from .core.settings import get_settings
from .core.logging import setup_logging
from .db.indexes import ensure_indexes
from .db.mongodb import close_mongo_connection, connect_to_mongo

# Initialize logging at module load time
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name)

# Configure CORS
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # local Next.js dev
    allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - returns API documentation."""
    logger.debug("Root endpoint accessed")
    return JSONResponse({
        "message": "Plagiarism Detection API",
        "version": "1.0.0",
        "documentation": "http://127.0.0.1:8001/docs",
        "openapi": "http://127.0.0.1:8001/openapi.json",
        "api_base": "/api/v1",
    })


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Handle favicon requests to prevent 404 errors."""
    return Response(status_code=204)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Application startup event triggered")
    await connect_to_mongo()
    logger.info("MongoDB connection established")
    await ensure_indexes()
    logger.info("Database indexes ensured")
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Application shutdown event triggered")
    close_mongo_connection()
    logger.info("MongoDB connection closed")
