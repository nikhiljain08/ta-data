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
        "GSTDETAILS.LIST",
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

# ASCII control characters used by Tally as internal markers (e.g. \x04 before
# "Applicable") must be stripped from display strings before storing.
_CTRL_CHARS = "".join(chr(i) for i in range(32) if i not in (9, 10, 13))


def _clean(s: str) -> str:
    return s.strip(_CTRL_CHARS).strip()


def _hsn_from_gst_details(elem: Any) -> str:
    """Read HSNCode from the GSTDetails sub-collection.

    Flat $HSNCode on StockItem returns nothing in TallyPrime 7; the value
    lives in GSTDetails.  Return the first non-empty HSN found, or fall back
    to the legacy flat <HSNCODE> tag for historical archive rows.
    """
    for detail in elem.findall("GSTDETAILS.LIST"):
        hsn = base.text(detail, "HSNCODE")
        if hsn:
            return hsn
    return base.text(elem, "HSNCODE")


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
        gst_applicable=_clean(base.text(elem, "GSTAPPLICABLE")),
        gst_type_of_supply=_clean(base.text(elem, "GSTTYPEOFSUPPLY")),
        hsn_code=_hsn_from_gst_details(elem),
        description=base.text(elem, "DESCRIPTION"),
        opening_balance=base.quantity(elem, "OPENINGBALANCE"),
        opening_rate=base.rate(elem, "OPENINGRATE"),
        opening_value=base.decimal_amount(elem, "OPENINGVALUE"),
        closing_balance=base.quantity(elem, "CLOSINGBALANCE"),
        closing_rate=base.rate(elem, "CLOSINGRATE"),
        closing_value=base.decimal_amount(elem, "CLOSINGVALUE"),
        alter_id=base.integer(elem, "ALTERID"),
    )
