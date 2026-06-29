"""Caricamento immagini cachato per le pagine Streamlit.

Livello sopra `storage/client.py`: aggiunge una cache in memoria
(`st.cache_data`, condivisa tra sessioni e rerun) così la stessa immagine non
viene riscaricata a ogni rerun, e collassa il vecchio pattern
`object_exists()` + `download_bytes()` in un singolo download che ritorna
`None` quando l'oggetto non esiste (404), come già fa la cover KIDS.

`storage/client.py` resta puro (niente dipendenza da Streamlit): la cache vive
solo qui.
"""

from __future__ import annotations

import streamlit as st

from storage.client import download_bytes


@st.cache_data(ttl=600, show_spinner=False, max_entries=256)
def load_image_bytes(key: str, version: str = "") -> bytes | None:
    """Scarica i bytes di un'immagine con cache. `None` se assente.

    Un solo viaggio di rete (il download): nessun `object_exists` separato.
    L'assenza (404 / oggetto mancante) è un caso normale e viene cachata come
    `None`, così i rerun successivi non ripetono il tentativo.

    `version` entra nella chiave di cache: passare un valore che cambia quando
    l'immagine viene rigenerata (es. `updated_at`) per invalidare in automatico.
    Per le scritture che non espongono una versione, chiamare
    `invalidate_image_cache()` dopo upload/eliminazione.
    """
    try:
        return download_bytes(key)
    except Exception:
        return None


def invalidate_image_cache() -> None:
    """Svuota la cache immagini.

    Da chiamare dopo upload/rigenerazione/eliminazione di un'immagine così la
    versione nuova viene riletta dallo storage e non resta quella vecchia.
    """
    try:
        load_image_bytes.clear()
    except Exception:
        pass
