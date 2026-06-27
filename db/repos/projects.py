"""Repository progetti — CRUD + duplica + soft delete."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..base import utcnow
from ..models import LengthTarget, Project, Script, User


def _slugify(name: str) -> str:
    """Converte un titolo in slug URL-safe (es. 'La notte del riccio' → 'la-notte-del-riccio')."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "progetto"


def _unique_slug(session: Session, owner_user_id: uuid.UUID, base: str) -> str:
    """Genera slug univoco per owner."""
    slug = base
    n = 2
    while True:
        existing = (
            session.execute(
                select(Project).where(
                    Project.owner_user_id == owner_user_id,
                    Project.slug == slug,
                    Project.deleted_at.is_(None),
                )
            )
            .scalar_one_or_none()
        )
        if existing is None:
            return slug
        slug = f"{base}-{n}"
        n += 1


def create_project(
    session: Session,
    *,
    owner: User,
    name: str,
    length_target: LengthTarget = LengthTarget.medio,
) -> Project:
    """Crea progetto. NON committa."""
    name = name.strip()
    if not name:
        raise ValueError("Il titolo non può essere vuoto.")
    slug = _unique_slug(session, owner.id, _slugify(name))

    project = Project(
        owner_user_id=owner.id,
        slug=slug,
        name=name,
        length_target=length_target,
    )
    session.add(project)
    session.flush()
    return project


def get_by_id(session: Session, project_id: uuid.UUID | str) -> Project | None:
    if isinstance(project_id, str):
        project_id = uuid.UUID(project_id)
    return session.get(Project, project_id)


def get_by_slug(
    session: Session, owner_user_id: uuid.UUID | str, slug: str
) -> Project | None:
    if isinstance(owner_user_id, str):
        owner_user_id = uuid.UUID(owner_user_id)
    stmt = (
        select(Project)
        .where(Project.owner_user_id == owner_user_id)
        .where(Project.slug == slug)
        .where(Project.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def list_by_owner(
    session: Session,
    owner_user_id: uuid.UUID | str,
    *,
    include_deleted: bool = False,
) -> list[Project]:
    if isinstance(owner_user_id, str):
        owner_user_id = uuid.UUID(owner_user_id)
    stmt = (
        select(Project)
        .where(Project.owner_user_id == owner_user_id)
        .order_by(Project.updated_at.desc())
    )
    if not include_deleted:
        stmt = stmt.where(Project.deleted_at.is_(None))
    return list(session.execute(stmt).scalars())


def count_by_owner(session: Session, owner_user_id: uuid.UUID | str) -> int:
    return len(list_by_owner(session, owner_user_id, include_deleted=False))


def rename_project(session: Session, project: Project, new_name: str) -> None:
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Il titolo non può essere vuoto.")
    project.name = new_name


def set_style(session: Session, project: Project, style_id: str | None) -> None:
    project.style_id = style_id


def set_source_text(session: Session, project: Project, text: str) -> None:
    project.source_text = text


def soft_delete(session: Session, project: Project) -> None:
    """Marca eliminato — non distrugge dati. Per recupero futuro."""
    project.deleted_at = utcnow()


def hard_delete(session: Session, project: Project) -> None:
    """Distrugge davvero — solo dopo conferma o per cleanup."""
    session.delete(project)


def duplicate_project(
    session: Session, source: Project, new_name: str
) -> Project:
    """Duplica progetto: copia tutto tranne le vignette generate.

    Vedi specifica funzionale in docs/design/02_USER_FLOWS.md.
    """
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Il nome del duplicato non può essere vuoto.")

    slug = _unique_slug(session, source.owner_user_id, _slugify(new_name))

    dup = Project(
        owner_user_id=source.owner_user_id,
        slug=slug,
        name=new_name,
        length_target=source.length_target,
        page_format=source.page_format,
        style_id=source.style_id,
        source_text=source.source_text,
    )
    session.add(dup)
    session.flush()  # popola dup.id

    # Sceneggiatura
    if source.script:
        new_script = Script(
            project_id=dup.id,
            logline=source.script.logline,
            n_pages=source.script.n_pages,
            n_panels=source.script.n_panels,
            payload=dict(source.script.payload),
        )
        session.add(new_script)

    # Character sheets + reference (le ref si COPIANO — sono "config" del personaggio,
    # non output da rigenerare)
    for cs in source.character_sheets:
        new_cs = type(cs)(
            project_id=dup.id,
            name=cs.name,
            visual_description=cs.visual_description,
            color_palette=cs.color_palette,
            order_idx=cs.order_idx,
        )
        session.add(new_cs)
        session.flush()
        for ref in cs.references:
            session.add(
                type(ref)(
                    character_sheet_id=new_cs.id,
                    slot_number=ref.slot_number,
                    storage_key=ref.storage_key,  # ! stesso key — l'object storage condivide
                    mime_type=ref.mime_type,
                    file_size=ref.file_size,
                    variant_kind=ref.variant_kind,
                )
            )

    # Page layouts
    for pl in source.page_layouts:
        session.add(
            type(pl)(
                project_id=dup.id,
                page_number=pl.page_number,
                grid_id=pl.grid_id,
                show_balloons=pl.show_balloons,
            )
        )

    # Copertina (NON copia illustration/render — vanno rigenerate)
    if source.cover:
        session.add(
            type(source.cover)(
                project_id=dup.id,
                title=source.cover.title,
                subtitle=source.cover.subtitle,
                author=source.cover.author,
                description=source.cover.description,
                payload=dict(source.cover.payload),
            )
        )

    # Vignette: NON copiate (vanno rigenerate ex-novo).

    return dup
