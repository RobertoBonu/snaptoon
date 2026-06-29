"""SnapToon — pagina ⚙️ Account.

Profilo utente, dati abbonamento, lista progetti, sicurezza.

Accessibile a tutti gli utenti loggati (non admin-only).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Account — SnapToon",
    page_icon="⚙️",
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
_page_loader = show_page_loading("Apriamo il tuo account...")


# ============================================================
# Backend imports
# ============================================================
import app_state as appstate
from auth import current_user, hash_password, logout
from auth.passwords import verify_password
from billing.plans import role_config
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import users as users_repo
from db.session import session_scope


# ============================================================
# Auth gate (qualsiasi ruolo)
# ============================================================
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


_cfg = role_config(_user.role)


# ============================================================
# Sidebar
# ============================================================
render_sidebar_nav(_user)

with st.sidebar:
    # Email + ruolo + crediti sono mostrati nel contenuto principale della
    # pagina Account, non servono ridondanti in sidebar.
    if st.button("🚪 Esci", key="_sb_logout_account", use_container_width=True):
        with session_scope() as s:
            logout(s)
        appstate.clear_session_keys()
        st.switch_page("app.py")


# ============================================================
# Header
# ============================================================
st.title("⚙️ Account")
st.caption(f"Profilo di **{_user.email}**")

st.divider()


# ============================================================
# Profilo
# ============================================================
st.markdown("### Profilo")

col_p1, col_p2 = st.columns(2)
with col_p1:
    st.markdown(f"**Email:** {_user.email}")
    st.markdown(f"**Ruolo:** {_cfg.label}")
with col_p2:
    st.markdown(f"**Account creato:** {_user.created_at.strftime('%d/%m/%Y')}")
    if _user.last_login_at:
        st.markdown(f"**Ultimo accesso:** {_user.last_login_at.strftime('%d/%m/%Y %H:%M')}")
    else:
        st.markdown(f"**Ultimo accesso:** —")

st.divider()


# ============================================================
# Abbonamento
# ============================================================
st.markdown("### Abbonamento")

col_a1, col_a2 = st.columns(2)
with col_a1:
    with st.container(border=True):
        st.markdown(f"#### {_cfg.label}")
        st.caption("Il tuo ruolo attuale")

        pct = (_user.credits_used_this_period / _user.credits_total_this_period * 100) if _user.credits_total_this_period > 0 else 0
        st.markdown(f"**Crediti rimasti:** {_user.credits_remaining} / {_user.credits_total_this_period}")
        st.progress(min(1.0, _user.credits_used_this_period / max(1, _user.credits_total_this_period)))
        st.caption(f"Usati: {_user.credits_used_this_period} crediti ({pct:.0f}%)")
        st.caption(f"Periodo iniziato: {_user.period_started_at.strftime('%d/%m/%Y')}")

with col_a2:
    with st.container(border=True):
        st.markdown("#### Cosa include")
        for feature in _cfg.features:
            st.markdown(f"- {feature}")
        if _cfg.can_access_admin:
            st.caption("🛠 Accesso pannello Admin")
        if _cfg.can_use_bookshop:
            st.caption("📚 Pubblicazione bookshop (in arrivo)")
        if _cfg.can_export_idml:
            st.caption("🖨 Export IDML tipografico (in arrivo)")

st.caption(
    "Per cambiare ruolo o ottenere più crediti, contatta l'amministratore."
)

st.divider()


# ============================================================
# Storico crediti
# ============================================================
st.markdown("### Storico operazioni crediti")

with session_scope() as _s:
    _user_db = users_repo.get_by_id(_s, _user.id)
    _ledger = credits_repo.get_ledger(_s, _user_db, limit=50)
    _ledger_view = [
        {
            "Data": e.occurred_at.strftime("%d/%m/%Y %H:%M"),
            "Operazione": e.operation.value,
            "Δ": f"{'+' if e.delta > 0 else ''}{e.delta}",
            "Saldo dopo": e.balance_after,
            "Motivo": (e.reason or "")[:60],
        }
        for e in _ledger
    ]

if _ledger_view:
    st.dataframe(_ledger_view, use_container_width=True, hide_index=True)
else:
    st.caption("_Nessuna operazione registrata._")

st.divider()


# ============================================================
# I miei progetti
# ============================================================
st.markdown("### I miei progetti")

with session_scope() as _s:
    _projects = projects_repo.list_by_owner(_s, _user.id)
    _projects_view = [
        {
            "slug": p.slug,
            "name": p.name,
            "length_target": p.length_target.value,
            "style_id": p.style_id,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        for p in _projects
    ]

if not _projects_view:
    st.caption("_Nessun progetto ancora. Crea il primo dalla home._")
else:
    st.caption(f"_{len(_projects_view)} progetti_")
    for proj in _projects_view:
        with st.container(border=True):
            col_pi, col_pa = st.columns([4, 1])
            with col_pi:
                st.markdown(f"**{proj['name']}**")
                st.caption(
                    f"Lunghezza: {proj['length_target']} · "
                    f"Stile: `{proj['style_id'] or '—'}` · "
                    f"Creato il {proj['created_at'].strftime('%d/%m/%Y')}"
                )
            with col_pa:
                if st.button("Apri", key=f"_open_{proj['slug']}", use_container_width=True):
                    appstate.set_current_project_slug(proj["slug"])
                    try:
                        st.switch_page("pages/01_📝_Testo.py")
                    except Exception:
                        st.switch_page("app.py")

st.divider()


# ============================================================
# Sicurezza — cambio password
# ============================================================
st.markdown("### 🔑 Sicurezza")

with st.form("_form_change_pwd", border=True):
    st.markdown("**Cambia la tua password**")
    old_pwd = st.text_input("Password attuale", type="password")
    new_pwd = st.text_input("Nuova password (min 8 caratteri)", type="password")
    confirm_pwd = st.text_input("Conferma nuova password", type="password")

    if st.form_submit_button("Aggiorna password", type="primary"):
        if not verify_password(old_pwd, _user.password_hash):
            st.error("Password attuale non corretta.")
        elif len(new_pwd) < 8:
            st.error("La nuova password deve avere almeno 8 caratteri.")
        elif new_pwd != confirm_pwd:
            st.error("Le due nuove password non coincidono.")
        else:
            with session_scope() as s:
                fresh = users_repo.get_by_id(s, _user.id)
                if fresh is not None:
                    users_repo.set_password_hash(s, fresh, hash_password(new_pwd))
            st.success("Password aggiornata. Al prossimo accesso usa la nuova password.")
