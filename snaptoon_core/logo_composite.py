"""Compositing PIL del logo di sistema su cover e quarta di copertina KIDS.

L'admin controlla in `admin/sistema` dimensione (px) e posizione (X, Y) del
logo separatamente per copertina e quarta. La cover viene generata pulita
da gpt-image-2 (senza logo). Al momento del rendering PDF (o preview), il
logo viene sovrapposto in PIL con questi parametri.

Vantaggio: cambiare logo/parametri non costa crediti AI, e togliere il
logo torna alla cover pulita originale senza rigenerare nulla.
"""
from __future__ import annotations

import io
import json
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# Dimensioni del canvas su cui il logo viene compositato
CANVAS_W = 1024
CANVAS_H = 1536

# Default parametri se admin non ha ancora salvato niente
DEFAULT_LOGO_PARAMS = {
    "logo_show": False,
    "cover_size_px": 200,
    "cover_x": 40,
    "cover_y": 40,
    "back_size_px": 200,
    "back_x": (CANVAS_W - 200) // 2,  # centrato orizzontalmente
    "back_y": 100,
}


def parse_logo_params(raw_json: Optional[bytes]) -> dict:
    """Parsa il JSON dei parametri logo (dall'object storage).

    Ritorna sempre un dict completo — merge coi DEFAULT per i campi mancanti.
    Robusto a JSON malformato / vuoto: fallback ai default.
    """
    params = dict(DEFAULT_LOGO_PARAMS)
    if not raw_json:
        return params
    try:
        data = json.loads(raw_json)
        if isinstance(data, dict):
            for k in DEFAULT_LOGO_PARAMS:
                if k in data:
                    params[k] = data[k]
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning("Logo params JSON malformato, uso default")
    return params


def _clamp_int(value, lo: int, hi: int, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def composite_logo(
    base_bytes: bytes,
    logo_bytes: bytes,
    size_px: int,
    x: int,
    y: int,
) -> bytes:
    """Sovrappone il logo sulla base image.

    Args:
        base_bytes: bytes dell'immagine base (cover o quarta pulita) — PNG/JPEG
        logo_bytes: bytes del logo — PNG con alpha preferito, JPEG/WEBP ok
        size_px: dimensione del lato lungo del logo (30-800 px sensato)
        x, y: coordinate del pixel top-left del logo sul base
              (0,0) = angolo alto-sinistra; possono anche essere negativi o
              oltre bordo per uscire dal canvas parzialmente

    Returns:
        bytes PNG della base con logo sovrapposto (alpha rispettato).
        Se qualcosa fallisce (logo malformato, ecc.), ritorna base_bytes
        invariato — la generazione del libretto non deve rompere per un
        problema di logo.
    """
    try:
        base = Image.open(io.BytesIO(base_bytes)).convert("RGBA")
    except Exception as e:
        logger.error("Impossibile aprire base image per compositing logo: %s", e)
        return base_bytes

    try:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    except Exception as e:
        logger.warning("Logo malformato, skip compositing: %s", e)
        return base_bytes

    size_px = _clamp_int(size_px, 20, 2000, 200)

    # Ridimensiono il logo mantenendo aspect ratio, con lato lungo = size_px
    lw, lh = logo.size
    if lw >= lh:
        new_w = size_px
        new_h = max(1, int(lh * size_px / lw))
    else:
        new_h = size_px
        new_w = max(1, int(lw * size_px / lh))
    try:
        logo = logo.resize((new_w, new_h), Image.LANCZOS)
    except Exception as e:
        logger.warning("Resize logo fallito, skip: %s", e)
        return base_bytes

    # Coordinate: possono essere qualsiasi int; PIL taglia se esce dal canvas
    x = _clamp_int(x, -new_w, base.width + new_w, 0)
    y = _clamp_int(y, -new_h, base.height + new_h, 0)

    # Paste con mask alpha per rispettare trasparenza
    try:
        base.paste(logo, (x, y), logo)
    except Exception as e:
        logger.warning("Paste logo fallito, skip: %s", e)
        return base_bytes

    # Ritorno RGB (i PDF/preview non hanno bisogno di alpha finale)
    out_img = base.convert("RGB")
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    return buf.getvalue()
