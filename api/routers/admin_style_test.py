"""Endpoint Admin Test-Style.

Consente all'admin di:
  1. Generare un'immagine di prova per uno stile preset (con scene params
     opzionali e reference character opzionale)
  2. Visualizzare la galleria dei test già generati
  3. Assegnare un'immagine come "sample" per Pro o KIDS (uno per stile)
  4. Cancellare/modificare test

Endpoint pubblici (per i wizard di scelta stile):
  GET /api/styles/samples?flow=pro|kids  → mappa preset_id -> URL

Sono in questo router perché ha già i dependency di admin auth; il
router pubblico "styles" (già montato su /api/styles) espone il
solo endpoint samples.
"""
from __future__ import annotations

import io
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from api.routers.admin import require_admin
from billing.plans import cost_for_operation
from db.models import CreditOperation
from db.repos import credits as credits_repo
from db.repos import style_test_images as style_test_repo
from db.repos import users as users_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from storage.client import delete_object, download_bytes, object_exists, upload_bytes
from storage.keys import style_test_image_key

logger = logging.getLogger(__name__)

router = APIRouter()

_ACCEPTED_REF_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_MAX_REF_SIZE = 10 * 1024 * 1024  # 10 MB


# ============================================================
# Schemas
# ============================================================


class StylePresetOut(BaseModel):
    id: str
    label: str
    category: str
    has_sample_pro: bool
    has_sample_kids: bool


class StylePresetsListOut(BaseModel):
    presets: list[StylePresetOut]


class StyleTestImageOut(BaseModel):
    id: str
    style_preset_id: str
    prompt: str
    scene_params: dict
    quality: str
    aspect_ratio: str
    is_sample_pro: bool
    is_sample_kids: bool
    notes: str
    image_url: str
    created_at: str


class StyleTestImagesListOut(BaseModel):
    images: list[StyleTestImageOut]


class UpdateTestIn(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=2000)


class AssignSampleIn(BaseModel):
    flow: str = Field(..., pattern="^(pro|kids)$")


# ============================================================
# Helpers
# ============================================================


def _to_out(img) -> StyleTestImageOut:
    return StyleTestImageOut(
        id=str(img.id),
        style_preset_id=img.style_preset_id,
        prompt=img.prompt or "",
        scene_params=img.scene_params or {},
        quality=img.quality,
        aspect_ratio=img.aspect_ratio,
        is_sample_pro=img.is_sample_pro,
        is_sample_kids=img.is_sample_kids,
        notes=img.notes or "",
        image_url=f"/api/admin/style-test/images/{img.id}/image",
        created_at=img.created_at.isoformat() if img.created_at else "",
    )


def _aspect_to_size(ar: str) -> str:
    """Mappa aspect ratio key → size supportata da gpt-image-1.

    Riusa il helper canonico in snaptoon_core.scene per rimanere coerente
    con il resto del codice (le key sono nella forma '1_1', '2_3', '9_16'
    ecc — con underscore, non colon).
    """
    from snaptoon_core.scene import aspect_ratio_to_provider_size

    return aspect_ratio_to_provider_size(ar)


# ============================================================
# Presets (per il dropdown admin)
# ============================================================


@router.get("/presets", response_model=StylePresetsListOut)
def list_presets_for_admin(
    admin: dict = Depends(require_admin),
) -> StylePresetsListOut:
    from snaptoon_core.styles_library import list_presets

    # list_presets(category=None) ritorna TUTTI i preset (fumetto,
    # illustrazione, fotografia, cinema, kids, ...). Passargli argomenti
    # sbagliati causava un TypeError → 500.
    presets = list_presets()

    with session_scope() as s:
        # Fetch existing samples in one pass
        pro_ids: set[str] = set()
        kids_ids: set[str] = set()
        for img in style_test_repo.list_all(s):
            if img.is_sample_pro:
                pro_ids.add(img.style_preset_id)
            if img.is_sample_kids:
                kids_ids.add(img.style_preset_id)

    out = [
        StylePresetOut(
            id=p.id,
            label=p.label,
            category=p.category,
            has_sample_pro=p.id in pro_ids,
            has_sample_kids=p.id in kids_ids,
        )
        for p in presets
    ]
    return StylePresetsListOut(presets=out)


# ============================================================
# Generazione test
# ============================================================


