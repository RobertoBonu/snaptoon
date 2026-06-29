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
    try:
        from auth.sessions import current_user as _current_user
        from db.session import session_scope as _session_scope
        with _session_scope() as _s:
            _u = _current_user(_s)
            if _u is not None:
                is_admin = _u.is_admin
                # Aggiorna cache (per coerenza con altri consumer)
                st.session_state["snaptoon_user_is_admin"] = is_admin
    except Exception:
        pass

    # Nasconde gli ultimi N nav items per role:
    # - non-admin: nascondi solo "Admin" (ultimo, file 99_🛠_Admin.py)
    # - admin: nessun nav nascosto
    admin_link_hide_css = ""
    if not is_admin:
        admin_link_hide_css = """
        /* Nascondi il link Admin (ultimo nav item, file 99_🛠_Admin.py)
           per gli utenti che non hanno role=admin. Usa multipli selettori
           per robustezza tra versioni Streamlit. */
        [data-testid="stSidebarNavItems"] > *:last-child,
        [data-testid="stSidebarNav"] > ul > li:last-child,
        [data-testid="stSidebarNavItems"] a[href*="Admin"],
        [data-testid="stSidebarNav"] a[href*="Admin"] {
            display: none !important;
            visibility: hidden !important;
        }
        """

    st.markdown(
        f"""
        <style>
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
