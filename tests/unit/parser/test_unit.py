"""Tests for app.parser.unit — UnitRecord parsing."""

from __future__ import annotations

import pytest

from app.models.domain.unit import UnitRecord
from app.parser.unit import parse_units

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <UNIT NAME="Nos" RESERVEDNAME="">
      <GUID>unit-001</GUID>
      <GSTUNITNAME>OTH</GSTUNITNAME>
      <FORMALNAME>Numbers</FORMALNAME>
      <ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>
      <ALTERID>1</ALTERID>
    </UNIT>
    <UNIT NAME="Box" RESERVEDNAME="">
      <GUID>unit-002</GUID>
      <GSTUNITNAME>BOX</GSTUNITNAME>
      <FORMALNAME>Box</FORMALNAME>
      <ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>
      <ALTERID>2</ALTERID>
    </UNIT>
    <UNIT NAME="Dz" RESERVEDNAME="">
      <GUID>unit-003</GUID>
      <GSTUNITNAME>OTH</GSTUNITNAME>
      <ISSIMPLEUNIT>No</ISSIMPLEUNIT>
      <ALTERID>3</ALTERID>
    </UNIT>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseUnits:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_units(_XML))) == 3

    def test_simple_unit_fields(self) -> None:
        rec = list(parse_units(_XML))[0]
        assert isinstance(rec, UnitRecord)
        assert rec.name == "Nos"
        assert rec.guid == "unit-001"
        assert rec.gst_unit_name == "OTH"
        assert rec.formal_name == "Numbers"
        assert rec.is_simple_unit is True
        assert rec.alter_id == 1

    def test_compound_unit(self) -> None:
        rec = list(parse_units(_XML))[2]
        assert rec.name == "Dz"
        assert rec.is_simple_unit is False

    def test_empty_collection(self) -> None:
        assert list(parse_units(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_units(_XML))
        with pytest.raises(Exception):
            rec.name = "changed"  # type: ignore[misc]
