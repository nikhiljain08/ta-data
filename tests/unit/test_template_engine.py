"""Unit tests for the XML TemplateEngine."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.xml.template_engine import (
    TemplateEngine,
    TemplateError,
    _alter_id_block,
    _require_date,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


class TestAlterIdBlock:
    def test_zero_returns_empty(self) -> None:
        assert _alter_id_block(0) == ""

    def test_negative_returns_empty(self) -> None:
        assert _alter_id_block(-1) == ""

    def test_positive_returns_fragment(self) -> None:
        block = _alter_id_block(9999)
        assert "<ALTERID>9999</ALTERID>" in block

    def test_fragment_is_valid_xml_fragment(self) -> None:
        import lxml.etree as etree

        block = _alter_id_block(42)
        etree.fromstring(block)  # must not raise


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


class TestTemplateEngineLoading:
    def test_loads_template_from_disk(self, engine: TemplateEngine) -> None:
        xml = engine.company()
        assert "<ENVELOPE>" in xml
        assert "List of Companies" in xml

    def test_caches_template_after_first_load(self, engine: TemplateEngine) -> None:
        engine.ledgers(company="TestCo")
        before = len(engine._cache)
        engine.ledgers(company="TestCo")
        assert len(engine._cache) == before  # no new cache entries

    def test_missing_template_raises(self, tmp_path: Path) -> None:
        empty_engine = TemplateEngine(template_dir=tmp_path)
        with pytest.raises(TemplateError, match="not found"):
            empty_engine.company()


class TestMasterRequests:
    def test_ledgers_full_sync(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd")
        assert "<REPORTNAME>Ledger</REPORTNAME>" in xml
        assert "<SVCURRENTCOMPANY>Acme Ltd</SVCURRENTCOMPANY>" in xml
        assert "<ALTERID>" not in xml

    def test_ledgers_incremental_includes_alter_id(self, engine: TemplateEngine) -> None:
        xml = engine.ledgers(company="Acme Ltd", alter_id=5000)
        assert "<ALTERID>5000</ALTERID>" in xml

    def test_ledger_groups(self, engine: TemplateEngine) -> None:
        xml = engine.ledger_groups(company="Acme Ltd")
        assert "<REPORTNAME>Group</REPORTNAME>" in xml

    def test_voucher_types(self, engine: TemplateEngine) -> None:
        xml = engine.voucher_types(company="Acme Ltd")
        assert "<REPORTNAME>Voucher Type</REPORTNAME>" in xml

    def test_stock_groups(self, engine: TemplateEngine) -> None:
        xml = engine.stock_groups(company="Acme Ltd")
        assert "<REPORTNAME>Stock Group</REPORTNAME>" in xml

    def test_stock_items(self, engine: TemplateEngine) -> None:
        xml = engine.stock_items(company="Acme Ltd")
        assert "<REPORTNAME>Stock Item</REPORTNAME>" in xml

    def test_units(self, engine: TemplateEngine) -> None:
        xml = engine.units(company="Acme Ltd")
        assert "<REPORTNAME>Unit</REPORTNAME>" in xml

    def test_godowns(self, engine: TemplateEngine) -> None:
        xml = engine.godowns(company="Acme Ltd")
        assert "<REPORTNAME>Godown</REPORTNAME>" in xml

    def test_cost_centres(self, engine: TemplateEngine) -> None:
        xml = engine.cost_centres(company="Acme Ltd")
        assert "<REPORTNAME>Cost Centre</REPORTNAME>" in xml

    def test_cost_categories(self, engine: TemplateEngine) -> None:
        xml = engine.cost_categories(company="Acme Ltd")
        assert "<REPORTNAME>Cost Category</REPORTNAME>" in xml

    def test_currencies(self, engine: TemplateEngine) -> None:
        xml = engine.currencies(company="Acme Ltd")
        assert "<REPORTNAME>Currency</REPORTNAME>" in xml


class TestVoucherRequest:
    def test_voucher_includes_date_range(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(
            company="Acme Ltd", from_date="20240401", to_date="20240430"
        )
        assert "<SVFROMDATE>20240401</SVFROMDATE>" in xml
        assert "<SVTODATE>20240430</SVTODATE>" in xml

    def test_voucher_incremental(self, engine: TemplateEngine) -> None:
        xml = engine.vouchers(
            company="Acme Ltd",
            from_date="20240401",
            to_date="20240430",
            alter_id=1234,
        )
        assert "<ALTERID>1234</ALTERID>" in xml

    def test_voucher_invalid_from_date_raises(self, engine: TemplateEngine) -> None:
        with pytest.raises(TemplateError, match="YYYYMMDD"):
            engine.vouchers(
                company="Acme Ltd", from_date="01-04-2024", to_date="20240430"
            )

    def test_voucher_invalid_to_date_raises(self, engine: TemplateEngine) -> None:
        with pytest.raises(TemplateError, match="YYYYMMDD"):
            engine.vouchers(
                company="Acme Ltd", from_date="20240401", to_date="30/04/2024"
            )


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


class TestOutputIsValidXML:
    """All rendered templates must produce parseable XML."""

    def test_company_is_valid_xml(self, engine: TemplateEngine) -> None:
        import lxml.etree as etree

        etree.fromstring(engine.company().encode())

    def test_ledgers_is_valid_xml(self, engine: TemplateEngine) -> None:
        import lxml.etree as etree

        etree.fromstring(engine.ledgers(company="Acme", alter_id=100).encode())

    def test_vouchers_is_valid_xml(self, engine: TemplateEngine) -> None:
        import lxml.etree as etree

        etree.fromstring(
            engine.vouchers(
                company="Acme", from_date="20240401", to_date="20240430"
            ).encode()
        )
