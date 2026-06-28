from __future__ import annotations

from sqlalchemy import Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin


class CompanyModel(TimestampMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("name", name="uq_companies_name"),
        Index("ix_companies_alter_id", "alter_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    books_from: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    starting_from: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    ending_at: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    gstin: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
