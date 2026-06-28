from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UnitRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    gst_unit_name: str = ""  # GST unit code, e.g. "OTH", "BOX", "NOS"
    formal_name: str = ""
    is_simple_unit: bool = True
    alter_id: int = 0
