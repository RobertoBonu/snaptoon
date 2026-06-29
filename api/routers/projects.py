"""Endpoint /api/projects: list, create, delete, duplicate.

Riusa db/repos/projects.py esistente.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from billing.plans import plan_config, project_limit_reached
from db.models import LengthTarget
from db.repos import projects as projects_repo
from db.repos import users as users_repo
from db.session import session_scope

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class ProjectOut(BaseModel):
    id: str
    slug: str
    title: str
    length_target: str
    style_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectListOut(BaseModel):
    projects: list[ProjectOut]
    max_projects: int  # 0 = illimitato
    current_count: int


class ProjectCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    length: str = Field(default="medio")  # striscia | breve | medio | lungo


class ProjectDuplicateIn(BaseModel):
    new_title: str = Field(..., min_length=1, max_length=255)


# ============================================================
# Helpers
# ============================================================


def _to_out(p) -> ProjectOut:
    return ProjectOut(
        id=str(p.id),
        slug=p.slug,
        title=p.name,
        length_target=(
            p.length_target.value if hasattr(p.length_target, "value") else str(p.length_target)
        ),
        style_id=p.style_id,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ============================================================
# Endpoints
# ============================================================


@router.get("", response_model=ProjectListOut)
def list_projects(user: dict = Depends(require_user)) -> ProjectListOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        projects = projects_repo.list_by_owner(s, user_id)
        cfg = plan_config(u.plan)
        return ProjectListOut(
            projects=[_to_out(p) for p in projects],
            max_projects=cfg.max_projects,
            current_count=len(projects),
        )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateIn, user: dict = Depends(require_user)
) -> ProjectOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")

        count = projects_repo.count_by_owner(s, user_id)
        if project_limit_reached(u.plan, count):
            cfg = plan_config(u.plan)
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Hai raggiunto il limite del tuo piano ({cfg.max_projects} progetti). "
                    "Elimina un progetto o passa a un piano superiore."
                ),
            )

        try:
            length_target = LengthTarget(payload.length)
        except ValueError:
            length_target = LengthTarget.medio

        try:
            project = projects_repo.create_project(
                s, owner=u, name=payload.title, length_target=length_target
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return _to_out(project)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(slug: str, user: dict = Depends(require_user)) -> None:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        projects_repo.soft_delete(s, project)


@router.post(
    "/{slug}/duplicate", response_model=ProjectOut, status_code=status.HTTP_201_CREATED
)
def duplicate_project(
    slug: str, payload: ProjectDuplicateIn, user: dict = Depends(require_user)
) -> ProjectOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")

        count = projects_repo.count_by_owner(s, user_id)
        if project_limit_reached(u.plan, count):
            cfg = plan_config(u.plan)
            raise HTTPException(
                status_code=403,
                detail=f"Limite raggiunto ({cfg.max_projects} progetti).",
            )

        source = projects_repo.get_by_slug(s, user_id, slug)
        if source is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")

        dup = projects_repo.duplicate_project(s, source, payload.new_title)
        return _to_out(dup)
