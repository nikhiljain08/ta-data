"""Tests for app.parser.ledger_group — LedgerGroupRecord parsing."""

from __future__ import annotations

import pytest

from app.models.domain.ledger_group import LedgerGroupRecord
from app.parser.ledger_group import parse_ledger_groups

_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <GROUP NAME="Capital Account" RESERVEDNAME="Capital Account">
      <GUID>grp-001</GUID>
      <PARENT></PARENT>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <ISREVENUE>No</ISREVENUE>
      <AFFECTSSTOCK>No</AFFECTSSTOCK>
      <ALTERID>10</ALTERID>
    </GROUP>
    <GROUP NAME="Sundry Debtors" RESERVEDNAME="Sundry Debtors">
      <GUID>grp-002</GUID>
      <PARENT>Current Assets</PARENT>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <ISREVENUE>No</ISREVENUE>
      <AFFECTSSTOCK>No</AFFECTSSTOCK>
      <ALTERID>55</ALTERID>
    </GROUP>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY = b"<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>"


class TestParseLedgerGroups:
    def test_yields_correct_count(self) -> None:
        assert len(list(parse_ledger_groups(_XML))) == 2

    def test_root_group_has_empty_parent(self) -> None:
        rec = list(parse_ledger_groups(_XML))[0]
        assert isinstance(rec, LedgerGroupRecord)
        assert rec.name == "Capital Account"
        assert rec.parent == ""
        assert rec.is_deemed_positive is False
        assert rec.is_revenue is False
        assert rec.affects_stock is False
        assert rec.alter_id == 10

    def test_child_group(self) -> None:
        rec = list(parse_ledger_groups(_XML))[1]
        assert rec.name == "Sundry Debtors"
        assert rec.parent == "Current Assets"
        assert rec.is_deemed_positive is True
        assert rec.alter_id == 55

    def test_empty_collection(self) -> None:
        assert list(parse_ledger_groups(_EMPTY)) == []

    def test_records_are_frozen(self) -> None:
        rec = next(parse_ledger_groups(_XML))
        with pytest.raises(Exception):
            rec.name = "changed"  # type: ignore[misc]
