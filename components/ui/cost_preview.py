"""
CostPreview — anteprima costo crediti prima di un'operazione AI.
design: caption inline con stato insufficiente
"""
from __future__ import annotations
import streamlit as st


def render_cost_preview(
    operation_label: str,
    cost_credits: int,
    remaining_after: int,
) -> None:
    """
    Renderizza il costo previsto di un'operazione AI.

    Params:
        operation_label: Descrizione operazione (es. "Genera 24 vignette mancanti").
        cost_credits:    Crediti che verranno usati.
        remaining_after: Crediti rimasti dopo l'operazione.
    """
    if remaining_after < 0:
        css_class = "snaptoon-cost-preview snaptoon-cost-preview--insufficient"
        text = f"⚠️ Crediti insufficienti — servono {cost_credits}, ne hai {cost_credits + remaining_after}."
    else:
        css_class = "snaptoon-cost-preview"
        text = f"Costa {cost_credits} crediti. Ti resteranno {remaining_after}."

    st.markdown(
        f'<div class="{css_class}">{text}</div>',
        unsafe_allow_html=True,
    )
