"""One-off diagnostic: check tally_raw_archive for unknown/uncaptured fields.

Prints only aggregated counts and field names — never row data or credentials.
"""

from __future__ import annotations

import json
from collections import Counter

from sqlalchemy import text

from app.config.settings import Settings
from app.database.engine import build_engine

settings = Settings.from_yaml("config.yaml")
engine = build_engine(settings.database)

with engine.connect() as conn:
    total = conn.execute(text("SELECT count(*) FROM tally_raw_archive")).scalar_one()
    print(f"tally_raw_archive total rows: {total}")

    by_entity = conn.execute(
        text("SELECT entity_type, count(*) FROM tally_raw_archive GROUP BY entity_type ORDER BY 1")
    ).all()
    print("rows by entity_type:", dict(by_entity))

    rows = conn.execute(
        text(
            "SELECT entity_type, unknown_fields FROM tally_raw_archive "
            "WHERE unknown_fields IS NOT NULL AND unknown_fields::text <> '{}'"
        )
    ).all()
    print(f"\nrows with non-empty unknown_fields: {len(rows)}")

    field_counts: dict[str, Counter] = {}
    for entity_type, unknown in rows:
        data = unknown if isinstance(unknown, dict) else json.loads(unknown)
        field_counts.setdefault(entity_type, Counter()).update(data.keys())

    for entity_type, counter in field_counts.items():
        print(f"\n[{entity_type}] unknown/uncaptured tags seen (tag: row_count):")
        for tag, count in counter.most_common(20):
            print(f"  {tag}: {count}")

    # Null-rate spot check on a few important columns per entity table.
    print("\n--- null-rate spot checks ---")
    checks = [
        ("ledgers", ["gstin", "email", "state", "opening_balance"]),
        ("vouchers", ["party_ledger", "narration", "guid"]),
        ("stock_items", ["hsn_code", "opening_balance"]),
        ("companies", ["gstin", "books_from", "starting_from"]),
    ]
    for table, cols in checks:
        try:
            total_rows = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            if total_rows == 0:
                print(f"{table}: 0 rows, skipping")
                continue
            parts = [f"sum(({c} IS NULL OR {c}::text = '')::int) AS {c}_null" for c in cols]
            row = conn.execute(text(f"SELECT {', '.join(parts)} FROM {table}")).one()
            print(f"{table} ({total_rows} rows) null/empty counts: {dict(zip(cols, row))}")
        except Exception as exc:
            print(f"{table}: query failed — {exc}")
