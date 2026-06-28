"""SnapToon — pagina 📝 Testo.

Caricamento testo sorgente e adattamento in sceneggiatura via Claude.

Flusso:
  1. Utente carica .txt o incolla testo nel textarea
  2. Salva sorgente
  3. Click "Adatta a sceneggiatura" → costo crediti → Claude → script JSON
  4. Tab Sceneggiatura: editor (logline, personaggi, pagine, vignette)
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

# Page setup PRIMA di qualsiasi altra import Streamlit-related
st.set_page_config(
    page_title="Testo — SnapToon",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "style" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


_inject_css()

# ============================================================
# Auth + project resolution
# ============================================================
import app_state as appstate
from auth import current_user, logout
from billing.credits import InsufficientCreditsError
from billing.plans import cost_for_operation, plan_config
from db.models import CreditOperation, LengthTarget
from db.repos import characters as characters_repo
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import usage as usage_repo
from db.session import session_scope
from snaptoon_core.models import Script as PydScript
from snaptoon_core.script import adapt_text_to_script

# Gate: serve essere loggati
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


# Gate: serve un progetto attivo
_current_slug = appstate.get_current_project_slug()
if _current_slug is None:
    st.title("📝 Testo")
    st.error("Nessun progetto attivo.")
    st.info("Apri un progetto dalla **home** o creane uno nuovo.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


# ============================================================
# Helper: lookup progetto + render sidebar
# ============================================================


def _render_sidebar(user, project_name: str, plan_label: str, credits_left: int, credits_total: int) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="snaptoon-sidebar-logo">
              <span class="snaptoon-sidebar-logo__wordmark">
                SnapToon<span class="snaptoon-sidebar-logo__dot"></span>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(user.email)
        st.caption(f"Piano: **{plan_label}** · {credits_left}/{credits_total} crediti")
        st.divider()
        st.markdown(f"**Progetto attivo:**")
        st.markdown(f"_{project_name}_")
        st.divider()
        if st.button("🚪 Esci", key="_sb_logout_testo", use_container_width=True):
            with session_scope() as s:
                logout(s)
            appstate.clear_session_keys()
            st.switch_page("app.py")


# ============================================================
# TAB 1 — Sorgente
# ============================================================


def _render_tab_sorgente(project_id, source_text: str, user) -> None:
    st.markdown("### Carica il testo del fumetto")
    st.caption(
        "Carica un file `.txt` o incolla il testo direttamente. "
        "Sarà adattato da Claude in sceneggiatura strutturata."
    )

    # File uploader
    uploaded = st.file_uploader(
        "📤 Carica file (.txt, max 1 MB)",
        type=["txt"],
        key="_textarea_upload",
    )
    if uploaded is not None:
        try:
            content = uploaded.read().decode("utf-8")
            if len(content) > 1_000_000:
                st.error("Il file supera 1 MB. Riduci o spezzalo prima del caricamento.")
            else:
                with session_scope() as s:
                    project = projects_repo.get_by_id(s, project_id)
                    if project is not None:
                        projects_repo.set_source_text(s, project, content)
                st.success("Sorgente caricato dal file.")
                st.rerun()
        except UnicodeDecodeError:
            st.error("Il file non sembra essere testo UTF-8 valido.")

    # Textarea paste
    text_area_key = "_textarea_source"
    new_text = st.text_area(
        "Oppure incolla il testo",
        value=source_text,
        height=300,
        placeholder="Incolla qui il tuo testo (racconto, idea, scena, dialogo)...",
        key=text_area_key,
    )

    col_save, col_count = st.columns([1, 4])
    with col_save:
        if st.button("💾 Salva sorgente", type="secondary", use_container_width=True,
                     disabled=(new_text == source_text)):
            with session_scope() as s:
                project = projects_repo.get_by_id(s, project_id)
                if project is not None:
                    projects_repo.set_source_text(s, project, new_text)
            st.success("Sorgente salvato.")
            st.rerun()
    with col_count:
        words = len(new_text.split()) if new_text else 0
        chars = len(new_text)
        st.caption(f"_{words} parole · {chars} caratteri_")

    st.divider()

    # ============================================================
    # Adatta a sceneggiatura
    # ============================================================
    st.markdown("### Adatta a sceneggiatura")

    # Cost preview
    cost = cost_for_operation("adapt_script")
    remaining_after = user.credits_remaining - cost

    if not new_text.strip():
        st.info("Carica o incolla un testo per poter adattare.")
        return

    color = "#EF4444" if remaining_after < 0 else "#94A3B8"
    st.markdown(
        f'<p style="color:{color};">Costa <b>{cost} crediti</b>. '
        f'Saldo dopo: <b>{remaining_after}</b>.</p>',
        unsafe_allow_html=True,
    )

    can_adapt = (
        new_text == source_text  # è salvato
        and source_text.strip()
        and remaining_after >= 0
    )
    button_help = None
    if new_text != source_text:
        button_help = "Salva prima il sorgente"
    elif remaining_after < 0:
        button_help = "Crediti insufficienti"

    if st.button(
        "🪄 Adatta a sceneggiatura",
        type="primary",
        disabled=not can_adapt,
        help=button_help,
    ):
        _execute_adapt_script(project_id, source_text, user)


def _execute_adapt_script(project_id, source_text: str, user) -> None:
    """Esegue l'adattamento: charge crediti + chiamata Claude + salva script + usage log."""
    import time

    t0 = time.time()
    error_msg: str | None = None
    success = False

    with st.spinner("Sto adattando il testo in sceneggiatura..."):
        try:
            with session_scope() as s:
                # Re-fetch user nella stessa session per atomicità
                from db.repos import users as users_repo
                user_db = users_repo.get_by_id(s, user.id)
                if user_db is None:
                    st.error("Utente non trovato.")
                    return

                project = projects_repo.get_by_id(s, project_id)
                if project is None:
                    st.error("Progetto non trovato.")
                    return

                # Charge crediti — solleva se insufficient
                cost = cost_for_operation("adapt_script")
                credits_repo.charge(
                    s,
                    user_db,
                    cost=cost,
                    operation=CreditOperation.adapt_script,
                    reason=f"Adattamento script per progetto «{project.name}»",
                    reference_id=str(project.id),
                )

                # Chiama Claude
                length_target = project.length_target.value
                pyd_script = adapt_text_to_script(
                    title=project.name,
                    length_target=length_target,
                    source_text=source_text,
                )

                # Salva script
                orm_script = scripts_repo.get_or_create(s, project)
                scripts_repo.save_pydantic(s, orm_script, pyd_script)

                # Importa anche character_sheets se assenti (auto-bootstrap del cast)
                existing_names = {cs.name.lower() for cs in project.character_sheets}
                for ch in pyd_script.characters:
                    if ch.name.lower() not in existing_names:
                        characters_repo.create_character(
                            s,
                            project=project,
                            name=ch.name,
                            visual_description=ch.visual_bible,
                            color_palette="",
                        )

                # Usage log
                latency = int((time.time() - t0) * 1000)
                usage_repo.log_operation(
                    s,
                    user=user_db,
                    operation="adapt_script",
                    credits_spent=cost,
                    success=True,
                    latency_ms=latency,
                    project_id=project.id,
                )

                success = True

        except InsufficientCreditsError as e:
            error_msg = f"Crediti insufficienti: ti servono {e.required}, ne hai {e.available}."
        except Exception as e:
            error_msg = f"Errore durante l'adattamento: {e}"

            # Refund su errore generico (chiamata Claude fallita dopo charge)
            try:
                with session_scope() as s:
                    from db.repos import users as users_repo
                    user_db = users_repo.get_by_id(s, user.id)
                    if user_db is not None:
                        credits_repo.refund(
                            s,
                            user_db,
                            amount=cost_for_operation("adapt_script"),
                            reason=f"Refund per adapt_script fallito: {e}",
                        )
                        latency = int((time.time() - t0) * 1000)
                        usage_repo.log_operation(
                            s,
                            user=user_db,
                            operation="adapt_script",
                            credits_spent=0,
                            success=False,
                            error_message=str(e)[:500],
                            latency_ms=latency,
                            project_id=project_id,
                        )
            except Exception:
                pass

    if error_msg:
        st.error(error_msg)
    elif success:
        st.success("Sceneggiatura generata. Apri la tab **Sceneggiatura** per rivederla.")
        st.balloons()
        st.rerun()


