from __future__ import annotations

import datetime
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.database.bulk import bulk_upsert
from app.models.db.inventory import GodownModel, StockGroupModel, StockItemModel, UnitModel
from app.models.domain.godown import GodownRecord
from app.models.domain.stock_group import StockGroupRecord
from app.models.domain.stock_item import StockItemRecord
from app.models.domain.unit import UnitRecord
from app.repositories.base import BaseRepository

_UNIT_UPDATE = ["guid", "gst_unit_name", "formal_name", "is_simple_unit", "alter_id", "synced_at"]
_GODOWN_UPDATE = ["guid", "parent", "has_no_stock", "alter_id", "synced_at"]
_STOCK_GROUP_UPDATE = ["guid", "parent", "is_addable", "alter_id", "synced_at"]
_STOCK_ITEM_UPDATE = [
    "guid",
    "parent",
    "category",
    "base_units",
    "gst_applicable",
    "gst_type_of_supply",
    "hsn_code",
    "description",
    "opening_balance",
    "opening_rate",
    "opening_value",
    "closing_balance",
    "closing_rate",
    "closing_value",
    "alter_id",
    "synced_at",
]


class UnitRepository(BaseRepository[UnitRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[UnitRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "gst_unit_name": rec.gst_unit_name,
                "formal_name": rec.formal_name,
                "is_simple_unit": rec.is_simple_unit,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            UnitModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_UNIT_UPDATE,
        )


class GodownRepository(BaseRepository[GodownRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[GodownRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "parent": rec.parent,
                "has_no_stock": rec.has_no_stock,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            GodownModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_GODOWN_UPDATE,
        )


class StockGroupRepository(BaseRepository[StockGroupRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[StockGroupRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "parent": rec.parent,
                "is_addable": rec.is_addable,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            StockGroupModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_STOCK_GROUP_UPDATE,
        )


class StockItemRepository(BaseRepository[StockItemRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[StockItemRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "parent": rec.parent,
                "category": rec.category,
                "base_units": rec.base_units,
                "gst_applicable": rec.gst_applicable,
                "gst_type_of_supply": rec.gst_type_of_supply,
                "hsn_code": rec.hsn_code,
                "description": rec.description,
                "opening_balance": rec.opening_balance,
                "opening_rate": rec.opening_rate,
                "opening_value": rec.opening_value,
                "closing_balance": rec.closing_balance,
                "closing_rate": rec.closing_rate,
                "closing_value": rec.closing_value,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            StockItemModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_STOCK_ITEM_UPDATE,
        )
