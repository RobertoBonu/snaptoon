"""Free-to-play counters + subscription lifecycle + nuovi piani

Aggiunge:
- Colonne ftp_striscia_used / ftp_card_used / ftp_cover_used (counter azioni FTP)
- Colonne subscription_status / subscription_plan_requested /
  subscription_activated_at / subscription_rejection_reason
- Nuovi valori enum Plan: free_to_play, base, premium

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-07-05 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, None] = "a9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Estendi enum Plan con i nuovi valori
    op.execute("ALTER TYPE plan_enum ADD VALUE IF NOT EXISTS 'free_to_play'")
    op.execute("ALTER TYPE plan_enum ADD VALUE IF NOT EXISTS 'base'")
    op.execute("ALTER TYPE plan_enum ADD VALUE IF NOT EXISTS 'premium'")

    # 2. Counter Free-To-Play
    op.add_column(
        "users",
        sa.Column(
            "ftp_striscia_used", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "ftp_card_used", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "ftp_cover_used", sa.Integer(), nullable=False, server_default="0"
        ),
    )

    # 3. Subscription lifecycle
    # Gli utenti esistenti sono considerati già attivi (retrocompat)
    op.add_column(
        "users",
        sa.Column(
            "subscription_status",
            sa.String(length=30),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_plan_requested",
            sa.Enum(
                "free_trial",
                "creator",
                "pro",
                "free_to_play",
                "base",
                "premium",
                name="plan_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_activated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_rejection_reason",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )

    # 4. Per i NUOVI utenti creati dopo questa migrazione il default reale è
    #    pending_approval — impostato dall'ORM (default=). Il server_default
    #    "active" qui sopra serve SOLO a retrocompatibilizzare gli utenti
    #    esistenti (che sono già stati approvati implicitamente).


def downgrade() -> None:
    op.drop_column("users", "subscription_rejection_reason")
    op.drop_column("users", "subscription_activated_at")
    op.drop_column("users", "subscription_plan_requested")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "ftp_cover_used")
    op.drop_column("users", "ftp_card_used")
    op.drop_column("users", "ftp_striscia_used")
    # Non rimuoviamo i valori dell'enum plan_enum: Postgres non supporta
    # DROP VALUE su enum. Restano innocui.
