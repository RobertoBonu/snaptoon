"""Helper UI condivisi tra app.py e pages/*.py.

Centralizza override CSS necessari per garantire usabilità della UI
quando il design system custom dell'agente nasconde elementi critici.
"""

from __future__ import annotations

import streamlit as st


def enforce_sidebar_visibility() -> None:
    """Garantisce che il toggle sidebar resti sempre accessibile.

    Il CSS custom dell'agente nasconde `[data-testid="stHeader"]` per
    pulizia estetica. Quel contenitore però ospita anche il pulsante per
    riaprire la sidebar quando l'utente la chiude. Senza questo override,
    chiudere la sidebar la rende irrecuperabile (vedi bug 28/06/2026).

    Questo override:
    1. Ripristina la visibilità di stHeader (solo per il toggle)
    2. Forza visibilità del toggle nello stato collapsed
    3. NON nasconde il bottone chiudi sidebar (l'utente può chiudere se vuole)

    Da chiamare DOPO inject_css() in ogni pagina.
    """
    st.markdown(
        """
        <style>
        /* Override hide-stHeader del CSS agente: serve a ospitare il toggle. */
        [data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            background: transparent !important;
            height: auto !important;
            min-height: 40px !important;
            pointer-events: auto !important;
        }

        /* Toggle quando la sidebar è collassata (selettori multipli per
           compatibilità tra versioni Streamlit). */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="stHeader"] button,
        [data-testid="stHeader"] [data-testid*="Button"] {
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 9999 !important;
            pointer-events: auto !important;
        }

        /* Bottoni dentro stHeader devono essere cliccabili senza essere
           coperti da altri elementi (es. CSS dell'agente con position fixed). */
        [data-testid="stHeader"] svg {
            color: #E2E8F0 !important;
            fill: currentColor !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
