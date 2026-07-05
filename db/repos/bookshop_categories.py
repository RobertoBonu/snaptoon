"""Repository BookshopCategory."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import BookshopCategory

MACROS = ("kids", "young", "kidult")


def get_by_id(session: Session, cat_id: uuid.UUID) -> BookshopCategory | None:
    stmt = (
        select(BookshopCategory)
        .where(BookshopCategory.id == cat_id)
        .where(BookshopCategory.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def get_by_slug(session: Session, slug: str) -> BookshopCategory | None:
    stmt = (
        select(BookshopCategory)
        .where(BookshopCategory.slug == slug.strip().lower())
        .where(BookshopCategory.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def list_all(
    session: Session,
    *,
    macro: Optional[str] = None,
    only_active: bool = False,
) -> list[BookshopCategory]:
    stmt = select(BookshopCategory).where(BookshopCategory.deleted_at.is_(None))
    if macro:
        stmt = stmt.where(BookshopCategory.macro == macro)
    if only_active:
        stmt = stmt.where(BookshopCategory.is_active.is_(True))
    stmt = stmt.order_by(
        BookshopCategory.macro, BookshopCategory.position, BookshopCategory.label
    )
    return list(session.execute(stmt).scalars())


def create(
    session: Session,
    *,
    macro: str,
    slug: str,
    label: str,
    description: str = "",
    position: int = 0,
    is_active: bool = True,
) -> BookshopCategory:
    if macro not in MACROS:
        raise ValueError(f"macro non valida: {macro} (attese: {MACROS})")
    slug = slug.strip().lower()
    if not slug:
        raise ValueError("slug obbligatorio")
    if get_by_slug(session, slug) is not None:
        raise ValueError(f"slug già esistente: {slug}")
    cat = BookshopCategory(
        macro=macro,
        slug=slug,
        label=label.strip(),
        description=description.strip(),
        position=position,
        is_active=is_active,
    )
    session.add(cat)
    session.flush()
    return cat


def update(
    session: Session,
    cat: BookshopCategory,
    *,
    macro: Optional[str] = None,
    label: Optional[str] = None,
    description: Optional[str] = None,
    position: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> None:
    if macro is not None:
        if macro not in MACROS:
            raise ValueError(f"macro non valida: {macro}")
        cat.macro = macro
    if label is not None:
        cat.label = label.strip()
    if description is not None:
        cat.description = description.strip()
    if position is not None:
        cat.position = position
    if is_active is not None:
        cat.is_active = is_active


def soft_delete(session: Session, cat: BookshopCategory) -> None:
    cat.deleted_at = datetime.now(timezone.utc)
