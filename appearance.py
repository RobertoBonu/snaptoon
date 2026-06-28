"""Aspetto visivo personalizzato di un progetto.

Schema JSON salvato in Project.appearance. Conversione bidirezionale con
BalloonStyleConfig di snaptoon_core.layout (per il rendering pagine).

Contratto JSON:
{
  "page_bg": "#ffffff",
  "balloon": {
    "text_color": "#000000",
    "outline_color": "#000000",
    "fill_fumetto": "#ffffff",
    "fill_pensiero": "#f0f0f0",
    "font_size": 24
  },
  "caption": {
    "text_color": "#ffffff",
    "outline_color": "#000000",
    "fill": "#000000",
    "font_size": 22
  },
  "sfx": {
    "text_color": "#FFCC00",
    "outline_color": "#000000",
    "font_size": 60
  }
}
"""

from __future__ import annotations

from typing import Any

from snaptoon_core.layout import BalloonStyleConfig


DEFAULT_APPEARANCE: dict[str, Any] = {
    "page_bg": "#ffffff",
    "balloon": {
        "text_color": "#000000",
        "outline_color": "#000000",
        "fill_fumetto": "#ffffff",
        "fill_pensiero": "#f0f0f0",
        "font_size": 24,
    },
    "caption": {
        "text_color": "#ffffff",
        "outline_color": "#000000",
        "fill": "#000000",
        "font_size": 22,
    },
    "sfx": {
        "text_color": "#FFCC00",
        "outline_color": "#000000",
        "font_size": 60,
    },
}


def merge_with_defaults(appearance: dict | None) -> dict:
    """Merge dell'appearance custom con i default, per essere safe su key mancanti."""
    if not appearance:
        return dict(DEFAULT_APPEARANCE)
    result = {
        "page_bg": appearance.get("page_bg", DEFAULT_APPEARANCE["page_bg"]),
        "balloon": {**DEFAULT_APPEARANCE["balloon"], **(appearance.get("balloon") or {})},
        "caption": {**DEFAULT_APPEARANCE["caption"], **(appearance.get("caption") or {})},
        "sfx": {**DEFAULT_APPEARANCE["sfx"], **(appearance.get("sfx") or {})},
    }
    return result


def to_balloon_config(appearance: dict | None) -> BalloonStyleConfig:
    """Converte l'appearance JSON in BalloonStyleConfig per il render."""
    a = merge_with_defaults(appearance)
    return BalloonStyleConfig(
        page_bg=a["page_bg"],
        balloon_text_color=a["balloon"]["text_color"],
        balloon_outline_color=a["balloon"]["outline_color"],
        balloon_fumetto_fill=a["balloon"]["fill_fumetto"],
        balloon_pensiero_fill=a["balloon"]["fill_pensiero"],
        balloon_font_size=a["balloon"]["font_size"],
        caption_text_color=a["caption"]["text_color"],
        caption_outline_color=a["caption"]["outline_color"],
        caption_fill=a["caption"]["fill"],
        caption_font_size=a["caption"]["font_size"],
        sfx_text_color=a["sfx"]["text_color"],
        sfx_outline_color=a["sfx"]["outline_color"],
        sfx_font_size=a["sfx"]["font_size"],
    )
