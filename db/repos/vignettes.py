"""Repository vignette generate.

Le vignette generate AI vivono in object storage (PNG) + record DB con:
- storage_key (per fetch)
- prompt_hash (per cache lookup)
- metadati (provider, model, quality, aspect_ratio)

Cache lookup: dato (project, page, panel, prompt_hash), se esiste vignette
con stesso prompt_hash → riusa, niente nuovo addebito crediti.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Project, Vignette


def get(
    session: Session,
    *,
    project: Project,
    page_number: int,
    panel_number: int,
) -> Vignette | None:
    """Lookup vignetta per coordinate (project, page, panel)."""
    stmt = (
        select(Vignette)
        .where(Vignette.project_id == project.id)
        .where(Vignette.page_number == page_number)
        .where(Vignette.panel_number == panel_number)
    )
    return session.execute(stmt).scalar_one_or_none()


def list_for_project(
    session: Session, project: Project
) -> list[Vignette]:
    stmt = (
        select(Vignette)
        .where(Vignette.project_id == project.id)
        .order_by(Vignette.page_number, Vignette.panel_number)
    )
    return list(session.execute(stmt).scalars())


def count_generated(session: Session, project: Project) -> int:
    return len(list_for_project(session, project))


def find_by_prompt_hash(
    session: Session,
    *,
    project: Project,
    prompt_hash: str,
) -> Vignette | None:
    """Cache lookup: dato un hash di prompt+refs+quality+size, esiste vignette
    cached in questo progetto?

    Usato dal generator per evitare di rifare lo stesso lavoro AI.
    """
    stmt = (
        select(Vignette)
        .where(Vignette.project_id == project.id)
        .where(Vignette.prompt_hash == prompt_hash)
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def upsert(
    session: Session,
    *,
    project: Project,
    page_number: int,
    panel_number: int,
    storage_key: str,
    prompt_hash: str,
    quality: str = "medium",
    aspect_ratio_key: str = "1_1",
    provider: str = "openai",
    model: str = "gpt-image-2",
) -> Vignette:
    """Crea o aggiorna la vignetta per (project, page, panel)."""
    existing = get(
        session,
        project=project,
        page_number=page_number,
        panel_number=panel_number,
    )
    if existing is not None:
        existing.storage_key = storage_key
        existing.prompt_hash = prompt_hash
        existing.quality = quality
        existing.aspect_ratio_key = aspect_ratio_key
        existing.provider = provider
        existing.model = model
        return existing

    v = Vignette(
        project_id=project.id,
        page_number=page_number,
        panel_number=panel_number,
        storage_key=storage_key,
        prompt_hash=prompt_hash,
        quality=quality,
        aspect_ratio_key=aspect_ratio_key,
        provider=provider,
        model=model,
    )
    session.add(v)
    session.flush()
    return v


def delete(session: Session, vignette: Vignette) -> None:
    session.delete(vignette)
