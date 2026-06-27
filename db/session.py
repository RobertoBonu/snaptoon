"""Engine + session factory SQLAlchemy.

Su Replit la DATABASE_URL è popolata automaticamente quando si aggiunge
il Postgres managed. In locale (dev) puoi sovrascrivere con .env.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    """Restituisce la connection string. Replit la inietta come DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL non impostato. Su Replit aggiungi il Postgres managed; "
            "in locale aggiungilo a .env."
        )
    # Replit a volte usa lo schema `postgres://` legacy: SQLAlchemy 2 vuole `postgresql://`
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Engine singleton, lazy-init."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            future=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Session factory singleton, lazy-init."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionFactory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager che commit+close automatici, rollback su eccezione.

    Uso:
        with session_scope() as s:
            user = s.get(User, user_id)
            user.email = new_email
        # auto-commit + close
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
