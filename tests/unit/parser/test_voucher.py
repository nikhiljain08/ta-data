"""Tests for app.parser.voucher — streaming XML → VoucherRecord."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.domain.voucher import VoucherRecord
from app.parser.voucher import parse_vouchers

# ── Sample XML ────────────────────────────────────────────────────────────────

_SALES_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <BODY>
    <EXPORTDATA>
      <REQUESTDATA>
        <TALLYMESSAGE>
          <VOUCHER DATE="20240401" GUID="abc-001" VOUCHERTYPENAME="Sales" VOUCHERNUMBER="SAL/001">
            <DATE>20240401</DATE>
            <GUID>abc-001</GUID>
            <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
            <VOUCHERNUMBER>SAL/001</VOUCHERNUMBER>
            <PARTYLEDGERNAME>Customer A</PARTYLEDGERNAME>
            <NARRATION>April sale</NARRATION>
            <ISINVOICE>Yes</ISINVOICE>
            <ISCANCELLED>No</ISCANCELLED>
            <ISOPTIONAL>No</ISOPTIONAL>
            <ALTERID>101</ALTERID>
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Sales Account</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>-50000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Customer A</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>50000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
            <INVENTORYENTRIES.LIST>
              <STOCKITEMNAME>Widget A</STOCKITEMNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <ACTUALQTY>10 Nos</ACTUALQTY>
              <RATE>5000.0/Nos</RATE>
              <AMOUNT>50000</AMOUNT>
              <GODOWNNAME>Main Godown</GODOWNNAME>
              <GSTTAXDETAILS.LIST>
                <HSNCODE>12345678</HSNCODE>
                <TAXABLEVALUE>50000</TAXABLEVALUE>
                <IGSTAMOUNT>9000</IGSTAMOUNT>
                <CGSTAMOUNT>0</CGSTAMOUNT>
                <SGSTAMOUNT>0</SGSTAMOUNT>
                <TAXTYPE>Inter State</TAXTYPE>
              </GSTTAXDETAILS.LIST>
            </INVENTORYENTRIES.LIST>
          </VOUCHER>
          <VOUCHER DATE="20240402" GUID="abc-002" VOUCHERTYPENAME="Payment" VOUCHERNUMBER="PMT/001">
            <DATE>20240402</DATE>
            <GUID>abc-002</GUID>
            <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
            <VOUCHERNUMBER>PMT/001</VOUCHERNUMBER>
            <PARTYLEDGERNAME>Supplier B</PARTYLEDGERNAME>
            <NARRATION>Payment to supplier</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <ISCANCELLED>No</ISCANCELLED>
            <ISOPTIONAL>No</ISOPTIONAL>
            <ALTERID>102</ALTERID>
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Cash</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>-10000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Supplier B</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>10000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

_EMPTY_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE><BODY><EXPORTDATA><REQUESTDATA/></EXPORTDATA></BODY></ENVELOPE>"""


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestParseVouchers:
    def test_yields_correct_count(self) -> None:
        records = list(parse_vouchers(_SALES_XML))
        assert len(records) == 2

    def test_header_fields(self) -> None:
        rec = next(parse_vouchers(_SALES_XML))
        assert rec.voucher_number == "SAL/001"
        assert rec.voucher_type == "Sales"
        assert rec.date == "20240401"
        assert rec.party_ledger == "Customer A"
        assert rec.narration == "April sale"
        assert rec.is_invoice is True
        assert rec.is_cancelled is False
        assert rec.guid == "abc-001"
        assert rec.alter_id == 101

    def test_ledger_entries(self) -> None:
        rec = next(parse_vouchers(_SALES_XML))
        assert len(rec.ledger_entries) == 2
        sales = rec.ledger_entries[0]
        assert sales.ledger_name == "Sales Account"
        assert sales.is_deemed_positive is False
        assert sales.amount == Decimal("-50000")

    def test_inventory_entries(self) -> None:
        rec = next(parse_vouchers(_SALES_XML))
        assert len(rec.inventory_entries) == 1
        entry = rec.inventory_entries[0]
        assert entry.stock_item_name == "Widget A"
        assert entry.quantity == Decimal("10")
        assert entry.rate == Decimal("5000.0")
        assert entry.amount == Decimal("50000")
        assert entry.godown_name == "Main Godown"

    def test_gst_details(self) -> None:
        rec = next(parse_vouchers(_SALES_XML))
        assert len(rec.gst_details) == 1
        gst = rec.gst_details[0]
        assert gst.hsn_code == "12345678"
        assert gst.taxable_value == Decimal("50000")
        assert gst.igst_amount == Decimal("9000")
        assert gst.cgst_amount == Decimal("0")
        assert gst.sgst_amount == Decimal("0")
        assert gst.gst_type == "Inter State"

    def test_payment_voucher_no_inventory(self) -> None:
        records = list(parse_vouchers(_SALES_XML))
        pmt = records[1]
        assert pmt.voucher_number == "PMT/001"
        assert pmt.voucher_type == "Payment"
        assert len(pmt.inventory_entries) == 0
        assert len(pmt.gst_details) == 0
        assert len(pmt.ledger_entries) == 2

    def test_empty_xml_yields_nothing(self) -> None:
        records = list(parse_vouchers(_EMPTY_XML))
        assert records == []

    def test_returns_frozen_records(self) -> None:
        rec = next(parse_vouchers(_SALES_XML))
        assert isinstance(rec, VoucherRecord)
        with pytest.raises(ValidationError):
            rec.voucher_number = "CHANGED"  # type: ignore[misc]
