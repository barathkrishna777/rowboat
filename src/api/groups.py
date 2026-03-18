"""Group management API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.models.user import Group, User

router = APIRouter()

# In-memory store for MVP (will be replaced with SQLite)
_groups: dict[str, Group] = {}
_users: dict[str, User] = {}


class CreateGroupRequest(BaseModel):
    name: str
    creator_name: str
    creator_email: str


class AddMemberRequest(BaseModel):
    name: str
    email: str


@router.post("/", response_model=Group)
async def create_group(request: CreateGroupRequest):
    """Create a new outing group."""
    user_id = str(uuid.uuid4())
    user = User(id=user_id, name=request.creator_name, email=request.creator_email)
    _users[user_id] = user

    group_id = str(uuid.uuid4())
    group = Group(
        id=group_id,
        name=request.name,
        member_ids=[user_id],
        created_by=user_id,
    )
    _groups[group_id] = group
    return group


@router.get("/{group_id}", response_model=Group)
async def get_group(group_id: str):
    """Get group details."""
    if group_id not in _groups:
        raise HTTPException(status_code=404, detail="Group not found")
    return _groups[group_id]


@router.post("/{group_id}/members", response_model=Group)
async def add_member(group_id: str, request: AddMemberRequest):
    """Add a member to a group."""
    if group_id not in _groups:
        raise HTTPException(status_code=404, detail="Group not found")

    user_id = str(uuid.uuid4())
    user = User(id=user_id, name=request.name, email=request.email)
    _users[user_id] = user

    _groups[group_id].member_ids.append(user_id)
    return _groups[group_id]


@router.get("/{group_id}/members", response_model=list[User])
async def get_members(group_id: str):
    """Get all members of a group."""
    if group_id not in _groups:
        raise HTTPException(status_code=404, detail="Group not found")
    return [_users[uid] for uid in _groups[group_id].member_ids if uid in _users]
