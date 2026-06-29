from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.unit import UnitRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "GSTUNITNAME",
        "FORMALNAME",
        "ISSIMPLEUNIT",
        "ALTERID",
    }
)


def parse_units(source: XmlSource) -> Iterator[UnitRecord]:
    """Yield one UnitRecord per <UNIT> element in the XML response."""
    for elem in base.iter_collection(source, "UNIT"):
        yield _build(elem)


def parse_units_with_raw(
    source: XmlSource,
) -> Iterator[tuple[UnitRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <UNIT> element."""
    for elem, raw in base.iter_collection_with_raw(source, "UNIT"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> UnitRecord:
    return UnitRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        gst_unit_name=base.text(elem, "GSTUNITNAME"),
        formal_name=base.text(elem, "FORMALNAME"),
        is_simple_unit=base.bool_yes(elem, "ISSIMPLEUNIT"),
        alter_id=base.integer(elem, "ALTERID"),
    )
