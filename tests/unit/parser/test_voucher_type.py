"""Tests for app.parser.voucher_type — VoucherTypeRecord parsing."""

from __future__ import annotations

import pytest

from app.models.domain.voucher_type import VoucherTypeRecord
from app.parser.voucher_type import parse_voucher_types

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <VOUCHERTYPE NAME="Sales" RESERVEDNAME="Sales">
      <GUID>vt-001</GUID>
      <PARENT>Sales</PARENT>
      <NUMBERINGMETHOD>Automatic</NUMBERINGMETHOD>
      <ISACTIVE>Yes</ISACTIVE>
      <ALTERID>20</ALTERID>
    </VOUCHERTYPE>
    <VOUCHERTYPE NAME="Tax Invoice" RESERVEDNAME="">
      <GUID>vt-002</GUID>
      <PARENT>Sales</PARENT>
      <NUMBERINGMETHOD>Manual</NUMBERINGMETHOD>
      <ISACTIVE>Yes</ISACTIVE>
      <ALTERID>35</ALTERID>
    </VOUCHERTYPE>
    <VOUCHERTYPE NAME="OldType" RESERVEDNAME="">
      <GUID>vt-003</GUID>
      <PARENT>Journal</PARENT>
      <ISACTIVE>No</ISACTIVE>
      <ALTERID>12</ALTERID>
    </VOUCHERTYPE>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseVoucherTypes:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_voucher_types(_XML))) == 3

    def test_active_sales_type(self) -> None:
        rec = list(parse_voucher_types(_XML))[0]
        assert isinstance(rec, VoucherTypeRecord)
        assert rec.name == "Sales"
        assert rec.guid == "vt-001"
        assert rec.parent == "Sales"
        assert rec.numbering_method == "Automatic"
        assert rec.is_active is True
        assert rec.alter_id == 20

    def test_manual_numbering(self) -> None:
        rec = list(parse_voucher_types(_XML))[1]
        assert rec.name == "Tax Invoice"
        assert rec.numbering_method == "Manual"

    def test_inactive_type(self) -> None:
        rec = list(parse_voucher_types(_XML))[2]
        assert rec.name == "OldType"
        assert rec.is_active is False

    def test_empty_collection(self) -> None:
        assert list(parse_voucher_types(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_voucher_types(_XML))
        with pytest.raises(Exception):
            rec.name = "changed"  # type: ignore[misc]
