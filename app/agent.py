"""Top-level Agent — wires together scheduler, sync engine, and control API.

Lifecycle
---------
Agent.start() blocks until interrupted (SIGINT/SIGTERM or SCM stop signal).
The Windows Service wrapper calls start() in a background thread and calls
stop() from the service's SvcStop handler.
"""

from __future__ import annotations

import threading

from loguru import logger

from app.config.settings import Settings


class Agent:
    """Composition root for the TallySync agent."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop_event = threading.Event()
        self._scheduler: object | None = None
        self._api_thread: threading.Thread | None = None

    def start(self) -> None:
        logger.info("TallySync agent starting", version="0.1.0")
        self._stop_event.clear()

        from app.client.tally_client import TallyClient
        from app.database.engine import build_engine
        from app.database.session import make_session_factory
        from app.scheduler.scheduler import TallySyncScheduler
        from app.services import (
            CompanySyncService,
            GodownSyncService,
            LedgerGroupSyncService,
            LedgerSyncService,
            StockGroupSyncService,
            StockItemSyncService,
            UnitSyncService,
            VoucherSyncService,
            VoucherTypeSyncService,
        )
        from app.sync.engine import SyncEngine
        from app.xml.template_engine import TemplateEngine

        engine = build_engine(self._settings.database, echo=self._settings.database.echo_sql)
        session_factory = make_session_factory(engine)
        template = TemplateEngine()

        with TallyClient(self._settings.tally) as client:
            svc_kwargs = {
                "client": client,
                "template": template,
                "session_factory": session_factory,
            }
            services: dict[str, object] = {
                "company": CompanySyncService(**svc_kwargs),
                "ledger_group": LedgerGroupSyncService(**svc_kwargs),
                "unit": UnitSyncService(**svc_kwargs),
                "stock_group": StockGroupSyncService(**svc_kwargs),
                "godown": GodownSyncService(**svc_kwargs),
                "voucher_type": VoucherTypeSyncService(**svc_kwargs),
                "stock_item": StockItemSyncService(**svc_kwargs),
                "ledger": LedgerSyncService(**svc_kwargs),
                "voucher": VoucherSyncService(
                    **svc_kwargs,
                    from_date=self._settings.sync.voucher_from_date,
                ),
            }
            sync_engine = SyncEngine(services, self._settings.sync.entity_order)

            self._scheduler = TallySyncScheduler()
            company = self._settings.tally.company_name

            self._scheduler.add_interval_job(  # type: ignore[attr-defined]
                sync_engine.sync,
                minutes=self._settings.sync.incremental_interval_minutes,
                job_id="incremental_sync",
                company_name=company,
                full=False,
            )
            self._scheduler.add_cron_job(  # type: ignore[attr-defined]
                sync_engine.sync,
                cron=self._settings.sync.full_sync_cron,
                job_id="full_sync",
                company_name=company,
                full=True,
            )
            self._scheduler.start()  # type: ignore[attr-defined]

            if self._settings.sync.full_sync_on_startup:
                logger.info("Running full sync on startup")
                sync_engine.sync(company, full=True)

            if self._settings.api.enabled:
                self._start_api()

            logger.info("Agent running — press Ctrl+C to stop")
            try:
                self._stop_event.wait()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()

    def _start_api(self) -> None:
        import uvicorn

        from app.api.app import build_api

        api = build_api()

        def _run() -> None:
            uvicorn.run(
                api,
                host=self._settings.api.host,
                port=self._settings.api.port,
                log_level="warning",
            )

        self._api_thread = threading.Thread(target=_run, daemon=True, name="tallysync-api")
        self._api_thread.start()
        logger.info(
            "Control API started",
            host=self._settings.api.host,
            port=self._settings.api.port,
        )

    def stop(self) -> None:
        logger.info("TallySync agent stopping")
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)  # type: ignore[attr-defined]
        self._stop_event.set()
