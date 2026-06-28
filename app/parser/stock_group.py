from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.stock_group import StockGroupRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_stock_groups(source: XmlSource) -> Iterator[StockGroupRecord]:
    """Yield one StockGroupRecord per <STOCKGROUP> element in the XML response."""
    for elem in base.iter_collection(source, "STOCKGROUP"):
        yield StockGroupRecord(
            name=base.name_of(elem),
            guid=base.text(elem, "GUID"),
            parent=base.text(elem, "PARENT"),
            is_addable=base.bool_yes(elem, "ISADDABLE"),
            alter_id=base.integer(elem, "ALTERID"),
        )
