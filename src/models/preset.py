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
    activities: list[str] = Field(default_factory=list)
    cuisines: list[str] = Field(default_factory=list)
    vibe: list[str] = Field(default_factory=list)
    budget: str | None = None


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
