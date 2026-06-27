"""Registry degli stili visivi.

Ogni stile è un file YAML in core/styles_data/<id>.yaml.
Lo stile definisce SOLO il look condiviso: tecnica, aesthetic, palette,
illuminazione, vincoli tipografici, negative prompt.

I personaggi NON stanno qui: sono per-progetto, vedi Project.character_sheets.

build_panel_prompt() combina vignetta + stile + character sheets del PROGETTO
per produrre un prompt completo pronto per gpt-image-2 o Gemini.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import CharacterSheet, Cover, Panel, Script
from .scene import build_scene_clauses
from .styles_library import (
    HANDMADE_NEGATIVE_TERMS,
    MEDIA_AUTHENTICITY_CLAUSE,
    get_preset,
)

STYLES_DIR = Path(__file__).resolve().parent / "styles_data"
STYLE_LOGOS_DIR = STYLES_DIR / "logos"


def style_logo_path(style_id: str) -> Path:
    """Path al file logo PNG dell'editore per uno specifico stile.

    Il file potrebbe non esistere se l'utente non ha caricato un logo.
    Use `path.exists()` prima di leggere.
    """
    return STYLE_LOGOS_DIR / f"{style_id}.png"


# Re-export per compatibilità: altri moduli importavano CharacterSheet da styles
__all__ = ["Style", "list_styles", "build_panel_prompt", "build_cover_prompt", "CharacterSheet", "style_logo_path"]


class Style(BaseModel):
    """Uno stile visivo (template di look, condiviso tra progetti)."""

    # Tollera campi extra nel YAML (es. il vecchio `characters` legacy)
    # senza farli sparire né bloccare il caricamento.
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str = Field(description="Descrizione umana, una riga.")

    technique: str = Field(
        description="Tecnica e medium (es. 'flat anime/cartoon vector', "
        "'watercolor traditional', 'oil painting Caravaggesque')."
    )
    aesthetic: str = Field(
        description="Mood, atmosfera, riferimenti culturali/storici "
        "che devono trasparire."
    )
    palette: str = Field(
        description="Palette generale dello stile (colori dominanti, "
        "saturazione, contrasto)."
    )
    lighting: str = Field(
        default="",
        description="Tipo di illuminazione tipica.",
    )
    line_work: str = Field(
        default="",
        description="Tratto, linee, contorni (es. 'spessore costante 2px, "
        "linee pulite, niente sketch').",
    )

    typography_constraints: str = Field(
        default=(
            "Nei testi presenti nell'immagine: usa virgolette tipografiche, "
            "mai asterischi, mai testo cancellato o barrato. "
            "Esplicitare chi parla quando il contesto non lo rende ovvio."
        ),
        description="Vincoli sui testi che compaiono dentro l'immagine "
        "(balloon, didascalie, SFX). Default coerente con CLAUDE.md.",
    )

    negative_prompt: str = Field(
        default="",
        description="Cosa evitare (es. 'no realistic photo, no 3D render, "
        "no extra fingers, no AI-slop gradients').",
    )

    # --- Libreria 96 stili (Step B) ---
    library_preset_id: str | None = Field(
        default=None,
        description="ID del preset libreria applicato (es. 'heavy_ink_noir'). "
        "Se settato, l'espansione viene inclusa verbatim nel prompt e ha "
        "la precedenza sui campi technique/aesthetic/palette/lighting/line_work.",
    )
    category: str = Field(
        default="illustrazione",
        description="Categoria di rendering — webtoon | illustrazione | "
        "fotografia | kids. Decide il category prefix del prompt.",
    )

    # --- Aspetto visivo: sfondo pagina, font + colori balloon/caption/sfx ---
    # Tutti i colori in formato esadecimale "#RRGGBB".
    # Le dimensioni font sono in unità logiche (scalate 2× in supersampling).
    page_background_color: str = "#ffffff"

    balloon_font_id: str = "marker_felt"
    balloon_font_size: int = 22
    balloon_text_color: str = "#000000"
    balloon_outline_color: str = "#1a1a1a"
    balloon_fumetto_fill: str = "#ffffff"
    balloon_pensiero_fill: str = "#f7f7f7"
    # Tratto graphic-novel: contorno spesso uniforme + speed-lines + jitter
    # organico della forma. Vengono applicati a FUMETTO/PENSIERO/URLO.
    balloon_outline_width: int = 5
    balloon_speed_lines: bool = True
    balloon_jitter: bool = True
    # Padding interno del balloon (distanza testo ↔ bordo) in unità logiche.
    balloon_padding: int = 14

    caption_font_id: str = "helvetica"
    caption_font_size: int = 22
    caption_text_color: str = "#000000"
    caption_outline_color: str = "#1a1a1a"
    caption_fill: str = "#fff8d4"

    sfx_font_id: str = "impact"
    sfx_font_size: int = 56
    sfx_text_color: str = "#d32f2f"
    sfx_outline_color: str = "#7a1010"
    sfx_fill: str = "#fff7a3"

    # === Logo editore ===
    # Il file PNG vive in core/styles_data/logos/{style_id}.png
    # (helper: style_logo_path()). Qui i parametri visuali, SEPARATI fra
    # copertina e pagina copyright (così posso avere logo grande sulla cover
    # e logo discreto in fondo al copyright).
    publisher_logo_enabled: bool = False
    # Copertina
    publisher_logo_size_pct: float = 0.18   # % larghezza pagina (0.05-0.5)
    publisher_logo_position: str = "bc"      # "bl"|"bc"|"br"|"tl"|"tc"|"tr"
    # Pagina copyright (default: stessa della cover; modificabili separatamente)
    copyright_logo_size_pct: float = 0.18
    copyright_logo_position: str = "bc"

    def balloon_config(self):
        """Ritorna un BalloonStyleConfig pronto per il rendering."""
        from .layout import BalloonStyleConfig
        return BalloonStyleConfig(
            page_bg=self.page_background_color,
            balloon_font_id=self.balloon_font_id,
            balloon_font_size=self.balloon_font_size,
            balloon_text_color=self.balloon_text_color,
            balloon_outline_color=self.balloon_outline_color,
            balloon_fumetto_fill=self.balloon_fumetto_fill,
            balloon_pensiero_fill=self.balloon_pensiero_fill,
            balloon_outline_width=self.balloon_outline_width,
            balloon_speed_lines=self.balloon_speed_lines,
            balloon_jitter=self.balloon_jitter,
            balloon_padding=self.balloon_padding,
            caption_font_id=self.caption_font_id,
            caption_font_size=self.caption_font_size,
            caption_text_color=self.caption_text_color,
            caption_outline_color=self.caption_outline_color,
            caption_fill=self.caption_fill,
            sfx_font_id=self.sfx_font_id,
            sfx_font_size=self.sfx_font_size,
            sfx_text_color=self.sfx_text_color,
            sfx_outline_color=self.sfx_outline_color,
            sfx_fill=self.sfx_fill,
        )

    @classmethod
    def load(cls, style_id: str) -> "Style":
        path = STYLES_DIR / f"{style_id}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def save(self) -> None:
        STYLES_DIR.mkdir(parents=True, exist_ok=True)
        path = STYLES_DIR / f"{self.id}.yaml"
        # Salva solo i campi del modello dichiarati: esclude i campi "extra"
        # (es. il legacy `characters` che ora è gestito dall'Archivio Cast).
        # Pydantic 2 con extra="allow" mette quei campi in model_extra; li
        # filtriamo prendendo solo le chiavi del modello dichiarato.
        full = self.model_dump()
        declared_keys = set(self.__class__.model_fields.keys())
        cleaned = {k: v for k, v in full.items() if k in declared_keys}
        path.write_text(
            yaml.safe_dump(
                cleaned,
                sort_keys=False,
                allow_unicode=True,
                width=100,
            ),
            encoding="utf-8",
        )

    @property
    def legacy_characters(self) -> list[CharacterSheet]:
        """Personaggi salvati nel vecchio formato (Style.characters).

        Usato solo per offrire la migrazione al Project. Non usare per logica
        nuova. Restituisce lista vuota se il YAML non ha il campo legacy.
        """
        extra = self.__pydantic_extra__ or {}
        raw = extra.get("characters") or []
        out: list[CharacterSheet] = []
        for item in raw:
            try:
                out.append(CharacterSheet.model_validate(item))
            except Exception:
                continue
        return out


def list_styles() -> list[str]:
    STYLES_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p.stem for p in STYLES_DIR.glob("*.yaml"))


def build_panel_prompt(
    panel: Panel,
    style: Style,
    script: Script,
    character_sheets: list[CharacterSheet],
    page_number: int | None = None,
) -> str:
    """Compone il prompt finale per generare l'immagine di una vignetta.

    Segue l'assembly order della skill visual-prompt-engine:
      1. Category prefix (illustrazione/webtoon/...)
      2. Scene/subject (descrizione vignetta + parametri Scena)
      3. Style expansion (preset libreria verbatim, o campi tradizionali)
      4. Media authenticity clause (auto se preset hand-made)
      5. Character consistency block
      6. Composition (full-bleed) + text rules
      7. Negative prompt aggregato
    """
    # Personaggi attivi nella vignetta: selezione esplicita (panel.characters_in_scene)
    # se settata, altrimenti fallback al parsing testuale della description.
    from .generator import panel_active_characters
    mentioned = panel_active_characters(panel, character_sheets)
    has_explicit_cast = bool(getattr(panel, "characters_in_scene", None))

    # Preset libreria, se applicato
    preset = get_preset(style.library_preset_id) if style.library_preset_id else None

    parts: list[str] = []

    # --- 0. RENDER MODE: edge-to-edge (priorità massima, inizio prompt) ---
    # Questo blocco va PRIMA di tutto perché i modelli image-gen pesano di più
    # le istruzioni iniziali. Senza questo, modelli come Gemini tendono a
    # disegnare cornici da "fumetto stampato" anche con stili che richiamano
    # comic aesthetic (Sin City, silkscreen, ecc.).
    parts.append(
        "RENDER MODE — EDGE-TO-EDGE FILM STILL. The image is a borderless "
        "single frame, like a still extracted from a movie or a photograph "
        "taken with a camera. The scene continues BEYOND the visible edges "
        "of the frame — the camera is simply cropping a larger continuous "
        "world. The artwork occupies 100% of the canvas, all the way to the "
        "pixel boundaries on every side (top, bottom, left, right). "
        "ABSOLUTELY NO: comic-book panel border, ink frame, torn paper edge, "
        "deckled edge, aged paper texture margin, vignette darkening at the "
        "corners, drawn rectangular outline, drop-shadow framing, white or "
        "cream border, page background visible behind the art, passe-partout, "
        "mat board, decorative ornamental border, polaroid-style white margin. "
        "Do NOT depict this as an artwork sitting ON a piece of paper or "
        "framed within a panel — depict the scene ITSELF, with the canvas "
        "edges acting as the camera viewport. Even if the chosen visual "
        "style references comic-book or silkscreen aesthetics, the OUTPUT "
        "must be a clean borderless image without any frame or paper margin."
    )

    # --- 1. Category prefix ---
    category = (style.category or "illustrazione").lower()
    if category == "webtoon":
        parts.append(
            "\nSequential comic / webtoon panel artwork. Any in-panel dialogue "
            "(if present) is added as overlay in post — do NOT paint balloons or text."
        )
    elif category == "fotografia":
        parts.append("\nPhotorealistic photograph. No text, no illustration artifacts.")
    elif category == "kids":
        parts.append(
            "\nChild-safe 2D illustration for young children. Wholesome, "
            "reassuring, non-threatening — no scary, violent or mature elements."
        )
    else:  # illustrazione (default)
        parts.append(
            "\nSingle editorial illustration. No panel borders, no lettering, "
            "no text anywhere in the image."
        )

    # --- 2. Scene / subject ---
    page_tag = f"page {page_number} " if page_number else ""
    parts.append(f"\nSCENE ({page_tag}panel {panel.number}):")
    parts.append(panel.description)

    # --- 2.b Parametri di regia (Scena per-vignetta) ---
    scene_clauses = build_scene_clauses(panel)
    if scene_clauses:
        parts.append("")
        parts.extend(scene_clauses)

    # --- 3. Style ---
    if preset:
        # Espansione verbatim dalla libreria (96 preset)
        parts.append(f"\nVISUAL STYLE — {preset.label}:")
        parts.append(preset.expansion)
    else:
        # Campi tradizionali (per stili custom)
        parts.append(f"\nVISUAL STYLE — {style.name}:")
        parts.append(f"Technique: {style.technique}")
        parts.append(f"Aesthetic: {style.aesthetic}")
        parts.append(f"Palette: {style.palette}")
        if style.lighting:
            parts.append(f"Lighting: {style.lighting}")
        if style.line_work:
            parts.append(f"Line work: {style.line_work}")

    # --- 4. Media authenticity (anti-AI-look per stili hand-made) ---
    is_handmade = preset.is_handmade if preset else _is_handmade_text(
        f"{style.technique} {style.aesthetic} {style.line_work}"
    )
    if is_handmade:
        parts.append(f"\n{MEDIA_AUTHENTICITY_CLAUSE}")

    # --- 5. Character consistency (rafforzato) ---
    if mentioned:
        # Intestazione: lista dei personaggi presenti, in ordine.
        names_only = ", ".join(c.name for c in mentioned)
        parts.append(
            f"\nCHARACTERS IN THIS PANEL — exactly these characters appear: "
            f"**{names_only}**. They MUST look IDENTICAL to their reference "
            f"images supplied with this request (the references are the visual "
            f"ground truth — same face, same hairstyle, same skin tone, same "
            f"eye color, same costume, same body proportions). DO NOT redesign, "
            f"re-interpret, age, slim, or stylize them differently. Treat the "
            f"reference images as identity anchors, not as scene composition."
        )
        # Dettaglio per personaggio (rinforza con la bibbia testuale)
        for c in mentioned:
            block = f"- **{c.name}**: {c.visual_description}"
            if c.color_palette:
                block += f" — Colors: {c.color_palette}"
            parts.append(block)
        if has_explicit_cast:
            parts.append(
                "(Cast manually curated for this panel — only the characters "
                "listed above are in the scene; do not add others.)"
            )

    # --- 6. Reminder finale: no text + edge-to-edge ---
    parts.append(
        "\nFINAL REMINDERS: (1) NO TEXT in image — no balloons, no captions, "
        "no SFX lettering; text is added later as vector overlay. "
        "(2) EDGE-TO-EDGE composition — the scene fills the entire canvas, "
        "no border, no frame, no torn/aged paper edge, no comic-panel outline."
    )

    # --- 7. Negative prompt aggregato (rinforzato contro cornici) ---
    avoid_clauses = [
        # Testo
        "text inside image", "speech balloons painted in", "lettering", "typography",
        # Cornici geometriche
        "border", "frame", "inner border", "panel outline", "rectangular outline",
        "drawn frame", "drawn rectangle around the image",
        # Cornici "tipo carta"
        "torn paper edge", "deckled edge", "aged paper texture border",
        "paper margin", "white margin", "cream margin", "colored margin",
        "page background visible", "page texture visible behind art",
        "watercolor paper edge", "rough paper edge",
        # Cornici "tipo fumetto"
        "comic book panel border", "comic book ink frame", "manga panel border",
        "drawn comic panel", "newsprint border", "irregular ink border",
        "rough black border", "vintage comic frame",
        # Effetti di passe-partout / vignetta
        "passe-partout", "matboard", "polaroid border", "polaroid frame",
        "vignette darkening", "vignetting effect", "darkened corners",
        "drop-shadow framing the image", "decorative ornamental border",
        "ornate border", "filigree border",
    ]
    if is_handmade:
        avoid_clauses.extend(HANDMADE_NEGATIVE_TERMS)
    # Termini negative specifici del preset libreria (custom o ufficiale)
    if preset and preset.extra_negative_terms:
        avoid_clauses.extend(preset.extra_negative_terms)
    if style.negative_prompt and style.negative_prompt.strip() and not style.negative_prompt.strip().startswith("TODO"):
        avoid_clauses.append(style.negative_prompt)
    parts.append(f"\nAVOID: {', '.join(avoid_clauses)}")

    return "\n".join(parts)


# Keyword detection per stili custom non in libreria
_HANDMADE_KEYWORDS_TEXT = (
    "watercolor", "acquerello", "gouache", "oil paint", "oil painting",
    "ink wash", "brush and ink", "charcoal", "pencil sketch", "crayon",
    "pastel", "engraving", "crosshatch", "etching", "risograph",
    "screenprint", "silkscreen", "ink expressionism", "ink crosshatching",
)


def _is_handmade_text(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _HANDMADE_KEYWORDS_TEXT)


def build_cover_prompt(
    cover: Cover,
    style: Style,
    character_sheets: list[CharacterSheet],
) -> str:
    """Prompt per generare l'illustrazione di copertina (NO testo).

    Stessa estetica di stile delle vignette, ma composizione "da copertina":
    formato verticale, soggetto centrale d'impatto, area "respirabile" in
    alto-centro per ospitare il titolo che verrà sovrapposto come overlay.
    """
    preset = get_preset(style.library_preset_id) if style.library_preset_id else None
    parts: list[str] = []

    # --- 0. RENDER MODE: edge-to-edge ---
    parts.append(
        "RENDER MODE — EDGE-TO-EDGE BOOK COVER ILLUSTRATION. The image is a "
        "borderless full-bleed illustration that fills 100% of the canvas, "
        "no panel borders, no inner frame, no paper margin, no torn paper edge, "
        "no decorative ornament, no comic-style panel outline. The art reaches "
        "every pixel boundary on every side."
    )

    # --- 1. Soggetto / descrizione ---
    parts.append("\nCOVER SUBJECT:")
    if cover.description.strip():
        parts.append(cover.description)
    else:
        parts.append(
            "A single iconic, atmospheric establishing image that visually "
            "represents the spirit of the work."
        )

    # --- 1.b Parametri di Scena per la copertina (regia) ---
    scene_clauses = build_scene_clauses(cover)
    if scene_clauses:
        parts.append("")
        parts.extend(scene_clauses)

    # --- 2. Composizione da copertina ---
    parts.append(
        "\nCOMPOSITION RULES (cover-specific): "
        "(a) Vertical portrait format suitable for a book/comic cover. "
        "(b) Strong central focal subject with cinematic framing. "
        "(c) Leave the UPPER THIRD relatively unbusy and lower-contrast — a "
        "title will be overlaid there in post-production, so the area must "
        "remain readable. (d) Leave a small calm strip in the BOTTOM region "
        "for the author name overlay. (e) Mid-zone is where the visual "
        "punch lives."
    )

    # --- 3. Style ---
    if preset:
        parts.append(f"\nVISUAL STYLE — {preset.label}:")
        parts.append(preset.expansion)
    else:
        parts.append(f"\nVISUAL STYLE — {style.name}:")
        parts.append(f"Technique: {style.technique}")
        parts.append(f"Aesthetic: {style.aesthetic}")
        parts.append(f"Palette: {style.palette}")
        if style.lighting:
            parts.append(f"Lighting: {style.lighting}")
        if style.line_work:
            parts.append(f"Line work: {style.line_work}")

    is_handmade = preset.is_handmade if preset else _is_handmade_text(
        f"{style.technique} {style.aesthetic} {style.line_work}"
    )
    if is_handmade:
        parts.append(f"\n{MEDIA_AUTHENTICITY_CLAUSE}")

    # --- 4. Character consistency (cast esplicito se selezionato, altrimenti
    # nessun personaggio forzato — molte copertine sono atmospheric senza cast).
    explicit_cast = list(cover.characters_in_scene or [])
    if explicit_cast:
        cast_lower = {n.lower() for n in explicit_cast}
        active = [c for c in character_sheets if c.name.lower() in cast_lower]
        if active:
            names_only = ", ".join(c.name for c in active)
            parts.append(
                f"\nCHARACTERS ON THE COVER — exactly these characters appear: "
                f"**{names_only}**. They MUST look IDENTICAL to their reference "
                f"images supplied with this request (same face, hair, skin tone, "
                f"eye color, costume, proportions). Do NOT redesign or restyle them."
            )
            for c in active:
                block = f"- **{c.name}**: {c.visual_description}"
                if c.color_palette:
                    block += f" — Colors: {c.color_palette}"
                parts.append(block)

    # --- 5. Reminder finale: ZERO testo nell'immagine ---
    parts.append(
        "\nABSOLUTELY NO TEXT IN THE IMAGE — no title lettering, no author "
        "name, no tagline, no logo, no captions. The cover text will be "
        "composited later as vector overlay; the illustration must be "
        "completely text-free, including faux text or decorative letterforms."
    )

    # --- 6. Negative aggregato ---
    avoid_clauses = [
        "text inside image", "title text painted in", "lettering", "typography",
        "logo", "publisher mark", "barcode", "ISBN strip",
        "border", "frame", "inner border", "panel outline",
        "torn paper edge", "deckled edge", "white margin",
        "comic book panel border", "passe-partout", "polaroid frame",
    ]
    if is_handmade:
        avoid_clauses.extend(HANDMADE_NEGATIVE_TERMS)
    if preset and preset.extra_negative_terms:
        avoid_clauses.extend(preset.extra_negative_terms)
    if style.negative_prompt and style.negative_prompt.strip() and not style.negative_prompt.strip().startswith("TODO"):
        avoid_clauses.append(style.negative_prompt)
    parts.append(f"\nAVOID: {', '.join(avoid_clauses)}")

    return "\n".join(parts)
