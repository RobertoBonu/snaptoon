"""Endpoint figurine collezionabili degli utenti.

Flusso:
  1. Utente crea la card in /app/my-cards (name + type + caption +
     opzionale reference foto)
  2. POST /api/cards genera l'immagine AI e assegna un numero progressivo
     globale
  3. Utente può rigenerare (charge crediti) o modificare i metadata
  4. Utente pubblica scegliendo una categoria BookShop → status "pending"
  5. Admin approva/rifiuta
  6. Card pubblicate visibili nel BookShop /bookshop (griglia dedicata)

Costi:
  - Creazione card = 1 credito (medium quality)
  - Rigenerazione = 1 credito
  - Modifica metadata / publish / unpublish = 0 crediti
"""
from __future__ import annotations

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
from api.routers.auth import require_user
from billing.plans import (
    FreeToPlayLimitError,
    check_free_to_play_quota,
    consume_free_to_play,
    cost_for_operation,
)
from db.models import CreditOperation
from db.repos import bookshop_categories as bookshop_repo
from db.repos import credits as credits_repo
from db.repos import user_cards as cards_repo
from db.repos import users as users_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from storage.client import (
    delete_object,
    download_bytes,
    object_exists,
    upload_bytes,
)
from storage.keys import user_card_reference_key, user_card_rendered_key

logger = logging.getLogger(__name__)

router = APIRouter()
admin_router = APIRouter()
public_router = APIRouter()

_ACCEPTED_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


# ============================================================
# Schemas
# ============================================================


class CardOut(BaseModel):
    id: str
    name: str
    character_type: str
    caption: str
    author_display: str
    progressive_number: int
    has_rendered: bool
    has_reference: bool
    moderation_status: str
    rejection_reason: str
    bookshop_category_id: Optional[str] = None
    bookshop_category_label: Optional[str] = None
    bookshop_category_macro: Optional[str] = None
    style_preset_id: Optional[str] = None
    image_url: str
    read_url: str
    created_at: str


class CardsListOut(BaseModel):
    cards: list[CardOut]


class UpdateCardIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    character_type: Optional[str] = Field(default=None, max_length=120)
    caption: Optional[str] = Field(default=None, max_length=500)


class PublishCardIn(BaseModel):
    bookshop_category_id: str


class RejectIn(BaseModel):
    reason: str = Field(default="", max_length=1000)


# ============================================================
# Helpers
# ============================================================


def _to_out(card, cat=None) -> CardOut:
    return CardOut(
        id=str(card.id),
        name=card.name,
        character_type=card.character_type,
        caption=card.caption or "",
        author_display=card.author_display or "",
        progressive_number=card.progressive_number,
        has_rendered=bool(card.rendered_image_key),
        has_reference=bool(card.reference_image_key),
        moderation_status=card.moderation_status,
        rejection_reason=card.rejection_reason or "",
        bookshop_category_id=(
            str(card.bookshop_category_id) if card.bookshop_category_id else None
        ),
        bookshop_category_label=cat.label if cat else None,
        bookshop_category_macro=cat.macro if cat else None,
        style_preset_id=card.style_preset_id or None,
        image_url=f"/api/cards/{card.id}/image",
        read_url=f"/c/{card.id}",
        created_at=card.created_at.isoformat() if card.created_at else "",
    )


def _card_number_display(n: int) -> str:
    return f"#{n:04d}"


