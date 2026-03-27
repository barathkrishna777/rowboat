"""Preference quiz API endpoints — persisted to SQLite via SQLAlchemy."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import UserTable
from src.models.user import User, UserPreferences

router = APIRouter()


def _assert_owner(current_user: User, user_id: str) -> None:
    """Raise 403 if the authenticated user doesn't match the path user_id."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to act on behalf of another user",
        )


@router.post("/{user_id}", response_model=UserPreferences)
async def save_preferences(
    user_id: str,
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Save or update a user's preferences in the database."""
    _assert_owner(current_user, user_id)
    row = await session.get(UserTable, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row.preferences = preferences.model_dump_json()
    await session.commit()
    return preferences


@router.get("/{user_id}", response_model=UserPreferences)
async def get_preferences(
    user_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a user's stored preferences from the database."""
    _assert_owner(current_user, user_id)
    row = await session.get(UserTable, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    if not row.preferences:
        raise HTTPException(status_code=404, detail="Preferences not found for this user")
    return UserPreferences(**json.loads(row.preferences))
