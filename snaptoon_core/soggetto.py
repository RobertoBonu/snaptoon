"""Crea Soggetto — workflow ideativo in 4 fasi guidate.

Genera un soggetto strutturato (logline, premise, personaggi, sinossi, tono,
ambientazione) a partire da una "scintilla" (1-3 righe) e da risposte a
6 domande mirate.

L'output è un soggetto markdown pronto per essere passato a
`adapt_text_to_script` come testo sorgente.

Persistito in `projects/<slug>/soggetto.json` come `SoggettoState`.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from .llm import DEFAULT_MODEL, client


# ============================================================
# Modelli
# ============================================================

QUESTION_KEYS = (
    "protagonista",
    "conflitto",
    "target",
    "ambientazione",
    "tono",
    "estensione",
    "finale",
)

# Opzioni standard per il target (suggerite da Claude, ma il campo è
# comunque un text area libero — l'utente può integrare con dettagli).
TARGET_OPTIONS = (
    "Bambini 6-8",
    "Bambini 9-10",
    "Young",
    "Young Adult",
    "Adult",
    "Kidult",
)


class Question(BaseModel):
    """Una domanda di Fase 2 con il suggerimento contestualizzato da Claude."""
    key: Literal[
        "protagonista", "conflitto", "target", "ambientazione",
        "tono", "estensione", "finale",
    ]
    label: str          # es. "👤 Protagonista"
    prompt: str         # es. "Chi è? Cosa vuole? Cosa lo blocca?"
    suggestion: str     # suggerimento contestualizzato dalla scintilla


class SoggettoOutput(BaseModel):
    """Il soggetto generato in Fase 3 — 6 sezioni editabili."""
    logline: str = ""
    premise: str = ""
    personaggi: str = ""
    sinossi: str = ""
    tono: str = ""
    ambientazione: str = ""

    def to_markdown(self) -> str:
        """Serializza in markdown pulito, pronto per source.txt."""
        out: list[str] = []
        if self.logline.strip():
            out.append("## Logline")
            out.append(self.logline.strip())
            out.append("")
        if self.premise.strip():
            out.append("## Premise")
            out.append(self.premise.strip())
            out.append("")
        if self.personaggi.strip():
            out.append("## Personaggi")
            out.append(self.personaggi.strip())
            out.append("")
        if self.sinossi.strip():
            out.append("## Sinossi")
            out.append(self.sinossi.strip())
            out.append("")
        if self.tono.strip():
            out.append("## Tono e atmosfera")
            out.append(self.tono.strip())
            out.append("")
        if self.ambientazione.strip():
            out.append("## Ambientazione")
            out.append(self.ambientazione.strip())
        return "\n".join(out).strip() + "\n"


class SoggettoState(BaseModel):
    """Stato persistente del workflow Crea Soggetto."""
    scintilla: str = ""
    questions: list[Question] = Field(default_factory=list)
    # Risposte alle 6 domande, indicizzate per `key`. Stringa vuota = "decidi tu".
    answers: dict[str, str] = Field(default_factory=dict)
    # Lunghezza desiderata del soggetto.
    length: Literal["breve", "medio", "lungo"] = "medio"
    # Output generato in Fase 3 (editabile in Fase 4).
    output: SoggettoOutput = Field(default_factory=SoggettoOutput)


# ============================================================
# Claude API
# ============================================================

SYSTEM_PROMPT_QUESTIONS = """Sei un editor narrativo esperto che aiuta autori \
a sviluppare soggetti per fumetti, graphic novel e libri illustrati.

Il tuo compito ora è leggere una SCINTILLA narrativa (1-3 righe) e proporre \
7 domande mirate per arricchirla in un soggetto strutturato.

Le 7 domande hanno chiavi FISSE — devi compilarle TUTTE:
  - protagonista       (👤 chi è, cosa vuole, cosa lo blocca)
  - conflitto          (⚔️ il problema centrale)
  - target             (🎯 a chi è rivolto — fascia di lettore)
  - ambientazione      (🌍 luogo, epoca, atmosfera fisica)
  - tono               (🎭 registro emotivo)
  - estensione         (📏 dimensione narrativa)
  - finale             (🎬 idea del climax/risoluzione)

Per ognuna fornisci:
  - `label`: emoji + titolo breve (es. "👤 Protagonista")
  - `prompt`: 1 riga di domanda guida (max 80 caratteri)
  - `suggestion`: suggerimento concreto in 1-2 frasi BASATO sulla scintilla \
