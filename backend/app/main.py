from __future__ import annotations

from fastapi import FastAPI

from .api.router import router as api_router
from .core.settings import get_settings
from .db.indexes import ensure_indexes
from .db.mongodb import close_mongo_connection, connect_to_mongo

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    await connect_to_mongo()
    await ensure_indexes()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    close_mongo_connection()
