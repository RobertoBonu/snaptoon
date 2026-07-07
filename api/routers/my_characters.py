"""Endpoint 'I miei personaggi': archivio riusabile del cast per l'utente.

L'utente può creare personaggi in tre modi:
  1. Da descrizione testuale (POST /api/my-characters)
  2. Da foto reale (POST /api/my-characters/from-photo) — la foto viene
     usata come reference per gpt-image-2 e poi CANCELLATA subito
  3. Da un personaggio esistente in un progetto (endpoint dedicato altrove)

Ogni personaggio ha una reference PNG in stile neutro / portrait realistico,
riusabile in qualsiasi progetto KIDS o Pro senza consumare altri crediti.
"""
from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter, Depends, File, HTTPException, Response, UploadFile, status,
)
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from billing.plans import cost_for_operation
from db.models import CreditOperation
from db.repos import cast_archive as cast_archive_repo
from db.repos.credits import InsufficientCreditsError
from db.repos import credits as credits_repo
from db.repos import users as users_repo
from db.session import session_scope
from storage.client import (
    delete_object, download_bytes, object_exists, upload_bytes,
)
from storage.keys import my_character_reference_key

logger = logging.getLogger(__name__)

router = APIRouter()


_ACCEPTED_PHOTO_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB


# ============================================================
# Schemas
# ============================================================


class MyCharacterOut(BaseModel):
    id: str
    name: str
    visual_description: str
    has_reference: bool
    created_at: str
    # Stato condivisione: "not_shared" | "pending" | "published" | "rejected"
    share_status: str = "not_shared"
    share_caption: str = ""
    share_author_role: str = ""
    share_rejection_reason: str = ""


class MyCharactersListOut(BaseModel):
    characters: list[MyCharacterOut]


class MyCharacterCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    visual_description: str = Field(..., min_length=5, max_length=2000)


class MyCharacterUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    visual_description: Optional[str] = Field(default=None, max_length=2000)


# ============================================================
# Helpers
# ============================================================


def _to_out(entry) -> MyCharacterOut:
    return MyCharacterOut(
        id=str(entry.id),
        name=entry.name,
        visual_description=entry.visual_description,
        has_reference=bool(entry.reference_storage_key),
        created_at=entry.created_at.isoformat(),
        share_status=getattr(entry, "share_status", "not_shared") or "not_shared",
        share_caption=getattr(entry, "share_caption", "") or "",
        share_author_role=getattr(entry, "share_author_role", "") or "",
        share_rejection_reason=getattr(entry, "share_rejection_reason", "") or "",
    )


class ShareIn(BaseModel):
    caption: str = Field(default="", max_length=500)
    author_role: str = Field(default="", max_length=80)


def _build_neutral_reference_prompt(name: str, visual_description: str) -> str:
    """Prompt per generare una reference IN STILE NEUTRO / portrait realistico.

    L'obiettivo è avere una reference riusabile in progetti di stile diverso
    (KIDS pixar, chibi, superhero; Pro graphic novel, ecc.). Uno stile
    "portrait clean" permette a gpt-image-2 di adattare lo stile grafico
    al momento dell'uso nel progetto, mantenendo l'aspetto del soggetto.

    Formato output: 1024x1536 verticale (2:3). Vincoli forti sul framing
    per garantire che la testa sia SEMPRE completamente in cornice (evitare
    il problema classico dei generatori che tagliano il volto in alto).
    """
    return (
        "=== RENDER MODE ===\n"
        "Full-body vertical character reference sheet, 2:3 portrait format. "
        "Neutral clean illustration style, soft natural lighting, plain "
        "off-white background. The character stands facing the camera in a "
        "T-pose or relaxed neutral pose.\n\n"
        "=== CRITICAL FRAMING CONSTRAINTS ===\n"
        "The ENTIRE character must be FULLY VISIBLE inside the frame:\n"
        " - HEAD: the top of the hair/hat/crown must have at least 10% "
        "padding above it. The face is fully in frame, not cropped.\n"
        " - FEET: the bottom of the shoes/paws must have at least 5% "
        "padding below.\n"
        " - LEFT/RIGHT: 15% empty space on each side of the widest point "
        "(arms, wings, tail, etc).\n"
        "The camera is medium-wide, pulled back enough to fit the whole "
        "figure comfortably. NO close-up. NO cropping of the head, face, "
        "hands, or feet.\n\n"
        f"=== SUBJECT — {name} ===\n"
        f"{visual_description}\n\n"
        "=== EXPRESSION AND POSE ===\n"
        "Calm neutral expression, mouth slightly closed, eyes open looking "
        "forward. Arms slightly away from body (not covering torso), palms "
        "visible. No dramatic action, no motion.\n\n"
        "=== AVOID ===\n"
        "cropped head, head cut off at top, face cut off, chin only visible, "
        "close-up portrait, extreme angle, cinematic drama, background "
        "scenery, other characters, watermark, text, logo, signature, "
        "props hiding the body."
    )


