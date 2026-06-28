from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin

_AMOUNT = Numeric(18, 4)
_NAME = String(500)
_COMPANY = String(500)


class LedgerGroupModel(TimestampMixin, Base):
    __tablename__ = "ledger_groups"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_ledger_groups_company_name"),
        Index("ix_ledger_groups_company_alter_id", "company_name", "alter_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    parent: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    is_deemed_positive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_revenue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    affects_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LedgerModel(TimestampMixin, Base):
    __tablename__ = "ledgers"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_ledgers_company_name"),
        Index("ix_ledgers_company_alter_id", "company_name", "alter_id"),
        Index("ix_ledgers_gstin", "gstin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    parent: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    is_deemed_positive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    opening_balance: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    closing_balance: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    gst_registration_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    gstin: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    pan: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    mobile: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    pincode: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    # PostgreSQL TEXT[] — stored as array of address lines
    address: Mapped[list[str]] = mapped_column(  # type: ignore[type-arg]
        ARRAY(String(500)), nullable=False, default=list, server_default="{}"
    )
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class VoucherTypeModel(TimestampMixin, Base):
    __tablename__ = "voucher_types"
    __table_args__ = (
        UniqueConstraint("company_name", "name", name="uq_voucher_types_company_name"),
        Index("ix_voucher_types_company_alter_id", "company_name", "alter_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    name: Mapped[str] = mapped_column(_NAME, nullable=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    parent: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    numbering_method: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
