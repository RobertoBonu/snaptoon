"""
StyleCard — card stile visivo nella libreria.
design: card compatta con badge attivo, anteprima expansion e azioni
"""
from __future__ import annotations
import streamlit as st


def render_style_card(
    preset: dict,
    is_selected: bool,
    card_index: int = 0,
) -> tuple[bool, bool]:
    """
    Renderizza una StyleCard.

    Params:
        preset: Dict con campi:
                  id, label, category, is_handmade, is_custom, expansion (str)
        is_selected: True se questo stile è quello corrente del progetto.
        card_index:  Indice per chiavi univoche.

    Returns:
        (preview_clicked, apply_clicked) — tuple di bool.
    """
    selected_class = "snaptoon-style-card--selected" if is_selected else ""
    badge_active = '<span class="snaptoon-style-card__badge-active">Attivo</span>' if is_selected else ""
    custom_icon = " 🖌" if preset.get("is_custom") else ""
    expansion_preview = (preset.get("expansion") or "")[:120]
    if len(preset.get("expansion") or "") > 120:
        expansion_preview += "…"

    st.markdown(
        f"""
        <div class="snaptoon-style-card {selected_class}">
          {badge_active}
          <div class="snaptoon-style-card__title">{preset.get('label', '')}{custom_icon}</div>
          <div class="snaptoon-style-card__category">{preset.get('category', '')}</div>
          <div class="snaptoon-style-card__preview">{expansion_preview}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        preview = st.button(
            "👁 Anteprima",
            key=f"_ui_style_preview_{preset.get('id', card_index)}",
            use_container_width=True,
        )
    with col2:
        apply = st.button(
            f"✨ Applica",
            key=f"_ui_style_apply_{preset.get('id', card_index)}",
            type="primary" if not is_selected else "secondary",
            use_container_width=True,
        )

    return preview, apply