def _build_card_prompt(
    *,
    name: str,
    character_type: str,
    caption: str,
    author: str,
    number: str,
    style_preset_id: Optional[str] = None,
) -> str:
    """Prompt strutturato per la card 9:16 con testi bake-in.

    Layout ricalca la card di riferimento inviata da Rob (Neo GATTO CURIOSO).
    Se style_preset_id è fornito, la sua expansion viene inserita nel
    blocco STYLE per condizionare la resa artistica.
    """
    from snaptoon_core.styles_library import get_preset

    style_block = ""
    if style_preset_id:
        preset = get_preset(style_preset_id)
        if preset:
            style_block = (
                f"\n=== ART STYLE ===\n{preset.expansion.strip()}\n"
                "Apply this art style to the CENTRAL character illustration. "
                "Keep the card frame (border, banners, badges, stars, "
                "caption panel, number tag) in a friendly comic-book design "
                "regardless of the character style, so the card feels "
                "consistent with other collectibles.\n"
            )

    return (
        "=== RENDER MODE ===\n"
        "Vertical collectible trading card illustration, tall portrait "
        "format (2:3 aspect, will be shown as 9:16). Cartoon comic-book "
        "aesthetic with vibrant saturated colors, thick clean black "
        "outlines, subtle vintage paper halftone texture on the card "
        "background. The card has a decorative dark navy blue rounded "
        "frame border all around the edges (about 30px thick).\n\n"
        "=== TOP AREA (upper 25% of the card) ===\n"
        f"A large YELLOW comic-book banner ribbon (rectangular ribbon shape "
        f"with slight tapering V-cuts at the ends, halftone dot pattern) "
        f"centered horizontally, containing the character name in BOLD "
        f"CHUNKY comic-book letters, white with dark outline: "
        f"'{name.upper()}'.\n"
        f"Immediately below the yellow banner, a smaller BLUE tapered "
        f"sub-banner with the character type in bold white sans-serif: "
        f"'{character_type.upper()}'.\n"
        f"Below the blue sub-banner, a small ORANGE pill-shaped tag "
        f"centered with the author credit in a friendly rounded font: "
        f"'di {author}'.\n\n"
        "=== CENTER AREA (middle 55% of the card) ===\n"
        f"Central character illustration of {name}, described as: "
        f"a {character_type.lower()}. Set in a natural cozy environment "
        f"relevant to the character. The character fills the middle of the "
        f"card, in a friendly natural pose, expressive eyes, endearing "
        f"expression. Comic-book cel-shaded style with black outlines, "
        f"cartoon proportions.\n"
        f"If a reference image is provided, the character MUST look "
        f"IDENTICAL to the reference (same face, same colors, same "
        f"features) — treat as visual ground truth.\n\n"
        "=== BOTTOM AREA (lower 22% of the card) ===\n"
        "A horizontal row centered horizontally, well INSIDE the card "
        "frame with visible padding above and below. This row contains:\n"
        "  - three yellow filled 5-point stars on the LEFT side\n"
        f"  - a small BLUE rounded rectangle tag on the RIGHT side with "
        f"the progressive number in BOLD MONOSPACED font, white text: "
        f"'{number}'\n"
        "The stars and the number badge are on the SAME HORIZONTAL LINE, "
        "roughly the same height, visually balanced.\n"
        f"Below this row (still comfortably inside the card border, "
        f"leaving generous margin from the bottom edge of the card frame), "
        f"a BEIGE/TAN rounded rectangle panel with subtle paper texture, "
        f"containing the caption in bold italic serif font, black or "
        f"dark brown text: '{caption}'.\n\n"
        "=== SAFE AREA — CRITICAL ===\n"
        "ALL card elements (banners, badges, stars, number tag, caption "
        "panel) MUST fit STRICTLY INSIDE the outer card border with "
        "visible margin on all four sides. Do NOT let text or badges "
        "touch or cross the card edge. Nothing must appear cut off, "
        "truncated or clipped by the card boundary.\n\n"
        "=== TEXT RENDERING CRITICAL ===\n"
        "All text MUST be rendered CLEARLY and CORRECTLY SPELLED exactly "
        "as written above. Use recognizable readable fonts. Do NOT invent "
        "random text or scrambled letters. Keep the layout balanced and "
        "the character clearly the focal point.\n\n"
        + style_block
        + "\n=== AVOID ===\n"
        "misspelled or scrambled text, extra badges beyond those "
        "described, real brand logos, watermarks, panel borders like a "
        "comic page, more than one character on the card, dark or scary "
        "themes."
    )


