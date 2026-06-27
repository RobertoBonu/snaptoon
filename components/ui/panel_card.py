"""
PanelCard — card vignetta nella pagina Genera.
design: card con immagine/placeholder, caption cast e scena, bottoni azione
"""
from __future__ import annotations
import streamlit as st


def render_panel_card(
    panel: dict,
    vignette_image_path: str | None,
    panel_index: int = 0,
    page_index: int = 0,
) -> dict[str, bool]:
    """
    Renderizza la card di una vignetta.

    Params:
        panel: Dict con campi:
               number, description, dialogues (list), aspect_ratio,
               cast (list[str]), scene_params (dict)
        vignette_image_path: Path PNG vignetta. None = non generata.
        panel_index: Indice vignetta nella pagina.
        page_index:  Indice pagina (per chiavi univoche).

    Returns:
        Dict bool per ogni azione: {
          "generate", "scene_open", "prompt_open", "balloon_open", "move_open"
        }
    """
    number = panel.get("number", panel_index + 1)
    description = panel.get("description", "")
    cast = panel.get("cast", [])
    dialogues = panel.get("dialogues", [])
    scene_params = panel.get("scene_params") or {}

    key_pfx = f"_ui_panel_{page_index}_{panel_index}"
    actions: dict[str, bool] = {
        "generate": False,
        "scene_open": False,
        "prompt_open": False,
        "balloon_open": False,
        "move_open": False,
    }

    with st.container(border=True):
        st.markdown(
            f'<div class="snaptoon-panel-card__header">Vignetta {number}</div>',
            unsafe_allow_html=True,
        )

        if vignette_image_path:
            st.image(vignette_image_path, use_container_width=True)
        else:
            st.markdown(
                '<div class="snaptoon-panel-card__image">'
                '<em>— non ancora generata —</em></div>',
                unsafe_allow_html=True,
            )

        if description:
            preview = description[:120] + ("…" if len(description) > 120 else "")
            st.caption(preview)

        if cast:
            st.caption(f"👥 {', '.join(cast)}")

        meta_parts = []
        if scene_params.get("aspect_ratio"):
            meta_parts.append(f"📐 {scene_params['aspect_ratio']}")
        if scene_params.get("distance"):
            meta_parts.append(f"🎥 {scene_params['distance']}")
        if scene_params.get("angle"):
            meta_parts.append(f"🎞 {scene_params['angle']}")
        if scene_params.get("mood"):
            meta_parts.append(f"🎭 {scene_params['mood']}")
        if meta_parts:
            st.caption("  ".join(meta_parts))

        st.markdown("---")

        col_gen, col_scene = st.columns(2)
        with col_gen:
            btn_label = "🔄 Rigenera" if vignette_image_path else "✨ Genera"
            actions["generate"] = st.button(
                btn_label,
                key=f"{key_pfx}_gen",
                type="primary",
                use_container_width=True,
            )
        with col_scene:
            with st.popover("🎬 Scena", use_container_width=True):
                actions["scene_open"] = True
                _render_scene_popover(panel, key_pfx)

        col_prompt, col_balloon = st.columns(2)
        with col_prompt:
            with st.popover("👁 Prompt", use_container_width=True):
                actions["prompt_open"] = True
                st.caption("Anteprima prompt completo")
                st.text_area(
                    "Prompt",
                    value=panel.get("prompt_preview", "(non ancora generato)"),
                    height=200,
                    key=f"{key_pfx}_prompt_txt",
                    label_visibility="collapsed",
                    disabled=True,
                )
        with col_balloon:
            has_dialogues = bool(dialogues)
            actions["balloon_open"] = st.button(
                "🎈 Balloon",
                key=f"{key_pfx}_balloon",
                disabled=not has_dialogues,
                help="Nessun dialogo in questa vignetta." if not has_dialogues else None,
                use_container_width=True,
            )

        with st.popover("📦 Sposta vignetta", use_container_width=True):
            actions["move_open"] = True
            st.selectbox(
                "Sposta a pagina",
                options=["Pagina 1", "Pagina 2", "Pagina 3"],
                key=f"{key_pfx}_move_sel",
            )
            st.button("Sposta", key=f"{key_pfx}_move_ok", type="primary")

    return actions


def _render_scene_popover(panel: dict, key_pfx: str) -> None:
    """Contenuto interno del popover Scena."""
    st.markdown("**Parametri di regia di questa vignetta**")
    st.divider()

    st.markdown(
        '<div class="snaptoon-section-label">👥 Personaggi nella scena</div>',
        unsafe_allow_html=True,
    )
    cast = panel.get("cast", [])
    all_chars = panel.get("all_characters", cast)
    st.multiselect(
        "Cast",
        options=all_chars,
        default=cast,
        key=f"{key_pfx}_scene_cast",
        label_visibility="collapsed",
    )
    st.button("🔍 Auto-rileva da descrizione", key=f"{key_pfx}_scene_autocast")

    st.markdown(
        '<div class="snaptoon-section-label">Formato vignetta</div>',
        unsafe_allow_html=True,
    )
    st.selectbox(
        "Formato",
        options=["16:9", "4:3", "1:1", "3:4", "9:16"],
        key=f"{key_pfx}_scene_ratio",
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="snaptoon-section-label">Distanza inquadratura</div>',
        unsafe_allow_html=True,
    )
    st.selectbox(
        "Distanza",
        options=["Primo piano", "Piano americano", "Piano medio", "Campo lungo", "Campo larghissimo"],
        key=f"{key_pfx}_scene_dist",
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="snaptoon-section-label">Angolo / inquadratura speciale</div>',
        unsafe_allow_html=True,
    )
    st.selectbox(
        "Angolo",
        options=["Normale", "Dall'alto", "Dal basso", "Dutch angle", "POV"],
        key=f"{key_pfx}_scene_angle",
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="snaptoon-section-label">Tono emotivo</div>',
        unsafe_allow_html=True,
    )
    st.selectbox(
        "Tono",
        options=["Neutro", "Drammatico", "Comico", "Misterioso", "Romantico", "Adrenalinico"],
        key=f"{key_pfx}_scene_mood",
        label_visibility="collapsed",
    )

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.button("💾 Salva scena", key=f"{key_pfx}_scene_save", type="primary", use_container_width=True)
    with col2:
        st.button("↩️ Reset scena", key=f"{key_pfx}_scene_reset", use_container_width=True)
