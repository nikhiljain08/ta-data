"""Unit tests for TemplateEngine and tally_sdk request builders.

The requests no longer contain inline TDL (TDLMESSAGE).  They are plain
``Export Data`` envelopes referencing named reports in tallysync_exports.tdl.
Tests verify: correct REPORTNAME, correct STATICVARIABLES, valid XML.
"""

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
        etree.fromstring(engine.company().encode())

    def test_references_cmp_report(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_CMP_REPORT</REPORTNAME>" in engine.company()

    def test_no_svcurrentcompany(self, engine: TemplateEngine) -> None:
        assert "SVCURRENTCOMPANY" not in engine.company()

    def test_no_tsalterid_emitted(self, engine: TemplateEngine) -> None:
        # AlterID filtering is done in Python, not sent to Tally.
        assert "TSALTERID" not in engine.company()

    def test_no_tdlmessage(self, engine: TemplateEngine) -> None:
        assert "TDLMESSAGE" not in engine.company()

    def test_export_data_request_type(self, engine: TemplateEngine) -> None:
        assert "<TALLYREQUEST>Export Data</TALLYREQUEST>" in engine.company()


class TestMasterRequests:
    def test_ledgers_valid_xml(self, engine: TemplateEngine) -> None:
        etree.fromstring(engine.ledgers(company="Acme Ltd").encode())

    def test_ledgers_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_LED_REPORT</REPORTNAME>" in engine.ledgers(company="Acme")

    def test_ledgers_sets_company(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd")
        assert "<SVCURRENTCOMPANY>Acme Ltd</SVCURRENTCOMPANY>" in xml

    def test_ledgers_does_not_emit_tsalterid(self, engine: TemplateEngine) -> None:
        # alter_id is accepted for interface compatibility but never sent.
        assert "TSALTERID" not in engine.ledgers(company="Acme", alter_id=5000)

    def test_ledger_groups_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_GRP_REPORT</REPORTNAME>" in engine.ledger_groups(company="Acme")

    def test_voucher_types_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_VTYP_REPORT</REPORTNAME>" in engine.voucher_types(company="Acme")

    def test_stock_groups_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_SGRP_REPORT</REPORTNAME>" in engine.stock_groups(company="Acme")

    def test_stock_items_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_SITM_REPORT</REPORTNAME>" in engine.stock_items(company="Acme")

    def test_units_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_UNIT_REPORT</REPORTNAME>" in engine.units(company="Acme")

    def test_godowns_report_name(self, engine: TemplateEngine) -> None:
        assert "<REPORTNAME>TS_GDN_REPORT</REPORTNAME>" in engine.godowns(company="Acme")

    def test_no_tdlmessage_in_masters(self, engine: TemplateEngine) -> None:
        assert "TDLMESSAGE" not in engine.ledgers(company="Acme")


class TestVoucherRequest:
    def test_valid_xml(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        etree.fromstring(xml.encode())

    def test_report_name(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<REPORTNAME>TS_VOC_REPORT</REPORTNAME>" in xml

    def test_includes_svfromdate(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<SVFROMDATE>20240401</SVFROMDATE>" in xml

    def test_includes_svtodate(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "<SVTODATE>20240430</SVTODATE>" in xml

    def test_does_not_emit_tsalterid(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(
            company="Acme", from_date="20240401", to_date="20240430", alter_id=1234
        )
        assert "TSALTERID" not in xml

    def test_no_tdlmessage(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(company="Acme", from_date="20240401", to_date="20240430")
        assert "TDLMESSAGE" not in xml

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

    def test_company_with_spaces_works(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Private Limited")
        assert "Acme Private Limited" in xml

    def test_company_is_stripped(self, engine: TemplateEngine) -> None:
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
