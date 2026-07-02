"""Probe round 5 — StockItem HSN and Company GSTIN.

P_SI1 returned 0 items because the filter ($GSTApplicable = "Applicable")
matched nothing.  This script probes without a filter (P_SI2) to see what
$GSTApplicable actually returns, and whether the GSTDetails sub-collection
works.  Also adds Fetch to the collection as an alternative.

P_C1 showed all flat GSTIN variants are empty on Company — same pattern as
Ledger.  P_C2 probes CMPGSTRegDetails sub-collection (analogue of
LedGSTRegDetails).

BEFORE running:
  1. Press Ctrl+Alt+R inside TallyPrime.
  2. Confirm no error dialog.
  3. Run: .venv/Scripts/python scripts/tally_probe5.py
"""

from __future__ import annotations

import os

import requests

HOST    = os.getenv("TALLY_HOST", "localhost")
PORT    = int(os.getenv("TALLY_PORT", "9000"))
URL     = f"http://{HOST}:{PORT}"
COMPANY = os.getenv("TALLYSYNC_TALLY__COMPANY_NAME", "").strip()
HEADERS = {"Content-Type": "text/xml;charset=utf-8"}
TIMEOUT = 60


def _build(report_name: str, company: str = "") -> str:
    sv: list[str] = ["<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"]
    if company:
        sv.append(f"<SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>")
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


def _send(label: str, xml: str, truncate: int = 4000) -> None:
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


# ── P_SI2: StockItem — no filter, first 10 items, GSTDetails sub-part ────────
# P_SI1 returned 0 because $GSTApplicable = "Applicable" matched nothing.
# Here we show all items (no filter) to see the real $GSTApplicable value
# and test the GSTDetails sub-collection.
_send(
    "P_SI2 — StockItem: no filter, flat HSNCode + GSTDetails sub-part",
    _build("TS_PSI2_REPORT", company=COMPANY),
)

# ── P_C2: Company — GSTDetails sub-collection (CMPGSTRegDetails was invalid) ────
_send(
    "P_C2 — Company: GSTDetails sub-collection for GSTIN",
    _build("TS_PC2_REPORT"),
)

# ── P_C3: Company — Fetch forces $GSTIN pre-load (same trick that fixed Voucher) ──
_send(
    "P_C3 — Company: Fetch:GSTIN on collection",
    _build("TS_PC3_REPORT"),
)

print(f"\n{'='*72}")
print("PROBE 5 COMPLETE — paste this output back.")
print("=" * 72)