async def _read_reference(reference: Optional[UploadFile]) -> Optional[bytes]:
    if reference is None:
        return None
    if reference.content_type not in _ACCEPTED_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Formato reference non supportato ({reference.content_type}). Usa PNG, JPEG o WEBP.",
        )
    data = await reference.read()
    if len(data) > _MAX_SIZE:
        raise HTTPException(status_code=413, detail="Reference troppo grande (max 10 MB)")
    if len(data) == 0:
        return None
    return data


def _generate_card_image(
    *,
    card_id: uuid.UUID,
    name: str,
    character_type: str,
    caption: str,
    author: str,
    progressive_number: int,
    reference_bytes: Optional[bytes],
    style_preset_id: Optional[str] = None,
    quality: str = "medium",
) -> tuple[str, Optional[str]]:
    """Genera l'immagine AI + salva. Ritorna (rendered_key, reference_key).

    reference_key è settata solo se reference_bytes è presente (viene
    conservata per consentire rigenerazioni successive coerenti).
    """
    from snaptoon_core.generator import OpenAIImageGenerator

    generator = OpenAIImageGenerator()
    prompt = _build_card_prompt(
        name=name,
        character_type=character_type,
        caption=caption,
        author=author,
        number=_card_number_display(progressive_number),
        style_preset_id=style_preset_id,
    )

    tmp_ref_path: Optional[Path] = None
    reference_key: Optional[str] = None
    try:
        ref_list = None
        if reference_bytes:
            tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tf.write(reference_bytes)
            tf.close()
            tmp_ref_path = Path(tf.name)
            ref_list = [tmp_ref_path]
            # Persisti la reference per rigenerazioni future
            reference_key = user_card_reference_key(card_id)
            upload_bytes(reference_key, reference_bytes, content_type="image/png")

        img_bytes = generator._generate_bytes(
            prompt=prompt,
            size="1024x1536",  # 2:3 portrait, closest to 9:16 supported
            reference_images=ref_list,
            quality=quality,
        )
    finally:
        if tmp_ref_path is not None:
            try:
                tmp_ref_path.unlink()
            except OSError:
                pass

    rendered_key = user_card_rendered_key(card_id)
    upload_bytes(rendered_key, img_bytes, content_type="image/png")
    return rendered_key, reference_key


# ============================================================
# Endpoint utente
# ============================================================


