"""Tests for app.parser.stock_group — StockGroupRecord parsing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.domain.stock_group import StockGroupRecord
from app.parser.stock_group import parse_stock_groups

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <STOCKGROUP NAME="Primary" RESERVEDNAME="">
      <GUID>sg-001</GUID>
      <PARENT></PARENT>
      <ISADDABLE>No</ISADDABLE>
      <ALTERID>15</ALTERID>
    </STOCKGROUP>
    <STOCKGROUP NAME="Electronics" RESERVEDNAME="">
      <GUID>sg-002</GUID>
      <PARENT>Primary</PARENT>
      <ISADDABLE>Yes</ISADDABLE>
      <ALTERID>16</ALTERID>
    </STOCKGROUP>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseStockGroups:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_stock_groups(_XML))) == 2

    def test_root_group(self) -> None:
        rec = next(parse_stock_groups(_XML))
        assert isinstance(rec, StockGroupRecord)
        assert rec.name == "Primary"
        assert rec.guid == "sg-001"
        assert rec.parent == ""
        assert rec.is_addable is False
        assert rec.alter_id == 15

    def test_child_group(self) -> None:
        rec = list(parse_stock_groups(_XML))[1]
        assert rec.name == "Electronics"
        assert rec.parent == "Primary"
        assert rec.is_addable is True
        assert rec.alter_id == 16

    def test_empty_collection(self) -> None:
        assert list(parse_stock_groups(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_stock_groups(_XML))
        with pytest.raises(ValidationError):
            rec.name = "changed"  # type: ignore[misc]
