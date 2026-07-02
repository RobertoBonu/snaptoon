"""Repository ProjectAssetShare (condivisione community cover + tavole).

Ogni share ha kind='cover' o kind='tavola' (con page_number). Ownership è
per user_id, ma l'admin può vederli tutti per la moderazione.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ProjectAssetShare, Project, User


def get_by_id(
    session: Session, share_id: uuid.UUID
) -> ProjectAssetShare | None:
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.id == share_id)
        .where(ProjectAssetShare.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def get_by_user_and_id(
    session: Session, user: User, share_id: uuid.UUID
) -> ProjectAssetShare | None:
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.id == share_id)
        .where(ProjectAssetShare.user_id == user.id)
        .where(ProjectAssetShare.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def get_existing_for_asset(
    session: Session,
    project: Project,
    asset_kind: str,
    page_number: int | None,
) -> ProjectAssetShare | None:
    """Verifica se esiste già una share per il singolo asset (evita duplicati).

    Ignora quelle deleted / rejected (l'utente può rifare submit dopo rifiuto).
    """
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.project_id == project.id)
        .where(ProjectAssetShare.asset_kind == asset_kind)
        .where(ProjectAssetShare.deleted_at.is_(None))
        .where(ProjectAssetShare.share_status.in_(["pending", "published"]))
    )
    if page_number is None:
        stmt = stmt.where(ProjectAssetShare.page_number.is_(None))
    else:
        stmt = stmt.where(ProjectAssetShare.page_number == page_number)
    return session.execute(stmt).scalar_one_or_none()


def submit(
    session: Session,
    *,
    project: Project,
    user: User,
    asset_kind: str,
    page_number: int | None,
    storage_key: str,
    project_flow: str,
    caption: str = "",
    author_role: str = "",
) -> ProjectAssetShare:
    """Crea o riattiva una share per l'asset dato (idempotente su
    rejected → torna pending)."""
    # Cerca anche fra i rejected: se esiste, ne riattiva la richiesta
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.project_id == project.id)
        .where(ProjectAssetShare.asset_kind == asset_kind)
        .where(ProjectAssetShare.deleted_at.is_(None))
    )
    if page_number is None:
        stmt = stmt.where(ProjectAssetShare.page_number.is_(None))
    else:
        stmt = stmt.where(ProjectAssetShare.page_number == page_number)
    existing = session.execute(stmt).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing is not None:
        existing.share_status = "pending"
        existing.share_caption = caption.strip()[:500]
        existing.share_author_role = author_role.strip()[:80]
        existing.share_submitted_at = now
        existing.share_moderated_at = None
        existing.share_rejection_reason = ""
        existing.storage_key = storage_key
        existing.project_title = project.name
        existing.project_flow = project_flow
        return existing

    share = ProjectAssetShare(
        project_id=project.id,
        user_id=user.id,
        asset_kind=asset_kind,
        page_number=page_number,
        project_title=project.name,
        project_flow=project_flow,
        storage_key=storage_key,
        share_status="pending",
        share_caption=caption.strip()[:500],
        share_author_role=author_role.strip()[:80],
        share_submitted_at=now,
    )
    session.add(share)
    session.flush()
    return share


def unshare(session: Session, share: ProjectAssetShare) -> None:
    """Rimuove la condivisione (soft-delete). Non tocca la storage key
    del progetto (l'immagine resta nel progetto dell'utente)."""
    share.deleted_at = datetime.now(timezone.utc)


def approve(session: Session, share: ProjectAssetShare) -> None:
    share.share_status = "published"
    share.share_moderated_at = datetime.now(timezone.utc)
    share.share_rejection_reason = ""


def reject(
    session: Session, share: ProjectAssetShare, reason: str = ""
) -> None:
    share.share_status = "rejected"
    share.share_moderated_at = datetime.now(timezone.utc)
    share.share_rejection_reason = reason.strip()[:1000]


def list_by_user(
    session: Session, user: User
) -> list[ProjectAssetShare]:
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.user_id == user.id)
        .where(ProjectAssetShare.deleted_at.is_(None))
        .order_by(ProjectAssetShare.share_submitted_at.desc())
    )
    return list(session.execute(stmt).scalars())


def list_by_status(
    session: Session, status: str
) -> list[ProjectAssetShare]:
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.share_status == status)
        .where(ProjectAssetShare.deleted_at.is_(None))
        .order_by(ProjectAssetShare.share_submitted_at.desc())
    )
    return list(session.execute(stmt).scalars())


def list_all_not_deleted(session: Session) -> list[ProjectAssetShare]:
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.deleted_at.is_(None))
        .order_by(ProjectAssetShare.share_submitted_at.desc())
    )
    return list(session.execute(stmt).scalars())


def list_published_by_kind(
    session: Session, asset_kind: str
) -> list[ProjectAssetShare]:
    stmt = (
        select(ProjectAssetShare)
        .where(ProjectAssetShare.share_status == "published")
        .where(ProjectAssetShare.asset_kind == asset_kind)
        .where(ProjectAssetShare.deleted_at.is_(None))
        .where(ProjectAssetShare.storage_key.is_not(None))
        .order_by(ProjectAssetShare.share_moderated_at.desc())
    )
    return list(session.execute(stmt).scalars())
