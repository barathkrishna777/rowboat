"""Pydantic models for hangouts, swipes, and suggested matches."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class HangoutSource(str, Enum):
    AI_SUGGESTED = "ai_suggested"
    USER_CREATED = "user_created"
    TEMPLATE = "template"


class SwipeAction(str, Enum):
    PASS = "pass"
    INTERESTED = "interested"


class Hangout(BaseModel):
    id: str
    title: str
    description: str | None = None
    time_window: dict | None = None  # {"start": iso, "end": iso}
    location_area: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: HangoutSource = HangoutSource.USER_CREATED
    created_by: str | None = None


class HangoutCreate(BaseModel):
    title: str
    description: str | None = None
    time_window: dict | None = None
    location_area: str | None = None
    tags: list[str] = Field(default_factory=list)


class SwipeRequest(BaseModel):
    action: SwipeAction


class Swipe(BaseModel):
    user_id: str
    hangout_id: str
    action: SwipeAction


class SuggestedMatch(BaseModel):
    id: str
    hangout_id: str
    member_user_ids: list[str]
    score: int = 0
    status: str = "pending"
    group_id: str | None = None
