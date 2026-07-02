from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.company import CompanyRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "REMOTECMPNAME",
        "BOOKSBEGINNINGFROM",
        "STARTINGFROM",
        "ENDINGAT",
        "COUNTRYNAME",
        "STATENAME",
        "GSTIN",
        "GSTDETAILS.LIST",
        "ALTERID",
    }
)


def _gstin_from_gst_details(elem: Any) -> str:
    """Read GSTIN from the GSTDetails sub-collection.

    Flat $GSTIN on Company returns nothing in TallyPrime 7; the value (when
    entered) lives in the GSTDetails sub-object.  Fall back to the legacy flat
    <GSTIN> tag for historical archive rows written before this fix.
    """
    for detail in elem.findall("GSTDETAILS.LIST"):
        gstin = base.text(detail, "GSTIN")
        if gstin:
            return gstin
    return base.text(elem, "GSTIN")


def parse_companies(source: XmlSource) -> Iterator[CompanyRecord]:
    """Yield one CompanyRecord per <COMPANY> element in the XML response."""
    for elem in base.iter_collection(source, "COMPANY"):
        yield _build(elem)


def parse_companies_with_raw(
    source: XmlSource,
) -> Iterator[tuple[CompanyRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <COMPANY> element."""
    for elem, raw in base.iter_collection_with_raw(source, "COMPANY"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build(elem: Any) -> CompanyRecord:
    return CompanyRecord(
        name=base.name_of(elem) or base.text(elem, "REMOTECMPNAME"),
        guid=base.text(elem, "GUID"),
        books_from=base.tally_date(elem, "BOOKSBEGINNINGFROM"),
        starting_from=base.tally_date(elem, "STARTINGFROM"),
        ending_at=base.tally_date(elem, "ENDINGAT"),
        country=base.text(elem, "COUNTRYNAME"),
        state=base.text(elem, "STATENAME"),
        gstin=_gstin_from_gst_details(elem),
        alter_id=base.integer(elem, "ALTERID"),
    )
