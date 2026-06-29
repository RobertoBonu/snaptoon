"""Add role enum to users + backfill from is_admin/plan

Revision ID: c3d4e5f6a7b8
Revises: b7e8f9a0c1d2
Create Date: 2026-06-29 11:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b7e8f9a0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea enum role
    role_enum = sa.Enum(
        "admin", "autore_base", "autore_premium", "editore",
        name="role_enum",
    )
    role_enum.create(op.get_bind(), checkfirst=True)

    # Aggiungi colonna role (NULL temporaneamente per backfill)
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("admin", "autore_base", "autore_premium", "editore", name="role_enum"),
            nullable=True,
        ),
    )

    # Backfill basato su is_admin + plan
    op.execute("""
        UPDATE users SET role =
            CASE
                WHEN is_admin = TRUE THEN 'admin'::role_enum
                WHEN plan = 'pro' THEN 'autore_premium'::role_enum
                ELSE 'autore_base'::role_enum
            END
        WHERE role IS NULL
    """)

    # Adesso NOT NULL + default
    op.alter_column("users", "role", nullable=False, server_default="autore_base")


def downgrade() -> None:
    op.drop_column("users", "role")
    sa.Enum(name="role_enum").drop(op.get_bind(), checkfirst=True)