def _build_photo_to_reference_prompt(
    name: str, visual_description: str
) -> str:
    """Prompt per convertire una foto reale in reference stilizzata neutra.

    La foto è passata come reference_image a gpt-image-2. Il prompt chiede
    di preservare l'aspetto del soggetto ma renderizzarlo in stile portrait
    illustrato pulito, riusabile.
    """
    extra = ""
    if visual_description.strip():
        extra = f"\n\nAdditional description hints: {visual_description}"
    return (
        "=== RENDER MODE ===\n"
        "Convert this reference photo into a full-body vertical illustrated "
        "character reference sheet, 2:3 portrait format. Preserve the "
        "subject's facial features, hair color, body proportions and "
        "identifying characteristics from the photo. Render in a clean "
        "neutral illustration style with soft natural lighting, plain "
        "off-white background.\n\n"
        "=== CRITICAL FRAMING CONSTRAINTS ===\n"
        "The ENTIRE character must be FULLY VISIBLE inside the frame:\n"
        " - HEAD: 10% padding above the top of the hair. Face fully visible.\n"
        " - FEET: 5% padding below feet.\n"
        " - Character stands facing the camera, arms relaxed, calm "
        "expression. Medium-wide framing.\n"
        "NO cropping of head, face, hands, or feet. NO close-up portrait.\n\n"
        f"=== CHARACTER NAME ===\n{name}{extra}\n\n"
        "=== AVOID ===\n"
        "photorealistic skin, exact photo reproduction, cropped head, "
        "face cut off, close-up, cinematic drama, action pose, other "
        "people, background scenery, watermark, text."
    )


def _generate_and_save_reference(
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
    prompt: str,
    reference_photo: Optional[bytes],
    *,
    quality: str = "medium",
) -> str:
    """Chiama gpt-image-2 e salva la PNG in object storage.

    Se reference_photo è fornita, viene passata come reference alla generazione
    e MAI salvata in storage (rispetto privacy).

    Ritorna la storage_key.
    """
    from snaptoon_core.generator import OpenAIImageGenerator

    generator = OpenAIImageGenerator()

    tmp_photo_path: Optional[Path] = None
    ref_list: Optional[list[Path]] = None
    if reference_photo:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(reference_photo)
        tmp.close()
        tmp_photo_path = Path(tmp.name)
        ref_list = [tmp_photo_path]

    try:
        img_bytes = generator._generate_bytes(
            prompt=prompt,
            # 2:3 portrait — massimo spazio verticale per contenere la testa
            # e i piedi senza dover ricorrere a crop stretti.
            size="1024x1536",
            reference_images=ref_list,
            quality=quality,
        )
    finally:
        # CRITICO: cancella la foto temporanea IMMEDIATAMENTE
        if tmp_photo_path is not None:
            try:
                tmp_photo_path.unlink()
            except OSError:
                pass

    key = my_character_reference_key(user_id, entry_id)
    save_with_variants(key, img_bytes)
    return key


# ============================================================
# Endpoints
# ============================================================


@router.get("", response_model=MyCharactersListOut)
def list_my_characters(
    user: dict = Depends(require_user),
) -> MyCharactersListOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        entries = cast_archive_repo.list_for_user(s, u)
        return MyCharactersListOut(
            characters=[_to_out(e) for e in entries]
        )


