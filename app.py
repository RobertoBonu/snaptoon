"""SnapToon — entry point Streamlit.

Lancia con:  streamlit run app.py

Questo è il file principale dell'app. La logica di autenticazione, sessione,
e caricamento del progetto attivo vive qui. Le pagine specifiche sono in
`pages/`.

REPLIT_AGENT: puoi modificare lo strato visivo (markup, layout, header),
NON la logica delle funzioni auth (login, current_user, ...) che vivono in
`auth/`. Vedi docs/design/07_REPLIT_AGENT.md.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from auth import current_user, hash_password, login, logout
from db.models import LengthTarget, User
from db.repos import projects as projects_repo
from db.repos import users as users_repo
from db.session import session_scope
from billing.plans import plan_config, project_limit_reached
import app_state as appstate

st.set_page_config(
    page_title="SnapToon",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS design system
# ============================================================
def _inject_css() -> None:
    css_path = Path("style/custom.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def _hide_sidebar() -> None:
    """Le schermate di accesso non hanno sidebar (vedi brief 00_Login).

    !important serve a vincere su qualsiasi CSS iniettato in pagina
    (es. enforce_sidebar_visibility quando entriamo loggati e poi
    facciamo logout: il CSS precedente potrebbe persistere brevemente).
    """
    st.markdown(
        """<style>
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )


_inject_css()
# NB: enforce_sidebar_visibility() NON viene chiamato qui — verrebbe
# applicato anche alla schermata di login, dove vincerebbe con !important
# sul _hide_sidebar() facendo lampeggiare la sidebar. Lo invochiamo solo
# DOPO il check auth, quando sappiamo che l'utente è loggato.
from app_state.ui import enforce_sidebar_visibility


# ============================================================
# Schermate di autenticazione
# ============================================================
def _render_login() -> None:
    """Form di accesso. NON tocca la logica auth: la richiama soltanto."""
    from components.ui.login_form import render_login_form

    _hide_sidebar()
    email, password, submitted = render_login_form()

    if submitted:
        st.session_state.pop("_ui_login_error", None)
        with session_scope() as s:
            user = login(s, email=email, password=password)
        if user is None:
            st.session_state["_ui_login_error"] = "Credenziali non valide."
        st.rerun()


def _render_change_password() -> None:
    """Cambio password obbligatorio al primo accesso."""
    from components.ui.login_form import render_change_password_form

    _hide_sidebar()
    new_pwd, confirm_pwd, submitted = render_change_password_form()

    if submitted:
        st.session_state.pop("_ui_pwd_error", None)
        if len(new_pwd) < 8:
            st.session_state["_ui_pwd_error"] = (
                "La password deve essere lunga almeno 8 caratteri."
            )
        elif new_pwd != confirm_pwd:
            st.session_state["_ui_pwd_error"] = "Le due password non coincidono."
        else:
            with session_scope() as s:
                user = current_user(s)
                if user is not None:
                    users_repo.set_password_hash(s, user, hash_password(new_pwd))
        st.rerun()


# ============================================================
# Home autenticata — Project list
# ============================================================
def _list_user_projects(user: User) -> list[dict]:
    """Restituisce la lista progetti dell'utente come dict per i componenti UI."""
    with session_scope() as s:
        projects = projects_repo.list_by_owner(s, user.id)
        return [
            {
                "slug": p.slug,
                "title": p.name,
                "length_target": p.length_target.value,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "style_id": p.style_id,
            }
            for p in projects
        ]


def _create_new_project(user: User, title: str, length: str) -> str | None:
    """Crea un nuovo progetto. Ritorna lo slug, o None se errore (salvato in session_state)."""
    title = title.strip()
    if not title:
        st.session_state[appstate.KEY_NEW_PROJECT_ERROR] = "Inserisci un titolo."
        return None

    with session_scope() as s:
        # Pre-check: limite progetti per piano
        current_count = projects_repo.count_by_owner(s, user.id)
        if project_limit_reached(user.plan, current_count):
            cfg = plan_config(user.plan)
            st.session_state[appstate.KEY_NEW_PROJECT_ERROR] = (
                f"Hai raggiunto il limite del tuo piano ({cfg.max_projects} progetti). "
                "Elimina un progetto o passa a un piano superiore."
            )
            return None

        try:
            length_target = LengthTarget(length)
        except ValueError:
            length_target = LengthTarget.medio

        try:
            project = projects_repo.create_project(
                s, owner=user, name=title, length_target=length_target
            )
            return project.slug
        except ValueError as e:
            st.session_state[appstate.KEY_NEW_PROJECT_ERROR] = str(e)
            return None


def _delete_project_by_slug(user: User, slug: str) -> None:
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user.id, slug)
        if project is not None:
            projects_repo.soft_delete(s, project)
    # Se era il progetto attivo, pulisci
    if appstate.get_current_project_slug() == slug:
        appstate.clear_current_project()


