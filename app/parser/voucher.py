from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import lxml.etree as etree

from app.models.domain.voucher import (
    GstDetail,
    VoucherInventoryEntry,
    VoucherLedgerEntry,
    VoucherRecord,
)
from app.parser import base
from app.parser.base import XmlSource

_KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "VOUCHERNUMBER",
        "VOUCHERTYPENAME",
        "DATE",
        "PARTYLEDGERNAME",
        "NARRATION",
        "ISINVOICE",
        "ISCANCELLED",
        "ISOPTIONAL",
        "GUID",
        "ALTERID",
        "ALLLEDGERENTRIES.LIST",
        "LEDGERENTRIES.LIST",
        "ALLINVENTORYENTRIES.LIST",
        "INVENTORYENTRIES.LIST",
    }
)


def parse_vouchers(source: XmlSource) -> Iterator[VoucherRecord]:
    """Yield one VoucherRecord per <VOUCHER> element in the XML response."""
    for elem in base.iter_collection(source, "VOUCHER"):
        yield _build_record(elem)


def parse_vouchers_with_raw(
    source: XmlSource,
) -> Iterator[tuple[VoucherRecord, bytes, dict[str, Any]]]:
    """Yield (record, raw_xml_bytes, unknown_fields) for each <VOUCHER> element."""
    for elem, raw in base.iter_collection_with_raw(source, "VOUCHER"):
        yield _build_record(elem), raw, base.extract_unknown_fields(elem, _KNOWN_TAGS)


def _build_record(elem: etree._Element) -> VoucherRecord:
    return VoucherRecord(
        voucher_number=base.text(elem, "VOUCHERNUMBER"),
        voucher_type=base.text(elem, "VOUCHERTYPENAME"),
        date=base.tally_date(elem, "DATE"),
        party_ledger=base.text(elem, "PARTYLEDGERNAME"),
        narration=base.text(elem, "NARRATION"),
        is_invoice=base.bool_yes(elem, "ISINVOICE"),
        is_cancelled=base.bool_yes(elem, "ISCANCELLED"),
        is_optional=base.bool_yes(elem, "ISOPTIONAL"),
        guid=base.text(elem, "GUID"),
        alter_id=base.integer(elem, "ALTERID"),
        ledger_entries=tuple(_parse_ledger_entries(elem)),
        inventory_entries=tuple(_parse_inventory_entries(elem)),
        gst_details=tuple(_parse_gst_details(elem)),
    )


def _parse_ledger_entries(voucher: etree._Element) -> list[VoucherLedgerEntry]:
    entries: list[VoucherLedgerEntry] = []
    # TallyPrime 7 uses ALLLEDGERENTRIES.LIST; older exports use LEDGERENTRIES.LIST
    for container_tag in ("ALLLEDGERENTRIES.LIST", "LEDGERENTRIES.LIST"):
        for entry in voucher.findall(container_tag):
            ledger_name = base.text(entry, "LEDGERNAME")
            if ledger_name:
                entries.append(
                    VoucherLedgerEntry(
                        ledger_name=ledger_name,
                        is_deemed_positive=base.bool_yes(entry, "ISDEEMEDPOSITIVE"),
                        amount=base.decimal_amount(entry, "AMOUNT"),
                    )
                )
    return entries


def _parse_inventory_entries(voucher: etree._Element) -> list[VoucherInventoryEntry]:
    entries: list[VoucherInventoryEntry] = []
    for container_tag in ("INVENTORYENTRIES.LIST", "ALLINVENTORYENTRIES.LIST"):
        for entry in voucher.findall(container_tag):
            stock_item = base.text(entry, "STOCKITEMNAME")
            if stock_item:
                entries.append(
                    VoucherInventoryEntry(
                        stock_item_name=stock_item,
                        is_deemed_positive=base.bool_yes(entry, "ISDEEMEDPOSITIVE"),
                        quantity=base.quantity(entry, "ACTUALQTY"),
                        rate=base.rate(entry, "RATE"),
                        amount=base.decimal_amount(entry, "AMOUNT"),
                        godown_name=base.text(entry, "GODOWNNAME"),
                    )
                )
    return entries


def _parse_gst_details(voucher: etree._Element) -> list[GstDetail]:
    details: list[GstDetail] = []
    # GST details nest inside inventory entries (GSTTAXDETAILS.LIST per entry)
    for inv_tag in ("INVENTORYENTRIES.LIST", "ALLINVENTORYENTRIES.LIST"):
        for entry in voucher.findall(inv_tag):
            for gst in entry.findall("GSTTAXDETAILS.LIST"):
                details.append(
                    GstDetail(
                        hsn_code=base.text(gst, "HSNCODE"),
                        taxable_value=base.decimal_amount(gst, "TAXABLEVALUE"),
                        igst_amount=base.decimal_amount(gst, "IGSTAMOUNT"),
                        cgst_amount=base.decimal_amount(gst, "CGSTAMOUNT"),
                        sgst_amount=base.decimal_amount(gst, "SGSTAMOUNT"),
                        gst_type=base.text(gst, "TAXTYPE"),
                    )
                )
    return details
