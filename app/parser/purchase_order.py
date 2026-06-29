from __future__ import annotations

from collections.abc import Iterator

import lxml.etree as etree

from app.models.domain.purchase_order import PurchaseOrderItemRecord, PurchaseOrderRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_purchase_orders(source: XmlSource) -> Iterator[PurchaseOrderRecord]:
    """Yield one PurchaseOrderRecord per <VOUCHER> element in the XML response."""
    for elem in base.iter_collection(source, "VOUCHER"):
        yield _build_record(elem)


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
