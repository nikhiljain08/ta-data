from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.unit import UnitRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_units(source: XmlSource) -> Iterator[UnitRecord]:
    """Yield one UnitRecord per <UNIT> element in the XML response."""
    for elem in base.iter_collection(source, "UNIT"):
        yield UnitRecord(
            name=base.name_of(elem),
            guid=base.text(elem, "GUID"),
            gst_unit_name=base.text(elem, "GSTUNITNAME"),
            formal_name=base.text(elem, "FORMALNAME"),
            is_simple_unit=base.bool_yes(elem, "ISSIMPLEUNIT"),
            alter_id=base.integer(elem, "ALTERID"),
        )
