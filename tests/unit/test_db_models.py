"""Tests for SQLAlchemy ORM model structure.

These tests verify table names, column presence, and constraints without
requiring a database connection — SQLAlchemy's inspect() works on the
mapper metadata alone.
"""

from __future__ import annotations

from sqlalchemy import UniqueConstraint, inspect

from app.models.db import (
    CompanyModel,
    GodownModel,
    GstDetailModel,
    LedgerGroupModel,
    LedgerModel,
    StockGroupModel,
    StockItemModel,
    SyncCheckpointModel,
    SyncRunModel,
    UnitModel,
    VoucherInventoryEntryModel,
    VoucherLedgerEntryModel,
    VoucherModel,
    VoucherTypeModel,
)
from app.models.db.raw_archive import TallyEntityVersionModel, TallyRawArchiveModel


def _col_names(model: type) -> set[str]:
    return {col.key for col in inspect(model).mapper.column_attrs}


def _unique_constraints(model: type) -> list[str]:
    return [
        c.name
        for c in inspect(model).mapper.local_table.constraints
        if isinstance(c, UniqueConstraint) and c.name
    ]


# ── Table names ────────────────────────────────────────────────────────────────


class TestTableNames:
    def test_company(self) -> None:
        assert CompanyModel.__tablename__ == "companies"

    def test_ledger_group(self) -> None:
        assert LedgerGroupModel.__tablename__ == "ledger_groups"

    def test_ledger(self) -> None:
        assert LedgerModel.__tablename__ == "ledgers"

    def test_voucher_type(self) -> None:
        assert VoucherTypeModel.__tablename__ == "voucher_types"

    def test_unit(self) -> None:
        assert UnitModel.__tablename__ == "units"

    def test_godown(self) -> None:
        assert GodownModel.__tablename__ == "godowns"

    def test_stock_group(self) -> None:
        assert StockGroupModel.__tablename__ == "stock_groups"

    def test_stock_item(self) -> None:
        assert StockItemModel.__tablename__ == "stock_items"

    def test_voucher(self) -> None:
        assert VoucherModel.__tablename__ == "vouchers"

    def test_voucher_ledger_entry(self) -> None:
        assert VoucherLedgerEntryModel.__tablename__ == "voucher_ledger_entries"

    def test_voucher_inventory_entry(self) -> None:
        assert VoucherInventoryEntryModel.__tablename__ == "voucher_inventory_entries"

    def test_gst_detail(self) -> None:
        assert GstDetailModel.__tablename__ == "gst_details"

    def test_sync_checkpoint(self) -> None:
        assert SyncCheckpointModel.__tablename__ == "sync_checkpoints"

    def test_sync_run(self) -> None:
        assert SyncRunModel.__tablename__ == "sync_runs"


# ── Column presence ────────────────────────────────────────────────────────────


class TestCompanyColumns:
    def test_required_columns_exist(self) -> None:
        cols = _col_names(CompanyModel)
        for col in ("id", "name", "guid", "gstin", "alter_id", "synced_at"):
            assert col in cols, f"Missing column: {col}"

    def test_unique_on_name(self) -> None:
        assert "uq_companies_name" in _unique_constraints(CompanyModel)


class TestLedgerGroupColumns:
    def test_required_columns(self) -> None:
        cols = _col_names(LedgerGroupModel)
        for col in ("company_name", "name", "parent", "is_deemed_positive", "alter_id"):
            assert col in cols

    def test_unique_constraint(self) -> None:
        assert "uq_ledger_groups_company_name" in _unique_constraints(LedgerGroupModel)


class TestLedgerColumns:
    def test_required_columns(self) -> None:
        cols = _col_names(LedgerModel)
        for col in (
            "company_name",
            "name",
            "parent",
            "opening_balance",
            "closing_balance",
            "gstin",
            "pan",
            "email",
            "address",
            "alter_id",
        ):
            assert col in cols

    def test_unique_constraint(self) -> None:
        assert "uq_ledgers_company_name" in _unique_constraints(LedgerModel)


class TestStockItemColumns:
    def test_required_columns(self) -> None:
        cols = _col_names(StockItemModel)
        for col in (
            "company_name",
            "name",
            "parent",
            "base_units",
            "hsn_code",
            "opening_balance",
            "closing_balance",
            "alter_id",
        ):
            assert col in cols

    def test_unique_constraint(self) -> None:
        assert "uq_stock_items_company_name" in _unique_constraints(StockItemModel)


class TestSyncCheckpointColumns:
    def test_required_columns(self) -> None:
        cols = _col_names(SyncCheckpointModel)
        for col in ("company_name", "entity_type", "last_alter_id", "last_synced_at"):
            assert col in cols

    def test_unique_constraint(self) -> None:
        assert "uq_sync_checkpoints_company_entity" in _unique_constraints(SyncCheckpointModel)


class TestVoucherColumns:
    def test_required_columns(self) -> None:
        cols = _col_names(VoucherModel)
        for col in (
            "company_name",
            "voucher_number",
            "voucher_type",
            "date",
            "party_ledger",
            "is_invoice",
            "is_cancelled",
            "alter_id",
        ):
            assert col in cols

    def test_unique_constraint(self) -> None:
        assert "uq_vouchers_company_number_type" in _unique_constraints(VoucherModel)

    def test_has_ledger_entries_relationship(self) -> None:
        assert hasattr(VoucherModel, "ledger_entries")

    def test_has_inventory_entries_relationship(self) -> None:
        assert hasattr(VoucherModel, "inventory_entries")

    def test_has_gst_details_relationship(self) -> None:
        assert hasattr(VoucherModel, "gst_details")


class TestSyncRunFidelityColumns:
    def test_fidelity_columns_exist(self) -> None:
        cols = _col_names(SyncRunModel)
        for col in (
            "records_inserted",
            "records_updated",
            "records_skipped",
            "parser_version",
            "schema_version",
        ):
            assert col in cols, f"Missing SyncRunModel column: {col}"


class TestRawArchiveModel:
    def test_table_name(self) -> None:
        assert TallyRawArchiveModel.__tablename__ == "tally_raw_archive"

    def test_required_columns(self) -> None:
        cols = _col_names(TallyRawArchiveModel)
        for col in (
            "id",
            "entity_type",
            "company_name",
            "entity_name",
            "guid",
            "alter_id",
            "xml",
            "xml_hash",
            "unknown_fields",
            "parser_version",
            "sync_run_id",
            "created_at",
            "updated_at",
        ):
            assert col in cols, f"Missing TallyRawArchiveModel column: {col}"

    def test_unique_constraint(self) -> None:
        assert "uq_raw_archive_type_company_guid" in _unique_constraints(TallyRawArchiveModel)


class TestEntityVersionModel:
    def test_table_name(self) -> None:
        assert TallyEntityVersionModel.__tablename__ == "tally_entity_versions"

    def test_required_columns(self) -> None:
        cols = _col_names(TallyEntityVersionModel)
        for col in (
            "id",
            "entity_type",
            "company_name",
            "entity_name",
            "guid",
            "alter_id",
            "xml_hash",
            "xml",
            "normalized_json",
            "unknown_fields",
            "parser_version",
            "sync_run_id",
            "created_at",
        ):
            assert col in cols, f"Missing TallyEntityVersionModel column: {col}"

    def test_unique_constraint(self) -> None:
        assert "uq_entity_versions_type_company_guid_hash" in _unique_constraints(
            TallyEntityVersionModel
        )
