"""Gestione sessioni utente.

Pattern:
- Login → crea record UserSession con token random + scadenza
- Token salvato in st.session_state["snaptoon_session_token"]
- Ogni request: lookup token → user → cache in st.session_state["snaptoon_user_id"]
- Logout → cancella record + clean session_state
- TTL: 7 giorni rolling (last_seen_at aggiornato a ogni request)

NOTA: Streamlit ha già il suo session_state per ogni client browser. Noi
usiamo IN PIÙ una tabella DB per:
1. Invalidare sessioni server-side (logout forzato da admin)
2. Sopravvivere a restart del Reserved VM
3. Audit "chi era loggato quando"
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.base import utcnow
from db.models import User, UserSession
from db.repos import users as users_repo

from .passwords import verify_password


SESSION_TTL_DAYS = 7
SESSION_STATE_TOKEN_KEY = "snaptoon_session_token"
SESSION_STATE_USER_ID_KEY = "snaptoon_user_id"


# ============================================================
# Token utils
# ============================================================


def _generate_token() -> str:
    """Random URL-safe, 32 byte (256 bit di entropia)."""
    return secrets.token_urlsafe(32)


def _hash_token(token: str) -> str:
    """Salviamo SHA256 del token nel DB, non il token in chiaro.

    Così se qualcuno legge il DB non può rubare sessioni attive."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ============================================================
# Login / Logout
# ============================================================


def login(session: Session, *, email: str, password: str) -> User | None:
    """Verifica credenziali. Ritorna User loggato, o None.

    Su success:
    - Crea record UserSession nel DB
    - Salva token in st.session_state
    - Aggiorna user.last_login_at
    """
    user = users_repo.get_by_email(session, email)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None

    token = create_session(session, user)
    st.session_state[SESSION_STATE_TOKEN_KEY] = token
    st.session_state[SESSION_STATE_USER_ID_KEY] = str(user.id)

    users_repo.mark_login(session, user)
    return user


def create_session(session: Session, user: User) -> str:
    """Crea nuova UserSession nel DB. Ritorna il token in chiaro (da dare al client)."""
    token = _generate_token()
    sess = UserSession(
        user_id=user.id,
        token_hash=_hash_token(token),
        expires_at=utcnow() + timedelta(days=SESSION_TTL_DAYS),
        last_seen_at=utcnow(),
    )
    session.add(sess)
    session.flush()
    return token


def logout(session: Session) -> None:
    """Invalida la sessione corrente (server + client)."""
    token = st.session_state.get(SESSION_STATE_TOKEN_KEY)
    if token:
        invalidate_session(session, token)
    st.session_state.pop(SESSION_STATE_TOKEN_KEY, None)
    st.session_state.pop(SESSION_STATE_USER_ID_KEY, None)


def invalidate_session(session: Session, token: str) -> None:
    """Cancella il record UserSession dal DB."""
    token_hash = _hash_token(token)
    stmt = select(UserSession).where(UserSession.token_hash == token_hash)
    sess = session.execute(stmt).scalar_one_or_none()
    if sess is not None:
        session.delete(sess)


# ============================================================
# Resolve current user
# ============================================================


def current_user(session: Session) -> User | None:
    """Restituisce l'utente loggato corrente, o None.

    Side effect: rinfresca last_seen_at sulla UserSession (rolling TTL).
    """
    token = st.session_state.get(SESSION_STATE_TOKEN_KEY)
    if not token:
        return None

    token_hash = _hash_token(token)
    now = utcnow()

    stmt = select(UserSession).where(UserSession.token_hash == token_hash)
    sess = session.execute(stmt).scalar_one_or_none()
    if sess is None:
        # Token nel browser ma non più nel DB → sessione invalidata
        st.session_state.pop(SESSION_STATE_TOKEN_KEY, None)
        st.session_state.pop(SESSION_STATE_USER_ID_KEY, None)
        return None

    if sess.expires_at < now:
        session.delete(sess)
        st.session_state.pop(SESSION_STATE_TOKEN_KEY, None)
        st.session_state.pop(SESSION_STATE_USER_ID_KEY, None)
        return None

    user = session.get(User, sess.user_id)
    if user is None or not user.is_active:
        session.delete(sess)
        st.session_state.pop(SESSION_STATE_TOKEN_KEY, None)
        st.session_state.pop(SESSION_STATE_USER_ID_KEY, None)
        return None

    # Rolling TTL: rinfresca last_seen_at + sposta in avanti expires_at
    sess.last_seen_at = now
    sess.expires_at = now + timedelta(days=SESSION_TTL_DAYS)
    return user


def require_user(session: Session) -> User:
    """Versione "must" di current_user: solleva se nessuno è loggato."""
    user = current_user(session)
    if user is None:
        raise RuntimeError("Nessun utente loggato.")
    return user