@router.post("", response_model=CardOut, status_code=status.HTTP_201_CREATED)
async def create_card(
    name: str = Form(...),
    character_type: str = Form(...),
    caption: str = Form(default=""),
    style_preset_id: str = Form(default=""),
    reference: Optional[UploadFile] = File(default=None),
    user: dict = Depends(require_user),
) -> CardOut:
    """Crea una nuova figurina. Costo: 1 credito.

    style_preset_id: opzionale ma raccomandato — se non fornito, l'AI
    userà uno stile generico. Deve essere un preset di stile valido
    (verifica silenziosa: se non trovato, si continua senza).
    """
    from api.utils.user_display import public_author_name
    from snaptoon_core.styles_library import get_preset

    name = name.strip()
    character_type = character_type.strip()
    caption = caption.strip()
    style_preset_id = style_preset_id.strip()
    if not name or not character_type:
        raise HTTPException(
            status_code=400, detail="Nome e tipo del personaggio obbligatori"
        )
    if style_preset_id and get_preset(style_preset_id) is None:
        # non-fatal: procedi senza stile ma logga
        logger.warning("style_preset_id sconosciuto ignorato: %s", style_preset_id)
        style_preset_id = ""

    ref_bytes = await _read_reference(reference)

    user_id = uuid.UUID(user["id"])

    # 1. Crea record vuoto per ottenere id + numero progressivo
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        # Free-To-Play: verifica quota (solleva 402 con codice speciale
        # così il frontend può mostrare il popup upgrade)
        try:
            check_free_to_play_quota(u, "card")
        except FreeToPlayLimitError:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "free_to_play_exhausted",
                    "action": "card",
                    "message": "Hai usato la tua figurina gratuita.",
                },
            )
        author_display = public_author_name(u)
        try:
            card = cards_repo.create(
                s,
                user=u,
                name=name,
                character_type=character_type,
                caption=caption,
                author_display=author_display,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Errore creazione card: {str(e)[:200]}"
            )
        card_id = card.id
        card_number = card.progressive_number

    # 2. Charge crediti (usa preferred_quality dell'utente)
    from api.utils.quality import cost_for_generation, resolve_user_quality

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        user_quality = resolve_user_quality(u)
    cost = cost_for_generation("generate_panel", user_quality)
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_panel,
                reason=f"Card figurina #{card_number} ({user_quality})",
                reference_id=str(card_id),
            )
    except InsufficientCreditsError as e:
        # Cancella la card vuota se non ci sono crediti
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            card = cards_repo.get_by_user_and_id(s, u, card_id) if u else None
            if card is not None:
                cards_repo.soft_delete(s, card)
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # 3. Genera immagine
    try:
        rendered_key, reference_key = _generate_card_image(
            card_id=card_id,
            name=name,
            character_type=character_type,
            caption=caption,
            author=author_display,
            progressive_number=card_number,
            reference_bytes=ref_bytes,
            style_preset_id=style_preset_id or None,
            quality=user_quality,
        )
    except Exception as e:
        # Refund + cancella
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund card #{card_number}: {str(e)[:200]}",
            )
            card = cards_repo.get_by_user_and_id(s, u, card_id) if u else None
            if card is not None:
                cards_repo.soft_delete(s, card)
        raise HTTPException(
            status_code=502, detail=f"Errore generazione card: {str(e)[:200]}"
        )

    # 4. Aggiorna record con storage keys + style
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, card_id)
        if card is None:
            raise HTTPException(status_code=500, detail="Card sparita")
        cards_repo.set_rendered_key(s, card, rendered_key)
        if reference_key:
            cards_repo.set_reference_key(s, card, reference_key)
        if style_preset_id:
            card.style_preset_id = style_preset_id
        # Free-To-Play: consuma il counter DOPO successo
        consume_free_to_play(u, "card")
        return _to_out(card)


@router.get("/mine", response_model=CardsListOut)
def list_my_cards(user: dict = Depends(require_user)) -> CardsListOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        cards = cards_repo.list_by_user(s, u)
        # Resolve categorie
        out: list[CardOut] = []
        for c in cards:
            cat = None
            if c.bookshop_category_id:
                cat = bookshop_repo.get_by_id(s, c.bookshop_category_id)
            out.append(_to_out(c, cat))
        return CardsListOut(cards=out)


@router.get("/{card_id}/image")
def get_card_image(card_id: str, user: dict = Depends(require_user)) -> Response:
    """Preview della propria card (solo owner). Uso pubblico via
    /api/bookshop/cards/{id}/image."""
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid) if u else None
        if card is None:
            raise HTTPException(status_code=404, detail="Card non trovata")
        key = card.rendered_image_key
    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine non generata")
    return Response(content=download_bytes(key), media_type="image/png")


@router.patch("/{card_id}", response_model=CardOut)
def update_card(
    card_id: str,
    payload: UpdateCardIn,
    user: dict = Depends(require_user),
) -> CardOut:
    """Aggiorna metadata (senza rigenerare l'immagine)."""
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid) if u else None
        if card is None:
            raise HTTPException(status_code=404, detail="Card non trovata")
        cards_repo.update_metadata(
            s, card,
            name=payload.name,
            character_type=payload.character_type,
            caption=payload.caption,
        )
        cat = None
        if card.bookshop_category_id:
            cat = bookshop_repo.get_by_id(s, card.bookshop_category_id)
        return _to_out(card, cat)


