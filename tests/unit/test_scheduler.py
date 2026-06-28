"""Tests for app.scheduler.scheduler — TallySyncScheduler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestTallySyncScheduler:
    def test_builds_without_engine(self) -> None:
        from app.scheduler.scheduler import TallySyncScheduler

        with (
            patch("app.scheduler.scheduler._HAS_APSCHEDULER", True),
            patch("app.scheduler.scheduler.BackgroundScheduler") as mock_sched_cls,
        ):
            mock_sched_cls.return_value = MagicMock()
            sched = TallySyncScheduler(engine=None)
            assert sched._scheduler is not None

    def test_no_apscheduler_creates_stub(self) -> None:
        from app.scheduler.scheduler import TallySyncScheduler

        with patch("app.scheduler.scheduler._HAS_APSCHEDULER", False):
            sched = TallySyncScheduler()
            assert sched._scheduler is None

    def test_start_calls_scheduler_start(self) -> None:
        from app.scheduler.scheduler import TallySyncScheduler

        with (
            patch("app.scheduler.scheduler._HAS_APSCHEDULER", True),
            patch("app.scheduler.scheduler.BackgroundScheduler") as mock_sched_cls,
        ):
            mock_inner = MagicMock()
            mock_sched_cls.return_value = mock_inner
            sched = TallySyncScheduler()
            sched.start()
            mock_inner.start.assert_called_once()

    def test_shutdown_calls_scheduler_shutdown(self) -> None:
        from app.scheduler.scheduler import TallySyncScheduler

        with (
            patch("app.scheduler.scheduler._HAS_APSCHEDULER", True),
            patch("app.scheduler.scheduler.BackgroundScheduler") as mock_sched_cls,
        ):
            mock_inner = MagicMock()
            mock_sched_cls.return_value = mock_inner
            sched = TallySyncScheduler()
            sched.shutdown(wait=False)
            mock_inner.shutdown.assert_called_once_with(wait=False)

    def test_add_interval_job_no_scheduler_is_noop(self) -> None:
        from app.scheduler.scheduler import TallySyncScheduler

        with patch("app.scheduler.scheduler._HAS_APSCHEDULER", False):
            sched = TallySyncScheduler()
            # Must not raise
            sched.add_interval_job(lambda: None, minutes=15, job_id="test")

    def test_add_cron_job_invalid_cron_raises(self) -> None:
        import pytest

        from app.scheduler.scheduler import TallySyncScheduler

        with (
            patch("app.scheduler.scheduler._HAS_APSCHEDULER", True),
            patch("app.scheduler.scheduler.BackgroundScheduler") as mock_sched_cls,
        ):
            mock_sched_cls.return_value = MagicMock()
            sched = TallySyncScheduler()
            with pytest.raises(ValueError, match="5 fields"):
                sched.add_cron_job(lambda: None, cron="0 2 * *", job_id="bad")
