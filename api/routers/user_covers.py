"""Endpoint 'Le mie Cover' — cover standalone create dall'utente.

Riusa lo STESSO prompt delle copertine dei libretti KIDS
(snaptoon_core.kids_pipeline.build_cover_prompt). L'utente non deve
avere un libretto: sceglie titolo/sottotitolo/autore, stile e un cast
opzionale (dal Cast Archive → 'I miei Personaggi'). Genera, vede il
risultato, può rigenerare o pubblicare sul BookShop.

Costi:
  - Creazione cover (prima generazione)   = costo generate_panel * qualità utente
  - Rigenerazione                          = stesso costo
  - Modifica metadata / publish / delete   = 0 crediti
"""
from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from api.routers.admin import require_admin
from api.routers.auth import require_user
from api.utils.quality import cost_for_generation, resolve_user_quality
from db.models import CreditOperation
from db.repos import bookshop_categories as bookshop_repo
from db.repos import cast_archive as cast_archive_repo
from db.repos import credits as credits_repo
from db.repos import users as users_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from snaptoon_core.kids_pipeline import build_cover_prompt
from storage.client import (
    delete_object,
    download_bytes,
    object_exists,
    upload_bytes,
)
from storage.keys import user_cover_rendered_key

logger = logging.getLogger(__name__)

router = APIRouter()
admin_router = APIRouter()
public_router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class CoverCharacterIn(BaseModel):
    """Personaggio inserito nella cover.

    Se my_character_id è fornito → uso la reference AI già generata di
    quel personaggio del Cast Archive (coerenza visiva).
    Altrimenti uso nome+descrizione grezzi (nessun reference).
    """

    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=1000)
    my_character_id: Optional[str] = None


class CoverCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    subtitle: str = Field(default="", max_length=200)
    author: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=1000)  # logline SFX
    style_preset_id: str = Field(..., min_length=1, max_length=120)
    characters: list[CoverCharacterIn] = Field(default_factory=list, max_length=6)


class CoverUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    subtitle: Optional[str] = Field(default=None, max_length=200)
    author: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)


class CoverOut(BaseModel):
    id: str
    title: str
    subtitle: str
    author: str
    description: str
    style_preset_id: str
    author_display: str
    cast_snapshot: list[dict]
    has_image: bool
    moderation_status: str
    rejection_reason: str
    bookshop_category_id: Optional[str] = None
    created_at: str


class CoversListOut(BaseModel):
    covers: list[CoverOut]


class PublishIn(BaseModel):
    category_id: str


# ============================================================
# Helpers
# ============================================================


def _to_out(cover) -> CoverOut:
    return CoverOut(
        id=str(cover.id),
        title=cover.title,
        subtitle=cover.subtitle or "",
        author=cover.author or "",
        description=cover.description or "",
        style_preset_id=cover.style_preset_id,
        author_display=cover.author_display or "",
        cast_snapshot=list(cover.cast_snapshot or []),
        has_image=bool(cover.rendered_image_key),
        moderation_status=cover.moderation_status,
        rejection_reason=cover.rejection_reason or "",
        bookshop_category_id=(
            str(cover.bookshop_category_id) if cover.bookshop_category_id else None
        ),
        created_at=cover.created_at.isoformat() if cover.created_at else "",
    )


def _resolve_cast(session, u, characters_in: list[CoverCharacterIn]) -> tuple[list[dict], list[Path]]:
    """Restituisce (cast_snapshot, tmp_reference_paths).

    cast_snapshot: usato sia per il prompt sia per il salvataggio in DB.
    tmp_reference_paths: file temporanei da passare a OpenAI come reference.
    Il chiamante DEVE cancellarli in finally.
    """
    snapshot: list[dict] = []
    tmp_refs: list[Path] = []
    for ch in characters_in:
        item: dict = {
            "name": ch.name.strip(),
            "description": ch.description.strip(),
        }
        # Se my_character_id è dato, cerchiamo la reference del Cast Archive
        if ch.my_character_id:
            try:
                mc_uuid = uuid.UUID(ch.my_character_id)
            except ValueError:
                mc_uuid = None
            if mc_uuid is not None:
                entry = cast_archive_repo.get_by_id(session, u, mc_uuid)
                if (
                    entry is not None
                    and entry.reference_storage_key
                    and object_exists(entry.reference_storage_key)
                ):
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp.write(download_bytes(entry.reference_storage_key))
                    tmp.close()
                    tmp_refs.append(Path(tmp.name))
                    item["id"] = str(entry.id)
                    # Uso la description AI curata del Cast Archive se
                    # l'utente non ne ha inserita una diversa
                    if not item["description"]:
                        item["description"] = entry.visual_description
        snapshot.append(item)
    return snapshot, tmp_refs


