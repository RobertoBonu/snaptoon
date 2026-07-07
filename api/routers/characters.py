"""Endpoint personaggi: CRUD + generazione reference image."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from billing.plans import cost_for_operation
from db.models import CreditOperation
from db.repos import characters as characters_repo
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import users as users_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from storage.client import download_bytes, object_exists, upload_bytes
from storage.image_variants import save_with_variants
from storage.keys import reference_key

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class CharacterOut(BaseModel):
    id: str
    name: str
    visual_description: str
    has_reference: bool
    created_at: datetime


class CharacterListOut(BaseModel):
    characters: list[CharacterOut]


class CharacterCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    visual_description: str = Field(..., min_length=1, max_length=2000)


class CharacterUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    visual_description: Optional[str] = Field(
        default=None, min_length=1, max_length=2000
    )


# ============================================================
# Helpers
# ============================================================


def _to_out(cs, has_ref: bool) -> CharacterOut:
    return CharacterOut(
        id=str(cs.id),
        name=cs.name,
        visual_description=cs.visual_description,
        has_reference=has_ref,
        created_at=cs.created_at,
    )


# ============================================================
# Endpoints
# ============================================================


@router.get("/projects/{slug}/characters", response_model=CharacterListOut)
def list_characters(
    slug: str, user: dict = Depends(require_user)
) -> CharacterListOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        chars = characters_repo.list_for_project(s, project)
        # has_reference: controlla che la chiave esista su storage
        out = []
        for c in chars:
            rk = reference_key(project.id, c.id, 1)
            out.append(_to_out(c, has_ref=object_exists(rk)))
        return CharacterListOut(characters=out)


@router.post(
    "/projects/{slug}/characters",
    response_model=CharacterOut,
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    slug: str, payload: CharacterCreateIn, user: dict = Depends(require_user)
) -> CharacterOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        try:
            cs = characters_repo.create_character(
                s, project=project, name=payload.name,
                visual_description=payload.visual_description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _to_out(cs, has_ref=False)


@router.patch(
    "/projects/{slug}/characters/{char_id}",
    response_model=CharacterOut,
)
def update_character(
    slug: str,
    char_id: str,
    payload: CharacterUpdateIn,
    user: dict = Depends(require_user),
) -> CharacterOut:
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID personaggio invalido")
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        if payload.name is not None:
            characters_repo.rename_character(s, cs, payload.name)
        if payload.visual_description is not None:
            characters_repo.update_character(
                s, cs, visual_description=payload.visual_description
            )
        rk = reference_key(project.id, cs.id, 1)
        return _to_out(cs, has_ref=object_exists(rk))


@router.delete(
    "/projects/{slug}/characters/{char_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_character(
    slug: str, char_id: str, user: dict = Depends(require_user)
) -> None:
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID personaggio invalido")
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        characters_repo.delete_character(s, cs)


@router.post(
    "/projects/{slug}/characters/{char_id}/reference",
    response_model=CharacterOut,
)
def generate_reference(
    slug: str, char_id: str, user: dict = Depends(require_user)
) -> CharacterOut:
    """Genera reference image (slot 1) per il personaggio.

    Costa generate_reference (1 cr).
    """
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")

    # Carica dati
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        style_preset_id = project.style_id
        char_name = cs.name
        char_desc = cs.visual_description
        pid = project.id

    if not style_preset_id:
        raise HTTPException(
            status_code=400,
            detail="Scegli prima uno stile per il progetto.",
        )

    # Charge + risolvi qualità utente
    from api.utils.quality import resolve_user_quality
    with session_scope() as _s:
        _u = users_repo.get_by_id(_s, user_id)
        user_quality = resolve_user_quality(_u)
    cost = cost_for_operation("generate_reference")
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_reference,
                reason=f"Reference {char_name}",
                reference_id=str(pid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Genera
    try:
        from snaptoon_core.generator import OpenAIImageGenerator
        from snaptoon_core.kids_pipeline import build_reference_prompt

        generator = OpenAIImageGenerator()
        prompt = build_reference_prompt(char_name, char_desc, style_preset_id)
        img_bytes = generator._generate_bytes(
            prompt=prompt,
            size="1024x1024",
            reference_images=None,
            quality=user_quality,
        )
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund reference {char_name}: {str(e)[:200]}",
            )
        raise HTTPException(status_code=502, detail=f"Errore generazione: {str(e)[:300]}")

    # Upload + save
    rk = reference_key(pid, cid, 1)
    save_with_variants(rk, img_bytes)
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs:
            characters_repo.upsert_reference(
                s, cs, slot_number=1, storage_key=rk,
                mime_type="image/png", file_size=len(img_bytes),
            )
        return _to_out(cs, has_ref=True)


@router.get("/projects/{slug}/characters/{char_id}/reference")
def get_reference_image(
    slug: str, char_id: str, user: dict = Depends(require_user)
) -> Response:
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(char_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        pid = project.id
    rk = reference_key(pid, cid, 1)
    if not object_exists(rk):
        raise HTTPException(status_code=404, detail="Reference non trovata")
    return Response(content=download_bytes(rk), media_type="image/png")


# Formati foto accettati per l'upload della reference
_ACCEPTED_IMAGE_MIMES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}
_MAX_REF_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post(
    "/projects/{slug}/characters/{char_id}/upload-reference",
    response_model=CharacterOut,
)
async def upload_reference_image(
    slug: str,
    char_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_user),
) -> CharacterOut:
    """Carica una foto (o disegno) come reference image slot 1 del personaggio.

    Sostituisce quella eventualmente già presente (generata o caricata).
    Non consuma crediti — è un upload manuale, niente AI.

    Formati accettati: PNG, JPEG, WEBP. Max 8 MB.
    """
    user_id = uuid.UUID(user["id"])
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

    # Verifica proprietà + esiste personaggio
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        pid = project.id
        char_name = cs.name

    # Upload su Object Storage (chiave: reference slot 1, formato PNG a
    # prescindere dall'input — la generazione AI usa PNG per coerenza)
    rk = reference_key(pid, cid, 1)
    upload_bytes(rk, data, content_type=file.content_type or "image/png")

    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        cs = next((c for c in project.character_sheets if c.id == cid), None)
        if cs is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        characters_repo.upsert_reference(
            s, cs, slot_number=1, storage_key=rk,
            mime_type=file.content_type or "image/png",
            file_size=len(data),
        )
        return _to_out(cs, has_ref=True)
