from __future__ import annotations

import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.db.sync_state import SyncCheckpointModel, SyncRunModel


class CheckpointRepository:
    """Reads and writes AlterID checkpoints and sync-run audit rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── AlterID checkpoints ───────────────────────────────────────────────────

    def get_alter_id(self, company_name: str, entity_type: str) -> int:
        """Return the last-seen AlterID for this entity, or 0 if never synced."""
        row = (
            self._session.query(SyncCheckpointModel)
            .filter_by(company_name=company_name, entity_type=entity_type)
            .first()
        )
        return row.last_alter_id if row else 0

    def save_alter_id(
        self,
        company_name: str,
        entity_type: str,
        alter_id: int,
    ) -> None:
        """Upsert the AlterID checkpoint for this (company, entity) pair."""
        now = datetime.datetime.now(tz=datetime.UTC)
        stmt = insert(SyncCheckpointModel).values(
            company_name=company_name,
            entity_type=entity_type,
            last_alter_id=alter_id,
            last_synced_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["company_name", "entity_type"],
            set_={"last_alter_id": alter_id, "last_synced_at": now},
        )
        self._session.execute(stmt)

    # ── Sync run audit log ────────────────────────────────────────────────────

    def start_run(self, company_name: str, entity_type: str) -> int:
        """Insert a new sync_run row and return its ID."""
        run = SyncRunModel(
            company_name=company_name,
            entity_type=entity_type,
            status="running",
        )
        self._session.add(run)
        self._session.flush()  # assigns PK without committing
        return run.id  # type: ignore[return-value]

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        records_synced: int = 0,
        error_message: str | None = None,
    ) -> None:
        """Mark a sync run as finished."""
        run = self._session.get(SyncRunModel, run_id)
        if run is None:
            return
        run.finished_at = datetime.datetime.now(tz=datetime.UTC)
        run.status = status
        run.records_synced = records_synced
        run.error_message = error_message