def _generate_cover_image(
    cover_id: uuid.UUID,
    title: str,
    subtitle: str,
    author: str,
    description: str,
    style_preset_id: str,
    cast: list[dict],
    tmp_refs: list[Path],
    quality: str,
) -> str:
    """Genera la PNG e la carica su storage. Ritorna lo storage key."""
    from snaptoon_core.generator import OpenAIImageGenerator

    generator = OpenAIImageGenerator()
    prompt = build_cover_prompt(
        title=title,
        cast=cast,
        style_preset_id=style_preset_id,
        story_description=description,
        volume_number=1,
    )
    # Nota: il prompt canonico usa "Draw the main title '<title>'" e
    # non include sottotitolo/autore embedded (il libretto li ha nella
    # 4a di copertina/pagine interne). L'utente ha chiesto "funzione
    # identica ai libretti", quindi teniamo lo stesso prompt canonico.
    img_bytes = generator._generate_bytes(
        prompt=prompt,
        size="1024x1536",  # 2:3 verticale, come cover libretto
        reference_images=tmp_refs if tmp_refs else None,
        quality=quality,
    )
    storage_key = user_cover_rendered_key(cover_id)
    upload_bytes(storage_key, img_bytes, content_type="image/png")
    return storage_key


# ============================================================
# Endpoints utente
# ============================================================


@router.post("", response_model=CoverOut, status_code=status.HTTP_201_CREATED)
def create_cover(
    payload: CoverCreateIn, user: dict = Depends(require_user)
) -> CoverOut:
    """Crea una nuova cover: charge + generate + save."""
    from db.models import UserCover

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        user_quality = resolve_user_quality(u)
        author_display = (u.pseudonym or u.email.split("@")[0] or "").strip()

        # 1. Charge
        cost = cost_for_generation("generate_panel", user_quality)
        try:
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_cover,
                reason=f"Cover standalone «{payload.title}»",
            )
        except InsufficientCreditsError as e:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Crediti insufficienti: servono {e.required}, "
                    f"ne hai {e.available}"
                ),
            )

        # 2. Crea il record DB PRIMA della generazione (ci serve l'id
        #    per lo storage key)
        cover = UserCover(
            user_id=user_id,
            title=payload.title.strip(),
            subtitle=payload.subtitle.strip(),
            author=payload.author.strip(),
            description=payload.description.strip(),
            style_preset_id=payload.style_preset_id.strip(),
            author_display=author_display,
            cast_snapshot=[],  # popolato dopo
        )
        s.add(cover)
        s.flush()  # assegna cover.id
        cover_id = cover.id

        # 3. Risolve cast + reference paths
        cast_snapshot, tmp_refs = _resolve_cast(s, u, payload.characters)
        cover.cast_snapshot = cast_snapshot

    # 4. Genera fuori dalla session (chiamata OpenAI = lenta)
    try:
        storage_key = _generate_cover_image(
            cover_id=cover_id,
            title=payload.title.strip(),
            subtitle=payload.subtitle.strip(),
            author=payload.author.strip(),
            description=payload.description.strip(),
            style_preset_id=payload.style_preset_id.strip(),
            cast=cast_snapshot,
            tmp_refs=tmp_refs,
            quality=user_quality,
        )
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund cover «{payload.title}»: {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502, detail=f"Errore generazione cover: {str(e)[:300]}"
        )
    finally:
        for p in tmp_refs:
            try:
                p.unlink()
            except OSError:
                pass

    # 5. Salva lo storage_key
    with session_scope() as s:
        cov = s.get(UserCover, cover_id)
        cov.rendered_image_key = storage_key
        return _to_out(cov)


