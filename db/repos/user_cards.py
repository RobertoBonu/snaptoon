"""Repository UserCard (figurine collezionabili)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import User, UserCard


def get_by_id(session: Session, card_id: uuid.UUID) -> UserCard | None:
    stmt = (
        select(UserCard)
        .where(UserCard.id == card_id)
        .where(UserCard.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def get_by_user_and_id(
    session: Session, user: User, card_id: uuid.UUID
) -> UserCard | None:
    stmt = (
        select(UserCard)
        .where(UserCard.id == card_id)
        .where(UserCard.user_id == user.id)
        .where(UserCard.deleted_at.is_(None))
    )
    return session.execute(stmt).scalar_one_or_none()


def list_by_user(session: Session, user: User) -> list[UserCard]:
    stmt = (
        select(UserCard)
        .where(UserCard.user_id == user.id)
        .where(UserCard.deleted_at.is_(None))
        .order_by(UserCard.created_at.desc())
    )
    return list(session.execute(stmt).scalars())


def list_by_moderation(
    session: Session, status: str
) -> list[UserCard]:
    stmt = (
        select(UserCard)
        .where(UserCard.moderation_status == status)
        .where(UserCard.deleted_at.is_(None))
        .order_by(UserCard.submitted_at.desc())
    )
    return list(session.execute(stmt).scalars())


def list_published(
    session: Session,
    *,
    macro: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    limit: int = 60,
) -> list[UserCard]:
    """Card pubblicate (visibili nel BookShop). Ordinamento: più recenti."""
    stmt = (
        select(UserCard)
        .where(UserCard.moderation_status == "published")
        .where(UserCard.deleted_at.is_(None))
    )
    if category_id is not None:
        stmt = stmt.where(UserCard.bookshop_category_id == category_id)
    stmt = stmt.order_by(UserCard.moderated_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars())


def next_progressive_number(session: Session) -> int:
    """Global auto-increment: max + 1. Racy in teoria, ma il constraint
    unique sul campo garantisce che due creazioni concomitanti falliranno
    con IntegrityError sull'insert — a quel punto si riprova."""
    stmt = select(func.max(UserCard.progressive_number))
    result = session.execute(stmt).scalar()
    return (result or 0) + 1


def create(
    session: Session,
    *,
    user: User,
    name: str,
    character_type: str,
    caption: str,
    author_display: str,
) -> UserCard:
    card = UserCard(
        user_id=user.id,
        name=name.strip()[:120],
        character_type=character_type.strip()[:120],
        caption=caption.strip()[:500],
        author_display=author_display.strip()[:120],
        progressive_number=next_progressive_number(session),
    )
    session.add(card)
    session.flush()
    return card


def update_metadata(
    session: Session,
    card: UserCard,
    *,
    name: Optional[str] = None,
    character_type: Optional[str] = None,
    caption: Optional[str] = None,
) -> None:
    if name is not None:
        card.name = name.strip()[:120]
    if character_type is not None:
        card.character_type = character_type.strip()[:120]
    if caption is not None:
        card.caption = caption.strip()[:500]


def set_rendered_key(
    session: Session, card: UserCard, key: str | None
) -> None:
    card.rendered_image_key = key


def set_reference_key(
    session: Session, card: UserCard, key: str | None
) -> None:
    card.reference_image_key = key


def submit_for_moderation(
    session: Session, card: UserCard, *, category_id: uuid.UUID
) -> None:
    card.moderation_status = "pending"
    card.submitted_at = datetime.now(timezone.utc)
    card.moderated_at = None
    card.rejection_reason = ""
    card.bookshop_category_id = category_id


def unpublish(session: Session, card: UserCard) -> None:
    """Ritira la card dalla pubblicazione (torna a draft)."""
    card.moderation_status = "draft"
    card.moderated_at = None
    card.rejection_reason = ""


def approve(session: Session, card: UserCard) -> None:
    card.moderation_status = "published"
    card.moderated_at = datetime.now(timezone.utc)
    card.rejection_reason = ""


def reject(session: Session, card: UserCard, reason: str) -> None:
    card.moderation_status = "rejected"
    card.moderated_at = datetime.now(timezone.utc)
    card.rejection_reason = reason.strip()[:1000]


def soft_delete(session: Session, card: UserCard) -> None:
    card.deleted_at = datetime.now(timezone.utc)