fornita dall'autore — devi mostrare di aver letto e capito la scintilla, \
non un placeholder generico

Per la domanda `target`, scegli UNA fra queste 6 opzioni standard come \
nucleo del suggerimento, integrando con 1 frase di motivazione coerente \
con la scintilla:
  Bambini 6-8 | Bambini 9-10 | Young | Young Adult | Adult | Kidult

(Kidult = pubblico adulto che ama linguaggi infantili/giovanili rivisitati; \
Young ≈ 11-14; Young Adult ≈ 15-22; Adult = oltre i 22.)

Lingua: italiano. Tono: incisivo, da editor, mai paternalistico."""


QUESTIONS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "questions": {
            "type": "array",
            # NOTA: L'API Anthropic non supporta minItems/maxItems != 0/1.
            # La cardinalità "esattamente 6" è imposta nel SYSTEM PROMPT e
            # validata lato Python dentro propose_questions().
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "key": {
                        "type": "string",
                        "enum": list(QUESTION_KEYS),
                    },
                    "label": {"type": "string"},
                    "prompt": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
                "required": ["key", "label", "prompt", "suggestion"],
            },
        },
    },
    "required": ["questions"],
}


def propose_questions(scintilla: str) -> list[Question]:
    """Fase 2 — Claude legge la scintilla e propone le 6 domande mirate."""
    if not scintilla.strip():
        raise ValueError("La scintilla non può essere vuota.")

    user_msg = (
        f"Scintilla narrativa dell'autore:\n\n"
        f"---\n{scintilla.strip()}\n---\n\n"
        f"Proponi le 6 domande mirate con suggerimenti contestualizzati."
    )

    response = client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT_QUESTIONS,
        messages=[{"role": "user", "content": user_msg}],
        output_config={"format": {"type": "json_schema", "schema": QUESTIONS_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    raw = {q["key"]: q for q in data["questions"]}
    missing = [k for k in QUESTION_KEYS if k not in raw]
    if missing:
        # Il modello ha saltato alcune domande: lo segnaliamo all'utente
        # con un errore chiaro invece di restituire una lista parziale.
        raise ValueError(
            f"Il modello non ha generato tutte le 6 domande richieste. "
            f"Mancano: {missing}. Riprova."
        )
    # Riordino secondo QUESTION_KEYS (il modello potrebbe averle shuffled)
    return [Question.model_validate(raw[k]) for k in QUESTION_KEYS]


# ============================================================
# Fase 3 — Generazione soggetto
# ============================================================

SYSTEM_PROMPT_SOGGETTO = """Sei un editor narrativo esperto che scrive \
soggetti per fumetti, graphic novel e libri illustrati.

Dato:
  - una SCINTILLA narrativa dell'autore (la matrice originale)
  - le sue RISPOSTE a 7 domande di sviluppo (incluso il TARGET di lettore)
  - una LUNGHEZZA desiderata

produci un SOGGETTO strutturato in 6 sezioni distinte. Ogni sezione è un \
campo separato (non scrivere headers markdown dentro i campi).

Il TARGET (es. Bambini 6-8, Young Adult, Adult, Kidult) deve influenzare:
  - il lessico e la complessità sintattica
  - la profondità tematica (espliciti vs sottintesi, durezza degli eventi)
  - l'arco emotivo (rassicurante vs ambiguo)
Adatta TUTTE le sezioni del soggetto al target indicato, senza dichiararlo \
esplicitamente — è una scelta editoriale, non un'etichetta da incollare.

Sezioni:
  - logline:       1 frase compatta (max 30 parole), il "gancio" della storia
  - premise:       3-4 frasi, l'argomento centrale + conflitto principale
  - personaggi:    elenco breve dei personaggi principali, ognuno con \
nome - ruolo - arco breve. Lascia spazio agli ARCHI, non solo descrizioni \
fisiche.
  - sinossi:       narrazione in 3 atti (incipit, sviluppo, climax+finale). \
Frasi concrete e visive, niente astrazioni.
  - tono:          registro emotivo, atmosfera, riferimenti culturali \
(film, libri, fumetti) opzionali per ancorare il mood.
  - ambientazione: luogo, epoca, dettagli sensoriali significativi per la \
visualizzazione (clima, luce, materiali, suoni).

