from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class VoucherLedgerEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    ledger_name: str
    is_deemed_positive: bool = False
    amount: Decimal = Decimal(0)


class VoucherInventoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    stock_item_name: str
    is_deemed_positive: bool = False
    quantity: Decimal = Decimal(0)
    rate: Decimal = Decimal(0)
    amount: Decimal = Decimal(0)
    godown_name: str = ""


class GstDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    hsn_code: str = ""
    taxable_value: Decimal = Decimal(0)
    igst_amount: Decimal = Decimal(0)
    cgst_amount: Decimal = Decimal(0)
    sgst_amount: Decimal = Decimal(0)
    gst_type: str = ""


class VoucherRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    voucher_number: str
    voucher_type: str
    date: str  # YYYYMMDD string as returned by Tally
    party_ledger: str = ""
    narration: str = ""
    is_invoice: bool = False
    is_cancelled: bool = False
    is_optional: bool = False
    guid: str = ""
    alter_id: int = 0
    ledger_entries: tuple[VoucherLedgerEntry, ...] = ()
    inventory_entries: tuple[VoucherInventoryEntry, ...] = ()
    gst_details: tuple[GstDetail, ...] = ()
