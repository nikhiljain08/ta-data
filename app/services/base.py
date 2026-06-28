from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import ClassVar

from loguru import logger
from sqlalchemy.orm import Session, sessionmaker

from app.client.tally_client import TallyClient
from app.database.session import session_scope
from app.parser.base import XmlSource
from app.repositories.base import BaseRepository
from app.repositories.postgres.checkpoint import CheckpointRepository
from app.xml.template_engine import TemplateEngine


class BaseSyncService[T](ABC):
    """Fetch → parse → upsert pipeline for a single Tally entity type.

    Subclasses implement three abstract methods:
    * _build_xml  — construct the XML request string
    * _parse      — convert raw bytes into domain records
    * _make_repo  — create the concrete repository for this entity

    The base sync() method handles AlterID checkpointing, audit logging,
    and session lifecycle automatically.
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

    def sync(self, company_name: str, *, full: bool = False) -> int:
        """Sync one entity for *company_name*. Returns records upserted."""
        with session_scope(self._session_factory) as session:
            cp = CheckpointRepository(session)
            run_id = cp.start_run(company_name, self.entity_name)
            try:
                alter_id = 0 if full else cp.get_alter_id(company_name, self.entity_name)
                xml = self._build_xml(company_name, alter_id)
                records = self._fetch_and_parse(xml)
                # AlterID filtering is done here, not in TDL: custom variables
                # passed via HTTP STATICVARIABLES are not reliably accessible in
                # collection filters, so Tally returns the full set every time.
                if not full and alter_id > 0:
                    records = [r for r in records if getattr(r, "alter_id", 0) > alter_id]
                count = 0
                if records:
                    repo = self._make_repo(session)
                    count = repo.upsert_batch(company_name, records)
                    max_id = max((getattr(r, "alter_id", 0) for r in records), default=0)
                    if max_id > alter_id:
                        cp.save_alter_id(company_name, self.entity_name, max_id)
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

    def _fetch_and_parse(self, xml: str) -> list[T]:
        """POST *xml* to Tally and parse the response."""
        data = self._client.request(xml)
        return list(self._parse(data))

    @abstractmethod
    def _build_xml(self, company_name: str, alter_id: int) -> str: ...

    @abstractmethod
    def _parse(self, source: XmlSource) -> Iterator[T]: ...

    @abstractmethod
    def _make_repo(self, session: Session) -> BaseRepository[T]: ...
