"""Tests for app.parser.ledger — LedgerRecord parsing."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.domain.ledger import LedgerRecord
from app.parser.ledger import parse_ledgers

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <LEDGER NAME="Customer A" RESERVEDNAME="">
      <GUID>led-001</GUID>
      <PARENT>Sundry Debtors</PARENT>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <OPENINGBALANCE>0</OPENINGBALANCE>
      <CLOSINGBALANCE>75000</CLOSINGBALANCE>
      <GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>
      <GSTIN>27BBBBB0001B1Z6</GSTIN>
      <INCOMETAXNUMBER>ABCDE1234F</INCOMETAXNUMBER>
      <LEDGERMOBILE>9876543210</LEDGERMOBILE>
      <LEDGEREMAIL>customer@example.com</LEDGEREMAIL>
      <COUNTRYNAME>India</COUNTRYNAME>
      <LEDGERSTATENAME>Maharashtra</LEDGERSTATENAME>
      <PINCODE>400001</PINCODE>
      <ADDRESS.LIST TYPE="String">
        <ADDRESS>123 Main Road</ADDRESS>
        <ADDRESS>Mumbai</ADDRESS>
      </ADDRESS.LIST>
      <ALTERID>200</ALTERID>
    </LEDGER>
    <LEDGER NAME="Cash" RESERVEDNAME="Cash">
      <GUID>led-002</GUID>
      <PARENT>Cash-in-Hand</PARENT>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <OPENINGBALANCE>10000</OPENINGBALANCE>
      <CLOSINGBALANCE>50000</CLOSINGBALANCE>
      <ALTERID>5</ALTERID>
    </LEDGER>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_DR_BALANCE_XML = b"""
<ENVELOPE><BODY><DATA><COLLECTION>
  <LEDGER NAME="Purchases">
    <PARENT>Purchase Accounts</PARENT>
    <OPENINGBALANCE>30000 Dr</OPENINGBALANCE>
    <CLOSINGBALANCE>80000 Dr</CLOSINGBALANCE>
    <ALTERID>300</ALTERID>
  </LEDGER>
</COLLECTION></DATA></BODY></ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseLedgers:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_ledgers(_XML))) == 2

    def test_full_ledger_fields(self) -> None:
        rec = next(parse_ledgers(_XML))
        assert isinstance(rec, LedgerRecord)
        assert rec.name == "Customer A"
        assert rec.guid == "led-001"
        assert rec.parent == "Sundry Debtors"
        assert rec.is_deemed_positive is True
        assert rec.closing_balance == Decimal("75000")
        assert rec.gst_registration_type == "Regular"
        assert rec.gstin == "27BBBBB0001B1Z6"
        assert rec.pan == "ABCDE1234F"
        assert rec.mobile == "9876543210"
        assert rec.email == "customer@example.com"
        assert rec.country == "India"
        assert rec.state == "Maharashtra"
        assert rec.pincode == "400001"
        assert rec.address == ["123 Main Road", "Mumbai"]
        assert rec.alter_id == 200

    def test_minimal_ledger(self) -> None:
        rec = list(parse_ledgers(_XML))[1]
        assert rec.name == "Cash"
        assert rec.gstin == ""
        assert rec.address == []

    def test_dr_suffix_flips_sign(self) -> None:
        rec = next(parse_ledgers(_DR_BALANCE_XML))
        assert rec.opening_balance == Decimal("-30000")
        assert rec.closing_balance == Decimal("-80000")

    def test_empty_collection(self) -> None:
        assert list(parse_ledgers(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_ledgers(_XML))
        with pytest.raises(ValidationError):
            rec.name = "changed"  # type: ignore[misc]
