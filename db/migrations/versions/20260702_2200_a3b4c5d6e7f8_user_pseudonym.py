"""Aggiunge campo pseudonym (pseudonimo/brand pubblico) all'utente

Sostituisce l'email come autore mostrato sulle card della pagina
Esplora quando l'utente condivide personaggi, copertine o tavole.

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-07-02 22:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "pseudonym",
            sa.String(length=80),
            nullable=False,
            server_default="",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "pseudonym")
