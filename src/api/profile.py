"""Profile and availability API — authenticated, user-scoped."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import UserTable
from src.models.user import User, UserAvailability, UserProfile

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
