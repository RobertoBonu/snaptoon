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

from app_state.ui import enforce_sidebar_visibility, render_sidebar_nav, show_page_loading
enforce_sidebar_visibility()

# Loading overlay durante gli import (~3s)
_page_loader = show_page_loading("Carico la sceneggiatura...")

# ============================================================
# Auth + project resolution
# ============================================================
import app_state as appstate
from auth import current_user, logout
from billing.plans import cost_for_operation, plan_config
from db.models import CreditOperation, LengthTarget
from db.repos import characters as characters_repo
from db.repos import credits as credits_repo
from db.repos.credits import InsufficientCreditsError
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import usage as usage_repo
from db.repos import users as users_repo
from db.session import session_scope
from snaptoon_core.models import (
    Character,
    Dialogue,
    Page,
    Panel,
    Script as PydScript,
)
from snaptoon_core.script import adapt_text_to_script
from snaptoon_core.soggetto import (
    SoggettoOutput,
    SoggettoState,
    generate_soggetto,
    propose_questions,
    refine_soggetto,
)

# Gate: serve essere loggati
with session_scope() as _s:
    _user = current_user(_s)

# Backend pronto: rimuovi loading overlay
_page_loader.empty()

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
    render_sidebar_nav(user)
    with st.sidebar:
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
# TAB 0 — Soggetto guidato (4 fasi)
# ============================================================

_SG_KEY_SCINTILLA = "_sg_scintilla"
_SG_KEY_QUESTIONS = "_sg_questions"
_SG_KEY_ANSWERS = "_sg_answers"
_SG_KEY_OUTPUT = "_sg_output"
_SG_KEY_PHASE = "_sg_phase"


def _execute_propose_questions(scintilla: str, user) -> tuple[bool, str | None]:
    """Charge crediti + chiama Claude per proporre 7 domande."""
    cost = cost_for_operation("generate_subject")
    with session_scope() as s:
        user_db = users_repo.get_by_id(s, user.id)
        if user_db is None:
            return False, "Utente non trovato."
        try:
            credits_repo.charge(
                s, user_db, cost=cost,
                operation=CreditOperation.generate_subject,
                reason="Propose questions soggetto guidato",
            )
        except InsufficientCreditsError as e:
            return False, f"Crediti insufficienti: servono {e.required}, ne hai {e.available}."

    try:
        questions = propose_questions(scintilla)
        st.session_state[_SG_KEY_QUESTIONS] = [q.model_dump() for q in questions]
        return True, None
    except Exception as e:
        err = str(e)[:500]
        with session_scope() as s:
            user_db = users_repo.get_by_id(s, user.id)
            if user_db is not None:
                credits_repo.refund(s, user_db, amount=cost, reason=f"Refund propose_questions: {err}")
        return False, f"Errore: {err}"


def _execute_generate_soggetto(scintilla: str, answers: dict, length: str, user) -> tuple[bool, str | None]:
    cost = cost_for_operation("generate_subject")
    with session_scope() as s:
        from db.repos import users as users_repo
        user_db = users_repo.get_by_id(s, user.id)
        if user_db is None:
            return False, "Utente non trovato."
        try:
            credits_repo.charge(
                s, user_db, cost=cost,
                operation=CreditOperation.generate_subject,
                reason="Generate soggetto",
            )
        except InsufficientCreditsError as e:
            return False, f"Crediti insufficienti: servono {e.required}, ne hai {e.available}."

    try:
        output = generate_soggetto(scintilla, answers, length)
        st.session_state[_SG_KEY_OUTPUT] = output.model_dump()
        return True, None
    except Exception as e:
        err = str(e)[:500]
        with session_scope() as s:
            from db.repos import users as users_repo
            user_db = users_repo.get_by_id(s, user.id)
            if user_db is not None:
                credits_repo.refund(s, user_db, amount=cost, reason=f"Refund generate_soggetto: {err}")
        return False, f"Errore: {err}"


