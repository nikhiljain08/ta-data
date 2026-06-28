"""Core TDL XML envelope builder for TallyPrime 7.

TallyPrime's HTTP/XML API accepts embedded TDL (Tally Definition Language) in
the request envelope to define arbitrary data exports.  This module builds
those envelopes programmatically so every entity uses the same correct format.

TDL object hierarchy
--------------------
REPORT → FORM → PART → LINE → FIELD
                      ↘ (EXPLODE) → PART → LINE → FIELD
COLLECTION defines the data source (type + optional filter formula).
SYSTEM TYPE="Formulae" defines filter expressions.

TDL declaration flags
---------------------
Every element defined inside TDLMESSAGE MUST carry the five TDL metadata
attributes below.  Without them TallyPrime treats the element as a
modification of an existing built-in definition and fails to resolve the
custom report name with "Could not find Report".

    ISMODIFY="No" ISFIXED="No" ISINITIALIZE="No" ISOPTION="No" ISINTERNAL="No"

Response format
---------------
TallyPrime responds with the XML structure defined by the FORM / LINE XMLTAG
attributes, wrapped in the standard ENVELOPE/BODY/DATA envelope.  The parsers
in app/parser/ use lxml.iterparse to find specific element tags (e.g. LEDGER,
GROUP) anywhere in the document, so only the inner element tags need to match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

# Five mandatory attributes every TDL definition element must carry so
# TallyPrime registers it as a new definition rather than a modification.
_D = 'ISMODIFY="No" ISFIXED="No" ISINITIALIZE="No" ISOPTION="No" ISINTERNAL="No"'


class TdlField(NamedTuple):
    """Maps one TallyPrime TDL expression to an output XML element tag."""

    expr: str  # TDL expression, e.g. "$Name", "$$YesNo:$IsInvoice"
    xml_tag: str  # Output XML element name, e.g. "NAME", "ISDEEMEDPOSITIVE"


@dataclass
class TdlSubPart:
    """Nested data exported via EXPLODE — child records within a parent record.

    Used for ledger entries / inventory entries within a voucher.  The
    collection_type uses TallyPrime's "ChildType : ParentType" syntax so the
    sub-collection is scoped to the current parent object in context.
    """

    collection_type: str  # e.g. "AllLedgerEntries : Voucher"
    xml_record_tag: str  # XML tag per child record, e.g. "ALLLEDGERENTRIES.LIST"
    fields: list[TdlField]


def build_export(
    *,
    key: str,
    tally_type: str,
    xml_record_tag: str,
    fields: list[TdlField],
    company: str = "",
    alter_id: int = 0,
    from_date: str = "",
    to_date: str = "",
    sub_parts: list[TdlSubPart] | None = None,
) -> str:
    """Build a complete TDL-embedded XML export request for TallyPrime 7.

    Parameters
    ----------
    key          Short uppercase tag used to generate unique TDL element names.
    tally_type   TallyPrime object collection type, e.g. "Ledger", "Voucher".
    xml_record_tag  XML element name per exported record, e.g. "LEDGER".
    fields       (TDL expression, XML tag) pairs for the main record.
    company      SVCURRENTCOMPANY value; omitted from the envelope when empty
                 (correct for Company collection which works at gateway level).
    alter_id     Last known AlterID for incremental sync; 0 = full sync
                 (no filter added).
    from_date    YYYYMMDD start date — sets SVFROMDATE and $$IsWithinPeriod
                 filter (used for Voucher exports).
    to_date      YYYYMMDD end date — sets SVTODATE.
    sub_parts    Nested child collections exported via EXPLODE.
    """
    k = key.upper()

    # ── Static variables ──────────────────────────────────────────────────────
    sv_lines: list[str] = ["<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"]
    if company:
        sv_lines.append(f"<SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>")
    if from_date and to_date:
        sv_lines.append(f"<SVFROMDATE>{from_date}</SVFROMDATE>")
        sv_lines.append(f"<SVTODATE>{to_date}</SVTODATE>")
    sv_block = "\n          ".join(sv_lines)

    # ── Collection filter formula ─────────────────────────────────────────────
    filter_clauses: list[str] = []
    if from_date and to_date:
        # $$IsWithinPeriod uses SVFROMDATE / SVTODATE set above
        filter_clauses.append("$$IsWithinPeriod:$Date")
    if alter_id > 0:
        filter_clauses.append(f"$AlterID > {alter_id}")

    filter_ref = ""
    filter_def = ""
    if filter_clauses:
        filter_ref = f"<FILTER>TS_{k}_FILTER</FILTER>"
        filter_def = (
            f'<SYSTEM {_D} TYPE="Formulae" NAME="TS_{k}_FILTER">'
            + " AND ".join(filter_clauses)
            + "</SYSTEM>"
        )

    # ── Main record fields ────────────────────────────────────────────────────
    main_names: list[str] = []
    main_defs: list[str] = []
    for i, fld in enumerate(fields):
        fname = f"TS_{k}_F{i}"
        main_names.append(fname)
        main_defs.append(
            f'          <FIELD {_D} NAME="{fname}">'
            f"<SET>{fld.expr}</SET>"
            f"<XMLTAG>{fld.xml_tag}</XMLTAG>"
            f"</FIELD>"
        )

    # ── Sub-parts via EXPLODE ─────────────────────────────────────────────────
    explode_attr = ""
    sub_defs: list[str] = []
    if sub_parts:
        explode_names: list[str] = []
        for sp_idx, sp in enumerate(sub_parts):
            spk = f"TS_{k}_SP{sp_idx}"
            explode_names.append(spk)

            sp_field_names: list[str] = []
            sp_field_defs: list[str] = []
            for fi, fld in enumerate(sp.fields):
                fname = f"{spk}_F{fi}"
                sp_field_names.append(fname)
                sp_field_defs.append(
                    f'          <FIELD {_D} NAME="{fname}">'
                    f"<SET>{fld.expr}</SET>"
                    f"<XMLTAG>{fld.xml_tag}</XMLTAG>"
                    f"</FIELD>"
                )

            sub_defs.extend(
                [
                    f'          <PART {_D} NAME="{spk}">',
                    f"            <TOPLINES>{spk}_LINE</TOPLINES>",
                    f"            <REPEAT>{spk}_LINE : {spk}_COLL</REPEAT>",
                    "          </PART>",
                    f'          <LINE {_D} NAME="{spk}_LINE">',
                    f"            <TOPFIELDS>{','.join(sp_field_names)}</TOPFIELDS>",
                    f"            <XMLTAG>{sp.xml_record_tag}</XMLTAG>",
                    "          </LINE>",
                    *sp_field_defs,
                    f'          <COLLECTION {_D} NAME="{spk}_COLL">',
                    f"            <TYPE>{sp.collection_type}</TYPE>",
                    "          </COLLECTION>",
                ]
            )

        explode_attr = f"<EXPLODE>{','.join(explode_names)}</EXPLODE>"

    # ── Assemble complete envelope ─────────────────────────────────────────────
    main_fields_block = "\n".join(main_defs)
    sub_parts_block = "\n".join(sub_defs)
    explode_line = f"\n            {explode_attr}" if explode_attr else ""

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
        "        <TDLMESSAGE>\n"
        f'          <REPORT {_D} NAME="TS_{k}_REPORT"><FORMS>TS_{k}_FORM</FORMS></REPORT>\n'
        f'          <FORM {_D} NAME="TS_{k}_FORM">\n'
        f"            <TOPPARTS>TS_{k}_PART</TOPPARTS>\n"
        f"            <XMLTAG>TS_{k}_LIST</XMLTAG>\n"
        "          </FORM>\n"
        f'          <PART {_D} NAME="TS_{k}_PART">\n'
        f"            <TOPLINES>TS_{k}_LINE</TOPLINES>\n"
        f"            <REPEAT>TS_{k}_LINE : TS_{k}_COLL</REPEAT>\n"
        "            <SCROLLED>Vertical</SCROLLED>\n"
        "          </PART>\n"
        f'          <LINE {_D} NAME="TS_{k}_LINE">\n'
        f"            <TOPFIELDS>{','.join(main_names)}</TOPFIELDS>"
        f"{explode_line}\n"
        f"            <XMLTAG>{xml_record_tag}</XMLTAG>\n"
        "          </LINE>\n"
        f"{main_fields_block}\n"
        f"{sub_parts_block}\n"
        f'          <COLLECTION {_D} NAME="TS_{k}_COLL">\n'
        f"            <TYPE>{tally_type}</TYPE>\n"
        f"            {filter_ref}\n"
        "          </COLLECTION>\n"
        f"          {filter_def}\n"
        "        </TDLMESSAGE>\n"
        "      </REQUESTDESC>\n"
        "    </EXPORTDATA>\n"
        "  </BODY>\n"
        "</ENVELOPE>"
    )
