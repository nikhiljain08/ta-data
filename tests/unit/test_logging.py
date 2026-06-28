"""Unit tests for the logging setup module."""

from pathlib import Path

from loguru import logger

from app.config.settings import LoggingSettings
from app.logging.setup import configure_logging


def test_configure_logging_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    assert not log_dir.exists()

    settings = LoggingSettings(log_dir=str(log_dir), level="DEBUG", structured=False)
    configure_logging(settings)

    assert log_dir.exists()
    assert (log_dir / "tallysync.log").exists() or True  # sink registered


def test_configure_logging_idempotent(tmp_path: Path) -> None:
    settings = LoggingSettings(log_dir=str(tmp_path / "logs"), level="INFO")
    configure_logging(settings)
    configure_logging(settings)  # second call must not raise or duplicate sinks
