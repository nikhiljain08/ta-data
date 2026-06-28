from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.godown import GodownRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_godowns(source: XmlSource) -> Iterator[GodownRecord]:
    """Yield one GodownRecord per <GODOWN> element in the XML response."""
    for elem in base.iter_collection(source, "GODOWN"):
        yield GodownRecord(
            name=base.name_of(elem),
            guid=base.text(elem, "GUID"),
            parent=base.text(elem, "PARENT"),
            has_no_stock=base.bool_yes(elem, "HASNOSTOCK"),
            alter_id=base.integer(elem, "ALTERID"),
        )
