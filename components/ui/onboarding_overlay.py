"""
OnboardingOverlay — overlay onboarding a 3 step.
design: card centrata con step indicator, titolo, descrizione e CTA
"""
from __future__ import annotations
import streamlit as st


_STEPS = [
    {
        "title": "Dal testo al fumetto",
        "desc": "Carica un racconto, un'idea o anche solo una scena. La sceneggiatura la scriviamo insieme.",
        "icon": "📝",
    },
    {
        "title": "Stile e personaggi",
        "desc": "Scegli uno stile visivo. Crea il cast del fumetto. Le immagini di riferimento garantiscono coerenza.",
        "icon": "🎨",
    },
    {
        "title": "Genera e impagina",
        "desc": "Le vignette vengono generate una per una. Le impagini su pagina e le esporti in PDF.",
        "icon": "🖼",
    },
]


def render_onboarding_overlay(step: int = 1) -> tuple[bool, bool]:
    """
    Renderizza l'overlay onboarding.

    Params:
        step: Step corrente (1, 2 o 3).

    Returns:
        (skip_clicked, complete_clicked) — tuple di bool.
        complete_clicked è True solo quando si è all'ultimo step.
    """
    step_data = _STEPS[min(step - 1, 2)]
    is_last = step == 3

    dots_html = "".join(
        f'<div class="snaptoon-onboarding__dot'
        f'{" snaptoon-onboarding__dot--active" if i + 1 == step else ""}'
        f'"></div>'
        for i in range(3)
    )

    st.markdown(
        f"""
        <div class="snaptoon-onboarding">
          <div class="snaptoon-onboarding__step">Passo {step} di 3</div>
          <div style="font-size:3rem;margin-bottom:.5rem;">{step_data['icon']}</div>
          <div class="snaptoon-onboarding__title">{step_data['title']}</div>
          <div class="snaptoon-onboarding__desc">{step_data['desc']}</div>
          <div class="snaptoon-onboarding__dots">{dots_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col_cta, _ = st.columns([1, 2, 1])
    with col_cta:
        if is_last:
            complete = st.button(
                "Inizia con un progetto demo",
                key="_ui_onboarding_complete",
                type="primary",
                use_container_width=True,
            )
        else:
            complete = st.button(
                "Continua →",
                key=f"_ui_onboarding_next_{step}",
                type="primary",
                use_container_width=True,
            )

    _, col_skip, _ = st.columns([1, 2, 1])
    with col_skip:
        skip = st.button(
            "Salta tutorial",
            key="_ui_onboarding_skip",
            use_container_width=True,
        )

    return skip, complete
