"""Tests for app.sync.engine — SyncEngine orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.sync.engine import SyncEngine, SyncResult


def _make_service(name: str, count: int = 5) -> MagicMock:
    svc = MagicMock()
    svc.entity_name = name
    svc.sync.return_value = count
    return svc


class TestSyncResult:
    def test_total_records(self) -> None:
        result = SyncResult(synced={"company": 1, "ledger": 10})
        assert result.total_records == 11

    def test_has_errors_false(self) -> None:
        result = SyncResult(synced={"company": 1})
        assert result.has_errors is False

    def test_has_errors_true(self) -> None:
        result = SyncResult(errors={"ledger": "connection failed"})
        assert result.has_errors is True


class TestSyncEngine:
    def _build_engine(
        self, entities: list[str], counts: dict[str, int] | None = None
    ) -> tuple[SyncEngine, dict[str, MagicMock]]:
        counts = counts or {}
        services = {e: _make_service(e, counts.get(e, 3)) for e in entities}
        engine = SyncEngine(services, entities)
        return engine, services

    def test_calls_each_service_in_order(self) -> None:
        order = ["company", "ledger_group", "ledger"]
        engine, services = self._build_engine(order)
        engine.sync("Acme")
        call_order = [services[e].sync.call_args[1]["company_name"] for e in order]
        assert call_order == ["Acme", "Acme", "Acme"]

    def test_incremental_mode_passes_full_false(self) -> None:
        engine, services = self._build_engine(["company"])
        engine.sync("Acme", full=False)
        services["company"].sync.assert_called_once_with(company_name="Acme", full=False)

    def test_full_mode_passes_full_true(self) -> None:
        engine, services = self._build_engine(["company"])
        engine.sync("Acme", full=True)
        services["company"].sync.assert_called_once_with(company_name="Acme", full=True)

    def test_result_contains_counts(self) -> None:
        engine, _ = self._build_engine(["company", "ledger"], {"company": 2, "ledger": 7})
        result = engine.sync("Acme")
        assert result.synced == {"company": 2, "ledger": 7}

    def test_failure_in_one_entity_does_not_abort_others(self) -> None:
        order = ["company", "ledger_group", "ledger"]
        services = {e: _make_service(e) for e in order}
        services["ledger_group"].sync.side_effect = RuntimeError("DB unavailable")
        engine = SyncEngine(services, order)
        result = engine.sync("Acme")
        # company and ledger must still run
        services["company"].sync.assert_called_once()
        services["ledger"].sync.assert_called_once()
        assert "ledger_group" in result.errors
        assert result.errors["ledger_group"] == "DB unavailable"

    def test_unknown_entity_in_order_is_skipped(self) -> None:
        services = {"company": _make_service("company")}
        engine = SyncEngine(services, ["company", "nonexistent"])
        result = engine.sync("Acme")
        assert "nonexistent" not in result.synced
        assert "nonexistent" not in result.errors
