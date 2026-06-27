"""Parametri di regia per ogni singola vignetta.

Mentre lo Stile è scelto a livello progetto (look generale), la Scena è
per-vignetta: formato, distanza dell'inquadratura, angolo, tono emotivo.

Ogni valore ha:
- una `label` italiana (mostrata nell'UI)
- una `prompt_en` inglese (inserita nel prompt di generazione)

Il prompt è in inglese perché i modelli image-gen rispondono meglio
all'inglese (vedi linee guida visual-prompt-engine).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Option:
    key: str          # ID interno (snake_case, salvato nel project.json)
    label: str        # Etichetta italiana per la UI
    prompt_en: str    # Frase inglese da inserire nel prompt


# ============================================================
# Formato vignetta (aspect ratio)
# ============================================================

ASPECT_RATIOS: list[Option] = [
    Option("1_1",      "Quadrato 1:1",                "square 1:1 aspect ratio"),
    Option("3_4",      "Verticale 3:4",                "vertical 3:4 portrait aspect ratio"),
    Option("2_3",      "Verticale 2:3 (classico fumetto)", "vertical 2:3 portrait aspect ratio"),
    Option("9_16",     "Verticale 9:16 (webtoon)",     "vertical 9:16 portrait aspect ratio (tall vertical scroll)"),
    Option("4_3",      "Orizzontale 4:3 (TV classico)", "horizontal 4:3 landscape aspect ratio"),
    Option("3_2",      "Orizzontale 3:2 (fotografico)", "horizontal 3:2 landscape aspect ratio"),
    Option("16_9",     "Orizzontale 16:9 (widescreen)", "horizontal 16:9 widescreen cinematic aspect ratio"),
    Option("2_1",      "Cinematografico 2:1",          "horizontal 2:1 panoramic cinematic aspect ratio"),
]


def aspect_ratio_to_provider_size(key: str | None) -> str:
    """Mappa l'aspect ratio sulla size più vicina supportata da OpenAI gpt-image.
    OpenAI accetta solo 3 size; Gemini è flessibile via prompt hint.
    """
    if not key:
        return "1024x1024"
    # Portrait
    if key in ("3_4", "2_3", "9_16"):
        return "1024x1536"
    # Landscape / cinematic
    if key in ("4_3", "3_2", "16_9", "2_1"):
        return "1536x1024"
    # Quadrato (1_1) e default
    return "1024x1024"


# ============================================================
# Distanza inquadratura (shot distance)
# ============================================================

SHOT_DISTANCES: list[Option] = [
    Option("extreme_closeup", "Extreme close-up (dettaglio: occhi, mani)",
           "extreme close-up shot — a single facial feature, eyes only or hands only, filling the entire frame"),
    Option("closeup", "Close-up (volto intero)",
           "close-up shot — the subject's entire face fills the frame"),
    Option("medium_closeup", "Medium close-up (testa e spalle)",
           "medium close-up shot — head and shoulders of the subject"),
    Option("mezzo_busto", "Mezzo busto",
           "medium shot from the waist up — the subject's torso and head"),
    Option("americano", "Campo americano (dalle ginocchia)",
           "American shot (cowboy shot) — the subject framed from the knees up"),
    Option("medium", "Piano medio (figura intera)",
           "medium full shot — the subject's full body fills most of the frame"),
    Option("campo_totale", "Campo totale (figura nell'ambiente)",
           "full shot / total shot — the subject's full figure is shown within their environment"),
    Option("campo_lungo", "Campo lungo (figura piccola nell'ambiente)",
           "long shot — the subject appears small within a vast environment, environment dominates"),
    Option("establishing", "Establishing (panoramica ambiente, niente figure dominanti)",
           "establishing shot — wide panoramic view of the location, no single subject dominates, scene-setting frame"),
]


# ============================================================
# Angolo inquadratura (shot angle / camera POV)
# ============================================================

SHOT_ANGLES: list[Option] = [
    Option("eye_level", "Eye-level (livello degli occhi)",
           "neutral eye-level camera angle"),
    Option("low_angle", "Low angle (dal basso)",
           "low camera angle, looking up at the subject, making them appear powerful"),
    Option("worm_eye", "Worm's eye (dal basso estremo)",
           "extreme worm's-eye view from the ground looking straight up, dramatic perspective"),
    Option("high_angle", "High angle (dall'alto)",
           "high camera angle, looking down at the subject, making them appear vulnerable"),
    Option("birds_eye", "Bird's eye (vista d'uccello)",
           "bird's-eye view from high above, sweeping aerial perspective"),
    Option("zenitale", "Zenitale (perpendicolare dall'alto)",
           "overhead top-down shot, camera perfectly perpendicular above the scene"),
    Option("dutch_angle", "Dutch angle (inclinato)",
           "Dutch tilt / canted angle — camera rotated, horizon line tilted, creating unease"),
    Option("over_the_shoulder", "Over the shoulder (sopra la spalla)",
           "over-the-shoulder shot, framed from behind another character looking at the subject"),
    Option("fifty_fifty", "50/50 (due personaggi affacciati)",
           "fifty-fifty two-shot — two characters facing each other, evenly split frame"),
    Option("soggettiva", "Soggettiva / POV",
           "point-of-view shot from the subject's eyes, as if the viewer is the subject"),
    Option("frog_perspective", "Prospettiva della rana",
           "frog perspective, very low ground-level angle with extreme upward distortion"),
]


# ============================================================
# Tono emotivo (mood)
# ============================================================

MOODS: list[Option] = [
    Option("drammatico", "Drammatico",
           "dramatic mood — heightened emotional stakes, intense expressions, strong contrast lighting"),
    Option("allegro", "Allegro",
           "joyful mood — bright atmosphere, warm light, open expressions, vivid colors"),
    Option("angosciante", "Angosciante",
           "anguished mood — claustrophobic framing, oppressive atmosphere, cold colors, deep shadows"),
    Option("poetico", "Poetico",
           "poetic mood — lyrical light, contemplative pace, soft delicate atmosphere, considered composition"),
    Option("romantico", "Romantico",
           "romantic mood — warm golden light, soft focus, tender expressions, intimate framing"),
    Option("sospeso", "Sospeso",
           "suspended mood — held breath, frozen moment, expectant silence, restrained tension"),
    Option("grottesco", "Grottesco",
           "grotesque mood — distorted proportions, uncanny detail, dark humor, unsettling beauty"),
    Option("thriller", "Thriller",
           "thriller mood — taut suspense, sharp shadows, urgent body language, narrow framing"),
    Option("noir", "Noir",
           "noir mood — high-contrast shadows, rain-slicked surfaces, moral ambiguity, urban nocturnal atmosphere"),
    Option("epico", "Epico",
           "epic mood — vast scale, heroic stance, monumental composition, sweeping cinematic grandeur"),
    Option("onirico", "Onirico",
           "dreamlike mood — surreal logic, soft edges, impossible light, floating quality"),
    Option("fiabesco", "Fiabesco",
           "fairy-tale mood — wondrous atmosphere, enchanted detail, storybook palette, magical light"),
    Option("scifi", "Sci-fi",
           "science-fiction mood — speculative technology, futuristic atmosphere, otherworldly light, off-Earth feel"),
]


# ============================================================
# Lookup helpers
# ============================================================

def _by_key(options: list[Option], key: str | None) -> Option | None:
    if not key:
        return None
    for o in options:
        if o.key == key:
            return o
    return None


def aspect_ratio_option(key: str | None) -> Option | None:
    return _by_key(ASPECT_RATIOS, key)


def shot_distance_option(key: str | None) -> Option | None:
    return _by_key(SHOT_DISTANCES, key)


def shot_angle_option(key: str | None) -> Option | None:
    return _by_key(SHOT_ANGLES, key)


def mood_option(key: str | None) -> Option | None:
    return _by_key(MOODS, key)


def build_scene_clauses(panel) -> list[str]:
    """Costruisce le clausole inglesi da inserire nel prompt, dato un Panel.

    Ritorna una lista di stringhe (vuota se nessuna scelta di scena è stata
    fatta). Il chiamante le inserisce nei punti giusti del prompt.
    """
    out: list[str] = []
    ar = aspect_ratio_option(getattr(panel, "aspect_ratio", None))
    sd = shot_distance_option(getattr(panel, "shot_distance", None))
    sa = shot_angle_option(getattr(panel, "shot_angle", None))
    md = mood_option(getattr(panel, "mood", None))

    if ar:
        out.append(f"FORMAT: {ar.prompt_en}.")
    framing_bits: list[str] = []
    if sd:
        framing_bits.append(sd.prompt_en)
    if sa:
        framing_bits.append(sa.prompt_en)
    if framing_bits:
        out.append(f"FRAMING: {'; '.join(framing_bits)}.")
    if md:
        out.append(f"MOOD: {md.prompt_en}.")
    return out
