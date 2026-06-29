"""Helper UI condivisi tra app.py e pages/*.py.

Centralizza override CSS necessari per garantire usabilità della UI
quando il design system custom dell'agente nasconde elementi critici.
"""

from __future__ import annotations

import streamlit as st


# ============================================================
# Sidebar nav manuale (Streamlit multipage nativo è disabilitato
# via .streamlit/config.toml → client.showSidebarNavigation = false)
# ============================================================

# Ordine dei link: HOME, Testo, Stile, Personaggi, Genera, Impagina,
# KIDS, Account, Admin. I divisori sono inseriti come markdown <hr>.

_PAGE_LABELS = {
    "app.py": ("🏠", "Home"),
    "pages/01_📝_Testo.py": ("📝", "Testo"),
    "pages/02_🎨_Stile.py": ("🎨", "Stile"),
    "pages/03_👥_Personaggi.py": ("👥", "Personaggi"),
    "pages/04_🖼_Genera.py": ("🖼", "Genera"),
    "pages/05_📐_Impagina.py": ("📐", "Impagina"),
    "pages/06_⭐_KIDS.py": ("⭐", "KIDS"),
    "pages/89_⚙️_Account.py": ("⚙️", "Account"),
    "pages/99_🛠_Admin.py": ("🛠", "Admin"),
}


def _divider() -> None:
    st.sidebar.markdown(
        "<hr style='border:none;border-top:1px solid #1E2436;margin:8px 8px;'/>",
        unsafe_allow_html=True,
    )


def show_page_loading(message: str = "Caricamento...") -> "st._DeltaGenerator":
    """Mostra un loading overlay centrato con spinner animato.

    Da chiamare PRIMA degli import pesanti del backend, così l'utente vede
    subito feedback visivo invece di una pagina bianca. Streamlit invia
    questo render al browser via WebSocket, e il messaggio appare DURANTE
    gli import successivi (i 3s di caricamento backend).

    Returns:
        Il placeholder `st.empty()` su cui chiamare `.empty()` quando hai
        finito di caricare per nascondere il loader.

    Esempio:
        loader = show_page_loading("Apriamo i tuoi libretti...")
        # ... import pesanti ...
        loader.empty()  # nasconde il loader, l'utente vede il contenuto
    """
    placeholder = st.empty()
    placeholder.markdown(
        f"""
        <style>
        @keyframes _snaptoon_spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        @keyframes _snaptoon_pulse {{
            0%, 100% {{ opacity: 0.6; }}
            50% {{ opacity: 1; }}
        }}
        .snaptoon-loader-wrap {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #0D1017;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 24px;
            z-index: 9999;
        }}
        .snaptoon-loader-spinner {{
            width: 56px;
            height: 56px;
            border: 4px solid #1E2436;
            border-top-color: #F59E0B;
            border-radius: 50%;
            animation: _snaptoon_spin 0.9s linear infinite;
        }}
        .snaptoon-loader-text {{
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 500;
            animation: _snaptoon_pulse 1.6s ease-in-out infinite;
        }}
        .snaptoon-loader-brand {{
            position: absolute;
            top: 24px;
            color: #F59E0B;
            font-family: 'Inter', sans-serif;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 0.05em;
        }}
        </style>
        <div class="snaptoon-loader-wrap">
            <div class="snaptoon-loader-brand">📚 SnapToon</div>
            <div class="snaptoon-loader-spinner"></div>
            <div class="snaptoon-loader-text">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return placeholder


def render_sidebar_nav(user) -> None:
    """Costruisce la sidebar nav manualmente per un utente autenticato.

    Usa Material Icons come icone (st.page_link icon=":material/...:")
    per ottenere lo stesso look line-style del custom.css originale,
    senza dipendere dalla sidebar nativa di Streamlit (che farebbe
    lampeggiare sul login).

    Filtra i link in base al ruolo:
    - role=kids → solo HOME + KIDS + Account
    - admin    → tutto (incluso Admin + KIDS)
    - altri    → tutto tranne KIDS + Admin

    Chiamare DOPO che è stato verificato che l'utente è loggato.
    """
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    is_admin = bool(getattr(user, "is_admin", False))
    is_kids = (role_val == "kids")

    with st.sidebar:
        # Blocco 1 — Home
        st.page_link("app.py", label="Home", icon=":material/home:")

        # Blocco 2 — Flusso standard (non kids)
        if not is_kids:
            _divider()
            st.page_link("pages/01_📝_Testo.py", label="Testo", icon=":material/edit:")
            st.page_link("pages/02_🎨_Stile.py", label="Stile", icon=":material/palette:")
            st.page_link("pages/03_👥_Personaggi.py", label="Personaggi", icon=":material/group:")
            st.page_link("pages/04_🖼_Genera.py", label="Genera", icon=":material/image:")
            st.page_link("pages/05_📐_Impagina.py", label="Impagina", icon=":material/dashboard:")

        # Blocco 3 — KIDS (admin + role kids)
        if is_admin or is_kids:
            _divider()
            st.page_link("pages/06_⭐_KIDS.py", label="KIDS", icon=":material/star:")

        # Blocco 4 — Account (sempre)
        _divider()
        st.page_link("pages/89_⚙️_Account.py", label="Account", icon=":material/settings:")

        # Blocco 5 — Admin (solo admin)
        if is_admin:
            _divider()
            st.page_link("pages/99_🛠_Admin.py", label="Admin", icon=":material/build:")


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
