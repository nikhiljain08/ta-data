from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.models.domain.ledger import LedgerRecord
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "NAME",
        "GUID",
        "PARENT",
        "ISDEEMEDPOSITIVE",
        "OPENINGBALANCE",
        "CLOSINGBALANCE",
        "GSTREGISTRATIONTYPE",
        "GSTIN",
        "LEDGSTREGDETAILS.LIST",
        "INCOMETAXNUMBER",
        "LEDGERMOBILE",
        "LEDGEREMAIL",
        "LEDMAILINGDETAILS.LIST",
        "COUNTRYNAME",
        "LEDGERSTATENAME",
        "PINCODE",
        "ADDRESS.LIST",
        "ALTERID",
    }
)


def parse_ledgers(source: XmlSource) -> Iterator[LedgerRecord]:
    """Yield one LedgerRecord per <LEDGER> element in the XML response."""
    for elem in base.iter_collection(source, "LEDGER"):
        yield _build(elem)


def parse_ledgers_with_raw(
    source: XmlSource,
) -> Iterator[tuple[LedgerRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <LEDGER> element."""
    for elem, raw in base.iter_collection_with_raw(source, "LEDGER"):
        yield _build(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _gstin_from_gst_details(elem: Any) -> str:
    """Read GSTIN from the LedGSTRegDetails sub-collection.

    TallyPrime 7 does not expose GSTIN as a flat field on Ledger; the value
    lives in a repeating LedGSTRegDetails sub-object.  Return the first
    non-empty GSTIN found, or fall back to the legacy flat <GSTIN> tag for
    historical archive rows written before this fix.
    """
    for detail in elem.findall("LEDGSTREGDETAILS.LIST"):
        gstin = base.text(detail, "GSTIN")
        if gstin:
            return gstin
    return base.text(elem, "GSTIN")


def _email_from_mailing_details(elem: Any) -> str:
    """Read email from the LedMailingDetails sub-collection.

    $LedgerEmail returns empty as a flat field; the real value is in
    LedMailingDetails.  Return the first non-empty email found.
    """
    for detail in elem.findall("LEDMAILINGDETAILS.LIST"):
        email = base.text(detail, "EMAIL")
        if email:
            return email
    return base.text(elem, "LEDGEREMAIL")


def _address_from_mailing_details(elem: Any) -> list[str]:
    """Read address lines from the LedMailingDetails sub-collection.

    ADDRESS.LIST at the Ledger level returns nothing; address is in
    LedMailingDetails.  Fallback to ADDRESS.LIST for historical archive rows.
    """
    addresses: list[str] = []
    for detail in elem.findall("LEDMAILINGDETAILS.LIST"):
        addr = base.text(detail, "ADDRESS")
        if addr:
            addresses.append(addr)
    if addresses:
        return addresses
    return base.text_list(elem, "ADDRESS.LIST", "ADDRESS")


def _build(elem: Any) -> LedgerRecord:
    return LedgerRecord(
        name=base.name_of(elem),
        guid=base.text(elem, "GUID"),
        parent=base.text(elem, "PARENT"),
        is_deemed_positive=base.bool_yes(elem, "ISDEEMEDPOSITIVE"),
        opening_balance=base.decimal_amount(elem, "OPENINGBALANCE"),
        closing_balance=base.decimal_amount(elem, "CLOSINGBALANCE"),
        gst_registration_type=base.text(elem, "GSTREGISTRATIONTYPE"),
        gstin=_gstin_from_gst_details(elem),
        pan=base.text(elem, "INCOMETAXNUMBER"),
        mobile=base.text(elem, "LEDGERMOBILE"),
        email=_email_from_mailing_details(elem),
        country=base.text(elem, "COUNTRYNAME"),
        state=base.text(elem, "LEDGERSTATENAME"),
        pincode=base.text(elem, "PINCODE"),
        address=_address_from_mailing_details(elem),
        alter_id=base.integer(elem, "ALTERID"),
    )
