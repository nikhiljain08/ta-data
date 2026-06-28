"""Tests for app.api — FastAPI control API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import build_api


class TestHealthEndpoint:
    def setup_method(self) -> None:
        self.client = TestClient(build_api())

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSyncTriggerEndpoint:
    def setup_method(self) -> None:
        self.app = build_api()
        self.client = TestClient(self.app)

    def test_trigger_without_engine_returns_503(self) -> None:
        response = self.client.post(
            "/sync/trigger",
            json={"company_name": "Acme", "full": False},
        )
        # Default dependency raises 503 when engine not configured
        assert response.status_code == 503

    def test_run_without_engine_returns_503(self) -> None:
        response = self.client.post(
            "/sync/run",
            json={"company_name": "Acme", "full": True},
        )
        assert response.status_code == 503

    def test_trigger_with_mock_engine(self) -> None:
        from unittest.mock import MagicMock

        from app.api.routes.sync import _get_engine
        from app.sync.engine import SyncEngine, SyncResult

        mock_engine = MagicMock(spec=SyncEngine)
        mock_engine.sync.return_value = SyncResult(synced={"company": 1})

        self.app.dependency_overrides[_get_engine] = lambda: mock_engine
        try:
            response = self.client.post(
                "/sync/trigger",
                json={"company_name": "Acme", "full": False},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["company_name"] == "Acme"
            assert body["mode"] == "incremental"
        finally:
            self.app.dependency_overrides.clear()

    def test_run_with_mock_engine_returns_result(self) -> None:
        from unittest.mock import MagicMock

        from app.api.routes.sync import _get_engine
        from app.sync.engine import SyncEngine, SyncResult

        mock_engine = MagicMock(spec=SyncEngine)
        mock_engine.sync.return_value = SyncResult(synced={"company": 2, "ledger": 10}, errors={})

        self.app.dependency_overrides[_get_engine] = lambda: mock_engine
        try:
            response = self.client.post(
                "/sync/run",
                json={"company_name": "Acme", "full": True},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["total_records"] == 12
            assert body["synced"]["ledger"] == 10
        finally:
            self.app.dependency_overrides.clear()


class TestDocsEndpoint:
    def setup_method(self) -> None:
        self.client = TestClient(build_api())

    def test_openapi_schema_accessible(self) -> None:
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "TallySync Control API"
