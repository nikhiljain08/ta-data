from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StockGroupRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    parent: str = ""  # empty for root stock groups
    is_addable: bool = False
    alter_id: int = 0
