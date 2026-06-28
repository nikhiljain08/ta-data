"""Tally connectivity health checker with short-lived result cache.

Usage
-----
    checker = TallyHealthChecker(settings.tally)
    health = checker.check()
    if not health.is_alive:
        logger.error("Tally is not responding", error=health.error)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

from app.client.tally_client import TallyClient
from app.config.settings import TallySettings


@dataclass(frozen=True)
class TallyHealth:
    """Point-in-time snapshot of Tally connectivity."""

    is_alive: bool
    checked_at: datetime
    response_ms: float | None = None
    error: str | None = None

    def __str__(self) -> str:
        if self.is_alive:
            return f"Tally OK ({self.response_ms:.0f} ms)"
        return f"Tally UNREACHABLE — {self.error or 'unknown error'}"


@dataclass
class TallyHealthChecker:
    """Checks Tally connectivity and caches the most recent result.

    Cache TTL prevents hammering Tally with health pings during rapid
    status queries (e.g. API polling).  Use force=True to bypass the cache.
    """

    settings: TallySettings
    cache_ttl_seconds: float = 10.0

    _cached: TallyHealth | None = field(default=None, init=False, repr=False)
    _cache_ts: float = field(default=0.0, init=False, repr=False)

    def check(self, *, force: bool = False) -> TallyHealth:
        """Return the current health status, using cache if still fresh."""
        now = time.monotonic()
        if (
            not force
            and self._cached is not None
            and (now - self._cache_ts) < self.cache_ttl_seconds
        ):
            return self._cached

        result = self._probe()
        self._cached = result
        self._cache_ts = now

        if result.is_alive:
            logger.debug("Tally health check passed", response_ms=result.response_ms)
        else:
            logger.warning("Tally health check failed", error=result.error)

        return result

    def invalidate(self) -> None:
        """Clear the cache so the next check() always probes Tally."""
        self._cached = None
        self._cache_ts = 0.0

    # ── Internal ──────────────────────────────────────────────────────────────

    def _probe(self) -> TallyHealth:
        t0 = time.perf_counter()
        try:
            with TallyClient(self.settings) as client:
                alive = client.is_alive(timeout=5.0)
            response_ms = (time.perf_counter() - t0) * 1000
            return TallyHealth(
                is_alive=alive,
                checked_at=datetime.now(),
                response_ms=round(response_ms, 1),
                error=None if alive else "Empty or no response from Tally",
            )
        except Exception as exc:
            return TallyHealth(
                is_alive=False,
                checked_at=datetime.now(),
                response_ms=None,
                error=str(exc),
            )
