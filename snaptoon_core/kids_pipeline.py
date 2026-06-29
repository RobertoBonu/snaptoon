"""Pipeline KIDS condivisa tra Streamlit (legacy) e FastAPI (V2).

Centralizza la logica di generazione storia + immagini per i libretti KIDS.
Era originariamente in pages/06_KIDS.py — estratta qui per riuso da
api/routers/kids_generation.py.
"""
from __future__ import annotations

import json

from snaptoon_core.models import Character, Dialogue, Page, Panel
from snaptoon_core.models import Script as PydScript
from snaptoon_core.styles_library import get_preset


# ============================================================
# Mapping stile + griglia
# ============================================================

KIDS_STYLE_MAP = {
    "flat": ("Flat", "bold_toddler_graphic"),
    "3d": ("3D", "illumination_cartoon_style"),
    "manga": ("Manga", "japanese_preschool_anime"),
}
KIDS_STYLE_PRESET_IDS = {pid for _, pid in KIDS_STYLE_MAP.values()}

GRID_CAPACITY = {"splash": 1, "1+2": 3, "2x2": 4}


# ============================================================
# System prompt Claude (regola di coerenza personaggi secondari)
# ============================================================

CLAUDE_KIDS_SYSTEM = """Sei un autore di libri illustrati per bambini (5-8 anni).
Scrivi sceneggiature per fumetti brevi e dolci, con dialoghi semplici.

VINCOLI CRITICI — RISPETTA ESATTAMENTE:
- Numero di pagine fissato (lo riceverai)
- Numero di vignette per pagina fissato (lo riceverai)
- Dialoghi MASSIMO 4-5 parole (devono essere scritti DENTRO le immagini)
- Massimo 1 dialogo per vignetta
- Lessico semplice da bambini
- Nei dialoghi usa solo testo in MAIUSCOLO breve, niente apostrofi, niente accenti
  difficili. Esempi buoni: "CIAO!", "AIUTO!", "DOVE SEI?", "ANDIAMO!", "MAMMA!"
- Niente asterischi, niente testo cancellato, niente markdown

COERENZA VISIVA DEGLI ELEMENTI RICORRENTI — REGOLA FONDAMENTALE:
I personaggi principali hanno reference image, quindi sono coerenti automaticamente.
MA ogni altro elemento visivo che compare in più vignette (animali secondari,
oggetti caratteristici, ambienti specifici, vestiti, accessori) può essere
disegnato in modo diverso ogni volta perché l'AI immagine NON ha memoria.

Per evitare incoerenze:
1. La PRIMA volta che un elemento secondario appare in una vignetta, descrivilo
   con DETTAGLI VISIVI CONCRETI (colore esatto, forma, dimensione, eventuali
   macchie o caratteristiche distintive).
2. In OGNI vignetta successiva in cui ricompare, ripeti gli STESSI dettagli
   visivi alla lettera. Non variare mai colore, forma o dettagli.

Sii SEMPRE esplicito sui dettagli visivi nelle description delle vignette.
"""


# ============================================================
# JSON schema per Claude (output strutturato)
# ============================================================


def kids_script_schema(n_pages: int, capacities: list[int]) -> dict:
    """JSON schema dinamico: ogni pagina ha N vignette pre-fissate."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "logline": {"type": "string"},
            "pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "integer"},
                        "panels": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "number": {"type": "integer"},
                                    "description": {"type": "string"},
                                    "dialogue_speaker": {"type": ["string", "null"]},
                                    "dialogue_text": {"type": ["string", "null"]},
                                },
                                "required": [
                                    "number",
                                    "description",
                                    "dialogue_speaker",
                                    "dialogue_text",
                                ],
                            },
                        },
                    },
                    "required": ["number", "panels"],
                },
            },
        },
        "required": ["logline", "pages"],
    }


# ============================================================
# Generazione storia via Claude
# ============================================================


def generate_kids_script(
    scintilla: str,
    names: list[str],
    descs: list[str],
    grid_distribution: list[str],
    feedback: str = "",
) -> PydScript:
    """Chiama Claude per produrre uno script con gabbie pre-fissate.

    feedback: note opzionali dall'utente per ri-orientare una rigenerazione
              (es. "rendi più allegra", "meno paurosa", "aggiungi un nonno").
    """
    n_pages = len(grid_distribution)
    capacities = [GRID_CAPACITY[g] for g in grid_distribution]

    cast_block = "\n".join([f"- {n}: {d}" for n, d in zip(names, descs)])
    page_structure = "\n".join(
        [
            f"  Pagina {i+1}: {capacities[i]} vignett{'a' if capacities[i] == 1 else 'e'}"
            for i in range(n_pages)
        ]
    )

    feedback_block = ""
    if feedback.strip():
        feedback_block = (
            f"\n\nNOTE AGGIUNTIVE DELL'AUTORE (considera questi suggerimenti "
            f"per cambiare/migliorare la storia rispetto a una versione precedente):\n"
            f"{feedback.strip()}\n"
        )

    user_msg = f"""Scrivi un fumetto per bambini.

