"""Aggiunge style_preset_id a user_cards

Consente all'utente di scegliere uno stile KIDS al momento della
creazione della figurina. Nullable per retrocompat con card
gia esistenti.

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-03 21:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "d6e7f8a9b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_cards",
        sa.Column("style_preset_id", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_cards", "style_preset_id")
