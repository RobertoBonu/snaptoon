"""
ProjectSelector — selettore progetto attivo in sidebar.
design: dropdown progetto con link "Nuovo progetto"
"""
from __future__ import annotations
import streamlit as st


def render_project_selector(
    current_project_slug: str | None,
    projects: list[dict],
) -> str | None:
    """
    Renderizza il selettore del progetto attivo.

    Params:
        current_project_slug: Slug del progetto corrente (None se nessuno).
        projects:             Lista di dict {"slug": str, "title": str}.

    Returns:
        Slug del progetto selezionato, o None.
    """
    if not projects:
        st.markdown(
            '<p class="snaptoon-text-muted" style="padding: 0 1rem;">Nessun progetto</p>',
            unsafe_allow_html=True,
        )
        if st.button("+ Nuovo progetto", key="_ui_proj_new_empty", use_container_width=True):
            st.session_state["_ui_show_new_project_modal"] = True
        return None

    labels = [p["title"] for p in projects]
    slugs = [p["slug"] for p in projects]

    current_idx = 0
    if current_project_slug and current_project_slug in slugs:
        current_idx = slugs.index(current_project_slug)

    st.markdown(
        '<p style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;'
        'letter-spacing:.06em;padding:0 0 4px;margin:0;">Progetto attivo</p>',
        unsafe_allow_html=True,
    )

    selected_idx = st.selectbox(
        label="Progetto attivo",
        options=range(len(projects)),
        format_func=lambda i: labels[i],
        index=current_idx,
        key="_ui_project_selector",
        label_visibility="collapsed",
    )

    if st.button("+ Nuovo progetto", key="_ui_proj_new", use_container_width=False):
        st.session_state["_ui_show_new_project_modal"] = True

    return slugs[selected_idx] if selected_idx is not None else None
