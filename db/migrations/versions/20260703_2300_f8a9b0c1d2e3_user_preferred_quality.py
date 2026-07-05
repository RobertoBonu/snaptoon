"""Aggiunge preferred_quality all'utente

Consente all'utente di scegliere la qualità AI (auto/low/medium/high)
applicata a tutte le generazioni immagine. Il costo in crediti
varia di conseguenza (low+medium=1cr, high=4cr, auto=medium).

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-07-03 23:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "preferred_quality",
            sa.String(length=10),
            nullable=False,
            server_default="medium",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "preferred_quality")
