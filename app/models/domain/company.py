from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CompanyRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    guid: str = ""
    books_from: str = ""  # YYYYMMDD — first day of books
    starting_from: str = ""  # financial-year start
    ending_at: str = ""  # financial-year end
    country: str = ""
    state: str = ""
    gstin: str = ""
    alter_id: int = 0
