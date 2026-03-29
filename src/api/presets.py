"""Preset API for discover flow."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.db.database import get_session
from src.db.tables import PresetFavoriteTable, PresetTable
from src.models.preset import (
    Preset,
    PresetCreate,
    PresetCriteria,
    PresetFavoriteUpdate,
    PresetParseRequest,
    PresetParseResponse,
    PresetSource,
)
from src.models.user import User
from src.presets.agent import parse_natural_language_preset
from src.presets.catalog import BUILT_IN_PRESETS, get_built_in_preset

router = APIRouter()


def _row_to_preset(row: PresetTable, is_favorite: bool = False) -> Preset:
    return Preset(
        id=row.id,
        name=row.name,
        description=row.description,
        source=PresetSource(row.source),
        criteria=PresetCriteria(**json.loads(row.criteria)),
        is_favorite=is_favorite,
        is_built_in=False,
        created_at=row.created_at,
    )


@router.get("", response_model=list[Preset])
async def list_presets(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    favorites_result = await session.execute(
        select(PresetFavoriteTable.preset_id).where(PresetFavoriteTable.user_id == current_user.id)
    )
    favorite_ids = {r[0] for r in favorites_result.all()}

    result = await session.execute(
        select(PresetTable)
        .where(PresetTable.user_id == current_user.id)
        .order_by(PresetTable.updated_at.desc())
    )
    custom = [_row_to_preset(r, is_favorite=(r.id in favorite_ids)) for r in result.scalars().all()]
    built_in = [preset.model_copy(update={"is_favorite": preset.id in favorite_ids}) for preset in BUILT_IN_PRESETS]
    return [*built_in, *custom]


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
    )
    session.add(row)
    if body.is_favorite:
        session.add(PresetFavoriteTable(user_id=current_user.id, preset_id=row.id))
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
    built_in = get_built_in_preset(preset_id)
    if (not row or row.user_id != current_user.id) and not built_in:
        raise HTTPException(status_code=404, detail="Preset not found")

    existing = (await session.execute(
        select(PresetFavoriteTable).where(
            PresetFavoriteTable.user_id == current_user.id,
            PresetFavoriteTable.preset_id == preset_id,
        )
    )).scalar_one_or_none()

    if body.is_favorite and not existing:
        session.add(PresetFavoriteTable(user_id=current_user.id, preset_id=preset_id))
    if not body.is_favorite and existing:
        await session.delete(existing)

    await session.commit()
    if built_in:
        return built_in.model_copy(update={"is_favorite": body.is_favorite})
    await session.refresh(row)
    return _row_to_preset(row, is_favorite=body.is_favorite)


@router.post("/parse", response_model=PresetParseResponse)
async def parse_preset(
    body: PresetParseRequest,
    current_user: User = Depends(get_current_user),
):
    _ = current_user  # authenticated endpoint by design
    return parse_natural_language_preset(body.text)
