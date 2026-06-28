from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import status as status_router
from app.api.routes import sync as sync_router


def build_api() -> FastAPI:
    """Create and configure the TallySync internal control API.

    Binds only to 127.0.0.1:8765 — never exposed to the network.
    """
    app = FastAPI(
        title="TallySync Control API",
        description="Internal control interface for the TallySync agent.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
    )

    app.include_router(status_router.router)
    app.include_router(sync_router.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
