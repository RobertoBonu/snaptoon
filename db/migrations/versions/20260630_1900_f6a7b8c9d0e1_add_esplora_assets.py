"""Add esplora_assets table + seed

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-30 19:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED = {
    "copertine": [
        ("Cover · Avventura per bambini", "Avventura per bambini · Stile Flat"),
        ("Cover · Manga shonen", "Manga shonen · Stile Tokyo-Mecha"),
        ("Cover · Romance", "Romance · Stile Acquerello"),
        ("Cover · Sci-fi", "Sci-fi · Stile Cyber-Neon"),
        ("Cover · Horror", "Horror · Stile Noir"),
        ("Cover · Fantasy", "Fantasy · Stile Inchiostro"),
    ],
    "tavole": [
        ("Tavola · Splash + 2x2", "Splash + 2x2 · Stile Noir"),
        ("Tavola · Griglia 1+2", "Griglia 1+2 · Stile Disney"),
        ("Tavola · Fila singola", "Fila singola · Stile Manga"),
        ("Tavola · Mosaico 3x3", "Mosaico 3x3 · Stile Acquerello"),
    ],
    "personaggi": [
        ("Mia", "Eroina ribelle, 17 anni"),
        ("Kael", "Mercenario cibernetico"),
        ("Nonna Rosa", "Custode dei segreti"),
        ("Dr. Vex", "Antagonista geniale"),
        ("Bun", "Robot da compagnia"),
        ("Aria", "Pilota stellare"),
        ("Otto", "Detective stanco"),
        ("Lumi", "Spirito del bosco"),
    ],
}


def upgrade() -> None:
    table = op.create_table(
        "esplora_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("caption", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_esplora_assets_section", "esplora_assets", ["section"])
    op.create_index(
        "ix_esplora_assets_section_position", "esplora_assets", ["section", "position"]
    )

    rows = []
    for section, items in SEED.items():
        for i, (title, caption) in enumerate(items, start=1):
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "section": section,
                    "title": title,
                    "caption": caption,
                    "position": i,
                    "storage_key": None,
                    "prompt": "",
                    "is_active": True,
                }
            )
    op.bulk_insert(table, rows)


def downgrade() -> None:
    op.drop_index("ix_esplora_assets_section_position", table_name="esplora_assets")
    op.drop_index("ix_esplora_assets_section", table_name="esplora_assets")
    op.drop_table("esplora_assets")
