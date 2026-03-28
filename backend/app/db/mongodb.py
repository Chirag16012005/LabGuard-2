from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..core.settings import get_settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB client and verify connectivity."""
    global _client, _database

    if _client is not None and _database is not None:
        return

    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    await _client.admin.command("ping")
    _database = _client[settings.mongodb_db_name]


def close_mongo_connection() -> None:
    """Close MongoDB client gracefully."""
    global _client, _database

    if _client is not None:
        _client.close()

    _client = None
    _database = None


def get_database() -> AsyncIOMotorDatabase:
    """Return active MongoDB database handle."""
    if _database is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongo() first.")
    return _database
