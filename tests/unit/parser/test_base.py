"""Tests for app.parser.base — the shared lxml.iterparse utilities."""

from __future__ import annotations

import io
from decimal import Decimal

import lxml.etree as etree
import pytest

from app.parser.base import (
    bool_yes,
    decimal_amount,
    integer,
    iter_collection,
    name_of,
    quantity,
    rate,
    text,
    text_list,
)

# ── Helpers to build test elements ────────────────────────────────────────────

_SIMPLE_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <ITEM NAME="Widget">
      <GUID>abc-123</GUID>
      <AMOUNT>50000</AMOUNT>
      <QTY>100 Nos</QTY>
      <RATE>250.50/Nos</RATE>
      <ISACTIVE>Yes</ISACTIVE>
      <COUNT>42</COUNT>
      <ADDRESS.LIST TYPE="String">
        <ADDRESS>Line 1</ADDRESS>
        <ADDRESS>Line 2</ADDRESS>
      </ADDRESS.LIST>
    </ITEM>
    <ITEM NAME="Gadget">
      <GUID>def-456</GUID>
      <AMOUNT>-25000</AMOUNT>
    </ITEM>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""


def _elem(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode())


# ── iter_collection ────────────────────────────────────────────────────────────


class TestIterCollection:
    def test_yields_all_matching_tags(self) -> None:
        items = list(iter_collection(_SIMPLE_XML, "ITEM"))
        assert len(items) == 2

    def test_yields_correct_name_attributes(self) -> None:
        # Elements are cleared after each yield — read attributes inside the loop.
        names = [elem.get("NAME") for elem in iter_collection(_SIMPLE_XML, "ITEM")]
        assert names == ["Widget", "Gadget"]

    def test_unknown_tag_yields_nothing(self) -> None:
        assert list(iter_collection(_SIMPLE_XML, "NONEXISTENT")) == []

    def test_accepts_file_like_source(self) -> None:
        stream = io.BytesIO(_SIMPLE_XML)
        items = list(iter_collection(stream, "ITEM"))
        assert len(items) == 2

    def test_empty_collection(self) -> None:
        xml = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"
        assert list(iter_collection(xml, "ITEM")) == []


# ── text ──────────────────────────────────────────────────────────────────────


class TestText:
    def test_returns_child_text(self) -> None:
        elem = _elem("<ITEM><NAME>Cash</NAME></ITEM>")
        assert text(elem, "NAME") == "Cash"

    def test_strips_whitespace(self) -> None:
        elem = _elem("<ITEM><NAME>  Cash  </NAME></ITEM>")
        assert text(elem, "NAME") == "Cash"

    def test_missing_child_returns_default(self) -> None:
        elem = _elem("<ITEM/>")
        assert text(elem, "NAME") == ""
        assert text(elem, "NAME", "fallback") == "fallback"

    def test_empty_child_returns_default(self) -> None:
        elem = _elem("<ITEM><NAME/></ITEM>")
        assert text(elem, "NAME") == ""


# ── name_of ───────────────────────────────────────────────────────────────────


class TestNameOf:
    def test_prefers_attribute(self) -> None:
        elem = _elem('<LEDGER NAME="Cash"><NAME>Different</NAME></LEDGER>')
        assert name_of(elem) == "Cash"

    def test_falls_back_to_child_element(self) -> None:
        elem = _elem("<LEDGER><NAME>Cash</NAME></LEDGER>")
        assert name_of(elem) == "Cash"

    def test_strips_whitespace_from_attribute(self) -> None:
        elem = _elem('<LEDGER NAME="  Cash  "/>')
        assert name_of(elem) == "Cash"


# ── integer ───────────────────────────────────────────────────────────────────


class TestInteger:
    def test_parses_plain_int(self) -> None:
        elem = _elem("<X><ALTERID>1234</ALTERID></X>")
        assert integer(elem, "ALTERID") == 1234

    def test_strips_trailing_unit(self) -> None:
        # Unusual but defensive
        elem = _elem("<X><COUNT>42 units</COUNT></X>")
        assert integer(elem, "COUNT") == 42

    def test_missing_returns_default(self) -> None:
        elem = _elem("<X/>")
        assert integer(elem, "ALTERID") == 0
        assert integer(elem, "ALTERID", -1) == -1

    def test_non_numeric_returns_default(self) -> None:
        elem = _elem("<X><ALTERID>N/A</ALTERID></X>")
        assert integer(elem, "ALTERID") == 0


# ── bool_yes ──────────────────────────────────────────────────────────────────


