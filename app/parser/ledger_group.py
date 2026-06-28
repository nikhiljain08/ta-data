from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.ledger_group import LedgerGroupRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_ledger_groups(source: XmlSource) -> Iterator[LedgerGroupRecord]:
    """Yield one LedgerGroupRecord per <GROUP> element in the XML response."""
    for elem in base.iter_collection(source, "GROUP"):
        yield LedgerGroupRecord(
            name=base.name_of(elem),
            guid=base.text(elem, "GUID"),
            parent=base.text(elem, "PARENT"),
            is_deemed_positive=base.bool_yes(elem, "ISDEEMEDPOSITIVE"),
            is_revenue=base.bool_yes(elem, "ISREVENUE"),
            affects_stock=base.bool_yes(elem, "AFFECTSSTOCK"),
            alter_id=base.integer(elem, "ALTERID"),
        )