@router.post("/{card_id}/regenerate", response_model=CardOut)
def regenerate_card(
    card_id: str, user: dict = Depends(require_user)
) -> CardOut:
    """Rigenera l'immagine della card con gli attuali metadata + reference.
    Costa 1 credito."""
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    # Load context
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid) if u else None
        if card is None:
            raise HTTPException(status_code=404, detail="Card non trovata")
        name = card.name
        ctype = card.character_type
        caption = card.caption
        author = card.author_display
        number = card.progressive_number
        ref_key = card.reference_image_key
        style_id = card.style_preset_id
        # Blocca rigenerazione se pubblicata (per evitare cambi post approval)
        if card.moderation_status == "published":
            raise HTTPException(
                status_code=400,
                detail="Ritira la card dalla pubblicazione prima di rigenerarla.",
            )

    ref_bytes = None
    if ref_key and object_exists(ref_key):
        try:
            ref_bytes = download_bytes(ref_key)
        except Exception:
            pass

    # Charge (preferred_quality dell'utente)
    from api.utils.quality import cost_for_generation, resolve_user_quality

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        user_quality = resolve_user_quality(u)
    cost = cost_for_generation("generate_panel", user_quality)
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_panel,
                reason=f"Regen card figurina #{number} ({user_quality})",
                reference_id=str(cid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Genera
    try:
        rendered_key, _ = _generate_card_image(
            card_id=cid,
            name=name,
            character_type=ctype,
            caption=caption,
            author=author,
            progressive_number=number,
            reference_bytes=ref_bytes,
            style_preset_id=style_id,
            quality=user_quality,
        )
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund regen card #{number}: {str(e)[:200]}",
            )
        raise HTTPException(
            status_code=502, detail=f"Errore rigenerazione: {str(e)[:200]}"
        )

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid)
        if card is None:
            raise HTTPException(status_code=500, detail="Card sparita")
        cards_repo.set_rendered_key(s, card, rendered_key)
        cat = None
        if card.bookshop_category_id:
            cat = bookshop_repo.get_by_id(s, card.bookshop_category_id)
        return _to_out(card, cat)


@router.post("/{card_id}/publish", response_model=CardOut)
def publish_card(
    card_id: str,
    payload: PublishCardIn,
    user: dict = Depends(require_user),
) -> CardOut:
    """Sottopone la card a moderazione con la categoria scelta."""
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(card_id)
        cat_id = uuid.UUID(payload.bookshop_category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid) if u else None
        if card is None:
            raise HTTPException(status_code=404, detail="Card non trovata")
        if not card.rendered_image_key:
            raise HTTPException(
                status_code=400, detail="Card senza immagine — rigenera prima"
            )
        cat = bookshop_repo.get_by_id(s, cat_id)
        if cat is None or not cat.is_active:
            raise HTTPException(
                status_code=400, detail="Categoria non valida o non attiva"
            )
        cards_repo.submit_for_moderation(s, card, category_id=cat_id)
        return _to_out(card, cat)


@router.post("/{card_id}/unpublish", response_model=CardOut)
def unpublish_card(
    card_id: str, user: dict = Depends(require_user)
) -> CardOut:
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid) if u else None
        if card is None:
            raise HTTPException(status_code=404, detail="Card non trovata")
        cards_repo.unpublish(s, card)
        cat = None
        if card.bookshop_category_id:
            cat = bookshop_repo.get_by_id(s, card.bookshop_category_id)
        return _to_out(card, cat)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: str, user: dict = Depends(require_user)) -> None:
    user_id = uuid.UUID(user["id"])
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        card = cards_repo.get_by_user_and_id(s, u, cid) if u else None
        if card is None:
            raise HTTPException(status_code=404, detail="Card non trovata")
        rk = card.rendered_image_key
        ref = card.reference_image_key
        cards_repo.soft_delete(s, card)

    # Best-effort: cancella storage
    for key in (rk, ref):
        if key and object_exists(key):
            try:
                delete_object(key)
            except Exception as e:
                logger.warning("Delete card storage %s fallito: %s", key, e)


# ============================================================
# Endpoint public (BookShop / lettore)
# ============================================================


