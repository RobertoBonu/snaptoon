"""
GridPicker — selettore gabbia pagina (layout vignette).
design: thumbnail gabbia + selectbox + warning capienza
"""
from __future__ import annotations
import streamlit as st


_GRID_OPTIONS: list[tuple[str, int]] = [
    ("1×1 — 1 vignetta",  1),
    ("1×2 — 2 vignette",  2),
    ("2×1 — 2 vignette",  2),
    ("2×2 — 4 vignette",  4),
    ("2×3 — 6 vignette",  6),
    ("3×2 — 6 vignette",  6),
    ("3×3 — 9 vignette",  9),
    ("Strip 3 — 3 strip",  3),
    ("Strip 4 — 4 strip",  4),
    ("Copertina",          1),
]


def render_grid_picker(
    current_grid_id: str,
    n_panels: int,
    is_saved: bool,
    page_index: int = 0,
) -> tuple[bool, bool]:
    """
    Renderizza il GridPicker per una pagina.

    Params:
        current_grid_id: ID gabbia attuale (es. "2×3").
        n_panels:        Numero di vignette effettive.
        is_saved:        Se la gabbia è già stata salvata.
        page_index:      Per chiavi univoche.

    Returns:
        (saved, adapted) — bool per "Salva gabbia" e "Adatta formati".
    """
    key_pfx = f"_ui_grid_{page_index}"

    col_thumb, col_ctrl = st.columns([1, 2])

    with col_thumb:
        st.markdown(
            f"""
            <div class="snaptoon-grid-picker__thumbnail">
              <span style="text-align:center;padding:.5rem;">
                {current_grid_id}<br>
                <span style="font-size:10px;color:#475569;">anteprima gabbia</span>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ctrl:
        grid_labels = [g[0] for g in _GRID_OPTIONS]
        grid_capacities = {g[0]: g[1] for g in _GRID_OPTIONS}

        current_match = next(
            (i for i, g in enumerate(_GRID_OPTIONS) if current_grid_id in g[0]),
            0,
        )

        selected_label = st.selectbox(
            "Gabbia",
            options=grid_labels,
            index=current_match,
            key=f"{key_pfx}_sel",
            label_visibility="collapsed",
        )

        selected_capacity = grid_capacities.get(selected_label, 0)
        if selected_capacity != n_panels:
            st.warning(
                f"⚠️ Capienza mismatch: gabbia per {selected_capacity} vignette, "
                f"hai {n_panels} vignette."
            )

        col_s, col_a = st.columns(2)
        with col_s:
            saved = st.button(
                "💾 Salva gabbia",
                key=f"{key_pfx}_save",
                type="primary",
                use_container_width=True,
            )
        with col_a:
            adapted = st.button(
                "📐 Adatta formati vignette",
                key=f"{key_pfx}_adapt",
                use_container_width=True,
            )

    if is_saved:
        st.caption("✓ Gabbia salvata.")

    return saved, adapted