def _duplicate_project_by_slug(user: User, slug: str, new_name: str) -> str | None:
    with session_scope() as s:
        source = projects_repo.get_by_slug(s, user.id, slug)
        if source is None:
            return None
        # Check limite
        current_count = projects_repo.count_by_owner(s, user.id)
        if project_limit_reached(user.plan, current_count):
            cfg = plan_config(user.plan)
            st.error(
                f"Hai raggiunto il limite del tuo piano ({cfg.max_projects} progetti). "
                "Elimina un progetto prima di duplicare."
            )
            return None
        dup = projects_repo.duplicate_project(s, source, new_name)
        return dup.slug


def _render_sidebar_minimal(user: User) -> None:
    """Sidebar della home: nuovo progetto + esci. Niente nav verso pages
    (l'utente naviga via i link sidebar nativi di Streamlit). Email/ruolo/crediti
    NON ridondanti — sono già nel main content della home + Account page."""
    with st.sidebar:
        if st.button("+ Nuovo progetto", key="_sb_new_proj", use_container_width=True, type="primary"):
            st.session_state[appstate.KEY_SHOW_NEW_PROJECT_MODAL] = True
            st.rerun()
        st.divider()
        if st.button("🚪 Esci", key="_sb_logout", use_container_width=True):
            with session_scope() as s:
                logout(s)
            appstate.clear_session_keys()
            st.rerun()


def _render_project_card(project: dict, user: User) -> None:
    """Card di un singolo progetto nella grid."""
    length_labels = {
        "striscia": "Striscia",
        "breve": "Breve",
        "medio": "Medio",
        "lungo": "Lungo",
    }
    length_label = length_labels.get(project["length_target"], project["length_target"])
    created = project["created_at"].strftime("%d/%m/%Y") if project.get("created_at") else "—"

    with st.container(border=True):
        st.markdown(f"### {project['title']}")
        st.caption(f"{length_label} · Creato il {created}")
        st.caption(f"_slug: `{project['slug']}`_")

        col_open, col_dup, col_del = st.columns([2, 1, 1])
        with col_open:
            if st.button("Apri →", key=f"open_{project['slug']}", type="primary", use_container_width=True):
                appstate.set_current_project_slug(project["slug"])
                try:
                    st.switch_page("pages/01_📝_Testo.py")
                except Exception:
                    st.success(
                        f"Progetto «{project['title']}» attivo. "
                        "Apri 📝 Testo dalla sidebar."
                    )
                    st.rerun()
        with col_dup:
            if st.button("📋", key=f"dup_{project['slug']}", use_container_width=True,
                         help="Duplica progetto"):
                st.session_state[appstate.KEY_SHOW_DUPLICATE_PROJECT_TARGET] = project["slug"]
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"del_{project['slug']}", use_container_width=True,
                         help="Elimina progetto"):
                st.session_state[appstate.KEY_SHOW_DELETE_PROJECT_TARGET] = project["slug"]
                st.rerun()


def _render_new_project_modal_handler(user: User) -> None:
    """Modale Nuovo progetto: form + submit."""
    from components.wrappers import render_new_project_modal

    st.markdown("---")
    title, length, submitted = render_new_project_modal()

    col_cancel, _ = st.columns([1, 4])
    with col_cancel:
        if st.button("← Annulla", key="_modal_new_cancel"):
            st.session_state.pop(appstate.KEY_SHOW_NEW_PROJECT_MODAL, None)
            st.session_state.pop(appstate.KEY_NEW_PROJECT_ERROR, None)
            st.rerun()

    if submitted:
        new_slug = _create_new_project(user, title, length)
        if new_slug is not None:
            st.session_state.pop(appstate.KEY_SHOW_NEW_PROJECT_MODAL, None)
            st.session_state.pop(appstate.KEY_NEW_PROJECT_ERROR, None)
            appstate.set_current_project_slug(new_slug)
            st.success(f"Progetto creato. Apri 📝 Testo dalla sidebar.")
            st.rerun()


