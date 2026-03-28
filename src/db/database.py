"""Database connection and session management."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

# Ensure the data directory exists when using SQLite so the engine can
# create the database file without raising FileNotFoundError.
_url = settings.async_database_url
if "sqlite" in _url:
    _db_path = _url.split("///")[-1] if "///" in _url else ""
    if _db_path:
        os.makedirs(os.path.dirname(_db_path) or ".", exist_ok=True)

engine = create_async_engine(_url, echo=False)
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
