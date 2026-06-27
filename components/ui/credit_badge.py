"""
CreditBadge — badge crediti nella sidebar.
design: componente crediti con barra progresso e stati colorati
"""
from __future__ import annotations
import streamlit as st


def render_credit_badge(current: int, total: int, plan_name: str) -> bool:
    """
    Renderizza il badge crediti in sidebar.
    Restituisce True se l'utente ha cliccato (per navigare a Crediti & Account).

    Params:
        current:   Crediti rimasti.
        total:     Crediti totali del piano.
        plan_name: Nome del piano (es. "Creator").
    """
    if total <= 0:
        ratio = 0.0
    else:
        ratio = max(0.0, min(1.0, current / total))

    if ratio == 0:
        state_class = "snaptoon-credit-badge--empty"
        bar_class = "snaptoon-credit-badge__bar-fill--empty"
        bar_pct = 2
    elif ratio < 0.10:
        state_class = "snaptoon-credit-badge--low"
        bar_class = "snaptoon-credit-badge__bar-fill--low"
        bar_pct = max(2, int(ratio * 100))
    else:
        state_class = ""
        bar_class = "snaptoon-credit-badge__bar-fill--ok"
        bar_pct = int(ratio * 100)

    html = f"""
    <div class="snaptoon-credit-badge {state_class}">
      <div class="snaptoon-credit-badge__header">
        <span>💳 Crediti</span>
        <span class="snaptoon-badge snaptoon-badge--gray">{plan_name}</span>
      </div>
      <div class="snaptoon-credit-badge__value">{current:,} / {total:,}</div>
      <div class="snaptoon-credit-badge__bar-track">
        <div class="snaptoon-credit-badge__bar-fill {bar_class}"
             style="width: {bar_pct}%"></div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    clicked = st.button(
        "Gestisci →",
        key="_ui_credit_badge_nav",
        use_container_width=True,
        type="secondary",
    )
    return clicked