@router.post("", response_model=MyCharacterOut, status_code=status.HTTP_201_CREATED)
def create_my_character(
    payload: MyCharacterCreateIn, user: dict = Depends(require_user)
) -> MyCharacterOut:
    """Crea da descrizione testuale + genera reference AI. Charge 1 credito."""
    user_id = uuid.UUID(user["id"])

    # 1. Crea entry (senza reference)
    from sqlalchemy.exc import IntegrityError

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            entry = cast_archive_repo.create(
                s, user=u, name=payload.name,
                visual_description=payload.visual_description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except IntegrityError:
            # Doppione reale (vincolo unique parziale, solo su righe vive):
            # esiste già un personaggio con lo stesso nome per questo utente.
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Hai già un personaggio chiamato '{payload.name}'. "
                    "Usa un nome diverso o elimina prima quello esistente."
                ),
            )
        entry_id = entry.id

    # 2. Charge crediti + risolvi qualità utente
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
                reason=f"My character '{payload.name}' (descrizione)",
                reference_id=str(entry_id),
            )
    except InsufficientCreditsError as e:
        # Rimuovi entry appena creata (non ha ancora reference)
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            entry = cast_archive_repo.get_by_id(s, u, entry_id)
            if entry is not None:
                cast_archive_repo.soft_delete(s, entry)
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # 3. Genera reference + salva
    prompt = _build_neutral_reference_prompt(
        payload.name, payload.visual_description
    )
    try:
        key = _generate_and_save_reference(user_id, entry_id, prompt, reference_photo=None, quality=user_quality)
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund my-char '{payload.name}': {str(e)[:200]}",
            )
            entry = cast_archive_repo.get_by_id(s, u, entry_id)
            if entry is not None:
                cast_archive_repo.soft_delete(s, entry)
        raise HTTPException(
            status_code=502,
            detail=f"Errore generazione reference: {str(e)[:200]}",
        )

    # 4. Aggiorna entry con la storage_key
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, entry_id)
        if entry is None:
            raise HTTPException(status_code=500, detail="Entry sparita durante creazione")
        cast_archive_repo.set_reference_key(s, entry, key)
        return _to_out(entry)


@router.post(
    "/from-photo",
    response_model=MyCharacterOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_character_from_photo(
    name: str = "",
    visual_description: str = "",
    file: UploadFile = File(...),
    user: dict = Depends(require_user),
) -> MyCharacterOut:
    """Crea da foto reale: genera reference AI + cancella foto originale.

    La foto NON viene MAI persistita in object storage. Viene usata solo come
    reference in-memory per la chiamata OpenAI, poi il file temp viene
    cancellato immediatamente.
    """
    name = (name or "").strip()
    visual_description = (visual_description or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nome obbligatorio")

    if file.content_type not in _ACCEPTED_PHOTO_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Formato non supportato ({file.content_type}). Usa PNG, JPEG o WEBP.",
        )
    photo_bytes = await file.read()
    if len(photo_bytes) > _MAX_PHOTO_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Foto troppo grande (max {_MAX_PHOTO_SIZE // (1024*1024)} MB).",
        )
    if len(photo_bytes) == 0:
        raise HTTPException(status_code=400, detail="File vuoto.")

    user_id = uuid.UUID(user["id"])

    # 1. Crea entry
    from sqlalchemy.exc import IntegrityError

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            entry = cast_archive_repo.create(
                s, user=u, name=name,
                visual_description=visual_description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except IntegrityError:
            # Doppione reale — vedi commento in create_my_character
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Hai già un personaggio chiamato '{name}'. "
                    "Usa un nome diverso o elimina prima quello esistente."
                ),
            )
        entry_id = entry.id

    # 2. Charge + risolvi qualità utente
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
                reason=f"My character '{name}' (foto)",
                reference_id=str(entry_id),
            )
    except InsufficientCreditsError as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            entry = cast_archive_repo.get_by_id(s, u, entry_id)
            if entry is not None:
                cast_archive_repo.soft_delete(s, entry)
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # 3. Genera con foto (che viene cancellata subito dopo)
    prompt = _build_photo_to_reference_prompt(name, visual_description)
    try:
        key = _generate_and_save_reference(user_id, entry_id, prompt, reference_photo=photo_bytes, quality=user_quality)
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund my-char foto '{name}': {str(e)[:200]}",
            )
            entry = cast_archive_repo.get_by_id(s, u, entry_id)
            if entry is not None:
                cast_archive_repo.soft_delete(s, entry)
        raise HTTPException(
            status_code=502,
            detail=f"Errore generazione reference da foto: {str(e)[:200]}",
        )
    finally:
        # Assicurati che i bytes della foto siano rimossi dalla memoria
        # (Python garbage collector li libererà, ma esplicito è meglio)
        photo_bytes = None  # type: ignore

    # 4. Aggiorna entry
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, entry_id)
        if entry is None:
            raise HTTPException(status_code=500, detail="Entry sparita")
        cast_archive_repo.set_reference_key(s, entry, key)
        return _to_out(entry)


