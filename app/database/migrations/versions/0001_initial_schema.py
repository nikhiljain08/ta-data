"""Initial schema — all entity tables, sync state, voucher sub-tables.

Revision ID: 0001
Revises: (none)
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── companies ──────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("books_from", sa.String(8), nullable=False, server_default=""),
        sa.Column("starting_from", sa.String(8), nullable=False, server_default=""),
        sa.Column("ending_at", sa.String(8), nullable=False, server_default=""),
        sa.Column("country", sa.String(100), nullable=False, server_default=""),
        sa.Column("state", sa.String(100), nullable=False, server_default=""),
        sa.Column("gstin", sa.String(20), nullable=False, server_default=""),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("name", name="uq_companies_name"),
    )
    op.create_index("ix_companies_alter_id", "companies", ["alter_id"])

    # ── ledger_groups ──────────────────────────────────────────────────────────
    op.create_table(
        "ledger_groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("parent", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_deemed_positive", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_revenue", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("affects_stock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_ledger_groups_company_name"),
    )
    op.create_index(
        "ix_ledger_groups_company_alter_id", "ledger_groups", ["company_name", "alter_id"]
    )

    # ── ledgers ────────────────────────────────────────────────────────────────
    op.create_table(
        "ledgers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("parent", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_deemed_positive", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("opening_balance", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("closing_balance", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("gst_registration_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("gstin", sa.String(20), nullable=False, server_default=""),
        sa.Column("pan", sa.String(20), nullable=False, server_default=""),
        sa.Column("mobile", sa.String(50), nullable=False, server_default=""),
        sa.Column("email", sa.String(255), nullable=False, server_default=""),
        sa.Column("country", sa.String(100), nullable=False, server_default=""),
        sa.Column("state", sa.String(100), nullable=False, server_default=""),
        sa.Column("pincode", sa.String(20), nullable=False, server_default=""),
        sa.Column(
            "address",
            postgresql.ARRAY(sa.String(500)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_ledgers_company_name"),
    )
    op.create_index("ix_ledgers_company_alter_id", "ledgers", ["company_name", "alter_id"])
    op.create_index("ix_ledgers_gstin", "ledgers", ["gstin"])

    # ── voucher_types ──────────────────────────────────────────────────────────
    op.create_table(
        "voucher_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("parent", sa.String(500), nullable=False, server_default=""),
        sa.Column("numbering_method", sa.String(100), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_voucher_types_company_name"),
    )
    op.create_index(
        "ix_voucher_types_company_alter_id", "voucher_types", ["company_name", "alter_id"]
    )

    # ── units ──────────────────────────────────────────────────────────────────
    op.create_table(
        "units",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("gst_unit_name", sa.String(20), nullable=False, server_default=""),
        sa.Column("formal_name", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_simple_unit", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_units_company_name"),
    )
    op.create_index("ix_units_company_alter_id", "units", ["company_name", "alter_id"])

    # ── godowns ────────────────────────────────────────────────────────────────
    op.create_table(
        "godowns",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("parent", sa.String(500), nullable=False, server_default=""),
        sa.Column("has_no_stock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_godowns_company_name"),
    )
    op.create_index("ix_godowns_company_alter_id", "godowns", ["company_name", "alter_id"])

    # ── stock_groups ───────────────────────────────────────────────────────────
    op.create_table(
        "stock_groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("parent", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_addable", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_stock_groups_company_name"),
    )
    op.create_index(
        "ix_stock_groups_company_alter_id", "stock_groups", ["company_name", "alter_id"]
    )

    # ── stock_items ────────────────────────────────────────────────────────────
    op.create_table(
        "stock_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("parent", sa.String(500), nullable=False, server_default=""),
        sa.Column("category", sa.String(500), nullable=False, server_default=""),
        sa.Column("base_units", sa.String(100), nullable=False, server_default=""),
        sa.Column("gst_applicable", sa.String(50), nullable=False, server_default=""),
        sa.Column("gst_type_of_supply", sa.String(50), nullable=False, server_default=""),
        sa.Column("hsn_code", sa.String(20), nullable=False, server_default=""),
        sa.Column("description", sa.String(2000), nullable=False, server_default=""),
        sa.Column("opening_balance", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("opening_rate", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("opening_value", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("closing_balance", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("closing_rate", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("closing_value", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("company_name", "name", name="uq_stock_items_company_name"),
    )
    op.create_index("ix_stock_items_company_alter_id", "stock_items", ["company_name", "alter_id"])
    op.create_index("ix_stock_items_hsn", "stock_items", ["hsn_code"])

    # ── vouchers ───────────────────────────────────────────────────────────────
    op.create_table(
        "vouchers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("voucher_number", sa.String(100), nullable=False),
        sa.Column("voucher_type", sa.String(100), nullable=False),
        sa.Column("date", sa.String(8), nullable=False, server_default=""),
        sa.Column("party_ledger", sa.String(500), nullable=False, server_default=""),
        sa.Column("narration", sa.Text, nullable=False, server_default=""),
        sa.Column("is_invoice", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_cancelled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_optional", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "company_name",
            "voucher_number",
            "voucher_type",
            name="uq_vouchers_company_number_type",
        ),
    )
    op.create_index("ix_vouchers_company_date", "vouchers", ["company_name", "date"])
    op.create_index("ix_vouchers_company_alter_id", "vouchers", ["company_name", "alter_id"])
    op.create_index("ix_vouchers_party_ledger", "vouchers", ["party_ledger"])

    # ── voucher_ledger_entries ─────────────────────────────────────────────────
    op.create_table(
        "voucher_ledger_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "voucher_id",
            sa.Integer,
            sa.ForeignKey("vouchers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ledger_name", sa.String(500), nullable=False),
        sa.Column("is_deemed_positive", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
    )
    op.create_index("ix_vle_voucher_id", "voucher_ledger_entries", ["voucher_id"])
    op.create_index("ix_vle_ledger_name", "voucher_ledger_entries", ["ledger_name"])

    # ── voucher_inventory_entries ──────────────────────────────────────────────
    op.create_table(
        "voucher_inventory_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "voucher_id",
            sa.Integer,
            sa.ForeignKey("vouchers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stock_item_name", sa.String(500), nullable=False),
        sa.Column("is_deemed_positive", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("rate", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("godown_name", sa.String(500), nullable=False, server_default=""),
    )
    op.create_index("ix_vie_voucher_id", "voucher_inventory_entries", ["voucher_id"])
    op.create_index("ix_vie_stock_item", "voucher_inventory_entries", ["stock_item_name"])

    # ── gst_details ────────────────────────────────────────────────────────────
    op.create_table(
        "gst_details",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "voucher_id",
            sa.Integer,
            sa.ForeignKey("vouchers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hsn_code", sa.String(20), nullable=False, server_default=""),
        sa.Column("taxable_value", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("igst_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("cgst_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("sgst_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("gst_type", sa.String(50), nullable=False, server_default=""),
    )
    op.create_index("ix_gst_voucher_id", "gst_details", ["voucher_id"])
    op.create_index("ix_gst_hsn", "gst_details", ["hsn_code"])

    # ── sync_checkpoints ───────────────────────────────────────────────────────
    op.create_table(
        "sync_checkpoints",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("last_alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "company_name", "entity_type", name="uq_sync_checkpoints_company_entity"
        ),
    )

    # ── sync_runs ──────────────────────────────────────────────────────────────
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False, server_default=""),
        sa.Column("entity_type", sa.String(50), nullable=False, server_default=""),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("records_synced", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index("ix_sync_runs_company_entity", "sync_runs", ["company_name", "entity_type"])
    op.create_index("ix_sync_runs_started_at", "sync_runs", ["started_at"])


def downgrade() -> None:
    # Drop in reverse FK dependency order
    op.drop_table("sync_runs")
    op.drop_table("sync_checkpoints")
    op.drop_table("gst_details")
    op.drop_table("voucher_inventory_entries")
    op.drop_table("voucher_ledger_entries")
    op.drop_table("vouchers")
    op.drop_table("stock_items")
    op.drop_table("stock_groups")
    op.drop_table("godowns")
    op.drop_table("units")
    op.drop_table("voucher_types")
    op.drop_table("ledgers")
    op.drop_table("ledger_groups")
    op.drop_table("companies")
