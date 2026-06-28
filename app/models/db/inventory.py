from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin

_AMOUNT = Numeric(18, 4)
_NAME = String(500)
_COMPANY = String(500)


class UnitModel(TimestampMixin, Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_units_company_name"),
        Index("ix_units_company_alter_id", "company_name", "alter_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    gst_unit_name: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    formal_name: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    is_simple_unit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class GodownModel(TimestampMixin, Base):
    __tablename__ = "godowns"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_godowns_company_name"),
        Index("ix_godowns_company_alter_id", "company_name", "alter_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    parent: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    has_no_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class StockGroupModel(TimestampMixin, Base):
    __tablename__ = "stock_groups"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_stock_groups_company_name"),
        Index("ix_stock_groups_company_alter_id", "company_name", "alter_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    parent: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    is_addable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class StockItemModel(TimestampMixin, Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_stock_items_company_name"),
        Index("ix_stock_items_company_alter_id", "company_name", "alter_id"),
        Index("ix_stock_items_hsn", "hsn_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    parent: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    category: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    base_units: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    gst_applicable: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    gst_type_of_supply: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    opening_balance: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    opening_rate: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    opening_value: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    closing_balance: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    closing_rate: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    closing_value: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
