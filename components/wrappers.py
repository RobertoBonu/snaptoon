"""
Wrappers Streamlit — pattern ricorrenti di layout.
design: helper per inject CSS, sidebar completa, page setup standard
"""
from __future__ import annotations
from pathlib import Path
import streamlit as st

from components.ui.credit_badge import render_credit_badge
from components.ui.sidebar_nav import render_sidebar_logo, render_sidebar_nav
from components.ui.project_selector import render_project_selector


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

def inject_css() -> None:
    """Inietta il CSS custom nel DOM. Da chiamare in cima a ogni pagina."""
    css_path = Path(__file__).parent.parent / "style" / "custom.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

def setup_page(
    page_title: str = "SnapToon",
    layout: str = "wide",
    initial_sidebar_state: str = "expanded",
) -> None:
    """
    Chiama st.set_page_config con impostazioni standard SnapToon.
    Deve essere la PRIMA istruzione Streamlit della pagina.

    Params:
        page_title:            Titolo tab browser.
        layout:                "wide" o "centered".
        initial_sidebar_state: "expanded" o "collapsed" (per login: "collapsed").
    """
    st.set_page_config(
        page_title=f"{page_title} — SnapToon",
        page_icon="🎨",
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )
    inject_css()


# ---------------------------------------------------------------------------
# Sidebar completa (post-login)
# ---------------------------------------------------------------------------

def render_sidebar(
    current_page: str,
    projects: list[dict] | None = None,
    current_project_slug: str | None = None,
    credit_current: int = 0,
    credit_total: int = 0,
    plan_name: str = "—",
    is_admin: bool = False,
) -> str | None:
    """
    Renderizza la sidebar completa con logo, selettore progetto, nav e credit badge.

    Params:
        current_page:          Nome pagina corrente (es. "Genera").
        projects:              Lista dei progetti dell'utente.
        current_project_slug:  Slug del progetto attivo.
        credit_current:        Crediti rimasti.
        credit_total:          Crediti totali.
        plan_name:             Nome piano utente.
        is_admin:              True se utente admin.

    Returns:
        Slug del progetto selezionato (può cambiare via dropdown).
    """
    projects = projects or []
    selected_slug = current_project_slug

    with st.sidebar:
        render_sidebar_logo()

        st.markdown("")

        # Selettore progetto
        st.markdown(
            '<div style="padding:0 0.75rem;">',
            unsafe_allow_html=True,
        )
        selected_slug = render_project_selector(
            current_project_slug=current_project_slug,
            projects=projects,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<hr style='border-color:#1E2436;margin:.75rem 0;'>",
            unsafe_allow_html=True,
        )

        # Navigazione
        render_sidebar_nav(current_page=current_page, is_admin=is_admin)

        st.markdown(
            "<hr style='border-color:#1E2436;margin:.75rem 0;'>",
            unsafe_allow_html=True,
        )

        # Credit badge
        clicked = render_credit_badge(
            current=credit_current,
            total=credit_total,
            plan_name=plan_name,
        )
        if clicked:
            st.switch_page("pages/crediti.py")

        st.markdown("")

        # Logout
        if st.button("🚪 Esci", key="_ui_sidebar_logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("Login.py")

    return selected_slug


# ---------------------------------------------------------------------------
# Status bar globale (es. "12/24 vignette generate")
# ---------------------------------------------------------------------------

def render_status_bar(label: str, current: int, total: int) -> None:
    """
    Barra di stato in cima alla pagina con conteggio X/Y.

    Params:
        label:   Etichetta (es. "vignette generate").
        current: Numero corrente.
        total:   Totale.
    """
    pct = int(current / total * 100) if total > 0 else 0
    color = "#EF4444" if current == 0 else ("#F59E0B" if current < total else "#10B981")

    st.markdown(
        f"""
        <div class="snaptoon-status-bar">
          <span class="snaptoon-status-bar__count"
                style="color:{color};">{current}/{total}</span>
          <span>{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(pct / 100)


# ---------------------------------------------------------------------------
# Section label (titolo sezione dentro una pagina)
# ---------------------------------------------------------------------------

def render_section_label(label: str) -> None:
    """Titolo sezione uppercase con separatore inferiore."""
    st.markdown(
        f'<div class="snaptoon-section-label">{label}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Modale "Nuovo progetto" (expander simulato)
# ---------------------------------------------------------------------------

def render_new_project_modal() -> tuple[str, str, bool]:
    """
    Renderizza il form "Nuovo progetto" in un container con bordo.

    Returns:
        (title, length, submitted) — dati del form.
    """
    length_options = {
        "Striscia (1-2 pagine)": "striscia",
        "Breve (3-6 pagine)": "breve",
        "Medio (8-16 pagine)": "medio",
        "Lungo (24+ pagine)": "lungo",
    }

    with st.container(border=True):
        st.subheader("Nuovo progetto")

        with st.form("snaptoon_new_project_form"):
            title = st.text_input(
                "Titolo del fumetto",
                placeholder="Es. La notte del riccio",
                max_chars=120,
            )
            length_label = st.radio(
                "Lunghezza",
                options=list(length_options.keys()),
                index=2,
            )
            submitted = st.form_submit_button(
                "Crea progetto",
                type="primary",
                use_container_width=True,
            )

        error = st.session_state.get("_ui_new_project_error")
        if error:
            st.error(error)

    length_slug = length_options.get(length_label, "medio")
    return title, length_slug, submitted


# ---------------------------------------------------------------------------
# Modale crediti finiti (expander bloccante)
# ---------------------------------------------------------------------------

def render_credits_exhausted_modal() -> tuple[bool, bool]:
    """
    Renderizza la modale "Crediti esauriti".

    Returns:
        (see_plans_clicked, close_clicked)
    """
    with st.container(border=True):
        st.markdown(
            '<div style="text-align:center;padding:1rem 0;">',
            unsafe_allow_html=True,
        )
        st.markdown("### Crediti esauriti.")
        plan = st.session_state.get("user_plan", "attuale")
        st.markdown(
            f"Hai usato tutti i crediti del tuo piano **{plan}**. "
            "Per continuare a generare, passa a un piano superiore o contatta l'amministratore."
        )
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            see_plans = st.button(
                "Vedi piani",
                key="_ui_credits_modal_plans",
                type="primary",
                use_container_width=True,
            )
        with col2:
            close = st.button(
                "Chiudi",
                key="_ui_credits_modal_close",
                use_container_width=True,
            )

    return see_plans, close
