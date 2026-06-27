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

from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="SnapToon",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS design system
def _inject_css() -> None:
    css_path = Path("style/custom.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

_inject_css()

# ============================================================
# PLACEHOLDER — snaptoon_core non ancora disponibile
# Il file verrà popolato con auth + session quando snaptoon_core
# sarà aggiunto al repo.
# ============================================================

st.title("SnapToon")
st.caption("Dall'idea al fumetto, in uno snap.")

st.markdown(
    """
    ---

    ### 🚧 In costruzione

    L'app è in fase di sviluppo iniziale.

    - **Backend** (auth, DB, billing, snaptoon_core): in arrivo da Claude/Roberto
    - **Design** (theme, palette, layout, componenti): ✅ pronto

    Vedi `docs/design/` per le specifiche complete.
    """
)

with st.sidebar:
    st.markdown("**SnapToon** 🟣")
    st.caption("MVP in costruzione")
    st.divider()
    st.caption("📝 Testo")
    st.caption("🎨 Stile")
    st.caption("👥 Personaggi")
    st.caption("🖼 Genera")
    st.caption("📐 Impagina")
