"""Endpoint /api/kids: templates, projects, characters.

Riusa db/repos/kids_templates.py + db/repos/projects.py + characters.py.
La generazione vera (Claude + OpenAI + SSE) arriva in Sett. 4.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
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
    "chibi": ("Chibi", "chibi_kawaii_emotions"),
    "supereroi": ("Supereroi", "cartoon_superhero_kids"),
    "fiaba": ("Fiaba", "enchanted_fairytale_princess"),
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


# ============================================================
# Personaggi KIDS — upload/genera reference image
#
# Riusa la logica di api/routers/characters.py (flusso Pro) ma indicizza
# via project UUID invece di slug, per coerenza con il resto dell'API kids.
# ============================================================

from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import reference_key
from db.repos import characters as characters_repo
from db.repos import credits as credits_repo
from db.repos import users as users_repo
from db.repos.credits import InsufficientCreditsError
from db.models import CreditOperation
from billing.plans import cost_for_operation


class KidsCharacterOut(BaseModel):
    id: str
    name: str
    visual_description: str
    has_reference: bool


class KidsCharactersListOut(BaseModel):
    characters: list[KidsCharacterOut]


_ACCEPTED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_MAX_REF_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB


def _kids_project_or_404(project_id: str, user_id: uuid.UUID):
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID progetto invalido")
    return pid


@router.get(
    "/projects/{project_id}/characters", response_model=KidsCharactersListOut
)
def list_kids_characters(
    project_id: str, user: dict = Depends(require_user)
) -> KidsCharactersListOut:
    user_id = uuid.UUID(user["id"])
    pid = _kids_project_or_404(project_id, user_id)
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        out = []
        for cs in project.character_sheets:
            rk = reference_key(pid, cs.id, 1)
            out.append(
                KidsCharacterOut(
                    id=str(cs.id),
                    name=cs.name,
                    visual_description=cs.visual_description,
                    has_reference=object_exists(rk),
                )
            )
        return KidsCharactersListOut(characters=out)


@router.get("/projects/{project_id}/characters/{char_id}/reference")
def get_kids_character_reference(
    project_id: str, char_id: str, user: dict = Depends(require_user)
) -> Response:
    user_id = uuid.UUID(user["id"])
    pid = _kids_project_or_404(project_id, user_id)
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID personaggio invalido")
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
    rk = reference_key(pid, cid, 1)
    if not object_exists(rk):
        raise HTTPException(status_code=404, detail="Reference non trovata")
    return Response(content=download_bytes(rk), media_type="image/png")


@router.post(
    "/projects/{project_id}/characters/{char_id}/generate-reference",
    response_model=KidsCharacterOut,
)
def generate_kids_character_reference(
    project_id: str, char_id: str, user: dict = Depends(require_user)
) -> KidsCharacterOut:
    """Genera AI la reference image (slot 1) del personaggio KIDS.

    Costa generate_reference (1 cr). Refund automatico su errore.
    Usa build_reference_prompt di snaptoon_core.kids_pipeline.
    """
    from snaptoon_core.generator import OpenAIImageGenerator
    from snaptoon_core.kids_pipeline import build_reference_prompt

    user_id = uuid.UUID(user["id"])
    pid = _kids_project_or_404(project_id, user_id)
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID personaggio invalido")

    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        style_preset_id = project.style_id
        if not style_preset_id:
            raise HTTPException(
                status_code=400,
                detail="Stile non impostato sul progetto",
            )
        char_name = cs.name
        char_desc = cs.visual_description

    # Charge
    cost = cost_for_operation("generate_reference")
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_reference,
                reason=f"KIDS reference {char_name}",
                reference_id=str(pid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Genera
    try:
        generator = OpenAIImageGenerator()
        prompt = build_reference_prompt(char_name, char_desc, style_preset_id)
        img_bytes = generator._generate_bytes(
            prompt=prompt, size="1024x1024",
            reference_images=None, quality="medium",
        )
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund KIDS ref {char_name}: {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502, detail=f"Errore generazione: {str(e)[:300]}"
        )

    # Upload + save
    rk = reference_key(pid, cid, 1)
    upload_bytes(rk, img_bytes, content_type="image/png")
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is not None:
            characters_repo.upsert_reference(
                s, cs, slot_number=1, storage_key=rk,
                mime_type="image/png", file_size=len(img_bytes),
            )
        return KidsCharacterOut(
            id=str(cs.id) if cs else char_id,
            name=char_name,
            visual_description=char_desc,
            has_reference=True,
        )


@router.post(
    "/projects/{project_id}/characters/{char_id}/upload-reference",
    response_model=KidsCharacterOut,
)
async def upload_kids_character_reference(
    project_id: str,
    char_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_user),
) -> KidsCharacterOut:
    """Carica una foto come reference image slot 1 del personaggio KIDS.

    Sostituisce quella eventualmente già presente (generata o caricata).
    Zero crediti — è un upload manuale, no AI.
    """
    user_id = uuid.UUID(user["id"])
    pid = _kids_project_or_404(project_id, user_id)
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID personaggio invalido")

    if file.content_type not in _ACCEPTED_IMAGE_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Formato non supportato ({file.content_type}). Usa PNG, JPEG o WEBP.",
        )

    data = await file.read()
    if len(data) > _MAX_REF_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File troppo grande (max {_MAX_REF_SIZE_BYTES // (1024*1024)} MB).",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="File vuoto.")

    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")

    rk = reference_key(pid, cid, 1)
    upload_bytes(rk, data, content_type=file.content_type or "image/png")

    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        characters_repo.upsert_reference(
            s, cs, slot_number=1, storage_key=rk,
            mime_type=file.content_type or "image/png",
            file_size=len(data),
        )
        return KidsCharacterOut(
            id=str(cs.id),
            name=cs.name,
            visual_description=cs.visual_description,
            has_reference=True,
        )
