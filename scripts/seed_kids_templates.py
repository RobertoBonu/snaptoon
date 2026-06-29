"""Seed dei 6 template KIDS.

Esegui DOPO `alembic upgrade head`:
    python scripts/seed_kids_templates.py

Idempotente: usa upsert sullo slug.

Schemi:
- Breve (6 pagine, 16 vignette): splash · 1+2 · 2x2 · 1+2 · 2x2 · splash
- Lungo (16 pagine, ~50 vignette): pattern esteso con 3 splash strategici
  (apertura, climax centrale, finale)

3 template per le 2 lunghezze = 6 record totali. La differenza tra "1/2/3
personaggi" influisce SOLO sul prompt Claude (gabbie/scene identiche).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.models import LengthTarget
from db.repos import kids_templates as kids_templates_repo
from db.session import session_scope


# ============================================================
# Distribuzione gabbie + scene
# ============================================================

# 6 pagine — sequenza grid_id
GRIDS_BREVE = ["splash", "1+2", "2x2", "1+2", "2x2", "splash"]

# 16 pagine — sequenza grid_id (con 3 splash strategici)
GRIDS_LUNGO = [
    "splash",  # 1 — apertura
    "1+2", "1+2",  # 2-3 — setup
    "2x2", "2x2",  # 4-5 — sviluppo
    "1+2",  # 6
    "splash",  # 7 — climax 1
    "2x2", "2x2",  # 8-9
    "1+2",  # 10
    "2x2", "2x2",  # 11-12
    "1+2",  # 13
    "splash",  # 14 — climax 2
    "2x2",  # 15
    "splash",  # 16 — finale
]


# Numero di vignette per ogni grid_id (capienza)
GRID_CAPACITY = {"splash": 1, "1+2": 3, "2x2": 4}


def _scene_for_grid(grid_id: str, page_index: int) -> list[dict]:
    """Ritorna scene_params per ogni vignetta di una pagina.

    Pattern:
    - splash: establishing/birds_eye/epico (apertura) o close/eye_level/drammatico (climax)
    - 1+2:
        cella grande → medium / eye_level / allegro (panoramica)
        2 piccole → closeup / eye_level / allegro (reazioni)
    - 2x2:
        ciclico close/medium/close/medium con mood vario
    """
    is_climax = page_index in {6, 13}  # 0-indexed: climax 1 (pag 7) e climax 2 (pag 14)
    is_finale = page_index == 15  # pag 16
    is_opening = page_index == 0  # pag 1

    if grid_id == "splash":
        if is_climax:
            return [{"shot_distance": "closeup", "shot_angle": "low_angle", "mood": "drammatico"}]
        if is_finale:
            return [{"shot_distance": "medium", "shot_angle": "eye_level", "mood": "poetico"}]
        # opening + other splash
        return [{"shot_distance": "establishing", "shot_angle": "birds_eye", "mood": "epico"}]

    if grid_id == "1+2":
        return [
            {"shot_distance": "medium", "shot_angle": "eye_level", "mood": "allegro"},
            {"shot_distance": "closeup", "shot_angle": "eye_level", "mood": "allegro"},
            {"shot_distance": "closeup", "shot_angle": "eye_level", "mood": "sospeso"},
        ]

    if grid_id == "2x2":
        # alterna close/medium per 4 vignette
        return [
            {"shot_distance": "closeup", "shot_angle": "eye_level", "mood": "allegro"},
            {"shot_distance": "medium", "shot_angle": "eye_level", "mood": "sospeso"},
            {"shot_distance": "closeup", "shot_angle": "eye_level", "mood": "drammatico"},
            {"shot_distance": "medium", "shot_angle": "eye_level", "mood": "poetico"},
        ]

    # default fallback
    return [{"shot_distance": None, "shot_angle": None, "mood": None}
            for _ in range(GRID_CAPACITY.get(grid_id, 1))]


def _build_scene_distribution(grids: list[str]) -> list[dict]:
    """Per ogni vignetta nell'ordine in cui appare nei grid, scene params."""
    result = []
    for page_idx, grid_id in enumerate(grids):
        result.extend(_scene_for_grid(grid_id, page_idx))
    return result


# ============================================================
# Definizione dei 6 template
# ============================================================

TEMPLATES = [
    # 1 personaggio
    {
        "slug": "kids_1p_breve",
        "label": "1 personaggio · Breve",
        "n_characters": 1,
        "length_target": LengthTarget.breve,
        "grid_distribution": GRIDS_BREVE,
        "notes": "Focus assoluto su un singolo personaggio. 6 pagine, 16 vignette.",
    },
    {
        "slug": "kids_1p_lungo",
        "label": "1 personaggio · Lungo",
        "n_characters": 1,
        "length_target": LengthTarget.lungo,
        "grid_distribution": GRIDS_LUNGO,
        "notes": "Avventura completa di un singolo personaggio. 16 pagine, ~50 vignette.",
    },
    # 2 personaggi
    {
        "slug": "kids_2p_breve",
        "label": "2 personaggi · Breve",
        "n_characters": 2,
        "length_target": LengthTarget.breve,
        "grid_distribution": GRIDS_BREVE,
        "notes": "Duo di personaggi. Dialoghi 50/50. 6 pagine, 16 vignette.",
    },
    {
        "slug": "kids_2p_lungo",
        "label": "2 personaggi · Lungo",
        "n_characters": 2,
        "length_target": LengthTarget.lungo,
        "grid_distribution": GRIDS_LUNGO,
        "notes": "Storia di due personaggi. 16 pagine, ~50 vignette.",
    },
    # 3 personaggi
    {
        "slug": "kids_3p_breve",
        "label": "3 personaggi · Breve",
        "n_characters": 3,
        "length_target": LengthTarget.breve,
        "grid_distribution": GRIDS_BREVE,
        "notes": "Trio di amici. 6 pagine, 16 vignette.",
    },
    {
        "slug": "kids_3p_lungo",
        "label": "3 personaggi · Lungo",
        "n_characters": 3,
        "length_target": LengthTarget.lungo,
        "grid_distribution": GRIDS_LUNGO,
        "notes": "Avventura di gruppo. 16 pagine, ~50 vignette.",
    },
]


def main() -> None:
    with session_scope() as s:
        for tpl in TEMPLATES:
            grids = tpl["grid_distribution"]
            scenes = _build_scene_distribution(grids)

            kids_templates_repo.upsert(
                s,
                slug=tpl["slug"],
                label=tpl["label"],
                n_characters=tpl["n_characters"],
                length_target=tpl["length_target"],
                grid_distribution=grids,
                scene_distribution=scenes,
                notes=tpl["notes"],
            )

            n_pages = len(grids)
            n_panels = len(scenes)
            print(f"  ✓ {tpl['slug']:25} — {n_pages} pagine · {n_panels} vignette")

    print()
    print("✅ Seed kids_templates completato (6 template).")


if __name__ == "__main__":
    main()
