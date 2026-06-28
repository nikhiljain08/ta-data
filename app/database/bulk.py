"""Bulk upsert helper for PostgreSQL.

Uses INSERT … ON CONFLICT DO UPDATE (PostgreSQL "upsert"), which is a single
round-trip and handles concurrent writers without read-modify-write races.

Design
------
* Callers pass a flat list of dicts — one per record.
* `conflict_columns` must match a UNIQUE constraint on the table.
* `update_columns` lists every column that should be refreshed on conflict.
  Typically all non-PK, non-conflict columns including `synced_at`.
* Returns the number of rows touched (inserted + updated).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.db.base import Base


def bulk_upsert(
    session: Session,
    model: type[Base],
    rows: Sequence[dict[str, Any]],
    *,
    conflict_columns: list[str],
    update_columns: list[str],
) -> int:
    """Upsert *rows* into *model*'s table.

    Empty batch is a no-op; callers do not need to guard against it.
    Returns the number of rows processed (inserted or updated).
    """
    if not rows:
        return 0

    stmt = insert(model).values(list(rows))  # type: ignore[arg-type]
    update_dict = {col: getattr(stmt.excluded, col) for col in update_columns}
    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_=update_dict,
    )
    result = session.execute(stmt)
    # rowcount is -1 for INSERT … ON CONFLICT when no row is returned;
    # return len(rows) as the number of records submitted instead.
    return result.rowcount if result.rowcount >= 0 else len(rows)
