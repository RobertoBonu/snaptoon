"""Caricamento immagini cachato per le pagine Streamlit.

Livello sopra `storage/client.py`: aggiunge una cache in memoria
(`st.cache_data`, condivisa tra sessioni e rerun) così la stessa immagine non
viene riscaricata a ogni rerun.

Va usato SOLO nel punto in cui i bytes servono davvero a schermo (display,
download, generazione). Per i conteggi/stato "esiste o no" NON usare questo
modulo: usare i campi DB già disponibili nelle view (es. `ref_storage_key`,
`illustration_key`, i record vignetta) oppure `storage.client.object_exists`
(che fa un `list` con prefix, economico) — scaricare i bytes solo per contare
vanificherebbe il caricamento on-demand.

`storage/client.py` resta puro (niente dipendenza da Streamlit): la cache vive
solo qui.
"""

from __future__ import annotations

import logging

import streamlit as st

from storage.client import download_bytes

logger = logging.getLogger(__name__)

# Eccezioni che significano "oggetto non presente" (caso normale → None).
# Tutto il resto è un errore transitorio (rete/storage) da NON trattare come
# "immagine mancante" e da NON cachare.
try:
    from replit.object_storage.errors import (
        BucketNotFoundError,
        ObjectNotFoundError,
    )

    _NOT_FOUND_ERRORS: tuple[type[BaseException], ...] = (
        FileNotFoundError,
        ObjectNotFoundError,
        BucketNotFoundError,
    )
except Exception:  # SDK non disponibile (es. dev locale)
    _NOT_FOUND_ERRORS = (FileNotFoundError,)


@st.cache_data(ttl=600, show_spinner=False, max_entries=256)
def _download_cached(key: str, version: str = "") -> bytes:
    """Download cachato dei bytes. Solleva su miss/errore.

    `st.cache_data` NON memorizza le eccezioni: così un not-found o un errore
    transitorio non vengono mai cachati e il rerun successivo riprova.
    """
    return download_bytes(key)


def load_image_bytes(key: str, version: str = "") -> bytes | None:
    """Ritorna i bytes di un'immagine (cachati) o `None` se assente/fallita.

    - Oggetto mancante (404) → `None` (caso normale, nessun log).
    - Errore transitorio (rete/storage) → `None` ma con WARNING nei log e SENZA
      caching, così non resta "fantasma mancante" per la durata del TTL.

    `version` entra nella chiave di cache: passare un valore che cambia quando
    l'immagine viene rigenerata (es. `updated_at`) per invalidare in automatico.
    Per le scritture che non espongono una versione, chiamare
    `invalidate_image_cache()` dopo upload/eliminazione.
    """
    if not key:
        return None
    try:
        return _download_cached(key, version)
    except _NOT_FOUND_ERRORS:
        return None
    except Exception:
        logger.warning("load_image_bytes: errore non-404 per key=%s", key, exc_info=True)
        return None


def invalidate_image_cache() -> None:
    """Svuota la cache immagini.

    Da chiamare dopo upload/rigenerazione/eliminazione di un'immagine così la
    versione nuova viene riletta dallo storage e non resta quella vecchia.
    """
    try:
        _download_cached.clear()
    except Exception:
        pass
