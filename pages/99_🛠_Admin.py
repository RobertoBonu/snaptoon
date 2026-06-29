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

from app_state.ui import enforce_sidebar_visibility, render_sidebar_nav, show_page_loading
enforce_sidebar_visibility()

# Loading overlay durante gli import (~3s)
_page_loader = show_page_loading("Carico il pannello admin...")


# ============================================================
# Backend imports
# ============================================================
import app_state as appstate
from auth import current_user, hash_password, logout
from billing.plans import ROLE_CONFIG, role_config
from db.models import CreditOperation, Plan, Role, User
from db.repos import admin_styles as admin_styles_repo
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import usage as usage_repo
from db.repos import users as users_repo
from db.session import session_scope
from snaptoon_core.styles_library import list_presets


# ============================================================
# Auth gate ADMIN
# ============================================================
with session_scope() as _s:
    _user = current_user(_s)

# Backend pronto: rimuovi loading overlay
_page_loader.empty()

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
render_sidebar_nav(_user)

with st.sidebar:
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
# TABS: Utenti | Abbonamenti | Stili | Modelli AI
# ============================================================
tab_users, tab_subs, tab_styles, tab_models = st.tabs([
    "👥 Utenti",
    "💳 Abbonamenti",
    "🎨 Stili",
    "🤖 Modelli AI",
])


