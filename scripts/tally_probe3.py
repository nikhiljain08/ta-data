"""Probe round 3 — after fixing PartiesDetails TDL error.

What changed:
  - TS_PV2_SP now iterates AllLedgerEntries (PartiesDetails was wrong)
  - TS_PV3_REPORT added: tests $Party, $BasicNarration, and Fetch-based access
  - Timeout raised to 60s so ledger/stock probes don't die on large collections

BEFORE running:
  1. Press Ctrl+Alt+R inside TallyPrime to hot-reload tallysync_exports.tdl.
  2. Confirm no error dialog appears (PartiesDetails error should be gone).
  3. Run: .venv/Scripts/python scripts/tally_probe3.py

Paste the full output back.
"""

from __future__ import annotations

import os

import requests

HOST    = os.getenv("TALLY_HOST", "localhost")
PORT    = int(os.getenv("TALLY_PORT", "9000"))
URL     = f"http://{HOST}:{PORT}"
COMPANY = os.getenv("TALLYSYNC_TALLY__COMPANY_NAME", "").strip()
HEADERS = {"Content-Type": "text/xml;charset=utf-8"}

VOC_FROM = "20250601"
VOC_TO   = "20250630"
TIMEOUT  = 60  # seconds — ledger/stock collections can be large


def _build(report_name: str, company: str = "", from_date: str = "", to_date: str = "") -> str:
    sv: list[str] = ["<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"]
    if company:
        sv.append(f"<SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>")
    if from_date and to_date:
        sv.append(f"<SVFROMDATE>{from_date}</SVFROMDATE>")
        sv.append(f"<SVTODATE>{to_date}</SVTODATE>")
    sv_block = "\n          ".join(sv)
    return (
        "<ENVELOPE>\n"
        "  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>\n"
        "  <BODY>\n"
        "    <EXPORTDATA>\n"
        "      <REQUESTDESC>\n"
        f"        <REPORTNAME>{report_name}</REPORTNAME>\n"
        "        <STATICVARIABLES>\n"
        f"          {sv_block}\n"
        "        </STATICVARIABLES>\n"
        "      </REQUESTDESC>\n"
        "    </EXPORTDATA>\n"
        "  </BODY>\n"
        "</ENVELOPE>"
    )


def _send(label: str, xml: str, truncate: int = 5000) -> None:
    print(f"\n{'='*72}")
    print(f"PROBE: {label}")
    print("=" * 72)
    try:
        r = requests.post(URL, data=xml.encode("utf-8"), headers=HEADERS, timeout=TIMEOUT)
        body = r.text
        print(f"HTTP {r.status_code}  len={len(body)}")
        print(body[:truncate])
        if len(body) > truncate:
            print(f"... [{len(body) - truncate} chars truncated]")
    except Exception as exc:
        print(f"ERROR: {exc}")


# ── Reference: Day Book (Tally built-in) — see what raw XML Tally generates
_send(
    "REF — Day Book built-in (first 5000 chars of Tally's own voucher export)",
    f"""<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Day Book</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
          <SVFROMDATE>{VOC_FROM}</SVFROMDATE>
          <SVTODATE>{VOC_TO}</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>""",
)

# ── Bug 2: Voucher party / narration ─────────────────────────────────────────

_send(
    "P_V3 — Voucher: $Party + $BasicNarration + Fetch:PartyLedgerName,Narration (NEW)",
    _build("TS_PV3_REPORT", company=COMPANY, from_date=VOC_FROM, to_date=VOC_TO),
)

_send(
    "P_V2 — Voucher sub-part: AllLedgerEntries (fixed — was PartiesDetails)",
    _build("TS_PV2_REPORT", company=COMPANY, from_date=VOC_FROM, to_date=VOC_TO),
    truncate=3000,
)

# ── Bug 1: Ledger GSTIN / email ───────────────────────────────────────────────

_send(
    "P_L1 — Ledger flat: $GSTIN vs $GSTRegistrationNumber, $LedgerEmail vs $Email",
    _build("TS_PL1_REPORT", company=COMPANY),
    truncate=3000,
)

_send(
    "P_L2 — Ledger sub-part: LedGSTRegDetails.LIST",
    _build("TS_PL2_REPORT", company=COMPANY),
    truncate=3000,
)

_send(
    "P_L3 — Ledger sub-part: MailingDetails.LIST",
    _build("TS_PL3_REPORT", company=COMPANY),
    truncate=3000,
)

# ── Bug 1: StockItem HSN ──────────────────────────────────────────────────────

_send(
    "P_SI1 — StockItem: flat $HSNCode vs GSTDetails.LIST sub-part",
    _build("TS_PSI1_REPORT", company=COMPANY),
    truncate=3000,
)

# ── Bug 1: Company GSTIN ─────────────────────────────────────────────────────

_send(
    "P_C1 — Company: $GSTIN vs $GSTRegistrationNumber vs $GSTNumber",
    _build("TS_PC1_REPORT"),
    truncate=3000,
)

print(f"\n{'='*72}")
print("PROBE COMPLETE — paste this output back.")
print("=" * 72)
