"""Endpoint Esplora: asset pubblici (copertine, tavole, personaggi) + gestione admin.

Pubblici (no auth):
  GET  /api/esplora/assets                → asset attivi raggruppati per sezione
  GET  /api/esplora/assets/{id}/image     → bytes immagine

Admin (require_admin):
  GET    /api/admin/esplora/assets               → tutti gli asset (incl. inattivi)
  POST   /api/admin/esplora/assets               → crea asset (metadati)
  PATCH  /api/admin/esplora/assets/{id}          → aggiorna metadati
  DELETE /api/admin/esplora/assets/{id}          → elimina asset + immagine
  POST   /api/admin/esplora/assets/{id}/upload   → carica immagine (multipart)
  POST   /api/admin/esplora/assets/{id}/generate → genera/rigenera immagine (AI)
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from api.routers.admin import require_admin
from db.base import utcnow
from db.models import EsploraAsset
from db.session import session_scope
from storage import keys as storage_keys
from storage.client import delete_object, download_bytes, upload_bytes

public_router = APIRouter()
admin_router = APIRouter()


# ============================================================
# Config sezioni
# ============================================================

# key → (label UI, size image-gen valido per gpt-image, aspect-ratio CSS)
SECTIONS: dict[str, dict] = {
    "copertine": {"label": "Copertine", "size": "1024x1536", "aspect": "3 / 4"},
    "tavole": {"label": "Tavole", "size": "1536x1024", "aspect": "4 / 3"},
    "personaggi": {"label": "Personaggi", "size": "1024x1024", "aspect": "1 / 1"},
}


# ============================================================
# Schemas
# ============================================================


class EsploraAssetOut(BaseModel):
    id: str
    section: str
    asset_type: str
    title: str
    caption: str
    author_name: str
    author_role: str
    position: int
    has_image: bool
    image_url: Optional[str] = None
    prompt: str
    is_active: bool


class CreateAssetIn(BaseModel):
    section: str
    asset_type: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=255)
    caption: str = Field(default="", max_length=500)
    author_name: str = Field(default="", max_length=160)
    author_role: str = Field(default="", max_length=80)
    position: Optional[int] = None


class UpdateAssetIn(BaseModel):
    asset_type: Optional[str] = Field(default=None, max_length=120)
    title: Optional[str] = Field(default=None, max_length=255)
    caption: Optional[str] = Field(default=None, max_length=500)
    author_name: Optional[str] = Field(default=None, max_length=160)
    author_role: Optional[str] = Field(default=None, max_length=80)
    position: Optional[int] = None
    is_active: Optional[bool] = None


class GenerateAssetIn(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=4000)
    quality: str = "medium"


# ============================================================
# Helpers
# ============================================================


def _to_out(a: EsploraAsset, *, admin: bool = False) -> EsploraAssetOut:
    has_image = bool(a.storage_key)
    image_url = None
    if has_image:
        ts = int(a.updated_at.timestamp()) if a.updated_at else 0
        base = "/api/admin/esplora/assets" if admin else "/api/esplora/assets"
        image_url = f"{base}/{a.id}/image?v={ts}"
    return EsploraAssetOut(
        id=str(a.id),
        section=a.section,
        asset_type=a.asset_type,
        title=a.title,
        caption=a.caption,
        author_name=a.author_name,
        author_role=a.author_role,
        position=a.position,
        has_image=has_image,
        image_url=image_url,
        prompt=a.prompt,
        is_active=a.is_active,
    )


def _grouped(rows: list[EsploraAsset], *, admin: bool = False) -> dict:
    buckets: dict[str, list[EsploraAssetOut]] = {k: [] for k in SECTIONS}
    for a in rows:
        if a.section in buckets:
            buckets[a.section].append(_to_out(a, admin=admin))
    return {
        "sections": [
            {
                "key": k,
                "label": SECTIONS[k]["label"],
                "aspect": SECTIONS[k]["aspect"],
                "items": buckets[k],
            }
            for k in SECTIONS
        ]
    }


def _get_or_404(s, asset_id: str) -> EsploraAsset:
    try:
        aid = uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    a = s.get(EsploraAsset, aid)
    if a is None:
        raise HTTPException(status_code=404, detail="Asset non trovato")
    return a


# ============================================================
# Endpoint pubblici
# ============================================================


@public_router.get("/assets")
def list_public_assets() -> dict:
    from db.repos import cast_archive as cast_archive_repo
    from db.repos import users as users_repo

    with session_scope() as s:
        rows = (
            s.execute(
                select(EsploraAsset)
                .where(EsploraAsset.is_active.is_(True))
                .order_by(EsploraAsset.section, EsploraAsset.position)
            )
            .scalars()
            .all()
        )
        result = _grouped(rows)

        # Append i personaggi utenti pubblicati alla sezione "personaggi"
        shared = cast_archive_repo.list_published_shares(s)
        if shared:
            for section in result["sections"]:
                if section["key"] != "personaggi":
                    continue
                for entry in shared:
                    owner = users_repo.get_by_id(s, entry.user_id)
                    author_name = ""
                    if owner and owner.email:
                        # Fallback amichevole: parte prima della @ dell'email
                        author_name = owner.email.split("@")[0]
                    ts = 0
                    if entry.share_moderated_at:
                        ts = int(entry.share_moderated_at.timestamp())
                    section["items"].append(
                        EsploraAssetOut(
                            id=str(entry.id),
                            section="personaggi",
                            asset_type="COMMUNITY",
                            title=entry.name,
                            caption=entry.share_caption or "",
                            author_name=author_name,
                            author_role=entry.share_author_role or "",
                            position=9999,
                            has_image=True,
                            image_url=f"/api/esplora/user-characters/{entry.id}/image?v={ts}",
                            prompt="",
                            is_active=True,
                        )
                    )

        # Append cover + tavole community pubblicate
        from db.repos import project_asset_shares as shares_repo

        for kind, section_key in (("cover", "copertine"), ("tavola", "tavole")):
            published = shares_repo.list_published_by_kind(s, kind)
            if not published:
                continue
            for section in result["sections"]:
                if section["key"] != section_key:
                    continue
                for share in published:
                    owner = users_repo.get_by_id(s, share.user_id)
                    author_name = ""
                    if owner and owner.email:
                        author_name = owner.email.split("@")[0]
                    ts = 0
                    if share.share_moderated_at:
                        ts = int(share.share_moderated_at.timestamp())
                    title = share.project_title or ""
                    if kind == "tavola" and share.page_number:
                        title = f"{title} — Pagina {share.page_number}" if title else f"Pagina {share.page_number}"
                    section["items"].append(
                        EsploraAssetOut(
                            id=str(share.id),
                            section=section_key,
                            asset_type="COMMUNITY",
                            title=title,
                            caption=share.share_caption or "",
                            author_name=author_name,
                            author_role=share.share_author_role or "",
                            position=9999,
                            has_image=True,
                            image_url=f"/api/esplora/project-shares/{share.id}/image?v={ts}",
                            prompt="",
                            is_active=True,
                        )
                    )
        return result


@public_router.get("/project-shares/{share_id}/image")
def get_project_share_image_public(share_id: str) -> Response:
    """Serve cover/tavola pubblicata di un progetto utente."""
    from db.repos import project_asset_shares as shares_repo

    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        share = shares_repo.get_by_id(s, sid)
        if share is None or share.share_status != "published":
            raise HTTPException(status_code=404, detail="Non trovato")
        key = share.storage_key

    if not key:
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    return _serve_image(key)


@public_router.get("/user-characters/{entry_id}/image")
def get_user_character_image(entry_id: str) -> Response:
    """Serve la reference di un personaggio-utente pubblicato su /esplora.

    Verifica share_status='published' — le entry pending/rejected/not_shared
    non sono accessibili anche se qualcuno indovina l'URL.
    """
    from db.repos import cast_archive as cast_archive_repo

    with session_scope() as s:
        entry = cast_archive_repo.get_shared_by_id(s, entry_id)
        if entry is None or entry.share_status != "published":
            raise HTTPException(status_code=404, detail="Non trovato")
        if not entry.reference_storage_key:
            raise HTTPException(status_code=404, detail="Immagine non trovata")
        key = entry.reference_storage_key
    return _serve_image(key)


def _detect_media_type(data: bytes) -> str:
    """Riconosce il formato dai magic bytes: gli asset possono essere WebP
    (upload ottimizzati) o PNG (generati AI / vecchi upload)."""
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return "image/png"


def _serve_image(key: str | None) -> Response:
    if not key:
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    try:
        data = download_bytes(key)
    except Exception:
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    return Response(
        content=data,
        media_type=_detect_media_type(data),
        headers={"Cache-Control": "public, max-age=300"},
    )


@public_router.get("/assets/{asset_id}/image")
def get_asset_image(asset_id: str) -> Response:
    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        # Asset nascosti (is_active=False) non sono accessibili pubblicamente,
        # nemmeno via URL diretto noto.
        if not a.is_active:
            raise HTTPException(status_code=404, detail="Immagine non trovata")
        key = a.storage_key
    return _serve_image(key)


# ============================================================
# Endpoint admin
# ============================================================


@admin_router.get("/assets")
def list_admin_assets(admin: dict = Depends(require_admin)) -> dict:
    with session_scope() as s:
        rows = (
            s.execute(
                select(EsploraAsset).order_by(
                    EsploraAsset.section, EsploraAsset.position
                )
            )
            .scalars()
            .all()
        )
        return _grouped(rows, admin=True)


@admin_router.get("/assets/{asset_id}/image")
def get_admin_asset_image(
    asset_id: str, admin: dict = Depends(require_admin)
) -> Response:
    """Serve l'immagine anche per asset nascosti (anteprima admin)."""
    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        key = a.storage_key
    return _serve_image(key)


