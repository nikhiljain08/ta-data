"""Raw XML archive and entity version history tables.

Two tables serve the complete-data-fidelity requirement:

tally_raw_archive
    One row per entity (latest state only).  Every sync upserts here so the
    complete Tally XML is always available even if the normalised parser is
    later updated or buggy.

tally_entity_versions
    Append-only.  One row is inserted whenever the XML hash changes, giving a
    full audit trail.  Rows are never overwritten or deleted.

Both tables are keyed on (entity_type, company_name, guid) which is stable
across Tally restarts.  Entities without a GUID (should be none in TallyPrime 7)
fall back to an empty-string guid — still stored, never discarded.
"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base


class TallyRawArchiveModel(Base):
    """Stores the latest raw XML for every synced Tally entity.

    The row is upserted on every sync pass.  xml_hash lets the sync engine
    skip the version-creation step when the content has not changed.
    """

    __tablename__ = "tally_raw_archive"
    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "company_name",
            "guid",
            name="uq_raw_archive_type_company_guid",
        ),
        Index("ix_raw_archive_type_company", "entity_type", "company_name"),
        Index("ix_raw_archive_alter_id", "entity_type", "company_name", "alter_id"),
        Index("ix_raw_archive_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    master_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xml: Mapped[str] = mapped_column(Text, nullable=False)
    xml_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    unknown_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[type-arg]
    parser_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    sync_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TallyEntityVersionModel(Base):
    """Append-only version history for every Tally entity.

    A new row is inserted whenever the xml_hash changes for an entity.
    Rows are NEVER deleted or updated — this table is the audit trail.

    version_num is informational (computed on read via ROW_NUMBER() if needed).
    The unique constraint on (entity_type, company_name, guid, xml_hash) ensures
    duplicate content is never stored twice, even across re-syncs.
    """

    __tablename__ = "tally_entity_versions"
    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "company_name",
            "guid",
            "xml_hash",
            name="uq_entity_versions_type_company_guid_hash",
        ),
        Index("ix_entity_versions_type_company_guid", "entity_type", "company_name", "guid"),
        Index("ix_entity_versions_created_at", "created_at"),
        Index("ix_entity_versions_alter_id", "entity_type", "company_name", "alter_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xml_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    xml: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[type-arg]
    unknown_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[type-arg]
    parser_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    sync_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
