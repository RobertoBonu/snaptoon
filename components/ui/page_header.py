"""
PageHeader — header di ogni pagina di lavoro.
design: componente header pagina con titolo, sottotitolo e azioni globali
"""
from __future__ import annotations
import streamlit as st


def render_page_header(
    title: str,
    subtitle: str | None = None,
    actions: list[dict] | None = None,
) -> None:
    """
    Renderizza l'header della pagina.

    Params:
        title:    Titolo H1 della pagina.
        subtitle: Sottotitolo secondario (es. nome progetto + conteggio).
        actions:  Lista di dict {"label": str, "primary": bool, "key": str}.
                  Max 3 azioni. Resa come bottoni affiancati a destra.
    """
    actions = actions or []

    st.markdown(
        """
        <div class="snaptoon-page-header">
            <div class="snaptoon-page-header__left">
        """,
        unsafe_allow_html=True,
    )

    st.title(title)

    if subtitle:
        st.markdown(
            f'<p class="snaptoon-page-header__subtitle">{subtitle}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if actions:
        st.markdown('<div class="snaptoon-page-header__actions">', unsafe_allow_html=True)
        cols = st.columns(len(actions))
        for col, action in zip(cols, actions):
            with col:
                st.button(
                    action["label"],
                    key=action.get("key"),
                    type="primary" if action.get("primary") else "secondary",
                    use_container_width=False,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()
