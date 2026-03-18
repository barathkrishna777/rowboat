"""Google Calendar API tool — OAuth, free/busy, and event creation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from src.config import settings
from src.models.event import TimeSlot

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

REDIRECT_URI = "http://localhost:8000/api/calendar/callback"


def get_oauth_flow() -> Flow:
    """Create a Google OAuth2 flow for Calendar access."""
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    return flow


def get_auth_url() -> str:
    """Get the Google OAuth2 authorization URL."""
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_token(authorization_code: str) -> dict:
    """Exchange an authorization code for OAuth tokens."""
    flow = get_oauth_flow()
    flow.fetch_token(code=authorization_code)
    credentials = flow.credentials
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes),
    }


def _build_service(token_data: dict):
    """Build a Google Calendar API service from stored token data."""
    credentials = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id", settings.google_client_id),
        client_secret=token_data.get("client_secret", settings.google_client_secret),
        scopes=token_data.get("scopes", SCOPES),
    )
    return build("calendar", "v3", credentials=credentials)


async def get_free_busy(
    token_data: dict,
    time_min: datetime,
    time_max: datetime,
    calendar_id: str = "primary",
) -> list[dict]:
    """Get free/busy information for a user's calendar.

    Args:
        token_data: The user's stored OAuth token data.
        time_min: Start of the time range to check.
        time_max: End of the time range to check.
        calendar_id: Calendar ID (default "primary").

    Returns:
        List of busy periods as {start, end} dicts.
    """
    service = _build_service(token_data)
    body = {
        "timeMin": time_min.isoformat() + "Z",
        "timeMax": time_max.isoformat() + "Z",
        "items": [{"id": calendar_id}],
    }
    result = service.freebusy().query(body=body).execute()
    busy_periods = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
    return busy_periods


def find_group_availability(
    busy_periods_by_user: dict[str, list[dict]],
    date_range_start: datetime,
    date_range_end: datetime,
    min_duration_minutes: int = 120,
    preferred_hours: tuple[int, int] = (17, 23),
) -> list[TimeSlot]:
    """Find time slots where all users are available.

    Args:
        busy_periods_by_user: Mapping of user_id -> list of busy periods.
        date_range_start: Start of the search range.
        date_range_end: End of the search range.
        min_duration_minutes: Minimum slot duration in minutes.
        preferred_hours: Preferred time window (start_hour, end_hour) in 24h format.

    Returns:
        List of TimeSlot objects where all users are free.
    """
    user_ids = list(busy_periods_by_user.keys())
    available_slots: list[TimeSlot] = []

    current_date = date_range_start.date()
    end_date = date_range_end.date()

    while current_date <= end_date:
        # Check the preferred time window for this day
        window_start = datetime.combine(current_date, datetime.min.time().replace(hour=preferred_hours[0]))
        window_end = datetime.combine(current_date, datetime.min.time().replace(hour=preferred_hours[1]))

        # Check if all users are free during this window
        all_free = True
        effective_start = window_start
        effective_end = window_end

        for user_id, busy_list in busy_periods_by_user.items():
            for busy in busy_list:
                busy_start = datetime.fromisoformat(busy["start"].replace("Z", ""))
                busy_end = datetime.fromisoformat(busy["end"].replace("Z", ""))

                # Check overlap with our window
                if busy_start < window_end and busy_end > window_start:
                    # Busy covers the entire window
                    if busy_start <= effective_start and busy_end >= effective_end:
                        all_free = False
                        break
                    # Narrow the window
                    elif busy_start <= effective_start and busy_end < effective_end:
                        effective_start = max(effective_start, busy_end)
                    elif busy_start > effective_start and busy_end >= effective_end:
                        effective_end = min(effective_end, busy_start)
                    elif busy_start > effective_start and busy_end < effective_end:
                        # Busy period in the middle — take the larger chunk
                        before = (busy_start - effective_start).total_seconds() / 60
                        after = (effective_end - busy_end).total_seconds() / 60
                        if before >= after and before >= min_duration_minutes:
                            effective_end = busy_start
                        elif after >= min_duration_minutes:
                            effective_start = busy_end
                        else:
                            all_free = False
                            break

        duration = (effective_end - effective_start).total_seconds() / 60
        if all_free and duration >= min_duration_minutes:
            available_slots.append(
                TimeSlot(
                    start=effective_start,
                    end=effective_end,
                    available_user_ids=user_ids,
                )
            )

        current_date += timedelta(days=1)

    return available_slots


async def create_calendar_event(
    token_data: dict,
    summary: str,
    location: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    attendee_emails: list[str],
) -> dict:
    """Create a Google Calendar event and send invites.

    Args:
        token_data: The organizer's OAuth token data.
        summary: Event title.
        location: Event location/address.
        description: Event description.
        start_time: Event start time.
        end_time: Event end time.
        attendee_emails: List of attendee email addresses to invite.

    Returns:
        The created event data from Google Calendar API.
    """
    service = _build_service(token_data)

    event_body = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "America/New_York"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "America/New_York"},
        "attendees": [{"email": email} for email in attendee_emails],
        "reminders": {"useDefault": True},
    }

    event = service.events().insert(
        calendarId="primary",
        body=event_body,
        sendUpdates="all",
    ).execute()

    return {
        "event_id": event.get("id"),
        "html_link": event.get("htmlLink"),
        "status": event.get("status"),
    }
