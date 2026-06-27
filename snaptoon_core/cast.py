"""Archivio Cast — personaggi riusabili tra progetti.

Ogni personaggio è un file YAML in core/cast_data/<slug>.yaml.
È una sorta di "anagrafica" cross-progetto: l'utente può creare un
personaggio una volta e importarlo in più progetti senza riscrivere
descrizione e palette.

I file qui sono globali (template), non per-progetto.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CAST_DIR = Path(__file__).resolve().parent / "cast_data"


class CastEntry(BaseModel):
    """Voce dell'archivio cast."""

    name: str
    visual_description: str = ""
    color_palette: str = ""
    notes: str = Field(
        default="",
        description="Note opzionali: stile preferito, origine, riferimenti.",
    )


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "unnamed"


def cast_file_path(name: str) -> Path:
    return CAST_DIR / f"{_slug(name)}.yaml"


def list_cast() -> list[CastEntry]:
    """Tutte le voci dell'archivio, ordinate per nome."""
    CAST_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[CastEntry] = []
    for f in sorted(CAST_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            entries.append(CastEntry.model_validate(data))
        except Exception:
            continue
    return sorted(entries, key=lambda e: e.name.lower())


def save_cast_entry(entry: CastEntry) -> Path:
    """Salva o aggiorna una voce. La chiave è il nome (case-insensitive)."""
    CAST_DIR.mkdir(parents=True, exist_ok=True)
    path = cast_file_path(entry.name)
    path.write_text(
        yaml.safe_dump(
            entry.model_dump(),
            sort_keys=False,
            allow_unicode=True,
            width=100,
        ),
        encoding="utf-8",
    )
    return path


def delete_cast_entry(name: str) -> bool:
    path = cast_file_path(name)
    if path.exists():
        path.unlink()
        return True
    return False


def migrate_legacy_to_cast() -> int:
    """Migra i personaggi nel vecchio formato (Style.characters) all'archivio cast.

    Idempotente: deduplica per nome (case-insensitive). Dopo la migrazione,
    salva gli stili (che con model_dump escludono il campo legacy `characters`),
    così l'avviso "legacy" non comparirà più.

    Ritorna il numero di voci migrate (nuove).
    """
    # Import qui per evitare cicli
    from .styles import list_styles, Style

    existing_names = {e.name.lower() for e in list_cast()}
    migrated = 0
    styles_with_legacy: list[Style] = []

    for style_id in list_styles():
        try:
            style = Style.load(style_id)
        except Exception:
            continue
        legacy = style.legacy_characters
        if not legacy:
            continue
        for char in legacy:
            key = char.name.lower()
            if key in existing_names:
                continue
            save_cast_entry(CastEntry(
                name=char.name,
                visual_description=char.visual_description,
                color_palette=char.color_palette,
                notes=f"Migrato da stile «{style.name}»",
            ))
            existing_names.add(key)
            migrated += 1
        styles_with_legacy.append(style)

    # Pulisce gli stili: `style.save()` usa model_dump che esclude il campo
    # legacy `characters`. Salvo solo se c'erano legacy (per non riscrivere file
    # inutilmente).
    for style in styles_with_legacy:
        try:
            style.save()
        except Exception:
            continue

    return migrated
