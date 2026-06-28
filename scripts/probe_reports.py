"""Probe the real TallySync reports and dump raw TallyPrime responses.

Run AFTER tallysync_exports.tdl is loaded in TallyPrime:
    .venv\\Scripts\\python scripts\\probe_reports.py

Shows exactly what each report returns so we can diagnose 0-record results
and the company-export error.
"""

from __future__ import annotations

import os

import requests

HOST = os.getenv("TALLY_HOST", "localhost")
PORT = int(os.getenv("TALLY_PORT", "9000"))
URL = f"http://{HOST}:{PORT}"
COMPANY = "H. S. CONTRACTS - H"
HEADERS = {"Content-Type": "text/xml;charset=utf-8"}


def _req(report: str, *, company: str = "", tsalterid: int = -1, dates: bool = False) -> str:
    sv = ["<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"]
    if company:
        sv.append(f"<SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>")
    if dates:
        sv.append("<SVFROMDATE>20240401</SVFROMDATE>")
        sv.append("<SVTODATE>20250630</SVTODATE>")
    sv.append(f"<TSALTERID>{tsalterid}</TSALTERID>")
    sv_block = "\n          ".join(sv)
    return (
        "<ENVELOPE>\n"
        "  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>\n"
        "  <BODY>\n"
        "    <EXPORTDATA>\n"
        "      <REQUESTDESC>\n"
        f"        <REPORTNAME>{report}</REPORTNAME>\n"
        "        <STATICVARIABLES>\n"
        f"          {sv_block}\n"
        "        </STATICVARIABLES>\n"
        "      </REQUESTDESC>\n"
        "    </EXPORTDATA>\n"
        "  </BODY>\n"
        "</ENVELOPE>"
    )


def _send(label: str, xml: str) -> None:
    print(f"\n{'=' * 70}\nTEST: {label}\n{'=' * 70}")
    try:
        r = requests.post(URL, data=xml.encode("utf-8"), headers=HEADERS, timeout=30)
        body = r.text
        print(f"HTTP {r.status_code} | {len(body)} chars")
        print("RESPONSE (first 4000 chars):")
        print(body[:4000])
    except Exception as exc:
        print(f"ERROR: {exc}")


# Company — no company context, full sync
_send("TS_CMP_REPORT (company, no context)", _req("TS_CMP_REPORT", tsalterid=-1))

# Ledger groups — with company, full sync (TSALTERID=-1)
_send(
    "TS_GRP_REPORT (groups, company, TSALTERID=-1)",
    _req("TS_GRP_REPORT", company=COMPANY, tsalterid=-1),
)

# Ledgers — with company, full sync
_send(
    "TS_LED_REPORT (ledgers, company, TSALTERID=-1)",
    _req("TS_LED_REPORT", company=COMPANY, tsalterid=-1),
)

# Ledgers — same but TSALTERID=0, to compare filter behaviour
_send(
    "TS_LED_REPORT (ledgers, company, TSALTERID=0)",
    _req("TS_LED_REPORT", company=COMPANY, tsalterid=0),
)

# Vouchers — with company + date range
_send(
    "TS_VOC_REPORT (vouchers, company, dates, TSALTERID=-1)",
    _req("TS_VOC_REPORT", company=COMPANY, tsalterid=-1, dates=True),
)

print(f"\n{'=' * 70}\nPROBE COMPLETE — paste output back.\n{'=' * 70}")
