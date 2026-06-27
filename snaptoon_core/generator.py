"""Image generation — interfaccia astratta + impl OpenAI/Gemini.

Provider selezionato dal .env (`IMAGE_PROVIDER=openai|gemini`).
Le impl sono pigre: il client del provider scelto viene istanziato solo se serve.

Due tipi di generazione:
- Reference sheet di un personaggio (text-to-image, salvato per-stile)
- Panel/vignetta (text-to-image, opzionalmente con reference images come input
  visivo per character consistency)
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GenerationResult:
    image_path: Path
    prompt_path: Path
    provider: str
    model: str
    cached: bool = False


def _hash_file(path: Path) -> str:
    """Hash dei bytes di un file, usato per invalidare la cache se la ref cambia."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


class ImageGenerator(ABC):
    """Interfaccia comune per i provider di image generation."""

    provider_name: str
    model: str

    @abstractmethod
    def _generate_bytes(
        self,
        prompt: str,
        size: str,
        reference_images: list[Path] | None = None,
        quality: str = "medium",
    ) -> bytes:
        """Chiama l'API del provider e ritorna i bytes PNG."""

    def generate(
        self,
        prompt: str,
        out_image: Path,
        *,
        size: str = "1024x1024",
        use_cache: bool = True,
        reference_images: list[Path] | None = None,
        quality: str = "medium",
    ) -> GenerationResult:
        """Genera immagine, salva PNG e prompt accanto.

        Cache: hash su (provider, model, prompt, ref_paths+content, quality, size).
        Cambiando qualsiasi di questi, l'hash cambia e si rigenera.

        quality: 'low' | 'medium' | 'high' | 'auto'
                 (Su Gemini è no-op; OpenAI lo passa all'API).
        """
        out_image = Path(out_image)
        out_image.parent.mkdir(parents=True, exist_ok=True)
        prompt_path = out_image.with_suffix(".prompt.txt")

        # Cache key include anche quality e size
        refs_for_hash = ""
        if reference_images:
            ordered = sorted(reference_images, key=lambda p: p.name)
            refs_for_hash = "|".join(
                f"{p.name}:{_hash_file(p)}" for p in ordered if p.exists()
            )

        cache_key = (
            f"{self.provider_name}::{self.model}::{prompt}::"
            f"refs={refs_for_hash}::q={quality}::s={size}"
        )
        current_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

        if use_cache and out_image.exists() and prompt_path.exists():
            stored = prompt_path.read_text(encoding="utf-8")
            stored_hash = stored.split("\n", 1)[0].removeprefix("# hash: ")
            if stored_hash == current_hash:
                return GenerationResult(
                    image_path=out_image,
                    prompt_path=prompt_path,
                    provider=self.provider_name,
                    model=self.model,
                    cached=True,
                )

        image_bytes = self._generate_bytes(prompt, size, reference_images, quality)
        out_image.write_bytes(image_bytes)
        ref_summary = ", ".join(p.name for p in (reference_images or [])) or "(none)"
        prompt_path.write_text(
            f"# hash: {current_hash}\n"
            f"# provider: {self.provider_name}\n"
            f"# model: {self.model}\n"
            f"# size: {size}\n"
            f"# quality: {quality}\n"
            f"# references: {ref_summary}\n\n"
            f"{prompt}",
            encoding="utf-8",
        )
        return GenerationResult(
            image_path=out_image,
            prompt_path=prompt_path,
            provider=self.provider_name,
            model=self.model,
            cached=False,
        )


class OpenAIImageGenerator(ImageGenerator):
    provider_name = "openai"

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()  # legge OPENAI_API_KEY dal .env
        return self._client

    def _generate_bytes(
        self,
        prompt: str,
        size: str,
        reference_images: list[Path] | None = None,
        quality: str = "medium",
    ) -> bytes:
        client = self._client_lazy()
        # quality valido per gpt-image: low | medium | high | auto
        q = quality if quality in ("low", "medium", "high", "auto") else "medium"
        if reference_images:
            # Con immagini di riferimento → images.edit() supporta input visivi
            files = [open(p, "rb") for p in reference_images if p.exists()]
            try:
                resp = client.images.edit(
                    model=self.model,
                    image=files if len(files) > 1 else files[0],
                    prompt=prompt,
                    size=size,
                    quality=q,
                    n=1,
                )
            finally:
                for f in files:
                    f.close()
        else:
            resp = client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality=q,
                n=1,
            )
        b64 = resp.data[0].b64_json
        return base64.b64decode(b64)


