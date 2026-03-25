"""CRUD operations for the database."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import EventTable, FeedbackTable, FriendshipTable, GroupMemberTable, GroupTable, UserTable
from src.models.event import Itinerary
from src.models.feedback import PostEventFeedback
from src.models.user import Friendship, FriendshipStatus, Group, User, UserPreferences


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


# ── Friendships ────────────────────────────────────────────────────────


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(UserTable).where(UserTable.email == email))
    row = result.scalar_one_or_none()
    if not row:
        return None
    prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
    token = json.loads(row.google_calendar_token) if row.google_calendar_token else None
    return User(id=row.id, name=row.name, email=row.email, preferences=prefs, google_calendar_token=token)


async def send_friend_request(session: AsyncSession, requester_id: str, addressee_id: str) -> Friendship | None:
    if requester_id == addressee_id:
        return None

    # Check for existing friendship in either direction
    result = await session.execute(
        select(FriendshipTable).where(
            ((FriendshipTable.requester_id == requester_id) & (FriendshipTable.addressee_id == addressee_id))
            | ((FriendshipTable.requester_id == addressee_id) & (FriendshipTable.addressee_id == requester_id))
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return Friendship(
            id=existing.id,
            requester_id=existing.requester_id,
            addressee_id=existing.addressee_id,
            status=FriendshipStatus(existing.status),
        )

    row = FriendshipTable(requester_id=requester_id, addressee_id=addressee_id, status="pending")
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return Friendship(id=row.id, requester_id=requester_id, addressee_id=addressee_id, status=FriendshipStatus.PENDING)


async def respond_to_friend_request(session: AsyncSession, friendship_id: int, accept: bool) -> bool:
    row = await session.get(FriendshipTable, friendship_id)
    if not row or row.status != "pending":
        return False
    row.status = "accepted" if accept else "declined"
    await session.commit()
    return True


async def get_friends(session: AsyncSession, user_id: str) -> list[User]:
    """Return all accepted friends for a user."""
    result = await session.execute(
        select(FriendshipTable).where(
            ((FriendshipTable.requester_id == user_id) | (FriendshipTable.addressee_id == user_id))
            & (FriendshipTable.status == "accepted")
        )
    )
    rows = result.scalars().all()
    friends = []
    for row in rows:
        friend_id = row.addressee_id if row.requester_id == user_id else row.requester_id
        user = await get_user(session, friend_id)
        if user:
            friends.append(user)
    return friends


async def get_pending_requests(session: AsyncSession, user_id: str) -> list[Friendship]:
    """Return pending friend requests where user is the addressee."""
    result = await session.execute(
        select(FriendshipTable).where(
            (FriendshipTable.addressee_id == user_id) & (FriendshipTable.status == "pending")
        )
    )
    rows = result.scalars().all()
    friendships = []
    for row in rows:
        requester = await get_user(session, row.requester_id)
        friendships.append(Friendship(
            id=row.id,
            requester_id=row.requester_id,
            addressee_id=row.addressee_id,
            status=FriendshipStatus.PENDING,
            requester=requester,
        ))
    return friendships


async def get_sent_requests(session: AsyncSession, user_id: str) -> list[Friendship]:
    """Return pending friend requests sent by user."""
    result = await session.execute(
        select(FriendshipTable).where(
            (FriendshipTable.requester_id == user_id) & (FriendshipTable.status == "pending")
        )
    )
    rows = result.scalars().all()
    friendships = []
    for row in rows:
        addressee = await get_user(session, row.addressee_id)
        friendships.append(Friendship(
            id=row.id,
            requester_id=row.requester_id,
            addressee_id=row.addressee_id,
            status=FriendshipStatus.PENDING,
            addressee=addressee,
        ))
    return friendships


async def remove_friend(session: AsyncSession, user_id: str, friend_id: str) -> bool:
    result = await session.execute(
        select(FriendshipTable).where(
            ((FriendshipTable.requester_id == user_id) & (FriendshipTable.addressee_id == friend_id))
            | ((FriendshipTable.requester_id == friend_id) & (FriendshipTable.addressee_id == user_id))
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True
