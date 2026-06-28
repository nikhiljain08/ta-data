"""Tests for TallyHealthChecker."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.client.tally_health import TallyHealth, TallyHealthChecker
from tests.mock_tally.server import EMPTY_RESPONSE, PING_OK_RESPONSE, MockTallyServer


class TestTallyHealth:
    def test_str_alive(self) -> None:
        h = TallyHealth(is_alive=True, checked_at=datetime.now(), response_ms=12.5)
        assert "OK" in str(h)
        assert "12" in str(h)

    def test_str_dead(self) -> None:
        h = TallyHealth(is_alive=False, checked_at=datetime.now(), error="timeout")
        assert "UNREACHABLE" in str(h)
        assert "timeout" in str(h)


class TestTallyHealthChecker:
    def test_alive_when_tally_responds(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        checker = TallyHealthChecker(settings=mock_tally.tally_settings())
        health = checker.check()
        assert health.is_alive is True
        assert health.response_ms is not None
        assert health.response_ms >= 0

    def test_not_alive_when_empty_response(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(EMPTY_RESPONSE)
        checker = TallyHealthChecker(settings=mock_tally.tally_settings())
        health = checker.check()
        assert health.is_alive is False

    def test_not_alive_when_port_closed(self) -> None:
        from app.config.settings import TallySettings

        settings = TallySettings(host="127.0.0.1", port=19998, timeout_seconds=1)
        checker = TallyHealthChecker(settings=settings)
        health = checker.check()
        assert health.is_alive is False
        assert health.error is not None

    def test_result_is_cached(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        checker = TallyHealthChecker(
            settings=mock_tally.tally_settings(), cache_ttl_seconds=60.0
        )
        h1 = checker.check()
        # Queue a different response — cached result should be returned instead
        mock_tally.set_response(EMPTY_RESPONSE)
        h2 = checker.check()
        assert h1 is h2  # same object from cache
        assert mock_tally.request_count == 1

    def test_force_bypasses_cache(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        checker = TallyHealthChecker(
            settings=mock_tally.tally_settings(), cache_ttl_seconds=60.0
        )
        checker.check()
        mock_tally.set_response(EMPTY_RESPONSE)
        h2 = checker.check(force=True)
        assert h2.is_alive is False
        assert mock_tally.request_count == 2

    def test_invalidate_clears_cache(self, mock_tally: MockTallyServer) -> None:
        mock_tally.set_response(PING_OK_RESPONSE)
        checker = TallyHealthChecker(
            settings=mock_tally.tally_settings(), cache_ttl_seconds=60.0
        )
        h1 = checker.check()
        checker.invalidate()
        mock_tally.set_response(EMPTY_RESPONSE)
        h2 = checker.check()
        assert h1 is not h2
        assert h2.is_alive is False
