"""
LoginForm — form di accesso.
design: card centrata con logo SnapToon, form email + password, errori inline
"""
from __future__ import annotations
import streamlit as st


def render_login_form() -> tuple[str, str, bool]:
    """
    Renderizza il form di login centrato.

    Returns:
        (email, password, submitted) — tuple con i valori inseriti e se il form è stato inviato.
    """
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("snaptoon_login_form"):
            st.markdown(
                """
                <div class="snaptoon-login-logo">
                  <div class="snaptoon-login-logo__title">SnapToon<span class="snaptoon-login-logo__dot"></span></div>
                  <div class="snaptoon-login-logo__subtitle">Dall'idea al fumetto, in uno snap.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="snaptoon-field-label">EMAIL</div>', unsafe_allow_html=True)
            email = st.text_input(
                "Email", placeholder="nome@dominio.com", label_visibility="collapsed"
            )
            st.markdown('<div class="snaptoon-field-label">PASSWORD</div>', unsafe_allow_html=True)
            password = st.text_input(
                "Password", type="password", placeholder="••••••••", label_visibility="collapsed"
            )
            submitted = st.form_submit_button(
                "Accedi",
                type="primary",
                use_container_width=True,
            )
            st.markdown(
                "<p class=\"snaptoon-login-hint\">Hai dimenticato la password? "
                "Contatta l'amministratore.</p>",
                unsafe_allow_html=True,
            )

        error = st.session_state.get("_ui_login_error")
        if error:
            st.error(error)

    return email, password, submitted


def render_change_password_form() -> tuple[str, str, bool]:
    """
    Renderizza il form di cambio password obbligatorio (primo login).

    Returns:
        (new_password, confirm_password, submitted)
    """
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            """
            <div class="snaptoon-login-logo" style="margin-bottom:1.5rem;">
              <div class="snaptoon-login-logo__title">SnapToon</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("Imposta la tua password")
        st.caption(
            "Hai effettuato il primo accesso. "
            "Imposta una password personale per proseguire."
        )

        with st.form("snaptoon_change_pwd_form"):
            new_pwd = st.text_input("Nuova password", type="password")
            confirm_pwd = st.text_input("Conferma nuova password", type="password")
            submitted = st.form_submit_button(
                "Aggiorna password",
                type="primary",
                use_container_width=True,
            )

        error = st.session_state.get("_ui_pwd_error")
        if error:
            st.error(error)

    return new_pwd, confirm_pwd, submitted
