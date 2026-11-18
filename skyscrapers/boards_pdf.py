"""
Print Enlairats boards to a Modernista-styled multi-board A4 PDF.
"""

from __future__ import annotations

import math
import unicodedata
from pathlib import Path
from typing import Any, Iterable

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape as page_landscape
from reportlab.lib.utils import ImageReader

from .display import load_board_json
from .rater import score_to_label

# --- units ---
CM = 28.346456692913385  # points
# Page packing: gap 0.45 cm lets default 6 cm cards fit portrait 3×4 on A4.
PAGE_MARGIN_CM = 1.0
PAGE_GAP_CM = 0.45

# --- brand palette (cover-inspired) ---
CREAM = (0.961, 0.941, 0.902)  # #F5F0E6
CHOCOLATE = (0.290, 0.200, 0.145)  # #4A3325
SAGE = (0.478, 0.545, 0.435)  # #7A8B6F
TERRACOTTA = (0.769, 0.471, 0.353)  # #C4785A
DUSTY_BLUE = (0.478, 0.608, 0.690)  # #7A9BB0
SAND = (0.769, 0.647, 0.455)  # #C4A574
BURGUNDY = (0.451, 0.220, 0.239)  # #73383D
INK_FAINT = (0.290, 0.200, 0.145, 0.12)

SUPPORTED_LANGS = ("ca", "en")

DIFFICULTY_LABELS = {
    "ca": {
        "easy": "Aprenent",
        "medium": "Oficial",
        "hard": "Mestre artesà",
        "expert": "Arquitecte",
    },
    "en": {
        "easy": "Apprentice",
        "medium": "Journeyman",
        "hard": "Master Craftsman",
        "expert": "Architect",
    },
}

# Catalan labels (kept for callers / filters that still expect DIFFICULTY_CA).
DIFFICULTY_CA = DIFFICULTY_LABELS["ca"]

BOARD_PDF_TEXT = {
    "ca": {"solution": "Solució"},
    "en": {"solution": "Solution"},
}

# Accent + petal colors per difficulty key (green / blue / yellow / red)
LEVEL_STYLE = {
    "easy": {
        "petals": 4,
        "accent": (0.35, 0.52, 0.38),
        "petal": (0.52, 0.68, 0.48),
        "center": (0.88, 0.92, 0.82),
    },
    "medium": {
        "petals": 5,
        "accent": (0.35, 0.48, 0.62),
        "petal": (0.48, 0.62, 0.78),
        "center": CREAM,
    },
    "hard": {
        "petals": 6,
        "accent": (0.72, 0.58, 0.18),
        "petal": (0.88, 0.74, 0.28),
        "center": (0.98, 0.94, 0.78),
    },
    "expert": {
        "petals": 7,
        "accent": (0.62, 0.18, 0.22),
        "petal": (0.78, 0.32, 0.30),
        "center": (0.95, 0.88, 0.82),
    },
}

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_FONTS_DIR = _PACKAGE_ROOT / "2d_prints" / "graphics" / "fonts"
_BUILDINGS_DIR = _PACKAGE_ROOT / "2d_prints" / "graphics" / "buildings"
_FONTS_REGISTERED = False

# Rank badge colors (green / blue / ochre / terracotta) — shared with rules booklet.
RANK_BADGE = {
    1: (0.35, 0.52, 0.38),
    2: (0.38, 0.52, 0.68),
    3: (0.72, 0.55, 0.22),
    4: TERRACOTTA,
}

BUILDING_FILES = {
    1: _BUILDINGS_DIR / "masia_freixa.png",
    2: _BUILDINGS_DIR / "casa_amatller.png",
    3: _BUILDINGS_DIR / "torre_galatea.png",
    4: _BUILDINGS_DIR / "torre_sagrada_familia.png",
}


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _norm_key(text: str) -> str:
    return " ".join(_strip_accents(text).casefold().split())


def normalize_lang(lang: str | None) -> str:
    code = (lang or "ca").strip().casefold()
    if code not in SUPPORTED_LANGS:
        raise ValueError(
            f"unsupported language {lang!r} (expected one of: {', '.join(SUPPORTED_LANGS)})"
        )
    return code


