from __future__ import annotations

import datetime
import hashlib
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, ClassVar

from loguru import logger
from sqlalchemy.orm import Session, sessionmaker

from app.client.tally_client import TallyClient
from app.database.session import session_scope
from app.parser.base import XmlSource
from app.repositories.base import BaseRepository
from app.repositories.postgres.checkpoint import CheckpointRepository
from app.repositories.postgres.raw_archive import EntityVersionRepository, RawArchiveRepository
from app.xml.template_engine import TemplateEngine

_PARSER_VERSION = "1.0"

# Tuple layout: (domain_record, raw_xml_bytes, xml_hash_hex, unknown_fields)
type _FidelityRow[T] = tuple[T, bytes, str, dict[str, Any]]


class BaseSyncService[T](ABC):
    """Fetch → parse → upsert pipeline for a single Tally entity type.

    Subclasses implement three abstract methods:
    * _build_xml       — construct the XML request string
    * _parse           — convert raw bytes into domain records (legacy path)
    * _make_repo       — create the concrete repository for this entity

    Subclasses MAY override _parse_with_raw() to enable the fidelity pipeline:
    hash-based change detection, raw XML archiving, and entity versioning.
    If _parse_with_raw() returns None the legacy upsert path is used unchanged.
    """

    entity_name: ClassVar[str] = ""

    def __init__(
        self,
        client: TallyClient,
        template: TemplateEngine,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._client = client
        self._template = template
        self._session_factory = session_factory
        self._is_full_sync: bool = False
        self._last_synced_at: datetime.datetime | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def sync(self, company_name: str, *, full: bool = False) -> int:
        """Sync one entity for *company_name*. Returns records upserted."""
        with session_scope(self._session_factory) as session:
            cp = CheckpointRepository(session)
            run_id = cp.start_run(company_name, self.entity_name)
            try:
                alter_id = 0 if full else cp.get_alter_id(company_name, self.entity_name)
                self._is_full_sync = full
                self._last_synced_at = cp.get_last_synced_at(company_name, self.entity_name)
                xml = self._build_xml(company_name, alter_id)

                fidelity_items = self._fetch_and_parse_with_raw(xml)
                if fidelity_items is not None:
                    count, inserted, updated, skipped = self._run_fidelity_pipeline(
                        session=session,
                        company_name=company_name,
                        alter_id=alter_id,
                        full=full,
                        items=fidelity_items,
                        run_id=run_id,
                    )
                    if count > 0 or full:
                        max_id = max(
                            (getattr(r, "alter_id", 0) for r, _, _, _ in fidelity_items),
                            default=0,
                        )
                        if max_id > alter_id or full:
                            cp.save_alter_id(company_name, self.entity_name, max_id)
                    cp.finish_run(
                        run_id,
                        status="success",
                        records_synced=count,
                        records_inserted=inserted,
                        records_updated=updated,
                        records_skipped=skipped,
                        parser_version=_PARSER_VERSION,
                    )
                else:
                    count = self._run_legacy_pipeline(
                        session=session,
                        company_name=company_name,
                        alter_id=alter_id,
                        full=full,
                        xml=xml,
                        cp=cp,
                        run_id=run_id,
                    )
                    cp.finish_run(run_id, status="success", records_synced=count)

                logger.debug(
                    "Entity sync complete",
                    entity=self.entity_name,
                    company=company_name,
                    records=count,
                )
                return count

            except Exception as exc:
                logger.error(
                    "Entity sync error",
                    entity=self.entity_name,
                    company=company_name,
                    error=str(exc),
                    exc_info=True,
                )
                try:
                    cp.finish_run(run_id, status="failure", error_message=str(exc))
                except Exception as record_exc:
                    logger.warning(
                        "Could not record sync failure to DB",
                        record_error=str(record_exc),
                    )
                raise

    # ── Fidelity pipeline ─────────────────────────────────────────────────────

    def _run_fidelity_pipeline(
        self,
        *,
        session: Session,
        company_name: str,
        alter_id: int,
        full: bool,
        items: list[_FidelityRow[T]],
        run_id: int,
    ) -> tuple[int, int, int, int]:
        """Hash-based deduplication → upsert entity → archive raw XML → create version.

        Returns (total_processed, inserted, updated, skipped).
        """
        if not full and alter_id > 0:
            items = [r for r in items if getattr(r[0], "alter_id", 0) > alter_id]

        if not items:
            return 0, 0, 0, 0

        # Batch-fetch existing xml_hashes from archive to avoid N queries.
        guids = [getattr(r, "guid", "") for r, _, _, _ in items]
        raw_repo = RawArchiveRepository(session)
        existing_hashes = raw_repo.get_latest_hashes(self.entity_name, company_name, guids)

        new_or_changed: list[_FidelityRow[T]] = []
        unchanged: list[_FidelityRow[T]] = []

        for item in items:
            record, _raw, xml_hash, _unknown = item
            guid = getattr(record, "guid", "")
            stored_hash = existing_hashes.get(guid)
            if stored_hash is None or stored_hash != xml_hash:
                new_or_changed.append(item)
            else:
                unchanged.append(item)

        inserted = 0
        updated = 0

        if new_or_changed:
            # Upsert into the normalised entity table.
            repo = self._make_repo(session)
            repo.upsert_batch(company_name, [r for r, _, _, _ in new_or_changed])

            # Determine inserted vs updated by checking which guids were in existing_hashes.
            for record, _, _, _ in new_or_changed:
                guid = getattr(record, "guid", "")
                if guid in existing_hashes:
                    updated += 1
                else:
                    inserted += 1

            # Archive raw XML for new/changed records (upserts alter_id too).
            raw_repo.upsert_batch(self.entity_name, company_name, new_or_changed, run_id)

            # Append version rows (ON CONFLICT DO NOTHING on unique hash).
            ver_repo = EntityVersionRepository(session)
            ver_repo.create_versions(self.entity_name, company_name, new_or_changed, run_id)

        # For unchanged records still update alter_id in raw archive without new version.
        if unchanged:
            raw_repo.upsert_batch(self.entity_name, company_name, unchanged, run_id)

        skipped = len(unchanged)
        total = inserted + updated
        return total, inserted, updated, skipped

    def _run_legacy_pipeline(
        self,
        *,
        session: Session,
        company_name: str,
        alter_id: int,
        full: bool,
        xml: str,
        cp: CheckpointRepository,
        run_id: int,
    ) -> int:
        """Original upsert-everything path, used when _parse_with_raw() is not implemented."""
        records = self._fetch_and_parse(xml)
        if not full and alter_id > 0:
            records = [r for r in records if getattr(r, "alter_id", 0) > alter_id]
        count = 0
        if records:
            repo = self._make_repo(session)
            count = repo.upsert_batch(company_name, records)
            max_id = max((getattr(r, "alter_id", 0) for r in records), default=0)
            if max_id > alter_id or full:
                cp.save_alter_id(company_name, self.entity_name, max_id)
        return count

    # ── Override hooks ────────────────────────────────────────────────────────

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[T, bytes, dict[str, Any]]] | None:
        """Return (record, raw_xml_bytes, unknown_fields) tuples, or None to use legacy path."""
        return None

    def _fetch_and_parse_with_raw(self, xml: str) -> list[_FidelityRow[T]] | None:
        """Fetch XML from Tally and run _parse_with_raw(), computing SHA-256 hash per record.

        Returns None if _parse_with_raw() is not overridden.
        """
        it = self._parse_with_raw(self._client.request(xml))
        if it is None:
            return None
        result: list[_FidelityRow[T]] = []
        for record, raw, unknown in it:
            xml_hash = hashlib.sha256(raw).hexdigest()
            result.append((record, raw, xml_hash, unknown))
        return result

    def _fetch_and_parse(self, xml: str) -> list[T]:
        """POST *xml* to Tally and parse the response (legacy path)."""
        data = self._client.request(xml)
        return list(self._parse(data))

    @abstractmethod
    def _build_xml(self, company_name: str, alter_id: int) -> str: ...

    @abstractmethod
    def _parse(self, source: XmlSource) -> Iterator[T]: ...

    @abstractmethod
    def _make_repo(self, session: Session) -> BaseRepository[T]: ...
