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
    """Create all tables and seed default hangouts if the table is empty."""
    from src.db.tables import Base, HangoutTable
    from sqlalchemy import select, func
    import json
    import uuid

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default hangouts so new users see cards immediately
    async with async_session() as session:
        count = (await session.execute(select(func.count()).select_from(HangoutTable))).scalar_one()
        if count == 0:
            logger.info("[DB] Seeding default hangouts...")
            defaults = [
                ("Saturday Bowling Night", "Hit the lanes together — shoes included!", ["bowling", "casual", "evening"], "Pittsburgh, PA"),
                ("Escape Room Challenge", "60 minutes to break out — who's got the brains?", ["escape room", "puzzle", "teamwork"], "Pittsburgh, PA"),
                ("Trivia Night at a Bar", "Test your general knowledge over drinks.", ["trivia", "bar", "drinks"], "Pittsburgh, PA"),
                ("Hiking at North Park", "Easy 3-mile trail, great views, great company.", ["hiking", "outdoors", "nature"], "Pittsburgh, PA"),
                ("Board Game Café", "Pick from 500+ games and snacks. No experience needed.", ["board games", "café", "chill"], "Pittsburgh, PA"),
                ("Comedy Show Downtown", "Catch a live stand-up set and laugh the night away.", ["comedy", "live show", "nightlife"], "Pittsburgh, PA"),
                ("Sunday Brunch Run", "Casual run followed by a big brunch together.", ["running", "brunch", "active"], "Pittsburgh, PA"),
                ("Karaoke Night", "Belt your favorite songs — no talent required.", ["karaoke", "singing", "nightlife"], "Pittsburgh, PA"),
                ("Mini Golf Outing", "Classic outdoor mini golf, perfect for all skill levels.", ["mini golf", "outdoor", "fun"], "Pittsburgh, PA"),
                ("Museum Visit", "Explore the Carnegie Museum of Art or Natural History.", ["museum", "culture", "daytime"], "Pittsburgh, PA"),
            ]
            for title, desc, tags, location in defaults:
                session.add(HangoutTable(
                    id=str(uuid.uuid4()),
                    title=title,
                    description=desc,
                    tags=json.dumps(tags),
                    location_area=location,
                    source="template",
                ))
            await session.commit()
            logger.info(f"[DB] Seeded {len(defaults)} default hangouts.")


async def close_db():
    """Close the database engine."""
    await engine.dispose()
