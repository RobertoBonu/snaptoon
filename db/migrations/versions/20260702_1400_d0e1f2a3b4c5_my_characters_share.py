"""Aggiunge condivisione /esplora ai cast_archive_entries

Aggiunge 6 colonne per gestire il flusso "Condividi personaggio → Admin
approva/rifiuta → visibile su /esplora".

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-07-02 14:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "share_status",
            sa.String(length=20),
            nullable=False,
            server_default="not_shared",
        ),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "share_caption",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "share_author_role",
            sa.String(length=80),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "share_submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "share_moderated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "share_rejection_reason",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )
    op.create_index(
        "ix_cast_archive_share_status",
        "cast_archive_entries",
        ["share_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_cast_archive_share_status", table_name="cast_archive_entries")
    op.drop_column("cast_archive_entries", "share_rejection_reason")
    op.drop_column("cast_archive_entries", "share_moderated_at")
    op.drop_column("cast_archive_entries", "share_submitted_at")
    op.drop_column("cast_archive_entries", "share_author_role")
    op.drop_column("cast_archive_entries", "share_caption")
    op.drop_column("cast_archive_entries", "share_status")
