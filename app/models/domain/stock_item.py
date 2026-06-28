from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StockItemRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    parent: str = ""  # stock group
    category: str = ""  # stock category (optional feature)
    base_units: str = ""  # unit of measure name
    gst_applicable: str = ""  # Applicable / Not Applicable
    gst_type_of_supply: str = ""  # Goods / Services
    hsn_code: str = ""
    description: str = ""
    opening_balance: Decimal = Decimal(0)
    opening_rate: Decimal = Decimal(0)
    opening_value: Decimal = Decimal(0)
    closing_balance: Decimal = Decimal(0)
    closing_rate: Decimal = Decimal(0)
    closing_value: Decimal = Decimal(0)
    alter_id: int = 0
