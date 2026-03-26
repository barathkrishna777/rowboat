"""Group management API endpoints — persisted to SQLite via SQLAlchemy."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_session
from src.db.tables import GroupMemberTable, GroupTable, UserTable
from src.models.user import Group, User, UserPreferences

router = APIRouter()


class CreateGroupRequest(BaseModel):
    name: str
    creator_name: str
    creator_email: str


class AddMemberRequest(BaseModel):
    name: str
    email: str


def _row_to_user(row: UserTable) -> User:
    prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
    token = json.loads(row.google_calendar_token) if row.google_calendar_token else None
    return User(
        id=row.id, name=row.name, email=row.email,
        username=row.username, auth_provider=row.auth_provider,
        preferences=prefs, google_calendar_token=token,
    )


async def _get_or_create_user(session: AsyncSession, name: str, email: str) -> UserTable:
    """Find existing user by email, or create a new one (no password — added on registration)."""
    result = await session.execute(select(UserTable).where(UserTable.email == email))
    row = result.scalar_one_or_none()
    if row:
        if row.name != name:
            row.name = name
        return row
    row = UserTable(id=str(uuid.uuid4()), name=name, email=email)
    session.add(row)
    await session.flush()
    return row


@router.post("/", response_model=Group)
async def create_group(request: CreateGroupRequest, session: AsyncSession = Depends(get_session)):
    """Create a new outing group, persisted to the database."""
    user_row = await _get_or_create_user(session, request.creator_name, request.creator_email)

    group_id = str(uuid.uuid4())
    group_row = GroupTable(id=group_id, name=request.name, created_by=user_row.id)
    session.add(group_row)
    member_row = GroupMemberTable(group_id=group_id, user_id=user_row.id)
    session.add(member_row)
    await session.commit()

    return Group(id=group_id, name=request.name, member_ids=[user_row.id], created_by=user_row.id)


@router.get("/{group_id}", response_model=Group)
async def get_group(group_id: str, session: AsyncSession = Depends(get_session)):
    """Get group details."""
    group_row = await session.get(GroupTable, group_id)
    if not group_row:
        raise HTTPException(status_code=404, detail="Group not found")

    result = await session.execute(
        select(GroupMemberTable.user_id).where(GroupMemberTable.group_id == group_id)
    )
    member_ids = [r[0] for r in result.all()]
    return Group(id=group_row.id, name=group_row.name, member_ids=member_ids, created_by=group_row.created_by)


@router.post("/{group_id}/members", response_model=Group)
async def add_member(group_id: str, request: AddMemberRequest, session: AsyncSession = Depends(get_session)):
    """Add a member to a group (creates user record if needed)."""
    group_row = await session.get(GroupTable, group_id)
    if not group_row:
        raise HTTPException(status_code=404, detail="Group not found")

    user_row = await _get_or_create_user(session, request.name, request.email)

    existing = (await session.execute(
        select(GroupMemberTable).where(
            GroupMemberTable.group_id == group_id,
            GroupMemberTable.user_id == user_row.id,
        )
    )).scalar_one_or_none()
    if not existing:
        session.add(GroupMemberTable(group_id=group_id, user_id=user_row.id))
        await session.commit()

    result = await session.execute(
        select(GroupMemberTable.user_id).where(GroupMemberTable.group_id == group_id)
    )
    member_ids = [r[0] for r in result.all()]
    return Group(id=group_row.id, name=group_row.name, member_ids=member_ids, created_by=group_row.created_by)


@router.get("/{group_id}/members", response_model=list[User])
async def get_members(group_id: str, session: AsyncSession = Depends(get_session)):
    """Get all members of a group."""
    group_row = await session.get(GroupTable, group_id)
    if not group_row:
        raise HTTPException(status_code=404, detail="Group not found")

    result = await session.execute(
        select(GroupMemberTable.user_id).where(GroupMemberTable.group_id == group_id)
    )
    users = []
    for (uid,) in result.all():
        row = await session.get(UserTable, uid)
        if row:
            users.append(_row_to_user(row))
    return users
