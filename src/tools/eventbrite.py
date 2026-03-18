from __future__ import annotations

import httpx

from src.config import settings
from src.models.event import Venue, VenueCategory, VenueSource

EVENTBRITE_API_BASE = "https://www.eventbriteapi.com/v3"


def _eventbrite_to_venue(event: dict) -> Venue:
    """Convert an Eventbrite event response to our Venue model."""
    venue_data = event.get("venue", {})
    address = venue_data.get("address", {})

    return Venue(
        id=f"eventbrite-{event['id']}",
        source=VenueSource.EVENTBRITE,
        source_id=event["id"],
        name=event.get("name", {}).get("text", "Unknown Event"),
        category=VenueCategory.ACTIVITY,
        categories=[cat.get("name", "") for cat in event.get("categories", [])],
        address=address.get("localized_address_display", ""),
        city=address.get("city", ""),
        lat=float(address["latitude"]) if address.get("latitude") else None,
        lng=float(address["longitude"]) if address.get("longitude") else None,
        url=event.get("url"),
        image_url=event.get("logo", {}).get("url") if event.get("logo") else None,
        raw_details={
            "description": event.get("description", {}).get("text", ""),
            "start": event.get("start", {}).get("local"),
            "end": event.get("end", {}).get("local"),
            "is_free": event.get("is_free", False),
            "capacity": event.get("capacity"),
        },
    )


async def search_eventbrite(
    location: str | None = None,
    query: str | None = None,
    categories: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    price: str | None = None,
    limit: int = 10,
) -> list[Venue]:
    """Search Eventbrite for events.

    Args:
        location: Location string (e.g., "Pittsburgh").
        query: Search keyword.
        categories: Eventbrite category IDs.
        start_date: ISO format start date filter.
        end_date: ISO format end date filter.
        price: "free" or "paid".
        limit: Max results.

    Returns:
        List of Venue objects.
    """
    params: dict = {"expand": "venue,category"}
    if query:
        params["q"] = query
    if location:
        params["location.address"] = location
        params["location.within"] = "25mi"
    else:
        params["location.address"] = settings.default_location
        params["location.within"] = "25mi"
    if categories:
        params["categories"] = categories
    if start_date:
        params["start_date.range_start"] = start_date
    if end_date:
        params["start_date.range_end"] = end_date
    if price == "free":
        params["price"] = "free"

    headers = {"Authorization": f"Bearer {settings.eventbrite_api_key}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{EVENTBRITE_API_BASE}/events/search",
            headers=headers,
            params=params,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    events = data.get("events", [])[:limit]
    return [_eventbrite_to_venue(event) for event in events]
