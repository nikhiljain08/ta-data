from __future__ import annotations

from collections.abc import Iterator

from app.models.domain.ledger import LedgerRecord
from app.parser import base
from app.parser.base import XmlSource


def parse_ledgers(source: XmlSource) -> Iterator[LedgerRecord]:
    """Yield one LedgerRecord per <LEDGER> element in the XML response."""
    for elem in base.iter_collection(source, "LEDGER"):
        yield LedgerRecord(
            name=base.name_of(elem),
            guid=base.text(elem, "GUID"),
            parent=base.text(elem, "PARENT"),
            is_deemed_positive=base.bool_yes(elem, "ISDEEMEDPOSITIVE"),
            opening_balance=base.decimal_amount(elem, "OPENINGBALANCE"),
            closing_balance=base.decimal_amount(elem, "CLOSINGBALANCE"),
            gst_registration_type=base.text(elem, "GSTREGISTRATIONTYPE"),
            gstin=base.text(elem, "GSTIN"),
            pan=base.text(elem, "INCOMETAXNUMBER"),
            mobile=base.text(elem, "LEDGERMOBILE"),
            email=base.text(elem, "LEDGEREMAIL"),
            country=base.text(elem, "COUNTRYNAME"),
            state=base.text(elem, "LEDGERSTATENAME"),
            pincode=base.text(elem, "PINCODE"),
            address=base.text_list(elem, "ADDRESS.LIST", "ADDRESS"),
            alter_id=base.integer(elem, "ALTERID"),
        )
