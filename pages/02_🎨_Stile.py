"""SnapToon — pagina 🎨 Stile.

Selezione dello stile visivo dalla libreria di 98 preset.

Tabs:
  1. Selezione: mostra stile attivo + scorciatoia "Cambia stile"
  2. Sfoglia libreria: filtri categoria + grid card + applica
  3. Anteprima prompt: simulazione prompt completo per una vignetta tipo

Out-of-scope V1 (verranno aggiunti dopo):
  - Personalizza custom (modifica stile YAML proprio)
  - Aspetto pagina (sfondo + font/colori balloon/caption/SFX)
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Stile — SnapToon",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "style" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


_inject_css()

from app_state.ui import enforce_sidebar_visibility, render_sidebar_nav
enforce_sidebar_visibility()


# ============================================================
# Imports backend / Auth gate
# ============================================================
import app_state as appstate
from auth import current_user, logout
from billing.plans import plan_config
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.session import session_scope
from snaptoon_core.styles_library import (
    StylePreset,
    get_preset,
    list_presets,
)
from appearance import DEFAULT_APPEARANCE, merge_with_defaults


with session_scope() as _s:
    _user = current_user(_s)

if _user is None:
    st.error("Devi accedere per usare questa pagina.")
    st.markdown("[← Torna al login](/)")
    st.stop()

if _user.must_change_password:
    st.warning("Devi prima impostare una password personale dalla home.")
    st.markdown("[← Torna alla home](/)")
    st.stop()


_current_slug = appstate.get_current_project_slug()
if _current_slug is None:
    st.title("🎨 Stile")
    st.error("Nessun progetto attivo.")
    st.info("Apri un progetto dalla **home** o creane uno nuovo.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


# ============================================================
# Lookup progetto + sidebar
# ============================================================


def _render_sidebar(user, project_name: str, plan_label: str, credits_left: int, credits_total: int) -> None:
    render_sidebar_nav(user)
    with st.sidebar:
        st.markdown("**Progetto attivo:**")
        st.markdown(f"_{project_name}_")
        st.divider()
        if st.button("🚪 Esci", key="_sb_logout_stile", use_container_width=True):
            with session_scope() as s:
                logout(s)
            appstate.clear_session_keys()
            st.switch_page("app.py")


# ============================================================
# Helper: preset → dict per render_style_card
# ============================================================


def _preset_to_dict(p: StylePreset) -> dict:
    return {
        "id": p.id,
        "label": p.label,
        "category": p.category,
        "expansion": p.expansion,
        "is_handmade": p.is_handmade,
        "is_custom": p.is_custom,
    }


# ============================================================
# Tab 1 — Selezione (mostra stile attivo)
# ============================================================


CATEGORY_LABELS_IT = {
    "Personali": "🖌 I miei stili",
    "fumetto": "Fumetto",
    "illustrazione": "Illustrazione",
    "fotografia": "Fotografia",
    "cinema": "Cinema",
    "kids": "Kids",
    "fotografia_autore": "Fotografia d'autore",
}


def _render_tab_selezione(current_style_id: str | None) -> None:
    st.markdown("### Stile attivo del progetto")

    if current_style_id is None:
        st.info(
            "Nessuno stile selezionato. Scegli un preset dalla tab "
            "**📚 Sfoglia libreria** per attivare lo stile visivo."
        )
        return

    preset = get_preset(current_style_id)
    if preset is None:
        st.warning(
            f"Lo stile salvato (`{current_style_id}`) non è più nella libreria. "
            "Probabilmente è stato rinominato. Scegli un nuovo preset dalla tab Sfoglia."
        )
        return

    with st.container(border=True):
        st.markdown(f"## {preset.label}")
        st.caption(
            f"{CATEGORY_LABELS_IT.get(preset.category, preset.category)}"
            f"{'  ·  🖌 Custom' if preset.is_custom else ''}"
            f"{'  ·  ✋ Handmade' if preset.is_handmade else ''}"
        )
        st.markdown("---")
        st.markdown("**Descrizione completa:**")
        st.markdown(f"_{preset.expansion}_")
        if preset.extra_negative_terms:
            st.markdown("---")
            st.markdown("**Negative prompt extra:**")
            st.caption(", ".join(preset.extra_negative_terms))


# ============================================================
# Tab 2 — Sfoglia libreria
# ============================================================


def _render_tab_sfoglia(project_id, current_style_id: str | None) -> None:
    # Conteggio per categoria
    all_presets = list_presets()
    presets_by_cat: dict[str, list[StylePreset]] = {}
    for p in all_presets:
        presets_by_cat.setdefault(p.category, []).append(p)

    # Selettore categoria (radio compatto in cima)
    cats = list(presets_by_cat.keys())
    # Ordine voluto: Personali prima, poi 6 categorie ufficiali
    cat_order = ["Personali", "fumetto", "illustrazione", "fotografia", "cinema", "kids", "fotografia_autore"]
    cats = [c for c in cat_order if c in cats] + [c for c in cats if c not in cat_order]

    radio_labels = [
        f"{CATEGORY_LABELS_IT.get(c, c)} ({len(presets_by_cat[c])})"
        for c in cats
    ]
    selected_idx = st.radio(
        "Categoria",
        options=range(len(cats)),
        format_func=lambda i: radio_labels[i],
        horizontal=True,
        key="_stile_category",
        label_visibility="collapsed",
    )
    selected_cat = cats[selected_idx]

    st.markdown("")

    # Grid di card 3 colonne
    cat_presets = presets_by_cat[selected_cat]
    if not cat_presets:
        st.info("Nessuno stile in questa categoria.")
        return

    cols_per_row = 3
    for row_start in range(0, len(cat_presets), cols_per_row):
        row = cat_presets[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, preset in zip(cols, row):
            with col:
                card_index = row_start + row.index(preset)
                preview_clicked, apply_clicked = None, None
                # render_style_card è custom dell'agente
                from components.ui.style_card import render_style_card
                preview_clicked, apply_clicked = render_style_card(
                    preset=_preset_to_dict(preset),
                    is_selected=(preset.id == current_style_id),
                    card_index=card_index,
                )
                if preview_clicked:
                    _show_preview(preset)
                if apply_clicked:
                    _apply_style(project_id, preset.id, preset.label)


def _show_preview(preset: StylePreset) -> None:
    """Mostra anteprima espansione dello stile (modale-like)."""
    st.session_state[f"_stile_preview_{preset.id}"] = True
    # Espande in container border in fondo (sotto la grid). Streamlit non ha modali vere.
    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### Anteprima: {preset.label}")
        st.caption(CATEGORY_LABELS_IT.get(preset.category, preset.category))
        st.markdown("---")
        st.markdown(preset.expansion)
        if preset.extra_negative_terms:
            st.markdown("**Negative terms:**")
            st.caption(", ".join(preset.extra_negative_terms))


def _apply_style(project_id, preset_id: str, preset_label: str) -> None:
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is not None:
            projects_repo.set_style(s, project, preset_id)
    st.toast(f"Stile «{preset_label}» applicato.", icon="✨")
    st.rerun()


# ============================================================
# Tab 3 — Aspetto pagina
# ============================================================


def _load_project_appearance(project_id) -> dict:
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        return merge_with_defaults(project.appearance if project else None)


def _save_project_appearance(project_id, appearance: dict) -> None:
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is not None:
            project.appearance = appearance


def _render_tab_aspetto(project_id) -> None:
    appearance = _load_project_appearance(project_id)

    st.caption(
        "Colori e dimensioni dei testi nelle pagine renderizzate. "
        "Le modifiche si vedono solo quando rigeneri il render delle pagine "
        "in **📐 Impagina**."
    )

    with st.form("_form_appearance"):
        st.markdown("**🎨 Pagina**")
        page_bg = st.color_picker(
            "Sfondo pagina",
            value=appearance.get("page_bg", "#ffffff"),
        )

        st.divider()
        st.markdown("**💬 Balloon (fumetto + pensiero)**")
        col1, col2 = st.columns(2)
        with col1:
            balloon_text = st.color_picker(
                "Colore testo",
                value=appearance["balloon"]["text_color"],
                key="ap_b_text",
            )
            balloon_fill_fumetto = st.color_picker(
                "Fondo FUMETTO",
                value=appearance["balloon"]["fill_fumetto"],
                key="ap_b_f_fum",
            )
        with col2:
            balloon_outline = st.color_picker(
                "Colore contorno",
                value=appearance["balloon"]["outline_color"],
                key="ap_b_out",
            )
            balloon_fill_pensiero = st.color_picker(
                "Fondo PENSIERO",
                value=appearance["balloon"]["fill_pensiero"],
                key="ap_b_f_pen",
            )
        balloon_size = st.slider(
            "Dimensione testo balloon (px)",
            min_value=16, max_value=48,
            value=appearance["balloon"]["font_size"],
            key="ap_b_size",
        )

        st.divider()
        st.markdown("**📜 Didascalia (riquadro narrante)**")
        col3, col4 = st.columns(2)
        with col3:
            caption_text = st.color_picker(
                "Colore testo",
                value=appearance["caption"]["text_color"],
                key="ap_c_text",
            )
            caption_fill = st.color_picker(
                "Fondo riquadro",
                value=appearance["caption"]["fill"],
                key="ap_c_fill",
            )
        with col4:
            caption_outline = st.color_picker(
                "Colore contorno",
                value=appearance["caption"]["outline_color"],
                key="ap_c_out",
            )
            caption_size = st.slider(
                "Dimensione testo (px)",
                min_value=14, max_value=36,
                value=appearance["caption"]["font_size"],
                key="ap_c_size",
            )

        st.divider()
        st.markdown("**💥 SFX (onomatopee)**")
        col5, col6 = st.columns(2)
        with col5:
            sfx_text = st.color_picker(
                "Colore testo",
                value=appearance["sfx"]["text_color"],
                key="ap_s_text",
            )
        with col6:
            sfx_outline = st.color_picker(
                "Colore contorno",
                value=appearance["sfx"]["outline_color"],
                key="ap_s_out",
            )
        sfx_size = st.slider(
            "Dimensione SFX (px)",
            min_value=40, max_value=120,
            value=appearance["sfx"]["font_size"],
            key="ap_s_size",
        )

        st.divider()
        col_save, col_reset = st.columns(2)
        with col_save:
            save_btn = st.form_submit_button(
                "💾 Salva aspetto",
                type="primary",
                use_container_width=True,
            )
        with col_reset:
            reset_btn = st.form_submit_button(
                "↩️ Ripristina default",
                use_container_width=True,
            )

    if save_btn:
        new_appearance = {
            "page_bg": page_bg,
            "balloon": {
                "text_color": balloon_text,
                "outline_color": balloon_outline,
                "fill_fumetto": balloon_fill_fumetto,
                "fill_pensiero": balloon_fill_pensiero,
                "font_size": balloon_size,
            },
            "caption": {
                "text_color": caption_text,
                "outline_color": caption_outline,
                "fill": caption_fill,
                "font_size": caption_size,
            },
            "sfx": {
                "text_color": sfx_text,
                "outline_color": sfx_outline,
                "font_size": sfx_size,
            },
        }
        _save_project_appearance(project_id, new_appearance)
        st.toast("Aspetto salvato.", icon="🎨")
        st.rerun()

    if reset_btn:
        _save_project_appearance(project_id, DEFAULT_APPEARANCE.copy())
        st.toast("Aspetto ripristinato ai default.")
        st.rerun()


# ============================================================
# Tab 4 — Anteprima prompt
# ============================================================


def _render_tab_anteprima(project_id, current_style_id: str | None) -> None:
    if current_style_id is None:
        st.info(
            "Seleziona prima uno stile dalla tab **📚 Sfoglia libreria** "
            "per vedere come verrà costruito il prompt."
        )
        return

    preset = get_preset(current_style_id)
    if preset is None:
        st.error("Lo stile attivo non è più disponibile nella libreria.")
        return

    # Carichiamo script + cast per costruire un prompt realistico
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None:
            st.error("Progetto non trovato.")
            return

        # Cerchiamo una vignetta esempio
        pyd_script = None
        if project.script is not None and project.script.payload.get("pages"):
            pyd_script = scripts_repo.load_pydantic(project.script)

        cast_sheets = list(project.character_sheets)

    if pyd_script is None or not pyd_script.pages or not pyd_script.pages[0].panels:
        st.info(
            "Per generare un'anteprima del prompt servono almeno una vignetta nella "
            "sceneggiatura. Vai su **📝 Testo** e adatta un sorgente in sceneggiatura."
        )
        return

    # Prendiamo la prima vignetta della prima pagina come esempio
    example_panel = pyd_script.pages[0].panels[0]

    st.markdown("### Prompt per la prima vignetta")
    st.caption(
        f"Vignetta esempio: **Pagina {pyd_script.pages[0].number}, "
        f"Vignetta {example_panel.number}**"
    )
    st.markdown(f"_Descrizione:_ {example_panel.description}")
    st.markdown("---")

    # Costruzione semplificata del prompt (senza tutta la pipeline complessa)
    # Per MVP mostriamo solo l'espansione dello stile + descrizione della vignetta.
    # In Sessione F (Genera) integreremo build_panel_prompt completo.

    prompt_preview = _build_simplified_prompt(preset, example_panel, cast_sheets)

    st.code(prompt_preview, language="text", line_numbers=False)

    st.caption(
        "ℹ️ Questa è un'anteprima semplificata. Il prompt finale (con character "
        "consistency, full-bleed, regia scena, negative aggressive) viene costruito "
        "alla generazione vera nella pagina 🖼 Genera."
    )


def _build_simplified_prompt(preset: StylePreset, panel, cast) -> str:
    """Prompt sintetico solo per anteprima. Non usato per la generazione vera."""
    parts: list[str] = []

    # Stile
    parts.append("=== STILE ===")
    parts.append(preset.expansion.strip())

    # Cast
    if cast:
        parts.append("")
        parts.append("=== CAST ===")
        for cs in cast:
            parts.append(f"- {cs.name}: {cs.visual_description}")

    # Scena
    parts.append("")
    parts.append("=== SCENA ===")
    parts.append(panel.description.strip())

    # Negative (preset)
    if preset.extra_negative_terms:
        parts.append("")
        parts.append("=== NEGATIVE ===")
        parts.append(", ".join(preset.extra_negative_terms))

    return "\n".join(parts)


# ============================================================
# RENDER
# ============================================================

with session_scope() as _s:
    _project = projects_repo.get_by_slug(_s, _user.id, _current_slug)
    if _project is None:
        appstate.clear_current_project()
        st.error("Il progetto attivo non esiste più.")
        st.markdown("[← Vai alla home](/)")
        st.stop()
    _project_id = _project.id
    _project_name = _project.name
    _project_style_id = _project.style_id


_plan_cfg = plan_config(_user.plan)
_render_sidebar(
    _user,
    project_name=_project_name,
    plan_label=_plan_cfg.label,
    credits_left=_user.credits_remaining,
    credits_total=_user.credits_total_this_period,
)

st.title("🎨 Stile")
st.caption(f"Progetto: **{_project_name}**")

tab_selez, tab_sfoglia, tab_aspetto, tab_anteprima = st.tabs([
    "✨ Selezione",
    "📚 Sfoglia libreria",
    "🎨 Aspetto pagina",
    "👁 Anteprima prompt",
])

with tab_selez:
    _render_tab_selezione(_project_style_id)

with tab_sfoglia:
    _render_tab_sfoglia(_project_id, _project_style_id)

with tab_aspetto:
    _render_tab_aspetto(_project_id)

with tab_anteprima:
    _render_tab_anteprima(_project_id, _project_style_id)
