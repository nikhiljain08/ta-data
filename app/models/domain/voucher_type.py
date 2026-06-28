from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VoucherTypeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    parent: str = ""  # base Tally voucher class (Sales, Purchase, …)
    numbering_method: str = ""  # Automatic / Manual / Prevent Duplicates
    is_active: bool = True
    alter_id: int = 0