# ============================================================
# TAB UTENTI (codice esistente avvolto nel tab)
# ============================================================
with tab_users:


    # ============================================================
    # Crea nuovo utente
    # ============================================================

    with st.expander("➕ Crea nuovo utente", expanded=False):
        # Genera la password UNA VOLTA per sessione, salvala in session_state.
        # Senza questo, ad ogni rerun _generate_temp_password() ne genera una nuova
        # e quella visualizzata può divergere da quella salvata nel DB.
        if "_admin_new_user_pwd" not in st.session_state:
            st.session_state["_admin_new_user_pwd"] = _generate_temp_password()

        col_regen_l, col_regen_r = st.columns([3, 1])
        with col_regen_l:
            st.caption(
                f"Password temporanea generata: **`{st.session_state['_admin_new_user_pwd']}`**"
            )
        with col_regen_r:
            if st.button("🎲 Rigenera password", key="_regen_pwd", use_container_width=True):
                st.session_state["_admin_new_user_pwd"] = _generate_temp_password()
                st.rerun()

        with st.form("_form_new_user", clear_on_submit=False):
            col_email, col_role = st.columns(2)
            with col_email:
                new_email = st.text_input(
                    "Email",
                    placeholder="marco@example.com",
                    key="_new_user_email",
                )
            with col_role:
                new_role_label = st.selectbox(
                    "Ruolo iniziale",
                    options=[role_config(r).label for r in Role],
                    key="_new_user_role",
                )
                new_role = next(r for r in Role if role_config(r).label == new_role_label)

            col_pwd, col_credits = st.columns(2)
            with col_pwd:
                new_pwd = st.text_input(
                    "Password temporanea (editabile)",
                    value=st.session_state["_admin_new_user_pwd"],
                    help="L'utente la cambierà al primo login. Puoi modificarla qui o usare la rigenera sopra.",
                    key="_new_user_pwd",
                )
            with col_credits:
                new_credits = st.number_input(
                    "Crediti iniziali",
                    min_value=0, max_value=100000,
                    value=role_config(new_role).monthly_credits,
                    key="_new_user_credits",
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
                                Role.kids: Plan.creator,
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
                    # Reset la password generata per il prossimo utente
                    st.session_state["_admin_last_created"] = {
                        "email": new_email,
                        "pwd": new_pwd,
                        "role": role_config(new_role).label,
                    }
                    st.session_state.pop("_admin_new_user_pwd", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")

        # Mostra fuori dal form le credenziali appena create (sopravvive al rerun)
        if "_admin_last_created" in st.session_state:
            info = st.session_state["_admin_last_created"]
            st.success(
                f"✅ Utente **{info['email']}** creato come **{info['role']}**."
            )
            st.code(
                f"Email:    {info['email']}\nPassword: {info['pwd']}",
                language="text",
            )
            st.caption(
                "⚠️ Copia ora le credenziali e mandale all'utente. "
                "Verranno cancellate dalla pagina al refresh."
            )
            if st.button("🔒 Cancella credenziali dalla vista", key="_clear_last"):
                st.session_state.pop("_admin_last_created", None)
                st.rerun()


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

                # Reset password
                with st.form(f"_form_reset_pwd_{usr.id}", border=True):
                    st.markdown("**🔑 Reset password**")
                    reset_pwd_value = st.text_input(
                        "Nuova password temporanea",
                        value=_generate_temp_password(),
                        key=f"reset_pwd_{usr.id}",
                        help="L'utente dovrà cambiarla al prossimo login.",
                    )
                    if st.form_submit_button(
                        "🔑 Imposta nuova password",
                        use_container_width=True,
                    ):
                        if len(reset_pwd_value) < 8:
                            st.error("Password troppo corta (min 8 char).")
                        else:
                            with session_scope() as s:
                                fresh_usr = users_repo.get_by_id(s, usr.id)
                                if fresh_usr is not None:
                                    users_repo.set_password_hash(
                                        s, fresh_usr, hash_password(reset_pwd_value)
                                    )
                                    # Forziamo cambio al prossimo login
                                    fresh_usr.must_change_password = True
                                    usage_repo.audit_admin_action(
                                        s, admin=_user, action="reset_password",
                                        target_user_id=fresh_usr.id, payload={},
                                    )
                            st.success(
                                f"Password resettata. Nuova password temporanea: `{reset_pwd_value}` — "
                                "mandala all'utente."
                            )

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


# ============================================================
# TAB ABBONAMENTI
# ============================================================
with tab_subs:
    import os

    st.markdown("### 💳 Riepilogo abbonamenti")
    st.caption(
        "Storico movimenti crediti globali, distribuzione per ruolo, modifiche piano. "
        "(Stripe integrato in V1.1 — per ora le assegnazioni sono manuali via tab Utenti.)"
    )

    # Distribuzione ruoli
    st.markdown("#### Distribuzione utenti per ruolo")
    role_dist = [
        {
            "Ruolo": role_config(r).label,
            "Utenti": sum(1 for u in _all_users if u.role == r),
            "Crediti/mese": role_config(r).monthly_credits,
            "Progetti max": "∞" if role_config(r).max_projects == 0 else role_config(r).max_projects,
            "Qualità": ", ".join(role_config(r).allowed_qualities),
        }
        for r in Role
    ]
    st.dataframe(role_dist, use_container_width=True, hide_index=True)

    st.divider()

    # Storico credit_ledger globale
    st.markdown("#### Storico operazioni crediti (ultime 100)")
    with session_scope() as _s2:
        from sqlalchemy import select
        from db.models import CreditLedger
        recent_stmt = (
            select(CreditLedger)
            .order_by(CreditLedger.occurred_at.desc())
            .limit(100)
        )
        recent_entries = list(_s2.execute(recent_stmt).scalars())
        # Pre-build mapping user_id → email per visualizzazione
        ledger_view = []
        users_by_id = {u.id: u for u in _all_users}
        for e in recent_entries:
            user_email = users_by_id[e.user_id].email if e.user_id in users_by_id else "?"
            ledger_view.append({
                "Data": e.occurred_at.strftime("%d/%m %H:%M"),
                "Utente": user_email,
                "Operazione": e.operation.value,
                "Δ": f"{'+' if e.delta > 0 else ''}{e.delta}",
                "Saldo dopo": e.balance_after,
                "Motivo": (e.reason or "")[:80],
            })

    if ledger_view:
        st.dataframe(ledger_view, use_container_width=True, hide_index=True)
    else:
        st.caption("_Nessuna operazione registrata._")


# ============================================================
# TAB STILI
# ============================================================
with tab_styles:
    st.markdown("### 🎨 Gestione stili")
    st.caption(
        "Stili curati dall'admin disponibili a tutti gli utenti, "
        "in aggiunta ai 98 preset hardcoded della libreria visual-prompt-engine."
    )

    # Tabs interni: Admin Styles | Libreria preset (read-only)
    sub_admin, sub_lib = st.tabs(["✏️ Stili admin", "📚 Libreria preset (read-only)"])

    with sub_admin:
        with session_scope() as _s2:
            _admin_styles = admin_styles_repo.list_all(_s2)
            _admin_styles_view = [
                {
                    "id": s.id, "slug": s.slug, "label": s.label,
                    "category": s.category, "expansion": s.expansion,
                    "negative_terms": s.negative_terms, "is_handmade": s.is_handmade,
                    "is_active": s.is_active, "notes": s.notes,
                }
                for s in _admin_styles
            ]

        st.caption(f"{len(_admin_styles_view)} stili admin caricati.")

        # Crea nuovo
        with st.expander("➕ Crea nuovo stile admin", expanded=False):
            with st.form("_form_new_admin_style", clear_on_submit=True):
                new_label = st.text_input(
                    "Label", placeholder="Es. Cyberpunk Neon Editorial",
                )
                new_category = st.selectbox(
                    "Categoria",
                    options=["Personali", "fumetto", "illustrazione", "fotografia",
                             "cinema", "kids", "fotografia_autore"],
                    index=0,
                )
                new_expansion = st.text_area(
                    "Espansione (prompt completo)",
                    height=180,
                    placeholder="Visual style: ... Technique: ... Aesthetic: ...",
                )
                new_negative = st.text_input(
                    "Negative terms (separati da virgola)",
                    placeholder="anime, chibi, photoreal, soft gradients",
                )
                new_handmade = st.checkbox(
                    "is_handmade (forza media authenticity clause)",
                    value=False,
                )
                new_notes = st.text_area(
                    "Note (solo per admin, non finiscono nel prompt)",
                    height=80,
                )

                if st.form_submit_button("Crea stile", type="primary"):
                    try:
                        with session_scope() as s:
                            admin_styles_repo.create(
                                s,
                                label=new_label,
                                category=new_category,
                                expansion=new_expansion,
                                negative_terms=new_negative,
                                is_handmade=new_handmade,
                                notes=new_notes,
                            )
                        st.toast(f"Stile «{new_label}» creato.", icon="🎨")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

        # Lista stili admin
        if not _admin_styles_view:
            st.info(
                "Nessuno stile admin ancora. Crea il primo qui sopra. "
                "Gli stili appariranno in 🎨 Stile → Sfoglia libreria → categoria scelta."
            )
        else:
            for stl in _admin_styles_view:
                active_icon = "🟢" if stl["is_active"] else "⚪"
                with st.expander(
                    f"{active_icon} **{stl['label']}** — {stl['category']}",
                    expanded=False,
                ):
                    with st.form(f"_edit_style_{stl['id']}"):
                        ed_label = st.text_input(
                            "Label", value=stl["label"],
                        )
                        ed_category = st.selectbox(
                            "Categoria",
                            options=["Personali", "fumetto", "illustrazione", "fotografia",
                                     "cinema", "kids", "fotografia_autore"],
                            index=["Personali", "fumetto", "illustrazione", "fotografia",
                                   "cinema", "kids", "fotografia_autore"].index(stl["category"])
                                  if stl["category"] in ["Personali", "fumetto", "illustrazione", "fotografia",
                                                          "cinema", "kids", "fotografia_autore"] else 0,
                        )
                        ed_expansion = st.text_area(
                            "Espansione", value=stl["expansion"], height=180,
                        )
                        ed_negative = st.text_input(
                            "Negative terms", value=stl["negative_terms"],
                        )
                        ed_handmade = st.checkbox(
                            "is_handmade", value=stl["is_handmade"],
                        )
                        ed_active = st.checkbox(
                            "Attivo (visibile agli utenti)", value=stl["is_active"],
                        )
                        ed_notes = st.text_area(
                            "Note (admin)", value=stl["notes"], height=80,
                        )

                        col_s, col_d = st.columns(2)
                        with col_s:
                            save_btn = st.form_submit_button(
                                "💾 Salva", type="secondary",
                                use_container_width=True,
                            )
                        with col_d:
                            del_btn = st.form_submit_button(
                                "🗑 Elimina",
                                use_container_width=True,
                            )

                        if save_btn:
                            with session_scope() as s:
                                style = admin_styles_repo.get_by_id(s, stl["id"])
                                if style is not None:
                                    admin_styles_repo.update(
                                        s, style,
                                        label=ed_label, category=ed_category,
                                        expansion=ed_expansion, negative_terms=ed_negative,
                                        is_handmade=ed_handmade, is_active=ed_active,
                                        notes=ed_notes,
                                    )
                            st.toast("Stile salvato.", icon="✅")
                            st.rerun()
                        if del_btn:
                            with session_scope() as s:
                                style = admin_styles_repo.get_by_id(s, stl["id"])
                                if style is not None:
                                    admin_styles_repo.delete(s, style)
                            st.toast("Stile eliminato.")
                            st.rerun()

                    st.caption(f"Slug: `{stl['slug']}`")

    with sub_lib:
        st.caption(
            "I 98 preset hardcoded della libreria visual-prompt-engine, "
            "in `snaptoon_core/library_data/styles.md` + `styles_custom.md`. "
            "Read-only (modificabili solo via codice + redeploy)."
        )
        all_presets = list_presets()
        lib_view = [
            {
                "ID": p.id,
                "Label": p.label,
                "Categoria": p.category,
                "Handmade": "✓" if p.is_handmade else "",
                "Custom": "✓" if p.is_custom else "",
            }
            for p in all_presets
        ]
        st.dataframe(lib_view, use_container_width=True, hide_index=True, height=400)


# ============================================================
# TAB MODELLI AI
# ============================================================
with tab_models:
    import os

    st.markdown("### 🤖 Configurazione modelli AI")
    st.caption(
        "I modelli AI usati globalmente dall'app. Sono caricati dalle environment "
        "variables di Replit (Secrets). Per cambiarli, modifica i Secrets nel Repl "
        "e riavvia l'app."
    )

    st.markdown("#### Testo (Claude)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Modello attivo:**")
        st.code(os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7 (default)"), language="text")
    with col_t2:
        st.markdown("**API key configurata:**")
        st.code("✅ presente" if os.getenv("ANTHROPIC_API_KEY") else "❌ mancante",
                language="text")

    st.markdown("#### Immagini — OpenAI")
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        st.markdown("**Modello attivo:**")
        st.code(os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2 (default)"), language="text")
    with col_o2:
        st.markdown("**API key configurata:**")
        st.code("✅ presente" if os.getenv("OPENAI_API_KEY") else "❌ mancante",
                language="text")

    st.markdown("#### Immagini — Google Gemini")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Modello attivo:**")
        st.code(os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview (default)"),
                language="text")
    with col_g2:
        st.markdown("**API key configurata:**")
        st.code("✅ presente" if os.getenv("GEMINI_API_KEY") else "❌ mancante",
                language="text")

    st.divider()
    st.markdown("#### Default qualità per ruolo")
    quality_dist = [
        {
            "Ruolo": role_config(r).label,
            "Qualità ammesse": ", ".join(role_config(r).allowed_qualities),
            "Note": "Selezionabile per vignetta dall'utente",
        }
        for r in Role
    ]
    st.dataframe(quality_dist, use_container_width=True, hide_index=True)

    st.divider()
    st.info(
        "**Roadmap V1.1**: tabella `ai_models` per persistere modelli + selezione "
        "default per ruolo + abilitazione/disabilitazione live senza riavvio."
    )
