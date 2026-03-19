"""FastAPI application for the Group Outing Planner."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import calendar, groups, plans, preferences

# Enable logging so we can see search/API diagnostics in Railway
logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")

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


@app.get("/")
async def root():
    return {"name": "Outing Planner API", "version": "0.1.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
