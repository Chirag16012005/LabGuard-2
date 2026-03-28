from __future__ import annotations

from pymongo import ASCENDING

from .mongodb import get_database


async def ensure_indexes() -> None:
    """Create indexes required by core collections."""
    db = get_database()

    await db["documents"].create_index(
        [("id", ASCENDING)], unique=True, name="documents_id_unique"
    )
    await db["reports"].create_index(
        [("report_id", ASCENDING)], unique=True, name="reports_report_id_unique"
    )
    await db["reports"].create_index(
        [("created_at", ASCENDING)], name="reports_created_at_idx"
    )
