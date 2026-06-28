from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class BaseRepository[T](ABC):
    """Abstract base for all entity repositories.

    Each concrete repository takes a SQLAlchemy Session in __init__ and
    implements upsert_batch() using INSERT … ON CONFLICT DO UPDATE.
    """

    @abstractmethod
    def upsert_batch(self, company_name: str, records: Sequence[T]) -> int:
        """Upsert *records* for *company_name*.

        Returns the number of rows processed.  An empty *records* sequence
        must return 0 without touching the database.
        """
        ...
