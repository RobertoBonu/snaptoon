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
    # Metadati opzionali per copertina + quarta di copertina.
    subtitle: str = Field(default="", max_length=255)
    author: str = Field(default="", max_length=255)
    copyright_text: str = Field(default="", max_length=1000)


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
    # Blocca la creazione di progetti Pro per gli account KIDS
    # (la sidebar li reindirizza già, ma difendo anche l'API).
    if user.get("role") == "kids":
        raise HTTPException(
            status_code=403,
            detail="Il tuo account non ha accesso al flusso Pro. Usa la sezione KIDS.",
        )
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

        # Salva metadati cover + copyright come nel flusso KIDS
        from db.models import Cover as CoverORM

        cover = CoverORM(
            project_id=project.id,
            title=payload.title.strip(),
            subtitle=payload.subtitle.strip(),
            author=payload.author.strip(),
            description="",
            payload={},
        )
        s.add(cover)
        if payload.copyright_text.strip():
            project.copyright_text = payload.copyright_text.strip()
        s.flush()

        return _to_out(project)


class CoverMetadataOut(BaseModel):
    title: str
    subtitle: str
    author: str
    copyright_text: str
    has_illustration: bool


class CoverMetadataIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    author: Optional[str] = Field(default=None, max_length=255)
    copyright_text: Optional[str] = Field(default=None, max_length=1000)


@router.get("/{slug}/cover-metadata", response_model=CoverMetadataOut)
def get_cover_metadata(
    slug: str, user: dict = Depends(require_user)
) -> CoverMetadataOut:
    from storage.client import object_exists
    from storage.keys import cover_illustration_key

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")

        cover = project.cover
        return CoverMetadataOut(
            title=(cover.title if cover else "") or project.name,
            subtitle=cover.subtitle if cover else "",
            author=cover.author if cover else "",
            copyright_text=project.copyright_text or "",
            has_illustration=object_exists(cover_illustration_key(project.id)),
        )


@router.patch("/{slug}/cover-metadata", response_model=CoverMetadataOut)
def update_cover_metadata(
    slug: str,
    payload: CoverMetadataIn,
    user: dict = Depends(require_user),
) -> CoverMetadataOut:
    from db.models import Cover as CoverORM

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")

        cover = project.cover
        if cover is None:
            cover = CoverORM(
                project_id=project.id,
                title="",
                subtitle="",
                author="",
                description="",
                payload={},
            )
            s.add(cover)

        if payload.title is not None:
            cover.title = payload.title.strip()
        if payload.subtitle is not None:
            cover.subtitle = payload.subtitle.strip()
        if payload.author is not None:
            cover.author = payload.author.strip()
        if payload.copyright_text is not None:
            project.copyright_text = payload.copyright_text.strip() or None

        s.flush()
        return get_cover_metadata(slug, user)


class GenerateCoverOut(BaseModel):
    ok: bool
    detail: str


def _build_pro_cover_prompt(
    title: str, subtitle: str, author: str, cast: list[dict], style_preset_id: str
) -> str:
    """Prompt AI per copertina di fumetto Pro (2:3 verticale, testi AI-bake).

    Ispirato a kids_pipeline.build_cover_prompt ma con estetica graphic novel
    invece di children's book.
    """
    from snaptoon_core.styles_library import get_preset

    preset = get_preset(style_preset_id)
    parts = [
        "=== RENDER MODE ===\n"
        "Vertical graphic novel cover illustration, 2:3 aspect ratio. "
        "Edge-to-edge full-bleed. Cinematic dramatic composition, strong "
        "atmosphere. No panel border, no frame, no paper margin. The title, "
        "the subtitle and the characters should be the visual focus.",
    ]
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")

    parts.append(f"=== COVER ===\nGraphic novel cover for «{title}»")

    if cast:
        cast_block = ["=== CHARACTERS ON COVER ==="]
        for cs in cast:
            cast_block.append(f"- {cs['name']}: {cs['description']}")
        cast_block.append(
            "Characters must look IDENTICAL to reference images. Iconic hero "
            "framing, expressive."
        )
        parts.append("\n".join(cast_block))

    text_block = ["=== TEXT (DRAW IT IN THE IMAGE) ==="]
    text_block.append(
        f"At the top of the image, draw the title in bold graphic-novel "
        f"style lettering: '{title.upper()}'. Strong outline, high contrast, "
        f"impactful."
    )
    if subtitle.strip():
        text_block.append(
            f"Below the title, draw the subtitle in smaller readable font: "
            f"'{subtitle}'"
        )
    if author.strip():
        text_block.append(
            f"At the bottom of the image, draw the author name in clean "
            f"understated font: '{author}'"
        )
    parts.append("\n".join(text_block))

    parts.append(
        "=== AVOID ===\n"
        "watermark, multiple titles, scrambled text, weird letters, "
        "misspelled words, panel borders."
    )
    return "\n\n".join(parts)