@router.get("/mine", response_model=CoversListOut)
def list_my_covers(user: dict = Depends(require_user)) -> CoversListOut:
    from db.models import UserCover
    from sqlalchemy import select

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        stmt = (
            select(UserCover)
            .where(UserCover.user_id == user_id)
            .where(UserCover.deleted_at.is_(None))
            .order_by(UserCover.created_at.desc())
        )
        covers = list(s.execute(stmt).scalars())
        return CoversListOut(covers=[_to_out(c) for c in covers])


@router.get("/{cover_id}/image")
def get_cover_image(
    cover_id: str, user: dict = Depends(require_user)
) -> Response:
    from db.models import UserCover

    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None or cov.user_id != user_id or cov.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        if not cov.rendered_image_key or not object_exists(cov.rendered_image_key):
            raise HTTPException(status_code=404, detail="Immagine non disponibile")
        data = download_bytes(cov.rendered_image_key)
        return Response(content=data, media_type="image/png")


@router.patch("/{cover_id}", response_model=CoverOut)
def update_cover(
    cover_id: str,
    payload: CoverUpdateIn,
    user: dict = Depends(require_user),
) -> CoverOut:
    """Modifica metadata (senza rigenerare l'immagine)."""
    from db.models import UserCover

    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None or cov.user_id != user_id or cov.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        if payload.title is not None:
            cov.title = payload.title.strip()[:120]
        if payload.subtitle is not None:
            cov.subtitle = payload.subtitle.strip()[:200]
        if payload.author is not None:
            cov.author = payload.author.strip()[:120]
        if payload.description is not None:
            cov.description = payload.description.strip()[:1000]
        return _to_out(cov)


@router.post("/{cover_id}/regenerate", response_model=CoverOut)
def regenerate_cover(
    cover_id: str, user: dict = Depends(require_user)
) -> CoverOut:
    """Rigenera l'immagine usando i metadata + cast_snapshot correnti."""
    from db.models import UserCover

    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")

    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None or cov.user_id != user_id or cov.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        u = users_repo.get_by_id(s, user_id)
        user_quality = resolve_user_quality(u)
        cost = cost_for_generation("generate_panel", user_quality)
        try:
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_cover,
                reason=f"Regen cover «{cov.title}»",
            )
        except InsufficientCreditsError as e:
            raise HTTPException(
                status_code=402,
                detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
            )

        # Reference paths dal cast_snapshot
        cast = list(cov.cast_snapshot or [])
        tmp_refs: list[Path] = []
        for ch in cast:
            ch_id = ch.get("id")
            if not ch_id:
                continue
            try:
                mc_uuid = uuid.UUID(ch_id)
            except (ValueError, TypeError):
                continue
            entry = cast_archive_repo.get_by_id(s, u, mc_uuid)
            if (
                entry is not None
                and entry.reference_storage_key
                and object_exists(entry.reference_storage_key)
            ):
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(download_bytes(entry.reference_storage_key))
                tmp.close()
                tmp_refs.append(Path(tmp.name))

        snapshot_title = cov.title
        snapshot_subtitle = cov.subtitle
        snapshot_author = cov.author
        snapshot_description = cov.description
        snapshot_style = cov.style_preset_id

    try:
        storage_key = _generate_cover_image(
            cover_id=cid,
            title=snapshot_title,
            subtitle=snapshot_subtitle,
            author=snapshot_author,
            description=snapshot_description,
            style_preset_id=snapshot_style,
            cast=cast,
            tmp_refs=tmp_refs,
            quality=user_quality,
        )
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund regen cover «{snapshot_title}»: {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502, detail=f"Errore generazione: {str(e)[:300]}"
        )
    finally:
        for p in tmp_refs:
            try:
                p.unlink()
            except OSError:
                pass

    with session_scope() as s:
        cov = s.get(UserCover, cid)
        cov.rendered_image_key = storage_key
        # Reset moderation se era pending/rejected — la nuova immagine
        # richiede una nuova approvazione se poi verrà pubblicata
        if cov.moderation_status in ("pending", "rejected"):
            cov.moderation_status = "draft"
            cov.rejection_reason = ""
        return _to_out(cov)