class GeminiImageGenerator(ImageGenerator):
    provider_name = "gemini"

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv(
            "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview"
        )
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def _generate_bytes(
        self,
        prompt: str,
        size: str,
        reference_images: list[Path] | None = None,
        quality: str = "medium",
    ) -> bytes:
        # Gemini 3 Pro Image non ha un parametro `quality`: produce sempre allo
        # stesso livello. Il param viene ricevuto per compatibilità interfaccia
        # ma non viene usato. (Nessun no-op nel prompt: non aiuta.)
        from google.genai import types
        from PIL import Image

        # Per Gemini, le immagini di riferimento si passano nel `contents` array
        # insieme al prompt testuale. Il modello le tratta come input visivo.
        contents: list = []
        if reference_images:
            for p in reference_images:
                if p.exists():
                    contents.append(Image.open(p))
        contents.append(prompt)

        resp = self._client_lazy().models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
        for part in resp.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                data = part.inline_data.data
                if isinstance(data, bytes):
                    return data
                return base64.b64decode(data)
        raise RuntimeError("Gemini non ha restituito un'immagine. Risposta: " + str(resp))


def get_generator() -> ImageGenerator:
    """Factory: legge IMAGE_PROVIDER dal .env."""
    provider = os.getenv("IMAGE_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return OpenAIImageGenerator()
    if provider == "gemini":
        return GeminiImageGenerator()
    raise ValueError(
        f"IMAGE_PROVIDER='{provider}' non valido. Usa 'openai' o 'gemini'."
    )


# ============================================================
# Path helpers
# ============================================================

def panel_image_path(project_dir: Path, page_number: int, panel_number: int) -> Path:
    """Path canonico del PNG di una vignetta."""
    return project_dir / "images" / f"p{page_number:02d}_v{panel_number:02d}.png"


def _slug(s: str) -> str:
    """Slug filesystem-safe per nomi personaggio."""
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "unnamed"


MAX_REFS_PER_CHARACTER = 7
# Limite globale di reference passate in una singola chiamata image-gen.
# Allineato ai limiti tipici dei provider (gpt-image-2: ~16 input images,
# Gemini 3: limite simile). Sotto questa soglia evitiamo errori 400.
MAX_REFS_PER_GENERATION = 16


def character_reference_path(project_dir: Path, character_name: str) -> Path:
    """Path canonico della reference PRINCIPALE di un personaggio (slot 1).

    Le reference sono per-progetto: ogni progetto ha la propria cartella
    `projects/<slug>/refs/<char-slug>.png`. Lo stesso personaggio può
    apparire diverso in due progetti, anche con lo stesso stile.
    """
    return Path(project_dir) / "refs" / f"{_slug(character_name)}.png"


def character_reference_slot_path(
    project_dir: Path, character_name: str, slot: int
) -> Path:
    """Path della reference per uno slot specifico (1..MAX_REFS_PER_CHARACTER).

    Convenzione filesystem:
    - slot 1 → `refs/<slug>.png` (retro-compatibile)
    - slot 2..N → `refs/<slug>-{slot}.png`

    Permettere più reference per personaggio (es. fronte, 3/4, profilo, full-body,
    espressioni varie) migliora la character consistency tra le scene rispetto
    a un'unica reference: il modello aggancia identità da più viste.
    """
    if slot < 1 or slot > MAX_REFS_PER_CHARACTER:
        raise ValueError(
            f"Slot reference fuori range: {slot} (1..{MAX_REFS_PER_CHARACTER})"
        )
    base = Path(project_dir) / "refs"
    if slot == 1:
        return base / f"{_slug(character_name)}.png"
    return base / f"{_slug(character_name)}-{slot}.png"


def character_reference_paths(project_dir: Path, character_name: str) -> list[Path]:
    """Lista di TUTTE le reference esistenti per un personaggio (slot 1..7).

    Ritorna solo i file che esistono sul filesystem, in ordine di slot.
    Lista vuota se il personaggio non ha alcuna reference.
    """
    out: list[Path] = []
    for slot in range(1, MAX_REFS_PER_CHARACTER + 1):
        p = character_reference_slot_path(project_dir, character_name, slot)
        if p.exists():
            out.append(p)
    return out


# ============================================================
# Prompt builders
# ============================================================

def build_character_reference_prompt(character, style) -> str:
    """Prompt per generare il character reference sheet di un personaggio.

    L'obiettivo è un'immagine pulita, neutra, multi-vista che il modello potrà
    poi usare come riferimento visivo per generare le vignette mantenendo la
    coerenza del personaggio.
    """
    parts: list[str] = []

    parts.append(
        f"CHARACTER REFERENCE SHEET for visual consistency. "
        f"Subject: {character.name}."
    )

    parts.append(f"\nCHARACTER DESCRIPTION:")
    parts.append(character.visual_description)
    if character.color_palette:
        parts.append(f"Colors: {character.color_palette}")

    parts.append(f"\nSTYLE:")
    parts.append(f"Technique: {style.technique}")
    parts.append(f"Aesthetic: {style.aesthetic}")
    parts.append(f"Palette: {style.palette}")
    if style.lighting:
        parts.append(f"Lighting: {style.lighting}")
    if style.line_work:
        parts.append(f"Line work: {style.line_work}")

    parts.append(
        f"\nLAYOUT: Character reference sheet, plain neutral background "
        f"(off-white #f0eee6). Multiple views of the SAME character: "
        f"full-body front view on the left, 3/4 view in the middle, "
        f"close-up portrait on the right. Neutral pose, neutral expression. "
        f"Clean separation between views. "
        f"NO TEXT in the image. NO labels, NO captions, NO speech balloons."
    )

    if style.negative_prompt:
        parts.append(f"\nAVOID: {style.negative_prompt}")

    return "\n".join(parts)


# ============================================================
# Varianti reference (slot 2..7) — più viste della stessa persona
# ============================================================

# Tipi di variante disponibili nella UI. Ogni voce è (key, label_it, view_clause_en).
# La view_clause_en finisce direttamente nel prompt — è scritta in inglese perché
# i modelli image-gen rispondono meglio.
CHARACTER_VARIANT_KINDS: list[tuple[str, str, str]] = [
    (
        "profile",
        "Profilo laterale",
        "Side profile view (camera perpendicular to the face), neutral expression, "
        "looking straight ahead, mouth closed.",
    ),
    (
        "three_quarter",
        "3/4 di faccia",
        "Three-quarter view of the face (camera at ~45° from frontal), neutral "
        "expression, eyes looking at the camera, mouth closed.",
    ),
    (
        "full_body",
        "Full-body in piedi",
        "Full-body shot, the entire figure visible from head to feet, neutral "
        "standing pose with arms relaxed at the sides, full outfit and shoes "
        "visible, frontal view.",
    ),
    (
        "smiling",
        "Sorridente (close-up)",
        "Close-up portrait, genuine warm smile showing teeth, eyes engaged with "
        "the camera, head slightly tilted.",
    ),
    (
        "dramatic",
        "Espressione drammatica",
        "Close-up portrait, intense dramatic expression — eyes wide, mouth open "
        "as if shouting or in shock, strong emotional tension.",
    ),
    (
        "back",
        "Vista da dietro",
        "Three-quarter back view of the figure, head turned slightly so the "
        "profile of the cheek is just visible, full outfit and hairstyle from "
        "behind clearly readable.",
    ),
    (
        "hands",
        "Mani in primo piano",
        "Close-up of both hands held in front of the chest, palms visible, "
        "showing fingers, knuckles, any rings/gloves/distinctive marks. The face "
        "may be partially visible at the top of the frame.",
    ),
]


def build_character_variant_prompt(character, style, variant_key: str) -> str:
    """Prompt per generare una VARIANTE di reference di un personaggio.

    A differenza di build_character_reference_prompt (che parte da zero),
    questa pretende che il modello prenda lo slot 1 come ancoraggio d'identità
    e produca una vista diversa della STESSA persona, stesso look, stesso stile.
    """
    view_clause = next(
        (clause for k, _label, clause in CHARACTER_VARIANT_KINDS if k == variant_key),
        None,
    )
    if not view_clause:
        raise ValueError(f"Variant key sconosciuta: {variant_key}")

    parts: list[str] = []

    parts.append(
        f"CHARACTER REFERENCE VARIANT — additional view of {character.name}. "
        f"This is a NEW view of THE SAME EXACT PERSON shown in the reference "
        f"image supplied with this request. The reference is the visual ground "
        f"truth: same face, same hairstyle, same skin tone, same eye color, "
        f"same body proportions, same costume, same color palette. Do NOT "
        f"redesign, age, slim, restyle, or re-interpret the character."
    )

    parts.append(f"\nREQUESTED VIEW:\n{view_clause}")

    parts.append("\nCHARACTER DESCRIPTION (textual anchor):")
    parts.append(character.visual_description)
    if character.color_palette:
        parts.append(f"Colors: {character.color_palette}")

    parts.append("\nSTYLE (must match the original reference):")
    parts.append(f"Technique: {style.technique}")
    parts.append(f"Aesthetic: {style.aesthetic}")
    parts.append(f"Palette: {style.palette}")
    if style.lighting:
        parts.append(f"Lighting: {style.lighting}")
    if style.line_work:
        parts.append(f"Line work: {style.line_work}")

    parts.append(
        "\nLAYOUT: Single-subject reference sheet on a plain neutral background "
        "(off-white #f0eee6, same as a canonical character sheet). Centered "
        "subject, clean separation from the background. NO TEXT, NO labels, "
        "NO speech balloons, NO frames or borders, NO multi-view collage — "
        "just this ONE view of the character."
    )

    if style.negative_prompt:
        parts.append(f"\nAVOID: {style.negative_prompt}")
    parts.append(
        "\nAVOID: redesigning the character, changing hairstyle/clothing, "
        "different person, multi-panel layout, text, watermark, frame, border, "
        "paper edge, background scenery."
    )

    return "\n".join(parts)


def panel_active_characters(panel, character_sheets: list) -> list:
    """Personaggi attivi in una vignetta.

    Se `panel.characters_in_scene` è non-vuota → vince (selezione esplicita,
    più affidabile). Altrimenti → fallback al parsing testuale della
    description (può sbagliare con descrizioni vaghe o nomi simili).
    """
    explicit = getattr(panel, "characters_in_scene", None) or []
    if explicit:
        names_lower = {n.lower() for n in explicit}
        return [c for c in character_sheets if c.name.lower() in names_lower]
    # Fallback: parsing testuale
    return [c for c in character_sheets if c.name.lower() in panel.description.lower()]


def collect_panel_references(
    panel,
    character_sheets: list,
    project_dir: Path,
) -> list[Path]:
    """Per una vignetta, restituisce TUTTE le reference esistenti dei personaggi
    attivi (selezione esplicita o parsing testuale come fallback).

    Cerca tutti gli slot 1..MAX_REFS_PER_CHARACTER per ciascun personaggio.
    Capping a MAX_REFS_PER_GENERATION per stare nei limiti API: con N personaggi
    e M ref/personaggio, ripartisce equamente prendendo round-robin fino al cap.
    """
    per_character: list[list[Path]] = []
    for c in panel_active_characters(panel, character_sheets):
        paths = character_reference_paths(project_dir, c.name)
        if paths:
            per_character.append(paths)
    return _cap_refs_roundrobin(per_character, MAX_REFS_PER_GENERATION)


def _cap_refs_roundrobin(per_character: list[list[Path]], cap: int) -> list[Path]:
    """Prende ref round-robin dai personaggi finché si raggiunge il cap.

    Garantisce che ogni personaggio abbia almeno una ref (slot 1) prima di
    aggiungere varianti, così nessuno scompare dal contesto visivo.
    """
    if not per_character:
        return []
    flat: list[Path] = []
    max_len = max(len(refs) for refs in per_character)
    for slot_i in range(max_len):
        for refs in per_character:
            if slot_i < len(refs):
                flat.append(refs[slot_i])
                if len(flat) >= cap:
                    return flat
    return flat
