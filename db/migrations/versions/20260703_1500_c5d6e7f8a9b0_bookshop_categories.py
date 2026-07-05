"""Aggiunge tabella bookshop_categories + FK su project_asset_shares

Ridisegna il BookShop come libreria dei webtoon utenti:
  - Macro categorie: kids | young | kidult (hardcoded, target età)
  - Categorie specifiche: gestite dall'admin (es. Fantasy, Slice of life)
  - Ogni webtoon share può essere associato a una categoria

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-07-03 15:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookshop_categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("macro", sa.String(length=20), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.UniqueConstraint("slug", name="uq_bookshop_category_slug"),
    )
    op.create_index(
        "ix_bookshop_category_macro",
        "bookshop_categories",
        ["macro"],
    )

    # FK su project_asset_shares
    op.add_column(
        "project_asset_shares",
        sa.Column(
            "bookshop_category_id",
            UUID(as_uuid=True),
            sa.ForeignKey("bookshop_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("project_asset_shares", "bookshop_category_id")
    op.drop_index("ix_bookshop_category_macro", table_name="bookshop_categories")
    op.drop_table("bookshop_categories")
