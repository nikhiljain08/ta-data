from __future__ import annotations

from dataclasses import dataclass, field

from loguru import logger


@dataclass
class SyncResult:
    synced: dict[str, int] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def total_records(self) -> int:
        return sum(self.synced.values())

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


class SyncEngine:
    """Orchestrates entity syncs for a single company in FK-dependency order.

    Each entity is synced independently; a failure in one entity is logged and
    recorded in SyncResult but does not abort subsequent entities.
    """

    def __init__(
        self,
        services: dict[str, object],  # entity_name → BaseSyncService
        entity_order: list[str],
    ) -> None:
        self._services = services
        self._order = entity_order

    def sync_entity(self, company_name: str, entity: str) -> SyncResult:
        """Sync a single entity immediately — called by TDL event triggers."""
        result = SyncResult()
        svc = self._services.get(entity)
        if svc is None:
            logger.warning("Unknown entity requested", entity=entity)
            return result
        try:
            count: int = svc.sync(company_name=company_name, full=False)  # type: ignore[attr-defined]
            result.synced[entity] = count
            logger.info(
                "Event-triggered sync complete", entity=entity, company=company_name, records=count
            )
        except Exception as exc:
            result.errors[entity] = str(exc)
            logger.error(
                "Event-triggered sync failed", entity=entity, company=company_name, error=str(exc)
            )
        return result

    def sync(self, company_name: str, *, full: bool = False) -> SyncResult:
        """Run sync for all configured entities in dependency order."""
        result = SyncResult()
        mode = "full" if full else "incremental"
        logger.info("Sync started", company=company_name, mode=mode)

        for entity in self._order:
            svc = self._services.get(entity)
            if svc is None:
                continue
            try:
                count: int = svc.sync(company_name=company_name, full=full)  # type: ignore[attr-defined]
                result.synced[entity] = count
                logger.info("Entity synced", entity=entity, company=company_name, records=count)
            except Exception as exc:
                result.errors[entity] = str(exc)
                logger.error(
                    "Entity sync failed",
                    entity=entity,
                    company=company_name,
                    error=str(exc),
                )

        logger.info(
            "Sync finished",
            company=company_name,
            mode=mode,
            total=result.total_records,
            errors=len(result.errors),
        )
        return result
