"""Probe round 4 — after fixing MailingDetails TDL error.

Covers remaining unknowns not resolved in probe3:
  - P_L3: Ledger mailing details (LedMailingDetails, now fixed in TDL)
  - P_SI1: StockItem HSN via GSTDetails sub-collection (was blocked by error dialog)
  - P_C1: Company GSTIN flat alternatives (was blocked by error dialog)
  - P_C2: Company GSTIN via sub-collection (CMPGSTRegDetails)

BEFORE running:
  1. Press Ctrl+Alt+R inside TallyPrime to hot-reload tallysync_exports.tdl.
  2. Confirm no error dialog appears.
  3. Run: .venv/Scripts/python scripts/tally_probe4.py

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


# ── P_L3: Ledger mailing details (LedMailingDetails — MailingDetails was wrong) ──
_send(
    "P_L3 — Ledger sub-part: LedMailingDetails (fixed from MailingDetails)",
    _build("TS_PL3_REPORT", company=COMPANY),
)

# ── P_SI1: StockItem HSN via GSTDetails sub-collection ───────────────────────
_send(
    "P_SI1 — StockItem: flat $HSNCode vs GSTDetails.LIST sub-part",
    _build("TS_PSI1_REPORT", company=COMPANY),
)

# ── P_C1: Company GSTIN flat alternatives ────────────────────────────────────
_send(
    "P_C1 — Company: $GSTIN vs $GSTRegistrationNumber vs $GSTNumber (flat)",
    _build("TS_PC1_REPORT"),
)

print(f"\n{'='*72}")
print("PROBE 4 COMPLETE — paste this output back.")
print("=" * 72)
