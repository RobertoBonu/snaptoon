"""Helper unificato per servire immagini con cache immutabile + varianti.

Ogni immagine generata dall'AI è IMMUTABILE una volta creata: se l'utente
la rigenera lo storage_key cambia (o le varianti WebP vengono sovrascritte).
Quindi le risposte HTTP possono usare Cache-Control massimo:
    public, max-age=31536000, immutable

Il browser scarica UNA volta e riusa dall'HTTP cache per un anno.
Se serve un refresh dopo rigenerazione, il frontend aggiunge ?t=<timestamp>
al src (cache-busting) — pattern già usato ovunque nel codebase.
"""
from __future__ import annotations

from fastapi import Response

from storage.image_variants import Variant, read_variant


# Cache HTTP massima per immagini generate.
# 31536000 = 1 anno, `immutable` = il browser non chiede mai revalidation.
IMMUTABLE_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
}


def serve_image_variant(base_key: str, variant: Variant) -> Response:
    """Legge una variante e ritorna una Response con headers di cache."""
    data, content_type = read_variant(base_key, variant)
    return Response(
        content=data,
        media_type=content_type,
        headers=IMMUTABLE_CACHE_HEADERS,
    )
