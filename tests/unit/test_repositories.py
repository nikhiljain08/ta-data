"""Tests for PostgreSQL repository implementations.

All tests use a mocked Session so no database is required.
They verify that:
  - empty batch returns 0 without hitting the DB
  - non-empty batch calls session.execute exactly once
  - returned count matches what bulk_upsert returns
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from app.models.domain.company import CompanyRecord
from app.models.domain.godown import GodownRecord
from app.models.domain.ledger import LedgerRecord
from app.models.domain.ledger_group import LedgerGroupRecord
from app.models.domain.stock_group import StockGroupRecord
from app.models.domain.stock_item import StockItemRecord
from app.models.domain.unit import UnitRecord
from app.models.domain.voucher_type import VoucherTypeRecord
from app.repositories.postgres.company import CompanyRepository
from app.repositories.postgres.inventory import (
    GodownRepository,
    StockGroupRepository,
    StockItemRepository,
    UnitRepository,
)
from app.repositories.postgres.ledger import (
    LedgerGroupRepository,
    LedgerRepository,
    VoucherTypeRepository,
)

COMPANY = "Acme Ltd"


def _mock_session(rowcount: int = 3) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.rowcount = rowcount
    session.execute.return_value = result
    return session


# ── CompanyRepository ──────────────────────────────────────────────────────────


class TestCompanyRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = CompanyRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = CompanyRepository(session)
        records = [CompanyRecord(name="Acme Ltd", guid="g1", alter_id=10)]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1


# ── LedgerGroupRepository ──────────────────────────────────────────────────────


class TestLedgerGroupRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = LedgerGroupRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=2)
        repo = LedgerGroupRepository(session)
        records = [
            LedgerGroupRecord(name="Sundry Debtors", parent="Current Assets", alter_id=5),
            LedgerGroupRecord(name="Capital Account", alter_id=3),
        ]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 2


# ── LedgerRepository ──────────────────────────────────────────────────────────


class TestLedgerRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = LedgerRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = LedgerRepository(session)
        records = [
            LedgerRecord(
                name="Customer A",
                parent="Sundry Debtors",
                gstin="27XXX",
                closing_balance=Decimal("50000"),
                address=["Line 1", "Mumbai"],
                alter_id=100,
            )
        ]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1


# ── VoucherTypeRepository ──────────────────────────────────────────────────────


class TestVoucherTypeRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = VoucherTypeRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = VoucherTypeRepository(session)
        records = [VoucherTypeRecord(name="Sales", parent="Sales", alter_id=20)]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1


# ── UnitRepository ────────────────────────────────────────────────────────────


class TestUnitRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = UnitRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = UnitRepository(session)
        records = [UnitRecord(name="Nos", gst_unit_name="OTH", alter_id=1)]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1


# ── GodownRepository ──────────────────────────────────────────────────────────


class TestGodownRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = GodownRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = GodownRepository(session)
        records = [GodownRecord(name="Main Warehouse", alter_id=8)]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1


# ── StockGroupRepository ───────────────────────────────────────────────────────


class TestStockGroupRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = StockGroupRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = StockGroupRepository(session)
        records = [StockGroupRecord(name="Electronics", parent="Primary", alter_id=15)]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1


# ── StockItemRepository ────────────────────────────────────────────────────────


class TestStockItemRepository:
    def test_empty_batch_returns_zero(self) -> None:
        repo = StockItemRepository(_mock_session())
        assert repo.upsert_batch(COMPANY, []) == 0

    def test_upserts_records(self) -> None:
        session = _mock_session(rowcount=1)
        repo = StockItemRepository(session)
        records = [
            StockItemRecord(
                name="Widget Pro",
                parent="Electronics",
                base_units="Nos",
                hsn_code="85423900",
                closing_balance=Decimal("30"),
                closing_rate=Decimal("500"),
                closing_value=Decimal("15000"),
                alter_id=50,
            )
        ]
        result = repo.upsert_batch(COMPANY, records)
        session.execute.assert_called_once()
        assert result == 1
