"""Calendar API endpoints — OAuth flow, availability, and booking."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from src.db.session import get_session
from src.db.crud import get_user, update_user_calendar_token
from src.tools.google_calendar import (
    create_calendar_event,
    exchange_code_for_token,
    find_group_availability,
    get_auth_url,
    get_free_busy,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── OAuth ─────────────────────────────────────────────────────────────


@router.get("/auth-url")
async def get_calendar_auth_url(user_id: str = ""):
    """Get the Google OAuth authorization URL for calendar access.

    Pass user_id so the callback knows which user to store the token for.
    """
    try:
        url = get_auth_url(state=user_id)
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def calendar_oauth_callback(code: str, state: str = ""):
    """Handle the Google OAuth callback — exchange code for token and store it."""
    try:
        token_data = exchange_code_for_token(code)
    except Exception as e:
        logger.error(f"[Calendar] OAuth token exchange failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    user_id = state
    if user_id:
        async with get_session() as session:
            saved = await update_user_calendar_token(session, user_id, token_data)
            if saved:
                logger.info(f"[Calendar] Token saved for user {user_id}")
            else:
                logger.warning(f"[Calendar] User {user_id} not found — token not saved")

    # Redirect back to the Streamlit UI with a success indicator
    import os
    ui_base = os.environ.get("UI_BASE_URL", "http://localhost:8501")
    return RedirectResponse(f"{ui_base}?calendar_connected=true&user_id={user_id}")


@router.get("/status/{user_id}")
async def calendar_status(user_id: str):
    """Check if a user has connected their Google Calendar."""
    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user:
            return {"connected": False}
        return {"connected": user.google_calendar_token is not None}


# ── Availability ──────────────────────────────────────────────────────


class AvailabilityRequest(BaseModel):
    user_ids: list[str]
    start_date: str = Field(description="ISO format date, e.g. 2026-04-01")
    end_date: str = Field(description="ISO format date, e.g. 2026-04-07")
    min_duration_hours: float = 2.0
    preferred_start_hour: int = 17
    preferred_end_hour: int = 23


@router.post("/availability")
async def find_availability(request: AvailabilityRequest):
    """Find group availability using real Google Calendar data when available.

    For users with connected calendars, queries their real free/busy data.
    For users without, assumes they're always free (no busy periods).
    """
    start = datetime.fromisoformat(request.start_date)
    end = datetime.fromisoformat(request.end_date)

    busy_periods_by_user: dict[str, list[dict]] = {}
    connected_users = []
    simulated_users = []

    async with get_session() as session:
        for user_id in request.user_ids:
            user = await get_user(session, user_id)
            if user and user.google_calendar_token:
                # Real calendar data
                try:
                    busy = await get_free_busy(user.google_calendar_token, start, end)
                    busy_periods_by_user[user_id] = busy
                    connected_users.append(user.name)
                    logger.info(f"[Calendar] Got {len(busy)} busy periods for {user.name}")
                except Exception as e:
                    logger.warning(f"[Calendar] Failed to get calendar for {user.name}: {e}")
                    busy_periods_by_user[user_id] = []
                    simulated_users.append(user.name if user else user_id)
            else:
                # No calendar connected — assume always free
                busy_periods_by_user[user_id] = []
                simulated_users.append(user.name if user else user_id)

    slots = find_group_availability(
        busy_periods_by_user=busy_periods_by_user,
        date_range_start=start,
        date_range_end=end,
        min_duration_minutes=int(request.min_duration_hours * 60),
        preferred_hours=(request.preferred_start_hour, request.preferred_end_hour),
    )

    slot_dicts = []
    for s in slots:
        slot_dicts.append({
            "date": s.start.strftime("%Y-%m-%d"),
            "day_name": s.start.strftime("%A"),
            "start_time": s.start.strftime("%I:%M %p"),
            "end_time": s.end.strftime("%I:%M %p"),
            "start_iso": s.start.isoformat(),
            "end_iso": s.end.isoformat(),
            "duration_hours": (s.end - s.start).total_seconds() / 3600,
            "is_weekend": s.start.weekday() >= 5,
        })

    return {
        "slots": slot_dicts,
        "total": len(slot_dicts),
        "connected_users": connected_users,
        "simulated_users": simulated_users,
    }


# ── Booking ───────────────────────────────────────────────────────────


class BookingRequest(BaseModel):
    organizer_user_id: str
    group_id: str
    venue_name: str
    venue_address: str = ""
    start_time: str = Field(description="ISO datetime")
    end_time: str = Field(description="ISO datetime")
    attendee_emails: list[str] = Field(default_factory=list)
    description: str = ""


@router.post("/book")
async def book_event(request: BookingRequest):
    """Book an outing — create a Google Calendar event and send invites.

    Requires the organizer to have connected their Google Calendar.
    """
    async with get_session() as session:
        organizer = await get_user(session, request.organizer_user_id)
        if not organizer:
            raise HTTPException(status_code=404, detail="Organizer not found")
        if not organizer.google_calendar_token:
            raise HTTPException(
                status_code=400,
                detail="Organizer must connect their Google Calendar first",
            )

    start = datetime.fromisoformat(request.start_time)
    end = datetime.fromisoformat(request.end_time)

    description = request.description or f"Group outing at {request.venue_name}, planned by Rowboat."

    try:
        event_result = await create_calendar_event(
            token_data=organizer.google_calendar_token,
            summary=f"Group Outing: {request.venue_name}",
            location=request.venue_address,
            description=description,
            start_time=start,
            end_time=end,
            attendee_emails=request.attendee_emails,
        )
        logger.info(f"[Booking] Created calendar event: {event_result.get('event_id')}")
        return {
            "status": "booked",
            "event_id": event_result.get("event_id"),
            "calendar_link": event_result.get("html_link"),
            "message": f"Event created! Calendar invites sent to {len(request.attendee_emails)} attendees.",
        }
    except Exception as e:
        logger.error(f"[Booking] Failed to create calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create calendar event: {e}")
