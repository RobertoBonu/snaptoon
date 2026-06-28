"""Add appearance JSONB + copyright_text to projects

Revision ID: a1b2c3d4e5f6
Revises: bc84352880ab
Create Date: 2026-06-28 11:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "bc84352880ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("appearance", JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("copyright_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "copyright_text")
    op.drop_column("projects", "appearance")
