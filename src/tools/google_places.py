"""Google Places API (New) — venue search using your Gemini/Google API key.

Falls back to a Gemini-powered venue lookup if the Places API is not enabled.
"""

from __future__ import annotations

import json
import logging
import uuid

import httpx

from src.config import settings
from src.models.event import Venue, VenueCategory, VenueSource
from src.models.user import BudgetTier

logger = logging.getLogger(__name__)

PLACES_API_BASE = "https://places.googleapis.com/v1/places"

# Map Google place types to our categories
TYPE_MAP = {
    "restaurant": VenueCategory.RESTAURANT,
    "food": VenueCategory.RESTAURANT,
    "cafe": VenueCategory.CAFE,
    "bar": VenueCategory.BAR,
    "night_club": VenueCategory.BAR,
    "bowling_alley": VenueCategory.ACTIVITY,
    "amusement_center": VenueCategory.ACTIVITY,
    "movie_theater": VenueCategory.ACTIVITY,
    "museum": VenueCategory.ACTIVITY,
    "performing_arts_theater": VenueCategory.THEATER,
    "event_venue": VenueCategory.ACTIVITY,
}

PRICE_MAP = {
    "PRICE_LEVEL_FREE": BudgetTier.LOW,
    "PRICE_LEVEL_INEXPENSIVE": BudgetTier.LOW,
    "PRICE_LEVEL_MODERATE": BudgetTier.MEDIUM,
    "PRICE_LEVEL_EXPENSIVE": BudgetTier.HIGH,
    "PRICE_LEVEL_VERY_EXPENSIVE": BudgetTier.LUXURY,
}


def _parse_category(types: list[str]) -> VenueCategory:
    for t in types:
        if t in TYPE_MAP:
            return TYPE_MAP[t]
    return VenueCategory.OTHER


def _place_to_venue(place: dict) -> Venue:
    """Convert a Google Places API response to our Venue model."""
    location = place.get("location", {})
    display_name = place.get("displayName", {})
    address = place.get("formattedAddress", "")
    types = place.get("types", [])
    price_level = place.get("priceLevel", "")

    return Venue(
        id=f"google-{place.get('id', uuid.uuid4().hex[:12])}",
        source=VenueSource.GOOGLE,
        source_id=place.get("id", ""),
        name=display_name.get("text", "Unknown"),
        category=_parse_category(types),
        categories=[t.replace("_", " ").title() for t in types[:5]],
        address=address,
        city="",
        lat=location.get("latitude"),
        lng=location.get("longitude"),
        price_tier=PRICE_MAP.get(price_level),
        rating=place.get("rating"),
        review_count=place.get("userRatingCount"),
        url=place.get("googleMapsUri"),
        image_url=None,
    )


async def _search_places_api(query: str, location: str, limit: int) -> list[Venue]:
    """Try the Google Places (New) API."""
    api_key = settings.google_api_key or settings.gemini_api_key
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.types,places.rating,"
            "places.userRatingCount,places.priceLevel,"
            "places.googleMapsUri,places.primaryType"
        ),
    }
    body = {
        "textQuery": f"{query} in {location}",
        "maxResultCount": min(limit, 20),
        "languageCode": "en",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PLACES_API_BASE}:searchText",
            headers=headers,
            json=body,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
    return [_place_to_venue(p) for p in data.get("places", [])]


async def _search_via_gemini(query: str, location: str, limit: int) -> list[Venue]:
    """Use Gemini to generate real venue recommendations when Places API is unavailable.

    Uses the google-genai SDK (same auth path as PydanticAI) instead of raw
    httpx, which hangs on Railway due to API key / auth differences.
    """
    from google import genai

    # Prefer GEMINI_API_KEY — on Railway, GOOGLE_API_KEY may be stale
    api_key = settings.gemini_api_key or settings.google_api_key
    model = settings.primary_model.split(":")[-1]  # e.g., "gemini-2.5-flash"

    prompt = f"""Find {limit} real, currently operating venues for: "{query}" in {location}.

Return ONLY a valid JSON array. Each object must have these exact fields:
- "name": string (real business name)
- "category": one of "restaurant", "bar", "cafe", "activity", "concert", "theater", "outdoor", "other"
- "categories": list of strings describing the venue
- "address": full street address
- "city": city name
- "rating": number 1-5 or null
- "price_tier": one of "$", "$$", "$$$", "$$$$" or null

Return the JSON array only, no markdown, no explanation."""

    client = genai.Client(api_key=api_key)
    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=genai.types.GenerateContentConfig(temperature=0.3),
    )

    text = response.text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # remove first line
        text = text.rsplit("```", 1)[0]  # remove last fence
    text = text.strip()

    venues_data = json.loads(text)

    budget_map = {"$": BudgetTier.LOW, "$$": BudgetTier.MEDIUM, "$$$": BudgetTier.HIGH, "$$$$": BudgetTier.LUXURY}
    cat_map = {c.value: c for c in VenueCategory}

    venues = []
    for v in venues_data:
        venues.append(Venue(
            id=f"gemini-{uuid.uuid4().hex[:8]}",
            source=VenueSource.GOOGLE,
            source_id="",
            name=v.get("name", "Unknown"),
            category=cat_map.get(v.get("category", ""), VenueCategory.OTHER),
            categories=v.get("categories", []),
            address=v.get("address", ""),
            city=v.get("city", location.split(",")[0].strip()),
            price_tier=budget_map.get(v.get("price_tier")),
            rating=v.get("rating"),
        ))
    return venues


async def search_google_places(
    query: str,
    location: str | None = None,
    limit: int = 10,
) -> list[Venue]:
    """Search for venues using Google Places API, with Gemini fallback.

    Args:
        query: Search text (e.g., "Italian restaurant with arcade").
        location: Location bias (e.g., "Pittsburgh, PA").
        limit: Max results (1-20).

    Returns:
        List of Venue objects.
    """
    api_key = settings.google_api_key or settings.gemini_api_key
    if not api_key:
        return []

    loc = location or settings.default_location

    # Try Places API first, fall back to Gemini
    try:
        venues = await _search_places_api(query, loc, limit)
        logger.info(f"[GooglePlaces] Places API returned {len(venues)} venues")
        return venues
    except Exception as e:
        logger.info(f"[GooglePlaces] Places API failed ({type(e).__name__}: {e}), trying Gemini fallback")

    try:
        venues = await _search_via_gemini(query, loc, limit)
        logger.info(f"[GooglePlaces] Gemini fallback returned {len(venues)} venues")
        return venues
    except Exception as e:
        logger.warning(f"[GooglePlaces] Gemini fallback also failed: {type(e).__name__}: {e}")
        return []
