"""Aggiunge tabella project_asset_shares (condivisione copertine e tavole)

Consente agli utenti di condividere copertine (kind='cover') e tavole
(kind='tavola' con page_number) di progetti KIDS o Pro sulla pagina
pubblica /esplora, previa moderazione admin.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-07-02 17:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_asset_shares",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_kind", sa.String(length=20), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column(
            "project_title",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "project_flow",
            sa.String(length=10),
            nullable=False,
            server_default="pro",
        ),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column(
            "share_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "share_caption",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "share_author_role",
            sa.String(length=80),
            nullable=False,
            server_default="",
        ),
        sa.Column("share_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("share_moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "share_rejection_reason",
            sa.Text(),
            nullable=False,
            server_default="",
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
        "ix_project_asset_shares_status",
        "project_asset_shares",
        ["share_status"],
    )
    op.create_index(
        "ix_project_asset_shares_project",
        "project_asset_shares",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_project_asset_shares_project", table_name="project_asset_shares")
    op.drop_index("ix_project_asset_shares_status", table_name="project_asset_shares")
    op.drop_table("project_asset_shares")
