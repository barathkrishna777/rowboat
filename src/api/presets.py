"""Preset API for discover flow."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import PresetTable
from src.models.preset import Preset, PresetCreate, PresetCriteria, PresetFavoriteUpdate, PresetSource
from src.models.user import User

router = APIRouter()


BUILT_IN_PRESETS: list[Preset] = [
    Preset(
        id="built-in-party",
        name="Feeling like Partying",
        description="Upbeat nightlife, social venues, and energetic group-friendly options.",
        source=PresetSource.BUILT_IN,
        criteria=PresetCriteria(activities=["nightlife"], vibe=["lively", "late night"]),
        is_favorite=False,
        is_built_in=True,
    ),
    Preset(
        id="built-in-hike",
        name="In the mood for a hike",
        description="Trails, outdoor activity, and nearby casual food after the walk.",
        source=PresetSource.BUILT_IN,
        criteria=PresetCriteria(activities=["hiking", "outdoors"], vibe=["active", "daytime"]),
        is_favorite=False,
        is_built_in=True,
    ),
    Preset(
        id="built-in-roast",
        name="Sunday roast?",
        description="Slow-paced comfort cuisine with cozy atmosphere and easy conversation.",
        source=PresetSource.BUILT_IN,
        criteria=PresetCriteria(cuisines=["comfort food"], vibe=["cozy", "weekend"]),
        is_favorite=False,
        is_built_in=True,
    ),
]


def _row_to_preset(row: PresetTable) -> Preset:
    return Preset(
        id=row.id,
        name=row.name,
        description=row.description,
        source=PresetSource(row.source),
        criteria=PresetCriteria(**json.loads(row.criteria)),
        is_favorite=bool(row.is_favorite),
        is_built_in=False,
        created_at=row.created_at,
    )


@router.get("", response_model=list[Preset])
async def list_presets(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PresetTable)
        .where(PresetTable.user_id == current_user.id)
        .order_by(PresetTable.updated_at.desc())
    )
    custom = [_row_to_preset(r) for r in result.scalars().all()]
    return [*BUILT_IN_PRESETS, *custom]


@router.post("", response_model=Preset, status_code=201)
async def create_preset(
    body: PresetCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if body.source == PresetSource.BUILT_IN:
        raise HTTPException(status_code=400, detail="Built-in source is not valid for user-created presets")

    row = PresetTable(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        source=body.source.value,
        criteria=body.criteria.model_dump_json(),
        is_favorite=1 if body.is_favorite else 0,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _row_to_preset(row)


@router.patch("/{preset_id}/favorite", response_model=Preset)
async def update_favorite(
    preset_id: str,
    body: PresetFavoriteUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    row = await session.get(PresetTable, preset_id)
    if not row or row.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Preset not found")

    row.is_favorite = 1 if body.is_favorite else 0
    await session.commit()
    await session.refresh(row)
    return _row_to_preset(row)
