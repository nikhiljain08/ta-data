"""Diagnostic probe — tests multiple TallyPrime HTTP/XML request structures.

Run:
    .venv\Scripts\python scripts\tally_probe.py

Each test sends a minimal request and prints what TallyPrime returns.
Paste the output here so we can pick the structure that actually works.
"""

from __future__ import annotations

import os
import sys
import textwrap

import requests

HOST = os.getenv("TALLY_HOST", "localhost")
PORT = int(os.getenv("TALLY_PORT", "9000"))
URL = f"http://{HOST}:{PORT}"
COMPANY = os.getenv("TALLYSYNC_TALLY__COMPANY_NAME", "").strip()

HEADERS = {"Content-Type": "text/xml;charset=utf-8"}


def _send(label: str, xml: str) -> None:
    xml = textwrap.dedent(xml).strip()
    print(f"\n{'='*70}")
    print(f"TEST: {label}")
    print(f"{'='*70}")
    print("REQUEST (first 2000 chars):")
    print(xml[:2000])
    print()
    try:
        r = requests.post(URL, data=xml.encode("utf-8"), headers=HEADERS, timeout=10)
        body = r.text
        print(f"HTTP STATUS: {r.status_code}")
        print("RESPONSE (first 3000 chars):")
        print(body[:3000])
    except Exception as exc:
        print(f"ERROR: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# T1: Built-in "List of Companies" (gateway level, no company context)
# ─────────────────────────────────────────────────────────────────────────────
_send(
    "T1 — built-in 'List of Companies'",
    """
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>List of Companies</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T2: Built-in "Day Book" (vouchers, date range required by Tally)
# ─────────────────────────────────────────────────────────────────────────────
_send(
    "T2 — built-in 'Day Book' (vouchers)",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>Day Book</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
              <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
              <SVFROMDATE>20240401</SVFROMDATE>
              <SVTODATE>20250630</SVTODATE>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T3: TDLMESSAGE BEFORE EXPORTDATA in BODY — no metadata flags
# ─────────────────────────────────────────────────────────────────────────────
_send(
    "T3 — TDLMESSAGE before EXPORTDATA in BODY, NO metadata flags",
    """
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <TDLMESSAGE>
          <REPORT NAME="TS_PROBE_REPORT"><FORMS>TS_PROBE_FORM</FORMS></REPORT>
          <FORM NAME="TS_PROBE_FORM">
            <TOPPARTS>TS_PROBE_PART</TOPPARTS>
            <XMLTAG>TS_PROBE_LIST</XMLTAG>
          </FORM>
          <PART NAME="TS_PROBE_PART">
            <TOPLINES>TS_PROBE_LINE</TOPLINES>
            <REPEAT>TS_PROBE_LINE : TS_PROBE_COLL</REPEAT>
            <SCROLLED>Vertical</SCROLLED>
          </PART>
          <LINE NAME="TS_PROBE_LINE">
            <TOPFIELDS>TS_PROBE_F0</TOPFIELDS>
            <XMLTAG>COMPANY</XMLTAG>
          </LINE>
          <FIELD NAME="TS_PROBE_F0">
            <SET>$Name</SET>
            <XMLTAG>NAME</XMLTAG>
          </FIELD>
          <COLLECTION NAME="TS_PROBE_COLL">
            <TYPE>Company</TYPE>
          </COLLECTION>
        </TDLMESSAGE>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>TS_PROBE_REPORT</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T4: TDLMESSAGE BEFORE EXPORTDATA in BODY — WITH metadata flags
# ─────────────────────────────────────────────────────────────────────────────
_D = 'ISMODIFY="No" ISFIXED="No" ISINITIALIZE="No" ISOPTION="No" ISINTERNAL="No"'
_send(
    "T4 — TDLMESSAGE before EXPORTDATA in BODY, WITH metadata flags",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <TDLMESSAGE>
          <REPORT {_D} NAME="TS_PROBE2_REPORT"><FORMS>TS_PROBE2_FORM</FORMS></REPORT>
          <FORM {_D} NAME="TS_PROBE2_FORM">
            <TOPPARTS>TS_PROBE2_PART</TOPPARTS>
            <XMLTAG>TS_PROBE2_LIST</XMLTAG>
          </FORM>
          <PART {_D} NAME="TS_PROBE2_PART">
            <TOPLINES>TS_PROBE2_LINE</TOPLINES>
            <REPEAT>TS_PROBE2_LINE : TS_PROBE2_COLL</REPEAT>
            <SCROLLED>Vertical</SCROLLED>
          </PART>
          <LINE {_D} NAME="TS_PROBE2_LINE">
            <TOPFIELDS>TS_PROBE2_F0</TOPFIELDS>
            <XMLTAG>COMPANY</XMLTAG>
          </LINE>
          <FIELD {_D} NAME="TS_PROBE2_F0">
            <SET>$Name</SET>
            <XMLTAG>NAME</XMLTAG>
          </FIELD>
          <COLLECTION {_D} NAME="TS_PROBE2_COLL">
            <TYPE>Company</TYPE>
          </COLLECTION>
        </TDLMESSAGE>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>TS_PROBE2_REPORT</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T5: TDLMESSAGE AFTER EXPORTDATA in BODY — WITH metadata flags
# ─────────────────────────────────────────────────────────────────────────────
_send(
    "T5 — TDLMESSAGE after EXPORTDATA in BODY, WITH metadata flags",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>TS_PROBE3_REPORT</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
        <TDLMESSAGE>
          <REPORT {_D} NAME="TS_PROBE3_REPORT"><FORMS>TS_PROBE3_FORM</FORMS></REPORT>
          <FORM {_D} NAME="TS_PROBE3_FORM">
            <TOPPARTS>TS_PROBE3_PART</TOPPARTS>
            <XMLTAG>TS_PROBE3_LIST</XMLTAG>
          </FORM>
          <PART {_D} NAME="TS_PROBE3_PART">
            <TOPLINES>TS_PROBE3_LINE</TOPLINES>
            <REPEAT>TS_PROBE3_LINE : TS_PROBE3_COLL</REPEAT>
            <SCROLLED>Vertical</SCROLLED>
          </PART>
          <LINE {_D} NAME="TS_PROBE3_LINE">
            <TOPFIELDS>TS_PROBE3_F0</TOPFIELDS>
            <XMLTAG>COMPANY</XMLTAG>
          </LINE>
          <FIELD {_D} NAME="TS_PROBE3_F0">
            <SET>$Name</SET>
            <XMLTAG>NAME</XMLTAG>
          </FIELD>
          <COLLECTION {_D} NAME="TS_PROBE3_COLL">
            <TYPE>Company</TYPE>
          </COLLECTION>
        </TDLMESSAGE>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T6: TDLMESSAGE at ENVELOPE level (sibling of HEADER and BODY)
# ─────────────────────────────────────────────────────────────────────────────
_send(
    "T6 — TDLMESSAGE at ENVELOPE level (outside BODY), WITH metadata flags",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>TS_PROBE4_REPORT</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
      <TDLMESSAGE>
        <REPORT {_D} NAME="TS_PROBE4_REPORT"><FORMS>TS_PROBE4_FORM</FORMS></REPORT>
        <FORM {_D} NAME="TS_PROBE4_FORM">
          <TOPPARTS>TS_PROBE4_PART</TOPPARTS>
          <XMLTAG>TS_PROBE4_LIST</XMLTAG>
        </FORM>
        <PART {_D} NAME="TS_PROBE4_PART">
          <TOPLINES>TS_PROBE4_LINE</TOPLINES>
          <REPEAT>TS_PROBE4_LINE : TS_PROBE4_COLL</REPEAT>
          <SCROLLED>Vertical</SCROLLED>
        </PART>
        <LINE {_D} NAME="TS_PROBE4_LINE">
          <TOPFIELDS>TS_PROBE4_F0</TOPFIELDS>
          <XMLTAG>COMPANY</XMLTAG>
        </LINE>
        <FIELD {_D} NAME="TS_PROBE4_F0">
          <SET>$Name</SET>
          <XMLTAG>NAME</XMLTAG>
        </FIELD>
        <COLLECTION {_D} NAME="TS_PROBE4_COLL">
          <TYPE>Company</TYPE>
        </COLLECTION>
      </TDLMESSAGE>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T7: Built-in "List of Ledger" (may or may not be a valid name)
# ─────────────────────────────────────────────────────────────────────────────
_send(
    f"T7 — built-in 'List of Ledger' with company={COMPANY!r}",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>List of Ledger</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
              <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T8: Built-in "List of Accounts" (another candidate)
# ─────────────────────────────────────────────────────────────────────────────
_send(
    f"T8 — built-in 'List of Accounts' with company={COMPANY!r}",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>List of Accounts</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
              <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

# ─────────────────────────────────────────────────────────────────────────────
# T9: Current broken approach — TDLMESSAGE inside REQUESTDESC WITH flags
#     (to confirm the "inside REQUESTDESC" never works, regardless of flags)
# ─────────────────────────────────────────────────────────────────────────────
_send(
    "T9 — current broken approach: TDLMESSAGE inside REQUESTDESC, WITH flags (baseline)",
    f"""
    <ENVELOPE>
      <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
      <BODY>
        <EXPORTDATA>
          <REQUESTDESC>
            <REPORTNAME>TS_PROBE5_REPORT</REPORTNAME>
            <STATICVARIABLES>
              <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
            <TDLMESSAGE>
              <REPORT {_D} NAME="TS_PROBE5_REPORT"><FORMS>TS_PROBE5_FORM</FORMS></REPORT>
              <FORM {_D} NAME="TS_PROBE5_FORM">
                <TOPPARTS>TS_PROBE5_PART</TOPPARTS>
                <XMLTAG>TS_PROBE5_LIST</XMLTAG>
              </FORM>
              <PART {_D} NAME="TS_PROBE5_PART">
                <TOPLINES>TS_PROBE5_LINE</TOPLINES>
                <REPEAT>TS_PROBE5_LINE : TS_PROBE5_COLL</REPEAT>
                <SCROLLED>Vertical</SCROLLED>
              </PART>
              <LINE {_D} NAME="TS_PROBE5_LINE">
                <TOPFIELDS>TS_PROBE5_F0</TOPFIELDS>
                <XMLTAG>COMPANY</XMLTAG>
              </LINE>
              <FIELD {_D} NAME="TS_PROBE5_F0">
                <SET>$Name</SET>
                <XMLTAG>NAME</XMLTAG>
              </FIELD>
              <COLLECTION {_D} NAME="TS_PROBE5_COLL">
                <TYPE>Company</TYPE>
              </COLLECTION>
            </TDLMESSAGE>
          </REQUESTDESC>
        </EXPORTDATA>
      </BODY>
    </ENVELOPE>
    """,
)

print(f"\n{'='*70}")
print("PROBE COMPLETE")
print(f"{'='*70}")
print(
    "\nPaste this output back so we can identify which structure TallyPrime accepts."
)
