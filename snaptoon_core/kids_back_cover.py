"""Rendering della quarta di copertina dei libretti KIDS.

Composta programmaticamente con PIL:
  - Sfondo pastello (gradiente ambra→crema o palette coerente)
  - Bordo decorativo
  - Titolo del libretto centrato
  - Sottotitolo (opzionale)
  - Autore
  - Testo editoriale dal template admin (opzionale)
  - Testo copyright del libretto in basso

Il LOGO è compositato separatamente da logo_composite.composite_logo() con
dimensione e posizione controllate dall'admin (px + coordinate X,Y).

Ritorna un file PNG nella dimensione della cover (1024x1536, 2:3 verticale)
pronto per essere inserito come ULTIMA pagina del PDF.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Dimensioni back cover (identiche alla cover per continuità visiva)
BACK_COVER_W = 1024
BACK_COVER_H = 1536

# Palette (coerente col tema SnapToon)
BG_TOP = (255, 245, 220)      # crema chiara
BG_BOTTOM = (245, 220, 200)   # pesca chiara
TEXT_DARK = (60, 40, 30)      # marrone caldo
TEXT_MUTED = (120, 100, 90)   # marrone chiaro
ACCENT = (245, 158, 11)       # ambra SnapToon


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    """Trova un font utilizzabile, con fallback progressive."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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
    subtitle: str = "",
    copyright_text: str = "",
    back_cover_template: str = "",
    out_path: Path,
) -> Path:
    """Genera la quarta di copertina del libretto come immagine PNG (SENZA logo).

    Il logo viene compositato separatamente da composite_logo() a valle,
    con dimensione e posizione controllate dall'admin.

    Args:
        title: Titolo del libretto (obbligatorio)
        author: Autore (es. "Mamma di Lillo")
        subtitle: Sottotitolo (opzionale)
        copyright_text: Testo copyright per la quarta (dal libretto specifico)
        back_cover_template: Testo editoriale sistema-wide (dall'admin)
        out_path: dove salvare il PNG risultante

    Returns:
        out_path (per convenienza)
    """
    canvas = Image.new("RGB", (BACK_COVER_W, BACK_COVER_H), BG_TOP)
    draw = ImageDraw.Draw(canvas)

    # Sfondo con gradiente verticale sottile
    for y in range(BACK_COVER_H):
        t = y / BACK_COVER_H
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (BACK_COVER_W, y)], fill=(r, g, b))

    # Bordo interno decorativo
    margin = 60
    draw.rectangle(
        [(margin, margin), (BACK_COVER_W - margin, BACK_COVER_H - margin)],
        outline=ACCENT,
        width=4,
    )

    # Il testo parte da un offset in alto sufficiente a lasciare spazio
    # a un eventuale logo compositato in alto. Se admin sceglie di piazzarlo
    # altrove (basso, destra, ecc.) questa area rimane libera.
    y = margin + 220

    # === Titolo grande ===
    title_font = _find_font(72)
    title_lines = _wrap_text(title.upper(), title_font, BACK_COVER_W - 200)
    y = _draw_multiline_centered(
        draw, title_lines, title_font, y, BACK_COVER_W, TEXT_DARK,
        line_height_mul=1.15,
    )
    y += 20

    # === Sottotitolo (se presente) ===
    if subtitle.strip():
        sub_font = _find_font(36)
        sub_lines = _wrap_text(subtitle, sub_font, BACK_COVER_W - 200)
        y = _draw_multiline_centered(
            draw, sub_lines, sub_font, y, BACK_COVER_W, TEXT_MUTED,
            line_height_mul=1.3,
        )
        y += 20

    # === Separatore decorativo ===
    sep_y = y + 20
    draw.line(
        [
            (BACK_COVER_W // 2 - 100, sep_y),
            (BACK_COVER_W // 2 + 100, sep_y),
        ],
        fill=ACCENT,
        width=3,
    )
    y = sep_y + 40

    # === Autore ===
    author_label_font = _find_font(28)
    y = _draw_multiline_centered(
        draw, ["di"], author_label_font, y, BACK_COVER_W, TEXT_MUTED,
    )
    y += 5

    author_font = _find_font(52)
    author_lines = _wrap_text(author, author_font, BACK_COVER_W - 200)
    y = _draw_multiline_centered(
        draw, author_lines, author_font, y, BACK_COVER_W, TEXT_DARK,
        line_height_mul=1.2,
    )
    y += 60

    # === Testo editoriale sistema (dal template admin) ===
    if back_cover_template.strip():
        ed_font = _find_font(28)
        ed_lines = _wrap_text(
            back_cover_template.strip(), ed_font, BACK_COVER_W - 200
        )
        # Limita a max 8 righe per non straripare
        ed_lines = ed_lines[:8]
        y = _draw_multiline_centered(
            draw, ed_lines, ed_font, y, BACK_COVER_W, TEXT_MUTED,
            line_height_mul=1.4,
        )
        y += 30

    # === Copyright del libretto in basso ===
    if copyright_text.strip():
        cr_font = _find_font(22)
        cr_lines = _wrap_text(
            copyright_text.strip(), cr_font, BACK_COVER_W - 200
        )
        cr_lines = cr_lines[:5]  # max 5 righe
        # Posizionato in basso, indipendentemente dallo y corrente
        try:
            base_h = cr_font.getbbox("Ay")[3] - cr_font.getbbox("Ay")[1]
        except Exception:
            base_h = 22
        line_h = int(base_h * 1.4)
        total_h = line_h * len(cr_lines)
        cr_y = BACK_COVER_H - margin - 40 - total_h
        _draw_multiline_centered(
            draw, cr_lines, cr_font, cr_y, BACK_COVER_W, TEXT_MUTED,
            line_height_mul=1.4,
        )

    canvas.save(out_path, "PNG")
    return out_path
