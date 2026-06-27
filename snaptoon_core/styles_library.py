"""Libreria di 96 style preset.

I dati vivono in `core/library_data/styles.md` (copia del file ufficiale
della skill `visual-prompt-engine`). Questo modulo lo parsa a runtime e
fornisce un'API pulita per cercare/applicare i preset nello Style YAML.

Ogni preset ha:
  - id (slug)
  - label (nome originale per la UI)
  - category (fumetto | illustrazione | fotografia | cinema | kids | fotografia_autore)
  - expansion (paragrafo inglese da inserire verbatim nel prompt)
  - is_handmade (bool — se True, il prompt riceve il media-authenticity layer
    anti-AI-look della skill)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

LIBRARY_FILE = Path(__file__).resolve().parent / "library_data" / "styles.md"
CUSTOM_LIBRARY_FILE = Path(__file__).resolve().parent / "library_data" / "styles_custom.md"

CATEGORY_LABELS: dict[str, str] = {
    "personali": "🎨 I miei stili",
    "fumetto": "Fumetto",
    "illustrazione": "Illustrazione",
    "fotografia": "Fotografia",
    "cinema": "Cinema",
    "kids": "Kids",
    "fotografia_autore": "Fotografia d'autore",
}

# Keywords che identificano stili hand-made / analog → attivano il media
# authenticity layer anti-AI-look della skill visual-prompt-engine.
_HANDMADE_KEYWORDS = (
    "watercolor", "acquerello", "gouache", "oil paint", "oil painting",
    "ink wash", "brush and ink", "ink expressionism", "ink illustration",
    "charcoal", "pencil", "crayon", "pastel",
    "engraving", "crosshatch", "etching",
    "risograph", "screenprint", "silkscreen",
    "watercolor washes", "ink crosshatching",
)


@dataclass(frozen=True)
class StylePreset:
    id: str
    label: str
    category: str
    expansion: str
    is_handmade: bool
    extra_negative_terms: tuple[str, ...] = ()
    is_custom: bool = False  # True per stili personali dell'utente


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s or "unnamed"


def _category_from_heading(heading: str) -> str:
    """Mappa intestazioni '## Fumetto (20)' → 'fumetto'."""
    name = heading.split("(")[0].strip().lower()
    if name.startswith("fotografia d"):
        return "fotografia_autore"
    if name == "personali":
        return "personali"
    return name


def _is_handmade(expansion: str) -> bool:
    text = expansion.lower()
    return any(kw in text for kw in _HANDMADE_KEYWORDS)


def _parse_md_file(text: str, is_custom: bool = False) -> list[StylePreset]:
    """Parsa un file markdown nel formato di styles.md / styles_custom.md.

    Riconosce:
    - `## Categoria` per le sezioni
    - `### Nome stile` per i singoli preset
    - `**NEGATIVE:** termine, termine` come riga opzionale subito sotto
      l'espansione (per stili custom)
    """
    presets: list[StylePreset] = []
    current_category: str | None = None
    current_label: str | None = None
    current_expansion_lines: list[str] = []
    current_negative: tuple[str, ...] = ()

    def _flush():
        nonlocal current_label, current_expansion_lines, current_negative
        if current_label and current_category:
            # Estrai eventuale riga **NEGATIVE:** dall'espansione
            expansion_clean_lines: list[str] = []
            negative_terms: tuple[str, ...] = current_negative
            for line in current_expansion_lines:
                stripped = line.strip()
                if stripped.upper().startswith("**NEGATIVE:**") or stripped.upper().startswith("NEGATIVE:"):
                    # Estrai termini
                    val = stripped.split(":", 1)[1].strip()
                    # Rimuovi eventuali ** rimasti
                    val = val.replace("**", "").strip()
                    terms = tuple(t.strip() for t in val.split(",") if t.strip())
                    negative_terms = negative_terms + terms
                else:
                    expansion_clean_lines.append(line)
            expansion = "\n".join(expansion_clean_lines).strip()
            if expansion:
                presets.append(StylePreset(
                    id=_slugify(current_label),
                    label=current_label,
                    category=current_category,
                    expansion=expansion,
                    is_handmade=_is_handmade(expansion),
                    extra_negative_terms=negative_terms,
                    is_custom=is_custom,
                ))
        current_label = None
        current_expansion_lines = []
        current_negative = ()

    in_toc = False
    for line in text.splitlines():
        # Sezioni categoria
        if line.startswith("## "):
            _flush()
            heading = line[3:].strip()
            if heading.lower().startswith(("table of contents",)):
                in_toc = True
                current_category = None
            elif heading.startswith("Style library"):
                current_category = None
            else:
                in_toc = False
                current_category = _category_from_heading(heading)
            continue
        if line.startswith("### "):
            _flush()
            current_label = line[4:].strip()
            continue
        if current_label and current_category and not in_toc:
            if line.strip().startswith("**Important:**"):
                continue
            if line.strip() == "---":
                _flush()
                continue
            current_expansion_lines.append(line)

    _flush()
    return presets


@lru_cache(maxsize=1)
def _load_all() -> tuple[StylePreset, ...]:
    """Carica preset ufficiali + custom dell'utente. Custom in cima."""
    all_presets: list[StylePreset] = []

    # Prima i custom (così appaiono in cima nella categoria "personali")
    if CUSTOM_LIBRARY_FILE.exists():
        text = CUSTOM_LIBRARY_FILE.read_text(encoding="utf-8")
        all_presets.extend(_parse_md_file(text, is_custom=True))

    # Poi gli ufficiali
    if LIBRARY_FILE.exists():
        text = LIBRARY_FILE.read_text(encoding="utf-8")
        all_presets.extend(_parse_md_file(text, is_custom=False))

    return tuple(all_presets)


