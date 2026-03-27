"""Tests for config status endpoint and _key_set() helper.

These are fast unit tests — no live API calls, no DB required.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import _key_set


# ── _key_set() unit tests ──────────────────────────────────────────────


def test_key_set_empty_string_is_false():
    assert _key_set("") is False


def test_key_set_placeholder_your_prefix_is_false():
    assert _key_set("your_gemini_api_key_here") is False
    assert _key_set("your_key") is False
    assert _key_set("your_secret") is False


def test_key_set_real_gemini_key_is_true():
    assert _key_set("AIzaSyABCDEFGHIJKLMNOP") is True


def test_key_set_real_anthropic_key_is_true():
    assert _key_set("sk-ant-api03-xxxxxxxxx") is True


def test_key_set_any_non_placeholder_string_is_true():
    assert _key_set("some-real-key-value") is True


# ── /api/config/status endpoint tests ────────────────────────────────


@pytest_asyncio.fixture
async def client():
    """AsyncClient pointing at the live FastAPI app."""
    from src.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_config_status_returns_200(client):
    resp = await client.get("/api/config/status")
    assert resp.status_code == 200


async def test_config_status_has_required_fields(client):
    data = (await client.get("/api/config/status")).json()
    required = {"gemini", "anthropic", "ai_ready", "yelp", "eventbrite",
                "ticketmaster", "google_places", "google_calendar"}
    assert required.issubset(data.keys()), f"Missing fields: {required - data.keys()}"


async def test_config_status_all_values_are_bool(client):
    data = (await client.get("/api/config/status")).json()
    for key, val in data.items():
        assert isinstance(val, bool), f"Field '{key}' is {type(val).__name__}, expected bool"


async def test_config_status_ai_ready_is_true_when_either_key_set(client):
    """ai_ready should be True when at least one LLM key is configured."""
    from src.config import settings
    has_any_key = bool(settings.anthropic_api_key) or bool(
        settings.gemini_api_key or settings.google_api_key
    )
    data = (await client.get("/api/config/status")).json()
    assert data["ai_ready"] == has_any_key


async def test_config_status_ai_ready_consistent_with_individual_flags(client):
    """ai_ready must equal (gemini OR anthropic)."""
    data = (await client.get("/api/config/status")).json()
    assert data["ai_ready"] == (data["gemini"] or data["anthropic"])
