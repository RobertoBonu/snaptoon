"""
AdminUserRow — riga utente nel pannello Admin.
design: riga con email, piano, crediti, stato e azioni
"""
from __future__ import annotations
import streamlit as st


def render_admin_user_table(users: list[dict]) -> None:
    """
    Renderizza la tabella utenti nell'Admin.

    Params:
        users: Lista di dict con campi:
               id, email, plan, credits_remaining, credits_total,
               created_at (str DD/MM/YYYY), is_active (bool)
    """
    if not users:
        st.caption("Nessun utente registrato.")
        return

    header_cols = st.columns([3, 1.5, 1.5, 1.5, 1, 2])
    headers = ["Email", "Piano", "Crediti", "Registrato", "Stato", "Azioni"]
    for col, h in zip(header_cols, headers):
        col.markdown(
            f'<div class="snaptoon-section-label" style="margin:0;">{h}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    for i, user in enumerate(users):
        cols = st.columns([3, 1.5, 1.5, 1.5, 1, 2])

        with cols[0]:
            st.markdown(f"<span style='font-size:13px;'>{user.get('email','')}</span>", unsafe_allow_html=True)

        with cols[1]:
            plan = user.get("plan", "—")
            badge_class = "snaptoon-badge--violet" if plan != "Free Trial" else "snaptoon-badge--gray"
            st.markdown(
                f'<span class="snaptoon-badge {badge_class}">{plan}</span>',
                unsafe_allow_html=True,
            )

        with cols[2]:
            rem = user.get("credits_remaining", 0)
            tot = user.get("credits_total", 0)
            st.markdown(
                f"<span style='font-size:13px;color:#CBD5E1;'>{rem}/{tot}</span>",
                unsafe_allow_html=True,
            )

        with cols[3]:
            st.caption(user.get("created_at", "—"))

        with cols[4]:
            is_active = user.get("is_active", True)
            badge_class = "snaptoon-badge--green" if is_active else "snaptoon-badge--red"
            label = "Attivo" if is_active else "Disabilitato"
            st.markdown(
                f'<span class="snaptoon-badge {badge_class}">{label}</span>',
                unsafe_allow_html=True,
            )

        with cols[5]:
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                st.button(
                    "🪙",
                    key=f"_ui_admin_credits_{i}",
                    help="Aggiungi crediti",
                )
            with action_col2:
                if is_active:
                    st.button(
                        "🚫",
                        key=f"_ui_admin_disable_{i}",
                        help="Disabilita account",
                    )
                else:
                    st.button(
                        "✓",
                        key=f"_ui_admin_enable_{i}",
                        help="Riabilita account",
                    )

        st.markdown(
            "<hr style='border-color:#1E2436;margin:.25rem 0;'>",
            unsafe_allow_html=True,
        )
