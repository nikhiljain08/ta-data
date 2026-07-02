"""Aggregate-only check: does PARTYLEDGERNAME/NARRATION ever appear non-empty in raw XML,
broken down by voucher_type. Prints counts only, never raw XML or PII.
"""

from __future__ import annotations

from sqlalchemy import text

from app.config.settings import Settings
from app.database.engine import build_engine

settings = Settings.from_yaml("config.yaml")
engine = build_engine(settings.database)

with engine.connect() as conn:
    types = conn.execute(
        text("SELECT voucher_type, count(*) FROM vouchers GROUP BY voucher_type ORDER BY 2 DESC")
    ).all()
    print("voucher_type distribution:", types)

    # Does the raw XML string contain a non-empty PARTYLEDGERNAME tag at all, per voucher_type?
    rows = conn.execute(
        text(
            "SELECT v.voucher_type, "
            "count(*) FILTER (WHERE r.xml ~ '<PARTYLEDGERNAME>[^<]') AS has_party_tag, "
            "count(*) FILTER (WHERE r.xml ~ '<NARRATION>[^<]') AS has_narration_tag, "
            "count(*) AS total "
            "FROM tally_raw_archive r "
            "JOIN vouchers v ON v.guid = r.guid "
            "WHERE r.entity_type = 'voucher' "
            "GROUP BY v.voucher_type ORDER BY total DESC"
        )
    ).all()
    print("\nper voucher_type: (has_party_tag, has_narration_tag, total)")
    for row in rows:
        print(f"  {row[0]!r}: party={row[1]}/{row[3]}  narration={row[2]}/{row[3]}")