def _execute_refine_soggetto(current: dict, instruction: str, user) -> tuple[bool, str | None]:
    cost = cost_for_operation("generate_subject")
    with session_scope() as s:
        from db.repos import users as users_repo
        user_db = users_repo.get_by_id(s, user.id)
        if user_db is None:
            return False, "Utente non trovato."
        try:
            credits_repo.charge(
                s, user_db, cost=cost,
                operation=CreditOperation.generate_subject,
                reason="Refine soggetto",
            )
        except InsufficientCreditsError as e:
            return False, f"Crediti insufficienti: servono {e.required}, ne hai {e.available}."

    try:
        new_output = refine_soggetto(SoggettoOutput.model_validate(current), instruction)
        st.session_state[_SG_KEY_OUTPUT] = new_output.model_dump()
        return True, None
    except Exception as e:
        err = str(e)[:500]
        with session_scope() as s:
            from db.repos import users as users_repo
            user_db = users_repo.get_by_id(s, user.id)
            if user_db is not None:
                credits_repo.refund(s, user_db, amount=cost, reason=f"Refund refine: {err}")
        return False, f"Errore: {err}"


def _soggetto_to_source(output: dict) -> str:
    """Trasforma il soggetto in testo sorgente formattato per adapt."""
    parts = []
    if output.get("logline"):
        parts.append(f"LOGLINE\n{output['logline']}")
    if output.get("premise"):
        parts.append(f"\nPREMESSA\n{output['premise']}")
    if output.get("personaggi"):
        parts.append(f"\nPERSONAGGI\n{output['personaggi']}")
    if output.get("sinossi"):
        parts.append(f"\nSINOSSI\n{output['sinossi']}")
    return "\n".join(parts)


def _render_tab_soggetto(project_id, user) -> None:
    st.caption(
        "Workflow guidato in 4 fasi: scrivi una scintilla narrativa, "
        "rispondi alle domande generate da Claude, ricevi un soggetto "
        "strutturato, affinalo per istruzione, infine adottalo come sorgente "
        "per l'adattamento in sceneggiatura."
    )

    phase = st.session_state.get(_SG_KEY_PHASE, 1)
    cost = cost_for_operation("generate_subject")

    # ============================================================
    # FASE 1 — Scintilla
    # ============================================================
    st.markdown("### Fase 1 — Scintilla narrativa")
    scintilla = st.text_area(
        "L'idea iniziale, in 1-3 righe",
        value=st.session_state.get(_SG_KEY_SCINTILLA, ""),
        height=80,
        key="_sg_scintilla_input",
        placeholder="Es. Un uomo solitario entra in un bar di periferia. È l'ultimo a sapere che il mondo finirà tra un'ora.",
    )

    if st.button(
        f"➡️ Proponi domande ({cost} crediti)",
        type="primary",
        disabled=(not scintilla.strip()) or (user.credits_remaining < cost),
        key="_sg_btn_propose",
    ):
        st.session_state[_SG_KEY_SCINTILLA] = scintilla
        with st.spinner("Claude sta proponendo le domande..."):
            success, err = _execute_propose_questions(scintilla, user)
        if success:
            st.session_state[_SG_KEY_PHASE] = 2
            st.rerun()
        else:
            st.error(err)

    questions = st.session_state.get(_SG_KEY_QUESTIONS)
    if not questions:
        return

    st.divider()

    # ============================================================
    # FASE 2 — Domande di sviluppo
    # ============================================================
    st.markdown(f"### Fase 2 — Domande di sviluppo ({len(questions)})")
    st.caption("Rispondi a ogni domanda (lascia vuoto per «decidi tu Claude»).")

    with st.form("_sg_form_answers"):
        answers = {}
        existing_ans = st.session_state.get(_SG_KEY_ANSWERS, {})
        for q in questions:
            st.markdown(f"**{q['label']}**")
            st.caption(q.get("prompt", ""))
            if q.get("suggestion"):
                st.caption(f"💡 _{q['suggestion']}_")
            ans = st.text_area(
                f"La tua risposta",
                value=existing_ans.get(q["key"], ""),
                key=f"_sg_ans_{q['key']}",
                height=70,
                label_visibility="collapsed",
            )
            answers[q["key"]] = ans
            st.markdown("")

        length = st.radio(
            "Lunghezza del soggetto",
            options=["breve", "medio", "lungo"],
            index=1,
            horizontal=True,
        )

        if st.form_submit_button(
            f"🪄 Genera soggetto ({cost} crediti)",
            type="primary",
            use_container_width=True,
        ):
            st.session_state[_SG_KEY_ANSWERS] = answers
            with st.spinner("Claude sta scrivendo il soggetto..."):
                success, err = _execute_generate_soggetto(
                    st.session_state[_SG_KEY_SCINTILLA],
                    answers,
                    length,
                    user,
                )
            if success:
                st.session_state[_SG_KEY_PHASE] = 3
                st.rerun()
            else:
                st.error(err)

    output = st.session_state.get(_SG_KEY_OUTPUT)
    if not output:
        return

    st.divider()

    # ============================================================
    # FASE 3 + 4 — Soggetto + Affina
    # ============================================================
    st.markdown("### Fase 3 — Soggetto generato")
    if output.get("logline"):
        st.markdown("**Logline**")
        st.write(output["logline"])
    if output.get("premise"):
        st.markdown("**Premessa**")
        st.write(output["premise"])
    if output.get("personaggi"):
        st.markdown("**Personaggi**")
        st.write(output["personaggi"])
    if output.get("sinossi"):
        st.markdown("**Sinossi**")
        st.write(output["sinossi"])

    st.divider()
    st.markdown("### Fase 4 — Affina con Claude")
    with st.form("_sg_form_refine"):
        instruction = st.text_area(
            "Istruzione di affinamento",
            placeholder="Es. Rendi più drammatico il finale. Oppure: rendi il protagonista una donna. Oppure: aggiungi un sottotrama romantica.",
            height=100,
        )
        if st.form_submit_button(
            f"🪄 Affina soggetto ({cost} crediti)",
            type="secondary",
            disabled=(user.credits_remaining < cost),
        ):
            if instruction.strip():
                with st.spinner("Claude sta affinando il soggetto..."):
                    success, err = _execute_refine_soggetto(output, instruction, user)
                if success:
                    st.rerun()
                else:
                    st.error(err)
            else:
                st.warning("Inserisci una istruzione.")

    st.divider()
    if st.button(
        "✅ Adotta come sorgente",
        type="primary",
        help="Trasferisce il soggetto come testo sorgente, pronto per l'adattamento in sceneggiatura.",
    ):
        source = _soggetto_to_source(output)
        with session_scope() as s:
            project = projects_repo.get_by_id(s, project_id)
            if project is not None:
                projects_repo.set_source_text(s, project, source)
        st.session_state[_SG_KEY_PHASE] = 1
        st.session_state.pop(_SG_KEY_QUESTIONS, None)
        st.session_state.pop(_SG_KEY_OUTPUT, None)
        st.toast("Soggetto adottato come sorgente. Vai alla tab 📤 Sorgente.", icon="✨")
        st.rerun()


