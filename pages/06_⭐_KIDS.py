"""SnapToon — modalità ⭐ KIDS.

Wizard a 5 step per creare libretti illustrati per bambini con flusso
super-semplificato. Solo per ruolo `kids` e `admin`.

Flusso:
  Step 1 — Scegli template (1/2/3 personaggi · breve/lungo) + stile
  Step 2 — Scintilla narrativa + nomi personaggi
  Step 3 — Foto + descrizione personaggi
  Step 4 — Genera tutto (script Claude + reference + vignette AI-bake)
  Step 5 — Anteprima + esporta PDF
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import time
import uuid
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="KIDS — SnapToon",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "style" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


_inject_css()

from app_state.ui import enforce_sidebar_visibility
enforce_sidebar_visibility()


# ============================================================
# Backend imports
# ============================================================
import app_state as appstate
from auth import current_user, logout
from billing.plans import cost_for_operation, role_config
from db.models import CreditOperation, LengthTarget, Role
from db.repos import characters as characters_repo
from db.repos import covers as covers_repo
from db.repos import credits as credits_repo
from db.repos import kids_templates as kids_templates_repo
from db.repos import page_layouts as page_layouts_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import usage as usage_repo
from db.repos import users as users_repo
from db.repos import vignettes as vignettes_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from snaptoon_core.layout import GRIDS, export_pdf, render_page
from snaptoon_core.llm import DEFAULT_MODEL, client as llm_client
from snaptoon_core.models import Character, Dialogue, Page, Panel
from snaptoon_core.models import Script as PydScript
from snaptoon_core.styles_library import get_preset
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import (
    cover_illustration_key,
    page_render_key,
    pdf_export_key,
    reference_key,
    vignette_key,
)


# ============================================================
# Auth gate
# ============================================================
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

# Check accesso Kids — robusto a cache stale del modulo billing/plans:
# admin ha sempre accesso (via is_admin); kids tramite Role enum.
_user_role_str = _user.role.value if hasattr(_user.role, "value") else str(_user.role)
_can_use_kids = _user.is_admin or (_user_role_str == "kids")
if not _can_use_kids:
    st.error("Modalità Kids non disponibile per il tuo ruolo.")
    st.markdown("[← Vai alla home](/)")
    st.stop()

# Carica role_cfg per uso dopo (può essere None se cache stale, usiamo fallback)
try:
    _role_cfg = role_config(_user.role)
except KeyError:
    _role_cfg = None


# ============================================================
# Sidebar minimal
# ============================================================
with st.sidebar:
    if st.button("🚪 Esci", key="_sb_logout_kids", use_container_width=True):
        with session_scope() as s:
            logout(s)
        appstate.clear_session_keys()
        st.switch_page("app.py")


# ============================================================
# Costanti & helpers
# ============================================================

KIDS_STYLE_MAP = {
    "flat": ("Flat", "bold_toddler_graphic"),
    "3d": ("3D", "illumination_cartoon_style"),
    "manga": ("Manga", "japanese_preschool_anime"),
}

# Set di style_id riconducibili a progetti Kids (per filtrare la dashboard)
KIDS_STYLE_PRESET_IDS = {preset_id for _, preset_id in KIDS_STYLE_MAP.values()}

GRID_CAPACITY = {"splash": 1, "1+2": 3, "2x2": 4}

# Session-state keys
SK_VIEW = "_kids_view"  # "dashboard" | "wizard"
SK_STEP = "_kids_step"
SK_TEMPLATE_ID = "_kids_template_id"
SK_STYLE = "_kids_style"
SK_SCINTILLA = "_kids_scintilla"
SK_CHAR_NAMES = "_kids_char_names"
SK_CHAR_DESCS = "_kids_char_descs"
SK_CHAR_PHOTOS = "_kids_char_photos"  # bytes
SK_PYD_SCRIPT = "_kids_pyd_script"  # script generato (dict da Pydantic)
SK_REGEN_FEEDBACK = "_kids_regen_feedback"
SK_PROJECT_ID = "_kids_project_id"
SK_GEN_PROGRESS = "_kids_gen_progress"


def _step() -> int:
    return st.session_state.get(SK_STEP, 1)


def _set_step(n: int) -> None:
    st.session_state[SK_STEP] = n


def _reset_wizard() -> None:
    for k in [SK_VIEW, SK_STEP, SK_TEMPLATE_ID, SK_STYLE, SK_SCINTILLA,
              SK_CHAR_NAMES, SK_CHAR_DESCS, SK_CHAR_PHOTOS,
              SK_PYD_SCRIPT, SK_REGEN_FEEDBACK,
              SK_PROJECT_ID, SK_GEN_PROGRESS]:
        st.session_state.pop(k, None)


def _list_kids_projects(user_id) -> list[dict]:
    """Restituisce i progetti dell'utente che usano uno stile Kids."""
    with session_scope() as s:
        projects = projects_repo.list_by_owner(s, user_id)
        return [
            {
                "id": p.id, "slug": p.slug, "name": p.name,
                "style_id": p.style_id,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in projects
            if p.style_id in KIDS_STYLE_PRESET_IDS
        ]


# ============================================================
# Header + step indicator
# ============================================================

st.title("⭐ SnapToon KIDS")

# Decide: dashboard o wizard
current_view = st.session_state.get(SK_VIEW)
if current_view is None:
    # Prima visita: vedi se ci sono già libretti
    existing = _list_kids_projects(_user.id)
    if existing:
        st.session_state[SK_VIEW] = "dashboard"
    else:
        st.session_state[SK_VIEW] = "wizard"
        _set_step(1)
    current_view = st.session_state[SK_VIEW]

# Step indicator solo in modalità wizard
step = _step()
if current_view == "wizard":
    st.caption("Crea un libretto illustrato per bambini.")
    steps_labels = ["Template", "Scintilla", "Personaggi", "Storia", "Genera", "Esporta"]
    indicator_html = "<div style='display:flex;gap:12px;margin:16px 0;'>"
    for i, lbl in enumerate(steps_labels, start=1):
        color = "#F59E0B" if i == step else ("#10B981" if i < step else "#475569")
        bg = "#1A2035" if i == step else "transparent"
        indicator_html += (
            f"<div style='flex:1;padding:8px 12px;border-radius:6px;background:{bg};"
            f"border:1px solid {color};color:{color};font-weight:500;font-size:13px;"
            f"text-align:center;'>"
            f"{i}. {lbl}"
            "</div>"
        )
    indicator_html += "</div>"
    st.markdown(indicator_html, unsafe_allow_html=True)
else:
    st.caption("I tuoi libretti illustrati per bambini.")

st.divider()


# ============================================================
# DASHBOARD — lista libretti esistenti
# ============================================================


def _render_dashboard() -> None:
    libri = _list_kids_projects(_user.id)

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"### 📚 I miei libretti ({len(libri)})")
    with col_h2:
        if st.button("+ Nuovo libretto", type="primary", use_container_width=True):
            _reset_wizard()
            st.session_state[SK_VIEW] = "wizard"
            _set_step(1)
            st.rerun()

    if not libri:
        st.info("Non hai ancora libretti. Clicca **+ Nuovo libretto** per iniziare.")
        return

    st.markdown("")
    cols_per_row = 3
    for row_start in range(0, len(libri), cols_per_row):
        row = libri[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, lib in zip(cols, row):
            with col:
                with st.container(border=True):
                    cover_key = cover_illustration_key(lib["id"])
                    if object_exists(cover_key):
                        try:
                            data = download_bytes(cover_key)
                            st.image(data, use_container_width=True)
                        except Exception:
                            st.markdown(
                                "<div style='background:#161B26;height:200px;"
                                "border-radius:8px;display:flex;align-items:center;"
                                "justify-content:center;color:#475569;'>📕 (cover non disponibile)</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            "<div style='background:#161B26;height:200px;"
                            "border-radius:8px;display:flex;align-items:center;"
                            "justify-content:center;color:#475569;'>📕</div>",
                            unsafe_allow_html=True,
                        )

                    st.markdown(f"**{lib['name']}**")
                    st.caption(f"Creato il {lib['created_at'].strftime('%d/%m/%Y')}")

                    col_open, col_del = st.columns([2, 1])
                    with col_open:
                        if st.button(
                            "📖 Apri",
                            key=f"_open_kid_{lib['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state[SK_PROJECT_ID] = str(lib["id"])
                            st.session_state[SK_VIEW] = "wizard"
                            _set_step(6)
                            st.rerun()
                    with col_del:
                        confirm_key = f"_confirm_del_kid_{lib['id']}"
                        if st.session_state.get(confirm_key):
                            if st.button(
                                "❌",
                                key=f"_del_kid_yes_{lib['id']}",
                                use_container_width=True,
                                help="Conferma elimina",
                            ):
                                with session_scope() as s:
                                    proj = projects_repo.get_by_id(s, lib["id"])
                                    if proj is not None:
                                        projects_repo.soft_delete(s, proj)
                                st.session_state.pop(confirm_key, None)
                                st.toast("Libretto eliminato.", icon="🗑")
                                st.rerun()
                        else:
                            if st.button(
                                "🗑",
                                key=f"_del_kid_{lib['id']}",
                                use_container_width=True,
                                help="Elimina",
                            ):
                                st.session_state[confirm_key] = True
                                st.rerun()


# ============================================================
# STEP 1 — Template + stile
# ============================================================


def _render_step_1() -> None:
    st.markdown("### Step 1 — Scegli il tuo template")

    with session_scope() as s:
        templates = kids_templates_repo.list_all(s, only_active=True)
        templates_view = [
            {
                "id": t.id, "slug": t.slug, "label": t.label,
                "n_characters": t.n_characters,
                "length_target": t.length_target,
                "n_panels": len(t.scene_distribution),
                "n_pages": len(t.grid_distribution),
                "notes": t.notes,
            } for t in templates
        ]

    if not templates_view:
        st.error("Nessun template disponibile. Contatta l'amministratore.")
        return

    # Raggruppa per N personaggi (1/2/3)
    by_chars: dict[int, list[dict]] = {}
    for t in templates_view:
        by_chars.setdefault(t["n_characters"], []).append(t)

    st.markdown("**👥 Quanti personaggi?**")

    selected_template_id = st.session_state.get(SK_TEMPLATE_ID)

    cols = st.columns(3)
    for col_idx, n_chars in enumerate([1, 2, 3]):
        with cols[col_idx]:
            with st.container(border=True):
                st.markdown(f"#### {n_chars} personagg{'io' if n_chars == 1 else 'i'}")
                avail = by_chars.get(n_chars, [])

                # Per ogni lunghezza
                for tpl in avail:
                    is_selected = (tpl["id"] == selected_template_id)
                    btn_label = f"{'✅' if is_selected else '○'} {tpl['length_target'].capitalize()} ({tpl['n_pages']} pag · {tpl['n_panels']} vign)"
                    if st.button(
                        btn_label,
                        key=f"_tpl_{tpl['id']}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary",
                    ):
                        st.session_state[SK_TEMPLATE_ID] = tpl["id"]
                        st.rerun()

    st.divider()
    st.markdown("**🎨 Stile visivo**")

    selected_style = st.session_state.get(SK_STYLE)
    cols_style = st.columns(3)
    for col_idx, (slug, (label, preset_id)) in enumerate(KIDS_STYLE_MAP.items()):
        with cols_style[col_idx]:
            with st.container(border=True):
                is_selected = (slug == selected_style)
                if st.button(
                    f"{'✅' if is_selected else '○'} {label}",
                    key=f"_style_{slug}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    st.session_state[SK_STYLE] = slug
                    st.rerun()
                preset = get_preset(preset_id)
                if preset:
                    st.caption(preset.expansion[:140] + "...")

    st.divider()

    can_continue = bool(st.session_state.get(SK_TEMPLATE_ID)) and bool(st.session_state.get(SK_STYLE))
    if st.button(
        "Continua →",
        type="primary",
        disabled=not can_continue,
        help=None if can_continue else "Scegli template e stile prima di continuare.",
        use_container_width=True,
    ):
        _set_step(2)
        st.rerun()


# ============================================================
# STEP 2 — Scintilla + nomi
# ============================================================


def _render_step_2() -> None:
    template_id = st.session_state[SK_TEMPLATE_ID]
    with session_scope() as s:
        tpl = kids_templates_repo.get_by_id(s, template_id)
        if tpl is None:
            st.error("Template non trovato.")
            return
        n_chars = tpl.n_characters
        n_pages = len(tpl.grid_distribution)

    st.markdown(f"### Step 2 — La tua storia ({n_pages} pagine, {n_chars} personagg{'io' if n_chars == 1 else 'i'})")

    st.markdown("**🌟 La scintilla**")
    st.caption(
        "Descrivi in poche righe l'idea del tuo libretto: ambientazione, "
        "avventura, lezione di vita..."
    )
    scintilla = st.text_area(
        "Scintilla",
        value=st.session_state.get(SK_SCINTILLA, ""),
        height=140,
        placeholder="Es. Mia il riccio è curiosa e perde la mamma nel bosco. Trova nuovi amici "
                    "che la aiutano a tornare a casa.",
        label_visibility="collapsed",
    )

    st.markdown(f"**👥 Nomi dei {n_chars} personagg{'io' if n_chars == 1 else 'i'}**")
    existing_names = st.session_state.get(SK_CHAR_NAMES, [])
    names = []
    cols = st.columns(min(n_chars, 3))
    for i in range(n_chars):
        with cols[i % len(cols)]:
            default = existing_names[i] if i < len(existing_names) else ""
            n = st.text_input(
                f"Nome personaggio {i+1}",
                value=default,
                placeholder=["Mia", "Leo", "Sole"][i] if i < 3 else f"Personaggio {i+1}",
                key=f"_kids_name_{i}",
            )
            names.append(n.strip())

    st.divider()

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Indietro", use_container_width=True):
            _set_step(1)
            st.rerun()
    with col_next:
        all_named = all(n for n in names)
        if st.button(
            "Continua →",
            type="primary",
            disabled=(not scintilla.strip()) or (not all_named),
            help=None if (scintilla.strip() and all_named) else "Compila scintilla e tutti i nomi.",
            use_container_width=True,
        ):
            st.session_state[SK_SCINTILLA] = scintilla
            st.session_state[SK_CHAR_NAMES] = names
            _set_step(3)
            st.rerun()


# ============================================================
# STEP 3 — Foto + descrizione personaggi
# ============================================================


def _render_step_3() -> None:
    names = st.session_state[SK_CHAR_NAMES]
    n_chars = len(names)

    st.markdown(f"### Step 3 — I personaggi")
    st.caption(
        "Per ogni personaggio, descrivi il suo aspetto. "
        "Puoi caricare una foto come riferimento visivo (opzionale ma consigliato)."
    )

    existing_descs = st.session_state.get(SK_CHAR_DESCS, [""] * n_chars)
    existing_photos = st.session_state.get(SK_CHAR_PHOTOS, [None] * n_chars)

    descs = []
    photos = []

    for i, name in enumerate(names):
        with st.container(border=True):
            st.markdown(f"#### {name}")
            col_photo, col_desc = st.columns([1, 2])
            with col_photo:
                uploaded = st.file_uploader(
                    f"📷 Foto di riferimento (opzionale)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"_kids_photo_{i}",
                )
                photo_bytes = None
                if uploaded is not None:
                    photo_bytes = uploaded.read()
                    st.image(photo_bytes, use_container_width=True)
                elif i < len(existing_photos) and existing_photos[i]:
                    photo_bytes = existing_photos[i]
                    st.image(photo_bytes, use_container_width=True)
                    st.caption("_(foto già caricata)_")
                else:
                    st.caption("Nessuna foto caricata.")
                photos.append(photo_bytes)

            with col_desc:
                d = st.text_area(
                    "Descrizione visiva (aspetto, vestiti, caratteristiche)",
                    value=existing_descs[i] if i < len(existing_descs) else "",
                    placeholder=f"Es. {name} è una bambina di 6 anni, capelli castani ricci, "
                                "occhi verdi, indossa una salopette gialla e scarpe rosse.",
                    height=140,
                    key=f"_kids_desc_{i}",
                )
                descs.append(d.strip())

    st.divider()
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Indietro", use_container_width=True, key="_step3_back"):
            _set_step(2)
            st.rerun()
    with col_next:
        all_described = all(d for d in descs)
        if st.button(
            "Continua →",
            type="primary",
            disabled=not all_described,
            help=None if all_described else "Aggiungi una descrizione per ogni personaggio.",
            use_container_width=True,
            key="_step3_next",
        ):
            st.session_state[SK_CHAR_DESCS] = descs
            st.session_state[SK_CHAR_PHOTOS] = photos
            # Invalida script precedente (descrizioni cambiate)
            st.session_state.pop(SK_PYD_SCRIPT, None)
            _set_step(4)
            st.rerun()


# ============================================================
# STEP 4 — Anteprima Storia (genera con Claude, approva o rigenera)
# ============================================================


def _do_generate_story(scintilla: str, names: list[str], descs: list[str],
                       grid_distribution: list[str], feedback: str = "") -> tuple[bool, str | None]:
    """Chiama Claude per la storia + salva in session_state. Returns (ok, err)."""
    cost = cost_for_operation("adapt_script")
    try:
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.charge(
                s, fresh_user,
                cost=cost,
                operation=CreditOperation.adapt_script,
                reason=f"KIDS storia (preview)",
            )
    except InsufficientCreditsError as e:
        return False, f"Crediti insufficienti: servono {e.required}, ne hai {e.available}."

    try:
        pyd_script = _generate_kids_script(scintilla, names, descs, grid_distribution, feedback)
        # Salva in session_state come dict per serializzazione safe
        st.session_state[SK_PYD_SCRIPT] = pyd_script.model_dump()
        return True, None
    except Exception as e:
        err = str(e)[:500]
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.refund(
                s, fresh_user,
                amount=cost,
                reason=f"Refund kids story: {err}",
            )
        return False, f"Errore Claude: {err}"


def _render_step_4_storia() -> None:
    st.markdown("### Step 4 — Ecco la tua storia! 📖")

    template_id = st.session_state[SK_TEMPLATE_ID]
    with session_scope() as s:
        tpl = kids_templates_repo.get_by_id(s, template_id)
        if tpl is None:
            st.error("Template non valido.")
            return
        grid_distribution = list(tpl.grid_distribution)
        n_pages = len(grid_distribution)

    scintilla = st.session_state[SK_SCINTILLA]
    names = st.session_state[SK_CHAR_NAMES]
    descs = st.session_state[SK_CHAR_DESCS]

    # Se non c'è ancora una storia in memoria, generala
    if SK_PYD_SCRIPT not in st.session_state:
        with st.spinner("✍️ Claude sta scrivendo la tua storia..."):
            ok, err = _do_generate_story(scintilla, names, descs, grid_distribution, feedback="")
        if not ok:
            st.error(err)
            if st.button("← Torna indietro", use_container_width=True):
                _set_step(3)
                st.rerun()
            return
        st.rerun()  # ricarica con la storia disponibile

    # Storia presente — mostra in formato colorato
    pyd_dict = st.session_state[SK_PYD_SCRIPT]
    logline = pyd_dict.get("logline", "")
    pages = pyd_dict.get("pages", [])

    # Card centrale con la storia
    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg, #1A2035 0%, #2D1B4E 100%);
                    border-radius:16px;padding:24px;margin:16px 0;
                    border:2px solid #F59E0B;'>
            <div style='font-size:14px;color:#F59E0B;text-transform:uppercase;
                        letter-spacing:0.1em;margin-bottom:8px;'>✨ La tua storia</div>
            <div style='font-size:22px;font-weight:600;color:#F1F5F9;
                        line-height:1.5;font-style:italic;'>
                "{logline}"
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Riassunto: mostra pagina per pagina
    st.markdown("##### 📚 Come si svolge:")
    for pg in pages:
        with st.expander(f"📖 Pagina {pg['number']} ({len(pg.get('panels', []))} vignette)", expanded=False):
            for pn in pg.get("panels", []):
                desc = pn.get("description", "")
                dlg_text = pn.get("dialogue_text") if isinstance(pn, dict) else None
                dlg_speaker = pn.get("dialogue_speaker") if isinstance(pn, dict) else None
                # Compatibilità con vecchio formato (dialogues list)
                if "dialogues" in pn and pn["dialogues"]:
                    d = pn["dialogues"][0]
                    dlg_text = d.get("text")
                    dlg_speaker = d.get("speaker")

                st.markdown(f"**🎬 Vignetta {pn['number']}** — {desc}")
                if dlg_text:
                    speaker_str = f"**{dlg_speaker}**: " if dlg_speaker else ""
                    st.markdown(f"  💬 {speaker_str}_{dlg_text}_")
                st.markdown("")

    st.divider()

    # Box rigenera (toggle)
    show_regen = st.session_state.get("_kids_show_regen", False)

    col_back, col_regen, col_ok = st.columns([1, 1, 2])
    with col_back:
        if st.button("← Indietro", use_container_width=True, key="_step4_back"):
            _set_step(3)
            st.rerun()
    with col_regen:
        if st.button(
            "🔄 Rigenera storia",
            use_container_width=True,
            key="_step4_regen_toggle",
        ):
            st.session_state["_kids_show_regen"] = not show_regen
            st.rerun()
    with col_ok:
        if st.button(
            "✨ Mi piace! Genera le immagini →",
            type="primary",
            use_container_width=True,
            key="_step4_next",
        ):
            _set_step(5)
            st.rerun()

    if show_regen:
        st.markdown("---")
        with st.container(border=True):
            st.markdown("##### 🔄 Rigenera con un suggerimento")
            st.caption(
                "Vuoi cambiare qualcosa? Scrivi qui cosa modificare e Claude "
                "scriverà una nuova versione tenendo conto del tuo feedback."
            )
            feedback = st.text_area(
                "Note opzionali",
                value=st.session_state.get(SK_REGEN_FEEDBACK, ""),
                placeholder="Es. rendila più allegra, meno paurosa, aggiungi un finale a sorpresa, "
                            "fai parlare di più Mia, ambientala in inverno...",
                height=100,
                label_visibility="collapsed",
            )

            cost = cost_for_operation("adapt_script")
            st.caption(f"💰 Rigenerare costa **{cost} crediti**.")

            col_cancel, col_go = st.columns(2)
            with col_cancel:
                if st.button("Annulla", use_container_width=True, key="_kids_regen_cancel"):
                    st.session_state["_kids_show_regen"] = False
                    st.rerun()
            with col_go:
                if st.button(
                    "🔄 Rigenera adesso",
                    type="primary",
                    use_container_width=True,
                    key="_kids_regen_go",
                ):
                    st.session_state[SK_REGEN_FEEDBACK] = feedback
                    with st.spinner("✍️ Claude sta riscrivendo..."):
                        ok, err = _do_generate_story(scintilla, names, descs, grid_distribution, feedback)
                    if ok:
                        st.session_state["_kids_show_regen"] = False
                        st.toast("Nuova storia pronta!", icon="✨")
                        st.rerun()
                    else:
                        st.error(err)


# ============================================================
# STEP 5 — Genera tutto
# ============================================================

CLAUDE_KIDS_SYSTEM = """Sei un autore di libri illustrati per bambini (5-8 anni).
Scrivi sceneggiature per fumetti brevi e dolci, con dialoghi semplici.

VINCOLI CRITICI — RISPETTA ESATTAMENTE:
- Numero di pagine fissato (lo riceverai)
- Numero di vignette per pagina fissato (lo riceverai)
- Dialoghi MASSIMO 4-5 parole (devono essere scritti DENTRO le immagini)
- Massimo 1 dialogo per vignetta
- Lessico semplice da bambini
- Nei dialoghi usa solo testo in MAIUSCOLO breve, niente apostrofi, niente accenti
  difficili. Esempi buoni: "CIAO!", "AIUTO!", "DOVE SEI?", "ANDIAMO!", "MAMMA!"
- Niente asterischi, niente testo cancellato, niente markdown
"""


def _kids_script_schema(n_pages: int, capacities: list[int]) -> dict:
    """JSON schema dinamico per Claude. Ogni pagina ha N vignette pre-fissate."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "logline": {"type": "string"},
            "pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "integer"},
                        "panels": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "number": {"type": "integer"},
                                    "description": {"type": "string"},
                                    "dialogue_speaker": {"type": ["string", "null"]},
                                    "dialogue_text": {"type": ["string", "null"]},
                                },
                                "required": ["number", "description", "dialogue_speaker", "dialogue_text"],
                            },
                        },
                    },
                    "required": ["number", "panels"],
                },
            },
        },
        "required": ["logline", "pages"],
    }


def _generate_kids_script(
    scintilla: str,
    names: list[str],
    descs: list[str],
    grid_distribution: list[str],
    feedback: str = "",
) -> PydScript:
    """Chiama Claude per produrre uno script con gabbie pre-fissate.

    feedback: note opzionali dall'utente per ri-orientare una rigenerazione
              (es. "rendi più allegra", "meno paurosa", "aggiungi un nonno").
    """
    n_pages = len(grid_distribution)
    capacities = [GRID_CAPACITY[g] for g in grid_distribution]

    cast_block = "\n".join([f"- {n}: {d}" for n, d in zip(names, descs)])
    page_structure = "\n".join([
        f"  Pagina {i+1}: {capacities[i]} vignett{'a' if capacities[i] == 1 else 'e'}"
        for i in range(n_pages)
    ])

    feedback_block = ""
    if feedback.strip():
        feedback_block = (
            f"\n\nNOTE AGGIUNTIVE DELL'AUTORE (considera questi suggerimenti "
            f"per cambiare/migliorare la storia rispetto a una versione precedente):\n"
            f"{feedback.strip()}\n"
        )

    user_msg = f"""Scrivi un fumetto per bambini.

SCINTILLA:
{scintilla}

PERSONAGGI:
{cast_block}

STRUTTURA OBBLIGATORIA:
{page_structure}
{feedback_block}
Output JSON con logline + pages (ognuna con panels).
Ogni panel ha description (concreta, visualizzabile) + dialogue_speaker + dialogue_text.
Se la vignetta non ha dialogo, metti dialogue_speaker=null e dialogue_text=null.
"""

    response = llm_client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8000,
        system=CLAUDE_KIDS_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": _kids_script_schema(n_pages, capacities),
            }
        },
    )
    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)

    # Costruisci Pydantic Script
    pages = []
    for pg in data["pages"]:
        panels = []
        for pn in pg["panels"]:
            dialogues = []
            if pn.get("dialogue_text"):
                dialogues.append(Dialogue(
                    kind="FUMETTO",
                    speaker=pn.get("dialogue_speaker"),
                    text=pn["dialogue_text"],
                ))
            panels.append(Panel(
                number=pn["number"],
                description=pn["description"],
                dialogues=dialogues,
            ))
        pages.append(Page(number=pg["number"], panels=panels))

    return PydScript(
        logline=data["logline"],
        characters=[Character(name=n, visual_bible=d, voice="")
                    for n, d in zip(names, descs)],
        pages=pages,
    )


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "kids"


def _build_kids_reference_prompt(name: str, desc: str, style_preset_id: str) -> str:
    preset = get_preset(style_preset_id)
    parts = []
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")
    parts.append(
        f"=== CHARACTER REFERENCE ===\n"
        f"Subject: {name}\n"
        f"Visual description: {desc}\n"
    )
    parts.append(
        "=== RENDER MODE ===\n"
        "Full-body character on uniform clean background. Centered standing pose. "
        "Cartoon for children, friendly, expressive. Edge-to-edge full-bleed."
    )
    parts.append("=== AVOID ===\nphotorealism, scary, dark themes, frame, border, text, watermark")
    return "\n\n".join(parts)


def _build_kids_panel_prompt(
    panel: Panel,
    cast: list[dict],  # {name, desc}
    style_preset_id: str,
    scene_params: dict,
) -> str:
    preset = get_preset(style_preset_id)
    parts = []
    parts.append(
        "=== RENDER MODE ===\n"
        "Full-bleed single comic panel for children's book. Bright friendly colors. "
        "Edge-to-edge, no external frame or page border."
    )
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")
    parts.append(f"=== SCENE ===\n{panel.description.strip()}")

    # Scene directives
    from snaptoon_core.scene import ASPECT_RATIOS, SHOT_DISTANCES, SHOT_ANGLES, MOODS
    clauses = []
    sd = scene_params.get("shot_distance")
    sa = scene_params.get("shot_angle")
    md = scene_params.get("mood")
    if sd:
        o = next((o for o in SHOT_DISTANCES if o.key == sd), None)
        if o:
            clauses.append(f"SHOT DISTANCE: {o.prompt_en}.")
    if sa:
        o = next((o for o in SHOT_ANGLES if o.key == sa), None)
        if o:
            clauses.append(f"CAMERA ANGLE: {o.prompt_en}.")
    if md:
        o = next((o for o in MOODS if o.key == md), None)
        if o:
            clauses.append(f"MOOD: {o.prompt_en}.")
    if clauses:
        parts.append("=== DIRECTING ===\n" + " ".join(clauses))

    # Cast block (per consistency con reference)
    if cast:
        cast_block = ["=== CHARACTERS IN THIS PANEL ==="]
        for cs in cast:
            cast_block.append(f"- {cs['name']}: {cs['description']}")
        cast_block.append(
            "Characters must look IDENTICAL to the reference images provided. "
            "Same face, hair, clothes. Visual ground truth."
        )
        parts.append("\n".join(cast_block))

    # Balloon AI-bake: se ci sono dialoghi, instruct AI a disegnarli
    if panel.dialogues:
        balloon_block = ["=== SPEECH BUBBLE (DRAW IT IN THE IMAGE) ==="]
        for dlg in panel.dialogues:
            speaker = dlg.speaker or "narrator"
            text_clean = (dlg.text or "").upper()
            balloon_block.append(
                f"Draw a clean white speech bubble with a thin black border "
                f"pointing toward {speaker}. Inside the bubble write EXACTLY this text "
                f"in a clear bold sans-serif font, no decoration: '{text_clean}'"
            )
        balloon_block.append(
            "The speech bubble must be readable, white background, black border, "
            "black text. Place it in an empty part of the composition. "
            "Spell every letter exactly as given. No extra words."
        )
        parts.append("\n".join(balloon_block))
    else:
        parts.append("=== TEXT ===\nNo text or speech bubble in the image.")

    parts.append(
        "=== AVOID ===\n"
        "photorealism, scary or dark themes, blood, violence, frame, border, "
        "watermark, multiple panels, comic page layout, weird letters, "
        "misspelled words, scrambled text"
    )

    return "\n\n".join(parts)


def _hash_prompt(prompt: str, *extra: str) -> str:
    h = hashlib.sha256(prompt.encode("utf-8"))
    for e in extra:
        h.update(b"|")
        h.update(e.encode("utf-8"))
    return h.hexdigest()


def _render_step_5() -> None:
    st.markdown("### Step 5 — Crea il fumetto!")

    # Mostra recap delle scelte
    template_id = st.session_state[SK_TEMPLATE_ID]
    style_slug = st.session_state[SK_STYLE]
    names = st.session_state[SK_CHAR_NAMES]
    descs = st.session_state[SK_CHAR_DESCS]
    photos = st.session_state.get(SK_CHAR_PHOTOS, [])
    scintilla = st.session_state[SK_SCINTILLA]

    with session_scope() as s:
        tpl = kids_templates_repo.get_by_id(s, template_id)
        if tpl is None:
            st.error("Template non valido.")
            return
        tpl_label = tpl.label
        n_pages = len(tpl.grid_distribution)
        n_panels = len(tpl.scene_distribution)
        grid_distribution = list(tpl.grid_distribution)
        scene_distribution = list(tpl.scene_distribution)

    style_label, style_preset_id = KIDS_STYLE_MAP[style_slug]

    with st.container(border=True):
        st.markdown("**Riepilogo**")
        st.caption(f"Template: **{tpl_label}** · Stile: **{style_label}**")
        st.caption(f"Personaggi: {', '.join(names)}")
        st.caption(f"Pagine: {n_pages} · Vignette: {n_panels}")
        st.caption(f"Scintilla: _{scintilla[:120]}{'…' if len(scintilla) > 120 else ''}_")

    # Costi (lo script è già stato pagato in step 4, non lo conto qui)
    cost_per_ref = cost_for_operation("generate_reference")
    cost_per_panel = cost_for_operation("generate_panel", quality="medium")
    cost_cover = cost_for_operation("generate_panel", quality="medium")
    cost_total = cost_per_ref * len(names) + cost_cover + cost_per_panel * n_panels
    st.caption(
        f"💰 Costo immagini: **{cost_total} crediti** "
        f"({cost_per_ref * len(names)} reference + {cost_cover} copertina + "
        f"{cost_per_panel * n_panels} vignette)"
    )

    can_afford = _user.credits_remaining >= cost_total
    if not can_afford:
        st.error(
            f"⚠️ Crediti insufficienti: servono {cost_total}, ne hai {_user.credits_remaining}. "
            "Contatta l'amministratore."
        )

    # Bottone genera
    gen_state = st.session_state.get(SK_GEN_PROGRESS, {})
    project_id = st.session_state.get(SK_PROJECT_ID)

    if project_id is None:
        if st.button(
            "✨ Crea il fumetto!",
            type="primary",
            disabled=not can_afford,
            use_container_width=True,
        ):
            _execute_full_kids_generation(
                template_id=template_id,
                tpl_label=tpl_label,
                style_slug=style_slug,
                style_preset_id=style_preset_id,
                scintilla=scintilla,
                names=names,
                descs=descs,
                photos=photos,
                grid_distribution=grid_distribution,
                scene_distribution=scene_distribution,
            )
    else:
        st.info("Generazione completata.")
        if st.button("📖 Vai all'anteprima", type="primary", use_container_width=True):
            _set_step(6)
            st.rerun()

    col_back, _ = st.columns(2)
    with col_back:
        if st.button("← Indietro alla storia", use_container_width=True, key="_step5_back"):
            _set_step(4)
            st.rerun()


def _build_kids_cover_prompt(
    title: str,
    cast: list[dict],
    style_preset_id: str,
) -> str:
    """Prompt per la copertina del libretto kids."""
    preset = get_preset(style_preset_id)
    parts = []
    parts.append(
        "=== RENDER MODE ===\n"
        "Vertical book cover illustration for a children's picture book. "
        "Edge-to-edge full-bleed. Cinematic poster composition, eye-catching, "
        "bright friendly colors. No frame, no border. The title and characters "
        "should be the focus."
    )
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")

    parts.append(f"=== COVER ===\nBook cover for «{title}»")

    if cast:
        cast_block = ["=== CHARACTERS ON COVER ==="]
        for cs in cast:
            cast_block.append(f"- {cs['name']}: {cs['description']}")
        cast_block.append(
            "Characters must look IDENTICAL to reference images. Hero pose, friendly expression."
        )
        parts.append("\n".join(cast_block))

    # Titolo grande nella cover (AI-bake)
    parts.append(
        f"=== TITLE TEXT (DRAW IT IN THE IMAGE) ===\n"
        f"At the top of the image, draw the title in big bold playful "
        f"children's book font: '{title.upper()}'. Use clear readable letters, "
        f"strong outline so it stands out from the background. No subtitle, "
        f"no author name."
    )

    parts.append(
        "=== AVOID ===\n"
        "scary, dark themes, frame, border, watermark, multiple titles, "
        "scrambled text, weird letters, misspelled words"
    )
    return "\n\n".join(parts)


def _execute_full_kids_generation(
    *,
    template_id: uuid.UUID,
    tpl_label: str,
    style_slug: str,
    style_preset_id: str,
    scintilla: str,
    names: list[str],
    descs: list[str],
    photos: list[bytes | None],
    grid_distribution: list[str],
    scene_distribution: list[dict],
) -> None:
    """Esegue la pipeline completa: crea progetto, chiama Claude, genera reference, vignette.

    Ogni step appare gradualmente con messaggio simpatico + immagine live.
    """
    from snaptoon_core.generator import OpenAIImageGenerator

    # Galleria live che cresce mentre generiamo
    st.markdown("### 🎁 Sto creando il tuo fumetto...")
    status_slot = st.empty()  # messaggio simpatico corrente
    gallery_container = st.container()  # qui mostriamo le immagini man mano

    completed: list[dict] = []  # {kind, label, bytes, message}

    def _show_status(emoji: str, msg: str) -> None:
        status_slot.markdown(
            f"<div style='padding:16px;background:#1A2035;border-radius:8px;"
            f"border:1px solid #F59E0B;font-size:18px;text-align:center;'>"
            f"<span style='font-size:32px;'>{emoji}</span><br>{msg}"
            f"</div>",
            unsafe_allow_html=True,
        )

    def _add_to_gallery(image_bytes: bytes, label: str, message: str) -> None:
        completed.append({"bytes": image_bytes, "label": label})
        with gallery_container:
            st.success(message)
            cols = st.columns(min(4, max(1, len(completed))))
            # Mostra tutta la galleria aggiornata (ricreata ad ogni step)
            for i, item in enumerate(completed):
                with cols[i % len(cols)]:
                    st.image(item["bytes"], caption=item["label"], use_container_width=True)
        try:
            st.toast(message, icon="✨")
        except Exception:
            pass

    t0 = time.time()

    # === 1. Crea progetto ===
    _show_status("📦", "Sto preparando la scatola magica del fumetto...")
    project_name = f"{tpl_label} — {names[0]}"
    with session_scope() as s:
        fresh_user = users_repo.get_by_id(s, _user.id)
        project = projects_repo.create_project(
            s, owner=fresh_user, name=project_name,
            length_target=LengthTarget(scene_distribution and "lungo" if len(scene_distribution) > 30 else "breve"),
        )
        projects_repo.set_style(s, project, style_preset_id)
        project_id_local = project.id
    st.session_state[SK_PROJECT_ID] = str(project_id_local)

    # === 2. Carica lo script PRE-APPROVATO dallo step 4 ===
    _show_status("📖", "La storia è già pronta dallo step precedente...")
    pyd_dict = st.session_state.get(SK_PYD_SCRIPT)
    if not pyd_dict:
        st.error("Nessuno script approvato. Torna allo Step 4 per generare/approvare la storia.")
        return
    try:
        pyd_script = PydScript.model_validate(pyd_dict)
        kids_title = pyd_script.logline or project_name
        # Save
        with session_scope() as s:
            project = projects_repo.get_by_id(s, project_id_local)
            orm_script = scripts_repo.get_or_create(s, project)
            scripts_repo.save_pydantic(s, orm_script, pyd_script)
            # Crea character_sheets
            for nm, ds in zip(names, descs):
                try:
                    characters_repo.create_character(
                        s, project=project,
                        name=nm, visual_description=ds,
                    )
                except ValueError:
                    pass  # già esiste
        with gallery_container:
            st.success("📖 La storia è approvata!")
            st.caption(f"_Logline:_ **{kids_title}**")
    except Exception as e:
        st.error(f"Errore caricamento script: {e}")
        return

    # === 3. Save grid_distribution come page_layouts ===
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id_local)
        for page_idx, grid_id in enumerate(grid_distribution, start=1):
            pl = page_layouts_repo.get_or_create(s, project, page_idx)
            page_layouts_repo.set_grid(s, pl, grid_id)

    # === 4. Salva scene_params nei panel del script ===
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id_local)
        pyd_script_db = scripts_repo.load_pydantic(project.script)
        flat_panels = [(p, panel) for p in pyd_script_db.pages for panel in p.panels]
        for (page, panel), scene in zip(flat_panels, scene_distribution):
            if scene.get("shot_distance"):
                panel.shot_distance = scene["shot_distance"]
            if scene.get("shot_angle"):
                panel.shot_angle = scene["shot_angle"]
            if scene.get("mood"):
                panel.mood = scene["mood"]
            panel.characters_in_scene = names[:]  # tutti in scena per kids
        scripts_repo.save_pydantic(s, project.script, pyd_script_db)

    # === 5. Genera reference per ogni personaggio ===
    generator = OpenAIImageGenerator()
    char_storage_keys = {}
    for i, name in enumerate(names):
        _show_status("👤", f"Sto disegnando **{name}**...")
        try:
            ref_keys_for_gen = []
            # Se c'è foto utente, la usiamo come reference per il modello
            if photos[i]:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(photos[i])
                tmp.close()
                ref_keys_for_gen.append(Path(tmp.name))

            prompt = _build_kids_reference_prompt(name, descs[i], style_preset_id)

            with session_scope() as s:
                fresh_user = users_repo.get_by_id(s, _user.id)
                credits_repo.charge(
                    s, fresh_user,
                    cost=cost_for_operation("generate_reference"),
                    operation=CreditOperation.generate_reference,
                    reason=f"KIDS reference {name}",
                )

            image_bytes = generator._generate_bytes(
                prompt=prompt,
                size="1024x1024",
                reference_images=ref_keys_for_gen if ref_keys_for_gen else None,
                quality="medium",
            )
            # Upload come reference slot 1
            with session_scope() as s:
                project = projects_repo.get_by_id(s, project_id_local)
                cs = next((c for c in project.character_sheets if c.name == name), None)
                if cs is None:
                    continue
                ref_storage = reference_key(project_id_local, cs.id, 1)
                upload_bytes(ref_storage, image_bytes, content_type="image/png")
                characters_repo.upsert_reference(
                    s, cs, slot_number=1, storage_key=ref_storage,
                    mime_type="image/png", file_size=len(image_bytes),
                )
                char_storage_keys[name] = ref_storage

            # Mostra il personaggio nella galleria
            _add_to_gallery(
                image_bytes,
                label=name,
                message=f"👋 Ecco **{name}**! Pronto a entrare nella storia.",
            )

            # Cleanup tempfile
            for p in ref_keys_for_gen:
                try:
                    p.unlink()
                except OSError:
                    pass
        except Exception as e:
            st.warning(f"Reference di {name} fallita: {e}")
            with session_scope() as s:
                fresh_user = users_repo.get_by_id(s, _user.id)
                credits_repo.refund(
                    s, fresh_user,
                    amount=cost_for_operation("generate_reference"),
                    reason=f"Refund kids ref: {e}",
                )

    # === 5.5 — Genera COPERTINA del libretto ===
    _show_status("📕", "Sto disegnando la **copertina** del tuo libretto...")
    try:
        cast_block_for_cover = [{"name": n, "description": d} for n, d in zip(names, descs)]
        cover_prompt = _build_kids_cover_prompt(kids_title, cast_block_for_cover, style_preset_id)

        # Reference temp files dei personaggi
        cover_refs = []
        for name in names:
            rk = char_storage_keys.get(name)
            if rk and object_exists(rk):
                data = download_bytes(rk)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(data)
                tmp.close()
                cover_refs.append(Path(tmp.name))

        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.charge(
                s, fresh_user,
                cost=cost_for_operation("generate_panel", quality="medium"),
                operation=CreditOperation.generate_cover,
                reason=f"KIDS copertina {kids_title}",
                reference_id=str(project_id_local),
            )

        cover_bytes = generator._generate_bytes(
            prompt=cover_prompt,
            size="1024x1536",  # verticale per copertina
            reference_images=cover_refs if cover_refs else None,
            quality="medium",
        )

        cover_storage = cover_illustration_key(project_id_local)
        upload_bytes(cover_storage, cover_bytes, content_type="image/png")

        # Save sul Cover ORM
        with session_scope() as s:
            project = projects_repo.get_by_id(s, project_id_local)
            cover_orm = covers_repo.get_or_create(s, project)
            covers_repo.update_text(s, cover_orm, title=kids_title, author="", description=scintilla)
            covers_repo.update_illustration_key(s, cover_orm, cover_storage)

        _add_to_gallery(
            cover_bytes,
            label="📕 Copertina",
            message="✨ La **copertina** è pronta!!! Vediamo subito come viene?",
        )

        for p in cover_refs:
            try:
                p.unlink()
            except OSError:
                pass
    except Exception as e:
        st.warning(f"Copertina fallita: {e}")
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.refund(
                s, fresh_user,
                amount=cost_for_operation("generate_panel", quality="medium"),
                reason=f"Refund kids cover: {e}",
            )

    # === 6. Genera vignette in batch — una alla volta con annuncio simpatico ===
    cast_block_for_panel = [{"name": n, "description": d} for n, d in zip(names, descs)]

    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id_local)
        pyd_script_db = scripts_repo.load_pydantic(project.script)
        flat_panels = [(p, panel) for p in pyd_script_db.pages for panel in p.panels]

    # Conta quante vignette per pagina (per messaggi simpatici)
    panels_per_page: dict[int, int] = {}
    for page, panel in flat_panels:
        panels_per_page[page.number] = panels_per_page.get(page.number, 0) + 1

    last_announced_page = 0  # tracking annunci pagina

    for panel_idx, ((page, panel), scene) in enumerate(zip(flat_panels, scene_distribution)):
        # Messaggio simpatico — diverso al primo panel di ogni pagina
        if page.number != last_announced_page:
            if page.number == 1:
                _show_status("📖", f"**Pagina 1** in arrivo! Facciamo le vignette?")
            else:
                _show_status("✨", f"**Pagina {page.number}** disponibile! Continuiamo l'avventura...")
            last_announced_page = page.number
        else:
            _show_status(
                "🎨",
                f"Pagina {page.number} · vignetta {panel.number} di {panels_per_page[page.number]}...",
            )
        try:
            prompt = _build_kids_panel_prompt(
                panel, cast_block_for_panel, style_preset_id, scene,
            )
            # Reference temp files
            tmp_refs = []
            for name in names:
                rk = char_storage_keys.get(name)
                if rk and object_exists(rk):
                    data = download_bytes(rk)
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp.write(data)
                    tmp.close()
                    tmp_refs.append(Path(tmp.name))

            with session_scope() as s:
                fresh_user = users_repo.get_by_id(s, _user.id)
                credits_repo.charge(
                    s, fresh_user,
                    cost=cost_for_operation("generate_panel", quality="medium"),
                    operation=CreditOperation.generate_panel,
                    reason=f"KIDS vignetta p{page.number}v{panel.number}",
                )

            image_bytes = generator._generate_bytes(
                prompt=prompt,
                size="1024x1024",
                reference_images=tmp_refs if tmp_refs else None,
                quality="medium",
            )

            vk = vignette_key(project_id_local, page.number, panel.number)
            upload_bytes(vk, image_bytes, content_type="image/png")

            with session_scope() as s:
                project = projects_repo.get_by_id(s, project_id_local)
                vignettes_repo.upsert(
                    s, project=project,
                    page_number=page.number, panel_number=panel.number,
                    storage_key=vk,
                    prompt_hash=_hash_prompt(prompt),
                    quality="medium",
                    aspect_ratio_key="1_1",
                    provider="openai",
                    model="gpt-image-2",
                )

            # Aggiungi alla galleria con messaggio simpatico
            funny_messages = [
                f"🎨 Pagina {page.number} · vignetta {panel.number}: ecco fatta!",
                f"✏️ Vignetta {panel.number} di pagina {page.number} dipinta!",
                f"📖 Pagina {page.number} · vignetta {panel.number} appena uscita dal forno!",
                f"🌈 Ecco vignetta {panel.number} di pagina {page.number}!",
                f"🪄 Vignetta {panel.number} disegnata!",
            ]
            msg = funny_messages[panel_idx % len(funny_messages)]
            _add_to_gallery(image_bytes, label=f"P{page.number}V{panel.number}", message=msg)

            # Cleanup
            for p in tmp_refs:
                try:
                    p.unlink()
                except OSError:
                    pass

        except Exception as e:
            st.warning(f"Vignetta {panel_idx+1} fallita: {e}")
            with session_scope() as s:
                fresh_user = users_repo.get_by_id(s, _user.id)
                credits_repo.refund(
                    s, fresh_user,
                    amount=cost_for_operation("generate_panel", quality="medium"),
                    reason=f"Refund kids panel: {e}",
                )

    _show_status("🎉", "**Il tuo libretto è pronto!** Andiamo a vederlo tutto insieme...")
    st.balloons()
    time.sleep(2.5)
    _set_step(6)
    st.rerun()


# ============================================================
# STEP 6 — Anteprima + esporta + rigenera singole vignette/cover
# ============================================================


def _regenerate_single_panel(
    project_id: uuid.UUID,
    page_number: int,
    panel_number: int,
) -> tuple[bool, str | None]:
    """Rigenera UNA vignetta. Usa stessi dati del progetto."""
    from snaptoon_core.generator import OpenAIImageGenerator

    cost = cost_for_operation("generate_panel", quality="medium")

    # Carica context dal DB
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None or project.script is None:
            return False, "Progetto non trovato."

        pyd_script_db = scripts_repo.load_pydantic(project.script)
        panel = None
        for pg in pyd_script_db.pages:
            if pg.number == page_number:
                for p in pg.panels:
                    if p.number == panel_number:
                        panel = p
                        break
                break
        if panel is None:
            return False, "Vignetta non trovata."

        style_id = project.style_id
        cast = []
        for cs in project.character_sheets:
            ref = next((r for r in cs.references if r.slot_number == 1), None)
            cast.append({
                "name": cs.name,
                "description": cs.visual_description,
                "ref_key": ref.storage_key if ref else None,
            })

    # Charge
    try:
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.charge(
                s, fresh_user,
                cost=cost,
                operation=CreditOperation.generate_panel,
                reason=f"KIDS rigenera p{page_number}v{panel_number}",
            )
    except InsufficientCreditsError as e:
        return False, f"Crediti insufficienti: servono {e.required}, ne hai {e.available}."

    # Build prompt
    cast_block = [{"name": c["name"], "description": c["description"]} for c in cast]
    scene_params = {
        "shot_distance": panel.shot_distance,
        "shot_angle": panel.shot_angle,
        "mood": panel.mood,
    }
    prompt = _build_kids_panel_prompt(panel, cast_block, style_id, scene_params)

    # Download reference temp
    tmp_refs = []
    try:
        for c in cast:
            rk = c.get("ref_key")
            if rk and object_exists(rk):
                data = download_bytes(rk)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(data)
                tmp.close()
                tmp_refs.append(Path(tmp.name))

        generator = OpenAIImageGenerator()
        image_bytes = generator._generate_bytes(
            prompt=prompt,
            size="1024x1024",
            reference_images=tmp_refs if tmp_refs else None,
            quality="medium",
        )

        vk = vignette_key(project_id, page_number, panel_number)
        upload_bytes(vk, image_bytes, content_type="image/png")

        with session_scope() as s:
            project = projects_repo.get_by_id(s, project_id)
            vignettes_repo.upsert(
                s, project=project,
                page_number=page_number, panel_number=panel_number,
                storage_key=vk,
                prompt_hash=_hash_prompt(prompt, str(time.time())),  # invalida cache
                quality="medium",
                aspect_ratio_key="1_1",
                provider="openai",
                model="gpt-image-2",
            )

    except Exception as e:
        err = str(e)[:300]
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.refund(
                s, fresh_user, amount=cost,
                reason=f"Refund kids regen panel: {err}",
            )
        return False, f"Errore: {err}"
    finally:
        for p in tmp_refs:
            try:
                p.unlink()
            except OSError:
                pass

    return True, None


def _regenerate_cover(project_id: uuid.UUID) -> tuple[bool, str | None]:
    """Rigenera la copertina."""
    from snaptoon_core.generator import OpenAIImageGenerator

    cost = cost_for_operation("generate_panel", quality="medium")

    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None:
            return False, "Progetto non trovato."
        style_id = project.style_id
        title = project.cover.title if project.cover else project.name
        cast = []
        for cs in project.character_sheets:
            ref = next((r for r in cs.references if r.slot_number == 1), None)
            cast.append({
                "name": cs.name,
                "description": cs.visual_description,
                "ref_key": ref.storage_key if ref else None,
            })

    try:
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.charge(
                s, fresh_user, cost=cost,
                operation=CreditOperation.generate_cover,
                reason=f"KIDS rigenera copertina",
            )
    except InsufficientCreditsError as e:
        return False, f"Crediti insufficienti: servono {e.required}, ne hai {e.available}."

    cast_block = [{"name": c["name"], "description": c["description"]} for c in cast]
    prompt = _build_kids_cover_prompt(title, cast_block, style_id)

    tmp_refs = []
    try:
        for c in cast:
            rk = c.get("ref_key")
            if rk and object_exists(rk):
                data = download_bytes(rk)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(data)
                tmp.close()
                tmp_refs.append(Path(tmp.name))

        generator = OpenAIImageGenerator()
        image_bytes = generator._generate_bytes(
            prompt=prompt,
            size="1024x1536",
            reference_images=tmp_refs if tmp_refs else None,
            quality="medium",
        )

        cover_key = cover_illustration_key(project_id)
        upload_bytes(cover_key, image_bytes, content_type="image/png")

        with session_scope() as s:
            project = projects_repo.get_by_id(s, project_id)
            cover_orm = covers_repo.get_or_create(s, project)
            covers_repo.update_illustration_key(s, cover_orm, cover_key)
    except Exception as e:
        err = str(e)[:300]
        with session_scope() as s:
            fresh_user = users_repo.get_by_id(s, _user.id)
            credits_repo.refund(
                s, fresh_user, amount=cost,
                reason=f"Refund kids regen cover: {err}",
            )
        return False, f"Errore: {err}"
    finally:
        for p in tmp_refs:
            try:
                p.unlink()
            except OSError:
                pass

    return True, None


def _render_step_6() -> None:
    st.markdown("### Step 6 — Il tuo fumetto è pronto!")

    project_id_raw = st.session_state.get(SK_PROJECT_ID)
    if not project_id_raw:
        st.error("Nessun progetto generato.")
        return

    project_id = uuid.UUID(project_id_raw) if isinstance(project_id_raw, str) else project_id_raw

    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None:
            st.error("Progetto non trovato.")
            return
        proj_name = project.name
        pyd_script_db = scripts_repo.load_pydantic(project.script)
        flat_panels = [(p.number, panel) for p in pyd_script_db.pages for panel in p.panels]
        vigs = vignettes_repo.list_for_project(s, project)
        vig_keys = {(v.page_number, v.panel_number): v.storage_key for v in vigs}
        grids_by_page = {pl.page_number: pl.grid_id for pl in project.page_layouts}

    st.caption(f"Progetto: **{proj_name}**")
    st.markdown(f"_{pyd_script_db.logline}_")

    # Bottoni in alto (azioni globali)
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        if st.button("📚 Tutti i libretti", use_container_width=True, key="_step6_back_dash"):
            st.session_state[SK_VIEW] = "dashboard"
            st.session_state.pop(SK_PROJECT_ID, None)
            st.session_state.pop(SK_STEP, None)
            st.rerun()
    with col_t2:
        if st.button("+ Nuovo libretto", use_container_width=True, key="_step6_new"):
            _reset_wizard()
            st.session_state[SK_VIEW] = "wizard"
            _set_step(1)
            st.rerun()
    with col_t3:
        if st.button("📥 Genera PDF", type="primary", use_container_width=True, key="_step6_pdf"):
            _generate_kids_pdf(project_id)

    st.divider()

    # === Copertina con bottone rigenera ===
    st.markdown("#### 📕 Copertina")
    cv_key = cover_illustration_key(project_id)
    col_cv_img, col_cv_btn = st.columns([3, 1])
    with col_cv_img:
        if object_exists(cv_key):
            try:
                data = download_bytes(cv_key)
                st.image(data, width=320)
            except Exception:
                st.warning("Errore lettura copertina.")
        else:
            st.info("Copertina non disponibile.")
    with col_cv_btn:
        cost = cost_for_operation("generate_panel", quality="medium")
        can = _user.credits_remaining >= cost
        if st.button(
            f"🔄 Rigenera copertina\n({cost} cr)",
            key="_kids_regen_cover",
            disabled=not can,
            help=None if can else f"Servono {cost} crediti.",
            use_container_width=True,
        ):
            with st.spinner("Rigenero copertina..."):
                ok, err = _regenerate_cover(project_id)
            if ok:
                st.toast("Copertina rigenerata!", icon="📕")
                st.rerun()
            else:
                st.error(err)

    st.divider()
    st.markdown(f"#### 🖼 Vignette ({len(flat_panels)})")

    # Grid vignette con bottone rigenera per ciascuna
    cols_per_row = 4
    for row_start in range(0, len(flat_panels), cols_per_row):
        row = flat_panels[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (page_num, panel) in zip(cols, row):
            with col:
                with st.container(border=True):
                    key = (page_num, panel.number)
                    if key in vig_keys:
                        try:
                            data = download_bytes(vig_keys[key])
                            st.image(data, use_container_width=True)
                        except Exception:
                            st.warning("Errore")
                    else:
                        st.caption("Non generata")
                    st.caption(f"P{page_num}V{panel.number}")

                    cost = cost_for_operation("generate_panel", quality="medium")
                    can = _user.credits_remaining >= cost
                    if st.button(
                        f"🔄 Rigenera ({cost})",
                        key=f"_regen_p{page_num}v{panel.number}",
                        disabled=not can,
                        use_container_width=True,
                    ):
                        with st.spinner(f"Rigenero P{page_num}V{panel.number}..."):
                            ok, err = _regenerate_single_panel(project_id, page_num, panel.number)
                        if ok:
                            st.toast(f"P{page_num}V{panel.number} rigenerata!", icon="🎨")
                            st.rerun()
                        else:
                            st.error(err)


def _generate_kids_pdf(project_id: uuid.UUID) -> None:
    """Renderizza tutte le pagine + export PDF."""
    with st.spinner("Renderizzo il PDF..."):
        with session_scope() as s:
            project = projects_repo.get_by_id(s, project_id)
            if project is None:
                st.error("Progetto non trovato.")
                return
            project_slug = project.slug
            pyd_script_db = scripts_repo.load_pydantic(project.script)
            grids_by_page = {pl.page_number: pl.grid_id for pl in project.page_layouts}

        # Renderizza ogni pagina
        temp_files: list[Path] = []
        page_temp_paths: list[Path] = []

        try:
            for page in pyd_script_db.pages:
                grid_id = grids_by_page.get(page.number, "2x2")
                grid = GRIDS.get(grid_id)
                if grid is None:
                    continue

                # Scarica vignette
                panel_paths = []
                for panel in page.panels:
                    vk = vignette_key(project_id, page.number, panel.number)
                    if object_exists(vk):
                        data = download_bytes(vk)
                        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        tmp.write(data)
                        tmp.close()
                        p = Path(tmp.name)
                        temp_files.append(p)
                        panel_paths.append((panel, p))
                    else:
                        panel_paths.append((panel, None))

                # Render pagina (i balloon sono GIÀ nelle vignette generate AI-bake)
                out_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                out_tmp.close()
                out_path = Path(out_tmp.name)
                temp_files.append(out_path)
                render_page(
                    panels_with_images=panel_paths,
                    grid=grid,
                    out_path=out_path,
                    show_balloons=False,  # NO overlay PIL: i balloon sono nelle immagini
                )
                # Upload page render in storage (per cache)
                with open(out_path, "rb") as f:
                    upload_bytes(page_render_key(project_id, page.number),
                                 f.read(), content_type="image/png")
                page_temp_paths.append(out_path)

            # Export PDF
            pdf_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            pdf_tmp.close()
            pdf_path = Path(pdf_tmp.name)
            temp_files.append(pdf_path)
            export_pdf(page_temp_paths, pdf_path)

            pdf_bytes = pdf_path.read_bytes()
            st.session_state["_kids_pdf_bytes"] = pdf_bytes
            st.session_state["_kids_pdf_filename"] = f"snaptoon_kids_{project_slug}.pdf"
            st.success("PDF pronto.")
        finally:
            for tp in temp_files:
                try:
                    tp.unlink()
                except OSError:
                    pass

    # Download button
    if "_kids_pdf_bytes" in st.session_state:
        st.download_button(
            label="⬇️ Scarica PDF",
            data=st.session_state["_kids_pdf_bytes"],
            file_name=st.session_state["_kids_pdf_filename"],
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )


# ============================================================
# Router
# ============================================================

if current_view == "dashboard":
    _render_dashboard()
elif current_view == "wizard":
    if step == 1:
        _render_step_1()
    elif step == 2:
        _render_step_2()
    elif step == 3:
        _render_step_3()
    elif step == 4:
        _render_step_4_storia()
    elif step == 5:
        _render_step_5()
    elif step == 6:
        _render_step_6()
    else:
        _set_step(1)
        st.rerun()
