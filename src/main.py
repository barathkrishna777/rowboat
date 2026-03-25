"""FastAPI application for the Group Outing Planner."""

from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import calendar, groups, plans, preferences
from src.config import settings

# Enable logging so we can see search/API diagnostics in Railway
logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Outing Planner API",
    description="AI-powered group outing coordination agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router, prefix="/api/plans", tags=["plans"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])


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
    return {"name": "Outing Planner API", "version": "0.1.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