@public_router.get("/cards/{card_id}/image")
def get_public_card_image(card_id: str) -> Response:
    """Immagine pubblica: solo se la card è pubblicata (moderata)."""
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Non trovato")

    with session_scope() as s:
        card = cards_repo.get_by_id(s, cid)
        if card is None or card.moderation_status != "published":
            raise HTTPException(status_code=404, detail="Card non pubblica")
        key = card.rendered_image_key

    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    return Response(
        content=download_bytes(key),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@public_router.get("/cards")
def list_public_cards(
    macro: Optional[str] = None,
    category_id: Optional[str] = None,
    limit: int = 60,
) -> dict:
    """Elenco pubblico delle card pubblicate (per BookShop)."""
    cap = max(1, min(limit, 200))
    filter_cat: Optional[uuid.UUID] = None
    if category_id:
        try:
            filter_cat = uuid.UUID(category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="category_id non valido")

    with session_scope() as s:
        cards = cards_repo.list_published(
            s, macro=macro, category_id=filter_cat, limit=cap * 2
        )
        out: list[dict] = []
        for c in cards:
            if len(out) >= cap:
                break
            cat = None
            if c.bookshop_category_id:
                cat = bookshop_repo.get_by_id(s, c.bookshop_category_id)
            if macro and (cat is None or cat.macro != macro):
                continue
            out.append({
                "id": str(c.id),
                "name": c.name,
                "character_type": c.character_type,
                "caption": c.caption or "",
                "author_display": c.author_display or "",
                "progressive_number": c.progressive_number,
                "image_url": f"/api/bookshop/cards/{c.id}/image",
                "category_id": str(cat.id) if cat else None,
                "category_label": cat.label if cat else None,
                "category_macro": cat.macro if cat else None,
                "published_at": (
                    c.moderated_at.isoformat() if c.moderated_at else None
                ),
            })
        return {"cards": out}


# ============================================================
# Admin moderation
# ============================================================


@admin_router.get("/cards")
def admin_list_cards(
    status_filter: str = "pending",
    admin: dict = Depends(require_admin),
) -> dict:
    with session_scope() as s:
        if status_filter in ("pending", "published", "rejected", "draft"):
            cards = cards_repo.list_by_moderation(s, status_filter)
        else:
            # all: solo non-deleted
            from sqlalchemy import select
            from db.models import UserCard

            stmt = (
                select(UserCard)
                .where(UserCard.deleted_at.is_(None))
                .order_by(UserCard.created_at.desc())
            )
            cards = list(s.execute(stmt).scalars())

        out: list[dict] = []
        for c in cards:
            owner = users_repo.get_by_id(s, c.user_id)
            cat = None
            if c.bookshop_category_id:
                cat = bookshop_repo.get_by_id(s, c.bookshop_category_id)
            out.append({
                "id": str(c.id),
                "name": c.name,
                "character_type": c.character_type,
                "caption": c.caption or "",
                "author_display": c.author_display or "",
                "author_email": owner.email if owner else "",
                "progressive_number": c.progressive_number,
                "moderation_status": c.moderation_status,
                "rejection_reason": c.rejection_reason or "",
                "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
                "moderated_at": c.moderated_at.isoformat() if c.moderated_at else None,
                "image_url": f"/api/admin/bookshop/cards/{c.id}/image",
                "category_id": str(cat.id) if cat else None,
                "category_label": cat.label if cat else None,
                "category_macro": cat.macro if cat else None,
            })
        return {"cards": out}


@admin_router.get("/cards/{card_id}/image")
def admin_get_card_image(
    card_id: str, admin: dict = Depends(require_admin)
) -> Response:
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        card = cards_repo.get_by_id(s, cid)
        if card is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        key = card.rendered_image_key
    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    return Response(content=download_bytes(key), media_type="image/png")


@admin_router.post("/cards/{card_id}/approve")
def admin_approve_card(
    card_id: str, admin: dict = Depends(require_admin)
) -> dict:
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        card = cards_repo.get_by_id(s, cid)
        if card is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        cards_repo.approve(s, card)
        return {"ok": True, "status": card.moderation_status}


@admin_router.post("/cards/{card_id}/reject")
def admin_reject_card(
    card_id: str,
    payload: RejectIn,
    admin: dict = Depends(require_admin),
) -> dict:
    try:
        cid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        card = cards_repo.get_by_id(s, cid)
        if card is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        cards_repo.reject(s, card, reason=payload.reason)
        return {"ok": True, "status": card.moderation_status}
