"""Calendar API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from src.tools.google_calendar import exchange_code_for_token, get_auth_url

router = APIRouter()


@router.get("/auth-url")
async def get_calendar_auth_url():
    """Get the Google OAuth authorization URL for calendar access."""
    try:
        url = get_auth_url()
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def calendar_oauth_callback(code: str, state: str = ""):
    """Handle the Google OAuth callback."""
    try:
        token_data = exchange_code_for_token(code)
        # In production, store this token for the user
        return {"status": "success", "message": "Calendar connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AvailabilityRequest(BaseModel):
    user_ids: list[str]
    start_date: str = Field(description="ISO format date, e.g. 2026-04-01")
    end_date: str = Field(description="ISO format date, e.g. 2026-04-07")
    min_duration_hours: float = 2.0


@router.post("/availability")
async def find_availability(request: AvailabilityRequest):
    """Find group availability across connected calendars."""
    # For MVP, return simulated availability
    from datetime import datetime, timedelta

    slots = []
    current = datetime.fromisoformat(request.start_date)
    end = datetime.fromisoformat(request.end_date)

    while current <= end:
        if current.weekday() >= 5:  # Weekend
            slots.append({
                "start": current.replace(hour=12).isoformat(),
                "end": current.replace(hour=22).isoformat(),
                "available_user_ids": request.user_ids,
            })
        else:  # Weekday evening
            slots.append({
                "start": current.replace(hour=18).isoformat(),
                "end": current.replace(hour=22).isoformat(),
                "available_user_ids": request.user_ids,
            })
        current += timedelta(days=1)

    return {"slots": slots, "total": len(slots)}
