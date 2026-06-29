"""Repository utenti — operazioni CRUD + helper auth."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..base import utcnow
from ..models import Plan, Role, User


def get_by_id(session: Session, user_id: uuid.UUID | str) -> User | None:
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    return session.get(User, user_id)


def get_by_email(session: Session, email: str) -> User | None:
    """Lookup case-insensitive su email."""
    email = email.strip().lower()
    stmt = select(User).where(User.email == email)
    return session.execute(stmt).scalar_one_or_none()


def create_user(
    session: Session,
    *,
    email: str,
    password_hash: str,
    plan: Plan = Plan.free_trial,
    initial_credits: int = 30,
    is_admin: bool = False,
    must_change_password: bool = True,
) -> User:
    """Crea utente nuovo. NOTA: NON committa — il chiamante decide.

    `password_hash` è già bcrypt-hashed (vedi auth.passwords.hash_password).
    """
    user = User(
        email=email.strip().lower(),
        password_hash=password_hash,
        plan=plan,
        credits_total_this_period=initial_credits,
        credits_used_this_period=0,
        is_admin=is_admin,
        is_active=True,
        must_change_password=must_change_password,
        has_seen_onboarding=False,
    )
    session.add(user)
    session.flush()  # popola user.id
    return user


def list_all(session: Session, *, include_inactive: bool = True) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc())
    if not include_inactive:
        stmt = stmt.where(User.is_active.is_(True))
    return list(session.execute(stmt).scalars())


def set_password_hash(session: Session, user: User, new_password_hash: str) -> None:
    user.password_hash = new_password_hash
    user.must_change_password = False


def mark_login(session: Session, user: User) -> None:
    user.last_login_at = utcnow()


def set_active(session: Session, user: User, active: bool) -> None:
    user.is_active = active


def set_plan(session: Session, user: User, plan: Plan, new_period_credits: int) -> None:
    """Cambia piano (LEGACY) e RIPARTE il periodo da zero crediti usati."""
    user.plan = plan
    user.credits_total_this_period = new_period_credits
    user.credits_used_this_period = 0
    user.period_started_at = utcnow()


def set_role(
    session: Session,
    user: User,
    role: Role,
    *,
    reset_period_credits: int | None = None,
) -> None:
    """Cambia ruolo dell'utente. Aggiorna anche is_admin per backward compat.

    Se `reset_period_credits` è impostato, riparte il periodo crediti.
    """
    user.role = role
    user.is_admin = (role == Role.admin)
    if reset_period_credits is not None:
        user.credits_total_this_period = reset_period_credits
        user.credits_used_this_period = 0
        user.period_started_at = utcnow()


def mark_onboarding_seen(session: Session, user: User) -> None:
    user.has_seen_onboarding = True


def count_active_in_last_days(session: Session, days: int = 7) -> int:
    """Per dashboard admin."""
    from datetime import timedelta
    threshold = utcnow() - timedelta(days=days)
    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .where(User.last_login_at.isnot(None))
        .where(User.last_login_at >= threshold)
    )
    return len(list(session.execute(stmt).scalars()))
