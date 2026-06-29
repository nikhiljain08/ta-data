from __future__ import annotations

import datetime
import hashlib
import io
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain.voucher import VoucherRecord
from app.parser.base import XmlSource
from app.parser.voucher import parse_vouchers, parse_vouchers_with_raw
from app.repositories.base import BaseRepository
from app.repositories.postgres.voucher import VoucherRepository
from app.services.base import BaseSyncService, _FidelityRow
from app.sync.streaming import IteratorIO

_EPOCH = "19000101"  # earlier than any Tally company data


class VoucherSyncService(BaseSyncService[VoucherRecord]):
    """Syncs vouchers (sales, purchase, payments, receipts, journals).

    Vouchers are the largest dataset — uses streaming HTTP to avoid buffering
    the full response in memory.  Fetches all dates by default; pass from_date
    to restrict (e.g. for backfill testing).
    """

    entity_name = "voucher"

    def __init__(self, *args: object, from_date: str = "", **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._from_date = from_date

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        today = datetime.date.today().strftime("%Y%m%d")
        from_date = self._from_date or _EPOCH
        return self._template.vouchers(
            company=company_name,
            from_date=from_date,
            to_date=today,
            alter_id=alter_id,
        )

    def _fetch_and_parse(self, xml: str) -> list[VoucherRecord]:
        chunks = self._client.stream_request(xml)
        source: io.RawIOBase = IteratorIO(chunks)
        return list(parse_vouchers(io.BufferedReader(source)))

    def _fetch_and_parse_with_raw(self, xml: str) -> list[_FidelityRow[VoucherRecord]]:
        chunks = self._client.stream_request(xml)
        source: io.RawIOBase = IteratorIO(chunks)
        result: list[_FidelityRow[VoucherRecord]] = []
        for record, raw, unknown in parse_vouchers_with_raw(io.BufferedReader(source)):
            xml_hash = hashlib.sha256(raw).hexdigest()
            result.append((record, raw, xml_hash, unknown))
        return result

    def _parse(self, source: XmlSource) -> Iterator[VoucherRecord]:
        return parse_vouchers(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[VoucherRecord, bytes, dict[str, Any]]]:
        return parse_vouchers_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[VoucherRecord]:
        return VoucherRepository(session)
