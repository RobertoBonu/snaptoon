"""Decoratori e gate per le pagine Streamlit.

Uso tipico in una pagina (pages/2_📝_Testo.py):

    from auth import auth_required
    from db.session import session_scope

    auth_required()  # gate inline — chiama st.stop() se non loggato

    with session_scope() as s:
        user = current_user(s)
        ...

Niente decoratore funzione (non funziona bene con Streamlit script flow):
si usa chiamata inline ad auth_required() in cima alla pagina.
"""

from __future__ import annotations

import streamlit as st

from db.session import session_scope

from .sessions import current_user


def auth_required(*, allow_must_change_password_page: bool = False) -> None:
    """Gate inline: chiama st.stop() se utente non loggato o disabilitato.

    Side effect: popola st.session_state["snaptoon_user"] con l'utente corrente
    se autenticato.

    Se l'utente ha must_change_password=True e NON sta sulla pagina di cambio
    password, viene reindirizzato lì.
    """
    with session_scope() as s:
        user = current_user(s)

    if user is None:
        st.error("Devi accedere per usare questa pagina.")
        st.markdown("[← Vai al login](/)")
        st.stop()

    if user.must_change_password and not allow_must_change_password_page:
        st.warning("Devi prima impostare una password personale.")
        st.markdown("[Vai a cambio password →](/cambia_password)")
        st.stop()

    # Cache util per la pagina
    st.session_state["snaptoon_user_id"] = str(user.id)
    st.session_state["snaptoon_user_email"] = user.email
    st.session_state["snaptoon_user_is_admin"] = user.is_admin


def admin_required() -> None:
    """Gate per pagine admin. Implica auth_required."""
    auth_required()
    if not st.session_state.get("snaptoon_user_is_admin", False):
        st.error("Non hai i permessi per questa pagina.")
        st.markdown("[← Vai alla home](/)")
        st.stop()
