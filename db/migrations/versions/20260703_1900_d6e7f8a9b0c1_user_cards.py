"""Aggiunge tabella user_cards (figurine collezionabili utenti)

Card 9:16 verticali con banner nome, sub-banner tipo, autore, illustrazione
centrale, 3 stelle, caption, numero progressivo. Pubblicabili nel BookShop
con moderazione admin.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-03 19:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, None] = "c5d6e7f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_cards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("character_type", sa.String(length=120), nullable=False),
        sa.Column("caption", sa.String(length=500), nullable=False, server_default=""),
        sa.Column(
            "author_display",
            sa.String(length=120),
            nullable=False,
            server_default="",
        ),
        sa.Column("progressive_number", sa.Integer(), nullable=False),
        sa.Column("rendered_image_key", sa.String(length=512), nullable=True),
        sa.Column("reference_image_key", sa.String(length=512), nullable=True),
        sa.Column(
            "moderation_status",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "rejection_reason",
            sa.Text(),
            nullable=False,
            server_default="",
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
        sa.UniqueConstraint("progressive_number", name="uq_user_card_number"),
    )
    op.create_index("ix_user_card_owner", "user_cards", ["user_id"])
    op.create_index(
        "ix_user_card_moderation", "user_cards", ["moderation_status"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_card_moderation", table_name="user_cards")
    op.drop_index("ix_user_card_owner", table_name="user_cards")
    op.drop_table("user_cards")
