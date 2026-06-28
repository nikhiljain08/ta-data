from __future__ import annotations

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db.base import Base, TimestampMixin

_AMOUNT = Numeric(18, 4)
_NAME = String(500)
_COMPANY = String(500)


class VoucherModel(TimestampMixin, Base):
    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint(
            "company_name",
            "voucher_number",
            "voucher_type",
            name="uq_vouchers_company_number_type",
        ),
        Index("ix_vouchers_company_date", "company_name", "date"),
        Index("ix_vouchers_company_alter_id", "company_name", "alter_id"),
        Index("ix_vouchers_party_ledger", "party_ledger"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    voucher_number: Mapped[str] = mapped_column(String(100), nullable=False)
    voucher_type: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[str] = mapped_column(String(8), nullable=False, default="")  # YYYYMMDD
    party_ledger: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    narration: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_invoice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    ledger_entries: Mapped[list[VoucherLedgerEntryModel]] = relationship(
        back_populates="voucher", cascade="all, delete-orphan"
    )
    inventory_entries: Mapped[list[VoucherInventoryEntryModel]] = relationship(
        back_populates="voucher", cascade="all, delete-orphan"
    )
    gst_details: Mapped[list[GstDetailModel]] = relationship(
        back_populates="voucher", cascade="all, delete-orphan"
    )


class VoucherLedgerEntryModel(Base):
    __tablename__ = "voucher_ledger_entries"
    __table_args__ = (
        Index("ix_vle_voucher_id", "voucher_id"),
        Index("ix_vle_ledger_name", "ledger_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vouchers.id", ondelete="CASCADE"), nullable=False
    )
    ledger_name: Mapped[str] = mapped_column(_NAME, nullable=False)
    is_deemed_positive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amount: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)

    voucher: Mapped[VoucherModel] = relationship(back_populates="ledger_entries")


class VoucherInventoryEntryModel(Base):
    __tablename__ = "voucher_inventory_entries"
    __table_args__ = (
        Index("ix_vie_voucher_id", "voucher_id"),
        Index("ix_vie_stock_item", "stock_item_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vouchers.id", ondelete="CASCADE"), nullable=False
    )
    stock_item_name: Mapped[str] = mapped_column(_NAME, nullable=False)
    is_deemed_positive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quantity: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    rate: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    amount: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    godown_name: Mapped[str] = mapped_column(_NAME, nullable=False, default="")

    voucher: Mapped[VoucherModel] = relationship(back_populates="inventory_entries")


class GstDetailModel(Base):
    __tablename__ = "gst_details"
    __table_args__ = (
        Index("ix_gst_voucher_id", "voucher_id"),
        Index("ix_gst_hsn", "hsn_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vouchers.id", ondelete="CASCADE"), nullable=False
    )
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    taxable_value: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    igst_amount: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    cgst_amount: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    sgst_amount: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    gst_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    voucher: Mapped[VoucherModel] = relationship(back_populates="gst_details")
