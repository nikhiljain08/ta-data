"""XML template engine for TallyPrime requests.

Design
------
* Templates are .xml files in app/xml/ — one per Tally entity.
* Placeholders use Python's string.Template syntax: $variable.
* Optional fragments (AlterID for incremental sync, date range for vouchers)
  are composed in Python, then substituted as a single block — this avoids
  conditional logic inside XML files.
* Template files are loaded once and cached for the lifetime of the engine.

Usage
-----
    engine = TemplateEngine()

    # Full sync — no AlterID filter
    xml = engine.ledgers(company="MyCompany Ltd")

    # Incremental sync — AlterID filter applied
    xml = engine.ledgers(company="MyCompany Ltd", alter_id=8450)

    # Vouchers always need a date window
    xml = engine.vouchers(company="MyCompany Ltd", from_date="20240401", to_date="20240430")

Tally date format
-----------------
Tally expects dates as YYYYMMDD strings (e.g. "20240401").
The engine validates and normalises date strings before substitution.
"""

from __future__ import annotations

import re
import string
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent

# AlterID XML fragment — inserted into STATICVARIABLES when alter_id > 0.
# alter_id=0 means "full sync, no filter".
_ALTER_ID_FRAGMENT = "<ALTERID>{alter_id}</ALTERID>"

# Regex for validating Tally date strings (YYYYMMDD).
_DATE_RE = re.compile(r"^\d{8}$")


class TemplateError(ValueError):
    """Raised when a template cannot be rendered (missing vars, invalid dates)."""


class TemplateEngine:
    """Loads and renders TallyPrime XML request templates.

    Thread-safe after construction — the template cache is read-only once
    populated.  One shared instance per process is sufficient.
    """

    def __init__(self, template_dir: Path = _TEMPLATE_DIR) -> None:
        self._dir = template_dir
        self._cache: dict[str, string.Template] = {}

    # ── Entity request builders ───────────────────────────────────────────────

    def company(self) -> str:
        """Request the list of open companies.  No company context needed."""
        return self._render("company.xml")

    def ledger_groups(self, *, company: str, alter_id: int = 0) -> str:
        """Export all ledger groups (masters).  AlterID=0 → full sync."""
        return self._render(
            "ledger_group.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def ledgers(self, *, company: str, alter_id: int = 0) -> str:
        """Export all ledgers (party master, bank accounts, etc.)."""
        return self._render(
            "ledger.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def voucher_types(self, *, company: str, alter_id: int = 0) -> str:
        """Export all voucher type definitions."""
        return self._render(
            "voucher_type.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def vouchers(
        self,
        *,
        company: str,
        from_date: str,
        to_date: str,
        alter_id: int = 0,
    ) -> str:
        """Export vouchers within [from_date, to_date] (YYYYMMDD).

        The date window is mandatory — fetching all vouchers at once would
        produce an unbounded response for active companies.  The sync engine
        batches by month.
        """
        return self._render(
            "voucher.xml",
            company=_require_company(company),
            from_date=_require_date(from_date, "from_date"),
            to_date=_require_date(to_date, "to_date"),
            alter_id_block=_alter_id_block(alter_id),
        )

    def stock_groups(self, *, company: str, alter_id: int = 0) -> str:
        """Export stock group hierarchy."""
        return self._render(
            "stock_group.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def stock_items(self, *, company: str, alter_id: int = 0) -> str:
        """Export stock items (inventory master)."""
        return self._render(
            "stock_item.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def units(self, *, company: str, alter_id: int = 0) -> str:
        """Export units of measure."""
        return self._render(
            "unit.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def godowns(self, *, company: str, alter_id: int = 0) -> str:
        """Export godowns (warehouse / storage locations)."""
        return self._render(
            "godown.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def cost_centres(self, *, company: str, alter_id: int = 0) -> str:
        """Export cost centres."""
        return self._render(
            "cost_centre.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def cost_categories(self, *, company: str, alter_id: int = 0) -> str:
        """Export cost categories."""
        return self._render(
            "cost_category.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    def currencies(self, *, company: str, alter_id: int = 0) -> str:
        """Export currencies."""
        return self._render(
            "currency.xml",
            company=_require_company(company),
            alter_id_block=_alter_id_block(alter_id),
        )

    # ── Core rendering ────────────────────────────────────────────────────────

    def _render(self, template_name: str, **params: str) -> str:
        """Load template, substitute params, return the XML string.

        Uses string.Template.substitute() which raises KeyError on any
        unreplaced placeholder — catches template/param mismatches early.
        """
        tmpl = self._load(template_name)
        try:
            return tmpl.substitute(params)
        except KeyError as exc:
            raise TemplateError(
                f"Template '{template_name}' has unreplaced placeholder: {exc}"
            ) from exc
        except ValueError as exc:
            raise TemplateError(f"Template '{template_name}' substitution failed: {exc}") from exc

    def _load(self, name: str) -> string.Template:
        if name not in self._cache:
            path = self._dir / name
            if not path.exists():
                raise TemplateError(f"XML template not found: {path}")
            self._cache[name] = string.Template(path.read_text(encoding="utf-8"))
        return self._cache[name]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _alter_id_block(alter_id: int) -> str:
    """Return the <ALTERID> XML fragment, or empty string for full sync."""
    if alter_id <= 0:
        return ""
    return _ALTER_ID_FRAGMENT.format(alter_id=alter_id)


def _require_company(company: str) -> str:
    if not company or not company.strip():
        raise TemplateError("company name must not be empty")
    return company.strip()


def _require_date(value: str, param_name: str) -> str:
    """Validate and return a Tally date string (YYYYMMDD)."""
    if not _DATE_RE.match(value):
        raise TemplateError(f"{param_name} must be YYYYMMDD format, got: {value!r}")
    return value
