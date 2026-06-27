"""
ConfirmDialog — conferma per operazioni distruttive o costose.
design: expander con bordo rosso, testo warning, conferma opzionale per nome
"""
from __future__ import annotations
import streamlit as st


def render_confirm_dialog(
    title: str,
    body: str,
    confirm_label: str,
    confirm_danger: bool = False,
    requires_type_to_confirm: str | None = None,
    cost_in_credits: int | None = None,
    cancel_key: str = "_ui_confirm_cancel",
    confirm_key: str = "_ui_confirm_ok",
    input_key: str = "_ui_confirm_input",
) -> tuple[bool, bool]:
    """
    Renderizza un dialog di conferma.

    Returns:
        (confirmed, cancelled) — tuple di bool.
    """
    border_color = "#EF4444" if confirm_danger else "#F59E0B"

    st.markdown(
        f"""
        <div class="snaptoon-confirm-dialog"
             style="border-color: {border_color};">
          <div class="snaptoon-confirm-dialog__title">{title}</div>
          <div class="snaptoon-confirm-dialog__body">{body}</div>
        """,
        unsafe_allow_html=True,
    )

    if cost_in_credits is not None:
        st.markdown(
            f'<div class="snaptoon-confirm-dialog__warning">'
            f'⚠️ Costa {cost_in_credits} crediti.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    typed_match = True
    if requires_type_to_confirm:
        typed = st.text_input(
            f'Per confermare, scrivi: **{requires_type_to_confirm}**',
            key=input_key,
            placeholder=requires_type_to_confirm,
        )
        typed_match = typed.strip() == requires_type_to_confirm

    col1, col2 = st.columns([1, 1])

    with col1:
        confirmed = st.button(
            confirm_label,
            key=confirm_key,
            type="primary",
            disabled=not typed_match,
            use_container_width=True,
        )
        if confirm_danger:
            st.markdown(
                f"""
                <style>
                div[data-testid="column"]:first-child .stButton button {{
                  background: {'#EF4444' if typed_match else 'transparent'} !important;
                  border-color: #EF4444 !important;
                  color: {'#fff' if typed_match else '#EF4444'} !important;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        cancelled = st.button(
            "Annulla",
            key=cancel_key,
            type="secondary",
            use_container_width=True,
        )

    return confirmed, cancelled
