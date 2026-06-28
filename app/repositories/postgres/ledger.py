from __future__ import annotations

import datetime
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.database.bulk import bulk_upsert
from app.models.db.ledger import LedgerGroupModel, LedgerModel, VoucherTypeModel
from app.models.domain.ledger import LedgerRecord
from app.models.domain.ledger_group import LedgerGroupRecord
from app.models.domain.voucher_type import VoucherTypeRecord
from app.repositories.base import BaseRepository

_LEDGER_GROUP_UPDATE = [
    "guid",
    "parent",
    "is_deemed_positive",
    "is_revenue",
    "affects_stock",
    "alter_id",
    "synced_at",
]
_LEDGER_UPDATE = [
    "guid",
    "parent",
    "is_deemed_positive",
    "opening_balance",
    "closing_balance",
    "gst_registration_type",
    "gstin",
    "pan",
    "mobile",
    "email",
    "country",
    "state",
    "pincode",
    "address",
    "alter_id",
    "synced_at",
]
_VOUCHER_TYPE_UPDATE = [
    "guid",
    "parent",
    "numbering_method",
    "is_active",
    "alter_id",
    "synced_at",
]


class LedgerGroupRepository(BaseRepository[LedgerGroupRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[LedgerGroupRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "parent": rec.parent,
                "is_deemed_positive": rec.is_deemed_positive,
                "is_revenue": rec.is_revenue,
                "affects_stock": rec.affects_stock,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            LedgerGroupModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_LEDGER_GROUP_UPDATE,
        )


class LedgerRepository(BaseRepository[LedgerRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[LedgerRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "parent": rec.parent,
                "is_deemed_positive": rec.is_deemed_positive,
                "opening_balance": rec.opening_balance,
                "closing_balance": rec.closing_balance,
                "gst_registration_type": rec.gst_registration_type,
                "gstin": rec.gstin,
                "pan": rec.pan,
                "mobile": rec.mobile,
                "email": rec.email,
                "country": rec.country,
                "state": rec.state,
                "pincode": rec.pincode,
                "address": rec.address,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            LedgerModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_LEDGER_UPDATE,
        )


class VoucherTypeRepository(BaseRepository[VoucherTypeRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[VoucherTypeRecord]) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "company_name": company_name,
                "name": rec.name,
                "guid": rec.guid,
                "parent": rec.parent,
                "numbering_method": rec.numbering_method,
                "is_active": rec.is_active,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in records
        ]
        return bulk_upsert(
            self._session,
            VoucherTypeModel,
            rows,
            conflict_columns=["company_name", "name"],
            update_columns=_VOUCHER_TYPE_UPDATE,
        )
