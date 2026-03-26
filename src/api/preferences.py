"""Preference quiz API endpoints — persisted to SQLite via SQLAlchemy."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.db.tables import UserTable
from src.models.user import UserPreferences

router = APIRouter()


@router.post("/{user_id}", response_model=UserPreferences)
async def save_preferences(
    user_id: str,
    preferences: UserPreferences,
    session: AsyncSession = Depends(get_session),
):
    """Save or update a user's preferences in the database."""
    row = await session.get(UserTable, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row.preferences = preferences.model_dump_json()
    await session.commit()
    return preferences


@router.get("/{user_id}", response_model=UserPreferences)
async def get_preferences(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a user's stored preferences from the database."""
    row = await session.get(UserTable, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    if not row.preferences:
        raise HTTPException(status_code=404, detail="Preferences not found for this user")
    import json
    return UserPreferences(**json.loads(row.preferences))
