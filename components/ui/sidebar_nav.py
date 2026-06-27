"""
SidebarNav — navigazione sidebar + logo SnapToon.
design: sidebar con logo, selettore progetto, nav, credit badge, account
"""
from __future__ import annotations
import streamlit as st


_NAV_PAGES: list[tuple[str, str]] = [
    ("📝", "Testo"),
    ("🎨", "Stile"),
    ("👥", "Personaggi"),
    ("🖼", "Genera"),
    ("📐", "Impagina"),
]


def render_sidebar_logo() -> None:
    """Wordmark SnapToon in cima alla sidebar."""
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


def render_sidebar_nav(current_page: str, is_admin: bool = False) -> None:
    """
    Renderizza la navigazione nella sidebar.

    Params:
        current_page: Nome della pagina corrente (es. "Genera").
        is_admin:     Se True, aggiunge la voce Admin in fondo.
    """
    render_sidebar_logo()

    st.markdown(
        '<div class="snaptoon-sidebar-section">Navigazione</div>',
        unsafe_allow_html=True,
    )

    for icon, name in _NAV_PAGES:
        label = f"{icon} {name}"
        is_current = name.lower() == current_page.lower()
        if is_current:
            st.markdown(
                f"""
                <div style="
                  padding: 10px 20px;
                  margin: 2px 8px;
                  border-radius: 6px;
                  font-size: 14px;
                  font-weight: 600;
                  color: #F59E0B;
                  background: #1A2035;
                  border-left: 3px solid #F59E0B;
                  padding-left: 17px;
                ">{label}</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.page_link(f"pages/{name.lower()}.py", label=label)

    st.markdown('<div style="margin: 0.75rem 0;"><hr style="border-color:#1E2436;margin:0;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="snaptoon-sidebar-section">Account</div>',
        unsafe_allow_html=True,
    )

    st.page_link("pages/crediti.py", label="💳 Crediti & Account")

    if is_admin:
        st.page_link("pages/admin.py", label="🛠 Admin")
