from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base


class SyncCheckpointModel(Base):
    """Stores the maximum AlterID seen per (company, entity_type).

    Used by the SyncEngine to decide whether to do a full or incremental sync.
    alter_id == 0 means no sync has been run yet for this entity.
    """

    __tablename__ = "sync_checkpoints"
    __table_args__ = (
        UniqueConstraint("company_name", "entity_type", name="uq_sync_checkpoints_company_entity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    last_alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SyncRunModel(Base):
    """Audit log: one row per sync execution attempt."""

    __tablename__ = "sync_runs"
    __table_args__ = (
        Index("ix_sync_runs_company_entity", "company_name", "entity_type"),
        Index("ix_sync_runs_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    records_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
