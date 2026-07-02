"""Sostituisce UniqueConstraint su (user_id, name) con indice unico parziale

Il constraint originale uq_cast_archive_user_name contava anche le righe
soft-deleted, bloccando la creazione di un nuovo personaggio con lo
stesso nome anche dopo che l'utente aveva eliminato il vecchio. Fix:
indice unico PARZIALE con WHERE deleted_at IS NULL, così solo le righe
"vive" contano.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-02 20:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop del vincolo unique fisico
    op.drop_constraint(
        "uq_cast_archive_user_name", "cast_archive_entries", type_="unique"
    )
    # 2. Sostituisci con indice unico parziale (solo righe non-deleted)
    op.create_index(
        "uq_cast_archive_user_name_active",
        "cast_archive_entries",
        ["user_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_cast_archive_user_name_active", table_name="cast_archive_entries"
    )
    op.create_unique_constraint(
        "uq_cast_archive_user_name", "cast_archive_entries", ["user_id", "name"]
    )
