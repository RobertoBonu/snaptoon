"""Endpoint libreria stili + assegnazione stile al progetto."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.routers.auth import require_user
from db.repos import projects as projects_repo
from db.session import session_scope

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class StyleOut(BaseModel):
    id: str
    label: str
    category: str
    expansion: str
    is_handmade: bool
    is_custom: bool


class StyleListOut(BaseModel):
    styles: list[StyleOut]
    categories: list[str]


class SetStyleIn(BaseModel):
    style_id: str


# ============================================================
# Endpoints
# ============================================================


@router.get("", response_model=StyleListOut)
def list_styles(
    category: Optional[str] = None, user: dict = Depends(require_user)
) -> StyleListOut:
    from snaptoon_core.styles_library import count_by_category, list_presets

    presets = list_presets(category=category)
    categories = sorted(count_by_category().keys())
    return StyleListOut(
        styles=[
            StyleOut(
                id=p.id,
                label=p.label,
                category=p.category,
                expansion=p.expansion,
                is_handmade=p.is_handmade,
                is_custom=p.is_custom,
            )
            for p in presets
        ],
        categories=categories,
    )


@router.patch(
    "/projects/{slug}/style", status_code=status.HTTP_204_NO_CONTENT
)
def set_project_style(
    slug: str, payload: SetStyleIn, user: dict = Depends(require_user)
) -> None:
    from snaptoon_core.styles_library import get_preset

    if get_preset(payload.style_id) is None:
        raise HTTPException(status_code=400, detail="Stile non trovato")

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        projects_repo.set_style(s, project, payload.style_id)
