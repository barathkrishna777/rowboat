"""Shared test fixtures."""

import json
from pathlib import Path

import pytest

from src.models.event import Venue
from src.models.user import UserPreferences


@pytest.fixture
def sample_venues() -> list[Venue]:
    """Load sample venues from JSON."""
    data_path = Path(__file__).parent.parent / "data" / "sample_venues.json"
    with open(data_path) as f:
        raw = json.load(f)
    return [Venue(**v) for v in raw]


@pytest.fixture
def sample_preferences() -> list[dict]:
    """Load sample user preferences from JSON."""
    data_path = Path(__file__).parent.parent / "data" / "sample_preferences.json"
    with open(data_path) as f:
        return json.load(f)


@pytest.fixture
def mock_yelp_response() -> dict:
    """Mock Yelp API search response."""
    return {
        "businesses": [
            {
                "id": "test-biz-1",
                "name": "Test Italian Place",
                "categories": [{"alias": "restaurants", "title": "Italian"}],
                "location": {
                    "display_address": ["123 Test St", "Pittsburgh, PA 15213"],
                    "city": "Pittsburgh",
                },
                "coordinates": {"latitude": 40.4444, "longitude": -79.9532},
                "price": "$$",
                "rating": 4.5,
                "review_count": 200,
                "phone": "+14125551234",
                "url": "https://yelp.com/test-biz-1",
                "image_url": "https://example.com/image.jpg",
            }
        ],
        "total": 1,
    }
