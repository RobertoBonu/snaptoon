"""add card fields to esplora_assets (asset_type, author_name, author_role)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-01 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "esplora_assets",
        sa.Column("asset_type", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "esplora_assets",
        sa.Column("author_name", sa.String(length=160), nullable=False, server_default=""),
    )
    op.add_column(
        "esplora_assets",
        sa.Column("author_role", sa.String(length=80), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("esplora_assets", "author_role")
    op.drop_column("esplora_assets", "author_name")
    op.drop_column("esplora_assets", "asset_type")
