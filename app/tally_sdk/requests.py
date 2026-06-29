"""Entity-specific TallyPrime export request builders.

Each function returns a complete XML envelope that references a named report
defined in ``tallysync_exports.tdl``.  Field definitions and collection types
live entirely in that TDL file — only the static variables (company context
and, for vouchers, the date range) vary per call.

The ``alter_id`` parameter is accepted for a uniform service-layer interface
but is NOT sent to TallyPrime: incremental AlterID filtering is performed in
the agent after parsing (see app/services/base.py).  Custom variables passed
via HTTP STATICVARIABLES are not reliably accessible inside collection
filters, so server-side AlterID filtering is not possible.

TDL file must be loaded in TallyPrime before these requests are sent.
See the header of ``tallysync_exports.tdl`` for setup instructions.
"""

from __future__ import annotations

from app.tally_sdk.builder import build_export


def company_request() -> str:
    """Export all companies (gateway-level — no company context)."""
    return build_export(key="CMP")


def ledger_group_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="GRP", company=company)


def ledger_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="LED", company=company)


def unit_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="UNIT", company=company)


def stock_group_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="SGRP", company=company)


def godown_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="GDN", company=company)


def voucher_type_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="VTYP", company=company)


def stock_item_request(*, company: str, alter_id: int = 0) -> str:
    return build_export(key="SITM", company=company)


def voucher_request(
    *,
    company: str,
    from_date: str,
    to_date: str,
    alter_id: int = 0,
) -> str:
    """Export vouchers bounded server-side by the date range (SVFROMDATE/SVTODATE).

    The TDL filter uses ``$$IsWithinPeriod:$Date`` which reads those variables.
    AlterID filtering within the range is applied in the agent after parsing.
    """
    return build_export(
        key="VOC",
        company=company,
        from_date=from_date,
        to_date=to_date,
    )


def purchase_order_request(
    *,
    company: str,
    from_date: str,
    to_date: str,
    alter_id: int = 0,
) -> str:
    """Export Purchase Order vouchers bounded by the date range."""
    return build_export(
        key="PO",
        company=company,
        from_date=from_date,
        to_date=to_date,
    )
