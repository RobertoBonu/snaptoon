"""Seed admin iniziale.

Da eseguire DOPO `alembic upgrade head`. Idempotente: se l'admin esiste già
e ha la stessa email, non fa nulla.

Uso:
    python scripts/seed_admin.py

Variabili env opzionali:
    SEED_ADMIN_EMAIL    (default: aicreator.info@gmail.com)
    SEED_ADMIN_PASSWORD (default: snaptoon_admin)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Aggiungo root al PYTHONPATH per importare db/auth/billing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth.passwords import hash_password
from db.models import Plan
from db.repos import users as users_repo
from db.session import session_scope


def main() -> None:
    email = os.getenv("SEED_ADMIN_EMAIL", "aicreator.info@gmail.com").strip().lower()
    password = os.getenv("SEED_ADMIN_PASSWORD", "snaptoon_admin")

    with session_scope() as s:
        existing = users_repo.get_by_email(s, email)
        if existing is not None:
            print(f"✓ Admin {email} esiste già (id: {existing.id}). Niente da fare.")
            return

        users_repo.create_user(
            s,
            email=email,
            password_hash=hash_password(password),
            plan=Plan.pro,
            initial_credits=10000,  # admin parte con tanti crediti per testing
            is_admin=True,
            must_change_password=True,  # forzato a cambiare al primo login
        )
        print(f"✓ Admin {email} creato. Password temporanea: {password}")
        print("  Al primo login dovrà cambiarla.")


if __name__ == "__main__":
    main()
