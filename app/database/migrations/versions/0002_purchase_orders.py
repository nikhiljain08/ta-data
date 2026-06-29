"""Add purchase_orders and purchase_order_items tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("voucher_number", sa.String(100), nullable=False),
        sa.Column("date", sa.String(8), nullable=False, server_default=""),
        sa.Column("party_ledger", sa.String(500), nullable=False, server_default=""),
        sa.Column("narration", sa.Text, nullable=False, server_default=""),
        sa.Column("order_due_date", sa.String(8), nullable=False, server_default=""),
        sa.Column("is_cancelled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_optional", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "company_name", "voucher_number", name="uq_purchase_orders_company_number"
        ),
    )
    op.create_index("ix_po_company_date", "purchase_orders", ["company_name", "date"])
    op.create_index("ix_po_party_ledger", "purchase_orders", ["party_ledger"])

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "po_id",
            sa.Integer,
            sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stock_item_name", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("billed_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("rate", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("godown_name", sa.String(500), nullable=False, server_default=""),
    )
    op.create_index("ix_poi_po_id", "purchase_order_items", ["po_id"])
    op.create_index("ix_poi_stock_item", "purchase_order_items", ["stock_item_name"])


def downgrade() -> None:
    op.drop_table("purchase_order_items")
    op.drop_table("purchase_orders")
