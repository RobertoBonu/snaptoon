"""Aggiunge tabella user_covers

Cover standalone create dagli utenti nella nuova sezione "Le mie Cover".
Riusa lo stesso prompt delle copertine dei libretti KIDS ma vive come
entità autonoma con moderazione BookShop opzionale.

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-07-05 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_covers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column(
            "subtitle", sa.String(length=200), nullable=False, server_default=""
        ),
        sa.Column(
            "author", sa.String(length=120), nullable=False, server_default=""
        ),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "style_preset_id", sa.String(length=120), nullable=False
        ),
        sa.Column(
            "author_display",
            sa.String(length=120),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "cast_snapshot", JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("rendered_image_key", sa.String(length=512), nullable=True),
        sa.Column(
            "moderation_status",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "rejection_reason", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column(
            "bookshop_category_id",
            UUID(as_uuid=True),
            sa.ForeignKey("bookshop_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_user_cover_owner", "user_covers", ["user_id"], unique=False
    )
    op.create_index(
        "ix_user_cover_moderation",
        "user_covers",
        ["moderation_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_cover_moderation", table_name="user_covers")
    op.drop_index("ix_user_cover_owner", table_name="user_covers")
    op.drop_table("user_covers")
