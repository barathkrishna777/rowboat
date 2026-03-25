"""Context-manager session helper for use outside FastAPI dependency injection."""

from __future__ import annotations

from contextlib import asynccontextmanager

from src.db.database import async_session


@asynccontextmanager
async def get_session():
    """Async context manager for a DB session."""
    async with async_session() as session:
        yield session
