from __future__ import annotations

import httpx

from src.config import settings
from src.models.event import Venue, VenueCategory, VenueSource

TICKETMASTER_API_BASE = "https://app.ticketmaster.com/discovery/v2"

GENRE_TO_CATEGORY = {
    "Music": VenueCategory.CONCERT,
    "Sports": VenueCategory.SPORTS,
    "Arts & Theatre": VenueCategory.THEATER,
    "Film": VenueCategory.ACTIVITY,
    "Miscellaneous": VenueCategory.OTHER,
}


def _ticketmaster_to_venue(event: dict) -> Venue:
    """Convert a Ticketmaster event to our Venue model."""
    venues = event.get("_embedded", {}).get("venues", [{}])
    venue_data = venues[0] if venues else {}
    location = venue_data.get("location", {})
    classifications = event.get("classifications", [{}])
    genre = classifications[0].get("segment", {}).get("name", "") if classifications else ""
    images = event.get("images", [])
    price_ranges = event.get("priceRanges", [])

    address_parts = []
    if venue_data.get("address", {}).get("line1"):
        address_parts.append(venue_data["address"]["line1"])
    if venue_data.get("city", {}).get("name"):
        address_parts.append(venue_data["city"]["name"])
    if venue_data.get("state", {}).get("stateCode"):
        address_parts.append(venue_data["state"]["stateCode"])

    return Venue(
        id=f"ticketmaster-{event['id']}",
        source=VenueSource.TICKETMASTER,
        source_id=event["id"],
        name=event.get("name", "Unknown Event"),
        category=GENRE_TO_CATEGORY.get(genre, VenueCategory.OTHER),
        categories=[genre] if genre else [],
        address=", ".join(address_parts),
        city=venue_data.get("city", {}).get("name", ""),
        lat=float(location["latitude"]) if location.get("latitude") else None,
        lng=float(location["longitude"]) if location.get("longitude") else None,
        url=event.get("url"),
        image_url=images[0].get("url") if images else None,
        raw_details={
            "date": event.get("dates", {}).get("start", {}).get("localDate"),
            "time": event.get("dates", {}).get("start", {}).get("localTime"),
            "venue_name": venue_data.get("name"),
            "price_min": price_ranges[0].get("min") if price_ranges else None,
            "price_max": price_ranges[0].get("max") if price_ranges else None,
            "genre": genre,
            "sub_genre": (
                classifications[0].get("genre", {}).get("name") if classifications else None
            ),
        },
    )


async def search_ticketmaster(
    location: str | None = None,
    keyword: str | None = None,
    classification: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    city: str | None = None,
    limit: int = 10,
) -> list[Venue]:
    """Search Ticketmaster Discovery API for events.

    Args:
        location: GeoPoint (lat,lng) or use city parameter.
        keyword: Search keyword.
        classification: Genre/segment name (e.g., "Music", "Sports").
        start_date: Start date in ISO format (YYYY-MM-DDTHH:mm:ssZ).
        end_date: End date in ISO format.
        city: City name to search.
        limit: Max results.

    Returns:
        List of Venue objects.
    """
    params: dict = {
        "apikey": settings.ticketmaster_api_key,
        "size": min(limit, 50),
        "sort": "relevance,asc",
    }
    if keyword:
        params["keyword"] = keyword
    if classification:
        params["classificationName"] = classification
    if start_date:
        params["startDateTime"] = start_date
    if end_date:
        params["endDateTime"] = end_date
    if city:
        params["city"] = city
    elif not location:
        params["city"] = settings.default_location.split(",")[0].strip()
    if location:
        params["latlong"] = location

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TICKETMASTER_API_BASE}/events.json",
            params=params,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    events = data.get("_embedded", {}).get("events", [])
    return [_ticketmaster_to_venue(event) for event in events]
