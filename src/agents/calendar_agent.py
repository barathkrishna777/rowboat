"""Calendar Agent — manages group availability and calendar invites."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from src.config import settings
from src.models.event import TimeSlot
from src.tools.google_calendar import (
    create_calendar_event,
    find_group_availability,
    get_free_busy,
)


class AvailabilityResult(BaseModel):
    """Structured output from the Calendar Agent."""

    available_slots: list[TimeSlot] = Field(default_factory=list)
    total_slots_found: int = 0
    best_slot: TimeSlot | None = None
    summary: str = ""


class EventCreationResult(BaseModel):
    """Result of creating a calendar event."""

    event_id: str = ""
    html_link: str = ""
    success: bool = False
    message: str = ""


@dataclass
class CalendarDeps:
    """Dependencies for the calendar agent."""

    user_tokens: dict[str, dict] = field(default_factory=dict)  # user_id -> token_data
    user_emails: dict[str, str] = field(default_factory=dict)  # user_id -> email


calendar_agent = Agent(
    settings.primary_model,
    result_type=AvailabilityResult,
    deps_type=CalendarDeps,
    system_prompt="""\
You are a calendar coordination specialist for a group outing planner.
Your job is to find time slots when all group members are available.

When finding availability:
- Check each user's Google Calendar for busy periods
- Find overlapping free time across all members
- Prefer evening/weekend slots for social outings
- Ensure at least 2-hour windows for a proper outing
- Present the best options clearly with day and time

Use the tools to query calendars and find group overlap.
""",
)


@calendar_agent.tool
async def check_user_availability(
    ctx: RunContext[CalendarDeps],
    user_id: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """Check a single user's busy periods from Google Calendar.

    Args:
        user_id: The user's ID.
        start_date: Start date in ISO format (e.g., "2026-04-01").
        end_date: End date in ISO format (e.g., "2026-04-07").
    """
    token_data = ctx.deps.user_tokens.get(user_id)
    if not token_data:
        return [{"error": f"No calendar connected for user {user_id}"}]

    time_min = datetime.fromisoformat(start_date)
    time_max = datetime.fromisoformat(end_date)

    busy_periods = await get_free_busy(token_data, time_min, time_max)
    return busy_periods


@calendar_agent.tool
async def find_group_free_slots(
    ctx: RunContext[CalendarDeps],
    start_date: str,
    end_date: str,
    min_duration_hours: float = 2.0,
    preferred_start_hour: int = 17,
    preferred_end_hour: int = 23,
) -> list[dict]:
    """Find time slots when all group members are available.

    Args:
        start_date: Start of search range in ISO format (e.g., "2026-04-01").
        end_date: End of search range in ISO format (e.g., "2026-04-07").
        min_duration_hours: Minimum slot duration in hours (default 2).
        preferred_start_hour: Earliest preferred hour (24h, default 17 = 5 PM).
        preferred_end_hour: Latest preferred hour (24h, default 23 = 11 PM).
    """
    time_min = datetime.fromisoformat(start_date)
    time_max = datetime.fromisoformat(end_date)

    # Collect busy periods for all connected users
    busy_by_user: dict[str, list[dict]] = {}
    for user_id, token_data in ctx.deps.user_tokens.items():
        try:
            busy = await get_free_busy(token_data, time_min, time_max)
            busy_by_user[user_id] = busy
        except Exception as e:
            busy_by_user[user_id] = []  # Assume free if calendar fails

    slots = find_group_availability(
        busy_by_user,
        time_min,
        time_max,
        min_duration_minutes=int(min_duration_hours * 60),
        preferred_hours=(preferred_start_hour, preferred_end_hour),
    )

    return [s.model_dump(mode="json") for s in slots]


@calendar_agent.tool
async def send_calendar_invite(
    ctx: RunContext[CalendarDeps],
    organizer_user_id: str,
    event_title: str,
    event_location: str,
    event_description: str,
    start_time: str,
    end_time: str,
) -> dict:
    """Create a Google Calendar event and send invites to all group members.

    Args:
        organizer_user_id: User ID of the event organizer.
        event_title: Title of the event.
        event_location: Location/address of the event.
        event_description: Description of the event.
        start_time: Start time in ISO format (e.g., "2026-04-05T18:00:00").
        end_time: End time in ISO format (e.g., "2026-04-05T21:00:00").
    """
    token_data = ctx.deps.user_tokens.get(organizer_user_id)
    if not token_data:
        return {"success": False, "message": "Organizer has no calendar connected"}

    attendee_emails = [
        email for uid, email in ctx.deps.user_emails.items() if uid != organizer_user_id
    ]

    try:
        result = await create_calendar_event(
            token_data=token_data,
            summary=event_title,
            location=event_location,
            description=event_description,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            attendee_emails=attendee_emails,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def find_availability(
    user_tokens: dict[str, dict],
    start_date: str,
    end_date: str,
) -> AvailabilityResult:
    """Convenience function to find group availability."""
    deps = CalendarDeps(user_tokens=user_tokens)
    prompt = (
        f"Find available time slots for all {len(user_tokens)} group members "
        f"between {start_date} and {end_date}. "
        "Look for evening and weekend slots at least 2 hours long."
    )
    result = await calendar_agent.run(prompt, deps=deps)
    return result.data
