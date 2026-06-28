from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LedgerGroupRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    parent: str = ""  # empty for root groups (e.g. Capital Account)
    is_deemed_positive: bool = False
    is_revenue: bool = False
    affects_stock: bool = False
    alter_id: int = 0