@admin_router.post("/assets", response_model=EsploraAssetOut, status_code=201)
def create_asset(
    payload: CreateAssetIn, admin: dict = Depends(require_admin)
) -> EsploraAssetOut:
    if payload.section not in SECTIONS:
        raise HTTPException(status_code=400, detail=f"Sezione invalida: {payload.section}")
    with session_scope() as s:
        if payload.position is None:
            maxpos = s.execute(
                select(func.max(EsploraAsset.position)).where(
                    EsploraAsset.section == payload.section
                )
            ).scalar()
            pos = (maxpos or 0) + 1
        else:
            pos = payload.position
        a = EsploraAsset(
            section=payload.section,
            asset_type=payload.asset_type,
            title=payload.title,
            caption=payload.caption,
            author_name=payload.author_name,
            author_role=payload.author_role,
            position=pos,
        )
        s.add(a)
        s.flush()
        return _to_out(a, admin=True)


@admin_router.patch("/assets/{asset_id}", response_model=EsploraAssetOut)
def update_asset(
    asset_id: str, payload: UpdateAssetIn, admin: dict = Depends(require_admin)
) -> EsploraAssetOut:
    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        if payload.asset_type is not None:
            a.asset_type = payload.asset_type
        if payload.title is not None:
            a.title = payload.title
        if payload.caption is not None:
            a.caption = payload.caption
        if payload.author_name is not None:
            a.author_name = payload.author_name
        if payload.author_role is not None:
            a.author_role = payload.author_role
        if payload.position is not None:
            a.position = payload.position
        if payload.is_active is not None:
            a.is_active = payload.is_active
        s.flush()
        return _to_out(a, admin=True)


