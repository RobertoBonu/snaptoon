"""Helper UI condivisi tra app.py e pages/*.py.

Centralizza override CSS necessari per garantire usabilità della UI
quando il design system custom dell'agente nasconde elementi critici.
"""

from __future__ import annotations

import streamlit as st


def enforce_sidebar_visibility() -> None:
    """Fissa la sidebar SEMPRE visibile, non chiudibile.

    Decisione MVP: dato che il CSS dell'agente nasconde stHeader (dove vive
    il toggle), una volta chiusa la sidebar diventava irrecuperabile.
    Soluzione: la sidebar resta sempre aperta. Niente bottone chiudi,
    niente toggle in alto. Sidebar = sempre lì.

    Trade-off:
      + Sidebar sempre accessibile, zero bug di navigazione persa
      + Esperienza uniforme tra desktop e mobile (sui Repl preview)
      - Utenti su schermo stretto non possono recuperare spazio chiudendola

    Per MVP è il trade-off giusto.
    """
    # Determina se l'utente loggato corrente è admin per nascondere link Admin
    # ai non-admin. Streamlit mostra tutti i pages/*.py come link sidebar a
    # qualunque utente: bisogna nasconderli a livello CSS.
    #
    # SEMPRE lookup DB (no cache session_state): la cache può essere stale
    # da una sessione precedente con ruolo diverso, e mostrerebbe Admin
    # a utenti non-admin. Costo: 1 query in più per render.
    is_admin = False
    is_kids_role = False
    try:
        from auth.sessions import current_user as _current_user
        from db.models import Role as _Role
        from db.session import session_scope as _session_scope
        with _session_scope() as _s:
            _u = _current_user(_s)
            if _u is not None:
                is_admin = _u.is_admin
                is_kids_role = (_u.role == _Role.kids)
                st.session_state["snaptoon_user_is_admin"] = is_admin
                st.session_state["snaptoon_user_is_kids"] = is_kids_role
    except Exception:
        pass

    # Nasconde gli ultimi N nav items per role:
    # - non-admin: nascondi solo "Admin" (ultimo, file 99_🛠_Admin.py)
    # - admin: nessun nav nascosto
    # Costruisci CSS per nascondere link basato sul ruolo.
    # Ordine pages/ attuale (numerico = ordine sidebar):
    #   1. HOME (entrypoint app.py)
    #   2. 01_📝_Testo
    #   3. 02_🎨_Stile
    #   4. 03_👥_Personaggi
    #   5. 04_🖼_Genera
    #   6. 05_📐_Impagina
    #   7. 06_⭐_KIDS
    #   8. 89_⚙️_Account
    #   9. 99_🛠_Admin
    hide_css_parts: list[str] = []

    if not is_admin:
        # Nascondi link Admin per non-admin
        hide_css_parts.append("""
        [data-testid="stSidebarNavItems"] a[href*="Admin"],
        [data-testid="stSidebarNav"] a[href*="Admin"] {
            display: none !important;
            visibility: hidden !important;
        }
        """)

    if not (is_admin or is_kids_role):
        # KIDS visibile solo a admin + role=kids. Nascondi per altri.
        hide_css_parts.append("""
        [data-testid="stSidebarNavItems"] a[href*="KIDS"],
        [data-testid="stSidebarNav"] a[href*="KIDS"] {
            display: none !important;
            visibility: hidden !important;
        }
        """)

    if is_kids_role:
        # Per ruolo Kids: nascondi le 5 sezioni del flusso standard
        # (Testo, Stile, Personaggi, Genera, Impagina). Vedono solo
        # HOME + KIDS + Account.
        hide_css_parts.append("""
        [data-testid="stSidebarNavItems"] a[href*="Testo"],
        [data-testid="stSidebarNavItems"] a[href*="Stile"],
        [data-testid="stSidebarNavItems"] a[href*="Personaggi"],
        [data-testid="stSidebarNavItems"] a[href*="Genera"],
        [data-testid="stSidebarNavItems"] a[href*="Impagina"] {
            display: none !important;
            visibility: hidden !important;
        }
        """)

    admin_link_hide_css = "\n".join(hide_css_parts)

    st.markdown(
        f"""
        <style>
        /* ============================================================
           Riattiva la sidebar (custom.css la nasconde di default per
           evitare flash sulla pagina di login). enforce_sidebar_visibility()
           viene chiamato SOLO per utenti autenticati.
           ============================================================ */
        [data-testid="stSidebar"] {{
            display: flex !important;
            visibility: visible !important;
        }}

        /* ============================================================
           Sidebar nav divisori per blocchi:
             HOME
             ───
             📝 Testo · 🎨 Stile · 👥 Personaggi · 🖼 Genera · 📐 Impagina
             ───
             ⭐ KIDS    (solo admin + role kids)
             ───
             ⚙️ Account
             ───
             🛠 Admin   (solo admin)

           Indici DOM degli item (1-based con KIDS file 06_):
             1=HOME, 2=Testo, 3=Stile, 4=Personaggi, 5=Genera,
             6=Impagina, 7=KIDS, 8=Account, 9=Admin

           Border-top su 2 (sotto HOME), 7 (sopra KIDS),
           8 (sopra Account), 9 (sopra Admin). I CSS sui nav item
           nascosti (display:none) non causano visual issues.
           ============================================================ */
        [data-testid="stSidebarNavItems"] > *:nth-child(2),
        [data-testid="stSidebarNavItems"] > *:nth-child(7),
        [data-testid="stSidebarNavItems"] > *:nth-child(8),
        [data-testid="stSidebarNavItems"] > *:nth-child(9) {{
            border-top: 1px solid #1E2436 !important;
            padding-top: 8px !important;
            margin-top: 8px !important;
        }}

        /* ============================================================
           Sidebar SEMPRE visibile, qualunque sia lo stato aria-expanded.
           Sovrascrive il CSS dell'agente che può applicarci transform
           translateX(-100%) per "nasconderla".
           ============================================================ */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"][aria-expanded="false"],
        [data-testid="stSidebar"][aria-expanded="true"] {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: translateX(0) !important;
            min-width: 244px !important;
            max-width: 244px !important;
            width: 244px !important;
            pointer-events: auto !important;
            position: relative !important;
            margin-left: 0 !important;
        }}

        {admin_link_hide_css}

        /* Contenuto interno deve essere visibile anche se aria-expanded=false */
        [data-testid="stSidebarContent"] {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }}

        /* ============================================================
           Nascondi pulsante "chiudi sidebar" interno.
           Selettori multipli per compat tra versioni Streamlit.
           ============================================================ */
        [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"],
        [data-testid="stSidebar"] [data-testid="baseButton-header"],
        [data-testid="stSidebar"] button[kind="header"],
        [data-testid="stSidebarHeader"] button,
        [data-testid="stSidebarUserContent"] > div:first-child > button {{
            display: none !important;
        }}

        /* ============================================================
           Nascondi anche il toggle "apri sidebar" in alto (non serve
           più, la sidebar è sempre aperta).
           ============================================================ */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
