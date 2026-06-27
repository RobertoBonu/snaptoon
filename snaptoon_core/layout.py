"""Impaginazione — rendering di una pagina con vignette + balloon.

Una pagina è un'immagine PIL composta da:
  - una griglia (GridTemplate) che definisce posizione/dimensione delle celle
  - le vignette generate ridimensionate per riempire le celle
  - balloon overlay coi dialoghi della sceneggiatura, disegnati sopra

Rendering qualitativo:
  - Supersampling 2× (disegno a doppia risoluzione, downscale LANCZOS finale)
  - Font specifici per kind (Marker Felt / Helvetica / Impact)
  - Tail (coda) sui balloon di dialogo/pensiero
  - Drop shadow leggera per profondità
  - Forme curate (cloud con bumps organici, burst irregolare)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .models import Cover, Dialogue, Panel, TextBox

# Forme balloon supportate e default per kind
SHAPES = ["oval", "rounded_rect", "rect", "cloud", "burst"]
DEFAULT_SHAPE: dict[str, str] = {
    "FUMETTO": "oval",
    # PENSIERO: balloon ovale "liscio" + tail a bollicine (vedi _draw_tail
    # style='cloud'). Il vero indicatore di pensiero è la TAIL a bollicine,
    # non i lobi attorno al balloon. Per ottenere il look "cloud con lobi"
    # vecchio stile, l'utente può cambiare la forma nel selector.
    "PENSIERO": "oval",
    "DIDASCALIA": "rect",
    "SFX": "burst",
}

# Formato A4 a 150dpi
PAGE_W = 1240
PAGE_H = 1754
MARGIN = 60
GUTTER = 18
BORDER = 4

# Supersampling: tutto il rendering avviene a 2× e viene downscalato alla fine
RENDER_SCALE = 2


@dataclass
class GridCell:
    x: int
    y: int
    w: int
    h: int

    def scaled(self, s: int) -> "GridCell":
        return GridCell(self.x * s, self.y * s, self.w * s, self.h * s)


@dataclass
class GridTemplate:
    id: str
    name: str
    cells_normalized: list[tuple[float, float, float, float]]

    @property
    def capacity(self) -> int:
        return len(self.cells_normalized)

    def cells(self, page_w: int = PAGE_W, page_h: int = PAGE_H) -> list[GridCell]:
        inner_w = page_w - 2 * MARGIN
        inner_h = page_h - 2 * MARGIN
        out: list[GridCell] = []
        for (xp, yp, wp, hp) in self.cells_normalized:
            out.append(
                GridCell(
                    x=MARGIN + int(xp * inner_w),
                    y=MARGIN + int(yp * inner_h),
                    w=int(wp * inner_w),
                    h=int(hp * inner_h),
                )
            )
        return out


def _grid_from_rows(rows: list[int]) -> list[tuple[float, float, float, float]]:
    inner_w = PAGE_W - 2 * MARGIN
    inner_h = PAGE_H - 2 * MARGIN
    gutter_x_ratio = GUTTER / inner_w
    gutter_y_ratio = GUTTER / inner_h
    n_rows = len(rows)
    row_h = (1.0 - gutter_y_ratio * (n_rows - 1)) / n_rows
    cells: list[tuple[float, float, float, float]] = []
    y = 0.0
    for n_cols in rows:
        cell_w = (1.0 - gutter_x_ratio * (n_cols - 1)) / n_cols
        for c in range(n_cols):
            x = c * (cell_w + gutter_x_ratio)
            cells.append((x, y, cell_w, row_h))
        y += row_h + gutter_y_ratio
    return cells


GRIDS: dict[str, GridTemplate] = {
    "splash": GridTemplate("splash", "Splash (1)", _grid_from_rows([1])),
    "2x1": GridTemplate("2x1", "2 in riga (1×2)", _grid_from_rows([2])),
    "1x2": GridTemplate("1x2", "2 in colonna (2×1)", _grid_from_rows([1, 1])),
    "3x1": GridTemplate("3x1", "3 in riga (1×3)", _grid_from_rows([3])),
    "1x3": GridTemplate("1x3", "3 in colonna (3×1)", _grid_from_rows([1, 1, 1])),
    "1+2": GridTemplate("1+2", "1 grande + 2 sotto", _grid_from_rows([1, 2])),
    "2+1": GridTemplate("2+1", "2 sopra + 1 grande", _grid_from_rows([2, 1])),
    "2x2": GridTemplate("2x2", "Griglia 2×2 (4)", _grid_from_rows([2, 2])),
    "1+3": GridTemplate("1+3", "1 grande + 3 sotto (4)", _grid_from_rows([1, 3])),
    "3+1": GridTemplate("3+1", "3 sopra + 1 grande (4)", _grid_from_rows([3, 1])),
    "1+1+2": GridTemplate("1+1+2", "1 + 1 + 2 (4)", _grid_from_rows([1, 1, 2])),
    "2+3": GridTemplate("2+3", "2 sopra + 3 sotto (5)", _grid_from_rows([2, 3])),
    "3+2": GridTemplate("3+2", "3 sopra + 2 sotto (5)", _grid_from_rows([3, 2])),
    "1+2+2": GridTemplate("1+2+2", "1 grande + 2 + 2 (5, cinematografico)", _grid_from_rows([1, 2, 2])),
    "3x2": GridTemplate("3x2", "Griglia 3×2 (6)", _grid_from_rows([3, 3])),
    "2x3": GridTemplate("2x3", "Griglia 2×3 verticale (6)", _grid_from_rows([2, 2, 2])),
    "2+2+2": GridTemplate("2+2+2", "3 righe da 2 (6, bonelliana)", _grid_from_rows([2, 2, 2])),
    "1+2+3": GridTemplate("1+2+3", "1 + 2 + 3 crescendo (6)", _grid_from_rows([1, 2, 3])),
    "3+2+1": GridTemplate("3+2+1", "3 + 2 + 1 decrescendo (6)", _grid_from_rows([3, 2, 1])),
    "1+4+1": GridTemplate("1+4+1", "Splash + striscia 4 + splash (6, cinematografica)", _grid_from_rows([1, 4, 1])),
    "2+4": GridTemplate("2+4", "2 grandi + 4 piccole (6)", _grid_from_rows([2, 4])),
    "4+2": GridTemplate("4+2", "4 piccole + 2 grandi (6)", _grid_from_rows([4, 2])),
    "1+1+4": GridTemplate("1+1+4", "2 splash + striscia 4 (6)", _grid_from_rows([1, 1, 4])),
    "1+3+3": GridTemplate("1+3+3", "1 grande + 3 + 3 (7)", _grid_from_rows([1, 3, 3])),
    "3+3+1": GridTemplate("3+3+1", "3 + 3 + 1 grande (7)", _grid_from_rows([3, 3, 1])),
    "2x4": GridTemplate("2x4", "Griglia 2×4 verticale (8)", _grid_from_rows([2, 2, 2, 2])),
    "4x2": GridTemplate("4x2", "Griglia 4×2 (8)", _grid_from_rows([4, 4])),
    "3x3": GridTemplate("3x3", "Griglia 3×3 (9)", _grid_from_rows([3, 3, 3])),
}

DEFAULT_GRID = "2x2"


def default_grid_for(n_panels: int | None) -> str:
    if n_panels is None:
        return DEFAULT_GRID
    return {
        1: "splash", 2: "1x2", 3: "1x3", 4: "2x2", 5: "1+2+2",
        6: "3x2", 7: "1+3+3", 8: "2x4", 9: "3x3",
    }.get(n_panels, DEFAULT_GRID)


def grids_for_capacity(n_panels: int) -> list[str]:
    return [gid for gid, g in GRIDS.items() if g.capacity == n_panels]


# ============================================================
# Font: registry centralizzato con label + path + fallback
# ============================================================

# Ogni voce: id → (path, index, display_label)
# I path sono macOS-specific; il fallback ad Arial copre il caso file mancante.
FONT_REGISTRY: dict[str, tuple[str, int, str]] = {
    "marker_felt":      ("/System/Library/Fonts/MarkerFelt.ttc", 0, "Marker Felt (fumetto)"),
    "bradley_hand":     ("/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf", 0, "Bradley Hand (manoscritto)"),
    "comic_sans":       ("/System/Library/Fonts/Supplemental/Comic Sans MS.ttf", 0, "Comic Sans MS"),
    "comic_sans_bold":  ("/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf", 0, "Comic Sans MS Bold"),
    "chalkboard":       ("/System/Library/Fonts/Supplemental/Chalkboard.ttc", 0, "Chalkboard"),
    "chalkduster":      ("/System/Library/Fonts/Supplemental/Chalkduster.ttf", 0, "Chalkduster"),
    "helvetica":        ("/System/Library/Fonts/Helvetica.ttc", 0, "Helvetica"),
    "arial":            ("/System/Library/Fonts/Supplemental/Arial.ttf", 0, "Arial"),
    "impact":           ("/System/Library/Fonts/Supplemental/Impact.ttf", 0, "Impact (per SFX)"),
}

FONT_FALLBACK_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"


def _font_by_id(font_id: str, size: int) -> ImageFont.FreeTypeFont:
    """Carica un font dal registry. Fallback ad Arial, poi al font di default."""
    entry = FONT_REGISTRY.get(font_id)
    if entry:
        path, idx, _ = entry
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            pass
    try:
        return ImageFont.truetype(FONT_FALLBACK_PATH, size)
    except Exception:
        return ImageFont.load_default(size=size)


# Default font per kind (usato se la config non specifica)
DEFAULT_FONT_BY_KIND: dict[str, str] = {
    "FUMETTO": "marker_felt",
    "PENSIERO": "marker_felt",
    "DIDASCALIA": "helvetica",
    "SFX": "impact",
}


@dataclass(frozen=True)
class BalloonStyleConfig:
    """Personalizzazione visiva di balloon, caption, SFX e sfondo pagina.

    Tutti i colori sono stringhe esadecimali ("#RRGGBB"). I font sono `id`
    del FONT_REGISTRY. Le dimensioni sono in unità logiche (vengono
    moltiplicate per RENDER_SCALE = 2 in fase di rendering).
    """
    page_bg: str = "#ffffff"

    # FUMETTO + PENSIERO (condividono font e text color)
    balloon_font_id: str = "marker_felt"
    balloon_font_size: int = 22
    balloon_text_color: str = "#000000"
    balloon_outline_color: str = "#1a1a1a"
    balloon_fumetto_fill: str = "#ffffff"
    balloon_pensiero_fill: str = "#f7f7f7"
    # Tratto Graphic Novel
    balloon_outline_width: int = 5
    balloon_speed_lines: bool = True
    balloon_jitter: bool = True
    balloon_padding: int = 14

    # DIDASCALIA (caption)
    caption_font_id: str = "helvetica"
    caption_font_size: int = 22
    caption_text_color: str = "#000000"
    caption_outline_color: str = "#1a1a1a"
    caption_fill: str = "#fff8d4"

    # SFX
    sfx_font_id: str = "impact"
    sfx_font_size: int = 56
    sfx_text_color: str = "#d32f2f"
    sfx_outline_color: str = "#7a1010"
    sfx_fill: str = "#fff7a3"


# Default singleton da usare quando non viene passato un cfg
_DEFAULT_CFG = BalloonStyleConfig()


def _font_for_cfg(kind: str, size: int, cfg: BalloonStyleConfig) -> ImageFont.FreeTypeFont:
    """Sceglie il font giusto in base al kind, leggendo dal cfg."""
    if kind == "FUMETTO" or kind == "PENSIERO":
        return _font_by_id(cfg.balloon_font_id, size)
    if kind == "DIDASCALIA":
        return _font_by_id(cfg.caption_font_id, size)
    if kind == "SFX":
        return _font_by_id(cfg.sfx_font_id, size)
    return _font_by_id("arial", size)


# Backwards-compatible: alias usato in altri punti del file
def _font_for_kind(kind: str, size: int) -> ImageFont.FreeTypeFont:
    return _font_for_cfg(kind, size, _DEFAULT_CFG)


def _text_size(font, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _wrap(text: str, font, max_w: int) -> list[str]:
    """Word-wrap che RISPETTA i `\\n` espliciti come a capo forzati.

    Logica: il testo viene prima diviso sui newline (a capo manuali della
    sceneggiatura), poi ciascun segmento subisce word-wrap automatico in
    base a `max_w`. Permette di forzare un'andatura precisa nei balloon
    senza dover affidarsi solo all'auto-wrap.
    """
    if not text:
        return []
    out: list[str] = []
    for chunk in text.split("\n"):
        if not chunk:
            out.append("")  # riga intenzionalmente vuota (paragrafo)
            continue
        words = chunk.split()
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            if _text_size(font, test)[0] <= max_w:
                current = test
            else:
                if current:
                    out.append(current)
                current = w
        if current:
            out.append(current)
    return out


# ============================================================
# Shape drawing — più curato, con shadow opzionale
# ============================================================

def _draw_shadow(
    base_img: Image.Image,
    shape: str,
    x0: int, y0: int, x1: int, y1: int,
    *,
    offset: tuple[int, int] = (4, 4),
    blur: int = 6,
    alpha: int = 100,
) -> None:
    """Disegna una drop shadow sotto la forma, su un layer separato che
    viene blurrato e composito sull'immagine base."""
    bw, bh = base_img.size
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    sx0, sy0 = x0 + offset[0], y0 + offset[1]
    sx1, sy1 = x1 + offset[0], y1 + offset[1]
    if shape == "rect":
        ldraw.rectangle([(sx0, sy0), (sx1, sy1)], fill=(0, 0, 0, alpha))
    elif shape == "rounded_rect":
        radius = max(8, min(sx1 - sx0, sy1 - sy0) // 5)
        ldraw.rounded_rectangle([(sx0, sy0), (sx1, sy1)], radius=radius, fill=(0, 0, 0, alpha))
    elif shape == "burst":
        cx = (sx0 + sx1) // 2
        cy = (sy0 + sy1) // 2
        r_outer = min(sx1 - sx0, sy1 - sy0) // 2
        r_inner = int(r_outer * 0.55)
        n_pts = 12
        pts = []
        for i in range(n_pts * 2):
            ang = math.pi * i / n_pts - math.pi / 2
            r = r_outer if i % 2 == 0 else r_inner
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        ldraw.polygon(pts, fill=(0, 0, 0, alpha))
    else:  # oval, cloud
        ldraw.ellipse([(sx0, sy0), (sx1, sy1)], fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base_img.paste(layer, (0, 0), layer)


def _draw_shape(
    draw: ImageDraw.ImageDraw,
    x0: int, y0: int, x1: int, y1: int,
    shape: str,
    *,
    fill: str = "white",
    outline: str = "black",
    width: int = 2,
    seed: int = 0,
) -> None:
    """Disegna la forma del balloon nel bounding box."""
    if shape == "rect":
        draw.rectangle([(x0, y0), (x1, y1)], fill=fill, outline=outline, width=width)
    elif shape == "rounded_rect":
        radius = max(8, min(x1 - x0, y1 - y0) // 5)
        draw.rounded_rectangle(
            [(x0, y0), (x1, y1)], radius=radius, fill=fill, outline=outline, width=width
        )
    elif shape == "cloud":
        # Ovale base + 8-10 bumps organici lungo il perimetro
        draw.ellipse([(x0, y0), (x1, y1)], fill=fill, outline=outline, width=width)
        rnd = random.Random(seed)
        box_w = x1 - x0
        box_h = y1 - y0
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = box_w / 2
        ry = box_h / 2
        n_bumps = 10
        for i in range(n_bumps):
            ang = (i / n_bumps) * 2 * math.pi
            jitter = rnd.uniform(-0.08, 0.08)
            ang += jitter
            # Punto sul perimetro
            px = cx + rx * math.cos(ang)
            py = cy + ry * math.sin(ang)
            bump_size = rnd.uniform(0.18, 0.30) * min(box_w, box_h)
            half = int(bump_size / 2)
            draw.ellipse(
                [(int(px - half), int(py - half)), (int(px + half), int(py + half))],
                fill=fill, outline=outline, width=width,
            )
        # Ridisegna l'ellisse interna per coprire i bordi interni dei bumps
        inset = max(4, width * 2)
        draw.ellipse(
            [(x0 + inset, y0 + inset), (x1 - inset, y1 - inset)],
            fill=fill, outline=None,
        )
    elif shape == "burst":
        # Stella a 10-12 punte con vertici jitterati per look organico
        rnd = random.Random(seed)
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        r_outer = min(x1 - x0, y1 - y0) // 2
        r_inner = int(r_outer * 0.55)
        n_pts = 11
        pts: list[tuple[float, float]] = []
        for i in range(n_pts * 2):
            ang = math.pi * i / n_pts - math.pi / 2
            r = r_outer if i % 2 == 0 else r_inner
            # Jitter leggero per organicità
            r *= rnd.uniform(0.92, 1.08)
            ang += rnd.uniform(-0.04, 0.04)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "oval_jitter":
        # Ovale "drawn by hand" — poligono di N punti sul perimetro con
        # piccolo offset radiale random (deterministico via seed).
        # Riproduce l'imperfezione del contorno tracciato a mano.
        rnd = random.Random(seed)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        n_pts = 56  # abbastanza fitti da sembrare curvi
        pts: list[tuple[float, float]] = []
        for i in range(n_pts):
            ang = (i / n_pts) * 2 * math.pi
            # Jitter radiale ±3% del raggio: percepibile ma non grottesco
            jx = rnd.uniform(-0.03, 0.03)
            jy = rnd.uniform(-0.03, 0.03)
            px = cx + rx * (1 + jx) * math.cos(ang)
            py = cy + ry * (1 + jy) * math.sin(ang)
            pts.append((px, py))
        draw.polygon(pts, fill=fill, outline=outline)
        # PIL non offre width per polygon.outline → ridisegno i lati manualmente
        # per garantire spessore uniforme del contorno.
        for i in range(n_pts):
            a = pts[i]
            b = pts[(i + 1) % n_pts]
            draw.line([a, b], fill=outline, width=width)
    else:  # "oval"
        draw.ellipse([(x0, y0), (x1, y1)], fill=fill, outline=outline, width=width)


def _draw_tail(
    draw: ImageDraw.ImageDraw,
    balloon_x0: int, balloon_y0: int, balloon_x1: int, balloon_y1: int,
    *,
    origin_xy: tuple[int, int] | None = None,
    length_px: int = 60,
    base_px: int = 18,
    fill: str = "white",
    outline: str = "black",
    width: int = 2,
    style: str = "oval",  # "oval" → wedge triangolare, "cloud" → bollicine
) -> None:
    """Disegna la tail del balloon.

    Nuovo schema (semplice): la tail parte da `origin_xy` (un punto sul
    balloon) e si estende per `length_px` verso l'esterno. Direzione =
    dal centro del balloon attraverso origin.

    Parametri:
      origin_xy: punto da cui parte la tail. None = centro-bottom (legacy).
      length_px: lunghezza della tail dal balloon al tip.
      base_px: larghezza della base (lato che si attacca al balloon).
    """
    cx = (balloon_x0 + balloon_x1) / 2
    cy = (balloon_y0 + balloon_y1) / 2
    if origin_xy is None:
        ox, oy = cx, balloon_y1 - 2
    else:
        ox, oy = origin_xy

    # Direzione: dal centro del balloon verso origin (uscita radiale).
    # Caso degenere (origin = centro): default "giù".
    dx = ox - cx
    dy = oy - cy
    norm = math.sqrt(dx * dx + dy * dy)
    if norm < 1.0:
        ux, uy = 0.0, 1.0  # default verso il basso
    else:
        ux, uy = dx / norm, dy / norm
    # Tip = origin + direzione_unit * length
    tx = ox + ux * length_px
    ty = oy + uy * length_px

    if style == "cloud":
        # 3 bollicine decrescenti da origin verso il tip
        for i, frac in enumerate([0.35, 0.65, 0.9]):
            bx = ox + (tx - ox) * frac
            by = oy + (ty - oy) * frac
            size = max(4, int((base_px / 2) * (1.0 - i * 0.25)))
            draw.ellipse(
                [(int(bx - size), int(by - size)), (int(bx + size), int(by + size))],
                fill=fill, outline=outline, width=width,
            )
        return

    # Wedge: base perpendicolare alla direzione (ux, uy).
    px = -uy
    py = ux
    half_base = max(3, base_px // 2)
    # INSET: sposto la base leggermente DENTRO il balloon (controdirezione)
    # così il fill della tail sovrasta l'arco del contorno e la giunzione
    # appare continua. Senza inset, il bordo nero del balloon resta visibile
    # tra i due lati del wedge → tail "staccata".
    inset = max(width + 2, 4)
    ox_in = ox - ux * inset
    oy_in = oy - uy * inset
    a1 = (ox_in + px * half_base, oy_in + py * half_base)
    a2 = (ox_in - px * half_base, oy_in - py * half_base)
    tip = (tx, ty)
    # Riempi il triangolo (la base è dentro il balloon, copre il bordo)
    draw.polygon([a1, a2, tip], fill=fill, outline=None)
    # I due lati del wedge come outline. Disegnati dalla posizione esterna
    # (sul bordo) verso il tip, non dall'interno, per evitare di "sbordare"
    # dentro il balloon. Calcolo l'intersezione con il bordo radiale:
    # parto dai punti sul bordo (ox, oy) ± half_base*perp.
    edge1 = (ox + px * half_base, oy + py * half_base)
    edge2 = (ox - px * half_base, oy - py * half_base)
    draw.line([edge1, tip], fill=outline, width=width)
    draw.line([edge2, tip], fill=outline, width=width)


def _resolve_shape(dialogue: Dialogue) -> str:
    if dialogue.shape and dialogue.shape in SHAPES:
        return dialogue.shape
    return DEFAULT_SHAPE.get(dialogue.kind, "oval")


def _seed_for(dialogue: Dialogue) -> int:
    """Seed deterministico per shape randomizzate (cloud, burst)."""
    return abs(hash(dialogue.text + dialogue.kind)) % (2**31)


def _draw_speed_lines(
    draw: ImageDraw.ImageDraw,
    x0: int, y0: int, x1: int, y1: int,
    *,
    color: str = "#000000",
    width: int = 3,
    seed: int = 0,
) -> None:
    """Disegna 4-6 piccoli tratti decorativi vicini al bordo del balloon.

    Imitano il "drawn motion" tipico delle graphic novel: trattini paralleli
    al perimetro, di lunghezza 12-20 px, distanziati 6-10 px dal contorno.
    Posizionati su angoli e lati, mai a coprire la tail (in basso).
    """
    rnd = random.Random(seed ^ 0xBADA55)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    w = x1 - x0
    h = y1 - y0
    # 5 "ancore" angolari/laterali. Ogni ancora produce 2-3 trattini paralleli.
    # Evito il basso-centro per non interferire con la tail.
    anchors = [
        (-0.95, -0.55),  # top-left
        (0.95, -0.55),   # top-right
        (-1.05, 0.0),    # mid-left
        (1.05, 0.0),     # mid-right
        (0.55, -0.95),   # upper-right
    ]
    for ax, ay in anchors:
        # Posizione base appena fuori dal bordo
        bx = cx + ax * (w / 2)
        by = cy + ay * (h / 2)
        # Direzione: radiale verso l'esterno
        dxr = ax
        dyr = ay
        norm = math.sqrt(dxr * dxr + dyr * dyr) or 1.0
        dxr /= norm
        dyr /= norm
        # Tangente al perimetro (perpendicolare alla radiale)
        tx, ty = -dyr, dxr
        n_marks = rnd.randint(2, 3)
        for k in range(n_marks):
            length = rnd.uniform(14, 24)
            # offset lungo la tangente per spaziare i trattini
            offset = (k - (n_marks - 1) / 2) * 10
            sx = bx + tx * offset
            sy = by + ty * offset
            ex = sx + dxr * length
            ey = sy + dyr * length
            draw.line([(sx, sy), (ex, ey)], fill=color, width=width)


# ============================================================
# Balloon rendering
# ============================================================

def _draw_balloon(
    page_img: Image.Image,
    draw: ImageDraw.ImageDraw,
    cell: GridCell,
    y_cursor: int,
    dialogue: Dialogue,
    *,
    anchor_xy: tuple[int, int] | None = None,
    scale: int = 1,
    cfg: BalloonStyleConfig | None = None,
) -> int:
    """Disegna un balloon completo (shadow + shape + tail + testo)."""
    cfg = cfg or _DEFAULT_CFG
    pad = max(2, cfg.balloon_padding) * scale
    max_w = int(cell.w * 0.82)
    shape = _resolve_shape(dialogue)
    seed = _seed_for(dialogue)

    if anchor_xy is not None:
        x_center, y_top = anchor_xy
    else:
        x_center = cell.x + cell.w // 2
        y_top = y_cursor

    # --- SFX (testo grande + opzionale forma burst) ---
    if dialogue.kind == "SFX":
        font_size = cfg.sfx_font_size * scale
        font = _font_for_cfg("SFX", font_size, cfg)
        text = dialogue.text.upper()
        lines = _wrap(text, font, max_w)
        if not lines:
            return y_top + 8 * scale
        line_h = font.getbbox("Ag")[3] + 4 * scale
        text_h = line_h * len(lines)
        text_w = max(_text_size(font, line)[0] for line in lines)

        if shape == "burst":
            box_w = text_w + pad * 4
            box_h = text_h + pad * 4
            x0 = x_center - box_w // 2
            y0 = y_top
            _draw_shadow(page_img, "burst", x0, y0, x0 + box_w, y0 + box_h,
                         offset=(3 * scale, 3 * scale), blur=4 * scale, alpha=90)
            _draw_shape(draw, x0, y0, x0 + box_w, y0 + box_h, "burst",
                        fill=cfg.sfx_fill, outline=cfg.sfx_outline_color,
                        width=max(2, 3 * scale), seed=seed)
            ty = y0 + (box_h - text_h) // 2
            for line in lines:
                tw = _text_size(font, line)[0]
                draw.text(
                    (x_center - tw // 2, ty),
                    line, fill=cfg.sfx_text_color, font=font,
                    stroke_width=max(1, 2 * scale), stroke_fill="white",
                )
                ty += line_h
            return y0 + box_h + 12 * scale
        else:
            for line in lines:
                tw = _text_size(font, line)[0]
                draw.text(
                    (x_center - tw // 2, y_top),
                    line, fill=cfg.sfx_text_color, font=font,
                    stroke_width=max(2, 3 * scale), stroke_fill="white",
                )
                y_top += line_h
            return y_top + 8 * scale

    # --- DIDASCALIA (riquadro narrante) ---
    if dialogue.kind == "DIDASCALIA":
        font_size = cfg.caption_font_size * scale
        font = _font_for_cfg("DIDASCALIA", font_size, cfg)
        lines = _wrap(dialogue.text, font, max_w - pad * 2)
        line_h = font.getbbox("Ag")[3] + 4 * scale
        text_h = line_h * len(lines) if lines else line_h
        box_h = text_h + pad * 2
        box_w = min(
            (max(_text_size(font, line)[0] for line in lines) + pad * 2) if lines else 100 * scale,
            max_w,
        )
        if anchor_xy is not None:
            x0 = x_center - box_w // 2
            y0 = y_top
        else:
            x0 = cell.x + 16 * scale
            y0 = y_top

        _draw_shadow(page_img, shape, x0, y0, x0 + box_w, y0 + box_h,
                     offset=(3 * scale, 4 * scale), blur=5 * scale, alpha=80)
        _draw_shape(draw, x0, y0, x0 + box_w, y0 + box_h, shape,
                    fill=cfg.caption_fill, outline=cfg.caption_outline_color,
                    width=max(2, 2 * scale), seed=seed)
        for i, line in enumerate(lines):
            draw.text((x0 + pad, y0 + pad + i * line_h), line,
                      fill=cfg.caption_text_color, font=font)
        return y0 + box_h + 10 * scale

    # --- FUMETTO / PENSIERO ---
    # Lo speaker NON viene mai disegnato dentro al balloon: la tail già
    # identifica chi parla. Il campo `speaker` è solo metadato di
    # sceneggiatura. (Per attribuire un voice-over o chi pensa fuori scena,
    # usa una DIDASCALIA — quella sì può portare "SPEAKER:" nel testo.)
    font_size = cfg.balloon_font_size * scale
    font = _font_for_cfg(dialogue.kind, font_size, cfg)

    # Larghezza disponibile per il wrap:
    #  - Se l'utente ha forzato box_width_pct → wrappa a quella (così il
    #    testo va a capo ESATTAMENTE alla dimensione del balloon scelta).
    #  - Altrimenti → wrap su max_w (= 82% della cella, comportamento auto).
    # In più _wrap rispetta gli \n del testo come a capo forzati.
    if dialogue.box_width_pct is not None:
        forced_w = int(max(0.05, min(1.0, dialogue.box_width_pct)) * cell.w)
        wrap_w = max(20 * scale, forced_w - pad * 2)
    else:
        wrap_w = max_w - pad * 2

    lines = _wrap(dialogue.text, font, wrap_w)
    line_h = font.getbbox("Ag")[3] + 4 * scale
    text_h = line_h * len(lines)
    text_w = max(_text_size(font, line)[0] for line in lines) if lines else 60 * scale

    extra_w = pad * 4 if shape in ("oval", "cloud") else pad * 2
    extra_h = pad * 2 if shape in ("rect", "rounded_rect") else pad * 3
    box_w = min(text_w + extra_w, max_w)
    box_h = text_h + extra_h
    # Override manuale dimensione balloon (% della cella) — dimensione vincente
    if dialogue.box_width_pct is not None:
        box_w = int(max(0.05, min(1.0, dialogue.box_width_pct)) * cell.w)
    if dialogue.box_height_pct is not None:
        box_h = int(max(0.05, min(1.0, dialogue.box_height_pct)) * cell.h)
    x0 = x_center - box_w // 2
    y0 = y_top

    fill_color = cfg.balloon_fumetto_fill if dialogue.kind == "FUMETTO" else cfg.balloon_pensiero_fill
    outline_w = max(2, cfg.balloon_outline_width * scale)

    # Shadow soft (più diffusa per look graphic-novel)
    _draw_shadow(page_img, shape, x0, y0, x0 + box_w, y0 + box_h,
                 offset=(4 * scale, 5 * scale), blur=7 * scale, alpha=95)
    # Forma — se jitter attivo e shape è ovale, usa la variante "drawn"
    effective_shape = shape
    if cfg.balloon_jitter and shape == "oval":
        effective_shape = "oval_jitter"
    _draw_shape(draw, x0, y0, x0 + box_w, y0 + box_h, effective_shape,
                fill=fill_color, outline=cfg.balloon_outline_color,
                width=outline_w, seed=seed)
    # Speed lines decorative attorno al balloon (opzionale dallo Style)
    if cfg.balloon_speed_lines and dialogue.kind in ("FUMETTO", "PENSIERO"):
        _draw_speed_lines(
            draw, x0, y0, x0 + box_w, y0 + box_h,
            color=cfg.balloon_outline_color,
            width=max(2, (outline_w * 2) // 3),
            seed=seed,
        )
    # Tail (solo per FUMETTO/PENSIERO; ignorata per DIDASCALIA/SFX)
    if dialogue.kind in ("FUMETTO", "PENSIERO") and dialogue.show_tail:
        # Origin: dal preset 3×3 oppure default centro-bottom
        if dialogue.tail_origin_x is not None and dialogue.tail_origin_y is not None:
            ox_frac = max(0.0, min(1.0, dialogue.tail_origin_x))
            oy_frac = max(0.0, min(1.0, dialogue.tail_origin_y))
            tail_ox = x0 + int(ox_frac * box_w)
            tail_oy = y0 + int(oy_frac * box_h)
            origin_xy = (tail_ox, tail_oy)
        else:
            origin_xy = None  # centro-bottom legacy dentro _draw_tail

        # Lunghezza/base: parametri user (px logici, scalati per supersampling)
        length_px = (dialogue.tail_length_px or 60) * scale
        base_px = (dialogue.tail_base_px or 18) * scale
        tail_style = "cloud" if dialogue.kind == "PENSIERO" else "oval"
        _draw_tail(draw, x0, y0, x0 + box_w, y0 + box_h,
                   origin_xy=origin_xy,
                   length_px=length_px, base_px=base_px,
                   fill=fill_color, outline=cfg.balloon_outline_color,
                   width=outline_w, style=tail_style)

    # Testo — centrato sia orizzontalmente sia verticalmente nel box.
    # (box_h - text_h) // 2 funziona sia per dimensione auto che manuale:
    # quando auto, box_h = text_h + extra_h → (box_h - text_h)/2 = extra_h/2.
    text_block_y = y0 + max(0, (box_h - text_h) // 2)
    for i, line in enumerate(lines):
        lw = _text_size(font, line)[0]
        draw.text(
            (x_center - lw // 2, text_block_y + i * line_h),
            line, fill=cfg.balloon_text_color, font=font,
        )

    after_h = box_h + (60 * scale)
    return y0 + after_h


def _draw_balloons(
    page_img: Image.Image,
    draw: ImageDraw.ImageDraw,
    cell: GridCell,
    dialogues: list[Dialogue],
    *,
    scale: int = 1,
    cfg: BalloonStyleConfig | None = None,
) -> None:
    """Disegna i balloon di una cella."""
    cfg = cfg or _DEFAULT_CFG
    auto_dialogues: list[Dialogue] = []
    for d in dialogues:
        if d.position_x is not None and d.position_y is not None:
            px = max(0.0, min(1.0, d.position_x))
            py = max(0.0, min(1.0, d.position_y))
            anchor = (
                cell.x + int(px * cell.w),
                cell.y + int(py * cell.h),
            )
            _draw_balloon(page_img, draw, cell, anchor[1], d,
                          anchor_xy=anchor, scale=scale, cfg=cfg)
        else:
            auto_dialogues.append(d)

    y_cursor = cell.y + 18 * scale
    for d in auto_dialogues:
        if y_cursor > cell.y + cell.h - 30 * scale:
            break
        y_cursor = _draw_balloon(page_img, draw, cell, y_cursor, d, scale=scale, cfg=cfg)


# ============================================================
# Page rendering (con supersampling 2×)
# ============================================================

def render_page(
    panels_with_images: list[tuple[Panel, Path | None]],
    grid: GridTemplate,
    out_path: Path,
    *,
    show_balloons: bool = True,
    page_label: str = "",
    cfg: BalloonStyleConfig | None = None,
) -> Path:
    """Renderizza una pagina con supersampling 2×: tutto disegnato a doppia
    risoluzione, poi downscale finale con LANCZOS per anti-aliasing pulito.
    """
    cfg = cfg or _DEFAULT_CFG
    s = RENDER_SCALE
    page_w = PAGE_W * s
    page_h = PAGE_H * s

    page = Image.new("RGB", (page_w, page_h), cfg.page_bg)
    draw = ImageDraw.Draw(page)

    cells_hi = [c.scaled(s) for c in grid.cells()]
    panels = panels_with_images[: grid.capacity]

    for cell, (panel, img_path) in zip(cells_hi, panels):
        if img_path and img_path.exists():
            try:
                img = Image.open(img_path).convert("RGB")
                img = ImageOps.fit(img, (cell.w, cell.h), method=Image.LANCZOS)
                page.paste(img, (cell.x, cell.y))
            except Exception:
                draw.rectangle(
                    [(cell.x, cell.y), (cell.x + cell.w, cell.y + cell.h)], fill="#ffe0e0",
                )
        else:
            draw.rectangle(
                [(cell.x, cell.y), (cell.x + cell.w, cell.y + cell.h)], fill="#e8e8e8",
            )
            draw.text(
                (cell.x + 30, cell.y + 30),
                f"Vignetta {panel.number}\n(non ancora generata)",
                fill="#888888", font=_font_for_kind("DIDASCALIA", 30 * s),
            )

        # Bordo nero attorno alla cella
        draw.rectangle(
            [(cell.x, cell.y), (cell.x + cell.w - 1, cell.y + cell.h - 1)],
            outline="black", width=BORDER * s,
        )

        if show_balloons:
            _draw_balloons(page, draw, cell, panel.dialogues, scale=s, cfg=cfg)

    if page_label:
        font = _font_for_kind("DIDASCALIA", 18 * s)
        draw.text(
            (page_w - MARGIN * s - 80 * s, page_h - 40 * s),
            page_label, fill="#999999", font=font,
        )

    # Downscale finale
    final = page.resize((PAGE_W, PAGE_H), Image.LANCZOS)

    # Atomic write
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    final.save(tmp_path, "PNG", optimize=True)
    tmp_path.replace(out_path)
    return out_path


# ============================================================
# Thumbnail griglia (per UI di scelta gabbia)
# ============================================================

def render_grid_thumbnail(
    grid: GridTemplate,
    width: int = 140,
    height: int = 198,
    cell_fill: str = "#3b5bdb",
    bg_color: str = "#e9ecef",
    page_color: str = "#ffffff",
    page_border: str = "#212529",
    text_color: str = "#ffffff",
    cell_inset: int = 4,
) -> Image.Image:
    """Anteprima diagrammatica della gabbia: pagina bianca, celle blu con
    numero al centro. Le celle vengono "rimpicciolite" di `cell_inset` px
    su ogni lato per rendere il gutter chiaramente visibile (il gutter reale,
    18px su 1240, diventerebbe ~2px nel thumbnail — invisibile).
    """
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Margine "visivo" del thumbnail (proporzionale alla pagina A4)
    margin_x = max(6, int(width * (MARGIN / PAGE_W)))
    margin_y = max(6, int(height * (MARGIN / PAGE_H)))
    inner_w = width - 2 * margin_x
    inner_h = height - 2 * margin_y

    # Pagina (sfondo bianco con bordo scuro)
    draw.rectangle(
        [(margin_x, margin_y), (margin_x + inner_w - 1, margin_y + inner_h - 1)],
        fill=page_color, outline=page_border, width=1,
    )

    # Font per i numeri
    n_font_size = max(9, min(width, height) // 11)
    try:
        num_font = ImageFont.truetype(FONT_FALLBACK_PATH, n_font_size)
    except Exception:
        num_font = ImageFont.load_default()

    # Celle numerate — ognuna inset di `cell_inset` px per gutter visibile
    for i, (xp, yp, wp, hp) in enumerate(grid.cells_normalized, start=1):
        x0_full = margin_x + int(xp * inner_w)
        y0_full = margin_y + int(yp * inner_h)
        x1_full = x0_full + max(2, int(wp * inner_w))
        y1_full = y0_full + max(2, int(hp * inner_h))

        # Applica inset per creare il gutter visivo. Se la cella tocca il
        # bordo pagina, inset solo verso l'interno (mantieni il bordo originale).
        x0 = x0_full + cell_inset if xp > 0.01 else x0_full
        y0 = y0_full + cell_inset if yp > 0.01 else y0_full
        x1 = x1_full - cell_inset if (xp + wp) < 0.99 else x1_full
        y1 = y1_full - cell_inset if (yp + hp) < 0.99 else y1_full

        # Garantisci che la cella abbia almeno qualche px (evita rendering vuoto)
        if x1 - x0 < 4: x1 = x0 + 4
        if y1 - y0 < 4: y1 = y0 + 4

        draw.rectangle([(x0, y0), (x1 - 1, y1 - 1)], fill=cell_fill)
        # Numero al centro
        label = str(i)
        bbox = num_font.getbbox(label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cx = (x0 + x1) // 2 - tw // 2
        cy = (y0 + y1) // 2 - th // 2 - 1
        draw.text((cx, cy), label, fill=text_color, font=num_font)

    return img


def suggest_aspect_for_cell(cell_w: float, cell_h: float) -> str:
    """Suggerisce l'aspect_ratio key (di core/scene.py) più vicino alle
    proporzioni di una cella della griglia.
    """
    ratio = cell_w / cell_h if cell_h > 0 else 1.0
    # Soglie pragmatiche
    if 0.95 <= ratio <= 1.05:
        return "1_1"
    # Landscape
    if ratio > 1.05:
        if ratio >= 2.0:
            return "2_1"
        if ratio >= 1.7:
            return "16_9"
        if ratio >= 1.45:
            return "3_2"
        return "4_3"
    # Portrait
    if ratio <= 0.6:
        return "9_16"
    if ratio <= 0.72:
        return "2_3"
    return "3_4"


# ============================================================
# Preview vignetta singola
# ============================================================

def render_panel_preview(
    panel: Panel,
    vignette_image_path: Path | None,
    out_path: Path | None = None,
    *,
    size: int = 1024,
    cfg: BalloonStyleConfig | None = None,
) -> Image.Image:
    """Renderizza la singola vignetta col suo balloon overlay.

    Ritorna l'Image PIL (per passarla al widget senza re-read del disco).
    """
    cfg = cfg or _DEFAULT_CFG
    s = RENDER_SCALE
    hi = size * s

    if vignette_image_path and vignette_image_path.exists():
        try:
            src = Image.open(vignette_image_path).convert("RGB")
            img = ImageOps.fit(src, (hi, hi), method=Image.LANCZOS)
        except Exception:
            img = Image.new("RGB", (hi, hi), "#ffe0e0")
    else:
        img = Image.new("RGB", (hi, hi), "#e8e8e8")
        d = ImageDraw.Draw(img)
        d.text(
            (40, 40),
            f"Vignetta {panel.number} non ancora generata.",
            fill="#888888", font=_font_for_cfg("DIDASCALIA", 34 * s, cfg),
        )

    draw = ImageDraw.Draw(img)
    cell = GridCell(x=0, y=0, w=hi, h=hi)
    _draw_balloons(img, draw, cell, panel.dialogues, scale=s, cfg=cfg)

    # Downscale per UI
    final = img.resize((size, size), Image.LANCZOS)

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        final.save(tmp, "PNG", optimize=True)
        tmp.replace(out_path)
    return final


def panel_preview_path(project_dir: Path, page_number: int, panel_number: int) -> Path:
    return project_dir / "images" / f"p{page_number:02d}_v{panel_number:02d}.preview.png"


# ============================================================
# PDF export
# ============================================================

def export_pdf(image_paths: list[Path], out_path: Path) -> Path:
    if not image_paths:
        raise ValueError("Nessuna pagina da esportare.")
    images = [Image.open(p).convert("RGB") for p in image_paths]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        out_path, "PDF", save_all=True,
        append_images=images[1:], resolution=150.0,
    )
    return out_path


# ============================================================
# Path helpers
# ============================================================

def page_render_path(project_dir: Path, page_number: int) -> Path:
    return project_dir / "pages" / f"p{page_number:02d}.png"


def export_dir(project_dir: Path) -> Path:
    return project_dir / "exports"


# ============================================================
# Copertina
# ============================================================

def cover_illustration_path(project_dir: Path) -> Path:
    """PNG dell'illustrazione di copertina (senza testi sovrapposti)."""
    return project_dir / "images" / "cover.png"


def cover_render_path(project_dir: Path) -> Path:
    """PNG della copertina finale (illustrazione + box di testo sovrapposti)."""
    return project_dir / "pages" / "cover.png"


def _draw_cover_textbox(
    page_img: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: TextBox,
    text: str,
    *,
    page_w: int,
    page_h: int,
    scale: int = 1,
) -> None:
    """Disegna un box di testo della copertina (titolo/sottotitolo/autore)."""
    if not box.visible or not text.strip():
        return

    font_size = max(8, box.font_size) * scale
    font = _font_by_id(box.font_id, font_size)

    # Wrap su 90% della larghezza pagina
    max_w = int(page_w * 0.90)
    lines = _wrap(text, font, max_w)
    if not lines:
        return

    line_h = font.getbbox("Ag")[3] + 6 * scale
    text_h = line_h * len(lines)
    text_w = max(_text_size(font, line)[0] for line in lines)

    # Posizione: default centro orizzontale, e Y di default per ruolo
    px = box.position_x if box.position_x is not None else 0.5
    py = box.position_y if box.position_y is not None else 0.5
    cx = int(px * page_w)
    cy = int(py * page_h)

    pad_x = 24 * scale
    pad_y = 14 * scale

    # bg box opzionale
    if box.bg_color:
        x0 = cx - text_w // 2 - pad_x
        y0 = cy - text_h // 2 - pad_y
        x1 = cx + text_w // 2 + pad_x
        y1 = cy + text_h // 2 + pad_y
        # Shadow leggera
        _draw_shadow(page_img, "rounded_rect", x0, y0, x1, y1,
                     offset=(3 * scale, 4 * scale), blur=6 * scale, alpha=120)
        _draw_shape(draw, x0, y0, x1, y1, "rounded_rect",
                    fill=box.bg_color, outline=box.bg_color, width=1)

    # Disegna ogni linea, allineata in base a text_align
    y = cy - text_h // 2
    for line in lines:
        lw = _text_size(font, line)[0]
        if box.text_align == "left":
            x = cx - text_w // 2
        elif box.text_align == "right":
            x = cx + text_w // 2 - lw
        else:
            x = cx - lw // 2
        # Stroke (contorno) per leggibilità su qualsiasi sfondo immagine
        draw.text(
            (x, y), line,
            fill=box.color, font=font,
            stroke_width=max(1, 2 * scale),
            stroke_fill=_contrast_stroke(box.color),
        )
        y += line_h


def _contrast_stroke(hex_color: str) -> str:
    """Restituisce nero o bianco a seconda della luminanza del colore base.

    Serve a far risaltare il testo della copertina anche su sfondo immagine
    variegato — un sottile contorno opposto al colore principale.
    """
    s = hex_color.lstrip("#")
    if len(s) != 6:
        return "#000000"
    try:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return "#000000"
    # Luminanza percepita
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if lum > 0.55 else "#ffffff"


def paste_publisher_logo(
    page: Image.Image,
    logo_path: Path,
    *,
    position: str = "bc",
    size_pct: float = 0.18,
    margin_pct: float = 0.04,
) -> None:
    """Incolla il logo dell'editore in trasparenza sul `page`.

    Position keys:
      tl, tc, tr = top-left, top-center, top-right
      bl, bc, br = bottom-left, bottom-center, bottom-right
    `size_pct`: larghezza logo in % della larghezza pagina (0.05..0.5).
    `margin_pct`: spazio dai bordi (top/bottom/sx/dx) in % larghezza pagina.
    """
    if not logo_path.exists():
        return
    try:
        logo = Image.open(logo_path).convert("RGBA")
    except Exception:
        return
    page_w, page_h = page.size
    target_w = int(page_w * max(0.05, min(0.5, size_pct)))
    # Scale mantenendo aspect ratio
    src_w, src_h = logo.size
    ratio = target_w / src_w
    target_h = int(src_h * ratio)
    logo = logo.resize((target_w, target_h), Image.LANCZOS)
    margin = int(page_w * margin_pct)
    # Calcolo X
    if position.endswith("l"):
        x = margin
    elif position.endswith("r"):
        x = page_w - target_w - margin
    else:  # "c"
        x = (page_w - target_w) // 2
    # Calcolo Y
    if position.startswith("t"):
        y = margin
    else:  # "b"
        y = page_h - target_h - margin
    # Composite con alpha
    if page.mode != "RGBA":
        page_rgba = page.convert("RGBA")
        page_rgba.paste(logo, (x, y), logo)
        # Riconverti sul page originale RGB
        page.paste(page_rgba.convert("RGB"))
    else:
        page.paste(logo, (x, y), logo)


def render_cover(
    cover: Cover,
    illustration_path: Path | None,
    out_path: Path,
    *,
    style: "Style | None" = None,
) -> Path:
    """Renderizza la copertina: illustrazione + box testo + (opzionale) logo editore.

    Se `style` ha `publisher_logo_enabled=True` e il file logo esiste,
    viene composito sopra l'illustrazione secondo posizione/dimensione.
    """
    s = RENDER_SCALE
    page_w = PAGE_W * s
    page_h = PAGE_H * s

    # Carica illustrazione; se manca, sfondo grigio con placeholder
    if illustration_path and illustration_path.exists():
        try:
            src = Image.open(illustration_path).convert("RGB")
            page = ImageOps.fit(src, (page_w, page_h), method=Image.LANCZOS)
        except Exception:
            page = Image.new("RGB", (page_w, page_h), "#222222")
    else:
        page = Image.new("RGB", (page_w, page_h), "#1a1a1a")
        d = ImageDraw.Draw(page)
        d.text(
            (60 * s, 60 * s),
            "Copertina: illustrazione non ancora generata.",
            fill="#cccccc",
            font=_font_for_kind("DIDASCALIA", 30 * s),
        )

    draw = ImageDraw.Draw(page)

    _draw_cover_textbox(page, draw, cover.title_box, cover.title,
                       page_w=page_w, page_h=page_h, scale=s)
    _draw_cover_textbox(page, draw, cover.subtitle_box, cover.subtitle,
                       page_w=page_w, page_h=page_h, scale=s)
    _draw_cover_textbox(page, draw, cover.author_box, cover.author,
                       page_w=page_w, page_h=page_h, scale=s)

    # Logo editore (opzionale)
    if style is not None and getattr(style, "publisher_logo_enabled", False):
        from .styles import style_logo_path
        logo_path = style_logo_path(style.id)
        paste_publisher_logo(
            page, logo_path,
            position=style.publisher_logo_position,
            size_pct=style.publisher_logo_size_pct,
        )

    final = page.resize((PAGE_W, PAGE_H), Image.LANCZOS)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    final.save(tmp_path, "PNG", optimize=True)
    tmp_path.replace(out_path)
    return out_path
