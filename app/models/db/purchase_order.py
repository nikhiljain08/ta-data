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


class PurchaseOrderModel(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint(
            "company_name",
            "voucher_number",
            name="uq_purchase_orders_company_number",
        ),
        Index("ix_po_company_date", "company_name", "date"),
        Index("ix_po_party_ledger", "party_ledger"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(_COMPANY, nullable=False)
    voucher_number: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    party_ledger: Mapped[str] = mapped_column(_NAME, nullable=False, default="")
    narration: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_due_date: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guid: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    alter_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    items: Mapped[list[PurchaseOrderItemModel]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderItemModel(Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        Index("ix_poi_po_id", "po_id"),
        Index("ix_poi_stock_item", "stock_item_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    stock_item_name: Mapped[str] = mapped_column(_NAME, nullable=False)
    quantity: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    billed_qty: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    rate: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    amount: Mapped[float] = mapped_column(_AMOUNT, nullable=False, default=0)
    godown_name: Mapped[str] = mapped_column(_NAME, nullable=False, default="")

    purchase_order: Mapped[PurchaseOrderModel] = relationship(back_populates="items")
