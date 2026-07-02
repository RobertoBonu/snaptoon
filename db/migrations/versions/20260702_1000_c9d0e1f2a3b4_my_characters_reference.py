"""Add reference_storage_key + soft delete + updated_at to cast_archive_entries

Estende CastArchiveEntry per supportare "I miei personaggi": ogni entry ora
può avere una reference AI-generated riusabile tra progetti.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-02 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cast_archive_entries",
        sa.Column("reference_storage_key", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cast_archive_entries",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("cast_archive_entries", "updated_at")
    op.drop_column("cast_archive_entries", "deleted_at")
    op.drop_column("cast_archive_entries", "reference_storage_key")
