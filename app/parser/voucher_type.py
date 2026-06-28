from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.voucher_type import VoucherTypeRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_voucher_types(source: XmlSource) -> Iterator[VoucherTypeRecord]:
    """Yield one VoucherTypeRecord per <VOUCHERTYPE> element in the XML response."""
    for elem in base.iter_collection(source, "VOUCHERTYPE"):
        yield VoucherTypeRecord(
            name=base.name_of(elem),
            guid=base.text(elem, "GUID"),
            parent=base.text(elem, "PARENT"),
            numbering_method=base.text(elem, "NUMBERINGMETHOD"),
            is_active=base.bool_yes(elem, "ISACTIVE"),
            alter_id=base.integer(elem, "ALTERID"),
        )
