"""Email verification token + nome/cognome anagrafica

Aggiunge:
- users.first_name, users.last_name (opzionali, default "")
- users.email_verified (bool, default true per utenti esistenti)
- users.email_verification_token (token univoco)
- users.email_verified_at (timestamp)

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-07-06 10:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(length=80), nullable=False, server_default=""),
    )
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(length=80), nullable=False, server_default=""),
    )
    # Utenti esistenti = già verificati (server_default true).
    # I nuovi utenti creati dall'ORM parteranno da False (default Python).
    op.add_column(
        "users",
        sa.Column(
            "email_verified", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )
    op.add_column(
        "users",
        sa.Column("email_verification_token", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_email_verification_token",
        "users",
        ["email_verification_token"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_email_verification_token", table_name="users")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
