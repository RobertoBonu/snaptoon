"""Repository archivio personale del cast.

Utente può salvare un personaggio dal cast di un progetto nell'archivio
e riutilizzarlo in altri progetti via 'Importa'.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CastArchiveEntry, User


def list_for_user(session: Session, user: User) -> list[CastArchiveEntry]:
    stmt = (
        select(CastArchiveEntry)
        .where(CastArchiveEntry.user_id == user.id)
        .order_by(CastArchiveEntry.name)
    )
    return list(session.execute(stmt).scalars())


def get_by_name(session: Session, user: User, name: str) -> CastArchiveEntry | None:
    name_lc = name.strip().lower()
    for e in list_for_user(session, user):
        if e.name.strip().lower() == name_lc:
            return e
    return None


def upsert(
    session: Session,
    *,
    user: User,
    name: str,
    visual_description: str = "",
    color_palette: str = "",
    notes: str = "",
) -> CastArchiveEntry:
    name = name.strip()
    if not name:
        raise ValueError("Nome obbligatorio.")
    existing = get_by_name(session, user, name)
    if existing is not None:
        existing.visual_description = visual_description
        existing.color_palette = color_palette
        existing.notes = notes
        return existing

    entry = CastArchiveEntry(
        user_id=user.id,
        name=name,
        visual_description=visual_description,
        color_palette=color_palette,
        notes=notes,
    )
    session.add(entry)
    session.flush()
    return entry


def delete(session: Session, entry: CastArchiveEntry) -> None:
    session.delete(entry)
