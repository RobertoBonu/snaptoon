"""
EmptyState — stato vuoto generico.
design: empty state centrato con icona, titolo, descrizione e CTA opzionale
"""
from __future__ import annotations
import streamlit as st


def render_empty_state(
    icon: str,
    title: str,
    description: str | None = None,
    action_label: str | None = None,
    action_key: str = "_ui_empty_state_action",
) -> bool:
    """
    Renderizza uno stato vuoto centrato.

    Params:
        icon:         Emoji o carattere icona (grande).
        title:        Titolo principale.
        description:  Testo descrittivo opzionale.
        action_label: Testo CTA. Se None, nessun bottone.
        action_key:   Key univoca per il bottone Streamlit.

    Returns:
        True se l'utente ha cliccato la CTA.
    """
    desc_html = (
        f'<p class="snaptoon-empty-state__desc">{description}</p>'
        if description
        else ""
    )

    st.markdown(
        f"""
        <div class="snaptoon-empty-state">
          <div class="snaptoon-empty-state__icon">{icon}</div>
          <p class="snaptoon-empty-state__title">{title}</p>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if action_label:
        _, col, _ = st.columns([1, 2, 1])
        with col:
            return st.button(action_label, key=action_key, type="primary", use_container_width=True)

    return False