@admin_router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str, admin: dict = Depends(require_admin)) -> Response:
    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        key = a.storage_key
        s.delete(a)
    if key:
        delete_object(key)
    return Response(status_code=204)


@admin_router.post("/assets/{asset_id}/upload", response_model=EsploraAssetOut)
async def upload_asset_image(
    asset_id: str,
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin),
) -> EsploraAssetOut:
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Il file deve essere un'immagine")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    # Ottimizzazione: qualsiasi upload (PNG/JPEG/...) viene convertito in WebP,
    # mantenendo le stesse dimensioni in pixel ma con un file molto più leggero.
    from io import BytesIO

    from PIL import Image

    try:
        img = Image.open(BytesIO(raw))
        has_alpha = img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        )
        img = img.convert("RGBA" if has_alpha else "RGB")
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=85, method=6)
        data = buf.getvalue()
        content_type = "image/webp"
    except Exception:
        raise HTTPException(status_code=400, detail="Immagine non valida o corrotta")
    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        key = storage_keys.esplora_asset_key(a.section, a.id)
        upload_bytes(key, data, content_type=content_type)
        a.storage_key = key
        a.updated_at = utcnow()  # forza cache-bust anche se la key è invariata
        s.flush()
        return _to_out(a, admin=True)


@admin_router.post("/assets/{asset_id}/generate", response_model=EsploraAssetOut)
def generate_asset_image(
    asset_id: str, payload: GenerateAssetIn, admin: dict = Depends(require_admin)
) -> EsploraAssetOut:
    from snaptoon_core.generator import get_generator

    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        section = a.section
        asset_pk = a.id
    size = SECTIONS.get(section, {}).get("size", "1024x1024")
    quality = payload.quality if payload.quality in ("low", "medium", "high", "auto") else "medium"

    gen = get_generator()
    try:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.png"
            gen.generate(
                payload.prompt,
                out,
                size=size,
                use_cache=False,
                quality=quality,
            )
            data = out.read_bytes()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Generazione fallita: {e}")

    with session_scope() as s:
        a = _get_or_404(s, asset_id)
        key = storage_keys.esplora_asset_key(a.section, asset_pk)
        upload_bytes(key, data, content_type="image/png")
        a.storage_key = key
        a.prompt = payload.prompt
        a.updated_at = utcnow()
        s.flush()
        return _to_out(a, admin=True)