# ============================================================
# TAB 2 — Sceneggiatura
# ============================================================


def _render_tab_sceneggiatura(project_id) -> None:
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None or project.script is None or not project.script.payload.get("pages"):
            st.info(
                "Nessuna sceneggiatura ancora. Carica un testo nella tab **Sorgente** "
                "e clicca **Adatta a sceneggiatura**."
            )
            return
        pyd_script = scripts_repo.load_pydantic(project.script)

    # ============================================================
    # Logline
    # ============================================================
    st.markdown("### Logline")
    new_logline = st.text_area(
        "Sintesi della storia in 1-2 righe",
        value=pyd_script.logline,
        height=80,
        key="_script_logline",
        label_visibility="collapsed",
    )

    if new_logline != pyd_script.logline:
        if st.button("💾 Salva logline", key="_save_logline", type="secondary"):
            pyd_script.logline = new_logline
            with session_scope() as s:
                project = projects_repo.get_by_id(s, project_id)
                if project is not None:
                    orm_script = scripts_repo.get_or_create(s, project)
                    scripts_repo.save_pydantic(s, orm_script, pyd_script)
            st.success("Logline salvata.")
            st.rerun()

    st.divider()

    # ============================================================
    # Personaggi
    # ============================================================
    st.markdown(f"### Personaggi ({len(pyd_script.characters)})")
    if not pyd_script.characters:
        st.caption("_Nessun personaggio nella sceneggiatura._")
    else:
        for idx, ch in enumerate(pyd_script.characters):
            with st.expander(f"👤 **{ch.name}**", expanded=False):
                st.markdown(f"**Bibbia visiva:**")
                st.write(ch.visual_bible or "_(non specificata)_")
                if ch.voice:
                    st.markdown("**Voce:**")
                    st.write(ch.voice)

    st.divider()

    # ============================================================
    # Pagine + vignette
    # ============================================================
    n_pages = len(pyd_script.pages)
    n_panels = sum(len(p.panels) for p in pyd_script.pages)
    n_dialogues = sum(
        len(panel.dialogues) for page in pyd_script.pages for panel in page.panels
    )
    st.markdown(f"### Pagine ({n_pages} pagine · {n_panels} vignette · {n_dialogues} dialoghi)")

    for page in pyd_script.pages:
        with st.expander(f"📖 Pagina {page.number} — {len(page.panels)} vignette", expanded=False):
            for panel in page.panels:
                st.markdown(f"**Vignetta {panel.number}**")
                st.caption(panel.description)
                if panel.dialogues:
                    for dlg in panel.dialogues:
                        speaker = f"**{dlg.speaker}**: " if dlg.speaker else ""
                        kind_emoji = {
                            "FUMETTO": "💬",
                            "PENSIERO": "💭",
                            "DIDASCALIA": "📜",
                            "SFX": "💥",
                        }.get(dlg.kind, "")
                        st.markdown(f"{kind_emoji} {speaker}_{dlg.text}_")
                else:
                    st.caption("_(nessun dialogo)_")
                st.markdown("---")

    st.info(
        "💡 L'editing completo di logline, personaggi, dialoghi e vignette verrà "
        "abilitato nella prossima iterazione. Per ora puoi rigenerare la sceneggiatura "
        "dalla tab **Sorgente** se vuoi cambiare l'output."
    )


# ============================================================
# RENDER
# ============================================================

with session_scope() as _s:
    _project = projects_repo.get_by_slug(_s, _user.id, _current_slug)
    if _project is None:
        # Progetto eliminato o slug stale
        appstate.clear_current_project()
        st.error("Il progetto attivo non esiste più.")
        st.markdown("[← Vai alla home](/)")
        st.stop()
    _project_id = _project.id
    _project_name = _project.name
    _source_text = _project.source_text


_plan_cfg = plan_config(_user.plan)
_render_sidebar(
    _user,
    project_name=_project_name,
    plan_label=_plan_cfg.label,
    credits_left=_user.credits_remaining,
    credits_total=_user.credits_total_this_period,
)

st.title("📝 Testo")
st.caption(f"Progetto: **{_project_name}**")

tab_source, tab_script = st.tabs(["📤 Sorgente", "🎬 Sceneggiatura"])

with tab_source:
    _render_tab_sorgente(_project_id, _source_text, _user)

with tab_script:
    _render_tab_sceneggiatura(_project_id)
