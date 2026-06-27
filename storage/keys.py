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


def pdf_export_key(project_id: uuid.UUID | str, ts: datetime | None = None) -> str:
    if ts is None:
        ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%d_%H%M%S")
    return f"exports/{_stringify(project_id)}/comic_{stamp}.pdf"
