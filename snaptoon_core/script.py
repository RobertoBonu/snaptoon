"""Adattamento testo → sceneggiatura strutturata via Claude.

Usa output strutturato (JSON schema) per garantire un parsing affidabile.
SnapToon è solo per fumetti: niente adattamento libro illustrato.
"""

from __future__ import annotations

import json

from .llm import DEFAULT_MODEL, client
from .models import ProjectLength, Script

SYSTEM_PROMPT = """Sei uno sceneggiatore esperto di fumetti.
Adatti testi in narrazioni visive vignetta per vignetta usando il lettering di casa:
  FUMETTO   = parlato a voce alta dentro un balloon
  PENSIERO  = monologo interiore in una nuvoletta a pensiero
  DIDASCALIA = voce narrante in un riquadro
  SFX       = onomatopea grafica

Regole tassative:
- Mai asterischi, mai testo cancellato, mai segnali di formattazione markdown nei dialoghi.
- Ogni parlato indica esplicitamente chi parla (campo `speaker`).
- Le descrizioni visive sono concrete e impaginabili: inquadratura, soggetti, azione, ambientazione.
- Ogni personaggio nominato ha una bibbia visiva (aspetto, abbigliamento, segni distintivi) e una voce.
- Il numero di pagine scala col target di lunghezza richiesto.
"""

_LENGTH_GUIDE: dict[ProjectLength, str] = {
    "striscia": "1-2 pagine, 4-8 vignette totali (formato striscia)",
    "breve": "3-6 pagine, 12-24 vignette totali (formato breve)",
    "medio": "8-16 pagine, 32-64 vignette totali (formato standard)",
    "lungo": "24+ pagine, 96+ vignette totali (formato graphic novel)",
}


SCRIPT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "logline": {"type": "string"},
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "visual_bible": {"type": "string"},
                    "voice": {"type": "string"},
                },
                "required": ["name", "visual_bible", "voice"],
            },
        },
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
                                "dialogues": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "kind": {
                                                "type": "string",
                                                "enum": ["FUMETTO", "PENSIERO", "DIDASCALIA", "SFX"],
                                            },
                                            "speaker": {"type": ["string", "null"]},
                                            "text": {"type": "string"},
                                        },
                                        "required": ["kind", "speaker", "text"],
                                    },
                                },
                            },
                            "required": ["number", "description", "dialogues"],
                        },
                    },
                },
                "required": ["number", "panels"],
            },
        },
    },
    "required": ["logline", "characters", "pages"],
}


def adapt_text_to_script(
    title: str,
    length_target: ProjectLength,
    source_text: str,
) -> Script:
    """Trasforma il testo sorgente in sceneggiatura strutturata via Claude.

    Args:
        title: Titolo del fumetto (passato al modello come contesto).
        length_target: Lunghezza target (striscia/breve/medio/lungo).
        source_text: Testo sorgente da adattare.

    Returns:
        Script con logline, characters, pages, panels, dialogues.
    """
    length_guide = _LENGTH_GUIDE[length_target]

    user_msg = (
        f"Tipo di opera: fumetto\n"
        f"Titolo: {title}\n"
        f"Lunghezza target: {length_guide}\n\n"
        f"Adatta il testo seguente in sceneggiatura strutturata.\n\n"
        f"--- TESTO ---\n{source_text}\n--- FINE ---"
    )

    response = client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        output_config={"format": {"type": "json_schema", "schema": SCRIPT_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    return Script.model_validate(data)