# ============================================================
# Moderazione "Personaggi condivisi dagli utenti"
#
# Gli utenti condividono i loro personaggi dall'area "I miei personaggi"
# (POST /api/my-characters/{id}/share). Le entry con share_status='pending'
# appaiono qui in admin per approvazione / rifiuto.
# ============================================================


class SharedCharacterAdminOut(BaseModel):
    id: str
    name: str
    visual_description: str
    author_name: str
    author_email: str
    author_role: str
    caption: str
    submitted_at: Optional[str]
    moderated_at: Optional[str]
    rejection_reason: str
    share_status: str
    image_url: str


class RejectSharedCharacterIn(BaseModel):
    reason: str = Field(default="", max_length=1000)


def _shared_char_to_out(entry, owner) -> SharedCharacterAdminOut:
    author_name = ""
    author_email = ""
    if owner and owner.email:
        author_email = owner.email
        author_name = owner.email.split("@")[0]
    return SharedCharacterAdminOut(
        id=str(entry.id),
        name=entry.name,
        visual_description=entry.visual_description,
        author_name=author_name,
        author_email=author_email,
        author_role=entry.share_author_role or "",
        caption=entry.share_caption or "",
        submitted_at=(
            entry.share_submitted_at.isoformat() if entry.share_submitted_at else None
        ),
        moderated_at=(
            entry.share_moderated_at.isoformat() if entry.share_moderated_at else None
        ),
        rejection_reason=entry.share_rejection_reason or "",
        share_status=entry.share_status,
        image_url=f"/api/admin/esplora/user-characters/{entry.id}/image",
    )


@admin_router.get("/user-characters", response_model=list[SharedCharacterAdminOut])
def list_shared_user_characters(
    status_filter: str = "pending", admin: dict = Depends(require_admin)
) -> list[SharedCharacterAdminOut]:
    """Lista personaggi condivisi dagli utenti per moderazione.

    status_filter: "pending" (default) | "published" | "rejected" | "all"
    """
    from db.repos import cast_archive as cast_archive_repo
    from db.repos import users as users_repo
    from db.models import CastArchiveEntry

    with session_scope() as s:
        if status_filter == "pending":
            entries = cast_archive_repo.list_pending_shares(s)
        elif status_filter == "published":
            entries = cast_archive_repo.list_published_shares(s)
        else:
            from sqlalchemy import select as _select

            stmt = (
                _select(CastArchiveEntry)
                .where(CastArchiveEntry.share_status != "not_shared")
                .where(CastArchiveEntry.deleted_at.is_(None))
                .order_by(CastArchiveEntry.share_submitted_at.desc())
            )
            entries = list(s.execute(stmt).scalars())

        out = []
        for entry in entries:
            owner = users_repo.get_by_id(s, entry.user_id)
            out.append(_shared_char_to_out(entry, owner))
        return out


@admin_router.get("/user-characters/{entry_id}/image")
def admin_get_user_character_image(
    entry_id: str, admin: dict = Depends(require_admin)
) -> Response:
    from db.repos import cast_archive as cast_archive_repo

    with session_scope() as s:
        entry = cast_archive_repo.get_shared_by_id(s, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        if not entry.reference_storage_key:
            raise HTTPException(status_code=404, detail="Immagine non trovata")
        key = entry.reference_storage_key
    return _serve_image(key)


@admin_router.post(
    "/user-characters/{entry_id}/approve",
    response_model=SharedCharacterAdminOut,
)
def approve_shared_character(
    entry_id: str, admin: dict = Depends(require_admin)
) -> SharedCharacterAdminOut:
    from db.repos import cast_archive as cast_archive_repo
    from db.repos import users as users_repo

    with session_scope() as s:
        entry = cast_archive_repo.get_shared_by_id(s, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        cast_archive_repo.approve_sharing(s, entry)
        owner = users_repo.get_by_id(s, entry.user_id)
        return _shared_char_to_out(entry, owner)


@admin_router.post(
    "/user-characters/{entry_id}/reject",
    response_model=SharedCharacterAdminOut,
)
def reject_shared_character(
    entry_id: str,
    payload: RejectSharedCharacterIn,
    admin: dict = Depends(require_admin),
) -> SharedCharacterAdminOut:
    from db.repos import cast_archive as cast_archive_repo
    from db.repos import users as users_repo

    with session_scope() as s:
        entry = cast_archive_repo.get_shared_by_id(s, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        cast_archive_repo.reject_sharing(s, entry, reason=payload.reason)
        owner = users_repo.get_by_id(s, entry.user_id)
        return _shared_char_to_out(entry, owner)
