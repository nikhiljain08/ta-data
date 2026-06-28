"""Low-level lxml.iterparse utilities shared by all entity parsers.

Design
------
* iter_collection() is the only entry point for streaming XML.
* It yields one completed lxml element per Tally entity and then clears that
  element plus its preceding siblings so memory stays O(1) regardless of how
  many records the response contains.
* Entity parsers receive bytes or a file-like stream; both paths go through the
  same code.

Amount format
-------------
Tally serialises monetary values as plain numbers ("50000", "-25000") or with a
trailing unit token ("100 Nos", "50000 Dr").  decimal_amount() handles all cases.
Rates from stock items arrive as "100.0/Nos"; quantity() strips the unit suffix.
"""

from __future__ import annotations

import datetime
import io
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
from typing import IO

import lxml.etree as etree

type XmlSource = bytes | IO[bytes]

# Tally serialises dates in its UI display format (e.g. "30-Jun-26", "1-Apr-17"),
# which is not fixed-width.  tally_date() normalises these to YYYYMMDD.
_DATE_FORMATS = ("%d-%b-%y", "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d")


def iter_collection(source: XmlSource, tag: str) -> Iterator[etree._Element]:
    """Stream-parse *source*, yielding each completed element whose tag matches.

    Clears each yielded element (and preceding siblings) after the caller
    finishes with it, keeping RSS bounded for large exports.
    """
    if isinstance(source, bytes):
        # TallyPrime sometimes embeds Windows-1252 bytes (e.g. ® = 0xAE) in XML
        # that is declared as UTF-8.  Detect and re-encode so lxml can parse it.
        try:
            source.decode("utf-8")
        except UnicodeDecodeError:
            source = source.decode("cp1252").encode("utf-8")
    stream: IO[bytes] = io.BytesIO(source) if isinstance(source, bytes) else source
    context = etree.iterparse(stream, events=("end",), tag=tag, recover=True)
    for _, elem in context:
        yield elem
        # Standard lxml memory-management pattern for large documents.
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]  # type: ignore[index]


# ── Field extractors ──────────────────────────────────────────────────────────


def text(elem: etree._Element, path: str, default: str = "") -> str:
    """Return stripped text of a direct child element, or *default*."""
    child = elem.find(path)
    if child is None:
        return default
    return (child.text or "").strip()


def name_of(elem: etree._Element) -> str:
    """Return the entity name — prefers the NAME attribute over the child tag."""
    return (elem.get("NAME") or text(elem, "NAME")).strip()


def integer(elem: etree._Element, path: str, default: int = 0) -> int:
    raw = text(elem, path)
    if not raw:
        return default
    try:
        return int(raw.split()[0])
    except (ValueError, IndexError):
        return default


def bool_yes(elem: etree._Element, path: str) -> bool:
    """True when child element text is 'Yes' (case-insensitive)."""
    return text(elem, path).lower() == "yes"


def tally_date(elem: etree._Element, path: str, default: str = "") -> str:
    """Normalise a Tally date to YYYYMMDD.

    Tally exports dates in its display format ("30-Jun-26", "1-Apr-17") which is
    not fixed-width and overflows the 8-char date columns.  Convert to YYYYMMDD
    so it fits and sorts correctly.  Returns *default* when unparseable or empty.
    Two-digit years follow Python's pivot (00-68 → 20xx, 69-99 → 19xx).
    """
    raw = text(elem, path)
    if not raw:
        return default
    if len(raw) == 8 and raw.isdigit():  # already YYYYMMDD
        return raw
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    return default


def decimal_amount(
    elem: etree._Element,
    path: str,
    default: Decimal = Decimal(0),
) -> Decimal:
    """Parse a Tally amount — handles plain numbers, negative, and Dr/Cr suffix.

    Tally examples: "50000", "-25000", "50000 Dr", "1800 Cr"
    'Dr' (debit) flips sign to negative; 'Cr' is already positive.
    """
    raw = text(elem, path)
    if not raw:
        return default
    parts = raw.split()
    numeric = parts[0].replace(",", "")
    try:
        value = Decimal(numeric)
    except InvalidOperation:
        return default
    if len(parts) > 1 and parts[1].upper() == "DR":
        value = -value
    return value


def quantity(elem: etree._Element, path: str, default: Decimal = Decimal(0)) -> Decimal:
    """Parse a Tally quantity — strips the unit suffix ('100 Nos' → 100)."""
    return decimal_amount(elem, path, default)


def rate(elem: etree._Element, path: str, default: Decimal = Decimal(0)) -> Decimal:
    """Parse a Tally rate string — strips the unit denominator ('100.0/Nos' → 100)."""
    raw = text(elem, path)
    if not raw:
        return default
    numeric = raw.split("/")[0].replace(",", "")
    try:
        return Decimal(numeric)
    except InvalidOperation:
        return default


def text_list(elem: etree._Element, list_tag: str, child_tag: str) -> list[str]:
    """Collect repeated child text values from a Tally .LIST container.

    Example: <ADDRESS.LIST TYPE="String"><ADDRESS>line1</ADDRESS></ADDRESS.LIST>
    """
    container = elem.find(list_tag)
    if container is None:
        return []
    return [
        (child.text or "").strip()
        for child in container.findall(child_tag)
        if child.text and child.text.strip()
    ]
