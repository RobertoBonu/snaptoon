"""Repository StyleTestImage (Admin Test-Style)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import StyleTestImage


def get_by_id(session: Session, image_id: uuid.UUID) -> StyleTestImage | None:
    stmt = (
        select(StyleTestImage)
        .where(StyleTestImage.id == image_id)
        .where(StyleTestImage.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def list_all(
    session: Session,
    *,
    style_preset_id: Optional[str] = None,
    only_samples_flow: Optional[str] = None,  # "pro" | "kids"
) -> list[StyleTestImage]:
    """Lista test images. Filtri opzionali per preset e/o flag sample."""
    stmt = select(StyleTestImage).where(StyleTestImage.deleted_at.is_(None))
    if style_preset_id:
        stmt = stmt.where(StyleTestImage.style_preset_id == style_preset_id)
    if only_samples_flow == "pro":
        stmt = stmt.where(StyleTestImage.is_sample_pro.is_(True))
    elif only_samples_flow == "kids":
        stmt = stmt.where(StyleTestImage.is_sample_kids.is_(True))
    stmt = stmt.order_by(StyleTestImage.created_at.desc())
    return list(session.execute(stmt).scalars())


def create(
    session: Session,
    *,
    style_preset_id: str,
    storage_key: str,
    prompt: str = "",
    scene_params: Optional[dict] = None,
    quality: str = "medium",
    aspect_ratio: str = "1:1",
    notes: str = "",
    created_by_user_id: Optional[uuid.UUID] = None,
) -> StyleTestImage:
    img = StyleTestImage(
        style_preset_id=style_preset_id,
        storage_key=storage_key,
        prompt=prompt,
        scene_params=scene_params or {},
        quality=quality,
        aspect_ratio=aspect_ratio,
        notes=notes,
        created_by_user_id=created_by_user_id,
    )
    session.add(img)
    session.flush()
    return img


def update_notes(
    session: Session, image: StyleTestImage, notes: str
) -> None:
    image.notes = notes.strip()[:2000]


def assign_as_sample(
    session: Session,
    image: StyleTestImage,
    *,
    flow: str,  # "pro" | "kids"
) -> None:
    """Assegna l'immagine come sample per il flow indicato.

    Prima resetta il flag per tutte le altre immagini dello stesso preset
    nello stesso flow (garantisce unicità).
    """
    if flow not in ("pro", "kids"):
        raise ValueError(f"flow non valido: {flow}")

    # Reset flag su tutte le altre immagini dello stesso preset
    stmt = (
        select(StyleTestImage)
        .where(StyleTestImage.style_preset_id == image.style_preset_id)
        .where(StyleTestImage.id != image.id)
        .where(StyleTestImage.deleted_at.is_(None))
    )
    for other in session.execute(stmt).scalars():
        if flow == "pro":
            other.is_sample_pro = False
        else:
            other.is_sample_kids = False

    # Setta il flag sull'immagine target
    if flow == "pro":
        image.is_sample_pro = True
    else:
        image.is_sample_kids = True


def unassign_as_sample(
    session: Session, image: StyleTestImage, *, flow: str
) -> None:
    if flow not in ("pro", "kids"):
        raise ValueError(f"flow non valido: {flow}")
    if flow == "pro":
        image.is_sample_pro = False
    else:
        image.is_sample_kids = False


def get_sample_for(
    session: Session, style_preset_id: str, flow: str
) -> StyleTestImage | None:
    """Ritorna il sample assegnato per (style, flow) o None."""
    stmt = (
        select(StyleTestImage)
        .where(StyleTestImage.style_preset_id == style_preset_id)
        .where(StyleTestImage.deleted_at.is_(None))
    )
    if flow == "pro":
        stmt = stmt.where(StyleTestImage.is_sample_pro.is_(True))
    elif flow == "kids":
        stmt = stmt.where(StyleTestImage.is_sample_kids.is_(True))
    else:
        return None
    return session.execute(stmt).scalar_one_or_none()


def soft_delete(session: Session, image: StyleTestImage) -> None:
    image.deleted_at = datetime.now(timezone.utc)
    # Anche il flag sample viene rimosso per non lasciarlo appeso
    image.is_sample_pro = False
    image.is_sample_kids = False