def reload_library() -> None:
    """Forza il reload (utile dopo aver modificato styles_custom.md)."""
    _load_all.cache_clear()


def list_presets(category: str | None = None) -> list[StylePreset]:
    """Tutti i preset, opzionalmente filtrati per categoria."""
    all_presets = _load_all()
    if category is None:
        return list(all_presets)
    return [p for p in all_presets if p.category == category]


def get_preset(preset_id: str) -> StylePreset | None:
    for p in _load_all():
        if p.id == preset_id:
            return p
    return None


def count_by_category() -> dict[str, int]:
    out: dict[str, int] = {k: 0 for k in CATEGORY_LABELS}
    for p in _load_all():
        out[p.category] = out.get(p.category, 0) + 1
    return out


# ============================================================
# Media authenticity layer (anti-AI-look) — dalla skill visual-prompt-engine
# ============================================================

MEDIA_AUTHENTICITY_CLAUSE = (
    "MEDIA AUTHENTICITY — Render as a genuine hand-made original on paper, "
    "not a digital imitation. Show real material behavior: individual visible "
    "brush strokes, pigment granulation settling into the paper tooth, washes "
    "that pool, bloom and bleed unevenly at the edges, a few hard edges where "
    "the paint dried, visible paper grain and the slight warp of wet paper, "
    "natural asymmetry and small honest imperfections. Keep it loose and "
    "economical — let areas of paper breathe rather than filling every inch. "
    "Avoid the digital tells: no airbrushed smoothness, no plastic or waxy "
    "sheen, no over-rendered uniform micro-detail, no HDR glow, no "
    "oversaturated colors, no perfectly clean gradients, no uncanny symmetry."
)

# Negative prompt addizionale per stili hand-made (utile per Midjourney/SD,
# ignorato da gpt-image/Gemini ma incluso comunque per ridondanza testuale).
HANDMADE_NEGATIVE_TERMS = (
    "3d render", "cgi", "plastic", "airbrushed", "over-rendered",
    "hyperdetailed", "hdr", "oversaturated", "smooth digital gradient",
    "glossy sheen", "waxy", "uncanny symmetry", "deep-fried detail",
    "sticker look",
)
