from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GodownRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    parent: str = ""  # parent godown; empty for top-level locations
    has_no_stock: bool = False
    alter_id: int = 0
