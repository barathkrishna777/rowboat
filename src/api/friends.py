"""Friend management API endpoints — persisted to SQLite via SQLAlchemy."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import FriendshipTable, UserTable
from src.models.user import (
    Friendship, FriendshipStatus, User, UserAvailability, UserPreferences, UserProfile,
)

router = APIRouter()


def _assert_owner(current_user: User, user_id: str) -> None:
    """Raise 403 if the authenticated user doesn't match the path user_id."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to act on behalf of another user",
        )


def _row_to_user(row: UserTable) -> User:
    prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
    token = json.loads(row.google_calendar_token) if row.google_calendar_token else None
    profile = UserProfile(**json.loads(row.profile)) if row.profile else None
    avail = UserAvailability(**json.loads(row.availability)) if row.availability else None
    return User(
        id=row.id, name=row.name, email=row.email,
        username=row.username, auth_provider=row.auth_provider,
        preferences=prefs, google_calendar_token=token,
        profile=profile, availability=avail,
    )


class RegisterUserRequest(BaseModel):
    user_id: str
    name: str
    email: str


class SendFriendRequestBody(BaseModel):
    to_email: str | None = None
    to_username: str | None = None


class RespondFriendRequestBody(BaseModel):
    accept: bool


# ── User registration (called by UI on group creation) ────────────────


@router.post("/register", response_model=User)
async def register_user(req: RegisterUserRequest, session: AsyncSession = Depends(get_session)):
    """Register or update a user so they can be found by email."""
    row = await session.get(UserTable, req.user_id)
    if row:
        row.name = req.name
        row.email = req.email
    else:
        from src.api.groups import _get_or_create_user
        row = await _get_or_create_user(session, req.name, req.email)
    await session.commit()
    return _row_to_user(row)


@router.get("/search", response_model=list[User])
async def search_users(q: str = "", session: AsyncSession = Depends(get_session)):
    """Search registered users by name or email."""
    if not q or len(q) < 2:
        return []
    q_lower = f"%{q.lower()}%"
    result = await session.execute(
        select(UserTable).where(
            UserTable.name.ilike(q_lower) | UserTable.email.ilike(q_lower)
        )
    )
    return [_row_to_user(r) for r in result.scalars().all()]


# ── Friend requests ───────────────────────────────────────────────────


