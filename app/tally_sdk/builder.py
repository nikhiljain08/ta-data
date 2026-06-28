"""HTTP export request builder for TallyPrime 7.

Generates ``Export Data`` XML envelopes that reference named reports defined
in ``tallysync_exports.tdl``.  That TDL file must be loaded in TallyPrime
before any sync requests are sent (one-time setup — see the file header).

STATICVARIABLES passed in each request
---------------------------------------
SVEXPORTFORMAT   Always ``$$SysName:XML``.
SVCURRENTCOMPANY Company context for master exports; absent for Company
                 collection (gateway-level, no company context required).
SVFROMDATE       Voucher date-range start (YYYYMMDD).  TDL filter uses
SVTODATE         ``$$IsWithinPeriod:$Date`` which reads these variables.

Incremental sync
----------------
AlterID filtering is done in the agent (Python) after parsing — NOT in TDL.
Custom variables passed via HTTP STATICVARIABLES are not reliably accessible
inside collection filters, so every collection returns its full set and the
agent drops records at/below the stored checkpoint.  The ``alter_id``
parameter is therefore not emitted into the request.
"""

from __future__ import annotations


def build_export(
    *,
    key: str,
    company: str = "",
    from_date: str = "",
    to_date: str = "",
) -> str:
    """Build a TallyPrime ``Export Data`` HTTP XML request.

    Parameters
    ----------
    key        Short uppercase key matching the report suffix in the TDL file
               (e.g. ``"CMP"`` → ``TS_CMP_REPORT``).
    company    ``SVCURRENTCOMPANY`` value; omit for Company export.
    from_date  Voucher date range start, YYYYMMDD.
    to_date    Voucher date range end, YYYYMMDD.
    """
    k = key.upper()

    sv_lines: list[str] = ["<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"]
    if company:
        sv_lines.append(f"<SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>")
    if from_date and to_date:
        sv_lines.append(f"<SVFROMDATE>{from_date}</SVFROMDATE>")
        sv_lines.append(f"<SVTODATE>{to_date}</SVTODATE>")

    sv_block = "\n          ".join(sv_lines)

    return (
        "<ENVELOPE>\n"
        "  <HEADER>\n"
        "    <TALLYREQUEST>Export Data</TALLYREQUEST>\n"
        "  </HEADER>\n"
        "  <BODY>\n"
        "    <EXPORTDATA>\n"
        "      <REQUESTDESC>\n"
        f"        <REPORTNAME>TS_{k}_REPORT</REPORTNAME>\n"
        "        <STATICVARIABLES>\n"
        f"          {sv_block}\n"
        "        </STATICVARIABLES>\n"
        "      </REQUESTDESC>\n"
        "    </EXPORTDATA>\n"
        "  </BODY>\n"
        "</ENVELOPE>"
    )
