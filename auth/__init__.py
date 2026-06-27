"""SnapToon — autenticazione.

Email + password con bcrypt. Niente OAuth, niente magic link in MVP.
Accounts creati esclusivamente da admin (vedi pages/admin).

Moduli:
- passwords: hash + verify (bcrypt)
- sessions: gestione sessione utente (token + DB) + helper Streamlit
- decorators: @auth_required per gate delle pagine
"""

from __future__ import annotations

from .decorators import auth_required, admin_required
from .passwords import hash_password, verify_password
from .sessions import (
    create_session,
    current_user,
    invalidate_session,
    login,
    logout,
    require_user,
)

__all__ = [
    "auth_required",
    "admin_required",
    "hash_password",
    "verify_password",
    "create_session",
    "current_user",
    "invalidate_session",
    "login",
    "logout",
    "require_user",
]
