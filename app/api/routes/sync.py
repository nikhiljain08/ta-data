from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.sync.engine import SyncEngine, SyncResult

router = APIRouter(prefix="/sync", tags=["sync"])


class TriggerRequest(BaseModel):
    company_name: str
    full: bool = False


class TriggerResponse(BaseModel):
    message: str
    company_name: str
    mode: str


class SyncResultResponse(BaseModel):
    synced: dict[str, int]
    errors: dict[str, str]
    total_records: int


def _get_engine() -> SyncEngine:  # pragma: no cover
    raise HTTPException(status_code=503, detail="Sync engine not configured")


@router.post("/trigger", response_model=TriggerResponse)
def trigger_sync(
    body: TriggerRequest,
    background_tasks: BackgroundTasks,
    engine: SyncEngine = Depends(_get_engine),
) -> TriggerResponse:
    """Enqueue a sync run in the background and return immediately."""
    mode = "full" if body.full else "incremental"
    background_tasks.add_task(engine.sync, body.company_name, full=body.full)
    return TriggerResponse(
        message="Sync enqueued",
        company_name=body.company_name,
        mode=mode,
    )


@router.post("/run", response_model=SyncResultResponse)
def run_sync_blocking(
    body: TriggerRequest,
    engine: SyncEngine = Depends(_get_engine),
) -> SyncResultResponse:
    """Run a sync synchronously and return the result (useful for debugging)."""
    result: SyncResult = engine.sync(body.company_name, full=body.full)
    return SyncResultResponse(
        synced=result.synced,
        errors=result.errors,
        total_records=result.total_records,
    )
