"""Tests for app.parser.company — CompanyRecord parsing."""

from __future__ import annotations

import pytest

from app.models.domain.company import CompanyRecord
from app.parser.company import parse_companies

_COMPANIES_XML = b"""
<ENVELOPE>
  <BODY><DATA><COLLECTION>
    <COMPANY>
      <REMOTECMPNAME>Acme Industries Ltd</REMOTECMPNAME>
      <GUID>cmp-guid-001</GUID>
      <BOOKSBEGINNINGFROM>20230401</BOOKSBEGINNINGFROM>
      <STARTINGFROM>20230401</STARTINGFROM>
      <ENDINGAT>20240331</ENDINGAT>
      <COUNTRYNAME>India</COUNTRYNAME>
      <STATENAME>Maharashtra</STATENAME>
      <GSTIN>27AAAAA0000A1Z5</GSTIN>
      <ALTERID>1001</ALTERID>
    </COMPANY>
    <COMPANY>
      <REMOTECMPNAME>Beta Corp</REMOTECMPNAME>
      <GUID>cmp-guid-002</GUID>
      <BOOKSBEGINNINGFROM>20220401</BOOKSBEGINNINGFROM>
      <ALTERID>502</ALTERID>
    </COMPANY>
  </COLLECTION></DATA></BODY>
</ENVELOPE>
"""

_EMPTY_XML = b"""
<ENVELOPE><BODY><DATA><COLLECTION/></DATA></BODY></ENVELOPE>
"""


class TestParseCompanies:
    def test_yields_correct_count(self) -> None:
        records = list(parse_companies(_COMPANIES_XML))
        assert len(records) == 2

    def test_first_company_fields(self) -> None:
        rec = list(parse_companies(_COMPANIES_XML))[0]
        assert isinstance(rec, CompanyRecord)
        assert rec.name == "Acme Industries Ltd"
        assert rec.guid == "cmp-guid-001"
        assert rec.books_from == "20230401"
        assert rec.starting_from == "20230401"
        assert rec.ending_at == "20240331"
        assert rec.country == "India"
        assert rec.state == "Maharashtra"
        assert rec.gstin == "27AAAAA0000A1Z5"
        assert rec.alter_id == 1001

    def test_second_company_minimal(self) -> None:
        rec = list(parse_companies(_COMPANIES_XML))[1]
        assert rec.name == "Beta Corp"
        assert rec.alter_id == 502
        assert rec.gstin == ""

    def test_empty_collection_yields_nothing(self) -> None:
        assert list(parse_companies(_EMPTY_XML)) == []

    def test_records_are_immutable(self) -> None:
        rec = next(parse_companies(_COMPANIES_XML))
        with pytest.raises(Exception):
            rec.name = "changed"  # type: ignore[misc]

    def test_name_from_attribute_preferred(self) -> None:
        xml = b"""
        <ENVELOPE><BODY><DATA><COLLECTION>
          <COMPANY NAME="AttrName">
            <REMOTECMPNAME>ElemName</REMOTECMPNAME>
            <ALTERID>1</ALTERID>
          </COMPANY>
        </COLLECTION></DATA></BODY></ENVELOPE>
        """
        rec = next(parse_companies(xml))
        assert rec.name == "AttrName"
