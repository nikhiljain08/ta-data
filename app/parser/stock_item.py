from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.stock_item import StockItemRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "PARENT",
        "CATEGORY",
        "BASEUNITS",
        "GSTAPPLICABLE",
        "GSTTYPEOFSUPPLY",
        "HSNCODE",
        "DESCRIPTION",
        "OPENINGBALANCE",
        "OPENINGRATE",
        "OPENINGVALUE",
        "CLOSINGBALANCE",
        "CLOSINGRATE",
        "CLOSINGVALUE",
        "ALTERID",
    }
)


def parse_stock_items(source: XmlSource) -> Iterator[StockItemRecord]:
    """Yield one StockItemRecord per <STOCKITEM> element in the XML response."""
    for elem in base.iter_collection(source, "STOCKITEM"):
        yield _build(elem)


def parse_stock_items_with_raw(
    source: XmlSource,
) -> Iterator[tuple[StockItemRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <STOCKITEM> element."""
    for elem, raw in base.iter_collection_with_raw(source, "STOCKITEM"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> StockItemRecord:
    return StockItemRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        parent=base.text(elem, "PARENT"),
        category=base.text(elem, "CATEGORY"),
        base_units=base.text(elem, "BASEUNITS"),
        gst_applicable=base.text(elem, "GSTAPPLICABLE"),
        gst_type_of_supply=base.text(elem, "GSTTYPEOFSUPPLY"),
        hsn_code=base.text(elem, "HSNCODE"),
        description=base.text(elem, "DESCRIPTION"),
        opening_balance=base.quantity(elem, "OPENINGBALANCE"),
        opening_rate=base.rate(elem, "OPENINGRATE"),
        opening_value=base.decimal_amount(elem, "OPENINGVALUE"),
        closing_balance=base.quantity(elem, "CLOSINGBALANCE"),
        closing_rate=base.rate(elem, "CLOSINGRATE"),
        closing_value=base.decimal_amount(elem, "CLOSINGVALUE"),
        alter_id=base.integer(elem, "ALTERID"),
    )
