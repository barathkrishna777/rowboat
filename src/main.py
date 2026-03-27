"""FastAPI application for Rowboat."""

from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, calendar, friends, groups, hangouts, plans, preferences, profile
from src.config import settings

# Enable logging so we can see search/API diagnostics in Railway
logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rowboat API",
    description="AI-powered group outing coordination platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(plans.router, prefix="/api/plans", tags=["plans"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(friends.router, prefix="/api/friends", tags=["friends"])
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(hangouts.router, prefix="/api/hangouts", tags=["hangouts"])


async def _warmup_gemini():
    """Send a tiny Gemini request on startup to warm up DNS/TLS/model.

    This runs in the background so it doesn't block the health check.
    """
    api_key = settings.google_api_key or settings.gemini_api_key
    if not api_key:
        return
    model = settings.primary_model.split(":")[-1]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": "Say hi"}]}],
        "generationConfig": {"maxOutputTokens": 5},
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=body, timeout=30.0)
            logger.info(f"[Warmup] Gemini ping: {resp.status_code}")
    except Exception as e:
        logger.warning(f"[Warmup] Gemini ping failed: {e}")


@app.on_event("startup")
async def startup():
    """Initialize DB and warm up Gemini on startup."""
    from src.db.database import init_db
    await init_db()
    asyncio.create_task(_warmup_gemini())


@app.get("/")
async def root():
    return {"name": "Rowboat API", "version": "0.1.0", "status": "running"}


def _key_set(value: str) -> bool:
    """True only if the value is a real key — not empty and not a placeholder."""
    return bool(value) and not value.startswith("your_")


@app.get("/api/config/status")
async def config_status():
    """Return which optional integrations are configured (no secrets exposed)."""
    gemini = _key_set(settings.gemini_api_key) or _key_set(settings.google_api_key)
    anthropic = _key_set(settings.anthropic_api_key)
    return {
        "gemini": gemini,
        "anthropic": anthropic,
        "ai_ready": anthropic or gemini,  # True if ANY LLM provider is configured
        "yelp": _key_set(settings.yelp_api_key),
        "eventbrite": _key_set(settings.eventbrite_api_key),
        "ticketmaster": _key_set(settings.ticketmaster_api_key),
        "google_places": gemini,  # Places API uses Google key; LLM fallback prefers Claude
        "google_calendar": _key_set(settings.google_client_id) and _key_set(settings.google_client_secret),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
