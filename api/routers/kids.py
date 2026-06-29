"""Endpoint /api/kids: templates, projects, characters.

Riusa db/repos/kids_templates.py + db/repos/projects.py + characters.py.
La generazione vera (Claude + OpenAI + SSE) arriva in Sett. 4.
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
from db.repos import characters as characters_repo
from db.repos import kids_templates as kids_templates_repo
from db.repos import projects as projects_repo
from db.repos import users as users_repo
from db.session import session_scope

router = APIRouter()


# Mapping style slug → (label, preset_id). Stesso schema di pages/06_KIDS.py.
KIDS_STYLE_MAP = {
    "flat": ("Flat", "bold_toddler_graphic"),
    "3d": ("3D", "illumination_cartoon_style"),
    "manga": ("Manga", "japanese_preschool_anime"),
}
KIDS_STYLE_PRESET_IDS = {pid for _, pid in KIDS_STYLE_MAP.values()}


# ============================================================
# Schemas
# ============================================================


class KidsTemplateOut(BaseModel):
    id: str
    slug: str
    label: str
    n_characters: int
    length_target: str
    grid_distribution: list[str]
    scene_distribution: list[dict]
    notes: str


class KidsTemplateListOut(BaseModel):
    templates: list[KidsTemplateOut]


class KidsStyleOut(BaseModel):
    slug: str
    label: str
    preset_id: str


class KidsProjectOut(BaseModel):
    id: str
    slug: str
    name: str
    style_id: Optional[str] = None
    style_label: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KidsProjectListOut(BaseModel):
    projects: list[KidsProjectOut]


class CharacterIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=2000)


class KidsProjectCreateIn(BaseModel):
    template_id: str
    style_slug: str  # flat | 3d | manga
    scintilla: str = Field(..., min_length=1, max_length=4000)
    characters: list[CharacterIn] = Field(..., min_length=1, max_length=5)


# ============================================================
# Helpers
# ============================================================


def _tpl_to_out(t) -> KidsTemplateOut:
    return KidsTemplateOut(
        id=str(t.id),
        slug=t.slug,
        label=t.label,
        n_characters=t.n_characters,
        length_target=t.length_target if isinstance(t.length_target, str)
                       else t.length_target.value,
        grid_distribution=list(t.grid_distribution),
        scene_distribution=list(t.scene_distribution),
        notes=t.notes or "",
    )


def _style_label_from_preset(preset_id: Optional[str]) -> Optional[str]:
    if not preset_id:
        return None
    for slug, (label, pid) in KIDS_STYLE_MAP.items():
        if pid == preset_id:
            return label
    return None


def _proj_to_out(p) -> KidsProjectOut:
    return KidsProjectOut(
        id=str(p.id),
        slug=p.slug,
        name=p.name,
        style_id=p.style_id,
        style_label=_style_label_from_preset(p.style_id),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ============================================================
# Endpoints
# ============================================================


@router.get("/templates", response_model=KidsTemplateListOut)
def list_templates(user: dict = Depends(require_user)) -> KidsTemplateListOut:
    with session_scope() as s:
        templates = kids_templates_repo.list_all(s, only_active=True)
        return KidsTemplateListOut(templates=[_tpl_to_out(t) for t in templates])


@router.get("/styles", response_model=list[KidsStyleOut])
def list_styles(user: dict = Depends(require_user)) -> list[KidsStyleOut]:
    return [
        KidsStyleOut(slug=slug, label=label, preset_id=pid)
        for slug, (label, pid) in KIDS_STYLE_MAP.items()
    ]


@router.get("/projects", response_model=KidsProjectListOut)
def list_projects(user: dict = Depends(require_user)) -> KidsProjectListOut:
    """Restituisce i progetti dell'utente che usano uno stile Kids."""
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        all_projects = projects_repo.list_by_owner(s, user_id)
        kids_only = [p for p in all_projects if p.style_id in KIDS_STYLE_PRESET_IDS]
        return KidsProjectListOut(projects=[_proj_to_out(p) for p in kids_only])


@router.post("/projects", response_model=KidsProjectOut, status_code=status.HTTP_201_CREATED)
def create_kids_project(
    payload: KidsProjectCreateIn, user: dict = Depends(require_user)
) -> KidsProjectOut:
    """Crea il progetto Kids con template + stile + cast iniziale.

    NON genera ancora la storia o le immagini — quella è la pipeline di
    Sett. 4 (Claude + OpenAI + SSE). Qui salviamo solo le scelte iniziali
    dell'utente per dare un progetto "vivo" subito.
    """
    user_id = uuid.UUID(user["id"])

    if payload.style_slug not in KIDS_STYLE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Stile non valido. Usa uno tra: {list(KIDS_STYLE_MAP.keys())}",
        )
    _, preset_id = KIDS_STYLE_MAP[payload.style_slug]

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate template
        try:
            tpl = kids_templates_repo.get_by_id(s, payload.template_id)
        except Exception:
            tpl = None
        if tpl is None:
            raise HTTPException(status_code=400, detail="Template non valido")

        # Check num personaggi rispetto al template
        if len(payload.characters) != tpl.n_characters:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Il template richiede {tpl.n_characters} personaggi, "
                    f"ricevuti {len(payload.characters)}"
                ),
            )

        # Limite piano
        count = projects_repo.count_by_owner(s, user_id)
        if project_limit_reached(u.plan, count):
            cfg = plan_config(u.plan)
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Limite raggiunto ({cfg.max_projects} progetti). "
                    "Elimina un progetto o passa a un piano superiore."
                ),
            )

        # Length target dal template (lungo/breve)
        length_str = tpl.length_target if isinstance(tpl.length_target, str) else tpl.length_target.value
        try:
            length_target = LengthTarget(length_str)
        except ValueError:
            length_target = LengthTarget.breve

        # Nome del progetto: usa primo personaggio + label template
        project_name = f"{tpl.label} — {payload.characters[0].name}"

        project = projects_repo.create_project(
            s, owner=u, name=project_name, length_target=length_target
        )
        projects_repo.set_style(s, project, preset_id)
        # Salvo la scintilla come source_text
        projects_repo.set_source_text(s, project, payload.scintilla)

        # Crea i personaggi
        for ch in payload.characters:
            try:
                characters_repo.create_character(
                    s, project=project,
                    name=ch.name, visual_description=ch.description,
                )
            except ValueError:
                # Personaggio già esistente con quel nome → skip
                pass

        return _proj_to_out(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kids_project(project_id: str, user: dict = Depends(require_user)) -> None:
    user_id = uuid.UUID(user["id"])
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID progetto invalido")
    with session_scope() as s:
        project = projects_repo.get_by_id(s, proj_uuid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        projects_repo.soft_delete(s, project)
