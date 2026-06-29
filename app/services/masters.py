from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain.godown import GodownRecord
from app.models.domain.ledger import LedgerRecord
from app.models.domain.ledger_group import LedgerGroupRecord
from app.models.domain.stock_group import StockGroupRecord
from app.models.domain.stock_item import StockItemRecord
from app.models.domain.unit import UnitRecord
from app.models.domain.voucher_type import VoucherTypeRecord
from app.parser.base import XmlSource
from app.parser.godown import parse_godowns, parse_godowns_with_raw
from app.parser.ledger import parse_ledgers, parse_ledgers_with_raw
from app.parser.ledger_group import parse_ledger_groups, parse_ledger_groups_with_raw
from app.parser.stock_group import parse_stock_groups, parse_stock_groups_with_raw
from app.parser.stock_item import parse_stock_items, parse_stock_items_with_raw
from app.parser.unit import parse_units, parse_units_with_raw
from app.parser.voucher_type import parse_voucher_types, parse_voucher_types_with_raw
from app.repositories.base import BaseRepository
from app.repositories.postgres.inventory import (
    GodownRepository,
    StockGroupRepository,
    StockItemRepository,
    UnitRepository,
)
from app.repositories.postgres.ledger import (
    LedgerGroupRepository,
    LedgerRepository,
    VoucherTypeRepository,
)
from app.services.base import BaseSyncService


class LedgerGroupSyncService(BaseSyncService[LedgerGroupRecord]):
    entity_name = "ledger_group"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.ledger_groups(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[LedgerGroupRecord]:
        return parse_ledger_groups(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[LedgerGroupRecord, bytes, dict[str, Any]]]:
        return parse_ledger_groups_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[LedgerGroupRecord]:
        return LedgerGroupRepository(session)


class UnitSyncService(BaseSyncService[UnitRecord]):
    entity_name = "unit"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.units(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[UnitRecord]:
        return parse_units(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[UnitRecord, bytes, dict[str, Any]]]:
        return parse_units_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[UnitRecord]:
        return UnitRepository(session)


class StockGroupSyncService(BaseSyncService[StockGroupRecord]):
    entity_name = "stock_group"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.stock_groups(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[StockGroupRecord]:
        return parse_stock_groups(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[StockGroupRecord, bytes, dict[str, Any]]]:
        return parse_stock_groups_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[StockGroupRecord]:
        return StockGroupRepository(session)


class GodownSyncService(BaseSyncService[GodownRecord]):
    entity_name = "godown"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.godowns(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[GodownRecord]:
        return parse_godowns(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[GodownRecord, bytes, dict[str, Any]]]:
        return parse_godowns_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[GodownRecord]:
        return GodownRepository(session)


class VoucherTypeSyncService(BaseSyncService[VoucherTypeRecord]):
    entity_name = "voucher_type"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.voucher_types(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[VoucherTypeRecord]:
        return parse_voucher_types(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[VoucherTypeRecord, bytes, dict[str, Any]]]:
        return parse_voucher_types_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[VoucherTypeRecord]:
        return VoucherTypeRepository(session)


class StockItemSyncService(BaseSyncService[StockItemRecord]):
    entity_name = "stock_item"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.stock_items(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[StockItemRecord]:
        return parse_stock_items(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[StockItemRecord, bytes, dict[str, Any]]]:
        return parse_stock_items_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[StockItemRecord]:
        return StockItemRepository(session)


class LedgerSyncService(BaseSyncService[LedgerRecord]):
    entity_name = "ledger"

    def _build_xml(self, company_name: str, alter_id: int) -> str:
        return self._template.ledgers(company=company_name, alter_id=alter_id)

    def _parse(self, source: XmlSource) -> Iterator[LedgerRecord]:
        return parse_ledgers(source)

    def _parse_with_raw(
        self, source: XmlSource
    ) -> Iterator[tuple[LedgerRecord, bytes, dict[str, Any]]]:
        return parse_ledgers_with_raw(source)

    def _make_repo(self, session: Session) -> BaseRepository[LedgerRecord]:
        return LedgerRepository(session)
