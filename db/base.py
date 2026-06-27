"""SQLAlchemy Base declarative + tipi e mixin comuni."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base per tutti i model SQLAlchemy del progetto."""


def utcnow() -> datetime:
    """Timestamp UTC current. Funzione, non lambda, per facilitare il mock."""
    return datetime.now(timezone.utc)


# ============================================================
# Mixin riusabili
# ============================================================


class TimestampMixin:
    """Aggiunge created_at automatico."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


class UpdatedAtMixin:
    """Aggiunge updated_at automatico (aggiornato in onupdate)."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Aggiunge id UUID auto-generato come PK."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


# Helper alias per colonne stringa con lunghezza standard
def short_str(length: int = 255) -> type:
    """Helper per colonne stringa con lunghezza limitata."""
    return String(length)
