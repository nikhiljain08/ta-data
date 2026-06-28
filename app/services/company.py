from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.models.domain.company import CompanyRecord
from app.parser.base import XmlSource
from app.parser.company import parse_companies
from app.repositories.base import BaseRepository
from app.repositories.postgres.company import CompanyRepository
from app.services.base import BaseSyncService


class CompanySyncService(BaseSyncService[CompanyRecord]):
    """Syncs the list of open TallyPrime companies.

    The company XML request takes no company context — it returns all currently
    open companies.  AlterID is used to skip unchanged records.
    """

    entity_name = "company"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.company()  # no company context or AlterID filter

    def _parse(self, source: XmlSource) -> Iterator[CompanyRecord]:
        return parse_companies(source)

    def _make_repo(self, session: Session) -> BaseRepository[CompanyRecord]:
        return CompanyRepository(session)