# ============================================================
# TAB 2 — Sceneggiatura (editing completo)
# ============================================================


def _save_script(project_id, pyd_script: PydScript) -> None:
    """Salva l'intero Pydantic Script nel DB JSONB."""
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None:
            return
        orm_script = scripts_repo.get_or_create(s, project)
        scripts_repo.save_pydantic(s, orm_script, pyd_script)


def _renumber_pages(pyd_script: PydScript) -> None:
    """Rinumera pagine 1..N e vignette 1..M dentro ciascuna pagina."""
    for i, page in enumerate(pyd_script.pages, start=1):
        page.number = i
        for j, panel in enumerate(page.panels, start=1):
            panel.number = j


DIALOGUE_KINDS = ["FUMETTO", "PENSIERO", "DIDASCALIA", "SFX"]
KIND_EMOJI = {
    "FUMETTO": "💬",
    "PENSIERO": "💭",
    "DIDASCALIA": "📜",
    "SFX": "💥",
}


def _render_dialogue_editor(
    project_id,
    pyd_script: PydScript,
    page_idx: int,
    panel_idx: int,
    dlg_idx: int,
) -> None:
    """Mini form per editing di un singolo dialogo."""
    dlg = pyd_script.pages[page_idx].panels[panel_idx].dialogues[dlg_idx]
    key_prefix = f"dlg_p{page_idx}_v{panel_idx}_d{dlg_idx}"

    with st.form(f"_form_{key_prefix}", border=True):
        col_kind, col_speaker = st.columns([1, 2])
        with col_kind:
            new_kind = st.selectbox(
                "Tipo",
                options=DIALOGUE_KINDS,
                index=DIALOGUE_KINDS.index(dlg.kind) if dlg.kind in DIALOGUE_KINDS else 0,
                format_func=lambda k: f"{KIND_EMOJI.get(k, '')} {k}",
            )
        with col_speaker:
            new_speaker = st.text_input(
                "Speaker (lascia vuoto se non applicabile)",
                value=dlg.speaker or "",
                placeholder="es. Marco",
            )

        new_text = st.text_area(
            "Testo",
            value=dlg.text,
            height=70,
        )

        col_save, col_del = st.columns(2)
        with col_save:
            save = st.form_submit_button(
                "💾 Salva",
                type="primary",
                use_container_width=True,
            )
        with col_del:
            delete = st.form_submit_button(
                "🗑 Elimina dialogo",
                use_container_width=True,
            )

    if save:
        dlg.kind = new_kind
        dlg.speaker = new_speaker.strip() or None
        dlg.text = new_text
        _save_script(project_id, pyd_script)
        st.toast("Dialogo salvato.", icon="💬")
        st.rerun()

    if delete:
        del pyd_script.pages[page_idx].panels[panel_idx].dialogues[dlg_idx]
        _save_script(project_id, pyd_script)
        st.toast("Dialogo eliminato.")
        st.rerun()