@router.post("/generate", response_model=StyleTestImageOut, status_code=status.HTTP_201_CREATED)
async def generate_test_image(
    # NB: tutti i campi arrivano nel multipart form (insieme al file
    # reference). Se questi fossero parametri semplici FastAPI li
    # cercherebbe in query string e li ignorerebbe quando c'è
    # UploadFile → default value silente = i valori scelti dall'admin
    # non venivano applicati.
    style_preset_id: str = Form(...),
    prompt: str = Form(...),
    shot_distance: str = Form(default=""),
    shot_angle: str = Form(default=""),
    mood: str = Form(default=""),
    aspect_ratio: str = Form(default="1_1"),
    quality: str = Form(default="medium"),
    reference: Optional[UploadFile] = File(default=None),
    admin: dict = Depends(require_admin),
) -> StyleTestImageOut:
    """Genera un'immagine di test per lo stile indicato.

    Costo: 1 credito (charge sull'account admin che ha effettuato la
    richiesta). Se `reference` è fornito, viene passato come reference
    image a gpt-image-2 e cancellato subito dopo.
    """
    from snaptoon_core.generator import OpenAIImageGenerator
    from snaptoon_core.styles_library import get_preset

    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt obbligatorio")

    preset = get_preset(style_preset_id)
    if preset is None:
        raise HTTPException(status_code=400, detail=f"Preset non trovato: {style_preset_id}")

    # Read + validate reference
    ref_bytes: Optional[bytes] = None
    if reference is not None:
        if reference.content_type not in _ACCEPTED_REF_MIMES:
            raise HTTPException(
                status_code=400,
                detail=f"Formato reference non supportato ({reference.content_type})",
            )
        ref_bytes = await reference.read()
        if len(ref_bytes) > _MAX_REF_SIZE:
            raise HTTPException(status_code=413, detail="Reference troppo grande (max 10 MB)")
        if len(ref_bytes) == 0:
            ref_bytes = None

    # Costruisci il prompt seguendo lo stesso pattern di build_panel_prompt
    # (kids_pipeline.py): mappa le KEY delle scene params → prompt_en (le
    # frasi inglesi pronte all'uso definite in snaptoon_core.scene).
    # Se passassimo le key crude (es. "eye_level"), gpt-image le
    # interpreterebbe come stringhe generiche → resa scadente.
    from snaptoon_core.scene import (
        ASPECT_RATIOS,
        MOODS,
        SHOT_ANGLES,
        SHOT_DISTANCES,
    )

    # Descrizione aspect ratio nel prompt (aiuta il modello a comporre
    # correttamente all'interno del frame)
    ar_option = next((o for o in ASPECT_RATIOS if o.key == aspect_ratio), None)
    ar_hint = ar_option.prompt_en if ar_option else "square 1:1 aspect ratio"

    parts = [
        f"=== RENDER MODE ===\n"
        f"Full-bleed single comic vignette in {ar_hint}. Edge-to-edge, no "
        f"external frame or page border. Compose the scene to fill the "
        f"entire frame."
    ]
    parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")

    # DIRECTING: mappa le key delle scene params sulle frasi in inglese
    clauses: list[str] = []
    if shot_distance:
        o = next((o for o in SHOT_DISTANCES if o.key == shot_distance), None)
        if o:
            clauses.append(f"SHOT DISTANCE: {o.prompt_en}.")
    if shot_angle:
        o = next((o for o in SHOT_ANGLES if o.key == shot_angle), None)
        if o:
            clauses.append(f"CAMERA ANGLE: {o.prompt_en}.")
    if mood:
        o = next((o for o in MOODS if o.key == mood), None)
        if o:
            clauses.append(f"MOOD: {o.prompt_en}.")
    if clauses:
        parts.append("=== DIRECTING ===\n" + " ".join(clauses))

    parts.append(f"=== SUBJECT ===\n{prompt.strip()}")
    parts.append(
        "=== CHARACTER CONSISTENCY ===\n"
        "If a reference image is provided, the character in the output MUST "
        "look IDENTICAL to the reference: same face, same hair, same "
        "clothes. Visual ground truth."
    )
    if preset.extra_negative_terms:
        neg = ", ".join(preset.extra_negative_terms)
        parts.append(f"=== AVOID ===\n{neg}")
    full_prompt = "\n\n".join(parts)

    # Charge crediti admin
    admin_user_id = uuid.UUID(admin["id"])
    cost = cost_for_operation("generate_panel", quality=quality if quality != "auto" else "medium")
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, admin_user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_panel,
                reason=f"Style test '{style_preset_id}'",
                reference_id=None,
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti admin insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Genera immagine
    generator = OpenAIImageGenerator()
    tmp_ref_path: Optional[Path] = None
    ref_list = None
    try:
        if ref_bytes:
            tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tf.write(ref_bytes)
            tf.close()
            tmp_ref_path = Path(tf.name)
            ref_list = [tmp_ref_path]

        size = _aspect_to_size(aspect_ratio)
        img_bytes = generator._generate_bytes(
            prompt=full_prompt,
            size=size,
            reference_images=ref_list,
            quality=quality if quality in ("low", "medium", "high", "auto") else "medium",
        )
    except Exception as e:
        # Refund
        with session_scope() as s:
            u = users_repo.get_by_id(s, admin_user_id)
            credits_repo.refund(
                s, u, amount=cost, reason=f"Refund style test: {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502, detail=f"Errore generazione: {str(e)[:200]}"
        )
    finally:
        if tmp_ref_path is not None:
            try:
                tmp_ref_path.unlink()
            except OSError:
                pass

    # Crea record + upload
    scene_params = {
        "shot_distance": shot_distance or None,
        "shot_angle": shot_angle or None,
        "mood": mood or None,
    }
    with session_scope() as s:
        # Pre-create record to get UUID for storage key
        img = style_test_repo.create(
            s,
            style_preset_id=style_preset_id,
            storage_key="",  # placeholder
            prompt=prompt,
            scene_params=scene_params,
            quality=quality,
            aspect_ratio=aspect_ratio,
            created_by_user_id=admin_user_id,
        )
        key = style_test_image_key(img.id)
        upload_bytes(key, img_bytes, content_type="image/png")
        img.storage_key = key
        return _to_out(img)


