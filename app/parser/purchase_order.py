from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import lxml.etree as etree

from app.models.domain.purchase_order import PurchaseOrderItemRecord, PurchaseOrderRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "VOUCHERNUMBER",
        "DATE",
        "PARTYLEDGERNAME",
        "NARRATION",
        "ORDERDUEDATE",
        "ISCANCELLED",
        "ISOPTIONAL",
        "GUID",
        "ALTERID",
        "ALLINVENTORYENTRIES.LIST",
    }
)


def parse_purchase_orders(source: XmlSource) -> Iterator[PurchaseOrderRecord]:
    """Yield one PurchaseOrderRecord per <VOUCHER> element in the XML response."""
    for elem in base.iter_collection(source, "VOUCHER"):
        yield _build_record(elem)


def parse_purchase_orders_with_raw(
    source: XmlSource,
) -> Iterator[tuple[PurchaseOrderRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <VOUCHER> element."""
    for elem, raw in base.iter_collection_with_raw(source, "VOUCHER"):
        yield _build_record(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build_record(elem: etree._Element) -> PurchaseOrderRecord:
    return PurchaseOrderRecord(
        voucher_number=base.text(elem, "VOUCHERNUMBER"),
        date=base.tally_date(elem, "DATE"),
        party_ledger=base.text(elem, "PARTYLEDGERNAME"),
        narration=base.text(elem, "NARRATION"),
        order_due_date=base.tally_date(elem, "ORDERDUEDATE"),
        is_cancelled=base.bool_yes(elem, "ISCANCELLED"),
        is_optional=base.bool_yes(elem, "ISOPTIONAL"),
        guid=base.text(elem, "GUID"),
        alter_id=base.integer(elem, "ALTERID"),
        items=tuple(_parse_items(elem)),
    )


def _parse_items(voucher: etree._Element) -> list[PurchaseOrderItemRecord]:
    items: list[PurchaseOrderItemRecord] = []
    for tag in ("ALLINVENTORYENTRIES.LIST", "INVENTORYENTRIES.LIST"):
        for entry in voucher.findall(tag):
            stock_item = base.text(entry, "STOCKITEMNAME")
            if stock_item:
                items.append(
                    PurchaseOrderItemRecord(
                        stock_item_name=stock_item,
                        quantity=base.quantity(entry, "ACTUALQTY"),
                        billed_qty=base.quantity(entry, "BILLEDQTY"),
                        rate=base.rate(entry, "RATE"),
                        amount=base.decimal_amount(entry, "AMOUNT"),
                        godown_name=base.text(entry, "GODOWNNAME"),
                    )
                )
    return items
