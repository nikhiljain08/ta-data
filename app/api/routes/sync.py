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


class EntityTriggerResponse(BaseModel):
    message: str
    entity: str


def _get_engine() -> SyncEngine:  # pragma: no cover
    raise HTTPException(status_code=503, detail="Sync engine not configured")


def _get_company() -> str:  # pragma: no cover
    raise HTTPException(status_code=503, detail="Company not configured")


@router.get("/entity/{entity}", response_model=EntityTriggerResponse)
def trigger_entity_sync(
    entity: str,
    background_tasks: BackgroundTasks,
    engine: SyncEngine = Depends(_get_engine),
    company: str = Depends(_get_company),
) -> EntityTriggerResponse:
    """Enqueue an immediate incremental sync for one entity.

    Called by TDL event triggers ($$HTTPGET) on every Tally save/delete.
    Returns instantly; sync runs in the background.
    """
    background_tasks.add_task(engine.sync_entity, company, entity)
    return EntityTriggerResponse(message="Entity sync enqueued", entity=entity)


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