def _render_delete_dialog_handler(user: User, target_slug: str) -> None:
    """Modale conferma eliminazione progetto: doppia conferma con digitazione nome."""
    target = next((p for p in _list_user_projects(user) if p["slug"] == target_slug), None)
    if target is None:
        st.session_state.pop(appstate.KEY_SHOW_DELETE_PROJECT_TARGET, None)
        st.rerun()
        return

    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### 🗑 Elimina progetto «{target['title']}»")
        st.error(
            f"Stai per eliminare il progetto **{target['title']}**. "
            "Tutti i dati verranno persi: sceneggiatura, personaggi, vignette generate, "
            "pagine impaginate, export PDF. Questa operazione **non si può annullare**."
        )
        typed = st.text_input(
            f"Per confermare, scrivi esattamente il nome del progetto:",
            placeholder=target["title"],
            key=f"_del_confirm_input_{target_slug}",
        )
        name_matches = typed.strip() == target["title"]

        col_del, col_cancel = st.columns(2)
        with col_del:
            if st.button(
                "🗑 Elimina definitivamente",
                key=f"_del_confirm_{target_slug}",
                type="primary",
                disabled=not name_matches,
                use_container_width=True,
            ):
                _delete_project_by_slug(user, target_slug)
                st.session_state.pop(appstate.KEY_SHOW_DELETE_PROJECT_TARGET, None)
                st.success("Progetto eliminato.")
                st.rerun()
        with col_cancel:
            if st.button("Annulla", key=f"_del_cancel_{target_slug}", use_container_width=True):
                st.session_state.pop(appstate.KEY_SHOW_DELETE_PROJECT_TARGET, None)
                st.rerun()


def _render_duplicate_dialog_handler(user: User, target_slug: str) -> None:
    """Modale duplica progetto: chiedo nome + conferma."""
    target = next((p for p in _list_user_projects(user) if p["slug"] == target_slug), None)
    if target is None:
        st.session_state.pop(appstate.KEY_SHOW_DUPLICATE_PROJECT_TARGET, None)
        st.rerun()
        return

    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"### 📋 Duplica progetto")
        st.caption(
            "Crea una copia del progetto con tutti i dati (sceneggiatura, personaggi, "
            "reference) tranne le vignette generate. Quelle vanno rifatte nel duplicato."
        )
        default_new = f"{target['title']} — copia"
        new_name = st.text_input(
            "Nome del duplicato",
            value=default_new,
            key=f"_dup_name_{target_slug}",
        )
        col_dup, col_cancel = st.columns(2)
        with col_dup:
            if st.button(
                "📋 Duplica",
                key=f"_dup_confirm_{target_slug}",
                type="primary",
                use_container_width=True,
            ):
                new_slug = _duplicate_project_by_slug(user, target_slug, new_name.strip())
                if new_slug is not None:
                    st.session_state.pop(appstate.KEY_SHOW_DUPLICATE_PROJECT_TARGET, None)
                    appstate.set_current_project_slug(new_slug)
                    st.success("Progetto duplicato.")
                    st.rerun()
        with col_cancel:
            if st.button("Annulla", key=f"_dup_cancel_{target_slug}", use_container_width=True):
                st.session_state.pop(appstate.KEY_SHOW_DUPLICATE_PROJECT_TARGET, None)
                st.rerun()


def _render_home(user: User) -> None:
    # Cache user info per le pages
    st.session_state[appstate.KEY_USER_ID] = str(user.id)
    st.session_state[appstate.KEY_USER_EMAIL] = user.email
    st.session_state[appstate.KEY_USER_IS_ADMIN] = user.is_admin

    _render_sidebar_minimal(user)

    # Header
    st.title("I tuoi progetti")
    st.caption("Dall'idea al fumetto, in uno snap.")

    projects = _list_user_projects(user)

    # ============================================================
    # Modali (si auto-mostrano se session_state ce lo dice)
    # ============================================================
    if st.session_state.get(appstate.KEY_SHOW_NEW_PROJECT_MODAL):
        _render_new_project_modal_handler(user)
        return

    delete_target = st.session_state.get(appstate.KEY_SHOW_DELETE_PROJECT_TARGET)
    if delete_target:
        _render_delete_dialog_handler(user, delete_target)
        return

    duplicate_target = st.session_state.get(appstate.KEY_SHOW_DUPLICATE_PROJECT_TARGET)
    if duplicate_target:
        _render_duplicate_dialog_handler(user, duplicate_target)
        return

    # ============================================================
    # Vista normale: lista progetti o empty state
    # ============================================================
    if not projects:
        st.markdown("---")
        from components.ui.empty_state import render_empty_state
        clicked = render_empty_state(
            icon="📚",
            title="Non hai ancora progetti",
            description="Crea il primo per iniziare.",
            action_label="+ Nuovo progetto",
            action_key="_empty_state_new_project",
        )
        if clicked:
            st.session_state[appstate.KEY_SHOW_NEW_PROJECT_MODAL] = True
            st.rerun()
        return

    # Grid 3 colonne con card progetto
    st.markdown(f"_{len(projects)} progett{'o' if len(projects) == 1 else 'i'}_")
    st.markdown("")
    cols_per_row = 3
    for row_start in range(0, len(projects), cols_per_row):
        row = projects[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, project in zip(cols, row):
            with col:
                _render_project_card(project, user)


# ============================================================
# Routing in base allo stato di autenticazione
# ============================================================
with session_scope() as s:
    _user = current_user(s)

if _user is None:
    _render_login()
elif _user.must_change_password:
    _render_change_password()
else:
    enforce_sidebar_visibility()
    _render_home(_user)
