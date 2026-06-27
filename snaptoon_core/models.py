"""SnapToon — Pydantic models del dominio.

Modelli PURI: nessuna persistenza, nessun I/O. Tutto serializzabile in JSON.
Il layer DB (in db/) li mappa su tabelle SQLAlchemy.

Differenze rispetto a Creative Studio:
- Solo `fumetto` come tipo progetto (niente graphic_novel, niente libro_illustrato)
- Niente campi `book_*` su PageLayout
- Niente metodi save()/load()/migrate() su Project
- `length_target` esplicito (striscia/breve/medio/lungo)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ============================================================
# Enum-like literals
# ============================================================

ProjectLength = Literal["striscia", "breve", "medio", "lungo"]
"""Lunghezza target del progetto. Determina il numero di pagine consigliato
nell'adattamento Claude (`striscia` 1-2, `breve` 3-6, `medio` 8-16, `lungo` 24+)."""

DialogueKind = Literal["FUMETTO", "PENSIERO", "DIDASCALIA", "SFX"]
"""Tipo di dialogo:
- FUMETTO: balloon parlato
- PENSIERO: balloon pensiero (cloud)
- DIDASCALIA: riquadro narrante / voice-over
- SFX: onomatopea / effetto sonoro
"""

BalloonShape = Literal["oval", "rounded_rect", "rect", "cloud", "burst"]


# ============================================================
# Dialoghi
# ============================================================


class Dialogue(BaseModel):
    """Un dialogo singolo dentro una vignetta."""

    kind: DialogueKind
    speaker: str | None = None
    text: str

    # Posizione manuale opzionale: coordinate normalizzate 0-1 RELATIVE ALLA
    # VIGNETTA. Entrambe None → auto-stack in alto (default).
    position_x: float | None = None
    position_y: float | None = None

    # Forma del balloon. None → default in base al kind
    # (FUMETTO→oval, PENSIERO→cloud, DIDASCALIA→rect, SFX→burst).
    shape: BalloonShape | None = None

    # Tail (coda del balloon che indica chi parla).
    # Modello nuovo:
    #   - tail_origin_x/y: frazione 0-1 SUL BALLOON da cui parte la tail
    #   - tail_length_px: lunghezza tail in px (pre supersampling)
    #   - tail_base_px: larghezza base attacco al balloon (px)
    # Legacy: tail_x/tail_y come coordinate assolute del tip.
    tail_x: float | None = None
    tail_y: float | None = None
    tail_origin_x: float | None = None
    tail_origin_y: float | None = None
    tail_length_px: int | None = None
    tail_base_px: int | None = None
    show_tail: bool = True

    # Override dimensione balloon (frazioni 0-1 della cella).
    box_width_pct: float | None = None
    box_height_pct: float | None = None


# ============================================================
# Vignetta + Pagina
# ============================================================


class Panel(BaseModel):
    """Singola vignetta della pagina."""

    number: int
    description: str
    dialogues: list[Dialogue] = Field(default_factory=list)

    # Parametri di Scena (per-vignetta). Chiavi: vedi snaptoon_core/scene.py.
    # None = lascia decidere il modello.
    aspect_ratio: str | None = None
    shot_distance: str | None = None
    shot_angle: str | None = None
    mood: str | None = None

    # Cast esplicito: nomi dai character_sheets del progetto.
    # Se non vuoto, VINCE sul parsing testuale di `description`.
    characters_in_scene: list[str] = Field(default_factory=list)


class Page(BaseModel):
    """Pagina di sceneggiatura: contenitore ordinato di vignette."""

    number: int
    panels: list[Panel] = Field(default_factory=list)


# ============================================================
# Personaggi
# ============================================================


class Character(BaseModel):
    """Personaggio così come emerge dalla sceneggiatura (bibbia generica)."""

    name: str
    visual_bible: str = ""
    voice: str = ""


class CharacterSheet(BaseModel):
    """Personaggio reso *per questo progetto*: include come va disegnato
    nello stile scelto."""

    name: str
    visual_description: str = Field(
        description="Aspetto, abbigliamento, segni distintivi nello stile "
        "del progetto. Descrizione che rende il personaggio riconoscibile "
        "tra le vignette."
    )
    color_palette: str = Field(
        default="",
        description="Colori chiave (capelli, occhi, vestiti) — meglio se "
        "specifici con codici esadecimali.",
    )


# ============================================================
# Copertina
# ============================================================


class TextBox(BaseModel):
    """Box di testo sulla copertina: font, colore, dimensione, posizione."""

    font_id: str = "helvetica"
    font_size: int = 48
    color: str = "#ffffff"
    bg_color: str | None = None
    position_x: float | None = None
    position_y: float | None = None
    text_align: Literal["left", "center", "right"] = "center"
    visible: bool = True


class Cover(BaseModel):
    """Copertina del progetto: illustrazione + 3 box di testo sovrapposti."""

    title: str = ""
    subtitle: str = ""
    author: str = ""
    description: str = Field(
        default="",
        description="Descrizione visiva per generare l'illustrazione di copertina "
        "(prompt). Es. 'un uomo solitario sotto la pioggia di notte, neon rossi'.",
    )

    # Parametri di Scena (come per i Panel).
    aspect_ratio: str | None = "2_3"
    shot_distance: str | None = None
    shot_angle: str | None = None
    mood: str | None = None

    # Cast esplicito che appare in copertina.
    characters_in_scene: list[str] = Field(default_factory=list)

    title_box: TextBox = Field(
        default_factory=lambda: TextBox(
            font_id="impact", font_size=96, color="#ffffff",
            position_x=0.5, position_y=0.18, text_align="center",
        )
    )
    subtitle_box: TextBox = Field(
        default_factory=lambda: TextBox(
            font_id="helvetica", font_size=36, color="#e9ecef",
            position_x=0.5, position_y=0.32, text_align="center",
        )
    )
    author_box: TextBox = Field(
        default_factory=lambda: TextBox(
            font_id="helvetica", font_size=24, color="#ffffff",
            position_x=0.5, position_y=0.93, text_align="center",
        )
    )


# ============================================================
# Sceneggiatura
# ============================================================


class Script(BaseModel):
    """Sceneggiatura strutturata del progetto."""

    characters: list[Character] = Field(default_factory=list)
    pages: list[Page] = Field(default_factory=list)
    logline: str = ""


# ============================================================
# Layout di pagina (gabbia + balloon visibility)
# ============================================================


class PageLayout(BaseModel):
    """Impaginazione di una pagina del fumetto: gabbia + visibilità balloon.

    Niente campi `book_*`: SnapToon non gestisce libri illustrati.
    """

    page_number: int
    grid_id: str = "2x2"
    show_balloons: bool = True


# ============================================================
# Project (metadati del progetto)
# ============================================================


class ProjectMeta(BaseModel):
    """Metadati del progetto. NON contiene script/character_sheets/layouts
    (che vivono in tabelle DB separate per query efficienti).

    In Creative Studio era un'unica classe `Project` con tutto dentro,
    serializzata in JSON. In SnapToon ogni "sotto-aggregato" è una tabella
    DB e questo modello è solo l'intestazione.
    """

    slug: str
    name: str
    length_target: ProjectLength = "medio"
    page_format: str = "A4"
    created_at: str
    style_id: str | None = None
    source_text: str = ""

    # Owner (utente)
    owner_user_id: str | None = None
