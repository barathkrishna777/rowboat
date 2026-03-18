"""CRUD operations for the database."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import EventTable, FeedbackTable, GroupMemberTable, GroupTable, UserTable
from src.models.event import Itinerary
from src.models.feedback import PostEventFeedback
from src.models.user import Group, User, UserPreferences


# ── Users ──────────────────────────────────────────────────────────────


async def create_user(session: AsyncSession, name: str, email: str) -> User:
    user_id = str(uuid.uuid4())
    row = UserTable(id=user_id, name=name, email=email)
    session.add(row)
    await session.commit()
    return User(id=user_id, name=name, email=email)


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    row = await session.get(UserTable, user_id)
    if not row:
        return None
    prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
    token = json.loads(row.google_calendar_token) if row.google_calendar_token else None
    return User(id=row.id, name=row.name, email=row.email, preferences=prefs, google_calendar_token=token)


async def update_user_preferences(session: AsyncSession, user_id: str, prefs: UserPreferences) -> bool:
    row = await session.get(UserTable, user_id)
    if not row:
        return False
    row.preferences = prefs.model_dump_json()
    await session.commit()
    return True


async def update_user_calendar_token(session: AsyncSession, user_id: str, token_data: dict) -> bool:
    row = await session.get(UserTable, user_id)
    if not row:
        return False
    row.google_calendar_token = json.dumps(token_data)
    await session.commit()
    return True


# ── Groups ─────────────────────────────────────────────────────────────


async def create_group(session: AsyncSession, name: str, creator_id: str) -> Group:
    group_id = str(uuid.uuid4())
    row = GroupTable(id=group_id, name=name, created_by=creator_id)
    session.add(row)
    member = GroupMemberTable(group_id=group_id, user_id=creator_id)
    session.add(member)
    await session.commit()
    return Group(id=group_id, name=name, member_ids=[creator_id], created_by=creator_id)


async def add_group_member(session: AsyncSession, group_id: str, user_id: str) -> bool:
    group = await session.get(GroupTable, group_id)
    if not group:
        return False
    member = GroupMemberTable(group_id=group_id, user_id=user_id)
    session.add(member)
    await session.commit()
    return True


async def get_group(session: AsyncSession, group_id: str) -> Group | None:
    group = await session.get(GroupTable, group_id)
    if not group:
        return None
    result = await session.execute(
        select(GroupMemberTable.user_id).where(GroupMemberTable.group_id == group_id)
    )
    member_ids = [r[0] for r in result.all()]
    return Group(id=group.id, name=group.name, member_ids=member_ids, created_by=group.created_by)


async def get_group_members(session: AsyncSession, group_id: str) -> list[User]:
    result = await session.execute(
        select(GroupMemberTable.user_id).where(GroupMemberTable.group_id == group_id)
    )
    member_ids = [r[0] for r in result.all()]
    users = []
    for uid in member_ids:
        user = await get_user(session, uid)
        if user:
            users.append(user)
    return users


# ── Events ─────────────────────────────────────────────────────────────


async def save_event(session: AsyncSession, group_id: str, itinerary: Itinerary) -> str:
    row = EventTable(
        id=itinerary.id,
        group_id=group_id,
        itinerary=itinerary.model_dump_json(),
        status=itinerary.status,
    )
    session.add(row)
    await session.commit()
    return itinerary.id


async def get_event(session: AsyncSession, event_id: str) -> Itinerary | None:
    row = await session.get(EventTable, event_id)
    if not row or not row.itinerary:
        return None
    return Itinerary(**json.loads(row.itinerary))


# ── Feedback ───────────────────────────────────────────────────────────


async def save_feedback(session: AsyncSession, feedback: PostEventFeedback) -> str:
    row = FeedbackTable(
        id=feedback.feedback_id,
        user_id=feedback.user_id,
        event_id=feedback.event_id,
        overall_rating=feedback.overall_rating,
        venue_ratings=json.dumps(feedback.venue_ratings),
        would_repeat=1 if feedback.would_repeat else 0,
        free_text=feedback.free_text,
    )
    session.add(row)
    await session.commit()
    return feedback.feedback_id


async def get_event_feedback(session: AsyncSession, event_id: str) -> list[PostEventFeedback]:
    result = await session.execute(
        select(FeedbackTable).where(FeedbackTable.event_id == event_id)
    )
    rows = result.scalars().all()
    feedbacks = []
    for row in rows:
        feedbacks.append(
            PostEventFeedback(
                feedback_id=row.id,
                user_id=row.user_id,
                event_id=row.event_id,
                overall_rating=row.overall_rating,
                venue_ratings=json.loads(row.venue_ratings) if row.venue_ratings else {},
                would_repeat=bool(row.would_repeat),
                free_text=row.free_text,
            )
        )
    return feedbacks
