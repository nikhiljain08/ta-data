from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.voucher_type import VoucherTypeRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "PARENT",
        "NUMBERINGMETHOD",
        "ISACTIVE",
        "ALTERID",
    }
)


def parse_voucher_types(source: XmlSource) -> Iterator[VoucherTypeRecord]:
    """Yield one VoucherTypeRecord per <VOUCHERTYPE> element in the XML response."""
    for elem in base.iter_collection(source, "VOUCHERTYPE"):
        yield _build(elem)


def parse_voucher_types_with_raw(
    source: XmlSource,
) -> Iterator[tuple[VoucherTypeRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <VOUCHERTYPE> element."""
    for elem, raw in base.iter_collection_with_raw(source, "VOUCHERTYPE"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> VoucherTypeRecord:
    return VoucherTypeRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        parent=base.text(elem, "PARENT"),
        numbering_method=base.text(elem, "NUMBERINGMETHOD"),
        is_active=base.bool_yes(elem, "ISACTIVE"),
        alter_id=base.integer(elem, "ALTERID"),
    )
