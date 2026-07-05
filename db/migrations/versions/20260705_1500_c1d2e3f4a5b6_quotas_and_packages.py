"""Modello economico per-quote + pacchetti extra + stampa/export

Sostituisce il conteggio "crediti/mese astratti" con quote per tipo di
contenuto: libretti_kids / progetti_pro / cover / card. Ogni tipo ha
un counter mensile (reset al rinnovo) e uno extra (accumulato da
pacchetti, non scade).

Nuove tabelle:
- extra_package_purchases : acquisti pacchetti "quota extra"
- print_orders            : ordini stampa fisica (workflow admin)
- export_orders           : esportazioni ePub/Kindle/IDML

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-07-05 15:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b0c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Nuovo valore enum plan: kids_plan (piano dedicato famiglie)
    op.execute("ALTER TYPE plan_enum ADD VALUE IF NOT EXISTS 'kids_plan'")

    # 1. Quote per-tipo su users (4 tipi x 2 counter = 8 nuove colonne)
    for col_name in [
        "quota_libretti_kids_month",
        "quota_libretti_kids_extra",
        "quota_progetti_pro_month",
        "quota_progetti_pro_extra",
        "quota_cover_month",
        "quota_cover_extra",
        "quota_card_month",
        "quota_card_extra",
    ]:
        op.add_column(
            "users",
            sa.Column(col_name, sa.Integer(), nullable=False, server_default="0"),
        )

    # 2. Extra package purchases
    op.create_table(
        "extra_package_purchases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("package_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_eur_cents", sa.Integer(), nullable=False),
        sa.Column(
            "stripe_payment_id", sa.String(length=120),
            nullable=False, server_default="",
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="paid"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_extra_pkg_user", "extra_package_purchases", ["user_id"])
    op.create_index("ix_extra_pkg_type", "extra_package_purchases", ["package_type"])

    # 3. Print orders
    op.create_table(
        "print_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "project_kind", sa.String(length=20), nullable=False, server_default="kids",
        ),
        sa.Column("copies", sa.Integer(), nullable=False),
        sa.Column("price_eur_cents", sa.Integer(), nullable=False),
        sa.Column("shipping_address", JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending",
        ),
        sa.Column(
            "tracking_number", sa.String(length=120), nullable=False, server_default="",
        ),
        sa.Column("admin_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "stripe_payment_id", sa.String(length=120), nullable=False, server_default="",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_print_order_user", "print_orders", ["user_id"])
    op.create_index("ix_print_order_status", "print_orders", ["status"])

    # 4. Export orders
    op.create_table(
        "export_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_kind", sa.String(length=20), nullable=False),
        sa.Column("format_type", sa.String(length=30), nullable=False),
        sa.Column("price_eur_cents", sa.Integer(), nullable=False),
        sa.Column("export_storage_key", sa.String(length=512), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending",
        ),
        sa.Column(
            "stripe_payment_id", sa.String(length=120), nullable=False, server_default="",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_export_order_user", "export_orders", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_export_order_user", table_name="export_orders")
    op.drop_table("export_orders")
    op.drop_index("ix_print_order_status", table_name="print_orders")
    op.drop_index("ix_print_order_user", table_name="print_orders")
    op.drop_table("print_orders")
    op.drop_index("ix_extra_pkg_type", table_name="extra_package_purchases")
    op.drop_index("ix_extra_pkg_user", table_name="extra_package_purchases")
    op.drop_table("extra_package_purchases")
    for col in [
        "quota_card_extra", "quota_card_month",
        "quota_cover_extra", "quota_cover_month",
        "quota_progetti_pro_extra", "quota_progetti_pro_month",
        "quota_libretti_kids_extra", "quota_libretti_kids_month",
    ]:
        op.drop_column("users", col)
