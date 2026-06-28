"""Tests for app.parser.godown — GodownRecord parsing."""

from __future__ import annotations

import pytest

from app.models.domain.godown import GodownRecord
from app.parser.godown import parse_godowns

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <GODOWN NAME="Main Warehouse" RESERVEDNAME="">
      <GUID>gdwn-001</GUID>
      <PARENT></PARENT>
      <HASNOSTOCK>No</HASNOSTOCK>
      <ALTERID>8</ALTERID>
    </GODOWN>
    <GODOWN NAME="Shelf A" RESERVEDNAME="">
      <GUID>gdwn-002</GUID>
      <PARENT>Main Warehouse</PARENT>
      <HASNOSTOCK>No</HASNOSTOCK>
      <ALTERID>9</ALTERID>
    </GODOWN>
    <GODOWN NAME="Virtual Godown" RESERVEDNAME="">
      <GUID>gdwn-003</GUID>
      <PARENT></PARENT>
      <HASNOSTOCK>Yes</HASNOSTOCK>
      <ALTERID>10</ALTERID>
    </GODOWN>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseGodowns:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_godowns(_XML))) == 3

    def test_top_level_godown(self) -> None:
        rec = list(parse_godowns(_XML))[0]
        assert isinstance(rec, GodownRecord)
        assert rec.name == "Main Warehouse"
        assert rec.guid == "gdwn-001"
        assert rec.parent == ""
        assert rec.has_no_stock is False
        assert rec.alter_id == 8

    def test_child_godown(self) -> None:
        rec = list(parse_godowns(_XML))[1]
        assert rec.name == "Shelf A"
        assert rec.parent == "Main Warehouse"

    def test_virtual_godown_has_no_stock(self) -> None:
        rec = list(parse_godowns(_XML))[2]
        assert rec.has_no_stock is True

    def test_empty_collection(self) -> None:
        assert list(parse_godowns(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_godowns(_XML))
        with pytest.raises(Exception):
            rec.name = "changed"  # type: ignore[misc]
