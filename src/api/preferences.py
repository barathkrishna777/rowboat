"""Preference quiz API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.models.user import UserPreferences

router = APIRouter()

# In-memory store for MVP
_preferences: dict[str, UserPreferences] = {}


@router.post("/{user_id}", response_model=UserPreferences)
async def save_preferences(user_id: str, preferences: UserPreferences):
    """Save or update a user's preferences."""
    _preferences[user_id] = preferences
    return preferences


@router.get("/{user_id}", response_model=UserPreferences)
async def get_preferences(user_id: str):
    """Get a user's stored preferences."""
    if user_id not in _preferences:
        raise HTTPException(status_code=404, detail="Preferences not found for this user")
    return _preferences[user_id]