def resolve_difficulty_key(board: dict[str, Any]) -> str:
    """Return canonical difficulty key: easy / medium / hard / expert."""
    raw = board.get("difficulty")
    if isinstance(raw, str) and raw.strip():
        key = _norm_key(raw)
        for eng in DIFFICULTY_CA:
            aliases = {_norm_key(eng)}
            for lang in SUPPORTED_LANGS:
                aliases.add(_norm_key(DIFFICULTY_LABELS[lang][eng]))
            if key in aliases:
                return eng
    score = float(board["difficulty_score"])
    return score_to_label(score)


def resolve_difficulty_label(board: dict[str, Any], lang: str = "ca") -> str:
    """Return localized level name for a board JSON."""
    lang = normalize_lang(lang)
    return DIFFICULTY_LABELS[lang][resolve_difficulty_key(board)]


def parse_difficulty_filter(values: Iterable[str] | None) -> set[str] | None:
    """
    Parse CLI difficulty filters into a set of canonical keys
    (easy/medium/hard/expert). Accepts English tags and CA/EN display names.
    None → no filter.
    """
    if not values:
        return None
    allowed: set[str] = set()
    lookup: dict[str, str] = {}
    for eng in DIFFICULTY_CA:
        lookup[_norm_key(eng)] = eng
        for lang in SUPPORTED_LANGS:
            lookup[_norm_key(DIFFICULTY_LABELS[lang][eng])] = eng
    for value in values:
        key = _norm_key(value)
        if key not in lookup:
            known = ", ".join(
                list(DIFFICULTY_CA.keys())
                + list(DIFFICULTY_LABELS["ca"].values())
                + list(DIFFICULTY_LABELS["en"].values())
            )
            raise ValueError(f"unknown difficulty {value!r} (expected one of: {known})")
        allowed.add(lookup[key])
    return allowed


def _register_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    mapping = {
        "EnlairatsSerif": "CormorantGaramond-Regular.ttf",
        "EnlairatsSerif-SemiBold": "CormorantGaramond-SemiBold.ttf",
        "EnlairatsSerif-Bold": "CormorantGaramond-Bold.ttf",
        "EnlairatsDisplay": "Cinzel-Regular.ttf",
        "EnlairatsDisplay-Bold": "Cinzel-Bold.ttf",
    }
    for name, filename in mapping.items():
        path = _FONTS_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"missing font {path}; expected bundled fonts under 2d_prints/graphics/fonts/"
            )
        pdfmetrics.registerFont(TTFont(name, str(path)))
    _FONTS_REGISTERED = True


def _set_fill(c: canvas.Canvas, rgb: tuple[float, ...]) -> None:
    if len(rgb) == 4:
        c.setFillColorRGB(rgb[0], rgb[1], rgb[2], alpha=rgb[3])
    else:
        c.setFillColorRGB(*rgb)


def _set_stroke(c: canvas.Canvas, rgb: tuple[float, ...], width: float = 1.0) -> None:
    c.setStrokeColorRGB(*rgb[:3])
    c.setLineWidth(width)


def _draw_flower(
    c: canvas.Canvas,
    x: float,
    y: float,
    radius: float,
    *,
    petals: int,
    petal_rgb: tuple[float, float, float],
    center_rgb: tuple[float, float, float],
    accent_rgb: tuple[float, float, float],
) -> None:
    """Stylized Modernista blossom (cover-inspired)."""
    for i in range(petals):
        angle = i * (360.0 / petals)
        c.saveState()
        c.translate(x, y)
        c.rotate(angle)
        _set_fill(c, petal_rgb)
        _set_stroke(c, accent_rgb, width=0.6)
        c.ellipse(-radius * 0.35, radius * 0.15, radius * 0.35, radius * 1.05, fill=1, stroke=1)
        c.restoreState()
    _set_fill(c, center_rgb)
    _set_stroke(c, accent_rgb, width=0.7)
    c.circle(x, y, radius * 0.28, fill=1, stroke=1)
    # tiny inner dot
    _set_fill(c, accent_rgb)
    c.circle(x, y, radius * 0.1, fill=1, stroke=0)


