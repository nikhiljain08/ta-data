"""Root conftest — shared fixtures for all test layers."""

from __future__ import annotations

import pytest

from app.config.settings import Settings
from tests.mock_tally.server import MockTallyServer


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Minimal settings for unit tests — no real DB or Tally required."""
    return Settings(
        tally={"host": "localhost", "port": 9000, "timeout_seconds": 5},
        database={"url": "sqlite+aiosqlite:///:memory:", "echo_sql": False},
        sync={"batch_size": 10, "bulk_insert_size": 10},
        security={"use_keyring": False},
    )


@pytest.fixture()
def mock_tally() -> MockTallyServer:  # type: ignore[misc]
    """Start a mock Tally HTTP server for the duration of one test."""
    with MockTallyServer() as server:
        yield server
