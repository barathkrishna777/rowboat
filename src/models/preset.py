"""Pydantic models for discover presets."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PresetSource(str, Enum):
    MANUAL = "manual"
    AI = "ai"
    BUILT_IN = "built_in"


class PresetCriteria(BaseModel):
    cuisine_preferences: list[str] = Field(default_factory=list)
    activity_preferences: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    budget_max: str | None = "$$"
    dealbreakers: list[str] = Field(default_factory=list)
    preferred_neighborhoods: list[str] = Field(default_factory=list)
    accessibility_needs: list[str] = Field(default_factory=list)


class Preset(BaseModel):
    id: str
    name: str
    description: str | None = None
    source: PresetSource
    criteria: PresetCriteria = Field(default_factory=PresetCriteria)
    is_favorite: bool = False
    is_built_in: bool = False
    created_at: datetime | None = None


class PresetCreate(BaseModel):
    name: str
    description: str | None = None
    source: PresetSource = PresetSource.MANUAL
    criteria: PresetCriteria = Field(default_factory=PresetCriteria)
    is_favorite: bool = False


class PresetFavoriteUpdate(BaseModel):
    is_favorite: bool


class PresetParseRequest(BaseModel):
    text: str


class PresetParseResponse(BaseModel):
    name_suggestion: str
    description_suggestion: str
    criteria: PresetCriteria = Field(default_factory=PresetCriteria)
    confidence: float = 0.0