def _render_panel_editor(
    project_id,
    pyd_script: PydScript,
    page_idx: int,
    panel_idx: int,
) -> None:
    """Editor di una singola vignetta."""
    panel = pyd_script.pages[page_idx].panels[panel_idx]

    with st.container(border=True):
        st.markdown(f"**Vignetta {panel.number}**")

        # Form descrizione (separato dai dialoghi per non rerunnare tutto)
        with st.form(f"_form_panel_p{page_idx}_v{panel_idx}", border=False):
            new_desc = st.text_area(
                "Descrizione visiva",
                value=panel.description,
                height=100,
                placeholder="Cosa si vede nella vignetta...",
            )
            col_save_panel, col_del_panel = st.columns([3, 1])
            with col_save_panel:
                save_panel = st.form_submit_button(
                    "💾 Salva descrizione",
                    type="secondary",
                    use_container_width=True,
                )
            with col_del_panel:
                del_panel = st.form_submit_button(
                    "🗑",
                    help="Elimina questa vignetta",
                    use_container_width=True,
                )

        if save_panel:
            panel.description = new_desc
            _save_script(project_id, pyd_script)
            st.toast("Descrizione salvata.", icon="✅")
            st.rerun()
        if del_panel:
            del pyd_script.pages[page_idx].panels[panel_idx]
            _renumber_pages(pyd_script)
            _save_script(project_id, pyd_script)
            st.toast("Vignetta eliminata.")
            st.rerun()

        # Dialoghi
        st.markdown(f"_Dialoghi ({len(panel.dialogues)})_")
        for d_idx, dlg in enumerate(panel.dialogues):
            speaker = f"**{dlg.speaker}**: " if dlg.speaker else ""
            kind_label = KIND_EMOJI.get(dlg.kind, "")
            with st.expander(
                f"{kind_label} {speaker}_{dlg.text[:50]}{'…' if len(dlg.text) > 50 else ''}_",
                expanded=False,
            ):
                _render_dialogue_editor(project_id, pyd_script, page_idx, panel_idx, d_idx)

        # Aggiungi dialogo
        if st.button(
            "+ Aggiungi dialogo",
            key=f"_add_dlg_p{page_idx}_v{panel_idx}",
            use_container_width=True,
        ):
            panel.dialogues.append(Dialogue(kind="FUMETTO", text=""))
            _save_script(project_id, pyd_script)
            st.toast("Dialogo aggiunto.")
            st.rerun()


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
    # Logline (form per save sempre attivo)
    # ============================================================
    st.markdown("### Logline")
    with st.form("_form_logline", border=False):
        new_logline = st.text_area(
            "Sintesi della storia in 1-2 righe",
            value=pyd_script.logline,
            height=80,
            label_visibility="collapsed",
        )
        if st.form_submit_button("💾 Salva logline", type="secondary"):
            if new_logline != pyd_script.logline:
                pyd_script.logline = new_logline
                _save_script(project_id, pyd_script)
                st.toast("Logline salvata.", icon="✅")
                st.rerun()
            else:
                st.info("Nessuna modifica da salvare.")

    st.divider()

    # ============================================================
    # Personaggi (CRUD completo)
    # ============================================================
    st.markdown(f"### Personaggi ({len(pyd_script.characters)})")

    for ch_idx, ch in enumerate(pyd_script.characters):
        with st.expander(f"👤 **{ch.name}**", expanded=False):
            with st.form(f"_form_char_{ch_idx}", border=False):
                new_name = st.text_input("Nome", value=ch.name)
                new_bible = st.text_area(
                    "Bibbia visiva",
                    value=ch.visual_bible,
                    height=100,
                    placeholder="Aspetto, abbigliamento, segni distintivi...",
                )
                new_voice = st.text_area(
                    "Voce / modo di parlare",
                    value=ch.voice,
                    height=70,
                    placeholder="Tono, vocabolario, espressioni ricorrenti...",
                )
                col_save_ch, col_del_ch = st.columns(2)
                with col_save_ch:
                    save_ch = st.form_submit_button(
                        "💾 Salva personaggio",
                        type="secondary",
                        use_container_width=True,
                    )
                with col_del_ch:
                    del_ch = st.form_submit_button(
                        "🗑 Elimina dalla sceneggiatura",
                        use_container_width=True,
                    )

            if save_ch:
                pyd_script.characters[ch_idx].name = new_name.strip() or ch.name
                pyd_script.characters[ch_idx].visual_bible = new_bible
                pyd_script.characters[ch_idx].voice = new_voice
                _save_script(project_id, pyd_script)
                st.toast("Personaggio salvato.", icon="✅")
                st.rerun()
            if del_ch:
                del pyd_script.characters[ch_idx]
                _save_script(project_id, pyd_script)
                st.toast("Personaggio rimosso dalla sceneggiatura.")
                st.warning(
                    "⚠️ Eventuali character sheet con reference image in **👥 Personaggi** "
                    "sono separate e vanno eliminate là."
                )
                st.rerun()

    # Aggiungi personaggio
    with st.expander("➕ Aggiungi personaggio", expanded=False):
        with st.form("_form_add_char", clear_on_submit=True):
            add_name = st.text_input("Nome", placeholder="Es. Marco Riccio")
            add_bible = st.text_area("Bibbia visiva", height=80)
            add_voice = st.text_area("Voce", height=60)
            if st.form_submit_button("Aggiungi", type="primary"):
                if add_name.strip():
                    pyd_script.characters.append(
                        Character(
                            name=add_name.strip(),
                            visual_bible=add_bible,
                            voice=add_voice,
                        )
                    )
                    _save_script(project_id, pyd_script)
                    st.toast(f"Personaggio «{add_name}» aggiunto.", icon="✅")
                    st.rerun()
                else:
                    st.error("Inserisci un nome.")

    st.divider()

    # ============================================================
    # Pagine + vignette + dialoghi
    # ============================================================
    n_pages = len(pyd_script.pages)
    n_panels = sum(len(p.panels) for p in pyd_script.pages)
    n_dlg = sum(len(panel.dialogues) for page in pyd_script.pages for panel in page.panels)
    st.markdown(f"### Pagine ({n_pages} pagine · {n_panels} vignette · {n_dlg} dialoghi)")

    for page_idx, page in enumerate(pyd_script.pages):
        with st.expander(
            f"📖 Pagina {page.number} — {len(page.panels)} vignette",
            expanded=False,
        ):
            for panel_idx, panel in enumerate(page.panels):
                _render_panel_editor(project_id, pyd_script, page_idx, panel_idx)

            # Aggiungi vignetta
            col_add_pn, col_del_pg = st.columns(2)
            with col_add_pn:
                if st.button(
                    "+ Aggiungi vignetta",
                    key=f"_add_pn_p{page_idx}",
                    use_container_width=True,
                ):
                    new_pn_number = len(page.panels) + 1
                    page.panels.append(
                        Panel(number=new_pn_number, description="")
                    )
                    _save_script(project_id, pyd_script)
                    st.toast(f"Vignetta {new_pn_number} aggiunta.")
                    st.rerun()
            with col_del_pg:
                if st.button(
                    "🗑 Elimina pagina",
                    key=f"_del_pg_p{page_idx}",
                    use_container_width=True,
                    help="Cancella questa pagina e tutte le vignette dentro",
                ):
                    del pyd_script.pages[page_idx]
                    _renumber_pages(pyd_script)
                    _save_script(project_id, pyd_script)
                    st.toast("Pagina eliminata.")
                    st.rerun()

    # Aggiungi pagina globale
    if st.button("+ Aggiungi pagina", type="primary", use_container_width=True):
        new_pg_number = len(pyd_script.pages) + 1
        pyd_script.pages.append(Page(number=new_pg_number))
        _save_script(project_id, pyd_script)
        st.toast(f"Pagina {new_pg_number} aggiunta.")
        st.rerun()


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

tab_soggetto, tab_source, tab_script = st.tabs([
    "💡 Soggetto guidato",
    "📤 Sorgente",
    "🎬 Sceneggiatura",
])

with tab_soggetto:
    _render_tab_soggetto(_project_id, _user)

with tab_source:
    _render_tab_sorgente(_project_id, _source_text, _user)

with tab_script:
    _render_tab_sceneggiatura(_project_id)
