"""Add kids role + kids_templates table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-29 18:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aggiungi valore 'kids' all'enum role_enum (PostgreSQL specifico)
    op.execute("ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'kids'")

    # Crea tabella kids_templates
    # NB: length_target_enum esiste già (creato nella migration initial),
    # quindi create_type=False per evitare 'DuplicateObject'.
    op.create_table(
        "kids_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("n_characters", sa.Integer(), nullable=False),
        sa.Column(
            "length_target",
            sa.Enum(
                "striscia", "breve", "medio", "lungo",
                name="length_target_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("grid_distribution", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("scene_distribution", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_kids_templates_slug"),
    )


def downgrade() -> None:
    op.drop_table("kids_templates")
    # NB: PostgreSQL non supporta rimuovere valori da un enum.
    # Lasciamo 'kids' nell'enum role_enum (innocuo).
