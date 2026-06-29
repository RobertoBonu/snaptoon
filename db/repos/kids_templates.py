"""Repository template Kids."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import KidsTemplate, LengthTarget


def list_all(session: Session, *, only_active: bool = True) -> list[KidsTemplate]:
    stmt = select(KidsTemplate).order_by(
        KidsTemplate.n_characters, KidsTemplate.length_target,
    )
    if only_active:
        stmt = stmt.where(KidsTemplate.is_active.is_(True))
    return list(session.execute(stmt).scalars())


def get_by_id(session: Session, template_id: uuid.UUID | str) -> KidsTemplate | None:
    if isinstance(template_id, str):
        template_id = uuid.UUID(template_id)
    return session.get(KidsTemplate, template_id)


def get_by_slug(session: Session, slug: str) -> KidsTemplate | None:
    stmt = select(KidsTemplate).where(KidsTemplate.slug == slug)
    return session.execute(stmt).scalar_one_or_none()


def upsert(
    session: Session,
    *,
    slug: str,
    label: str,
    n_characters: int,
    length_target: LengthTarget,
    grid_distribution: list,
    scene_distribution: list,
    notes: str = "",
) -> KidsTemplate:
    existing = get_by_slug(session, slug)
    if existing is not None:
        existing.label = label
        existing.n_characters = n_characters
        existing.length_target = length_target
        existing.grid_distribution = grid_distribution
        existing.scene_distribution = scene_distribution
        existing.notes = notes
        return existing

    template = KidsTemplate(
        slug=slug,
        label=label,
        n_characters=n_characters,
        length_target=length_target,
        grid_distribution=grid_distribution,
        scene_distribution=scene_distribution,
        notes=notes,
        is_active=True,
    )
    session.add(template)
    session.flush()
    return template
