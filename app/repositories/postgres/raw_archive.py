"""Repositories for the fidelity layer: raw XML archive and entity versions.

RawArchiveRepository
    Upserts the latest raw XML for each entity into tally_raw_archive.
    Also provides batch hash lookup so the service can skip unchanged records.

EntityVersionRepository
    Inserts new version rows into tally_entity_versions whenever the XML hash
    changes.  Rows are append-only and protected by a unique constraint on
    (entity_type, company_name, guid, xml_hash) to prevent duplicates.
"""

from __future__ import annotations

import datetime
from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.db.raw_archive import TallyEntityVersionModel, TallyRawArchiveModel

_PARSER_VERSION = "1.0"

# PostgreSQL hard limit is 65,535 bound parameters per query.
# tally_raw_archive has ~12 writable columns; 500 rows x 12 = 6,000 params -- safe.
# tally_entity_versions has ~10 writable columns; 500 rows x 10 = 5,000 params -- safe.
_CHUNK_SIZE = 500


class RawArchiveRepository:
    """Read/write tally_raw_archive (one row per entity, latest state)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_latest_hashes(
        self,
        entity_type: str,
        company_name: str,
        guids: Sequence[str],
    ) -> dict[str, str]:
        """Return {guid: xml_hash} for the given guids from the raw archive.

        Missing guids (new entities) simply won't appear in the result dict.
        Batch fetch avoids N+1 queries.
        """
        if not guids:
            return {}
        rows = self._session.execute(
            text(
                "SELECT guid, xml_hash FROM tally_raw_archive "
                "WHERE entity_type = :et AND company_name = :cn "
                "AND guid = ANY(:guids)"
            ),
            {"et": entity_type, "cn": company_name, "guids": list(guids)},
        ).all()
        return {row.guid: row.xml_hash for row in rows}

    def upsert_batch(
        self,
        entity_type: str,
        company_name: str,
        records: Sequence[tuple[Any, bytes, str, dict[str, Any]]],
        sync_run_id: int | None,
    ) -> None:
        """Upsert raw XML rows; each tuple is (entity, raw_xml, xml_hash, unknown_fields).

        Automatically splits into _CHUNK_SIZE-row chunks to stay within
        PostgreSQL's 65,535-parameter-per-query ceiling.
        """
        if not records:
            return
        now = datetime.datetime.now(tz=datetime.UTC)
        rows = [
            {
                "entity_type": entity_type,
                "company_name": company_name,
                "entity_name": getattr(entity, "name", getattr(entity, "voucher_number", "")),
                "guid": getattr(entity, "guid", ""),
                "master_id": "",
                "alter_id": getattr(entity, "alter_id", 0),
                "xml": raw_xml.decode("utf-8", errors="replace"),
                "xml_hash": xml_hash,
                "unknown_fields": unknown_fields,
                "parser_version": _PARSER_VERSION,
                "sync_run_id": sync_run_id,
                "updated_at": now,
            }
            for entity, raw_xml, xml_hash, unknown_fields in records
        ]
        for i in range(0, len(rows), _CHUNK_SIZE):
            chunk = rows[i : i + _CHUNK_SIZE]
            stmt = insert(TallyRawArchiveModel).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["entity_type", "company_name", "guid"],
                set_={
                    "entity_name": stmt.excluded.entity_name,
                    "alter_id": stmt.excluded.alter_id,
                    "xml": stmt.excluded.xml,
                    "xml_hash": stmt.excluded.xml_hash,
                    "unknown_fields": stmt.excluded.unknown_fields,
                    "parser_version": stmt.excluded.parser_version,
                    "sync_run_id": stmt.excluded.sync_run_id,
                    "updated_at": now,
                },
            )
            self._session.execute(stmt)


class EntityVersionRepository:
    """Write-only repository for tally_entity_versions (append-only history)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_versions(
        self,
        entity_type: str,
        company_name: str,
        records: Sequence[tuple[Any, bytes, str, dict[str, Any]]],
        sync_run_id: int | None,
    ) -> None:
        """Insert version rows for records whose xml_hash changed.

        Uses ON CONFLICT DO NOTHING so duplicate hashes (e.g. re-syncing the same
        unchanged record) are silently skipped — the unique constraint on
        (entity_type, company_name, guid, xml_hash) guarantees idempotency.

        Automatically splits into _CHUNK_SIZE-row chunks.
        """
        if not records:
            return
        rows = []
        for entity, raw_xml, xml_hash, unknown_fields in records:
            try:
                normalized = entity.model_dump(mode="json")
            except Exception:
                normalized = {}
            rows.append(
                {
                    "entity_type": entity_type,
                    "company_name": company_name,
                    "entity_name": getattr(entity, "name", getattr(entity, "voucher_number", "")),
                    "guid": getattr(entity, "guid", ""),
                    "alter_id": getattr(entity, "alter_id", 0),
                    "xml_hash": xml_hash,
                    "xml": raw_xml.decode("utf-8", errors="replace"),
                    "normalized_json": normalized,
                    "unknown_fields": unknown_fields,
                    "parser_version": _PARSER_VERSION,
                    "sync_run_id": sync_run_id,
                }
            )
        for i in range(0, len(rows), _CHUNK_SIZE):
            chunk = rows[i : i + _CHUNK_SIZE]
            stmt = insert(TallyEntityVersionModel).values(chunk)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["entity_type", "company_name", "guid", "xml_hash"],
            )
            self._session.execute(stmt)
