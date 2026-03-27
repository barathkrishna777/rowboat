"""Tests for hangout cards, swipe idempotency, matching, and group creation."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.auth import _create_token
from src.db.tables import Base, UserTable

_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_session():
    async with _session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def app():
    from src.db.database import get_session
    from src.main import app as _app
    _app.dependency_overrides[get_session] = _override_get_session
    yield _app
    _app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _make_user(name: str, email: str, prefs_json: str | None = None):
    uid = str(uuid.uuid4())
    async with _session_factory() as session:
        session.add(UserTable(
            id=uid, name=name, email=email,
            auth_provider="email", preferences=prefs_json,
        ))
        await session.commit()
    return uid, _create_token(uid)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Hangout CRUD ───────────────────────────────────────────────────────


class TestHangoutCRUD:
    @pytest.mark.asyncio
    async def test_create_and_list(self, client):
        uid, token = await _make_user("Alice", "alice@test.com")
        resp = await client.post(
            "/api/hangouts",
            json={"title": "Brunch at Cafe", "tags": ["brunch", "coffee"]},
            headers=_bearer(token),
        )
        assert resp.status_code == 201
        hangout = resp.json()
        assert hangout["title"] == "Brunch at Cafe"
        assert hangout["tags"] == ["brunch", "coffee"]

        resp = await client.get("/api/hangouts", headers=_bearer(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client):
        resp = await client.post("/api/hangouts", json={"title": "No auth"})
        assert resp.status_code == 401


# ── Swipe idempotency ─────────────────────────────────────────────────


class TestSwipeIdempotency:
    @pytest.mark.asyncio
    async def test_swipe_creates_and_updates(self, client):
        uid, token = await _make_user("Alice", "alice@test.com")
        # Create a hangout
        resp = await client.post(
            "/api/hangouts",
            json={"title": "Test Hangout"},
            headers=_bearer(token),
        )
        hangout_id = resp.json()["id"]

        # First swipe: interested
        resp = await client.post(
            f"/api/hangouts/{hangout_id}/swipe",
            json={"action": "interested"},
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "interested"

        # Second swipe: change to pass (idempotent update)
        resp = await client.post(
            f"/api/hangouts/{hangout_id}/swipe",
            json={"action": "pass"},
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "pass"

        # Third swipe: back to interested (still idempotent)
        resp = await client.post(
            f"/api/hangouts/{hangout_id}/swipe",
            json={"action": "interested"},
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "interested"

    @pytest.mark.asyncio
    async def test_swipe_nonexistent_hangout_404(self, client):
        uid, token = await _make_user("Bob", "bob@test.com")
        resp = await client.post(
            "/api/hangouts/fake-id/swipe",
            json={"action": "interested"},
            headers=_bearer(token),
        )
        assert resp.status_code == 404


# ── Feed ───────────────────────────────────────────────────────────────


class TestFeed:
    @pytest.mark.asyncio
    async def test_feed_excludes_swiped(self, client):
        uid, token = await _make_user("Alice", "alice@test.com")

        # Create two hangouts
        r1 = await client.post(
            "/api/hangouts", json={"title": "H1"}, headers=_bearer(token),
        )
        r2 = await client.post(
            "/api/hangouts", json={"title": "H2"}, headers=_bearer(token),
        )
        h1_id = r1.json()["id"]

        # Swipe on H1
        await client.post(
            f"/api/hangouts/{h1_id}/swipe",
            json={"action": "pass"},
            headers=_bearer(token),
        )

        # Feed should only show H2
        resp = await client.get("/api/hangouts/feed/me", headers=_bearer(token))
        assert resp.status_code == 200
        titles = [h["title"] for h in resp.json()]
        assert "H2" in titles
        assert "H1" not in titles


# ── Matching + Group Creation ──────────────────────────────────────────


class TestMatchingAndGroupCreation:
    @pytest.mark.asyncio
    async def test_generate_matches_and_create_group(self, client):
        # Create two users with overlapping preferences
        import json
        prefs = json.dumps({
            "cuisine_preferences": ["italian", "japanese"],
            "activity_preferences": ["bowling"],
        })
        uid_a, token_a = await _make_user("Alice", "alice@test.com", prefs)
        uid_b, token_b = await _make_user("Bob", "bob@test.com", prefs)

        # Alice creates a hangout
        resp = await client.post(
            "/api/hangouts",
            json={"title": "Bowling Night"},
            headers=_bearer(token_a),
        )
        hangout_id = resp.json()["id"]

        # Both swipe interested
        await client.post(
            f"/api/hangouts/{hangout_id}/swipe",
            json={"action": "interested"},
            headers=_bearer(token_a),
        )
        await client.post(
            f"/api/hangouts/{hangout_id}/swipe",
            json={"action": "interested"},
            headers=_bearer(token_b),
        )

        # Generate matches
        resp = await client.post(
            f"/api/hangouts/{hangout_id}/generate-matches",
            headers=_bearer(token_a),
        )
        assert resp.status_code == 200
        matches = resp.json()
        assert len(matches) == 1
        match = matches[0]
        assert uid_a in match["member_user_ids"]
        assert uid_b in match["member_user_ids"]
        assert match["score"] > 0

        # Create group from match
        match_id = match["id"]
        resp = await client.post(
            f"/api/hangouts/matches/{match_id}/create-group",
            headers=_bearer(token_a),
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["group_id"] is not None
        assert result["status"] == "accepted"

        # Idempotent: calling again returns same group_id
        resp2 = await client.post(
            f"/api/hangouts/matches/{match_id}/create-group",
            headers=_bearer(token_a),
        )
        assert resp2.json()["group_id"] == result["group_id"]

    @pytest.mark.asyncio
    async def test_generate_matches_needs_two_users(self, client):
        uid, token = await _make_user("Alone", "alone@test.com")
        resp = await client.post(
            "/api/hangouts",
            json={"title": "Solo Hangout"},
            headers=_bearer(token),
        )
        hangout_id = resp.json()["id"]
        await client.post(
            f"/api/hangouts/{hangout_id}/swipe",
            json={"action": "interested"},
            headers=_bearer(token),
        )
        resp = await client.post(
            f"/api/hangouts/{hangout_id}/generate-matches",
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        assert resp.json() == []
