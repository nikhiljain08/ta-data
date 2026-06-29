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

# PostgreSQL hard limit is 65,535 parameters per query.
# 500 rows x up to 130 columns stays well within that ceiling for all our models.
_CHUNK_SIZE = 500


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
    Large batches are automatically split into chunks of _CHUNK_SIZE rows to
    stay under PostgreSQL's 65,535-parameter-per-query limit.
    Returns the number of rows processed (inserted or updated).
    """
    if not rows:
        return 0

    total = 0
    row_list = list(rows)
    for i in range(0, len(row_list), _CHUNK_SIZE):
        chunk = row_list[i : i + _CHUNK_SIZE]
        stmt = insert(model).values(chunk)  # type: ignore[arg-type]
        update_dict = {col: getattr(stmt.excluded, col) for col in update_columns}
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=update_dict,
        )
        result = session.execute(stmt)
        total += result.rowcount if result.rowcount >= 0 else len(chunk)
    return total
