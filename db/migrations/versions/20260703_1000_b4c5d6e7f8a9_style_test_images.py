"""Aggiunge tabella style_test_images

Supporta il modulo Admin "Test-Style" (QA visivo degli stili preset +
generazione dei sample rappresentativi mostrati nei wizard di scelta
stile).

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-07-03 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "style_test_images",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("style_preset_id", sa.String(length=120), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "scene_params",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "quality",
            sa.String(length=10),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "aspect_ratio",
            sa.String(length=10),
            nullable=False,
            server_default="1:1",
        ),
        sa.Column(
            "is_sample_pro",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_sample_kids",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_by_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
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
        "ix_style_test_preset",
        "style_test_images",
        ["style_preset_id"],
    )
    op.create_index(
        "ix_style_test_sample_pro",
        "style_test_images",
        ["style_preset_id", "is_sample_pro"],
    )
    op.create_index(
        "ix_style_test_sample_kids",
        "style_test_images",
        ["style_preset_id", "is_sample_kids"],
    )


def downgrade() -> None:
    op.drop_index("ix_style_test_sample_kids", table_name="style_test_images")
    op.drop_index("ix_style_test_sample_pro", table_name="style_test_images")
    op.drop_index("ix_style_test_preset", table_name="style_test_images")
    op.drop_table("style_test_images")
