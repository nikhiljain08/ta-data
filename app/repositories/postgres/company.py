from __future__ import annotations

import datetime
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.database.bulk import bulk_upsert
from app.models.db.company import CompanyModel
from app.models.domain.company import CompanyRecord
from app.repositories.base import BaseRepository

_UPDATE_COLS = [
    "guid",
    "books_from",
    "starting_from",
    "ending_at",
    "country",
    "state",
    "gstin",
    "alter_id",
    "synced_at",
]


class CompanyRepository(BaseRepository[CompanyRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[CompanyRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "name": rec.name,
                "guid": rec.guid,
                "books_from": rec.books_from,
                "starting_from": rec.starting_from,
                "ending_at": rec.ending_at,
                "country": rec.country,
                "state": rec.state,
                "gstin": rec.gstin,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            CompanyModel,
            rows,
            conflict_columns=["name"],
            update_columns=_UPDATE_COLS,
        )