# ============================================================
# Gallery / CRUD
# ============================================================


@router.get("/images", response_model=StyleTestImagesListOut)
def list_test_images(
    style_preset_id: Optional[str] = None,
    admin: dict = Depends(require_admin),
) -> StyleTestImagesListOut:
    with session_scope() as s:
        imgs = style_test_repo.list_all(s, style_preset_id=style_preset_id)
        return StyleTestImagesListOut(images=[_to_out(i) for i in imgs])


@router.get("/images/{image_id}/image")
def get_test_image(
    image_id: str, admin: dict = Depends(require_admin)
) -> Response:
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        img = style_test_repo.get_by_id(s, iid)
        if img is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        key = img.storage_key

    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine mancante")
    return Response(
        content=download_bytes(key),
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.patch("/images/{image_id}", response_model=StyleTestImageOut)
def update_test_image(
    image_id: str,
    payload: UpdateTestIn,
    admin: dict = Depends(require_admin),
) -> StyleTestImageOut:
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        img = style_test_repo.get_by_id(s, iid)
        if img is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        if payload.notes is not None:
            style_test_repo.update_notes(s, img, payload.notes)
        return _to_out(img)


@router.post("/images/{image_id}/assign-sample", response_model=StyleTestImageOut)
def assign_sample(
    image_id: str,
    payload: AssignSampleIn,
    admin: dict = Depends(require_admin),
) -> StyleTestImageOut:
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        img = style_test_repo.get_by_id(s, iid)
        if img is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        style_test_repo.assign_as_sample(s, img, flow=payload.flow)
        return _to_out(img)


@router.post("/images/{image_id}/unassign-sample", response_model=StyleTestImageOut)
def unassign_sample(
    image_id: str,
    payload: AssignSampleIn,
    admin: dict = Depends(require_admin),
) -> StyleTestImageOut:
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        img = style_test_repo.get_by_id(s, iid)
        if img is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        style_test_repo.unassign_as_sample(s, img, flow=payload.flow)
        return _to_out(img)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_image(
    image_id: str, admin: dict = Depends(require_admin)
) -> None:
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        img = style_test_repo.get_by_id(s, iid)
        if img is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        key = img.storage_key
        style_test_repo.soft_delete(s, img)

    if key and object_exists(key):
        try:
            delete_object(key)
        except Exception as e:
            logger.warning("Delete style test storage fallito: %s", e)


# ============================================================
# Public endpoint (per i wizard di scelta stile)
# ============================================================


class StyleSampleOut(BaseModel):
    style_preset_id: str
    image_url: str


class StyleSamplesListOut(BaseModel):
    samples: list[StyleSampleOut]


public_router = APIRouter()


@public_router.get("/samples", response_model=StyleSamplesListOut)
def list_public_style_samples(flow: str = "pro") -> StyleSamplesListOut:
    """Ritorna la mappa dei sample per il flow indicato.

    Consumato dai wizard Stile in Pro (/api/styles/samples?flow=pro) e
    KIDS (?flow=kids). Nessuna auth: i sample sono contenuto pubblico.
    """
    if flow not in ("pro", "kids"):
        raise HTTPException(status_code=400, detail="flow deve essere pro|kids")

    with session_scope() as s:
        imgs = style_test_repo.list_all(s, only_samples_flow=flow)
        return StyleSamplesListOut(
            samples=[
                StyleSampleOut(
                    style_preset_id=i.style_preset_id,
                    image_url=f"/api/styles/samples/{i.id}/image",
                )
                for i in imgs
            ]
        )


@public_router.get("/samples/{image_id}/image")
def get_public_sample_image(image_id: str) -> Response:
    """Serve i bytes di un sample. Solo se marcato come sample per Pro o KIDS."""
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Non trovato")

    with session_scope() as s:
        img = style_test_repo.get_by_id(s, iid)
        if img is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        if not (img.is_sample_pro or img.is_sample_kids):
            raise HTTPException(status_code=404, detail="Non pubblico")
        key = img.storage_key

    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine mancante")
    return Response(
        content=download_bytes(key),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )
