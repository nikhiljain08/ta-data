from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LedgerRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    parent: str = ""  # parent ledger group
    is_deemed_positive: bool = False
    opening_balance: Decimal = Decimal(0)
    closing_balance: Decimal = Decimal(0)
    gst_registration_type: str = ""  # Unregistered / Regular / Composition
    gstin: str = ""
    pan: str = ""
    mobile: str = ""
    email: str = ""
    country: str = ""
    state: str = ""
    pincode: str = ""
    address: list[str] = []
    alter_id: int = 0
