from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.company import CompanyRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_companies(source: XmlSource) -> Iterator[CompanyRecord]:
    """Yield one CompanyRecord per <COMPANY> element in the XML response."""
    for elem in base.iter_collection(source, "COMPANY"):
        yield CompanyRecord(
            name=base.name_of(elem) or base.text(elem, "REMOTECMPNAME"),
            guid=base.text(elem, "GUID"),
            books_from=base.tally_date(elem, "BOOKSBEGINNINGFROM"),
            starting_from=base.tally_date(elem, "STARTINGFROM"),
            ending_at=base.tally_date(elem, "ENDINGAT"),
            country=base.text(elem, "COUNTRYNAME"),
            state=base.text(elem, "STATENAME"),
            gstin=base.text(elem, "GSTIN"),
            alter_id=base.integer(elem, "ALTERID"),
        )
