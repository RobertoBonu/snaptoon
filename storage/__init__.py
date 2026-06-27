"""SnapToon — wrapper Replit Object Storage.

Path convention (storage keys):
- vignettes/{project_id}/p{page:02d}_v{panel:02d}.png
- references/{project_id}/{character_id}/slot{N}.png
- covers/{project_id}/illustration.png
- covers/{project_id}/rendered.png
- pages/{project_id}/page{N:02d}.png
- exports/{project_id}/comic_{timestamp}.pdf
"""

from __future__ import annotations

from .client import (
    delete_object,
    download_bytes,
    object_exists,
    storage_client,
    upload_bytes,
)
from .keys import (
    cover_illustration_key,
    cover_rendered_key,
    page_render_key,
    pdf_export_key,
    reference_key,
    vignette_key,
)

__all__ = [
    "delete_object",
    "download_bytes",
    "object_exists",
    "storage_client",
    "upload_bytes",
    "cover_illustration_key",
    "cover_rendered_key",
    "page_render_key",
    "pdf_export_key",
    "reference_key",
    "vignette_key",
]
