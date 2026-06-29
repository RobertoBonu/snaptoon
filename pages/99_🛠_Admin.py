"""SnapToon — pannello 🛠 Admin.

Accesso solo per utenti con role = admin.

Funzionalità I1:
- Lista utenti con filtri (ruolo, stato)
- Crea nuovo utente (con role, crediti iniziali)
- Modifica utente: role, credits, attivo/disabilitato, reset password
- Grant crediti manuale
- Disabilita / riabilita
"""

from __future__ import annotations

import secrets
import string
import uuid
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Admin — SnapToon",
    page_icon="🛠",
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
from auth import current_user, hash_password, logout
from billing.plans import ROLE_CONFIG, role_config
from db.models import CreditOperation, Plan, Role, User
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import usage as usage_repo
from db.repos import users as users_repo
from db.session import session_scope


# ============================================================
# Auth gate ADMIN
# ============================================================
with session_scope() as _s:
    _user = current_user(_s)

if _user is None:
    st.error("Devi accedere per usare questa pagina.")
    st.markdown("[← Torna al login](/)")
    st.stop()

if _user.role != Role.admin:
    st.error("Pagina riservata agli amministratori.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


# ============================================================
# Sidebar
# ============================================================
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
    st.caption(_user.email)
    st.caption("**Admin panel**")
    st.divider()
    if st.button("🚪 Esci", key="_sb_logout_admin", use_container_width=True):
        with session_scope() as s:
            logout(s)
        appstate.clear_session_keys()
        st.switch_page("app.py")


# ============================================================
# Header + metriche globali
# ============================================================

st.title("🛠 Pannello Admin")
st.caption("Solo per amministratori.")


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


with session_scope() as _s:
    _all_users = users_repo.list_all(_s)
    n_active = sum(1 for u in _all_users if u.is_active)
    n_admins = sum(1 for u in _all_users if u.role == Role.admin)
    n_premium = sum(1 for u in _all_users if u.role == Role.autore_premium)
    n_editor = sum(1 for u in _all_users if u.role == Role.editore)
    n_base = sum(1 for u in _all_users if u.role == Role.autore_base)
    active_7d = users_repo.count_active_in_last_days(_s, days=7)

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.metric("Utenti totali", len(_all_users))
with col_m2:
    st.metric("Attivi (7gg)", active_7d)
with col_m3:
    st.metric("Admin", n_admins)
with col_m4:
    st.metric("Premium", n_premium)
with col_m5:
    st.metric("Base + Editori", n_base + n_editor)

st.divider()


# ============================================================
# Crea nuovo utente
# ============================================================

with st.expander("➕ Crea nuovo utente", expanded=False):
    with st.form("_form_new_user", clear_on_submit=False):
        col_email, col_role = st.columns(2)
        with col_email:
            new_email = st.text_input(
                "Email",
                placeholder="marco@example.com",
            )
        with col_role:
            new_role_label = st.selectbox(
                "Ruolo iniziale",
                options=[role_config(r).label for r in Role],
            )
            new_role = next(r for r in Role if role_config(r).label == new_role_label)

        col_pwd, col_credits = st.columns(2)
        with col_pwd:
            new_pwd = st.text_input(
                "Password temporanea",
                value=_generate_temp_password(),
                help="L'utente la cambierà al primo login.",
            )
        with col_credits:
            new_credits = st.number_input(
                "Crediti iniziali",
                min_value=0, max_value=100000,
                value=role_config(new_role).monthly_credits,
            )

        if st.form_submit_button("Crea account", type="primary"):
            try:
                with session_scope() as s:
                    existing = users_repo.get_by_email(s, new_email)
                    if existing:
                        st.error(f"Esiste già un utente con email {new_email}.")
                    elif "@" not in new_email or len(new_pwd) < 8:
                        st.error("Email non valida o password troppo corta (min 8 char).")
                    else:
                        # Mappa role → plan legacy (per backward compat)
                        plan_map = {
                            Role.admin: Plan.pro,
                            Role.autore_base: Plan.creator,
                            Role.autore_premium: Plan.pro,
                            Role.editore: Plan.pro,
                        }
                        new_user = users_repo.create_user(
                            s,
                            email=new_email,
                            password_hash=hash_password(new_pwd),
                            plan=plan_map[new_role],
                            initial_credits=int(new_credits),
                            is_admin=(new_role == Role.admin),
                            must_change_password=True,
                        )
                        # Set role (set_user crea con role default; lo cambiamo)
                        users_repo.set_role(s, new_user, new_role)
                        usage_repo.audit_admin_action(
                            s, admin=_user, action="create_user",
                            target_user_id=new_user.id,
                            payload={"email": new_email, "role": new_role.value,
                                     "initial_credits": int(new_credits)},
                        )
                st.success(
                    f"✅ Utente **{new_email}** creato come **{role_config(new_role).label}**. "
                    f"Password temporanea: `{new_pwd}` — mandala fuori dall'app."
                )
                st.warning(
                    "⚠️ Per sicurezza, ricarica la pagina dopo aver comunicato la "
                    "password — sparirà dal log."
                )
            except Exception as e:
                st.error(f"Errore: {e}")


st.divider()


# ============================================================
# Lista utenti con filtri + azioni inline
# ============================================================

st.markdown("### Utenti registrati")

col_f1, col_f2 = st.columns(2)
with col_f1:
    filter_role = st.selectbox(
        "Filtro ruolo",
        options=["(tutti)"] + [role_config(r).label for r in Role],
    )
with col_f2:
    filter_status = st.selectbox(
        "Filtro stato",
        options=["(tutti)", "Attivi", "Disattivati"],
    )


def _user_passes_filters(u: User) -> bool:
    if filter_role != "(tutti)" and role_config(u.role).label != filter_role:
        return False
    if filter_status == "Attivi" and not u.is_active:
        return False
    if filter_status == "Disattivati" and u.is_active:
        return False
    return True


filtered_users = [u for u in _all_users if _user_passes_filters(u)]
st.caption(f"_{len(filtered_users)} utenti su {len(_all_users)} totali_")
st.markdown("")

for usr in filtered_users:
    role_label = role_config(usr.role).label
    status_emoji = "🟢" if usr.is_active else "🔴"
    is_me = (usr.id == _user.id)
    me_badge = " _(tu)_" if is_me else ""

    with st.expander(
        f"{status_emoji} **{usr.email}** — {role_label} · "
        f"{usr.credits_remaining}/{usr.credits_total_this_period} crediti{me_badge}",
        expanded=False,
    ):
        col_info, col_act = st.columns([2, 1])

        with col_info:
            st.markdown(f"**ID:** `{usr.id}`")
            st.markdown(f"**Email:** {usr.email}")
            st.markdown(f"**Ruolo:** {role_label}")
            st.markdown(f"**Piano (legacy):** {usr.plan.value}")
            st.markdown(f"**Crediti:** {usr.credits_remaining}/{usr.credits_total_this_period}")
            st.markdown(f"**Periodo iniziato:** {usr.period_started_at.strftime('%d/%m/%Y')}")
            st.markdown(f"**Creato il:** {usr.created_at.strftime('%d/%m/%Y')}")
            if usr.last_login_at:
                st.markdown(f"**Ultimo accesso:** {usr.last_login_at.strftime('%d/%m/%Y %H:%M')}")
            st.markdown(f"**Stato:** {'✅ attivo' if usr.is_active else '🚫 disabilitato'}")
            if usr.must_change_password:
                st.caption("⚠️ Deve ancora cambiare password al primo login.")

        with col_act:
            # Cambia ruolo
            with st.form(f"_form_role_{usr.id}", border=True):
                st.markdown("**Cambia ruolo**")
                new_role_label = st.selectbox(
                    "Nuovo ruolo",
                    options=[role_config(r).label for r in Role],
                    index=list(Role).index(usr.role),
                    key=f"role_sel_{usr.id}",
                    label_visibility="collapsed",
                )
                new_role_obj = next(r for r in Role if role_config(r).label == new_role_label)
                reset_credits = st.checkbox(
                    f"Resetta crediti a {role_config(new_role_obj).monthly_credits}",
                    value=(new_role_obj != usr.role),
                    key=f"reset_cr_{usr.id}",
                )
                if st.form_submit_button(
                    "💾 Applica",
                    type="secondary",
                    use_container_width=True,
                    disabled=is_me and new_role_obj != Role.admin,
                    help="Non puoi togliere il ruolo admin a te stesso." if is_me and new_role_obj != Role.admin else None,
                ):
                    with session_scope() as s:
                        fresh_usr = users_repo.get_by_id(s, usr.id)
                        if fresh_usr is not None:
                            users_repo.set_role(
                                s, fresh_usr, new_role_obj,
                                reset_period_credits=role_config(new_role_obj).monthly_credits if reset_credits else None,
                            )
                            usage_repo.audit_admin_action(
                                s, admin=_user, action="change_role",
                                target_user_id=fresh_usr.id,
                                payload={"new_role": new_role_obj.value, "reset_credits": reset_credits},
                            )
                    st.toast(f"Ruolo aggiornato a {role_config(new_role_obj).label}.", icon="🛠")
                    st.rerun()

            # Grant crediti
            with st.form(f"_form_grant_{usr.id}", border=True):
                st.markdown("**🪙 Aggiungi crediti**")
                grant_amount = st.number_input(
                    "Quantità",
                    min_value=1, max_value=10000, value=100,
                    key=f"grant_amt_{usr.id}",
                )
                grant_reason = st.text_input(
                    "Motivazione",
                    placeholder="Es. compensazione bug",
                    key=f"grant_reason_{usr.id}",
                )
                if st.form_submit_button(
                    "🪙 Accredita",
                    type="primary",
                    use_container_width=True,
                ):
                    with session_scope() as s:
                        fresh_usr = users_repo.get_by_id(s, usr.id)
                        if fresh_usr is not None:
                            credits_repo.grant(
                                s, fresh_usr,
                                amount=int(grant_amount),
                                operation=CreditOperation.admin_grant,
                                reason=f"Admin grant da {_user.email}: {grant_reason}",
                            )
                            usage_repo.audit_admin_action(
                                s, admin=_user, action="grant_credits",
                                target_user_id=fresh_usr.id,
                                payload={"amount": int(grant_amount), "reason": grant_reason},
                            )
                    st.toast(f"+{grant_amount} crediti accreditati.", icon="🪙")
                    st.rerun()

            # Disabilita / Riabilita
            if not is_me:
                if usr.is_active:
                    if st.button(
                        "🚫 Disabilita account",
                        key=f"deact_{usr.id}",
                        use_container_width=True,
                    ):
                        with session_scope() as s:
                            fresh_usr = users_repo.get_by_id(s, usr.id)
                            if fresh_usr is not None:
                                users_repo.set_active(s, fresh_usr, False)
                                usage_repo.audit_admin_action(
                                    s, admin=_user, action="deactivate_user",
                                    target_user_id=fresh_usr.id, payload={},
                                )
                        st.toast("Account disabilitato.")
                        st.rerun()
                else:
                    if st.button(
                        "✓ Riabilita account",
                        key=f"react_{usr.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        with session_scope() as s:
                            fresh_usr = users_repo.get_by_id(s, usr.id)
                            if fresh_usr is not None:
                                users_repo.set_active(s, fresh_usr, True)
                                usage_repo.audit_admin_action(
                                    s, admin=_user, action="reactivate_user",
                                    target_user_id=fresh_usr.id, payload={},
                                )
                        st.toast("Account riattivato.")
                        st.rerun()
            else:
                st.caption("_(non puoi disabilitare te stesso)_")
