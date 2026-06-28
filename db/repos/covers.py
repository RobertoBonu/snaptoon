"""Repository copertina del progetto."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ..models import Cover, Project


def get_or_create(session: Session, project: Project) -> Cover:
    """Restituisce la cover del progetto, creandola vuota se non esiste."""
    if project.cover is not None:
        return project.cover
    cv = Cover(
        project_id=project.id,
        title="",
        subtitle="",
        author="",
        description="",
        payload={},
    )
    session.add(cv)
    session.flush()
    project.cover = cv
    return cv


def update_text(
    session: Session,
    cover: Cover,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    author: str | None = None,
    description: str | None = None,
) -> None:
    if title is not None:
        cover.title = title
    if subtitle is not None:
        cover.subtitle = subtitle
    if author is not None:
        cover.author = author
    if description is not None:
        cover.description = description


def update_illustration_key(session: Session, cover: Cover, storage_key: str | None) -> None:
    cover.illustration_storage_key = storage_key


def update_rendered_key(session: Session, cover: Cover, storage_key: str | None) -> None:
    cover.rendered_storage_key = storage_key


def update_payload(session: Session, cover: Cover, payload: dict) -> None:
    """Salva il payload (TextBox positions, scene params) come JSONB."""
    cover.payload = payload
