"""Repository "I miei personaggi" (archivio riusabile del cast).

L'utente può:
  - Creare personaggi da descrizione testuale (AI genera reference)
  - Creare personaggi da foto reale (foto NON archiviata, cancellata subito)
  - Importarli in progetti KIDS o Pro (copia name+description+reference)
  - Modificarli, rigenerare la reference, cancellarli (soft delete)

Retrocompatibile con il vecchio archivio: le entry esistenti senza
reference_storage_key continuano a funzionare (senza reference).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CastArchiveEntry, User


def list_for_user(session: Session, user: User) -> list[CastArchiveEntry]:
    """Personaggi non-soft-deleted dell'utente, ordinati per nome."""
    stmt = (
        select(CastArchiveEntry)
        .where(CastArchiveEntry.user_id == user.id)
        .where(CastArchiveEntry.deleted_at.is_(None))
        .order_by(CastArchiveEntry.name)
    )
    return list(session.execute(stmt).scalars())


def get_by_id(
    session: Session, user: User, entry_id: uuid.UUID
) -> CastArchiveEntry | None:
    """Lookup per id (rispetta ownership + soft delete)."""
    stmt = (
        select(CastArchiveEntry)
        .where(CastArchiveEntry.id == entry_id)
        .where(CastArchiveEntry.user_id == user.id)
        .where(CastArchiveEntry.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def get_by_name(session: Session, user: User, name: str) -> CastArchiveEntry | None:
    name_lc = name.strip().lower()
    for e in list_for_user(session, user):
        if e.name.strip().lower() == name_lc:
            return e
    return None


def create(
    session: Session,
    *,
    user: User,
    name: str,
    visual_description: str = "",
    color_palette: str = "",
    notes: str = "",
) -> CastArchiveEntry:
    """Crea un nuovo personaggio (senza reference: viene aggiunta dopo)."""
    name = name.strip()
    if not name:
        raise ValueError("Nome obbligatorio.")
    if get_by_name(session, user, name):
        raise ValueError(f"Personaggio con nome '{name}' esiste già.")
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


def upsert(
    session: Session,
    *,
    user: User,
    name: str,
    visual_description: str = "",
    color_palette: str = "",
    notes: str = "",
) -> CastArchiveEntry:
    """Aggiorna se esiste, altrimenti crea. Retrocompat col vecchio codice."""
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


def update_metadata(
    session: Session,
    entry: CastArchiveEntry,
    *,
    name: str | None = None,
    visual_description: str | None = None,
) -> None:
    """Aggiorna nome e/o descrizione di un personaggio."""
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("Nome non può essere vuoto.")
        entry.name = name
    if visual_description is not None:
        entry.visual_description = visual_description


def set_reference_key(
    session: Session, entry: CastArchiveEntry, storage_key: str | None
) -> None:
    entry.reference_storage_key = storage_key


def soft_delete(session: Session, entry: CastArchiveEntry) -> None:
    entry.deleted_at = datetime.now(timezone.utc)


# === Condivisione su /esplora ===


def submit_for_sharing(
    session: Session,
    entry: CastArchiveEntry,
    *,
    caption: str = "",
    author_role: str = "",
) -> None:
    """Marca il personaggio come 'in attesa' di approvazione admin."""
    entry.share_status = "pending"
    entry.share_caption = caption.strip()[:500]
    entry.share_author_role = author_role.strip()[:80]
    entry.share_submitted_at = datetime.now(timezone.utc)
    entry.share_moderated_at = None
    entry.share_rejection_reason = ""


def unshare(session: Session, entry: CastArchiveEntry) -> None:
    """Rimuove la condivisione (torna 'not_shared', mantiene il record)."""
    entry.share_status = "not_shared"
    entry.share_moderated_at = None
    entry.share_rejection_reason = ""


def approve_sharing(session: Session, entry: CastArchiveEntry) -> None:
    entry.share_status = "published"
    entry.share_moderated_at = datetime.now(timezone.utc)
    entry.share_rejection_reason = ""


def reject_sharing(
    session: Session, entry: CastArchiveEntry, reason: str = ""
) -> None:
    entry.share_status = "rejected"
    entry.share_moderated_at = datetime.now(timezone.utc)
    entry.share_rejection_reason = reason.strip()[:1000]


def list_pending_shares(session: Session) -> list[CastArchiveEntry]:
    """Personaggi in attesa di moderazione, ordinati per data di submit."""
    from sqlalchemy import select

    stmt = (
        select(CastArchiveEntry)
        .where(CastArchiveEntry.share_status == "pending")
        .where(CastArchiveEntry.deleted_at.is_(None))
        .order_by(CastArchiveEntry.share_submitted_at)
    )
    return list(session.execute(stmt).scalars())


def list_published_shares(session: Session) -> list[CastArchiveEntry]:
    """Personaggi pubblicati (visibili su /esplora)."""
    from sqlalchemy import select

    stmt = (
        select(CastArchiveEntry)
        .where(CastArchiveEntry.share_status == "published")
        .where(CastArchiveEntry.deleted_at.is_(None))
        .where(CastArchiveEntry.reference_storage_key.is_not(None))
        .order_by(CastArchiveEntry.share_moderated_at.desc())
    )
    return list(session.execute(stmt).scalars())


def get_shared_by_id(
    session: Session, entry_id
) -> CastArchiveEntry | None:
    """Lookup per admin (senza ownership check — l'ownership è dell'utente
    che ha condiviso, ma l'admin può moderare tutti)."""
    import uuid as _uuid
    from sqlalchemy import select

    if isinstance(entry_id, str):
        try:
            entry_id = _uuid.UUID(entry_id)
        except ValueError:
            return None

    stmt = (
        select(CastArchiveEntry)
        .where(CastArchiveEntry.id == entry_id)
        .where(CastArchiveEntry.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


# Retrocompatibilità: alcune parti del codice chiamano ancora delete(entry)
def delete(session: Session, entry: CastArchiveEntry) -> None:
    soft_delete(session, entry)
