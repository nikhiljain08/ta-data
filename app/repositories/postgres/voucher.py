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

# Keep each INSERT well under PostgreSQL's 65,535 bind-parameter ceiling.
# Voucher headers: 12 cols → 500 rows = 6,000 params (safe).
# Child rows: 4-7 cols x 500 rows = 2,000-3,500 params (safe).
_CHUNK_SIZE = 500


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

        # 1. Upsert voucher headers in chunks; accumulate id_map via RETURNING.
        id_map: dict[tuple[str, str], int] = {}
        for i in range(0, len(deduped), _CHUNK_SIZE):
            chunk = deduped[i : i + _CHUNK_SIZE]
            chunk_rows = [
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
                for rec in chunk
            ]
            stmt = insert(VoucherModel).values(chunk_rows)
            update_dict = {col: getattr(stmt.excluded, col) for col in _VOUCHER_UPDATE}
            stmt = stmt.on_conflict_do_update(
                index_elements=["company_name", "voucher_number", "voucher_type"],
                set_=update_dict,
            ).returning(
                VoucherModel.id,
                VoucherModel.voucher_number,
                VoucherModel.voucher_type,
            )
            for row in self._session.execute(stmt).all():
                id_map[(row.voucher_number, row.voucher_type)] = row.id

        if not id_map:
            return 0

        voucher_ids = list(id_map.values())

        # 2. Delete stale child rows for these vouchers.
        # IN clauses with ~6k IDs are fine (one param per ID, well under 65k).
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

        # 3. Build fresh child rows.
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

        # 4. Insert child rows in chunks to stay under the 65,535-param ceiling.
        for i in range(0, len(ledger_rows), _CHUNK_SIZE):
            self._session.execute(
                insert(VoucherLedgerEntryModel).values(ledger_rows[i : i + _CHUNK_SIZE])
            )
        for i in range(0, len(inv_rows), _CHUNK_SIZE):
            self._session.execute(
                insert(VoucherInventoryEntryModel).values(inv_rows[i : i + _CHUNK_SIZE])
            )
        for i in range(0, len(gst_rows), _CHUNK_SIZE):
            self._session.execute(insert(GstDetailModel).values(gst_rows[i : i + _CHUNK_SIZE]))

        return len(deduped)
