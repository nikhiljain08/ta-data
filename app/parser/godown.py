from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.godown import GodownRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "PARENT",
        "HASNOSTOCK",
        "ALTERID",
    }
)


def parse_godowns(source: XmlSource) -> Iterator[GodownRecord]:
    """Yield one GodownRecord per <GODOWN> element in the XML response."""
    for elem in base.iter_collection(source, "GODOWN"):
        yield _build(elem)


def parse_godowns_with_raw(
    source: XmlSource,
) -> Iterator[tuple[GodownRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <GODOWN> element."""
    for elem, raw in base.iter_collection_with_raw(source, "GODOWN"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> GodownRecord:
    return GodownRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        parent=base.text(elem, "PARENT"),
        has_no_stock=base.bool_yes(elem, "HASNOSTOCK"),
        alter_id=base.integer(elem, "ALTERID"),
    )
