"""Profile and availability API — authenticated, user-scoped."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import UserTable
from src.models.user import User, UserAvailability, UserPreferences, UserProfile

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the current user's profile."""
    row = await session.get(UserTable, current_user.id)
    if not row or not row.profile:
        return UserProfile()
    return UserProfile(**json.loads(row.profile))


@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    profile: UserProfile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create or update the current user's profile."""
    row = await session.get(UserTable, current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row.profile = profile.model_dump_json()
    await session.commit()
    return profile


@router.post("/me/generate-preferences", response_model=UserPreferences)
async def generate_preferences_from_bio(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Extract structured UserPreferences from the user's profile bio + tags.

    Calls the Preference Agent (LLM) to parse free-text into cuisines,
    activities, dietary restrictions, budget, etc. and persists the result.
    """
    from src.agents.preference_agent import run_preference_quiz

    row = await session.get(UserTable, current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    profile_data = json.loads(row.profile) if row.profile else {}
    bio = profile_data.get("bio", "")
    tags = profile_data.get("interest_tags", [])

    if not bio and not tags:
        raise HTTPException(
            status_code=400,
            detail="Please add a bio or interest tags to your profile first.",
        )

    text_parts = []
    if bio:
        text_parts.append(bio)
    if tags:
        text_parts.append(f"Interests: {', '.join(tags)}")
    combined_text = "\n".join(text_parts)

    try:
        result = await run_preference_quiz(user_id=current_user.id, answers_text=combined_text)
        preferences = result.preferences
    except Exception as e:
        logger.error("Preference agent failed for user %s: %s", current_user.id, e)
        raise HTTPException(status_code=502, detail="Failed to generate preferences. Try again later.")

    row.preferences = preferences.model_dump_json()
    await session.commit()
    return preferences


@router.get("/me/availability", response_model=UserAvailability)
async def get_my_availability(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the current user's structured availability."""
    row = await session.get(UserTable, current_user.id)
    if not row or not row.availability:
        return UserAvailability()
    return UserAvailability(**json.loads(row.availability))


@router.put("/me/availability", response_model=UserAvailability)
async def update_my_availability(
    availability: UserAvailability,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create or update the current user's availability."""
    row = await session.get(UserTable, current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row.availability = availability.model_dump_json()
    await session.commit()
    return availability