Tassativo:
  - Italiano fluido, voce neutra (NON imitare nessun autore specifico).
  - Niente cliché ("oscuro segreto", "destino crudele").
  - Specificità > genericità: meglio "una pasticceria sopra una latteria" \
che "un negozio".
  - Se l'autore ha risposto "" (vuoto) a una domanda, decidi tu in modo \
coerente con la scintilla e le altre risposte.
  - Mai asterischi, mai grassetto markdown, mai testo cancellato."""


SOGGETTO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "logline":      {"type": "string"},
        "premise":      {"type": "string"},
        "personaggi":   {"type": "string"},
        "sinossi":      {"type": "string"},
        "tono":         {"type": "string"},
        "ambientazione": {"type": "string"},
    },
    "required": [
        "logline", "premise", "personaggi",
        "sinossi", "tono", "ambientazione",
    ],
}


_LENGTH_HINTS = {
    "breve": "Lunghezza target: BREVE (~400 parole totali) — one-shot, fumetto breve di 1-4 pagine.",
    "medio": "Lunghezza target: MEDIO (~1200 parole totali) — episodio di 20-30 tavole.",
    "lungo": "Lunghezza target: LUNGO (~3000+ parole totali) — graphic novel, romanzo grafico.",
}


def generate_soggetto(
    scintilla: str,
    answers: dict[str, str],
    length: Literal["breve", "medio", "lungo"] = "medio",
) -> SoggettoOutput:
    """Fase 3 — Genera il soggetto a partire da scintilla + risposte."""
    if not scintilla.strip():
        raise ValueError("La scintilla non può essere vuota.")

    # Compongo il blocco risposte in ordine fisso
    answers_block_lines: list[str] = []
    for k in QUESTION_KEYS:
        val = (answers.get(k) or "").strip()
        answers_block_lines.append(
            f"- {k}: {val if val else '(decidi tu)'}"
        )
    answers_block = "\n".join(answers_block_lines)

    user_msg = (
        f"SCINTILLA:\n---\n{scintilla.strip()}\n---\n\n"
        f"RISPOSTE DELL'AUTORE:\n{answers_block}\n\n"
        f"{_LENGTH_HINTS[length]}\n\n"
        f"Scrivi ora il soggetto strutturato in 6 sezioni."
    )

    response = client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT_SOGGETTO,
        messages=[{"role": "user", "content": user_msg}],
        output_config={"format": {"type": "json_schema", "schema": SOGGETTO_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    return SoggettoOutput.model_validate(data)


# ============================================================
# Fase 4 — Affinamento via chat
# ============================================================

SYSTEM_PROMPT_REFINE = """Sei un editor narrativo. L'autore ti chiede di \
modificare il soggetto esistente seguendo una sua istruzione.

Mantieni la stessa struttura a 6 sezioni (logline, premise, personaggi, \
sinossi, tono, ambientazione). Modifica SOLO ciò che serve per soddisfare \
l'istruzione, lasciando intatto il resto.

Restituisci il soggetto COMPLETO aggiornato in tutte le 6 sezioni (anche \
quelle non toccate, identiche al precedente).

Tassativo:
  - Italiano fluido, voce neutra.
  - Niente cliché.
  - Mai asterischi, mai markdown."""


def refine_soggetto(
    current: SoggettoOutput,
    instruction: str,
) -> SoggettoOutput:
    """Fase 4 — Affinamento via chat: applica un'istruzione all'intero soggetto."""
    if not instruction.strip():
        raise ValueError("L'istruzione non può essere vuota.")

    user_msg = (
        f"SOGGETTO ATTUALE:\n\n"
        f"## Logline\n{current.logline}\n\n"
        f"## Premise\n{current.premise}\n\n"
        f"## Personaggi\n{current.personaggi}\n\n"
        f"## Sinossi\n{current.sinossi}\n\n"
        f"## Tono\n{current.tono}\n\n"
        f"## Ambientazione\n{current.ambientazione}\n\n"
        f"---\n\n"
        f"ISTRUZIONE DELL'AUTORE:\n{instruction.strip()}\n\n"
        f"Restituisci il soggetto aggiornato (tutte e 6 le sezioni)."
    )

    response = client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT_REFINE,
        messages=[{"role": "user", "content": user_msg}],
        output_config={"format": {"type": "json_schema", "schema": SOGGETTO_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    return SoggettoOutput.model_validate(data)
