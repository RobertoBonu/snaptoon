"""Helper per state condiviso tra app.py e pages/*.py.

Centralizziamo qui le chiavi di st.session_state usate dall'app, per
evitare typo e per documentare il contratto tra pagine.
"""

from __future__ import annotations

import uuid

import streamlit as st


# ============================================================
# Chiavi st.session_state
# ============================================================

KEY_CURRENT_PROJECT_SLUG = "snaptoon_current_project_slug"
KEY_USER_ID = "snaptoon_user_id"
KEY_USER_EMAIL = "snaptoon_user_email"
KEY_USER_IS_ADMIN = "snaptoon_user_is_admin"

# Modali UI
KEY_SHOW_NEW_PROJECT_MODAL = "_ui_show_new_project_modal"
KEY_SHOW_DELETE_PROJECT_TARGET = "_ui_show_delete_target"
KEY_SHOW_DUPLICATE_PROJECT_TARGET = "_ui_show_duplicate_target"

# Errori inline
KEY_NEW_PROJECT_ERROR = "_ui_new_project_error"


# ============================================================
# Current project
# ============================================================


def get_current_project_slug() -> str | None:
    return st.session_state.get(KEY_CURRENT_PROJECT_SLUG)


def set_current_project_slug(slug: str | None) -> None:
    if slug is None:
        st.session_state.pop(KEY_CURRENT_PROJECT_SLUG, None)
    else:
        st.session_state[KEY_CURRENT_PROJECT_SLUG] = slug


def clear_current_project() -> None:
    st.session_state.pop(KEY_CURRENT_PROJECT_SLUG, None)


# ============================================================
# Cached user info (popolato dopo auth_required)
# ============================================================


def get_user_id() -> uuid.UUID | None:
    raw = st.session_state.get(KEY_USER_ID)
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except (TypeError, ValueError):
        return None


def is_admin() -> bool:
    return bool(st.session_state.get(KEY_USER_IS_ADMIN, False))


# ============================================================
# Cleanup completo (logout)
# ============================================================


def clear_session_keys() -> None:
    """Pulisce tutto lo state SnapToon (logout)."""
    keys_to_drop = [k for k in st.session_state.keys() if k.startswith("snaptoon_") or k.startswith("_ui_")]
    for k in keys_to_drop:
        st.session_state.pop(k, None)
