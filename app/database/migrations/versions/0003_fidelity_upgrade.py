"""Add raw XML archive, entity version history, and extended sync_run stats.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29

Changes:
- Create tally_raw_archive   (latest raw XML per entity)
- Create tally_entity_versions (append-only change history)
- Add records_inserted, records_updated, records_skipped,
  parser_version, schema_version columns to sync_runs
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tally_raw_archive ────────────────────────────────────────────────────
    op.create_table(
        "tally_raw_archive",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("entity_name", sa.String(500), nullable=False, server_default=""),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("master_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column("xml", sa.Text, nullable=False),
        sa.Column("xml_hash", sa.String(64), nullable=False),
        sa.Column(
            "unknown_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("parser_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("sync_run_id", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "entity_type",
            "company_name",
            "guid",
            name="uq_raw_archive_type_company_guid",
        ),
    )
    op.create_index(
        "ix_raw_archive_type_company", "tally_raw_archive", ["entity_type", "company_name"]
    )
    op.create_index(
        "ix_raw_archive_alter_id",
        "tally_raw_archive",
        ["entity_type", "company_name", "alter_id"],
    )
    op.create_index("ix_raw_archive_updated_at", "tally_raw_archive", ["updated_at"])

    # ── tally_entity_versions ────────────────────────────────────────────────
    op.create_table(
        "tally_entity_versions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("entity_name", sa.String(500), nullable=False, server_default=""),
        sa.Column("guid", sa.String(100), nullable=False, server_default=""),
        sa.Column("alter_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column("xml_hash", sa.String(64), nullable=False),
        sa.Column("xml", sa.Text, nullable=False),
        sa.Column(
            "normalized_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "unknown_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("parser_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("sync_run_id", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "entity_type",
            "company_name",
            "guid",
            "xml_hash",
            name="uq_entity_versions_type_company_guid_hash",
        ),
    )
    op.create_index(
        "ix_entity_versions_type_company_guid",
        "tally_entity_versions",
        ["entity_type", "company_name", "guid"],
    )
    op.create_index("ix_entity_versions_created_at", "tally_entity_versions", ["created_at"])
    op.create_index(
        "ix_entity_versions_alter_id",
        "tally_entity_versions",
        ["entity_type", "company_name", "alter_id"],
    )

    # ── sync_runs extra columns ───────────────────────────────────────────────
    op.add_column(
        "sync_runs",
        sa.Column("records_inserted", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "sync_runs",
        sa.Column("records_updated", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "sync_runs",
        sa.Column("records_skipped", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "sync_runs",
        sa.Column("parser_version", sa.String(20), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "sync_runs",
        sa.Column("schema_version", sa.String(20), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("sync_runs", "schema_version")
    op.drop_column("sync_runs", "parser_version")
    op.drop_column("sync_runs", "records_skipped")
    op.drop_column("sync_runs", "records_updated")
    op.drop_column("sync_runs", "records_inserted")

    op.drop_index("ix_entity_versions_alter_id", table_name="tally_entity_versions")
    op.drop_index("ix_entity_versions_created_at", table_name="tally_entity_versions")
    op.drop_index("ix_entity_versions_type_company_guid", table_name="tally_entity_versions")
    op.drop_table("tally_entity_versions")

    op.drop_index("ix_raw_archive_updated_at", table_name="tally_raw_archive")
    op.drop_index("ix_raw_archive_alter_id", table_name="tally_raw_archive")
    op.drop_index("ix_raw_archive_type_company", table_name="tally_raw_archive")
    op.drop_table("tally_raw_archive")