def _draw_corner_flourish(
    c: canvas.Canvas,
    x: float,
    y: float,
    size: float,
    rgb: tuple[float, float, float],
    corner: str,
) -> None:
    """Whiplash corner curl."""
    _set_stroke(c, rgb, width=1.1)
    c.setLineCap(1)
    if corner == "tl":
        path = c.beginPath()
        path.moveTo(x, y - size)
        path.curveTo(x, y - size * 0.3, x + size * 0.3, y, x + size, y)
        c.drawPath(path, stroke=1, fill=0)
    elif corner == "tr":
        path = c.beginPath()
        path.moveTo(x, y - size)
        path.curveTo(x, y - size * 0.3, x - size * 0.3, y, x - size, y)
        c.drawPath(path, stroke=1, fill=0)
    elif corner == "bl":
        path = c.beginPath()
        path.moveTo(x, y + size)
        path.curveTo(x, y + size * 0.3, x + size * 0.3, y, x + size, y)
        c.drawPath(path, stroke=1, fill=0)
    else:  # br
        path = c.beginPath()
        path.moveTo(x, y + size)
        path.curveTo(x, y + size * 0.3, x - size * 0.3, y, x - size, y)
        c.drawPath(path, stroke=1, fill=0)


def _draw_scalloped_frame(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    accent: tuple[float, float, float],
    *,
    max_flourish: float | None = None,
    side_scallops: bool = True,
) -> None:
    """Double frame: chocolate inner, sage/accent outer with soft scallops."""
    # Outer sage-ish band
    _set_stroke(c, SAGE, width=2.2)
    c.roundRect(x, y, w, h, 6, stroke=1, fill=0)
    _set_stroke(c, accent, width=1.0)
    c.roundRect(x + 2.5, y + 2.5, w - 5, h - 5, 5, stroke=1, fill=0)
    _set_stroke(c, CHOCOLATE, width=0.9)
    c.roundRect(x + 5, y + 5, w - 10, h - 10, 4, stroke=1, fill=0)

    # Scallop hints mid-sides
    if side_scallops:
        r = 3.2
        _set_fill(c, CREAM)
        _set_stroke(c, SAGE, width=0.8)
        for px, py in (
            (x + w / 2, y + h - 1),
            (x + w / 2, y + 1),
            (x + 1, y + h / 2),
            (x + w - 1, y + h / 2),
        ):
            c.circle(px, py, r, fill=1, stroke=1)

    flourish = min(w, h) * 0.12
    if max_flourish is not None:
        flourish = min(flourish, max_flourish)
    _draw_corner_flourish(c, x + 8, y + h - 8, flourish, SAGE, "tl")
    _draw_corner_flourish(c, x + w - 8, y + h - 8, flourish, SAGE, "tr")
    _draw_corner_flourish(c, x + 8, y + 8, flourish, SAGE, "bl")
    _draw_corner_flourish(c, x + w - 8, y + 8, flourish, SAGE, "br")


def _draw_cell_pattern(
    c: canvas.Canvas,
    x: float,
    y: float,
    size: float,
) -> None:
    """Faint geometric Modernista tile inside an empty cell."""
    c.saveState()
    c.setFillColorRGB(SAGE[0], SAGE[1], SAGE[2], alpha=0.10)
    c.setStrokeColorRGB(SAGE[0], SAGE[1], SAGE[2], alpha=0.18)
    c.setLineWidth(0.4)
    # diamond
    mid = size / 2
    path = c.beginPath()
    path.moveTo(x + mid, y + size * 0.12)
    path.lineTo(x + size * 0.88, y + mid)
    path.lineTo(x + mid, y + size * 0.88)
    path.lineTo(x + size * 0.12, y + mid)
    path.close()
    c.drawPath(path, stroke=1, fill=1)
    # tiny center square
    s = size * 0.16
    c.rect(x + mid - s / 2, y + mid - s / 2, s, s, stroke=1, fill=0)
    c.restoreState()


