"""Tests for JWT authorization on user-scoped routes (Phase 1 — authz-api)."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.auth import _create_token
from src.db.tables import Base, UserTable

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    """Create tables before each test and drop after."""
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
    """Return a fresh FastAPI app with the DB dependency overridden."""
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


@pytest_asyncio.fixture
async def user_a():
    """Create user A in the test DB and return (user_id, jwt_token)."""
    uid = str(uuid.uuid4())
    async with _session_factory() as session:
        session.add(UserTable(
            id=uid, name="Alice", email="alice@test.com",
            auth_provider="email",
        ))
        await session.commit()
    return uid, _create_token(uid)


@pytest_asyncio.fixture
async def user_b():
    """Create user B in the test DB and return (user_id, jwt_token)."""
    uid = str(uuid.uuid4())
    async with _session_factory() as session:
        session.add(UserTable(
            id=uid, name="Bob", email="bob@test.com",
            auth_provider="email",
        ))
        await session.commit()
    return uid, _create_token(uid)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Friends routes — auth required
# ---------------------------------------------------------------------------


class TestFriendsAuthz:
    """Verify friends routes reject missing/wrong tokens."""

    @pytest.mark.asyncio
    async def test_get_friends_no_token_returns_401(self, client, user_a):
        uid, _ = user_a
        resp = await client.get(f"/api/friends/{uid}/friends")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_friends_wrong_user_returns_403(self, client, user_a, user_b):
        uid_a, _ = user_a
        _, token_b = user_b
        resp = await client.get(f"/api/friends/{uid_a}/friends", headers=_bearer(token_b))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_friends_own_token_returns_200(self, client, user_a):
        uid, token = user_a
        resp = await client.get(f"/api/friends/{uid}/friends", headers=_bearer(token))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_send_request_no_token_returns_401(self, client, user_a, user_b):
        uid_a, _ = user_a
        resp = await client.post(
            f"/api/friends/{uid_a}/request",
            json={"to_email": "bob@test.com"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_send_request_wrong_user_returns_403(self, client, user_a, user_b):
        uid_a, _ = user_a
        _, token_b = user_b
        resp = await client.post(
            f"/api/friends/{uid_a}/request",
            json={"to_email": "bob@test.com"},
            headers=_bearer(token_b),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_send_request_own_token_succeeds(self, client, user_a, user_b):
        uid_a, token_a = user_a
        resp = await client.post(
            f"/api/friends/{uid_a}/request",
            json={"to_email": "bob@test.com"},
            headers=_bearer(token_a),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_incoming_requests_wrong_user_returns_403(self, client, user_a, user_b):
        uid_a, _ = user_a
        _, token_b = user_b
        resp = await client.get(
            f"/api/friends/{uid_a}/requests/incoming",
            headers=_bearer(token_b),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_outgoing_requests_wrong_user_returns_403(self, client, user_a, user_b):
        uid_a, _ = user_a
        _, token_b = user_b
        resp = await client.get(
            f"/api/friends/{uid_a}/requests/outgoing",
            headers=_bearer(token_b),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Preferences routes — auth required
# ---------------------------------------------------------------------------


class TestPreferencesAuthz:
    """Verify preferences routes reject missing/wrong tokens."""

    @pytest.mark.asyncio
    async def test_get_prefs_no_token_returns_401(self, client, user_a):
        uid, _ = user_a
        resp = await client.get(f"/api/preferences/{uid}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_prefs_wrong_user_returns_403(self, client, user_a, user_b):
        uid_a, _ = user_a
        _, token_b = user_b
        resp = await client.get(f"/api/preferences/{uid_a}", headers=_bearer(token_b))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_save_prefs_no_token_returns_401(self, client, user_a):
        uid, _ = user_a
        resp = await client.post(f"/api/preferences/{uid}", json={})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_save_prefs_wrong_user_returns_403(self, client, user_a, user_b):
        uid_a, _ = user_a
        _, token_b = user_b
        resp = await client.post(
            f"/api/preferences/{uid_a}",
            json={},
            headers=_bearer(token_b),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_save_prefs_own_token_succeeds(self, client, user_a):
        uid, token = user_a
        resp = await client.post(
            f"/api/preferences/{uid}",
            json={"cuisine_preferences": ["italian"]},
            headers=_bearer(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_prefs_own_token_after_save(self, client, user_a):
        uid, token = user_a
        # Save first
        await client.post(
            f"/api/preferences/{uid}",
            json={"cuisine_preferences": ["thai"]},
            headers=_bearer(token),
        )
        resp = await client.get(f"/api/preferences/{uid}", headers=_bearer(token))
        assert resp.status_code == 200
        assert "thai" in resp.json()["cuisine_preferences"]
