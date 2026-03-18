"""Tests for the database persistence layer."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.tables import Base
from src.db import crud
from src.models.user import UserPreferences, DietaryRestriction, BudgetTier
from src.models.feedback import PostEventFeedback


@pytest_asyncio.fixture
async def db_session():
    """Create a test database in memory."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


class TestUserCRUD:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        user = await crud.create_user(db_session, "Alice", "alice@example.com")
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        assert user.id  # Should have a UUID

    @pytest.mark.asyncio
    async def test_get_user(self, db_session):
        user = await crud.create_user(db_session, "Bob", "bob@example.com")
        fetched = await crud.get_user(db_session, user.id)
        assert fetched is not None
        assert fetched.name == "Bob"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, db_session):
        fetched = await crud.get_user(db_session, "nonexistent")
        assert fetched is None

    @pytest.mark.asyncio
    async def test_update_preferences(self, db_session):
        user = await crud.create_user(db_session, "Charlie", "charlie@example.com")
        prefs = UserPreferences(
            cuisine_preferences=["italian", "japanese"],
            dietary_restrictions=[DietaryRestriction.VEGETARIAN],
            budget_max=BudgetTier.MEDIUM,
        )
        result = await crud.update_user_preferences(db_session, user.id, prefs)
        assert result is True

        fetched = await crud.get_user(db_session, user.id)
        assert fetched.preferences is not None
        assert "italian" in fetched.preferences.cuisine_preferences
        assert DietaryRestriction.VEGETARIAN in fetched.preferences.dietary_restrictions

    @pytest.mark.asyncio
    async def test_update_calendar_token(self, db_session):
        user = await crud.create_user(db_session, "Dana", "dana@example.com")
        token = {"token": "abc123", "refresh_token": "xyz789"}
        result = await crud.update_user_calendar_token(db_session, user.id, token)
        assert result is True

        fetched = await crud.get_user(db_session, user.id)
        assert fetched.google_calendar_token is not None
        assert fetched.google_calendar_token["token"] == "abc123"


class TestGroupCRUD:
    @pytest.mark.asyncio
    async def test_create_group(self, db_session):
        user = await crud.create_user(db_session, "Eve", "eve@example.com")
        group = await crud.create_group(db_session, "Test Group", user.id)
        assert group.name == "Test Group"
        assert user.id in group.member_ids

    @pytest.mark.asyncio
    async def test_add_member(self, db_session):
        user1 = await crud.create_user(db_session, "Frank", "frank@example.com")
        user2 = await crud.create_user(db_session, "Grace", "grace@example.com")
        group = await crud.create_group(db_session, "Duo", user1.id)

        result = await crud.add_group_member(db_session, group.id, user2.id)
        assert result is True

        fetched = await crud.get_group(db_session, group.id)
        assert len(fetched.member_ids) == 2
        assert user2.id in fetched.member_ids

    @pytest.mark.asyncio
    async def test_get_group_members(self, db_session):
        user1 = await crud.create_user(db_session, "Hank", "hank@example.com")
        user2 = await crud.create_user(db_session, "Ivy", "ivy@example.com")
        group = await crud.create_group(db_session, "Pair", user1.id)
        await crud.add_group_member(db_session, group.id, user2.id)

        members = await crud.get_group_members(db_session, group.id)
        assert len(members) == 2
        names = {m.name for m in members}
        assert "Hank" in names
        assert "Ivy" in names


class TestFeedbackCRUD:
    @pytest.mark.asyncio
    async def test_save_and_get_feedback(self, db_session):
        user = await crud.create_user(db_session, "Jack", "jack@example.com")
        group = await crud.create_group(db_session, "Solo", user.id)

        # Create an event first
        from src.models.event import Itinerary
        itinerary = Itinerary(id="event-1", group_id=group.id)
        await crud.save_event(db_session, group.id, itinerary)

        feedback = PostEventFeedback(
            feedback_id="fb-1",
            user_id=user.id,
            event_id="event-1",
            overall_rating=4,
            venue_ratings={"v1": 5, "v2": 3},
            would_repeat=True,
            free_text="Great time!",
        )
        await crud.save_feedback(db_session, feedback)

        feedbacks = await crud.get_event_feedback(db_session, "event-1")
        assert len(feedbacks) == 1
        assert feedbacks[0].overall_rating == 4
        assert feedbacks[0].would_repeat is True
