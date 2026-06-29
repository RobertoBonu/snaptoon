"""Repository per stili curati dall'admin."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AdminStyle


def _slugify(label: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return s or "stile"


def list_all(session: Session, *, only_active: bool = False) -> list[AdminStyle]:
    stmt = select(AdminStyle).order_by(AdminStyle.label)
    if only_active:
        stmt = stmt.where(AdminStyle.is_active.is_(True))
    return list(session.execute(stmt).scalars())


def get_by_id(session: Session, style_id: uuid.UUID | str) -> AdminStyle | None:
    if isinstance(style_id, str):
        style_id = uuid.UUID(style_id)
    return session.get(AdminStyle, style_id)


def get_by_slug(session: Session, slug: str) -> AdminStyle | None:
    stmt = select(AdminStyle).where(AdminStyle.slug == slug)
    return session.execute(stmt).scalar_one_or_none()


def create(
    session: Session,
    *,
    label: str,
    category: str,
    expansion: str,
    negative_terms: str = "",
    is_handmade: bool = False,
    notes: str = "",
) -> AdminStyle:
    label = label.strip()
    if not label:
        raise ValueError("Label obbligatoria.")
    if not expansion.strip():
        raise ValueError("Expansion obbligatoria.")

    slug = _slugify(label)
    # Unique slug
    if get_by_slug(session, slug) is not None:
        n = 2
        while get_by_slug(session, f"{slug}_{n}") is not None:
            n += 1
        slug = f"{slug}_{n}"

    style = AdminStyle(
        slug=slug,
        label=label,
        category=category,
        expansion=expansion,
        negative_terms=negative_terms,
        is_handmade=is_handmade,
        notes=notes,
        is_active=True,
    )
    session.add(style)
    session.flush()
    return style


def update(
    session: Session,
    style: AdminStyle,
    *,
    label: str | None = None,
    category: str | None = None,
    expansion: str | None = None,
    negative_terms: str | None = None,
    is_handmade: bool | None = None,
    is_active: bool | None = None,
    notes: str | None = None,
) -> None:
    if label is not None:
        style.label = label
    if category is not None:
        style.category = category
    if expansion is not None:
        style.expansion = expansion
    if negative_terms is not None:
        style.negative_terms = negative_terms
    if is_handmade is not None:
        style.is_handmade = is_handmade
    if is_active is not None:
        style.is_active = is_active
    if notes is not None:
        style.notes = notes


def delete(session: Session, style: AdminStyle) -> None:
    session.delete(style)
