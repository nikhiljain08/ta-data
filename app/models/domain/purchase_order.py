from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PurchaseOrderItemRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    stock_item_name: str
    quantity: Decimal = Decimal(0)       # ActualQty — ordered qty
    billed_qty: Decimal = Decimal(0)     # BilledQty — received so far
    rate: Decimal = Decimal(0)
    amount: Decimal = Decimal(0)
    godown_name: str = ""


class PurchaseOrderRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    voucher_number: str
    date: str          # YYYYMMDD
    party_ledger: str = ""
    narration: str = ""
    order_due_date: str = ""   # YYYYMMDD — expected delivery date
    is_cancelled: bool = False
    is_optional: bool = False
    guid: str = ""
    alter_id: int = 0
    items: tuple[PurchaseOrderItemRecord, ...] = ()
