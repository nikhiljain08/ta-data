"""Tests for app.database — engine factory, session scope, bulk upsert."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import DatabaseSettings
from app.database.bulk import bulk_upsert
from app.database.engine import build_engine
from app.database.session import make_session_factory, session_scope

# ── build_engine ──────────────────────────────────────────────────────────────


class TestBuildEngine:
    def test_passes_url_to_create_engine(self) -> None:
        db = DatabaseSettings(url="postgresql+psycopg://u:p@localhost/testdb")
        with patch("app.database.engine.create_engine") as mock_create:
            mock_create.return_value = MagicMock()
            build_engine(db)
            args, _ = mock_create.call_args
            assert args[0] == "postgresql+psycopg://u:p@localhost/testdb"

    def test_engine_has_pool_pre_ping(self) -> None:
        db = DatabaseSettings(url="postgresql+psycopg://u:p@localhost/db")
        with patch("app.database.engine.create_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine
            result = build_engine(db)
            _, kwargs = mock_create.call_args
            assert kwargs["pool_pre_ping"] is True
            assert result is mock_engine


# ── make_session_factory ──────────────────────────────────────────────────────


class TestMakeSessionFactory:
    def test_returns_callable_factory(self) -> None:
        mock_engine = MagicMock()
        factory = make_session_factory(mock_engine)
        assert callable(factory)


# ── session_scope ─────────────────────────────────────────────────────────────


class TestSessionScope:
    def test_commits_on_success(self) -> None:
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        with session_scope(mock_factory) as session:
            assert session is mock_session

        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()

    def test_rolls_back_on_exception(self) -> None:
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        with pytest.raises(ValueError), session_scope(mock_factory):
            raise ValueError("boom")

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()


# ── bulk_upsert ───────────────────────────────────────────────────────────────


class TestBulkUpsert:
    def test_empty_batch_returns_zero_without_db_call(self) -> None:
        mock_session = MagicMock()
        mock_model = MagicMock()

        result = bulk_upsert(
            mock_session,
            mock_model,
            [],
            conflict_columns=["company_name", "name"],
            update_columns=["alter_id"],
        )

        assert result == 0
        mock_session.execute.assert_not_called()

    def test_non_empty_batch_calls_execute(self) -> None:
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_session.execute.return_value = mock_result

        from app.models.db.inventory import UnitModel

        rows = [
            {"company_name": "Acme", "name": "Nos", "alter_id": 1, "synced_at": None},
            {"company_name": "Acme", "name": "Box", "alter_id": 2, "synced_at": None},
        ]
        result = bulk_upsert(
            mock_session,
            UnitModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=["alter_id", "synced_at"],
        )

        mock_session.execute.assert_called_once()
        assert result == 2

    def test_negative_rowcount_returns_batch_size(self) -> None:
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = -1
        mock_session.execute.return_value = mock_result

        from app.models.db.inventory import UnitModel

        rows = [{"company_name": "Acme", "name": "Nos", "alter_id": 1, "synced_at": None}]
        result = bulk_upsert(
            mock_session,
            UnitModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=["alter_id"],
        )

        assert result == len(rows)
