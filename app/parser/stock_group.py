from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.stock_group import StockGroupRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "PARENT",
        "ISADDABLE",
        "ALTERID",
    }
)


def parse_stock_groups(source: XmlSource) -> Iterator[StockGroupRecord]:
    """Yield one StockGroupRecord per <STOCKGROUP> element in the XML response."""
    for elem in base.iter_collection(source, "STOCKGROUP"):
        yield _build(elem)


def parse_stock_groups_with_raw(
    source: XmlSource,
) -> Iterator[tuple[StockGroupRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <STOCKGROUP> element."""
    for elem, raw in base.iter_collection_with_raw(source, "STOCKGROUP"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> StockGroupRecord:
    return StockGroupRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        parent=base.text(elem, "PARENT"),
        is_addable=base.bool_yes(elem, "ISADDABLE"),
        alter_id=base.integer(elem, "ALTERID"),
    )
