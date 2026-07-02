"""Probe for Bug 1 (GST/address/HSN fields) and Bug 2 (party name / narration).

Calls pre-loaded TDL probe reports defined in tallysync_exports.tdl.
Each report tests one or more alternative field-access forms so we can see
which one Tally actually populates.

BEFORE running:
  1. Make sure tallysync_exports.tdl is loaded in TallyPrime.
  2. Press Ctrl+Alt+R inside TallyPrime to hot-reload the TDL.
  3. Then run: .venv/Scripts/python scripts/tally_probe2.py

Paste the full output back so we can identify working field names.
"""

from __future__ import annotations

import os

import requests

HOST = os.getenv("TALLY_HOST", "localhost")
PORT = int(os.getenv("TALLY_PORT", "9000"))
URL = f"http://{HOST}:{PORT}"
COMPANY = os.getenv("TALLYSYNC_TALLY__COMPANY_NAME", "").strip()

HEADERS = {"Content-Type": "text/xml;charset=utf-8"}

# Narrow date window keeps voucher probe output manageable.
VOC_FROM = "20250601"
VOC_TO   = "20250630"


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
        r = requests.post(URL, data=xml.encode("utf-8"), headers=HEADERS, timeout=15)
        body = r.text
        print(f"HTTP {r.status_code}  len={len(body)}")
        print(body[:truncate])
        if len(body) > truncate:
            print(f"... [{len(body) - truncate} chars truncated]")
    except Exception as exc:
        print(f"ERROR: {exc}")


# ── Bug 2: Voucher party name / narration ────────────────────────────────────

_send(
    "P_V1 — Voucher flat: $BasicPartyName vs $PartyLedgerName, $Narration vs $$RemoveEnter:$Narration",
    _build("TS_PV1_REPORT", company=COMPANY, from_date=VOC_FROM, to_date=VOC_TO),
)

_send(
    "P_V2 — Voucher sub-part: PartiesDetails.LIST → $LedgerName",
    _build("TS_PV2_REPORT", company=COMPANY, from_date=VOC_FROM, to_date=VOC_TO),
)

# ── Bug 1: Ledger GSTIN / email / address ────────────────────────────────────

_send(
    "P_L1 — Ledger flat: $GSTIN vs $GSTRegistrationNumber, $LedgerEmail vs $Email  (GST-registered ledgers only)",
    _build("TS_PL1_REPORT", company=COMPANY),
)

_send(
    "P_L2 — Ledger sub-part: LedGSTRegDetails.LIST → GSTIN field name variants",
    _build("TS_PL2_REPORT", company=COMPANY),
)

_send(
    "P_L3 — Ledger sub-part: MailingDetails.LIST → email / address  (ledgers with mobile only)",
    _build("TS_PL3_REPORT", company=COMPANY),
)

# ── Bug 1: StockItem HSN code ─────────────────────────────────────────────────

_send(
    "P_SI1 — StockItem: flat $HSNCode vs GSTDetails.LIST sub-part  (GST-applicable items only)",
    _build("TS_PSI1_REPORT", company=COMPANY),
)

# ── Bug 1: Company GSTIN ──────────────────────────────────────────────────────

_send(
    "P_C1 — Company: $GSTIN vs $GSTRegistrationNumber vs $GSTNumber",
    _build("TS_PC1_REPORT"),
)

print(f"\n{'='*72}")
print("PROBE COMPLETE — paste this output back to determine correct field names.")
print("=" * 72)
