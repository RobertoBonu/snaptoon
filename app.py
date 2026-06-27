"""SnapToon — entry point Streamlit.

Lancia con:  streamlit run app.py

Questo è il file principale dell'app. La logica di autenticazione, sessione,
e caricamento del progetto attivo vive qui. Le pagine specifiche sono in
`pages/`.

REPLIT_AGENT: puoi modificare lo strato visivo (markup, layout, header),
NON la logica delle funzioni auth (login, current_user, ...) che vivono in
`auth/`. Vedi docs/design/07_REPLIT_AGENT.md.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from auth import current_user, hash_password, login, logout
from db.repos import users as users_repo
from db.session import session_scope

st.set_page_config(
    page_title="SnapToon",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS design system
# ============================================================
def _inject_css() -> None:
    css_path = Path("style/custom.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def _hide_sidebar() -> None:
    """Le schermate di accesso non hanno sidebar (vedi brief 00_Login)."""
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True,
    )


_inject_css()


# ============================================================
# Schermate di autenticazione
# ============================================================
def _render_login() -> None:
    """Form di accesso. NON tocca la logica auth: la richiama soltanto."""
    from components.ui.login_form import render_login_form

    _hide_sidebar()
    email, password, submitted = render_login_form()

    if submitted:
        st.session_state.pop("_ui_login_error", None)
        with session_scope() as s:
            user = login(s, email=email, password=password)
        if user is None:
            st.session_state["_ui_login_error"] = "Credenziali non valide."
        st.rerun()


def _render_change_password() -> None:
    """Cambio password obbligatorio al primo accesso."""
    from components.ui.login_form import render_change_password_form

    _hide_sidebar()
    new_pwd, confirm_pwd, submitted = render_change_password_form()

    if submitted:
        st.session_state.pop("_ui_pwd_error", None)
        if len(new_pwd) < 8:
            st.session_state["_ui_pwd_error"] = (
                "La password deve essere lunga almeno 8 caratteri."
            )
        elif new_pwd != confirm_pwd:
            st.session_state["_ui_pwd_error"] = "Le due password non coincidono."
        else:
            with session_scope() as s:
                user = current_user(s)
                if user is not None:
                    users_repo.set_password_hash(s, user, hash_password(new_pwd))
        st.rerun()


# ============================================================
# Home autenticata
# ============================================================
def _render_home(user) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="snaptoon-sidebar-logo">
              <span class="snaptoon-sidebar-logo__wordmark">
                SnapToon<span class="snaptoon-sidebar-logo__dot"></span>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(user.email)
        st.divider()
        if st.button("🚪 Esci", use_container_width=True):
            with session_scope() as s:
                logout(s)
            st.rerun()

    st.title("SnapToon")
    st.caption("Dall'idea al fumetto, in uno snap.")
    st.markdown("---")
    st.subheader(f"Ciao 👋")
    st.write(f"Hai effettuato l'accesso come **{user.email}**.")
    st.info(
        "Le pagine dell'editor (Testo, Stile, Personaggi, Genera, Impagina) "
        "arriveranno a breve."
    )


# ============================================================
# Routing in base allo stato di autenticazione
# ============================================================
with session_scope() as s:
    _user = current_user(s)

if _user is None:
    _render_login()
elif _user.must_change_password:
    _render_change_password()
else:
    _render_home(_user)
