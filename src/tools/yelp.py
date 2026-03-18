from __future__ import annotations

import uuid

import httpx

from src.config import settings
from src.models.event import Venue, VenueCategory, VenueSource
from src.models.user import BudgetTier

YELP_API_BASE = "https://api.yelp.com/v3"

# Map Yelp price levels to our tiers
PRICE_MAP = {1: BudgetTier.LOW, 2: BudgetTier.MEDIUM, 3: BudgetTier.HIGH, 4: BudgetTier.LUXURY}

# Map Yelp categories to our categories
CATEGORY_MAP = {
    "restaurants": VenueCategory.RESTAURANT,
    "food": VenueCategory.RESTAURANT,
    "bars": VenueCategory.BAR,
    "nightlife": VenueCategory.BAR,
    "coffee": VenueCategory.CAFE,
    "arts": VenueCategory.ACTIVITY,
    "active": VenueCategory.ACTIVITY,
    "bowling": VenueCategory.ACTIVITY,
    "escapegames": VenueCategory.ACTIVITY,
    "eventservices": VenueCategory.OTHER,
}


def _parse_category(categories: list[dict]) -> VenueCategory:
    """Map Yelp category aliases to our VenueCategory."""
    for cat in categories:
        alias = cat.get("alias", "")
        for key, venue_cat in CATEGORY_MAP.items():
            if key in alias:
                return venue_cat
    return VenueCategory.OTHER


def _yelp_to_venue(biz: dict) -> Venue:
    """Convert a Yelp business API response to our Venue model."""
    location = biz.get("location", {})
    coords = biz.get("coordinates", {})
    categories = biz.get("categories", [])

    return Venue(
        id=f"yelp-{biz['id']}",
        source=VenueSource.YELP,
        source_id=biz["id"],
        name=biz["name"],
        category=_parse_category(categories),
        categories=[c.get("title", "") for c in categories],
        address=", ".join(location.get("display_address", [])),
        city=location.get("city", ""),
        lat=coords.get("latitude"),
        lng=coords.get("longitude"),
        price_tier=PRICE_MAP.get(len(biz.get("price", ""))) if biz.get("price") else None,
        rating=biz.get("rating"),
        review_count=biz.get("review_count"),
        phone=biz.get("phone"),
        url=biz.get("url"),
        image_url=biz.get("image_url"),
    )


async def search_yelp(
    location: str | None = None,
    term: str | None = None,
    categories: str | None = None,
    price: str | None = None,
    radius: int | None = None,
    limit: int = 10,
    sort_by: str = "best_match",
) -> list[Venue]:
    """Search Yelp Fusion API for businesses.

    Args:
        location: Location to search (e.g., "Pittsburgh, PA"). Defaults to config.
        term: Search term (e.g., "Italian dinner").
        categories: Comma-separated Yelp categories (e.g., "restaurants,bars").
        price: Comma-separated price levels 1-4 (e.g., "1,2").
        radius: Search radius in meters (max 40000).
        limit: Max results (1-50).
        sort_by: One of "best_match", "rating", "review_count", "distance".

    Returns:
        List of Venue objects.
    """
    params: dict = {
        "location": location or settings.default_location,
        "limit": min(limit, 50),
        "sort_by": sort_by,
    }
    if term:
        params["term"] = term
    if categories:
        params["categories"] = categories
    if price:
        params["price"] = price
    if radius:
        params["radius"] = min(radius, 40000)

    headers = {"Authorization": f"Bearer {settings.yelp_api_key}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{YELP_API_BASE}/businesses/search",
            headers=headers,
            params=params,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    return [_yelp_to_venue(biz) for biz in data.get("businesses", [])]


async def get_yelp_details(business_id: str) -> Venue | None:
    """Get detailed info for a single Yelp business."""
    headers = {"Authorization": f"Bearer {settings.yelp_api_key}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{YELP_API_BASE}/businesses/{business_id}",
            headers=headers,
            timeout=15.0,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        biz = resp.json()

    venue = _yelp_to_venue(biz)
    # Add extra details available in the detail endpoint
    if biz.get("hours"):
        hours_data = biz["hours"][0].get("open", []) if biz["hours"] else []
        venue.hours = {
            entry.get("day", ""): f"{entry.get('start', '')}-{entry.get('end', '')}"
            for entry in hours_data
        }
    return venue


async def get_yelp_reviews(business_id: str) -> list[dict]:
    """Get up to 3 reviews for a Yelp business (free tier limit)."""
    headers = {"Authorization": f"Bearer {settings.yelp_api_key}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{YELP_API_BASE}/businesses/{business_id}/reviews",
            headers=headers,
            params={"limit": 3, "sort_by": "yelp_sort"},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {"text": r.get("text", ""), "rating": r.get("rating"), "time": r.get("time_created")}
        for r in data.get("reviews", [])
    ]
