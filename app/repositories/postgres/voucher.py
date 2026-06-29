from __future__ import annotations

import datetime
from collections.abc import Sequence

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.db.voucher import (
    GstDetailModel,
    VoucherInventoryEntryModel,
    VoucherLedgerEntryModel,
    VoucherModel,
)
from app.models.domain.voucher import VoucherRecord
from app.repositories.base import BaseRepository

_VOUCHER_UPDATE = [
    "date",
    "party_ledger",
    "narration",
    "is_invoice",
    "is_cancelled",
    "is_optional",
    "guid",
    "alter_id",
    "synced_at",
]


class VoucherRepository(BaseRepository[VoucherRecord]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_batch(self, company_name: str, records: Sequence[VoucherRecord]) -> int:
        if not records:
            return 0

        now = datetime.datetime.now(tz=datetime.UTC)

        # Deduplicate by natural key within the batch: ON CONFLICT DO UPDATE rejects
        # duplicate constrained values in the same INSERT command (CardinalityViolation).
        # Keep the record with the highest alter_id when duplicates exist.
        seen: dict[tuple[str, str], VoucherRecord] = {}
        for rec in records:
            key = (rec.voucher_number, rec.voucher_type)
            if key not in seen or rec.alter_id > seen[key].alter_id:
                seen[key] = rec
        deduped = list(seen.values())

        # 1. Upsert voucher headers; get id mapping via RETURNING
        header_rows = [
            {
                "company_name": company_name,
                "voucher_number": rec.voucher_number,
                "voucher_type": rec.voucher_type,
                "date": rec.date,
                "party_ledger": rec.party_ledger,
                "narration": rec.narration,
                "is_invoice": rec.is_invoice,
                "is_cancelled": rec.is_cancelled,
                "is_optional": rec.is_optional,
                "guid": rec.guid,
                "alter_id": rec.alter_id,
                "synced_at": now,
            }
            for rec in deduped
        ]
        stmt = insert(VoucherModel).values(header_rows)
        update_dict = {col: getattr(stmt.excluded, col) for col in _VOUCHER_UPDATE}
        stmt = stmt.on_conflict_do_update(
            index_elements=["company_name", "voucher_number", "voucher_type"],
            set_=update_dict,
        ).returning(
            VoucherModel.id,
            VoucherModel.voucher_number,
            VoucherModel.voucher_type,
        )
        rows = self._session.execute(stmt).all()
        id_map: dict[tuple[str, str], int] = {
            (row.voucher_number, row.voucher_type): row.id for row in rows
        }

        if not id_map:
            return 0

        voucher_ids = list(id_map.values())

        # 2. Delete stale child rows for these vouchers
        self._session.execute(
            delete(VoucherLedgerEntryModel).where(
                VoucherLedgerEntryModel.voucher_id.in_(voucher_ids)
            )
        )
        self._session.execute(
            delete(VoucherInventoryEntryModel).where(
                VoucherInventoryEntryModel.voucher_id.in_(voucher_ids)
            )
        )
        self._session.execute(
            delete(GstDetailModel).where(GstDetailModel.voucher_id.in_(voucher_ids))
        )

        # 3. Insert fresh child rows
        ledger_rows: list[dict[str, object]] = []
        inv_rows: list[dict[str, object]] = []
        gst_rows: list[dict[str, object]] = []
        for rec in deduped:
            vid = id_map.get((rec.voucher_number, rec.voucher_type))
            if vid is None:
                continue
            for entry in rec.ledger_entries:
                ledger_rows.append(
                    {
                        "voucher_id": vid,
                        "ledger_name": entry.ledger_name,
                        "is_deemed_positive": entry.is_deemed_positive,
                        "amount": entry.amount,
                    }
                )
            for entry in rec.inventory_entries:
                inv_rows.append(
                    {
                        "voucher_id": vid,
                        "stock_item_name": entry.stock_item_name,
                        "is_deemed_positive": entry.is_deemed_positive,
                        "quantity": entry.quantity,
                        "rate": entry.rate,
                        "amount": entry.amount,
                        "godown_name": entry.godown_name,
                    }
                )
            for gst in rec.gst_details:
                gst_rows.append(
                    {
                        "voucher_id": vid,
                        "hsn_code": gst.hsn_code,
                        "taxable_value": gst.taxable_value,
                        "igst_amount": gst.igst_amount,
                        "cgst_amount": gst.cgst_amount,
                        "sgst_amount": gst.sgst_amount,
                        "gst_type": gst.gst_type,
                    }
                )

        if ledger_rows:
            self._session.execute(insert(VoucherLedgerEntryModel).values(ledger_rows))
        if inv_rows:
            self._session.execute(insert(VoucherInventoryEntryModel).values(inv_rows))
        if gst_rows:
            self._session.execute(insert(GstDetailModel).values(gst_rows))

        return len(deduped)
