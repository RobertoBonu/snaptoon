"""Salvataggio e serving di immagini con 3 varianti.

Per ogni PNG generato dall'AI salviamo 3 file su object storage:
    - <base>.png           ← intatto (per PDF finale, download, stampa)
    - <base>.full.webp     ← stesse dimensioni, WebP quality=92 (per zoom UI)
    - <base>.thumb.webp    ← 400px lato lungo, WebP quality=85 (per anteprime liste)

Un thumb da 400px pesa ~30-60 KB (vs ~2 MB del PNG originale).
Un full.webp mantiene qualità visiva paragonabile al PNG ma pesa ~5-10x meno.

Il PNG originale NON viene mai cancellato: resta la ground truth pixel-perfect
per export PDF, ordini di stampa fisica e download pubblico.
"""
from __future__ import annotations

import io
import logging
from typing import Literal

from PIL import Image

from storage.client import download_bytes, object_exists, upload_bytes

logger = logging.getLogger(__name__)


Variant = Literal["thumb", "full", "original"]

# Configurazione varianti WebP
THUMB_MAX_SIDE_PX = 400   # lato lungo del thumbnail
THUMB_QUALITY = 85        # WebP quality per thumb (compressione più aggressiva)
FULL_QUALITY = 92         # WebP quality per full (visivamente identico al PNG)


def variant_key(base_key: str, variant: Variant) -> str:
    """Deriva la storage_key per una variante da quella dell'originale.

    Esempi (base = 'my-characters/uid/entry.png'):
        variant='original' → 'my-characters/uid/entry.png'
        variant='full'     → 'my-characters/uid/entry.full.webp'
        variant='thumb'    → 'my-characters/uid/entry.thumb.webp'
    """
    if variant == "original":
        return base_key
    if "." in base_key:
        stem, _ext = base_key.rsplit(".", 1)
    else:
        stem = base_key
    return f"{stem}.{variant}.webp"


def _encode_webp(img: Image.Image, quality: int) -> bytes:
    """Salva un'Image PIL in WebP e ritorna i bytes."""
    buf = io.BytesIO()
    # Rimuove profili colore complessi non sempre supportati
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
    # method=6 = massima compressione (lento ma qualità/rapporto migliore)
    img.save(buf, format="WEBP", quality=quality, method=6)
    return buf.getvalue()


def _make_thumbnail(img: Image.Image, max_side: int) -> Image.Image:
    """Ridimensiona mantenendo aspect ratio; lato lungo = max_side."""
    w, h = img.size
    if max(w, h) <= max_side:
        return img.copy()
    if w >= h:
        new_w = max_side
        new_h = int(round(h * max_side / w))
    else:
        new_h = max_side
        new_w = int(round(w * max_side / h))
    return img.resize((new_w, new_h), Image.LANCZOS)


def save_with_variants(base_key: str, png_bytes: bytes) -> None:
    """Salva PNG originale + full.webp + thumb.webp.

    Il chiamante passa la storage_key "canonical" (la chiave PNG che
    già usa). Questa funzione:
      1. Fa upload di png_bytes su base_key (invariata, comportamento pre-esistente).
      2. Genera e uploada anche <base>.full.webp e <base>.thumb.webp.

    Se la generazione WebP fallisce, la variante NON viene salvata ma
    l'originale PNG resta valido — nessun break.
    """
    # 1. Upload PNG originale (comportamento pre-esistente, sempre garantito)
    upload_bytes(base_key, png_bytes, content_type="image/png")

    # 2. Genera varianti WebP (best-effort, non blocca il flow principale)
    try:
        img = Image.open(io.BytesIO(png_bytes))
        # full.webp: stesse dimensioni, alta qualità
        full_webp = _encode_webp(img, FULL_QUALITY)
        upload_bytes(variant_key(base_key, "full"), full_webp, content_type="image/webp")
        # thumb.webp: ridimensionata, qualità media
        thumb_img = _make_thumbnail(img, THUMB_MAX_SIDE_PX)
        thumb_webp = _encode_webp(thumb_img, THUMB_QUALITY)
        upload_bytes(variant_key(base_key, "thumb"), thumb_webp, content_type="image/webp")
    except Exception as e:
        logger.warning(
            "Fallita generazione varianti WebP per %s: %s (PNG originale OK)",
            base_key, e,
        )


def read_variant(base_key: str, variant: Variant) -> tuple[bytes, str]:
    """Legge una variante dell'immagine con fallback intelligente.

    Ritorna (bytes, content_type). Fallback order:
        - requested variant, se esiste
        - full.webp, se richiesto thumb ma non esiste
        - original PNG (sempre presente)

    Utile per immagini generate PRIMA dell'introduzione delle varianti:
    la variante WebP non esiste → fallback trasparente al PNG originale.
    """
    if variant == "original":
        return download_bytes(base_key), "image/png"

    v_key = variant_key(base_key, variant)
    if object_exists(v_key):
        return download_bytes(v_key), "image/webp"

    # Thumb mancante → prova full.webp prima del PNG
    if variant == "thumb":
        full_k = variant_key(base_key, "full")
        if object_exists(full_k):
            return download_bytes(full_k), "image/webp"

    # Fallback definitivo: PNG originale
    return download_bytes(base_key), "image/png"


def parse_variant(raw: str | None) -> Variant:
    """Sanitizza il parametro ?variant=... proveniente dal client."""
    v = (raw or "full").strip().lower()
    if v in ("thumb", "full", "original"):
        return v  # type: ignore[return-value]
    return "full"
