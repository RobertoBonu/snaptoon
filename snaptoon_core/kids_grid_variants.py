"""Ritmi (grid variants) alternativi per libretti KIDS.

Ogni libretto KIDS può essere generato con uno di 6 "ritmi" per lunghezza,
scelti casualmente al momento della creazione. Questo evita che tutti i
libretti abbiano la stessa impaginazione e dà varietà cinematografica.

L'utente non sceglie il ritmo (KIDS è pensato per essere semplice), ma
il ritmo scelto viene esposto come piccolo tag informativo nella
dashboard del libretto.

Ogni ritmo è una sequenza di grid_id (da snaptoon_core.layout.GRIDS):
  - splash: 1 vignetta full-page
  - 1+2: 1 grande sopra + 2 piccole sotto (3 pannelli)
  - 2x2: griglia 2x2 (4 pannelli)

I ritmi differiscono per densità di pannelli, alternanza splash/griglia,
e punto di ingresso (partire con splash "poster" o direttamente in
medias res).
"""
from __future__ import annotations

import random
from typing import TypedDict


class GridVariant(TypedDict):
    slug: str
    label: str
    description: str
    grid_distribution: list[str]


# ============================================================
# BREVE (4 pagine interne)
# ============================================================

BREVE_VARIANTS: dict[str, GridVariant] = {
    "classico": {
        "slug": "classico",
        "label": "Classico",
        "description": "Apertura poster, dialogo, azione, chiusura poster",
        "grid_distribution": ["splash", "1+2", "2x2", "splash"],
    },
    "cinematografico": {
        "slug": "cinematografico",
        "label": "Cinematografico",
        "description": "Apertura, azione veloce, dialogo, chiusura",
        "grid_distribution": ["splash", "2x2", "1+2", "splash"],
    },
    "serrato": {
        "slug": "serrato",
        "label": "Serrato",
        "description": "Poster + due griglie fitte + poster (più vignette)",
        "grid_distribution": ["splash", "2x2", "2x2", "splash"],
    },
    "contemplativo": {
        "slug": "contemplativo",
        "label": "Contemplativo",
        "description": "Meno vignette, respiro fiabesco, molti dialoghi",
        "grid_distribution": ["splash", "1+2", "1+2", "splash"],
    },
    "twist": {
        "slug": "twist",
        "label": "Twist",
        "description": "Apre in medias res col dialogo, non col poster",
        "grid_distribution": ["1+2", "splash", "2x2", "splash"],
    },
    "serial": {
        "slug": "serial",
        "label": "Serial",
        "description": "Tre poster sequenziali all'inizio, ritmo iconico",
        "grid_distribution": ["splash", "splash", "2x2", "splash"],
    },
}


# ============================================================
# LUNGO (14 pagine interne)
# ============================================================

LUNGO_VARIANTS: dict[str, GridVariant] = {
    "classico": {
        "slug": "classico",
        "label": "Classico",
        "description": "3 poster strategici, alternanza equilibrata",
        "grid_distribution": [
            "splash",  # 1 apertura
            "1+2", "1+2",  # 2-3 setup dialogato
            "2x2", "2x2",  # 4-5 sviluppo
            "splash",  # 6 climax 1
            "2x2", "2x2",  # 7-8
            "1+2",  # 9
            "2x2", "2x2",  # 10-11
            "1+2",  # 12
            "splash",  # 13 climax 2
            "splash",  # 14 finale
        ],
    },
    "cinematografico": {
        "slug": "cinematografico",
        "label": "Cinematografico",
        "description": "Molti poster splash, ritmo da film d'animazione",
        "grid_distribution": [
            "splash",  # 1
            "1+2",  # 2
            "splash",  # 3
            "2x2",  # 4
            "splash",  # 5
            "2x2", "2x2",  # 6-7
            "splash",  # 8
            "1+2", "1+2",  # 9-10
            "splash",  # 11
            "2x2",  # 12
            "splash",  # 13
            "splash",  # 14 finale
        ],
    },
    "serrato": {
        "slug": "serrato",
        "label": "Serrato",
        "description": "Molte griglie fitte, poche pause, azione densa",
        "grid_distribution": [
            "splash",  # 1
            "2x2", "2x2", "2x2",  # 2-4 azione fitta
            "1+2",  # 5 respiro
            "2x2", "2x2", "2x2",  # 6-8
            "1+2",  # 9
            "2x2", "2x2",  # 10-11
            "1+2",  # 12
            "2x2",  # 13
            "splash",  # 14 finale
        ],
    },
    "contemplativo": {
        "slug": "contemplativo",
        "label": "Contemplativo",
        "description": "Molte pagine dialogate, ritmo lento fiabesco",
        "grid_distribution": [
            "splash",  # 1
            "1+2", "1+2", "1+2",  # 2-4 dialoghi
            "2x2",  # 5 azione
            "splash",  # 6
            "1+2", "1+2",  # 7-8 dialoghi
            "2x2",  # 9
            "1+2", "1+2",  # 10-11
            "splash",  # 12
            "1+2",  # 13
            "splash",  # 14 finale
        ],
    },
    "twist": {
        "slug": "twist",
        "label": "Twist",
        "description": "Apre in medias res, poster centrale forte",
        "grid_distribution": [
            "1+2",  # 1 in medias res
            "2x2", "2x2",  # 2-3
            "splash",  # 4 riveal
            "1+2", "1+2",  # 5-6
            "2x2", "2x2",  # 7-8
            "splash",  # 9 climax
            "2x2",  # 10
            "1+2", "1+2",  # 11-12
            "splash",  # 13
            "splash",  # 14 finale
        ],
    },
    "serial": {
        "slug": "serial",
        "label": "Serial",
        "description": "Poster iniziali multipli, tipo prima pagina fumetto",
        "grid_distribution": [
            "splash", "splash",  # 1-2 doppio poster apertura
            "1+2",  # 3
            "2x2", "2x2",  # 4-5
            "splash",  # 6
            "1+2",  # 7
            "2x2", "2x2", "2x2",  # 8-10
            "1+2",  # 11
            "splash",  # 12
            "2x2",  # 13
            "splash",  # 14 finale
        ],
    },
}


ALL_VARIANTS: dict[str, dict[str, GridVariant]] = {
    "breve": BREVE_VARIANTS,
    "lungo": LUNGO_VARIANTS,
}


def pick_random_variant(length_target: str) -> GridVariant:
    """Sceglie un ritmo casuale per la lunghezza data.

    length_target: "breve" | "lungo" (case-insensitive)

    Fallback: "classico" se length_target non è tra quelli conosciuti.
    """
    key = length_target.lower().strip()
    pool = ALL_VARIANTS.get(key)
    if not pool:
        return BREVE_VARIANTS["classico"]
    return random.choice(list(pool.values()))


def get_variant(length_target: str, slug: str) -> GridVariant | None:
    """Ritorna un ritmo specifico per (length, slug) o None se non esiste."""
    key = length_target.lower().strip()
    pool = ALL_VARIANTS.get(key)
    if not pool:
        return None
    return pool.get(slug)


def get_variant_by_slug_any_length(slug: str) -> GridVariant | None:
    """Cerca il ritmo per slug in entrambe le lunghezze (breve+lungo).

    Utile quando conosciamo solo lo slug salvato ma non la lunghezza.
    """
    for pool in ALL_VARIANTS.values():
        if slug in pool:
            return pool[slug]
    return None
