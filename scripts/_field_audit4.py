"""Aggregate-only check: GSTIN/email/address (ledgers), HSNCODE (stock items),
GSTIN (company), PartyLedgerName/Narration (vouchers).
Prints counts only — never raw XML or PII.
"""

from __future__ import annotations

from sqlalchemy import text

from app.config.settings import Settings
from app.database.engine import build_engine

settings = Settings.from_yaml("config.yaml")
engine = build_engine(settings.database)

with engine.connect() as conn:
    print("=== LEDGERS ===")
    total = conn.execute(text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='ledger'")).scalar_one()
    # GSTIN lives in <LEDGSTREGDETAILS.LIST><GSTIN>value</GSTIN> after the fix.
    has_gstin = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='ledger' AND xml ~ '<GSTIN>[^<]'")
    ).scalar_one()
    # Email lives in <LEDMAILINGDETAILS.LIST><EMAIL>value</EMAIL> after the fix.
    has_email = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='ledger' AND xml ~ '<EMAIL>[^<]'")
    ).scalar_one()
    # Address lives in <LEDMAILINGDETAILS.LIST><ADDRESS>value</ADDRESS> after the fix.
    has_address = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='ledger' AND xml ~ '<ADDRESS>[^<]'")
    ).scalar_one()
    has_mobile = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='ledger' AND xml ~ '<LEDGERMOBILE>[^<]'")
    ).scalar_one()
    has_gstregtype = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='ledger' AND xml ~ '<GSTREGISTRATIONTYPE>[^<]'")
    ).scalar_one()
    print(
        f"total={total} gstin={has_gstin} email={has_email} "
        f"address={has_address} mobile={has_mobile} gst_reg_type={has_gstregtype}"
    )

    print("\n=== STOCK ITEMS ===")
    total_si = conn.execute(text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='stock_item'")).scalar_one()
    # HSNCODE lives in <GSTDETAILS.LIST><HSNCODE>value</HSNCODE> after the fix.
    has_hsn = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='stock_item' AND xml ~ '<HSNCODE>[^<]'")
    ).scalar_one()
    has_gstapplicable = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='stock_item' AND xml ~ '<GSTAPPLICABLE>[^<]'")
    ).scalar_one()
    has_category = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='stock_item' AND xml ~ '<CATEGORY>[^<]'")
    ).scalar_one()
    has_baseunits = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='stock_item' AND xml ~ '<BASEUNITS>[^<]'")
    ).scalar_one()
    print(f"total={total_si} hsn_code={has_hsn} gst_applicable={has_gstapplicable} category={has_category} base_units={has_baseunits}")

    print("\n=== COMPANY ===")
    total_c = conn.execute(text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='company'")).scalar_one()
    # GSTIN lives in <GSTDETAILS.LIST><GSTIN>value</GSTIN> after the fix.
    has_cgstin = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='company' AND xml ~ '<GSTIN>[^<]'")
    ).scalar_one()
    print(f"total={total_c} gstin={has_cgstin}")

    print("\n=== VOUCHERS ===")
    total_v = conn.execute(text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='voucher'")).scalar_one()
    # These were 0% before — Fetch on collection was needed.
    has_party = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='voucher' AND xml ~ '<PARTYLEDGERNAME>[^<]'")
    ).scalar_one()
    has_narration = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='voucher' AND xml ~ '<NARRATION>[^<]'")
    ).scalar_one()
    has_vouchernum = conn.execute(
        text("SELECT count(*) FROM tally_raw_archive WHERE entity_type='voucher' AND xml ~ '<VOUCHERNUMBER>[^<]'")
    ).scalar_one()
    print(
        f"total={total_v} party_ledger={has_party} narration={has_narration} "
        f"voucher_number={has_vouchernum} (sanity)"
    )
