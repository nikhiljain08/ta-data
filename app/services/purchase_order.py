from __future__ import annotations

import datetime
import hashlib
import io
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain.purchase_order import PurchaseOrderRecord
from app.parser.base import XmlSource
from app.parser.purchase_order import parse_purchase_orders, parse_purchase_orders_with_raw
from app.repositories.base import BaseRepository
from app.repositories.postgres.purchase_order import PurchaseOrderRepository
from app.services.base import BaseSyncService, _FidelityRow
from app.sync.streaming import IteratorIO

_EPOCH = "19000101"


class PurchaseOrderSyncService(BaseSyncService[PurchaseOrderRecord]):
    """Syncs Purchase Order vouchers from TallyPrime.

    Purchase Orders are vouchers of type 'Purchase Order' — they represent
    intended purchases before a Purchase Bill is created.  Stored separately
    from the vouchers table so consumers can query open orders independently.
    """

    entity_name = "purchase_order"

    def __init__(self, *args: object, from_date: str = "", **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._from_date = from_date

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        today = datetime.date.today().strftime("%Y%m%d")
        from_date = self._from_date or _EPOCH
        return self._template.purchase_orders(
            company=company_name,
            from_date=from_date,
            to_date=today,
            alter_id=alter_id,
        )

    def _fetch_and_parse(self, xml: str) -> list[PurchaseOrderRecord]:
        chunks = self._client.stream_request(xml)
        source: io.RawIOBase = IteratorIO(chunks)
        return list(parse_purchase_orders(io.BufferedReader(source)))

    def _fetch_and_parse_with_raw(self, xml: str) -> list[_FidelityRow[PurchaseOrderRecord]]:
        chunks = self._client.stream_request(xml)
        source: io.RawIOBase = IteratorIO(chunks)
        result: list[_FidelityRow[PurchaseOrderRecord]] = []
        for record, raw, unknown in parse_purchase_orders_with_raw(io.BufferedReader(source)):
            xml_hash = hashlib.sha256(raw).hexdigest()
            result.append((record, raw, xml_hash, unknown))
        return result

    def _parse(self, source: XmlSource) -> Iterator[PurchaseOrderRecord]:
        return parse_purchase_orders(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[PurchaseOrderRecord, bytes, dict[str, Any]]]:
        return parse_purchase_orders_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[PurchaseOrderRecord]:
        return PurchaseOrderRepository(session)
