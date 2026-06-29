"""Tests for the fidelity sync pipeline in BaseSyncService.

Verifies hash-based change detection:
- New records (guid not in archive) are upserted + versioned
- Changed records (hash differs) are upserted + versioned
- Unchanged records (hash identical) are skipped from entity upsert and version
  but still update the raw archive alter_id
- Incremental AlterID filter works correctly
- Legacy path (no _parse_with_raw) falls through to original upsert
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.domain.ledger import LedgerRecord
from app.parser.base import XmlSource
from app.repositories.base import BaseRepository
from app.services.base import BaseSyncService

COMPANY = "Acme Ltd"


# ── Test doubles ──────────────────────────────────────────────────────────────


def _ledger(name: str = "Cash", guid: str = "g1", alter_id: int = 10) -> LedgerRecord:
    return LedgerRecord(name=name, guid=guid, alter_id=alter_id)


def _raw(content: str = "<L/>") -> bytes:
    return content.encode()


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class _FakeRepo(BaseRepository[LedgerRecord]):
    def __init__(self) -> None:
        self.upserted: list[LedgerRecord] = []

    def upsert_batch(self, company_name: str, records: list[LedgerRecord]) -> int:
        self.upserted.extend(records)
        return len(records)


class _LedgerService(BaseSyncService[LedgerRecord]):
    """Concrete subclass wired with configurable parse output for testing."""

    entity_name = "ledger"

    def __init__(
        self,
        session: Session,
        fidelity_items: list[tuple[LedgerRecord, bytes, dict[str, Any]]] | None = None,
        legacy_records: list[LedgerRecord] | None = None,
        existing_hashes: dict[str, str] | None = None,
    ) -> None:
        self._fake_session = session
        self._fidelity_items = fidelity_items
        self._legacy_records = legacy_records or []
        self._existing_hashes = existing_hashes or {}
        self._fake_repo = _FakeRepo()

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return "<xml/>"

    def _parse(self, source: XmlSource) -> Iterator[LedgerRecord]:
        return iter(self._legacy_records)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[LedgerRecord, bytes, dict[str, Any]]] | None:
        if self._fidelity_items is None:
            return None
        return iter(self._fidelity_items)

    def _make_repo(self, session: Session) -> BaseRepository[LedgerRecord]:
        return self._fake_repo

    def _run_fidelity(
        self,
        items: list[tuple[LedgerRecord, bytes, str, dict[str, Any]]],
        alter_id: int = 0,
    ) -> tuple[int, int, int, int]:
        """Helper: call _run_fidelity_pipeline with mocked archive repo."""
        session = MagicMock()
        raw_repo = MagicMock()
        raw_repo.get_latest_hashes.return_value = self._existing_hashes
        ver_repo = MagicMock()

        with (
            patch("app.services.base.RawArchiveRepository", return_value=raw_repo),
            patch("app.services.base.EntityVersionRepository", return_value=ver_repo),
        ):
            return self._run_fidelity_pipeline(
                session=session,
                company_name=COMPANY,
                alter_id=alter_id,
                full=False,
                items=items,
                run_id=1,
            )


# ── Fidelity pipeline tests ───────────────────────────────────────────────────


class TestFidelityPipeline:
    def test_empty_items_returns_zeros(self) -> None:
        svc = _LedgerService(MagicMock())
        total, ins, upd, skp = svc._run_fidelity(items=[])
        assert (total, ins, upd, skp) == (0, 0, 0, 0)

    def test_new_record_counted_as_inserted(self) -> None:
        raw = _raw("<LEDGER>Cash</LEDGER>")
        xml_hash = _hash(raw)
        ledger = _ledger(guid="g1", alter_id=5)
        svc = _LedgerService(MagicMock(), existing_hashes={})
        total, ins, upd, skp = svc._run_fidelity([(ledger, raw, xml_hash, {})])
        assert ins == 1
        assert upd == 0
        assert skp == 0
        assert total == 1
        assert svc._fake_repo.upserted == [ledger]

    def test_changed_record_counted_as_updated(self) -> None:
        raw = _raw("<LEDGER>Bank</LEDGER>")
        xml_hash = _hash(raw)
        ledger = _ledger(guid="g1", alter_id=20)
        svc = _LedgerService(MagicMock(), existing_hashes={"g1": "old_hash_xyz"})
        total, ins, upd, skp = svc._run_fidelity([(ledger, raw, xml_hash, {})])
        assert upd == 1
        assert ins == 0
        assert skp == 0
        assert total == 1
        assert svc._fake_repo.upserted == [ledger]

    def test_unchanged_record_is_skipped(self) -> None:
        raw = _raw("<LEDGER>Cash</LEDGER>")
        xml_hash = _hash(raw)
        ledger = _ledger(guid="g1", alter_id=10)
        # Same hash already in archive → unchanged
        svc = _LedgerService(MagicMock(), existing_hashes={"g1": xml_hash})
        total, _ins, _upd, skp = svc._run_fidelity([(ledger, raw, xml_hash, {})])
        assert skp == 1
        assert total == 0
        # Entity repo should NOT receive unchanged record
        assert svc._fake_repo.upserted == []

    def test_mixed_batch(self) -> None:
        raw_new = _raw("<LEDGER>New</LEDGER>")
        raw_changed = _raw("<LEDGER>Changed</LEDGER>")
        raw_same = _raw("<LEDGER>Same</LEDGER>")
        h_new = _hash(raw_new)
        h_changed = _hash(raw_changed)
        h_same = _hash(raw_same)

        ledger_new = _ledger("New", "g_new", 30)
        ledger_changed = _ledger("Changed", "g_changed", 31)
        ledger_same = _ledger("Same", "g_same", 32)

        svc = _LedgerService(
            MagicMock(),
            existing_hashes={
                "g_changed": "old_hash",  # hash changed
                "g_same": h_same,  # hash identical
            },
        )
        items = [
            (ledger_new, raw_new, h_new, {}),
            (ledger_changed, raw_changed, h_changed, {}),
            (ledger_same, raw_same, h_same, {}),
        ]
        total, ins, upd, skp = svc._run_fidelity(items)
        assert ins == 1
        assert upd == 1
        assert skp == 1
        assert total == 2
        # Only new and changed go to entity repo
        assert {r.guid for r in svc._fake_repo.upserted} == {"g_new", "g_changed"}

    def test_alter_id_filter_excludes_old_records(self) -> None:
        raw = _raw("<LEDGER>Old</LEDGER>")
        xml_hash = _hash(raw)
        # alter_id=5 is NOT > last_alter_id=10 → filtered out
        ledger = _ledger(guid="g1", alter_id=5)
        svc = _LedgerService(MagicMock(), existing_hashes={})
        total, ins, upd, skp = svc._run_fidelity([(ledger, raw, xml_hash, {})], alter_id=10)
        assert (total, ins, upd, skp) == (0, 0, 0, 0)
        assert svc._fake_repo.upserted == []

    def test_alter_id_filter_includes_newer_records(self) -> None:
        raw = _raw("<LEDGER>New</LEDGER>")
        xml_hash = _hash(raw)
        # alter_id=20 > last_alter_id=10 → included
        ledger = _ledger(guid="g1", alter_id=20)
        svc = _LedgerService(MagicMock(), existing_hashes={})
        total, ins, _upd, _skp = svc._run_fidelity([(ledger, raw, xml_hash, {})], alter_id=10)
        assert total == 1
        assert ins == 1


# ── Legacy path tests ─────────────────────────────────────────────────────────


class TestLegacyPath:
    """When _parse_with_raw returns None the service falls back to old behaviour."""

    def _make_svc(self, records: list[LedgerRecord]) -> _LedgerService:
        # fidelity_items=None → _parse_with_raw returns None → legacy path
        return _LedgerService(MagicMock(), fidelity_items=None, legacy_records=records)

    def test_legacy_parse_with_raw_is_none(self) -> None:
        svc = self._make_svc([])
        result = svc._parse_with_raw(b"<xml/>")
        assert result is None

    def test_fetch_and_parse_with_raw_returns_none_for_legacy(self) -> None:
        svc = self._make_svc([_ledger()])
        # Override _client so request() doesn't fail
        svc._client = MagicMock()  # type: ignore[assignment]
        svc._client.request.return_value = b"<xml/>"
        result = svc._fetch_and_parse_with_raw("<xml/>")
        assert result is None


# ── Hash computation in _fetch_and_parse_with_raw ─────────────────────────────


class TestHashComputation:
    def test_sha256_hash_computed_per_record(self) -> None:
        raw = _raw("<LEDGER>Test</LEDGER>")
        expected_hash = hashlib.sha256(raw).hexdigest()

        fidelity_items = [(_ledger(), raw, {})]
        svc = _LedgerService(MagicMock(), fidelity_items=fidelity_items)
        svc._client = MagicMock()  # type: ignore[assignment]
        svc._client.request.return_value = b"<xml/>"

        result = svc._fetch_and_parse_with_raw("<xml/>")
        assert result is not None
        assert len(result) == 1
        _, _, xml_hash, _ = result[0]
        assert xml_hash == expected_hash
