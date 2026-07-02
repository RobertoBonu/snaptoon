"""Helper per costruire storage keys consistenti.

Convenzione:
- Tutti i path sono prefissati per area
- Sotto-prefissati per project_id (per quick GC su delete progetto)
- Naming uniforme su tutta l'app
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _stringify(project_id: uuid.UUID | str) -> str:
    if isinstance(project_id, uuid.UUID):
        return str(project_id)
    return project_id


def vignette_key(project_id: uuid.UUID | str, page: int, panel: int) -> str:
    return f"vignettes/{_stringify(project_id)}/p{page:02d}_v{panel:02d}.png"


def reference_key(
    project_id: uuid.UUID | str,
    character_id: uuid.UUID | str,
    slot: int,
) -> str:
    if isinstance(character_id, uuid.UUID):
        character_id = str(character_id)
    return f"references/{_stringify(project_id)}/{character_id}/slot{slot}.png"


def cover_illustration_key(project_id: uuid.UUID | str) -> str:
    return f"covers/{_stringify(project_id)}/illustration.png"


def cover_rendered_key(project_id: uuid.UUID | str) -> str:
    return f"covers/{_stringify(project_id)}/rendered.png"


def page_render_key(project_id: uuid.UUID | str, page: int) -> str:
    return f"pages/{_stringify(project_id)}/page{page:02d}.png"


def esplora_asset_key(section: str, asset_id: uuid.UUID | str) -> str:
    """Storage key per un asset della pagina pubblica /esplora."""
    return f"esplora/{section}/{_stringify(asset_id)}.png"


def crea_image_key(slot: str) -> str:
    """Storage key per un'immagine (slot fisso) della pagina pubblica /crea."""
    return f"crea/{slot}.png"


def my_character_reference_key(
    user_id: uuid.UUID | str, entry_id: uuid.UUID | str
) -> str:
    """Reference PNG di un personaggio nella libreria personale dell'utente."""
    return f"my-characters/{_stringify(user_id)}/{_stringify(entry_id)}.png"


def pdf_export_key(project_id: uuid.UUID | str, ts: datetime | None = None) -> str:
    if ts is None:
        ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%d_%H%M%S")
    return f"exports/{_stringify(project_id)}/comic_{stamp}.pdf"


# Chiavi legacy KIDS (retrocompatibilità: puntano ai file esistenti)
ADMIN_LOGO_KEY = "admin/system_logo.png"
ADMIN_DEFAULT_COPYRIGHT_KEY = "admin/default_copyright.txt"
ADMIN_BACK_COVER_TEMPLATE_KEY = "admin/back_cover_template.txt"
ADMIN_LOGO_PARAMS_KEY = "admin/logo_params.json"

# Chiavi separate per KIND (kids | pro): logo di sistema e parametri
# possono essere diversi per libretti KIDS e progetti Pro.
_ADMIN_LOGO_KEYS = {
    "kids": ADMIN_LOGO_KEY,           # coincide col legacy
    "pro": "admin/system_logo_pro.png",
}
_ADMIN_LOGO_PARAMS_KEYS = {
    "kids": ADMIN_LOGO_PARAMS_KEY,    # coincide col legacy
    "pro": "admin/logo_params_pro.json",
}


def admin_logo_key(kind: str) -> str:
    """Storage key del logo di sistema per KIND (kids | pro)."""
    if kind not in _ADMIN_LOGO_KEYS:
        raise ValueError(f"kind logo non valido: {kind}")
    return _ADMIN_LOGO_KEYS[kind]


def admin_logo_params_key(kind: str) -> str:
    """Storage key dei parametri logo (dimensione + posizione) per KIND."""
    if kind not in _ADMIN_LOGO_PARAMS_KEYS:
        raise ValueError(f"kind logo params non valido: {kind}")
    return _ADMIN_LOGO_PARAMS_KEYS[kind]