@router.get("/{entry_id}/image")
def get_my_character_image(
    entry_id: str,
    user: dict = Depends(require_user),
    variant: str = "full",
) -> Response:
    """Bytes immagine della reference (variante WebP se disponibile)."""
    from api.utils.serve_image import serve_image_variant
    from storage.image_variants import parse_variant, save_with_variants

    user_id = uuid.UUID(user["id"])
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid) if u else None
        if entry is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        key = entry.reference_storage_key

    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Reference non generata")
    return serve_image_variant(key, parse_variant(variant))


@router.patch("/{entry_id}", response_model=MyCharacterOut)
def update_my_character(
    entry_id: str,
    payload: MyCharacterUpdateIn,
    user: dict = Depends(require_user),
) -> MyCharacterOut:
    user_id = uuid.UUID(user["id"])
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid) if u else None
        if entry is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        try:
            cast_archive_repo.update_metadata(
                s, entry,
                name=payload.name,
                visual_description=payload.visual_description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _to_out(entry)


@router.post("/{entry_id}/regenerate", response_model=MyCharacterOut)
def regenerate_my_character(
    entry_id: str, user: dict = Depends(require_user)
) -> MyCharacterOut:
    """Rigenera la reference AI da descrizione testuale (senza foto).

    Costa 1 credito. La vecchia reference viene sostituita.
    """
    user_id = uuid.UUID(user["id"])
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid) if u else None
        if entry is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        name = entry.name
        description = entry.visual_description

    if not description.strip():
        raise HTTPException(
            status_code=400,
            detail="Servono descrizione visiva per rigenerare.",
        )

    # Cancella vecchia reference se presente
    old_key = my_character_reference_key(user_id, eid)
    if object_exists(old_key):
        try:
            delete_object(old_key)
        except Exception as e:
            logger.warning("Delete old ref my-char fallito: %s", e)

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
                reason=f"Regen my-char '{name}'",
                reference_id=str(eid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Genera
    prompt = _build_neutral_reference_prompt(name, description)
    try:
        key = _generate_and_save_reference(user_id, eid, prompt, reference_photo=None, quality=user_quality)
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund regen my-char '{name}': {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502,
            detail=f"Errore rigenerazione: {str(e)[:200]}",
        )

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid)
        if entry is None:
            raise HTTPException(status_code=500, detail="Entry sparita")
        cast_archive_repo.set_reference_key(s, entry, key)
        return _to_out(entry)


@router.post("/{entry_id}/share", response_model=MyCharacterOut)
def share_my_character(
    entry_id: str,
    payload: ShareIn,
    user: dict = Depends(require_user),
) -> MyCharacterOut:
    """Sottopone il personaggio alla moderazione admin per /esplora.

    Il personaggio DEVE avere una reference generata. Lo status passa a
    'pending'. Se era già 'published' o 'rejected', si riparte da capo.
    """
    user_id = uuid.UUID(user["id"])
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid) if u else None
        if entry is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        if not entry.reference_storage_key:
            raise HTTPException(
                status_code=400,
                detail="Genera prima la reference AI, poi condividi",
            )
        cast_archive_repo.submit_for_sharing(
            s, entry,
            caption=payload.caption,
            author_role=payload.author_role,
        )
        return _to_out(entry)


@router.post("/{entry_id}/unshare", response_model=MyCharacterOut)
def unshare_my_character(
    entry_id: str, user: dict = Depends(require_user)
) -> MyCharacterOut:
    """Ritira la condivisione (rimuove da moderazione e da /esplora se pubblicato)."""
    user_id = uuid.UUID(user["id"])
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid) if u else None
        if entry is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        cast_archive_repo.unshare(s, entry)
        return _to_out(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_character(
    entry_id: str, user: dict = Depends(require_user)
) -> None:
    user_id = uuid.UUID(user["id"])
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        entry = cast_archive_repo.get_by_id(s, u, eid) if u else None
        if entry is None:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        # Cancella anche la reference dallo storage (soft delete + hard file)
        key = entry.reference_storage_key
        cast_archive_repo.soft_delete(s, entry)

    if key and object_exists(key):
        try:
            delete_object(key)
        except Exception as e:
            logger.warning("Delete ref my-char storage fallito: %s", e)