@router.post("/{slug}/generate-cover", response_model=GenerateCoverOut)
def generate_pro_cover(
    slug: str, user: dict = Depends(require_user)
) -> GenerateCoverOut:
    """Genera la copertina AI del fumetto Pro (2:3 verticale, testi AI-bake).

    Idempotente: se cover_illustration_key esiste già, ritorna 200 senza
    consumare crediti. Per rigenerare bisogna eliminare la cover prima.

    Usa i character references esistenti (li aspetta già generati).
    """
    import tempfile
    from pathlib import Path

    from billing.plans import cost_for_operation
    from db.models import CreditOperation
    from db.repos import characters as characters_repo
    from db.repos import covers as covers_repo
    from db.repos import credits as credits_repo
    from db.repos.credits import InsufficientCreditsError
    from snaptoon_core.generator import OpenAIImageGenerator
    from storage.client import download_bytes, object_exists, upload_bytes
    from storage.keys import cover_illustration_key, reference_key

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if not project.style_id:
            raise HTTPException(
                status_code=400, detail="Devi scegliere uno stile prima."
            )
        style_preset_id = project.style_id
        pid = project.id
        cast = [
            {
                "name": cs.name,
                "description": cs.visual_description or "",
                "id": str(cs.id),
            }
            for cs in project.character_sheets
        ]
        cover_orm = project.cover
        title = (cover_orm.title if cover_orm else "") or project.name
        subtitle = (cover_orm.subtitle if cover_orm else "") or ""
        author = (cover_orm.author if cover_orm else "") or ""

    cover_key = cover_illustration_key(pid)
    if object_exists(cover_key):
        return GenerateCoverOut(ok=True, detail="Cover già presente")

    # Charge crediti (analogo KIDS: uso medium quality)
    cost = cost_for_operation("generate_panel", quality="medium")
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_cover,
                reason=f"Cover Pro «{title}»",
                reference_id=str(pid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Genera cover con i reference dei personaggi
    generator = OpenAIImageGenerator()
    tmp_refs: list[Path] = []
    try:
        for c in cast:
            rk = reference_key(pid, uuid.UUID(c["id"]), 1)
            if object_exists(rk):
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(download_bytes(rk))
                tmp.close()
                tmp_refs.append(Path(tmp.name))

        prompt = _build_pro_cover_prompt(
            title, subtitle, author, cast, style_preset_id
        )
        img_bytes = generator._generate_bytes(
            prompt=prompt,
            size="1024x1536",
            reference_images=tmp_refs if tmp_refs else None,
            quality="medium",
        )
        upload_bytes(cover_key, img_bytes, content_type="image/png")

        with session_scope() as s:
            project = projects_repo.get_by_slug(s, user_id, slug)
            cover_orm = covers_repo.get_or_create(s, project)
            covers_repo.update_illustration_key(s, cover_orm, cover_key)

        return GenerateCoverOut(ok=True, detail="Cover generata")
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost, reason=f"Refund cover Pro: {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502, detail=f"Errore generazione cover: {str(e)[:200]}"
        )
    finally:
        for p in tmp_refs:
            try:
                p.unlink()
            except OSError:
                pass


@router.delete("/{slug}/cover", status_code=status.HTTP_204_NO_CONTENT)
def delete_pro_cover(slug: str, user: dict = Depends(require_user)) -> None:
    """Elimina la cover illustrata (per rigenerarla). Non tocca i metadata."""
    from db.repos import covers as covers_repo
    from storage.client import delete_object, object_exists
    from storage.keys import cover_illustration_key

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        key = cover_illustration_key(project.id)
        if object_exists(key):
            delete_object(key)
        cover_orm = project.cover
        if cover_orm is not None:
            covers_repo.update_illustration_key(s, cover_orm, None)


@router.get("/{slug}/cover-image")
def get_pro_cover_image(
    slug: str, user: dict = Depends(require_user)
):
    """Ritorna i bytes della cover Pro per preview nel frontend."""
    from fastapi.responses import Response as FastAPIResponse
    from storage.client import download_bytes, object_exists
    from storage.keys import cover_illustration_key

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        key = cover_illustration_key(project.id)

    if not object_exists(key):
        raise HTTPException(status_code=404, detail="Cover non generata")
    return FastAPIResponse(
        content=download_bytes(key), media_type="image/png"
    )


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
