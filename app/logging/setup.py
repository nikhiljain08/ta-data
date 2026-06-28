"""Structured logging via Loguru.

All other modules call `from loguru import logger` directly.
This module is the single place that configures sinks, format, and rotation.

Call configure_logging() once at startup before any other module logs.
"""

import sys
from pathlib import Path

from loguru import logger

from app.config.settings import LoggingSettings

_PLAIN_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
    "{extra}"
)

_JSON_FORMAT = (
    '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
    '"level":"{level}",'
    '"logger":"{name}",'
    '"function":"{function}",'
    '"line":{line},'
    '"message":"{message}"'
    "{extra}"
    "}}"
)


def configure_logging(settings: LoggingSettings) -> None:
    """Configure Loguru sinks from settings.  Safe to call multiple times."""
    logger.remove()

    fmt = _JSON_FORMAT if settings.structured else _PLAIN_FORMAT

    # Stderr sink — always present
    logger.add(
        sys.stderr,
        level=settings.level,
        format=_PLAIN_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Rotating file sink
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "tallysync.log",
        level=settings.level,
        format=fmt,
        rotation=settings.rotation,
        retention=settings.retention,
        compression="gz",
        encoding="utf-8",
        backtrace=True,
        diagnose=False,  # no variable values in prod logs (security)
    )

    # Separate error-only sink for quick triage
    logger.add(
        log_dir / "tallysync.error.log",
        level="ERROR",
        format=fmt,
        rotation=settings.rotation,
        retention=settings.retention,
        compression="gz",
        encoding="utf-8",
    )

    logger.info(
        "Logging configured",
        level=settings.level,
        structured=settings.structured,
        log_dir=str(log_dir.resolve()),
    )
