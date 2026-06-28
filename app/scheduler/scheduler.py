from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger

try:
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.schedulers.background import BackgroundScheduler

    _HAS_APSCHEDULER = True
except ImportError:  # pragma: no cover
    _HAS_APSCHEDULER = False


class TallySyncScheduler:
    """Wraps APScheduler's BackgroundScheduler for the TallySync agent.

    Jobs are persisted in PostgreSQL via SQLAlchemyJobStore so they survive
    process restarts.  If APScheduler is not installed, the scheduler is a
    no-op stub that logs a warning.
    """

    def __init__(self, engine: Any | None = None) -> None:
        self._scheduler: Any = None
        if _HAS_APSCHEDULER and engine is not None:
            jobstores = {"default": SQLAlchemyJobStore(engine=engine)}
            self._scheduler = BackgroundScheduler(jobstores=jobstores)
        elif _HAS_APSCHEDULER:
            self._scheduler = BackgroundScheduler()
        else:
            logger.warning("APScheduler not installed — scheduler is disabled")

    def start(self) -> None:
        if self._scheduler is not None:
            self._scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self, *, wait: bool = True) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler stopped")

    def add_interval_job(
        self,
        func: Callable[..., Any],
        *,
        minutes: int,
        job_id: str,
        replace_existing: bool = True,
        **kwargs: Any,
    ) -> None:
        """Schedule *func* to run every *minutes* minutes."""
        if self._scheduler is None:
            return
        self._scheduler.add_job(
            func,
            "interval",
            minutes=minutes,
            id=job_id,
            replace_existing=replace_existing,
            kwargs=kwargs,
        )
        logger.info("Interval job registered", job_id=job_id, interval_minutes=minutes)

    def add_cron_job(
        self,
        func: Callable[..., Any],
        *,
        cron: str,
        job_id: str,
        replace_existing: bool = True,
        **kwargs: Any,
    ) -> None:
        """Schedule *func* on a cron expression (e.g. '0 2 * * *')."""
        if self._scheduler is None:
            return
        parts = cron.split()
        if len(parts) != 5:
            raise ValueError(f"cron expression must have 5 fields, got: {cron!r}")
        minute, hour, day, month, day_of_week = parts
        self._scheduler.add_job(
            func,
            "cron",
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=job_id,
            replace_existing=replace_existing,
            kwargs=kwargs,
        )
        logger.info("Cron job registered", job_id=job_id, cron=cron)
