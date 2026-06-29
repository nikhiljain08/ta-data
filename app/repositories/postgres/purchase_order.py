from __future__ import annotations

import datetime
from collections.abc import Sequence

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.db.purchase_order import PurchaseOrderItemModel, PurchaseOrderModel
from app.models.domain.purchase_order import PurchaseOrderRecord
from app.repositories.base import BaseRepository

_PO_UPDATE = [
    "date",
    "party_ledger",
    "narration",
    "order_due_date",
    "is_cancelled",
    "is_optional",
    "guid",
    "alter_id",
    "synced_at",
]


class PurchaseOrderRepository(BaseRepository[PurchaseOrderRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[PurchaseOrderRecord]) -> int:
        if not records:
            return 0

        now = datetime.datetime.now(tz=datetime.UTC)

        # Deduplicate by natural key to avoid CardinalityViolation.
        seen: dict[str, PurchaseOrderRecord] = {}
        for rec in records:
            if rec.voucher_number not in seen or rec.alter_id > seen[rec.voucher_number].alter_id:
                seen[rec.voucher_number] = rec
        deduped = list(seen.values())

        header_rows = [
            {
                "company_name": company_name,
                "voucher_number": rec.voucher_number,
                "date": rec.date,
                "party_ledger": rec.party_ledger,
                "narration": rec.narration,
                "order_due_date": rec.order_due_date,
                "is_cancelled": rec.is_cancelled,
                "is_optional": rec.is_optional,
                "guid": rec.guid,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in deduped
        ]

        stmt = insert(PurchaseOrderModel).values(header_rows)
        update_dict = {col: getattr(stmt.excluded, col) for col in _PO_UPDATE}
        stmt = stmt.on_conflict_do_update(
            index_elements=["company_name", "voucher_number"],
            set_=update_dict,
        ).returning(PurchaseOrderModel.id, PurchaseOrderModel.voucher_number)
        rows = self._session.execute(stmt).all()
        id_map: dict[str, int] = {row.voucher_number: row.id for row in rows}

        if not id_map:
            return 0

        # Delete stale items then insert fresh ones.
        self._session.execute(
            delete(PurchaseOrderItemModel).where(PurchaseOrderItemModel.po_id.in_(id_map.values()))
        )

        item_rows: list[dict[str, object]] = []
        for rec in deduped:
            po_id = id_map.get(rec.voucher_number)
            if po_id is None:
                continue
            for item in rec.items:
                item_rows.append(
                    {
                        "po_id": po_id,
                        "stock_item_name": item.stock_item_name,
                        "quantity": item.quantity,
                        "billed_qty": item.billed_qty,
                        "rate": item.rate,
                        "amount": item.amount,
                        "godown_name": item.godown_name,
                    }
                )

        if item_rows:
            self._session.execute(insert(PurchaseOrderItemModel).values(item_rows))

        return len(deduped)
