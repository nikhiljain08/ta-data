from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from app.client.tally_health import TallyHealthChecker
from app.models.db.sync_state import SyncCheckpointModel, SyncRunModel

router = APIRouter(prefix="/status", tags=["status"])


class CheckpointInfo(BaseModel):
    company_name: str
    entity_type: str
    last_alter_id: int
    last_synced_at: str | None


class LastRunInfo(BaseModel):
    company_name: str
    entity_type: str
    status: str
    records_synced: int
    started_at: str
    error_message: str | None


class StatusResponse(BaseModel):
    tally_alive: bool
    tally_error: str | None
    checkpoints: list[CheckpointInfo]
    last_runs: list[LastRunInfo]


def _get_session(session_factory: sessionmaker[Session]) -> Session:  # pragma: no cover
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.get("", response_model=StatusResponse)
def get_status(
    health: TallyHealthChecker = Depends(),
    session_factory: sessionmaker[Session] = Depends(),
) -> StatusResponse:
    """Return Tally health and current sync checkpoint state."""
    h = health.check()
    with session_factory() as session:  # type: ignore[attr-defined]
        checkpoints = session.query(SyncCheckpointModel).all()
        last_runs = (
            session.query(SyncRunModel).order_by(SyncRunModel.started_at.desc()).limit(50).all()
        )
    return StatusResponse(
        tally_alive=h.is_alive,
        tally_error=h.error,
        checkpoints=[
            CheckpointInfo(
                company_name=cp.company_name,
                entity_type=cp.entity_type,
                last_alter_id=cp.last_alter_id,
                last_synced_at=cp.last_synced_at.isoformat() if cp.last_synced_at else None,
            )
            for cp in checkpoints
        ],
        last_runs=[
            LastRunInfo(
                company_name=run.company_name,
                entity_type=run.entity_type,
                status=run.status,
                records_synced=run.records_synced,
                started_at=run.started_at.isoformat(),
                error_message=run.error_message,
            )
            for run in last_runs
        ],
    )
