from __future__ import annotations

import datetime
import io
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.models.domain.voucher import VoucherRecord
from app.parser.base import XmlSource
from app.parser.voucher import parse_vouchers
from app.repositories.base import BaseRepository
from app.repositories.postgres.voucher import VoucherRepository
from app.services.base import BaseSyncService
from app.sync.streaming import IteratorIO


def _financial_year_start() -> str:
    """Return the start of the current Indian financial year as YYYYMMDD."""
    today = datetime.date.today()
    year = today.year if today.month >= 4 else today.year - 1
    return f"{year}0401"


class VoucherSyncService(BaseSyncService[VoucherRecord]):
    """Syncs vouchers (sales, purchase, payments, receipts, journals).

    Vouchers are the largest dataset — uses streaming HTTP to avoid buffering
    the full response in memory.  The date window defaults to the current
    financial year; pass from_date to override.
    """

    entity_name = "voucher"

    def __init__(self, *args: object, from_date: str = "", **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._from_date = from_date

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        today = datetime.date.today().strftime("%Y%m%d")
        from_date = self._from_date or _financial_year_start()
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

    def _parse(self, source: XmlSource) -> Iterator[VoucherRecord]:
        return parse_vouchers(source)

    def _make_repo(self, session: Session) -> BaseRepository[VoucherRecord]:
        return VoucherRepository(session)