class TestBoolYes:
    def test_yes_returns_true(self) -> None:
        elem = _elem("<X><ISACTIVE>Yes</ISACTIVE></X>")
        assert bool_yes(elem, "ISACTIVE") is True

    def test_no_returns_false(self) -> None:
        elem = _elem("<X><ISACTIVE>No</ISACTIVE></X>")
        assert bool_yes(elem, "ISACTIVE") is False

    def test_case_insensitive(self) -> None:
        elem = _elem("<X><ISACTIVE>YES</ISACTIVE></X>")
        assert bool_yes(elem, "ISACTIVE") is True

    def test_missing_returns_false(self) -> None:
        elem = _elem("<X/>")
        assert bool_yes(elem, "ISACTIVE") is False


# ── decimal_amount ─────────────────────────────────────────────────────────────


class TestDecimalAmount:
    def test_plain_positive(self) -> None:
        elem = _elem("<X><AMT>50000</AMT></X>")
        assert decimal_amount(elem, "AMT") == Decimal("50000")

    def test_plain_negative(self) -> None:
        elem = _elem("<X><AMT>-25000</AMT></X>")
        assert decimal_amount(elem, "AMT") == Decimal("-25000")

    def test_dr_suffix_makes_negative(self) -> None:
        elem = _elem("<X><AMT>30000 Dr</AMT></X>")
        assert decimal_amount(elem, "AMT") == Decimal("-30000")

    def test_cr_suffix_stays_positive(self) -> None:
        elem = _elem("<X><AMT>30000 Cr</AMT></X>")
        assert decimal_amount(elem, "AMT") == Decimal("30000")

    def test_decimal_value(self) -> None:
        elem = _elem("<X><AMT>1234.56</AMT></X>")
        assert decimal_amount(elem, "AMT") == Decimal("1234.56")

    def test_missing_returns_default(self) -> None:
        elem = _elem("<X/>")
        assert decimal_amount(elem, "AMT") == Decimal(0)

    def test_non_numeric_returns_default(self) -> None:
        elem = _elem("<X><AMT>N/A</AMT></X>")
        assert decimal_amount(elem, "AMT") == Decimal(0)


# ── quantity ──────────────────────────────────────────────────────────────────


class TestQuantity:
    def test_strips_unit_suffix(self) -> None:
        elem = _elem("<X><QTY>100 Nos</QTY></X>")
        assert quantity(elem, "QTY") == Decimal("100")

    def test_plain_number(self) -> None:
        elem = _elem("<X><QTY>250</QTY></X>")
        assert quantity(elem, "QTY") == Decimal("250")


# ── rate ──────────────────────────────────────────────────────────────────────


class TestRate:
    def test_strips_unit_denominator(self) -> None:
        elem = _elem("<X><RATE>250.50/Nos</RATE></X>")
        assert rate(elem, "RATE") == Decimal("250.50")

    def test_plain_number(self) -> None:
        elem = _elem("<X><RATE>100</RATE></X>")
        assert rate(elem, "RATE") == Decimal("100")

    def test_missing_returns_default(self) -> None:
        elem = _elem("<X/>")
        assert rate(elem, "RATE") == Decimal(0)


# ── text_list ─────────────────────────────────────────────────────────────────


class TestTextList:
    def test_extracts_multiple_items(self) -> None:
        elem = _elem(
            "<LEDGER>"
            '<ADDRESS.LIST TYPE="String">'
            "<ADDRESS>123 Main St</ADDRESS>"
            "<ADDRESS>Mumbai</ADDRESS>"
            "</ADDRESS.LIST>"
            "</LEDGER>"
        )
        assert text_list(elem, "ADDRESS.LIST", "ADDRESS") == ["123 Main St", "Mumbai"]

    def test_empty_list_tag(self) -> None:
        elem = _elem("<LEDGER><ADDRESS.LIST TYPE=\"String\"/></LEDGER>")
        assert text_list(elem, "ADDRESS.LIST", "ADDRESS") == []

    def test_missing_list_tag(self) -> None:
        elem = _elem("<LEDGER/>")
        assert text_list(elem, "ADDRESS.LIST", "ADDRESS") == []

    def test_skips_blank_entries(self) -> None:
        elem = _elem(
            "<LEDGER>"
            '<ADDRESS.LIST TYPE="String">'
            "<ADDRESS>Line 1</ADDRESS>"
            "<ADDRESS>   </ADDRESS>"
            "<ADDRESS>Line 3</ADDRESS>"
            "</ADDRESS.LIST>"
            "</LEDGER>"
        )
        result = text_list(elem, "ADDRESS.LIST", "ADDRESS")
        assert result == ["Line 1", "Line 3"]