def _draw_rank_badge(
    c: canvas.Canvas,
    x: float,
    y: float,
    rank: int,
    radius: float,
    *,
    font_size: float,
) -> None:
    """Colored circle with white rank digit."""
    _set_fill(c, RANK_BADGE[rank])
    c.circle(x, y, radius, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("EnlairatsDisplay-Bold", font_size)
    c.drawCentredString(x, y - font_size * 0.32, str(rank))
    c.setFillColorRGB(*CHOCOLATE)


def _fit_image(
    c: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    max_w: float,
    max_h: float,
    *,
    center: bool = True,
) -> tuple[float, float]:
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    draw_x = x + (max_w - w) / 2 if center else x
    draw_y = y + (max_h - h) / 2 if center else y
    c.drawImage(img, draw_x, draw_y, width=w, height=h, mask="auto")
    return w, h


def _draw_card_shell(
    c: canvas.Canvas,
    origin_x: float,
    origin_y: float,
    board: dict[str, Any],
    board_size_cm: float,
    *,
    header_label: str,
) -> dict[str, float]:
    """Cream card, frame, flower header, and id row. Returns layout metrics."""
    style = LEVEL_STYLE[resolve_difficulty_key(board)]
    layout = _compute_card_layout(board_size_cm)
    card_w = layout["card_w"]
    card_h = layout["card_h"]
    frame_pad = layout["frame"]
    header = layout["header"]
    id_row = layout["id_row"]

    _set_fill(c, CREAM)
    _set_stroke(c, CHOCOLATE, width=0.5)
    c.roundRect(origin_x, origin_y, card_w, card_h, 8, fill=1, stroke=0)
    _draw_scalloped_frame(c, origin_x, origin_y, card_w, card_h, style["accent"])

    header_drop = 0.14 * CM
    flower_r = min(header * 0.36, 0.24 * CM)
    header_y = origin_y + card_h - frame_pad - header / 2 - header_drop
    font_size = max(8.0, min(10.5, header * 0.50))
    c.setFont("EnlairatsDisplay-Bold", font_size)
    label = header_label.upper()
    text_w = pdfmetrics.stringWidth(label, "EnlairatsDisplay-Bold", font_size)
    flower_text_gap = 0.22 * CM
    group_w = 2 * flower_r + flower_text_gap + text_w
    group_left = origin_x + (card_w - group_w) / 2
    flower_x = group_left + flower_r
    text_x = group_left + 2 * flower_r + flower_text_gap
    _draw_flower(
        c,
        flower_x,
        header_y,
        flower_r,
        petals=style["petals"],
        petal_rgb=style["petal"],
        center_rgb=style["center"],
        accent_rgb=style["accent"],
    )
    c.setFillColorRGB(*CHOCOLATE)
    c.drawString(text_x, header_y - font_size * 0.38, label)

    id_font = max(5.0, min(6.5, id_row * 0.55))
    c.setFont("EnlairatsSerif", id_font)
    c.setFillColorRGB(CHOCOLATE[0], CHOCOLATE[1], CHOCOLATE[2], alpha=0.55)
    c.drawCentredString(
        origin_x + card_w / 2,
        origin_y + frame_pad + id_row * 0.52,
        str(board["id"]),
    )
    c.setFillColorRGB(*CHOCOLATE)

    return layout


def _compute_card_layout(card_size_cm: float) -> dict[str, float]:
    """
    Layout for a square card.

    ``card_size_cm`` is the outer card side (default 6 cm), not the inner grid.
    Clue font size is prioritised; the inner grid shrinks if needed to fit.
    """
    card = card_size_cm * CM
    frame = 0.14 * CM
    header = 0.42 * CM
    id_row = 0.18 * CM
    clue_gap = 0.10 * CM

    # Larger clue digits; scale gently with card size
    clue_font = 12.0 * (card_size_cm / 6.0)
    clue_font = max(9.0, min(13.0, clue_font))

    # Clue band must fit the full digit height plus gap from the grid
    clue_band = clue_gap + clue_font * 0.95 + 0.08 * CM

    grid = card - 2 * frame - header - id_row - 2 * clue_band
    if grid < 2.5 * CM:
        raise ValueError(
            f"card size {card_size_cm} cm is too small for readable clues; "
            "increase --board-size"
        )

    cell = grid / 4
    puzzle = grid + 2 * clue_band
    return {
        "card": card,
        "card_w": card,
        "card_h": card,
        "frame": frame,
        "header": header,
        "id_row": id_row,
        "clue_band": clue_band,
        "clue_gap": clue_gap,
        "clue_font": clue_font,
        "grid": grid,
        "cell": cell,
        "puzzle": puzzle,
    }


def card_dimensions(board_size_cm: float) -> tuple[float, float, float]:
    """
    Return (card_w, card_h, grid_size) in points.

    ``board_size_cm`` is the outer square card side length.
    """
    layout = _compute_card_layout(board_size_cm)
    return layout["card_w"], layout["card_h"], layout["grid"]


def _best_page_layout(
    card_w: float,
    card_h: float,
    *,
    margin_cm: float = PAGE_MARGIN_CM,
    gap_cm: float = PAGE_GAP_CM,
) -> tuple[tuple[float, float], int, int, bool]:
    """Pick portrait or landscape A4 for maximum boards per page."""
    gap = gap_cm * CM
    margin = margin_cm * CM

    def fit(page_size: tuple[float, float]) -> tuple[int, int, int]:
        pw, ph = page_size
        usable_w = pw - 2 * margin
        usable_h = ph - 2 * margin
        cols = max(1, int((usable_w + gap) // (card_w + gap)) if card_w <= usable_w else 0)
        rows = max(1, int((usable_h + gap) // (card_h + gap)) if card_h <= usable_h else 0)
        if cols == 0 or rows == 0:
            # still force 1×1 if a single card fits with tighter check
            cols = 1 if card_w <= usable_w else 0
            rows = 1 if card_h <= usable_h else 0
        return cols * rows, cols, rows

    portrait = A4
    landscape = page_landscape(A4)
    p_count, p_cols, p_rows = fit(portrait)
    l_count, l_cols, l_rows = fit(landscape)

    if p_count == 0 and l_count == 0:
        raise ValueError(
            "board size too large to fit on an A4 page with margins; "
            "try a smaller --board-size"
        )
    if l_count > p_count:
        return landscape, l_cols, l_rows, True
    return portrait, p_cols, p_rows, False


def _draw_board_card(
    c: canvas.Canvas,
    origin_x: float,
    origin_y: float,
    board: dict[str, Any],
    board_size_cm: float,
    *,
    lang: str = "ca",
) -> None:
    """Draw one playable board card (front); origin is bottom-left of the card."""
    n = int(board["N"])
    if n != 4:
        raise ValueError(f"only 4×4 boards are supported for print (got N={n})")

    c.saveState()
    try:
        _draw_board_card_contents(
            c, origin_x, origin_y, board, board_size_cm, lang=lang
        )
    finally:
        c.restoreState()


def _draw_solution_card(
    c: canvas.Canvas,
    origin_x: float,
    origin_y: float,
    board: dict[str, Any],
    board_size_cm: float,
    *,
    lang: str = "ca",
) -> None:
    """Draw the solution side (back) of a board card."""
    n = int(board["N"])
    if n != 4:
        raise ValueError(f"only 4×4 boards are supported for print (got N={n})")
    if "solution" not in board:
        raise ValueError(f"board {board.get('id', '?')} has no solution")

    c.saveState()
    try:
        _draw_solution_card_contents(
            c, origin_x, origin_y, board, board_size_cm, lang=lang
        )
    finally:
        c.restoreState()


def _draw_board_card_contents(
    c: canvas.Canvas,
    origin_x: float,
    origin_y: float,
    board: dict[str, Any],
    board_size_cm: float,
    *,
    lang: str = "ca",
) -> None:
    n = int(board["N"])
    level = resolve_difficulty_label(board, lang=lang)
    clues = board["clues"]
    layout = _draw_card_shell(
        c, origin_x, origin_y, board, board_size_cm, header_label=level
    )
    grid_left, grid_bottom, cell = _draw_puzzle_frame(
        c, origin_x, origin_y, layout, n
    )
    _draw_border_clues(c, layout, clues, grid_left, grid_bottom, cell, n)


def _draw_solution_card_contents(
    c: canvas.Canvas,
    origin_x: float,
    origin_y: float,
    board: dict[str, Any],
    board_size_cm: float,
    *,
    lang: str = "ca",
) -> None:
    """Back of the card: same grid/clues as the front, filled with the solution."""
    n = int(board["N"])
    solution = board["solution"]
    clues = board["clues"]
    lang = normalize_lang(lang)
    layout = _draw_card_shell(
        c,
        origin_x,
        origin_y,
        board,
        board_size_cm,
        header_label=BOARD_PDF_TEXT[lang]["solution"],
    )
    grid_left, grid_bottom, cell = _draw_puzzle_frame(
        c, origin_x, origin_y, layout, n
    )

    img_pad = cell * 0.08
    badge_r = max(0.11 * CM, min(0.16 * CM, cell * 0.17))
    badge_font = max(4.5, min(6.5, badge_r * 2.8))

    for r in range(n):
        for col in range(n):
            rank = int(solution[r][col])
            x = grid_left + col * cell
            y = grid_bottom + (n - 1 - r) * cell

            path = BUILDING_FILES[rank]
            if path.is_file():
                _fit_image(
                    c,
                    path,
                    x + img_pad,
                    y + img_pad,
                    cell - 2 * img_pad,
                    cell - 2 * img_pad,
                )
            else:
                c.setFont("EnlairatsDisplay-Bold", cell * 0.45)
                c.setFillColorRGB(*RANK_BADGE[rank])
                c.drawCentredString(
                    x + cell / 2, y + cell * 0.32, str(rank)
                )

            _draw_rank_badge(
                c,
                x + cell - badge_r - 0.04 * CM,
                y + cell - badge_r - 0.04 * CM,
                rank,
                badge_r,
                font_size=badge_font,
            )

    _draw_border_clues(c, layout, clues, grid_left, grid_bottom, cell, n)


def _draw_puzzle_frame(
    c: canvas.Canvas,
    origin_x: float,
    origin_y: float,
    layout: dict[str, float],
    n: int,
) -> tuple[float, float, float]:
    """Draw the empty grid (same size on front and back). Returns grid origin + cell."""
    card_w = layout["card_w"]
    grid = layout["grid"]
    clue_band = layout["clue_band"]
    frame_pad = layout["frame"]
    id_row = layout["id_row"]
    puzzle = layout["puzzle"]
    cell = layout["cell"]

    puzzle_left = origin_x + (card_w - puzzle) / 2
    puzzle_bottom = origin_y + frame_pad + id_row
    grid_left = puzzle_left + clue_band
    grid_bottom = puzzle_bottom + clue_band

    _set_fill(c, CREAM)
    _set_stroke(c, CHOCOLATE, width=1.2)
    c.rect(grid_left, grid_bottom, grid, grid, fill=1, stroke=1)

    for r in range(n):
        for col in range(n):
            x = grid_left + col * cell
            y = grid_bottom + (n - 1 - r) * cell
            _draw_cell_pattern(c, x, y, cell)
            _set_stroke(c, CHOCOLATE, width=0.7)
            c.rect(x, y, cell, cell, fill=0, stroke=1)

    return grid_left, grid_bottom, cell


def _draw_border_clues(
    c: canvas.Canvas,
    layout: dict[str, float],
    clues: dict[str, list[int]],
    grid_left: float,
    grid_bottom: float,
    cell: float,
    n: int,
) -> None:
    grid = layout["grid"]
    clue_band = layout["clue_band"]
    clue_gap = layout["clue_gap"]
    clue_font = layout["clue_font"]
    grid_top = grid_bottom + grid

    c.setFont("EnlairatsSerif-SemiBold", clue_font)
    c.setFillColorRGB(*CHOCOLATE)

    def draw_clue(val: int, cx: float, baseline_y: float) -> None:
        if not val:
            return
        c.drawCentredString(cx, baseline_y, str(val))

    top_baseline = grid_top + clue_gap
    bottom_baseline = grid_bottom - clue_font * 0.86 - 0.8

    for i, val in enumerate(clues["top"]):
        draw_clue(val, grid_left + (i + 0.5) * cell, top_baseline)
    for i, val in enumerate(clues["bottom"]):
        draw_clue(val, grid_left + (i + 0.5) * cell, bottom_baseline)
    for i, val in enumerate(clues["left"]):
        draw_clue(
            val,
            grid_left - clue_band * 0.50,
            grid_bottom + (n - 1 - i + 0.5) * cell - clue_font * 0.35,
        )
    for i, val in enumerate(clues["right"]):
        draw_clue(
            val,
            grid_left + grid + clue_band * 0.50,
            grid_bottom + (n - 1 - i + 0.5) * cell - clue_font * 0.35,
        )


def _card_slot_xy(
    slot: int,
    cols: int,
    rows: int,
    start_x: float,
    start_y: float,
    card_w: float,
    card_h: float,
    gap: float,
    *,
    mirror: bool = False,
) -> tuple[float, float]:
    """Bottom-left of a card slot; ``mirror`` flips columns for duplex backs."""
    col = slot % cols
    row = slot // cols
    if mirror:
        col = cols - 1 - col
    x = start_x + col * (card_w + gap)
    y = start_y + (rows - 1 - row) * (card_h + gap)
    return x, y


def load_boards_for_print(
    input_dir: Path,
    difficulty_filter: set[str] | None = None,
) -> list[dict[str, Any]]:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"input directory not found: {input_dir}")
    files = sorted(input_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no board JSON files in {input_dir}")

    boards: list[dict[str, Any]] = []
    for path in files:
        board = load_board_json(path)
        n = int(board["N"])
        if n != 4:
            raise ValueError(
                f"{path.name}: only 4×4 boards can be printed (found N={n})"
            )
        if "clues" not in board:
            raise ValueError(f"{path.name}: missing clues")
        if "solution" not in board:
            raise ValueError(f"{path.name}: missing solution (needed for card backs)")
        level_key = resolve_difficulty_key(board)
        if difficulty_filter is not None and level_key not in difficulty_filter:
            continue
        board = dict(board)
        board["_path"] = str(path)
        board["_level_key"] = level_key
        boards.append(board)

    if not boards:
        raise ValueError("no boards matched the difficulty filter")
    return boards


def write_boards_pdf(
    boards: list[dict[str, Any]],
    output_path: Path,
    *,
    board_size_cm: float = 6.0,
    lang: str = "ca",
) -> Path:
    if board_size_cm <= 0:
        raise ValueError("--board-size must be positive")
    lang = normalize_lang(lang)

    missing_art = [p for p in BUILDING_FILES.values() if not p.is_file()]
    if missing_art:
        raise FileNotFoundError(
            "missing building images: " + ", ".join(str(p) for p in missing_art)
        )

    _register_fonts()
    card_w, card_h, _grid = card_dimensions(board_size_cm)
    page_size, cols, rows, is_landscape = _best_page_layout(card_w, card_h)
    gap = PAGE_GAP_CM * CM
    per_page = cols * rows

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=page_size)
    pw, ph = page_size

    # Center the grid of cards on the page
    total_w = cols * card_w + (cols - 1) * gap
    total_h = rows * card_h + (rows - 1) * gap
    start_x = (pw - total_w) / 2
    start_y = (ph - total_h) / 2

    # Duplex sheets: fronts, then mirrored backs (flip on long edge).
    for page_start in range(0, len(boards), per_page):
        chunk = boards[page_start : page_start + per_page]
        if page_start > 0:
            c.showPage()
        for slot, board in enumerate(chunk):
            x, y = _card_slot_xy(
                slot, cols, rows, start_x, start_y, card_w, card_h, gap
            )
            _draw_board_card(c, x, y, board, board_size_cm, lang=lang)

        c.showPage()
        for slot, board in enumerate(chunk):
            x, y = _card_slot_xy(
                slot,
                cols,
                rows,
                start_x,
                start_y,
                card_w,
                card_h,
                gap,
                mirror=True,
            )
            _draw_solution_card(c, x, y, board, board_size_cm, lang=lang)

    c.save()
    return output_path


def print_boards(
    input_dir: Path,
    output_path: Path,
    *,
    board_size_cm: float = 6.0,
    difficulties: Iterable[str] | None = None,
    lang: str = "ca",
) -> tuple[Path, int, dict[str, Any]]:
    """
    Build the PDF. Returns (path, board_count, layout_info).
    """
    lang = normalize_lang(lang)
    filt = parse_difficulty_filter(difficulties)
    boards = load_boards_for_print(input_dir, filt)
    path = write_boards_pdf(
        boards, output_path, board_size_cm=board_size_cm, lang=lang
    )
    card_w, card_h, _ = card_dimensions(board_size_cm)
    page_size, cols, rows, is_landscape = _best_page_layout(card_w, card_h)
    front_pages = math.ceil(len(boards) / (cols * rows))
    info = {
        "boards": len(boards),
        "cols": cols,
        "rows": rows,
        "per_page": cols * rows,
        "landscape": is_landscape,
        "board_size_cm": board_size_cm,
        "pages": front_pages * 2,  # fronts + backs
        "front_pages": front_pages,
    }
    return path, len(boards), info