SCINTILLA:
{scintilla}

PERSONAGGI:
{cast_block}

STRUTTURA OBBLIGATORIA:
{page_structure}
{feedback_block}
Output JSON con logline + pages (ognuna con panels).
Ogni panel ha description (concreta, visualizzabile) + dialogue_speaker + dialogue_text.
Se la vignetta non ha dialogo, metti dialogue_speaker=null e dialogue_text=null.
"""

    # Lazy import (anthropic SDK pesa ~2-3s)
    from snaptoon_core.llm import DEFAULT_MODEL, client as llm_client

    response = llm_client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8000,
        system=CLAUDE_KIDS_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": kids_script_schema(n_pages, capacities),
            }
        },
    )
    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)

    # Costruisci Pydantic Script
    pages = []
    for pg in data["pages"]:
        panels = []
        for pn in pg["panels"]:
            dialogues = []
            if pn.get("dialogue_text"):
                dialogues.append(
                    Dialogue(
                        kind="FUMETTO",
                        speaker=pn.get("dialogue_speaker"),
                        text=pn["dialogue_text"],
                    )
                )
            panels.append(
                Panel(
                    number=pn["number"],
                    description=pn["description"],
                    dialogues=dialogues,
                )
            )
        pages.append(Page(number=pg["number"], panels=panels))

    return PydScript(
        logline=data["logline"],
        characters=[
            Character(name=n, visual_bible=d, voice="") for n, d in zip(names, descs)
        ],
        pages=pages,
    )


# ============================================================
# Aspect ratio per cella della griglia
# ============================================================


def panel_size_for(grid_id: str, panel_number: int) -> tuple[str, str, str]:
    """Returns (openai_size, aspect_ratio_key, human_format) per una cella.

    OpenAI gpt-image-2 accetta 3 size: 1024x1024, 1024x1536 (2:3 verticale),
    1536x1024 (3:2 orizzontale). Mappiamo ogni cella alla forma giusta.

    Mappatura (pagina libro = verticale 2:3):
    - splash:    1 cella full-page  → 2:3 verticale
    - 1+2 #1:    grande orizzontale → 3:2
    - 1+2 #2,3:  piccole verticali  → 2:3
    - 2x2:       4 celle 2:3 ciascuna
    """
    if grid_id == "splash":
        return ("1024x1536", "2_3", "vertical portrait, tall format")
    if grid_id == "1+2":
        if panel_number == 1:
            return ("1536x1024", "3_2", "horizontal panoramic, wide format")
        return ("1024x1536", "2_3", "vertical portrait, tall format")
    if grid_id == "2x2":
        return ("1024x1536", "2_3", "vertical portrait, tall format")
    return ("1024x1024", "1_1", "square format")


# ============================================================
# Prompt builders per OpenAI gpt-image-2
# ============================================================


def build_reference_prompt(name: str, desc: str, style_preset_id: str) -> str:
    """Prompt per generare una character sheet (reference slot 1)."""
    preset = get_preset(style_preset_id)
    parts = []
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")
    parts.append(
        f"=== CHARACTER REFERENCE ===\n"
        f"Subject: {name}\n"
        f"Visual description: {desc}\n"
    )
    parts.append(
        "=== RENDER MODE ===\n"
        "Full-body character on uniform clean background. Centered standing pose. "
        "Cartoon for children, friendly, expressive. Edge-to-edge full-bleed."
    )
    parts.append(
        "=== AVOID ===\nphotorealism, scary, dark themes, frame, border, text, watermark"
    )
    return "\n\n".join(parts)


def build_panel_prompt(
    panel: Panel,
    cast: list[dict],  # [{"name": ..., "description": ...}]
    style_preset_id: str,
    scene_params: dict,
    panel_format: str = "square format",
) -> str:
    """Prompt per generare una singola vignetta con balloon AI-bake."""
    preset = get_preset(style_preset_id)
    parts = []
    parts.append(
        f"=== RENDER MODE ===\n"
        f"Full-bleed single comic panel for children's book in {panel_format}. "
        f"Bright friendly colors. Edge-to-edge, no external frame or page border. "
        f"Compose the scene to fill the entire {panel_format} — characters, action "
        f"and any speech bubble must fit comfortably inside without being cropped."
    )
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")
    parts.append(f"=== SCENE ===\n{panel.description.strip()}")

    # Scene directives
    from snaptoon_core.scene import MOODS, SHOT_ANGLES, SHOT_DISTANCES

    clauses = []
    sd = scene_params.get("shot_distance")
    sa = scene_params.get("shot_angle")
    md = scene_params.get("mood")
    if sd:
        o = next((o for o in SHOT_DISTANCES if o.key == sd), None)
        if o:
            clauses.append(f"SHOT DISTANCE: {o.prompt_en}.")
    if sa:
        o = next((o for o in SHOT_ANGLES if o.key == sa), None)
        if o:
            clauses.append(f"CAMERA ANGLE: {o.prompt_en}.")
    if md:
        o = next((o for o in MOODS if o.key == md), None)
        if o:
            clauses.append(f"MOOD: {o.prompt_en}.")
    if clauses:
        parts.append("=== DIRECTING ===\n" + " ".join(clauses))

    # Cast consistency
    if cast:
        cast_block = ["=== CHARACTERS IN THIS PANEL ==="]
        for cs in cast:
            cast_block.append(f"- {cs['name']}: {cs['description']}")
        cast_block.append(
            "Characters must look IDENTICAL to the reference images provided. "
            "Same face, hair, clothes. Visual ground truth."
        )
        parts.append("\n".join(cast_block))

    # Balloon AI-bake
    if panel.dialogues:
        balloon_block = ["=== SPEECH BUBBLE (DRAW IT IN THE IMAGE) ==="]
        for dlg in panel.dialogues:
            speaker = dlg.speaker or "narrator"
            text_clean = (dlg.text or "").upper()
            balloon_block.append(
                f"Draw a clean white speech bubble with a thin black border "
                f"pointing toward {speaker}. Inside the bubble write EXACTLY "
                f"this text in a clear bold sans-serif font, no decoration: "
                f"'{text_clean}'"
            )
        balloon_block.append(
            "The speech bubble must be readable, white background, black border, "
            "black text. Place it in an empty part of the composition. "
            "Spell every letter exactly as given. No extra words."
        )
        parts.append("\n".join(balloon_block))
    else:
        parts.append("=== TEXT ===\nNo text or speech bubble in the image.")

    parts.append(
        "=== AVOID ===\n"
        "photorealism, scary or dark themes, blood, violence, frame, border, "
        "watermark, multiple panels, comic page layout, weird letters, "
        "misspelled words, scrambled text"
    )

    return "\n\n".join(parts)


def build_cover_prompt(
    title: str,
    cast: list[dict],
    style_preset_id: str,
) -> str:
    """Prompt per la copertina del libretto (2:3 verticale, titolo AI-bake)."""
    preset = get_preset(style_preset_id)
    parts = []
    parts.append(
        "=== RENDER MODE ===\n"
        "Vertical book cover illustration for a children's picture book. "
        "Edge-to-edge full-bleed. Cinematic poster composition, eye-catching, "
        "bright friendly colors. No frame, no border. The title and characters "
        "should be the focus."
    )
    if preset:
        parts.append(f"=== STYLE ===\n{preset.expansion.strip()}")

    parts.append(f"=== COVER ===\nBook cover for «{title}»")

    if cast:
        cast_block = ["=== CHARACTERS ON COVER ==="]
        for cs in cast:
            cast_block.append(f"- {cs['name']}: {cs['description']}")
        cast_block.append(
            "Characters must look IDENTICAL to reference images. Hero pose, "
            "friendly expression."
        )
        parts.append("\n".join(cast_block))

    parts.append(
        f"=== TITLE TEXT (DRAW IT IN THE IMAGE) ===\n"
        f"At the top of the image, draw the title in big bold playful "
        f"children's book font: '{title.upper()}'. Use clear readable letters, "
        f"strong outline so it stands out from the background. No subtitle, "
        f"no author name."
    )

    parts.append(
        "=== AVOID ===\n"
        "scary, dark themes, frame, border, watermark, multiple titles, "
        "scrambled text, weird letters, misspelled words"
    )
    return "\n\n".join(parts)
