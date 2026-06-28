"""Unit tests for the TDL-based TemplateEngine and tally_sdk builders."""

from __future__ import annotations

import lxml.etree as etree
import pytest

from app.xml.template_engine import TemplateEngine, TemplateError, _require_date

# ── Helpers ───────────────────────────────────────────────────────────────────


class TestRequireDate:
    def test_valid_date_passes(self) -> None:
        assert _require_date("20240401", "from_date") == "20240401"

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(TemplateError, match="YYYYMMDD"):
            _require_date("2024-04-01", "from_date")

    def test_too_short_raises(self) -> None:
        with pytest.raises(TemplateError):
            _require_date("2024401", "to_date")

    def test_non_digit_raises(self) -> None:
        with pytest.raises(TemplateError):
            _require_date("2024ABCD", "from_date")


# ── TemplateEngine ────────────────────────────────────────────────────────────


@pytest.fixture()
def engine() -> TemplateEngine:
    return TemplateEngine()


class TestCompanyRequest:
    def test_returns_valid_xml(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        etree.fromstring(xml.encode())  # must not raise

    def test_contains_tdl_collection(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<TDLMESSAGE>" in xml
        assert "<COLLECTION" in xml

    def test_uses_company_collection_type(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<TYPE>Company</TYPE>" in xml

    def test_no_svcurrentcompany(self, engine: TemplateEngine) -> None:
        # Company collection is gateway-scoped; no company context should be set
        xml = engine.company()
        assert "SVCURRENTCOMPANY" not in xml

    def test_exports_company_record_tag(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<XMLTAG>COMPANY</XMLTAG>" in xml

    def test_exports_name_field(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<XMLTAG>NAME</XMLTAG>" in xml

    def test_exports_guid_field(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<XMLTAG>GUID</XMLTAG>" in xml

    def test_exports_alterid_field(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<XMLTAG>ALTERID</XMLTAG>" in xml


class TestMasterRequests:
    def test_ledgers_full_sync_valid_xml(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd")
        etree.fromstring(xml.encode())

    def test_ledgers_sets_company(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd")
        assert "<SVCURRENTCOMPANY>Acme Ltd</SVCURRENTCOMPANY>" in xml

    def test_ledgers_uses_ledger_type(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd")
        assert "<TYPE>Ledger</TYPE>" in xml

    def test_ledgers_exports_ledger_tag(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd")
        assert "<XMLTAG>LEDGER</XMLTAG>" in xml

    def test_ledgers_full_sync_no_filter(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd", alter_id=0)
        assert "FILTER" not in xml

    def test_ledgers_incremental_includes_filter(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd", alter_id=5000)
        assert "FILTER" in xml
        assert "5000" in xml
        assert "$AlterID" in xml

    def test_ledger_groups_uses_group_type(self, engine: TemplateEngine) -> None:
        xml = engine.ledger_groups(company="Acme Ltd")
        assert "<TYPE>Group</TYPE>" in xml
        assert "<XMLTAG>GROUP</XMLTAG>" in xml

    def test_voucher_types_valid_xml(self, engine: TemplateEngine) -> None:
        xml = engine.voucher_types(company="Acme Ltd")
        etree.fromstring(xml.encode())
        assert "<TYPE>VoucherType</TYPE>" in xml
        assert "<XMLTAG>VOUCHERTYPE</XMLTAG>" in xml

    def test_stock_groups_uses_stockgroup_type(self, engine: TemplateEngine) -> None:
        xml = engine.stock_groups(company="Acme Ltd")
        assert "<TYPE>StockGroup</TYPE>" in xml
        assert "<XMLTAG>STOCKGROUP</XMLTAG>" in xml

    def test_stock_items_valid_xml(self, engine: TemplateEngine) -> None:
        xml = engine.stock_items(company="Acme Ltd")
        etree.fromstring(xml.encode())
        assert "<TYPE>StockItem</TYPE>" in xml
        assert "<XMLTAG>STOCKITEM</XMLTAG>" in xml

    def test_units_uses_unit_type(self, engine: TemplateEngine) -> None:
        xml = engine.units(company="Acme Ltd")
        assert "<TYPE>Unit</TYPE>" in xml
        assert "<XMLTAG>UNIT</XMLTAG>" in xml

    def test_godowns_uses_godown_type(self, engine: TemplateEngine) -> None:
        xml = engine.godowns(company="Acme Ltd")
        assert "<TYPE>Godown</TYPE>" in xml
        assert "<XMLTAG>GODOWN</XMLTAG>" in xml


class TestVoucherRequest:
    def test_valid_xml(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        etree.fromstring(xml.encode())

    def test_includes_svfromdate(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<SVFROMDATE>20240401</SVFROMDATE>" in xml

    def test_includes_svtodate(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<SVTODATE>20240430</SVTODATE>" in xml

    def test_uses_voucher_type(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<TYPE>Voucher</TYPE>" in xml

    def test_exports_voucher_tag(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<XMLTAG>VOUCHER</XMLTAG>" in xml

    def test_includes_date_filter_formula(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "$$IsWithinPeriod:$Date" in xml

    def test_incremental_combines_date_and_alterid_filter(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(
            company="Acme", from_date="20240401", to_date="20240430", alter_id=1234
        )
        assert "1234" in xml
        assert "$AlterID" in xml
        assert "$$IsWithinPeriod:$Date" in xml

    def test_includes_ledger_entries_sub_collection(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "AllLedgerEntries" in xml
        assert "<XMLTAG>ALLLEDGERENTRIES.LIST</XMLTAG>" in xml

    def test_includes_inventory_entries_sub_collection(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "AllInventoryEntries" in xml
        assert "<XMLTAG>ALLINVENTORYENTRIES.LIST</XMLTAG>" in xml

    def test_invalid_from_date_raises(self, engine: TemplateEngine) -> None:
        with pytest.raises(TemplateError, match="YYYYMMDD"):
            engine.vouchers(company="Acme", from_date="01-04-2024", to_date="20240430")

    def test_invalid_to_date_raises(self, engine: TemplateEngine) -> None:
        with pytest.raises(TemplateError, match="YYYYMMDD"):
            engine.vouchers(company="Acme", from_date="20240401", to_date="30/04/2024")


class TestValidation:
    def test_empty_company_raises(self, engine: TemplateEngine) -> None:
        with pytest.raises(TemplateError, match="company name"):
            engine.ledgers(company="")

    def test_whitespace_only_company_raises(self, engine: TemplateEngine) -> None:
        with pytest.raises(TemplateError, match="company name"):
            engine.ledgers(company="   ")

    def test_company_name_with_spaces_works(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Private Limited")
        assert "Acme Private Limited" in xml

    def test_company_name_is_stripped(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="  Acme Ltd  ")
        assert "<SVCURRENTCOMPANY>Acme Ltd</SVCURRENTCOMPANY>" in xml


class TestAllOutputValidXml:
    """Every builder must produce parseable, well-formed XML."""

    def test_company(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.company().encode())

    def test_ledger_groups(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.ledger_groups(company="X").encode())

    def test_ledgers(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.ledgers(company="X", alter_id=100).encode())

    def test_units(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.units(company="X").encode())

    def test_stock_groups(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.stock_groups(company="X").encode())

    def test_godowns(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.godowns(company="X").encode())

    def test_voucher_types(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.voucher_types(company="X").encode())

    def test_stock_items(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.stock_items(company="X").encode())

    def test_vouchers(self, engine: TemplateEngine) -> None:
        etree.fromstring(
            engine.vouchers(company="X", from_date="20240401", to_date="20240430").encode()
        )
