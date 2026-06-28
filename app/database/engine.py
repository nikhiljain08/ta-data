from __future__ import annotations

from sqlalchemy import Engine, create_engine

from app.config.settings import DatabaseSettings


def build_engine(db: DatabaseSettings, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy Engine from database settings.

    pool_pre_ping=True keeps connections healthy across Tally's long idle
    periods between scheduled sync runs.
    """
    return create_engine(
        db.url,
        pool_size=db.pool_size,
        max_overflow=db.max_overflow,
        pool_pre_ping=True,
        echo=echo,
    )
