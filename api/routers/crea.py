"""Endpoint CREA: immagini della pagina pubblica /crea + gestione admin.

La pagina /crea mostra 6 immagini a slot fisso (hero + 5 step del workflow).
Di default sono file statici in web/public/images/crea/; l'admin può
sovrascriverle caricando un'immagine (convertita in WebP, come Esplora).

Pubblici (no auth):
  GET  /api/crea/images               → lista slot con image_url (o null)
  GET  /api/crea/images/{slot}/image  → bytes immagine caricata

Admin (require_admin):
  GET    /api/admin/crea/images                → lista slot (anteprima admin)
  GET    /api/admin/crea/images/{slot}/image   → bytes immagine caricata
  POST   /api/admin/crea/images/{slot}/upload  → carica/sostituisce immagine
  DELETE /api/admin/crea/images/{slot}         → rimuove upload (torna al default)
"""
from __future__ import annotations

from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select

from api.routers.admin import require_admin
from api.routers.esplora import _detect_media_type, _serve_image
from db.base import utcnow
from db.models import CreaImage
from db.session import session_scope
from storage import keys as storage_keys
from storage.client import delete_object, upload_bytes

public_router = APIRouter()
admin_router = APIRouter()


# ============================================================
# Config slot (fissi, in ordine di apparizione sulla pagina)
# ============================================================

# slot → (label UI, aspect-ratio CSS, path statico di default, sezione).
# La "section" serve solo all'admin per raggruppare visivamente:
#   "autori" → 6 slot della pagina /crea (ex-Crea, ora "Autori")
#   "kids"   → 7 slot della pagina /kids showcase pubblica
SLOTS: dict[str, dict] = {
    # === Autori (/crea) ===
    "dashboard": {
        "label": "Dashboard · I miei progetti",
        "aspect": "4 / 3",
        "default": "/images/crea/dashboard.png",
        "section": "autori",
    },
    "step-testo": {
        "label": "Pagina /testo · script generato",
        "aspect": "4 / 3",
        "default": "/images/crea/step-testo.png",
        "section": "autori",
    },
    "step-stile": {
        "label": "Griglia stili",
        "aspect": "4 / 3",
        "default": "/images/crea/step-stile.png",
        "section": "autori",
    },
    "step-personaggi": {
        "label": "Card personaggio · reference image",
        "aspect": "4 / 3",
        "default": "/images/crea/step-personaggi.png",
        "section": "autori",
    },
    "step-genera": {
        "label": "Pagina /genera · scene selector",
        "aspect": "4 / 3",
        "default": "/images/crea/step-genera.png",
        "section": "autori",
    },
    "step-impagina": {
        "label": "Pagina completa renderizzata",
        "aspect": "4 / 3",
        "default": "/images/crea/step-impagina.png",
        "section": "autori",
    },
    # === Kids (/kids) ===
    "kids-hero": {
        "label": "Hero · wizard KIDS + anteprima",
        "aspect": "4 / 3",
        "default": "/images/kids/hero.png",
        "section": "kids",
    },
    "kids-step-1": {
        "label": "1. Il tuo stile (13 stili + 6 ritmi)",
        "aspect": "4 / 3",
        "default": "/images/kids/step-1-stile.png",
        "section": "kids",
    },
    "kids-step-2": {
        "label": "2. La scintilla (titolo + storia)",
        "aspect": "4 / 3",
        "default": "/images/kids/step-2-storia.png",
        "section": "kids",
    },
    "kids-step-3": {
        "label": "3. I personaggi (foto + archivio)",
        "aspect": "4 / 3",
        "default": "/images/kids/step-3-personaggi.png",
        "section": "kids",
    },
    "kids-step-4": {
        "label": "4. La copertina (badge fumetto)",
        "aspect": "4 / 3",
        "default": "/images/kids/step-4-copertina.png",
        "section": "kids",
    },
    "kids-step-5": {
        "label": "5. Le vignette (rigenera singola)",
        "aspect": "4 / 3",
        "default": "/images/kids/step-5-vignette.png",
        "section": "kids",
    },
    "kids-step-6": {
        "label": "6. Il libretto (PDF + community)",
        "aspect": "4 / 3",
        "default": "/images/kids/step-6-pdf.png",
        "section": "kids",
    },
}


# ============================================================
# Schemas
# ============================================================


