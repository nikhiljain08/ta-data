"""TallyPrime XML request builder — public facade over the TDL SDK.

All entity services call this class.  Internally it delegates to
app/tally_sdk/ which builds correct TDL-embedded XML envelopes instead of
the old static XML template files that used invalid report names.

Public interface is unchanged so no service code needs modification.
"""

from __future__ import annotations

import re

from app.tally_sdk import requests as _sdk

_DATE_RE = re.compile(r"^\d{8}$")


class TemplateError(ValueError):
    """Raised when a request cannot be built (empty company, bad date, etc.)."""


class TemplateEngine:
    """Builds TallyPrime XML export requests using embedded TDL collections."""

    # ── Entity request builders ───────────────────────────────────────────────

    def company(self) -> str:
        """Request all companies visible in TallyPrime (no company context needed)."""
        return _sdk.company_request()

    def ledger_groups(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.ledger_group_request(company=_require_company(company), alter_id=alter_id)

    def ledgers(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.ledger_request(company=_require_company(company), alter_id=alter_id)

    def voucher_types(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.voucher_type_request(company=_require_company(company), alter_id=alter_id)

    def vouchers(
        self,
        *,
        company: str,
        from_date: str,
        to_date: str,
        alter_id: int = 0,
    ) -> str:
        return _sdk.voucher_request(
            company=_require_company(company),
            from_date=_require_date(from_date, "from_date"),
            to_date=_require_date(to_date, "to_date"),
            alter_id=alter_id,
        )

    def stock_groups(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.stock_group_request(company=_require_company(company), alter_id=alter_id)

    def stock_items(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.stock_item_request(company=_require_company(company), alter_id=alter_id)

    def units(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.unit_request(company=_require_company(company), alter_id=alter_id)

    def godowns(self, *, company: str, alter_id: int = 0) -> str:
        return _sdk.godown_request(company=_require_company(company), alter_id=alter_id)

    def cost_centres(self, *, company: str, alter_id: int = 0) -> str:
        raise NotImplementedError("cost_centres export not yet implemented")

    def cost_categories(self, *, company: str, alter_id: int = 0) -> str:
        raise NotImplementedError("cost_categories export not yet implemented")

    def currencies(self, *, company: str, alter_id: int = 0) -> str:
        raise NotImplementedError("currencies export not yet implemented")


# ── Validators ────────────────────────────────────────────────────────────────


def _require_company(company: str) -> str:
    if not company or not company.strip():
        raise TemplateError("company name must not be empty")
    return company.strip()


def _require_date(value: str, param_name: str) -> str:
    if not _DATE_RE.match(value):
        raise TemplateError(f"{param_name} must be YYYYMMDD format, got: {value!r}")
    return value
