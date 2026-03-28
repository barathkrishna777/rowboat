"""Database connection and session management."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

logger = logging.getLogger(__name__)


def _build_url() -> str:
    """Resolve and validate the database URL, logging diagnostics."""
    url = settings.async_database_url

    # Log the scheme and host (never the password) for debugging
    try:
        parsed = urlparse(url)
        logger.info(
            f"[DB] URL scheme={parsed.scheme!r} host={parsed.hostname!r} "
            f"port={parsed.port} dbname={parsed.path!r}"
        )
    except Exception:
        logger.error(f"[DB] Could not parse URL — first 30 chars: {url[:30]!r}…")

    # Ensure the data directory exists for SQLite
    if "sqlite" in url:
        db_path = url.split("///")[-1] if "///" in url else ""
        if db_path:
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    return url


_url = _build_url()
try:
    engine = create_async_engine(_url, echo=False)
except Exception as exc:
    # Fall back to in-memory SQLite so the app can at least start and
    # serve /health — the real DB error will surface later.
    logger.error(f"[DB] Failed to create engine with URL: {exc}")
    logger.error(f"[DB] Raw DATABASE_URL value (first 60 chars): {settings.database_url[:60]!r}")
    logger.warning("[DB] Falling back to in-memory SQLite — DB operations will not persist!")
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """Get a database session."""
    async with async_session() as session:
        yield session


async def init_db():
    """Create all tables."""
    from src.db.tables import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close the database engine."""
    await engine.dispose()
