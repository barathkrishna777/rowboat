"""Hangout cards, swipe, feed, matching, and from-match group creation."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import (
    GroupMemberTable,
    GroupTable,
    HangoutTable,
    SuggestedMatchTable,
    SwipeTable,
    UserTable,
)
from src.matching.scorer import score_pair
from src.models.hangout import (
    Hangout,
    HangoutCreate,
    HangoutSource,
    SuggestedMatch,
    Swipe,
    SwipeAction,
    SwipeRequest,
)
from src.models.user import User, UserPreferences, UserProfile

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────


def _row_to_hangout(row: HangoutTable) -> Hangout:
    return Hangout(
        id=row.id,
        title=row.title,
        description=row.description,
        time_window=json.loads(row.time_window) if row.time_window else None,
        location_area=row.location_area,
        tags=json.loads(row.tags) if row.tags else [],
        source=HangoutSource(row.source),
        created_by=row.created_by,
    )


def _row_to_match(row: SuggestedMatchTable) -> SuggestedMatch:
    return SuggestedMatch(
        id=row.id,
        hangout_id=row.hangout_id,
        member_user_ids=json.loads(row.member_user_ids),
        score=row.score,
        status=row.status,
        group_id=row.group_id,
    )


# ── Hangout CRUD ───────────────────────────────────────────────────────


@router.post("", response_model=Hangout, status_code=201)
async def create_hangout(
    body: HangoutCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new hangout card."""
    hangout_id = str(uuid.uuid4())
    row = HangoutTable(
        id=hangout_id,
        title=body.title,
        description=body.description,
        time_window=json.dumps(body.time_window) if body.time_window else None,
        location_area=body.location_area,
        tags=json.dumps(body.tags),
        source="user_created",
        created_by=current_user.id,
    )
    session.add(row)
    await session.commit()
    return _row_to_hangout(row)


@router.get("", response_model=list[Hangout])
async def list_hangouts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all hangout cards (feed). MVP: returns all, newest first."""
    result = await session.execute(
        select(HangoutTable).order_by(HangoutTable.created_at.desc())
    )
    return [_row_to_hangout(r) for r in result.scalars().all()]


@router.get("/{hangout_id}", response_model=Hangout)
async def get_hangout(
    hangout_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single hangout card by ID."""
    row = await session.get(HangoutTable, hangout_id)
    if not row:
        raise HTTPException(status_code=404, detail="Hangout not found")
    return _row_to_hangout(row)


# ── Feed (personalized) ───────────────────────────────────────────────


@router.get("/feed/me", response_model=list[Hangout])
async def my_feed(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return hangouts the user hasn't swiped on yet, newest first."""
    swiped = (
        select(SwipeTable.hangout_id).where(SwipeTable.user_id == current_user.id)
    )
    result = await session.execute(
        select(HangoutTable)
        .where(HangoutTable.id.not_in(swiped))
        .order_by(HangoutTable.created_at.desc())
    )
    return [_row_to_hangout(r) for r in result.scalars().all()]


# ── Swipe ──────────────────────────────────────────────────────────────


@router.post("/{hangout_id}/swipe", response_model=Swipe)
async def swipe(
    hangout_id: str,
    body: SwipeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Record a swipe. Idempotent — updates action if already swiped."""
    hangout = await session.get(HangoutTable, hangout_id)
    if not hangout:
        raise HTTPException(status_code=404, detail="Hangout not found")

    existing = (await session.execute(
        select(SwipeTable).where(
            SwipeTable.user_id == current_user.id,
            SwipeTable.hangout_id == hangout_id,
        )
    )).scalar_one_or_none()

    if existing:
        existing.action = body.action.value
    else:
        session.add(SwipeTable(
            user_id=current_user.id,
            hangout_id=hangout_id,
            action=body.action.value,
        ))
    await session.commit()

    return Swipe(
        user_id=current_user.id,
        hangout_id=hangout_id,
        action=body.action,
    )


# ── Matching / Suggestions ────────────────────────────────────────────


@router.get("/{hangout_id}/matches", response_model=list[SuggestedMatch])
async def get_matches(
    hangout_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get suggested matches for a hangout the user is interested in."""
    result = await session.execute(
        select(SuggestedMatchTable).where(
            SuggestedMatchTable.hangout_id == hangout_id,
            SuggestedMatchTable.status == "pending",
        )
    )
    return [_row_to_match(r) for r in result.scalars().all()]


@router.post("/{hangout_id}/generate-matches", response_model=list[SuggestedMatch])
async def generate_matches(
    hangout_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate suggested matches for a hangout based on interested users + similarity."""
    hangout = await session.get(HangoutTable, hangout_id)
    if not hangout:
        raise HTTPException(status_code=404, detail="Hangout not found")

    # Get all users who swiped "interested" on this hangout
    interested_result = await session.execute(
        select(SwipeTable).where(
            SwipeTable.hangout_id == hangout_id,
            SwipeTable.action == "interested",
        )
    )
    interested_swipes = interested_result.scalars().all()
    user_ids = [s.user_id for s in interested_swipes]

    if len(user_ids) < 2:
        return []

    # Load user preferences and profiles for scoring
    users_data: dict[str, tuple[UserPreferences | None, UserProfile | None]] = {}
    for uid in user_ids:
        row = await session.get(UserTable, uid)
        if row:
            prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
            prof = UserProfile(**json.loads(row.profile)) if row.profile else None
            users_data[uid] = (prefs, prof)

    # Build cohorts: for MVP, create one suggested match with all interested users
    # Score = average pairwise similarity * 100
    total_score = 0.0
    pair_count = 0
    uids = list(users_data.keys())
    for i in range(len(uids)):
        for j in range(i + 1, len(uids)):
            prefs_a, prof_a = users_data[uids[i]]
            prefs_b, prof_b = users_data[uids[j]]
            total_score += score_pair(prefs_a, prefs_b, prof_a, prof_b)
            pair_count += 1

    avg_score = int((total_score / pair_count) * 100) if pair_count > 0 else 0

    match_id = str(uuid.uuid4())
    match_row = SuggestedMatchTable(
        id=match_id,
        hangout_id=hangout_id,
        member_user_ids=json.dumps(uids),
        score=avg_score,
        status="pending",
    )
    session.add(match_row)
    await session.commit()

    return [_row_to_match(match_row)]


# ── From-match group creation ──────────────────────────────────────────


@router.post("/matches/{match_id}/create-group", response_model=SuggestedMatch)
async def create_group_from_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Accept a suggested match → create a GroupTable + members, return group_id."""
    match_row = await session.get(SuggestedMatchTable, match_id)
    if not match_row:
        raise HTTPException(status_code=404, detail="Suggested match not found")
    if match_row.group_id:
        # Already created — return idempotently
        return _row_to_match(match_row)

    member_ids = json.loads(match_row.member_user_ids)
    if current_user.id not in member_ids:
        raise HTTPException(status_code=403, detail="Not a member of this match")

    # Fetch hangout title for group name
    hangout = await session.get(HangoutTable, match_row.hangout_id)
    group_name = hangout.title if hangout else "Hangout Group"

    group_id = str(uuid.uuid4())
    group = GroupTable(id=group_id, name=group_name, created_by=current_user.id)
    session.add(group)

    for uid in member_ids:
        session.add(GroupMemberTable(group_id=group_id, user_id=uid))

    match_row.group_id = group_id
    match_row.status = "accepted"
    await session.commit()

    return _row_to_match(match_row)
