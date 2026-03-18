"""FastAPI application for the Group Outing Planner."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import groups, plans, preferences

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


@app.get("/")
async def root():
    return {"name": "Outing Planner API", "version": "0.1.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
