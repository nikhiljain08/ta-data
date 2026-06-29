"""Tests for app.services — BaseSyncService and concrete service subclasses."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.company import CompanySyncService
from app.services.masters import LedgerGroupSyncService, LedgerSyncService, UnitSyncService


def _make_service(cls: type) -> tuple[object, MagicMock, MagicMock, MagicMock]:
    """Return (service, mock_client, mock_template, mock_session_factory)."""
    client = MagicMock()
    template = MagicMock()
    session_factory = MagicMock()
    svc = cls(client=client, template=template, session_factory=session_factory)
    return svc, client, template, session_factory


class TestCompanySyncService:
    def test_entity_name(self) -> None:
        svc, _, _, _ = _make_service(CompanySyncService)
        assert svc.entity_name == "company"

    def test_build_xml_calls_template_company(self) -> None:
        svc, _, template, _ = _make_service(CompanySyncService)
        template.company.return_value = "<xml/>"
        xml = svc._build_xml("Acme", 0)
        template.company.assert_called_once()
        assert xml == "<xml/>"

    def test_sync_returns_zero_on_empty_response(self) -> None:
        svc, client, template, _session_factory = _make_service(CompanySyncService)
        template.company.return_value = "<xml/>"
        # Client returns empty XML (no COMPANY elements)
        client.request.return_value = b"<ENVELOPE/>"

        mock_session = MagicMock()
        mock_cp = MagicMock()
        mock_cp.get_alter_id.return_value = 0
        mock_cp.start_run.return_value = 1

        with (
            patch("app.services.base.session_scope") as mock_scope,
            patch("app.services.base.CheckpointRepository", return_value=mock_cp),
        ):
            mock_scope.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            count = svc.sync("Acme")

        assert count == 0
        call_kwargs = mock_cp.finish_run.call_args
        assert call_kwargs is not None
        assert call_kwargs.args[0] == 1
        assert call_kwargs.kwargs.get("status") == "success"
        assert call_kwargs.kwargs.get("records_synced") == 0


class TestLedgerGroupSyncService:
    def test_entity_name(self) -> None:
        svc, _, _, _ = _make_service(LedgerGroupSyncService)
        assert svc.entity_name == "ledger_group"

    def test_build_xml_passes_alter_id(self) -> None:
        svc, _, template, _ = _make_service(LedgerGroupSyncService)
        template.ledger_groups.return_value = "<xml/>"
        svc._build_xml("Acme", 99)
        template.ledger_groups.assert_called_once_with(company="Acme", alter_id=99)


class TestUnitSyncService:
    def test_entity_name(self) -> None:
        svc, _, _, _ = _make_service(UnitSyncService)
        assert svc.entity_name == "unit"

    def test_build_xml_full_sync(self) -> None:
        svc, _, template, _ = _make_service(UnitSyncService)
        template.units.return_value = "<xml/>"
        svc._build_xml("Acme", 0)
        template.units.assert_called_once_with(company="Acme", alter_id=0)


class TestLedgerSyncService:
    def test_entity_name(self) -> None:
        svc, _, _, _ = _make_service(LedgerSyncService)
        assert svc.entity_name == "ledger"

    def test_build_xml_incremental(self) -> None:
        svc, _, template, _ = _make_service(LedgerSyncService)
        template.ledgers.return_value = "<xml/>"
        svc._build_xml("Acme", 500)
        template.ledgers.assert_called_once_with(company="Acme", alter_id=500)
