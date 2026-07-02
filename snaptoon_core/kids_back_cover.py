"""Rendering della quarta di copertina dei libretti KIDS + Pro.

Layout (v2, minimalista):
  - Sfondo grigio chiaro uniforme #F7F7F7 (no cornice, no gradiente)
  - Titolo grande in ROSSO in alto (uppercase, wrap automatico)
  - Miniatura della COVER del libretto centrata con bordo scuro 5px
  - "di" + autore (uppercase grigio scuro)
  - Testo editoriale sistema-wide (opzionale)
  - Testo copyright del libretto in basso (opzionale)

Il LOGO è compositato separatamente da logo_composite.composite_logo()
con dimensione e posizione controllate dall'admin (px + coordinate X,Y).

Ritorna un file PNG (1024x1536, 2:3 verticale) pronto per essere inserito
come ULTIMA pagina del PDF.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

BACK_COVER_W = 1024
BACK_COVER_H = 1536

# Palette v2 (allineata a mockup Rob)
BG_COLOR = (247, 247, 247)      # #F7F7F7 grigio chiaro uniforme
TITLE_RED = (220, 30, 30)       # rosso vivo per il titolo
AUTHOR_DARK = (85, 85, 85)      # grigio scuro per l'autore (uppercase)
LABEL_MUTED = (140, 140, 140)   # grigio medio per "di" e testo editoriale
COPYRIGHT_MUTED = (150, 150, 150)
COVER_BORDER = (40, 40, 40)     # bordo scuro 5px attorno alla miniatura cover
COVER_BORDER_PX = 5


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Trova un font utilizzabile con fallback progressivi.

    bold=True prova prima le varianti Bold del font.
    """
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/HelveticaNeueBold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap_text(
    text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> list[str]:
    """Wrap semplice del testo per stare dentro max_width pixels."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        candidate = f"{current} {w}".strip()
        try:
            width = font.getbbox(candidate)[2]
        except Exception:
            width = font.getsize(candidate)[0]
        if width <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def _draw_multiline_centered(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    y: int,
    canvas_w: int,
    color: tuple,
    line_height_mul: float = 1.35,
) -> int:
    """Disegna righe centrate orizzontalmente. Ritorna y dopo l'ultima riga."""
    if not lines:
        return y
    try:
        base_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    except Exception:
        base_h = font.getsize("Ay")[1]
    line_h = int(base_h * line_height_mul)

    for line in lines:
        try:
            w = font.getbbox(line)[2] - font.getbbox(line)[0]
        except Exception:
            w = font.getsize(line)[0]
        x = (canvas_w - w) // 2
        draw.text((x, y), line, fill=color, font=font)
        y += line_h
    return y


def render_back_cover(
    *,
    title: str,
    author: str,
    subtitle: str = "",  # non usato nel layout v2 ma mantenuto per API compat
    copyright_text: str = "",
    back_cover_template: str = "",
    cover_bytes: Optional[bytes] = None,
    out_path: Path,
) -> Path:
    """Genera la quarta di copertina come PNG (SENZA logo).

    Layout minimalista allineato al mockup:
      - Sfondo #F7F7F7 uniforme, NESSUNA cornice
      - Titolo grande ROSSO in alto (uppercase, wrap automatico)
      - Miniatura cover centrata con bordo scuro 5px
      - "di" + AUTORE (uppercase grigio scuro)
      - Testo editoriale sistema (opzionale, grigio medio)
      - Copyright in basso (opzionale)

    Il logo viene compositato separatamente da composite_logo() a valle
    (dimensione + posizione da admin).

    Args:
        title: Titolo (obbligatorio, sarà stampato uppercase)
        author: Autore (stampato uppercase)
        subtitle: NON usato nel layout v2 (compat API)
        copyright_text: Testo copyright della quarta
        back_cover_template: Testo editoriale sistema-wide dall'admin
        cover_bytes: PNG della cover del libretto (mostrato come miniatura).
                     Se None, l'area miniatura è vuota.
        out_path: destinazione PNG
    """
    canvas = Image.new("RGB", (BACK_COVER_W, BACK_COVER_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Margini generali
    hmargin = 80    # margine orizzontale (px)
    top_margin = 100

    y = top_margin

    # === Titolo grande rosso ===
    title_font = _find_font(84, bold=True)
    title_lines = _wrap_text(
        title.upper(), title_font, BACK_COVER_W - 2 * hmargin
    )
    y = _draw_multiline_centered(
        draw, title_lines, title_font, y, BACK_COVER_W, TITLE_RED,
        line_height_mul=1.1,
    )
    y += 50

    # === Miniatura cover con bordo scuro ===
    if cover_bytes:
        try:
            cover_img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
            # Ridimensiona a larghezza fissa mantenendo aspect
            target_w = 420
            aspect = cover_img.height / cover_img.width
            target_h = int(target_w * aspect)
            cover_img = cover_img.resize(
                (target_w, target_h), Image.LANCZOS
            )
            # Piazza centrata orizzontalmente
            cx = (BACK_COVER_W - target_w) // 2
            cy = y
            # Bordo: disegna rettangolo scuro dietro + paste cover
            draw.rectangle(
                [
                    (cx - COVER_BORDER_PX, cy - COVER_BORDER_PX),
                    (cx + target_w + COVER_BORDER_PX,
                     cy + target_h + COVER_BORDER_PX),
                ],
                fill=COVER_BORDER,
            )
            canvas.paste(cover_img, (cx, cy))
            y = cy + target_h + COVER_BORDER_PX + 50
        except Exception:
            # Se la cover è malformata, salta senza bloccare
            y += 40

    # === "di" ===
    di_font = _find_font(34)
    y = _draw_multiline_centered(
        draw, ["di"], di_font, y, BACK_COVER_W, LABEL_MUTED,
    )
    y += 10

    # === Autore (uppercase grigio scuro, bold) ===
    author_font = _find_font(56, bold=True)
    author_lines = _wrap_text(
        author.upper(), author_font, BACK_COVER_W - 2 * hmargin
    )
    y = _draw_multiline_centered(
        draw, author_lines, author_font, y, BACK_COVER_W, AUTHOR_DARK,
        line_height_mul=1.15,
    )
    y += 60

    # === Testo editoriale sistema (opzionale) ===
    if back_cover_template.strip():
        ed_font = _find_font(28)
        ed_lines = _wrap_text(
            back_cover_template.strip(),
            ed_font, BACK_COVER_W - 2 * hmargin,
        )
        ed_lines = ed_lines[:8]
        y = _draw_multiline_centered(
            draw, ed_lines, ed_font, y, BACK_COVER_W, LABEL_MUTED,
            line_height_mul=1.4,
        )
        y += 30

    # === Copyright in basso (posizionato in fondo indipendentemente) ===
    if copyright_text.strip():
        cr_font = _find_font(22)
        cr_lines = _wrap_text(
            copyright_text.strip(), cr_font, BACK_COVER_W - 2 * hmargin,
        )
        cr_lines = cr_lines[:5]
        try:
            base_h = cr_font.getbbox("Ay")[3] - cr_font.getbbox("Ay")[1]
        except Exception:
            base_h = 22
        line_h = int(base_h * 1.4)
        total_h = line_h * len(cr_lines)
        cr_y = BACK_COVER_H - 100 - total_h
        _draw_multiline_centered(
            draw, cr_lines, cr_font, cr_y, BACK_COVER_W, COPYRIGHT_MUTED,
            line_height_mul=1.4,
        )

    canvas.save(out_path, "PNG")
    return out_path