@router.post("/{user_id}/request", response_model=Friendship)
async def send_friend_request(
    user_id: str,
    body: SendFriendRequestBody,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _assert_owner(current_user, user_id)
    """Send a friend request to another user by email."""
    sender = await session.get(UserTable, user_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not registered. Call /register first.")

    target = None
    if body.to_username:
        result = await session.execute(
            select(UserTable).where(UserTable.username == body.to_username)
        )
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail=f"No user found with username @{body.to_username}")
    elif body.to_email:
        result = await session.execute(
            select(UserTable).where(UserTable.email == body.to_email)
        )
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail=f"No user found with email {body.to_email}")
    else:
        raise HTTPException(status_code=400, detail="Provide either to_email or to_username")
    if target.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot send a friend request to yourself")

    existing_result = await session.execute(
        select(FriendshipTable).where(
            ((FriendshipTable.requester_id == user_id) & (FriendshipTable.addressee_id == target.id))
            | ((FriendshipTable.requester_id == target.id) & (FriendshipTable.addressee_id == user_id))
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=400, detail="Already friends")
        if existing.status == "pending":
            raise HTTPException(status_code=400, detail="Friend request already pending")

    row = FriendshipTable(requester_id=user_id, addressee_id=target.id, status="pending")
    session.add(row)
    await session.commit()
    await session.refresh(row)

    return Friendship(
        id=row.id,
        requester_id=user_id,
        addressee_id=target.id,
        status=FriendshipStatus.PENDING,
        requester=_row_to_user(sender),
        addressee=_row_to_user(target),
    )


@router.post("/{user_id}/respond/{friendship_id}", response_model=Friendship)
async def respond_to_request(
    user_id: str,
    friendship_id: int,
    body: RespondFriendRequestBody,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _assert_owner(current_user, user_id)
    """Accept or decline a friend request."""
    row = await session.get(FriendshipTable, friendship_id)
    if not row:
        raise HTTPException(status_code=404, detail="Friend request not found")
    if row.addressee_id != user_id:
        raise HTTPException(status_code=403, detail="Only the addressee can respond")
    if row.status != "pending":
        raise HTTPException(status_code=400, detail="Request already resolved")

    row.status = "accepted" if body.accept else "declined"
    await session.commit()

    requester = await session.get(UserTable, row.requester_id)
    addressee = await session.get(UserTable, row.addressee_id)
    return Friendship(
        id=row.id,
        requester_id=row.requester_id,
        addressee_id=row.addressee_id,
        status=FriendshipStatus(row.status),
        requester=_row_to_user(requester) if requester else None,
        addressee=_row_to_user(addressee) if addressee else None,
    )


# ── Friend list & pending requests ────────────────────────────────────


@router.get("/{user_id}/friends", response_model=list[User])
async def get_friends(user_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    _assert_owner(current_user, user_id)
    """Get all accepted friends for a user."""
    result = await session.execute(
        select(FriendshipTable).where(
            ((FriendshipTable.requester_id == user_id) | (FriendshipTable.addressee_id == user_id))
            & (FriendshipTable.status == "accepted")
        )
    )
    friends: list[User] = []
    for row in result.scalars().all():
        friend_id = row.addressee_id if row.requester_id == user_id else row.requester_id
        user_row = await session.get(UserTable, friend_id)
        if user_row:
            friends.append(_row_to_user(user_row))
    return friends


@router.get("/{user_id}/requests/incoming", response_model=list[Friendship])
async def get_incoming_requests(user_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    _assert_owner(current_user, user_id)
    """Get pending friend requests received by user."""
    result = await session.execute(
        select(FriendshipTable).where(
            (FriendshipTable.addressee_id == user_id) & (FriendshipTable.status == "pending")
        )
    )
    incoming = []
    for row in result.scalars().all():
        requester = await session.get(UserTable, row.requester_id)
        incoming.append(Friendship(
            id=row.id,
            requester_id=row.requester_id,
            addressee_id=row.addressee_id,
            status=FriendshipStatus.PENDING,
            requester=_row_to_user(requester) if requester else None,
        ))
    return incoming


@router.get("/{user_id}/requests/outgoing", response_model=list[Friendship])
async def get_outgoing_requests(user_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    _assert_owner(current_user, user_id)
    """Get pending friend requests sent by user."""
    result = await session.execute(
        select(FriendshipTable).where(
            (FriendshipTable.requester_id == user_id) & (FriendshipTable.status == "pending")
        )
    )
    outgoing = []
    for row in result.scalars().all():
        addressee = await session.get(UserTable, row.addressee_id)
        outgoing.append(Friendship(
            id=row.id,
            requester_id=row.requester_id,
            addressee_id=row.addressee_id,
            status=FriendshipStatus.PENDING,
            addressee=_row_to_user(addressee) if addressee else None,
        ))
    return outgoing


# ── Remove friend ─────────────────────────────────────────────────────


@router.delete("/{user_id}/friends/{friend_id}")
async def remove_friend(user_id: str, friend_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    _assert_owner(current_user, user_id)
    """Remove an existing friendship."""
    result = await session.execute(
        select(FriendshipTable).where(
            ((FriendshipTable.requester_id == user_id) & (FriendshipTable.addressee_id == friend_id))
            | ((FriendshipTable.requester_id == friend_id) & (FriendshipTable.addressee_id == user_id))
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Friendship not found")
    await session.delete(row)
    await session.commit()
    return {"detail": "Friend removed"}
