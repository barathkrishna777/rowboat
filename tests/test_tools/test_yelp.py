"""Tests for the Yelp API tool."""

import pytest
import respx
import httpx

from src.config import settings
from src.tools.yelp import search_yelp, get_yelp_details, YELP_API_BASE
from src.models.event import VenueSource, VenueCategory
from src.models.user import BudgetTier


@pytest.fixture(autouse=True)
def _set_yelp_key(monkeypatch):
    """Ensure tests run with a mock API key so guards don't short-circuit."""
    monkeypatch.setattr(settings, "yelp_api_key", "test-key-123")


@respx.mock
@pytest.mark.asyncio
async def test_search_yelp_basic(mock_yelp_response):
    """Test basic Yelp search returns parsed venues."""
    respx.get(f"{YELP_API_BASE}/businesses/search").mock(
        return_value=httpx.Response(200, json=mock_yelp_response)
    )

    venues = await search_yelp(location="Pittsburgh, PA", term="Italian")

    assert len(venues) == 1
    venue = venues[0]
    assert venue.name == "Test Italian Place"
    assert venue.source == VenueSource.YELP
    assert venue.source_id == "test-biz-1"
    assert venue.price_tier == BudgetTier.MEDIUM
    assert venue.rating == 4.5
    assert venue.category == VenueCategory.RESTAURANT


@respx.mock
@pytest.mark.asyncio
async def test_search_yelp_empty():
    """Test Yelp search with no results."""
    respx.get(f"{YELP_API_BASE}/businesses/search").mock(
        return_value=httpx.Response(200, json={"businesses": [], "total": 0})
    )

    venues = await search_yelp(location="Nowhere", term="xyz")
    assert venues == []


@respx.mock
@pytest.mark.asyncio
async def test_search_yelp_with_filters(mock_yelp_response):
    """Test Yelp search passes filters correctly."""
    route = respx.get(f"{YELP_API_BASE}/businesses/search").mock(
        return_value=httpx.Response(200, json=mock_yelp_response)
    )

    await search_yelp(
        location="Pittsburgh",
        term="dinner",
        categories="restaurants",
        price="1,2",
        radius=5000,
        limit=5,
    )

    assert route.called
    request = route.calls[0].request
    assert "categories=restaurants" in str(request.url)
    assert "price=1%2C2" in str(request.url) or "price=1,2" in str(request.url)


@respx.mock
@pytest.mark.asyncio
async def test_get_yelp_details():
    """Test getting details for a single business."""
    detail_response = {
        "id": "test-biz-1",
        "name": "Test Place",
        "categories": [{"alias": "restaurants", "title": "Italian"}],
        "location": {"display_address": ["123 St"], "city": "Pittsburgh"},
        "coordinates": {"latitude": 40.44, "longitude": -79.95},
        "rating": 4.0,
        "review_count": 100,
        "hours": [{"open": [{"day": 0, "start": "1100", "end": "2200"}]}],
    }
    respx.get(f"{YELP_API_BASE}/businesses/test-biz-1").mock(
        return_value=httpx.Response(200, json=detail_response)
    )

    venue = await get_yelp_details("test-biz-1")
    assert venue is not None
    assert venue.name == "Test Place"
    assert venue.hours is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_yelp_details_not_found():
    """Test 404 returns None."""
    respx.get(f"{YELP_API_BASE}/businesses/nonexistent").mock(
        return_value=httpx.Response(404)
    )

    venue = await get_yelp_details("nonexistent")
    assert venue is None
