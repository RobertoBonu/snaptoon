"""SnapToon — entry point Streamlit.

Lancia con:  streamlit run app.py

Questo è il file principale dell'app. La logica di autenticazione, sessione,
e caricamento del progetto attivo vive qui. Le pagine specifiche sono in
`pages/`.

REPLIT_AGENT: puoi modificare lo strato visivo (markup, layout, header),
NON la logica delle funzioni auth_required, load_session, ecc. Vedi
docs/design/07_REPLIT_AGENT.md.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="SnapToon",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PLACEHOLDER — Settimana 1
# Questo file verrà popolato durante lo sviluppo del backend (auth, DB).
# Per ora mostra solo un saluto in modo che Replit Agent possa cominciare
# a lavorare sul theme.
# ============================================================

st.title("SnapToon")
st.caption("Dall'idea al fumetto, in uno snap.")

st.markdown(
    """
    ---

    ### 🚧 In costruzione

    L'app è in fase di sviluppo iniziale.

    - Backend (auth, DB, billing): in arrivo da Claude
    - Design (theme, palette, layout): in arrivo da Replit Agent

    Vedi `docs/design/` per le specifiche complete.
    """
)

with st.sidebar:
    st.markdown("**SnapToon**")
    st.caption("MVP in costruzione")