@router.post("/{cover_id}/publish", response_model=CoverOut)
def publish_cover(
    cover_id: str,
    payload: PublishIn,
    user: dict = Depends(require_user),
) -> CoverOut:
    """Sottomette la cover a moderazione con una categoria BookShop."""
    from db.models import UserCover
    from datetime import datetime, timezone

    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(cover_id)
        cat_id = uuid.UUID(payload.category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None or cov.user_id != user_id or cov.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        if not cov.rendered_image_key:
            raise HTTPException(
                status_code=400,
                detail="La cover non ha ancora un'immagine generata.",
            )
        cat = bookshop_repo.get_by_id(s, cat_id)
        if cat is None or cat.deleted_at is not None or not cat.is_active:
            raise HTTPException(status_code=400, detail="Categoria non valida")
        cov.bookshop_category_id = cat_id
        cov.moderation_status = "pending"
        cov.submitted_at = datetime.now(timezone.utc)
        cov.rejection_reason = ""
        return _to_out(cov)


@router.post("/{cover_id}/unpublish", response_model=CoverOut)
def unpublish_cover(
    cover_id: str, user: dict = Depends(require_user)
) -> CoverOut:
    from db.models import UserCover

    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None or cov.user_id != user_id or cov.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        cov.moderation_status = "draft"
        cov.bookshop_category_id = None
        cov.submitted_at = None
        return _to_out(cov)


@router.delete("/{cover_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cover(cover_id: str, user: dict = Depends(require_user)) -> None:
    from db.models import UserCover
    from datetime import datetime, timezone

    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None or cov.user_id != user_id:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        if cov.rendered_image_key and object_exists(cov.rendered_image_key):
            try:
                delete_object(cov.rendered_image_key)
            except Exception as e:
                logger.warning("Delete cover storage fallito: %s", e)
        cov.deleted_at = datetime.now(timezone.utc)
        cov.rendered_image_key = None


# ============================================================
# Endpoints pubblici (BookShop)
# ============================================================


@public_router.get("/{cover_id}/image")
def get_public_cover_image(cover_id: str) -> Response:
    from db.models import UserCover

    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if (
            cov is None
            or cov.deleted_at is not None
            or cov.moderation_status != "published"
            or not cov.rendered_image_key
            or not object_exists(cov.rendered_image_key)
        ):
            raise HTTPException(status_code=404, detail="Cover non trovata")
        data = download_bytes(cov.rendered_image_key)
        return Response(content=data, media_type="image/png")


# ============================================================
# Endpoints admin
# ============================================================


@admin_router.get("", response_model=CoversListOut)
def admin_list_covers(
    _: dict = Depends(require_admin),
    status_filter: Optional[str] = None,
) -> CoversListOut:
    from db.models import UserCover
    from sqlalchemy import select

    with session_scope() as s:
        stmt = (
            select(UserCover)
            .where(UserCover.deleted_at.is_(None))
            .order_by(UserCover.created_at.desc())
        )
        if status_filter:
            stmt = stmt.where(UserCover.moderation_status == status_filter)
        covers = list(s.execute(stmt).scalars())
        return CoversListOut(covers=[_to_out(c) for c in covers])


@admin_router.post("/{cover_id}/approve", response_model=CoverOut)
def admin_approve_cover(
    cover_id: str, _: dict = Depends(require_admin)
) -> CoverOut:
    from db.models import UserCover
    from datetime import datetime, timezone

    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        cov.moderation_status = "published"
        cov.moderated_at = datetime.now(timezone.utc)
        cov.rejection_reason = ""
        return _to_out(cov)


class AdminRejectIn(BaseModel):
    reason: str = Field(..., max_length=500)


@admin_router.post("/{cover_id}/reject", response_model=CoverOut)
def admin_reject_cover(
    cover_id: str,
    payload: AdminRejectIn,
    _: dict = Depends(require_admin),
) -> CoverOut:
    from db.models import UserCover
    from datetime import datetime, timezone

    try:
        cid = uuid.UUID(cover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID cover invalido")
    with session_scope() as s:
        cov = s.get(UserCover, cid)
        if cov is None:
            raise HTTPException(status_code=404, detail="Cover non trovata")
        cov.moderation_status = "rejected"
        cov.rejection_reason = payload.reason.strip()[:500]
        cov.moderated_at = datetime.now(timezone.utc)
        return _to_out(cov)
