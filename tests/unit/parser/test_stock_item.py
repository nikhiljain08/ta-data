"""Tests for app.parser.stock_item — StockItemRecord parsing."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.domain.stock_item import StockItemRecord
from app.parser.stock_item import parse_stock_items

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <STOCKITEM NAME="Widget Pro" RESERVEDNAME="">
      <GUID>si-001</GUID>
      <PARENT>Electronics</PARENT>
      <CATEGORY>Consumer</CATEGORY>
      <BASEUNITS>Nos</BASEUNITS>
      <GSTAPPLICABLE>Applicable</GSTAPPLICABLE>
      <GSTTYPEOFSUPPLY>Goods</GSTTYPEOFSUPPLY>
      <HSNCODE>85423900</HSNCODE>
      <DESCRIPTION>Electronic widget</DESCRIPTION>
      <OPENINGBALANCE>50 Nos</OPENINGBALANCE>
      <OPENINGRATE>500.00/Nos</OPENINGRATE>
      <OPENINGVALUE>25000.00</OPENINGVALUE>
      <CLOSINGBALANCE>30 Nos</CLOSINGBALANCE>
      <CLOSINGRATE>500.00/Nos</CLOSINGRATE>
      <CLOSINGVALUE>15000.00</CLOSINGVALUE>
      <ALTERID>50</ALTERID>
    </STOCKITEM>
    <STOCKITEM NAME="Basic Item" RESERVEDNAME="">
      <GUID>si-002</GUID>
      <PARENT>Primary</PARENT>
      <BASEUNITS>Nos</BASEUNITS>
      <ALTERID>51</ALTERID>
    </STOCKITEM>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseStockItems:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_stock_items(_XML))) == 2

    def test_full_item_fields(self) -> None:
        rec = next(parse_stock_items(_XML))
        assert isinstance(rec, StockItemRecord)
        assert rec.name == "Widget Pro"
        assert rec.guid == "si-001"
        assert rec.parent == "Electronics"
        assert rec.category == "Consumer"
        assert rec.base_units == "Nos"
        assert rec.gst_applicable == "Applicable"
        assert rec.gst_type_of_supply == "Goods"
        assert rec.hsn_code == "85423900"
        assert rec.description == "Electronic widget"
        assert rec.opening_balance == Decimal("50")
        assert rec.opening_rate == Decimal("500.00")
        assert rec.opening_value == Decimal("25000.00")
        assert rec.closing_balance == Decimal("30")
        assert rec.closing_rate == Decimal("500.00")
        assert rec.closing_value == Decimal("15000.00")
        assert rec.alter_id == 50

    def test_minimal_item(self) -> None:
        rec = list(parse_stock_items(_XML))[1]
        assert rec.name == "Basic Item"
        assert rec.hsn_code == ""
        assert rec.opening_balance == Decimal(0)
        assert rec.alter_id == 51

    def test_empty_collection(self) -> None:
        assert list(parse_stock_items(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_stock_items(_XML))
        with pytest.raises(ValidationError):
            rec.name = "changed"  # type: ignore[misc]

    def test_rate_strips_unit_denominator(self) -> None:
        xml = b"""
        <ENVELOPE><BODY><DATA><COLLECTION>
          <STOCKITEM NAME="X">
            <PARENT>Primary</PARENT>
            <BASEUNITS>Kg</BASEUNITS>
            <OPENINGRATE>1250.75/Kg</OPENINGRATE>
            <ALTERID>99</ALTERID>
          </STOCKITEM>
        </COLLECTION></DATA></BODY></ENVELOPE>
        """
        rec = next(parse_stock_items(xml))
        assert rec.opening_rate == Decimal("1250.75")
