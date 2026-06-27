"""
CharacterCard — card personaggio nella pagina Personaggi.
design: expander con thumbnail, form descrizione, bottoni genera/upload, varianti
"""
from __future__ import annotations
import streamlit as st


_STATUS_META = {
    "valid":    ("🟢", "Reference valida",         "snaptoon-char-status--valid"),
    "corrupted":("🟠", "File corrotto",             "snaptoon-char-status--corrupted"),
    "missing":  ("⚪", "Nessuna reference",          "snaptoon-char-status--missing"),
}


def render_character_card(
    character: dict,
    ref_status: str,
    n_variants: int,
    card_index: int = 0,
    ref_image_path: str | None = None,
) -> dict[str, bool]:
    """
    Renderizza la card di un personaggio.

    Params:
        character:      Dict con "name" e "visual_description".
        ref_status:     "valid" | "corrupted" | "missing"
        n_variants:     Numero di varianti reference (slot 2-7).
        card_index:     Indice per chiavi univoche.
        ref_image_path: Path all'immagine reference principale (None se assente).

    Returns:
        Dict con bool per ogni azione: {
          "generate", "upload", "delete_corrupted", "variants_toggled"
        }
    """
    icon, label, css_class = _STATUS_META.get(ref_status, _STATUS_META["missing"])

    default_open = ref_status != "valid"
    name = character.get("name", "Personaggio")

    actions: dict[str, bool] = {
        "generate": False,
        "upload": False,
        "delete_corrupted": False,
        "variants_toggled": False,
    }

    with st.expander(
        f"{icon} {name}",
        expanded=default_open,
    ):
        st.markdown(
            f'<span class="snaptoon-char-status {css_class}">{icon} {label}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        col_img, col_form = st.columns([1, 2])

        with col_img:
            if ref_image_path and ref_status == "valid":
                st.image(ref_image_path, use_container_width=True)
            else:
                st.markdown(
                    '<div style="width:100%;aspect-ratio:1;background:#0A0E17;border:1px solid #1E2436;'
                    'border-radius:6px;display:flex;align-items:center;justify-content:center;'
                    'color:#334155;font-size:11px;">Nessuna ref.</div>',
                    unsafe_allow_html=True,
                )

            if ref_status == "corrupted":
                actions["delete_corrupted"] = st.button(
                    "🗑 Elimina file corrotto",
                    key=f"_ui_char_del_{card_index}",
                    use_container_width=True,
                )

        with col_form:
            st.markdown(
                '<div class="snaptoon-section-label">Descrizione visiva</div>',
                unsafe_allow_html=True,
            )
            st.text_area(
                "Descrizione visiva",
                value=character.get("visual_description", ""),
                placeholder="Es. uomo sui 40, barba grigia corta, occhi nocciola, giacca di pelle marrone consumata",
                height=90,
                key=f"_ui_char_desc_{card_index}",
                label_visibility="collapsed",
            )

            btn_label = "🔄 Rigenera con AI" if ref_status == "valid" else "✨ Genera con AI"
            col_g, col_u = st.columns(2)
            with col_g:
                actions["generate"] = st.button(
                    btn_label,
                    key=f"_ui_char_gen_{card_index}",
                    type="primary" if ref_status == "missing" else "secondary",
                    use_container_width=True,
                )
            with col_u:
                actions["upload"] = st.button(
                    "📤 Carica file",
                    key=f"_ui_char_upload_{card_index}",
                    use_container_width=True,
                )

        st.markdown("")
        st.markdown(
            f'<div class="snaptoon-section-label">📚 Reference aggiuntive ({n_variants}/7)</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Mostra varianti", expanded=False):
            actions["variants_toggled"] = True
            variant_kinds = [
                ("profile", "Profilo"),
                ("three_quarter", "Tre quarti"),
                ("full_body", "Figura intera"),
                ("smiling", "Sorridente"),
                ("dramatic", "Espressione drammatica"),
                ("back", "Di spalle"),
            ]
            cols = st.columns(3)
            for i, (kind, kind_label) in enumerate(variant_kinds):
                with cols[i % 3]:
                    st.caption(kind_label)
                    st.button(
                        "✨",
                        key=f"_ui_char_var_{card_index}_{kind}",
                        help=f"Genera variante: {kind_label}",
                    )

    return actions
