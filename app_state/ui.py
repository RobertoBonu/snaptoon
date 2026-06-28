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
    st.markdown(
        """
        <style>
        /* ============================================================
           Sidebar SEMPRE visibile, qualunque sia lo stato aria-expanded.
           Sovrascrive il CSS dell'agente che può applicarci transform
           translateX(-100%) per "nasconderla".
           ============================================================ */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"][aria-expanded="false"],
        [data-testid="stSidebar"][aria-expanded="true"] {
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
        }

        /* Contenuto interno deve essere visibile anche se aria-expanded=false */
        [data-testid="stSidebarContent"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        /* ============================================================
           Nascondi pulsante "chiudi sidebar" interno.
           Selettori multipli per compat tra versioni Streamlit.
           ============================================================ */
        [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"],
        [data-testid="stSidebar"] [data-testid="baseButton-header"],
        [data-testid="stSidebar"] button[kind="header"],
        [data-testid="stSidebarHeader"] button,
        [data-testid="stSidebarUserContent"] > div:first-child > button {
            display: none !important;
        }

        /* ============================================================
           Nascondi anche il toggle "apri sidebar" in alto (non serve
           più, la sidebar è sempre aperta).
           ============================================================ */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
