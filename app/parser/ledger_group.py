from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.ledger_group import LedgerGroupRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "PARENT",
        "ISDEEMEDPOSITIVE",
        "ISREVENUE",
        "AFFECTSSTOCK",
        "ALTERID",
    }
)


def parse_ledger_groups(source: XmlSource) -> Iterator[LedgerGroupRecord]:
    """Yield one LedgerGroupRecord per <GROUP> element in the XML response."""
    for elem in base.iter_collection(source, "GROUP"):
        yield _build(elem)


def parse_ledger_groups_with_raw(
    source: XmlSource,
) -> Iterator[tuple[LedgerGroupRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <GROUP> element."""
    for elem, raw in base.iter_collection_with_raw(source, "GROUP"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> LedgerGroupRecord:
    return LedgerGroupRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        parent=base.text(elem, "PARENT"),
        is_deemed_positive=base.bool_yes(elem, "ISDEEMEDPOSITIVE"),
        is_revenue=base.bool_yes(elem, "ISREVENUE"),
        affects_stock=base.bool_yes(elem, "AFFECTSSTOCK"),
        alter_id=base.integer(elem, "ALTERID"),
    )
