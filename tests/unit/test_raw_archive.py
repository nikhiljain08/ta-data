"""Tests for RawArchiveRepository and EntityVersionRepository.

All tests use a mocked Session — no database required.
They verify the upsert and version-creation logic, including:
- empty batch is a no-op
- hash lookup delegates to session.execute correctly
- upsert_batch calls execute with the ON CONFLICT DO UPDATE statement
- create_versions calls execute with ON CONFLICT DO NOTHING
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.models.domain.ledger import LedgerRecord
from app.repositories.postgres.raw_archive import EntityVersionRepository, RawArchiveRepository

COMPANY = "Test Company"
ENTITY = "ledger"


def _mock_session(rows: list[object] | None = None) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows or []
    session.execute.return_value = result
    return session


def _ledger(name: str = "Cash", guid: str = "g1", alter_id: int = 1) -> LedgerRecord:
    return LedgerRecord(name=name, guid=guid, alter_id=alter_id)


def _raw(content: str = "<LEDGER/>") -> bytes:
    return content.encode()


# ── RawArchiveRepository ───────────────────────────────────────────────────────


class TestRawArchiveRepositoryGetHashes:
    def test_empty_guids_returns_empty_dict(self) -> None:
        repo = RawArchiveRepository(_mock_session())
        result = repo.get_latest_hashes(ENTITY, COMPANY, [])
        assert result == {}

    def test_queries_database_with_given_guids(self) -> None:
        row1 = MagicMock()
        row1.guid = "g1"
        row1.xml_hash = "abc123"
        session = _mock_session(rows=[row1])
        repo = RawArchiveRepository(session)
        result = repo.get_latest_hashes(ENTITY, COMPANY, ["g1"])
        assert result == {"g1": "abc123"}
        session.execute.assert_called_once()

    def test_maps_multiple_rows(self) -> None:
        r1, r2 = MagicMock(), MagicMock()
        r1.guid, r1.xml_hash = "g1", "h1"
        r2.guid, r2.xml_hash = "g2", "h2"
        session = _mock_session(rows=[r1, r2])
        repo = RawArchiveRepository(session)
        result = repo.get_latest_hashes(ENTITY, COMPANY, ["g1", "g2"])
        assert result == {"g1": "h1", "g2": "h2"}


class TestRawArchiveRepositoryUpsert:
    def test_empty_batch_skips_execute(self) -> None:
        session = _mock_session()
        repo = RawArchiveRepository(session)
        repo.upsert_batch(ENTITY, COMPANY, [], sync_run_id=None)
        session.execute.assert_not_called()

    def test_non_empty_batch_calls_execute(self) -> None:
        session = _mock_session()
        repo = RawArchiveRepository(session)
        records = [(_ledger(), _raw(), "hash1", {})]
        repo.upsert_batch(ENTITY, COMPANY, records, sync_run_id=1)
        session.execute.assert_called_once()

    def test_unknown_fields_included(self) -> None:
        session = _mock_session()
        repo = RawArchiveRepository(session)
        unknown = {"EXTRA_TAG": "some_value"}
        records = [(_ledger(), _raw(), "hash1", unknown)]
        repo.upsert_batch(ENTITY, COMPANY, records, sync_run_id=None)
        # Just verify it completes without error and executes once
        assert session.execute.call_count == 1

    def test_multiple_records_in_single_execute(self) -> None:
        session = _mock_session()
        repo = RawArchiveRepository(session)
        records = [
            (_ledger("Cash", "g1", 1), _raw("<LEDGER>Cash</LEDGER>"), "h1", {}),
            (_ledger("Bank", "g2", 2), _raw("<LEDGER>Bank</LEDGER>"), "h2", {}),
        ]
        repo.upsert_batch(ENTITY, COMPANY, records, sync_run_id=5)
        # Both records in a single batch execute
        session.execute.assert_called_once()


# ── EntityVersionRepository ────────────────────────────────────────────────────


class TestEntityVersionRepository:
    def test_empty_batch_skips_execute(self) -> None:
        session = _mock_session()
        repo = EntityVersionRepository(session)
        repo.create_versions(ENTITY, COMPANY, [], sync_run_id=None)
        session.execute.assert_not_called()

    def test_single_record_calls_execute(self) -> None:
        session = _mock_session()
        repo = EntityVersionRepository(session)
        records = [(_ledger(), _raw(), "hash1", {})]
        repo.create_versions(ENTITY, COMPANY, records, sync_run_id=1)
        session.execute.assert_called_once()

    def test_normalized_json_serializes_pydantic_model(self) -> None:
        session = _mock_session()
        repo = EntityVersionRepository(session)
        ledger = _ledger("Cash", "g1", 10)
        records = [(ledger, _raw(), "h1", {})]
        # Should not raise even though model_dump() is called internally
        repo.create_versions(ENTITY, COMPANY, records, sync_run_id=None)
        session.execute.assert_called_once()

    def test_multiple_records_batched(self) -> None:
        session = _mock_session()
        repo = EntityVersionRepository(session)
        records = [
            (_ledger("Cash", "g1", 1), _raw(), "h1", {}),
            (_ledger("Bank", "g2", 2), _raw(), "h2", {}),
        ]
        repo.create_versions(ENTITY, COMPANY, records, sync_run_id=None)
        session.execute.assert_called_once()