class CreaImageOut(BaseModel):
    slot: str
    label: str
    aspect: str
    default_src: str
    section: str = "autori"  # "autori" | "kids" — retrocompat default
    has_image: bool
    image_url: Optional[str] = None


# ============================================================
# Helpers
# ============================================================


def _rows_by_slot() -> dict[str, CreaImage]:
    with session_scope() as s:
        rows = s.execute(select(CreaImage)).scalars().all()
        return {r.slot: r for r in rows}


def _to_out(slot: str, row: Optional[CreaImage], *, admin: bool = False) -> CreaImageOut:
    cfg = SLOTS[slot]
    has_image = bool(row and row.storage_key)
    image_url = None
    if has_image:
        ts = int(row.updated_at.timestamp()) if row.updated_at else 0
        base = "/api/admin/crea/images" if admin else "/api/crea/images"
        image_url = f"{base}/{slot}/image?v={ts}"
    return CreaImageOut(
        slot=slot,
        label=cfg["label"],
        aspect=cfg["aspect"],
        default_src=cfg["default"],
        section=cfg.get("section", "autori"),
        has_image=has_image,
        image_url=image_url,
    )


def _list(*, admin: bool = False) -> dict:
    by_slot = _rows_by_slot()
    return {
        "images": [_to_out(slot, by_slot.get(slot), admin=admin) for slot in SLOTS]
    }


def _get_storage_key(slot: str) -> str | None:
    with session_scope() as s:
        row = s.execute(
            select(CreaImage).where(CreaImage.slot == slot)
        ).scalar_one_or_none()
        return row.storage_key if row else None


# ============================================================
# Endpoint pubblici
# ============================================================


@public_router.get("/images")
def list_public_images(response: Response) -> dict:
    # No-store: la lista deve riflettere subito gli upload admin. Senza questo,
    # un browser/proxy può servire un JSON vecchio (image_url null) e mostrare
    # i default statici invece delle immagini appena caricate.
    response.headers["Cache-Control"] = "no-store"
    return _list()


@public_router.get("/images/{slot}/image")
def get_public_image(slot: str) -> Response:
    if slot not in SLOTS:
        raise HTTPException(status_code=404, detail="Slot non trovato")
    return _serve_image(_get_storage_key(slot))


# ============================================================
# Endpoint admin
# ============================================================


@admin_router.get("/images")
def list_admin_images(admin: dict = Depends(require_admin)) -> dict:
    return _list(admin=True)


@admin_router.get("/images/{slot}/image")
def get_admin_image(slot: str, admin: dict = Depends(require_admin)) -> Response:
    if slot not in SLOTS:
        raise HTTPException(status_code=404, detail="Slot non trovato")
    return _serve_image(_get_storage_key(slot))


@admin_router.post("/images/{slot}/upload", response_model=CreaImageOut)
async def upload_image(
    slot: str,
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin),
) -> CreaImageOut:
    if slot not in SLOTS:
        raise HTTPException(status_code=404, detail="Slot non trovato")
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Il file deve essere un'immagine")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    # Ottimizzazione: qualsiasi upload (PNG/JPEG/...) viene convertito in WebP,
    # mantenendo le stesse dimensioni in pixel ma con un file molto più leggero.
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
    except Exception:
        raise HTTPException(status_code=400, detail="Immagine non valida o corrotta")

    key = storage_keys.crea_image_key(slot)
    upload_bytes(key, data, content_type="image/webp")
    with session_scope() as s:
        row = s.execute(
            select(CreaImage).where(CreaImage.slot == slot)
        ).scalar_one_or_none()
        if row is None:
            row = CreaImage(slot=slot, storage_key=key)
            s.add(row)
        else:
            row.storage_key = key
        row.updated_at = utcnow()  # forza cache-bust anche se la key è invariata
        s.flush()
        return _to_out(slot, row, admin=True)


@admin_router.delete("/images/{slot}", response_model=CreaImageOut)
def delete_image(slot: str, admin: dict = Depends(require_admin)) -> CreaImageOut:
    if slot not in SLOTS:
        raise HTTPException(status_code=404, detail="Slot non trovato")
    key: str | None = None
    with session_scope() as s:
        row = s.execute(
            select(CreaImage).where(CreaImage.slot == slot)
        ).scalar_one_or_none()
        if row is not None:
            key = row.storage_key
            row.storage_key = None
            row.updated_at = utcnow()
            s.flush()
    if key:
        delete_object(key)
    return _to_out(slot, None, admin=True)
