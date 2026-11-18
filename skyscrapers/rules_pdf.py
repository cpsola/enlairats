"""
Generate a 10×10 cm Modernista-styled Enlairats rules booklet PDF.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

from .boards_pdf import (
    CM,
    CREAM,
    CHOCOLATE,
    SAGE,
    TERRACOTTA,
    DIFFICULTY_LABELS,
    LEVEL_STYLE,
    normalize_lang,
    _draw_flower,
    _draw_scalloped_frame,
    _register_fonts,
    _set_fill,
    _set_stroke,
)

PAGE = 10 * CM  # 10×10 cm square (content design size / non-A4 PDF)
# A4 imposition tile size (slightly smaller than PAGE to leave sheet margins).
A4_TILE = 9 * CM
# Safe content inset clear of the triple frame and corner curls.
MARGIN = 1.35 * CM
FRAME_INSET = 0.14 * CM
FRAME_FLOURISH_MAX = 0.22 * CM
# Warm parchment matching cover_v2.png edges (not the cooler CREAM used elsewhere).
COVER_PARCHMENT = (238 / 255, 218 / 255, 189 / 255)

# Typography defaults
TITLE_SIZE = 11.0
SECTION_SIZE = 8.5
BODY_SIZE = 7.5
BODY_LEADING = 9.6
SMALL_SIZE = 6.5

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_GRAPHICS = _PACKAGE_ROOT / "2d_prints" / "graphics"
_BUILDINGS = _GRAPHICS / "buildings"
_COVER = _GRAPHICS / "cover_v2.png"

BUILDINGS = [
    {
        "key": "masia_freixa",
        "name": "Masia Freixa",
        "height": {
            "ca": "La més baixa",
            "en": "The shortest",
        },
        "rank": 1,
        "file": _BUILDINGS / "masia_freixa.png",
    },
    {
        "key": "casa_amatller",
        "name": "Casa Amatller",
        "height": {
            "ca": "Mitjana-baixa",
            "en": "Low–medium",
        },
        "rank": 2,
        "file": _BUILDINGS / "casa_amatller.png",
    },
    {
        "key": "torre_galatea",
        "name": "Torre Galatea",
        "height": {
            "ca": "Mitjana-alta",
            "en": "Medium–high",
        },
        "rank": 3,
        "file": _BUILDINGS / "torre_galatea.png",
    },
    {
        "key": "torre_sagrada_familia",
        "name": "Torre de la Sagrada Família",
        "height": {
            "ca": "La més alta",
            "en": "The tallest",
        },
        "rank": 4,
        "file": _BUILDINGS / "torre_sagrada_familia.png",
    },
]

ALL_EXAMPLES: dict[str, list[tuple[list[int], str, int]]] = {
    "ca": [
        (
            [1, 2, 3, 4],
            "Es veuen tots quatre, cada un més alt que l’anterior.",
            4,
        ),
        (
            [4, 1, 2, 3],
            "Només es veu la Torre de la Sagrada Família (4), que tapa la resta d'edificis.",
            1,
        ),
        (
            [2, 1, 4, 3],
            "Es veuen la Casa Amatller (2) i la Torre de la Sagrada Família (4).",
            2,
        ),
        (
            [3, 1, 4, 2],
            "Es veuen la Torre Galatea (3) i la Torre de la Sagrada Família (4).",
            2,
        ),
    ],
    "en": [
        (
            [1, 2, 3, 4],
            "All four are visible, each taller than the one in front.",
            4,
        ),
        (
            [4, 1, 2, 3],
            "Only Torre de la Sagrada Família (4) is visible; it hides the rest.",
            1,
        ),
        (
            [2, 1, 4, 3],
            "Casa Amatller (2) and Torre de la Sagrada Família (4) are visible.",
            2,
        ),
        (
            [3, 1, 4, 2],
            "Torre Galatea (3) and Torre de la Sagrada Família (4) are visible.",
            2,
        ),
    ],
}

# Embedded copy for the booklet (proper names stay in Catalan/local form).
RULES_COPY: dict[str, dict[str, object]] = {
    "ca": {
        "cover_label": "INSTRUCCIONS",
        "title_what": "Què és Enlairats?",
        "intro": (
            "Enlairats és un joc de lògica ambientat en l’arquitectura modernista "
            "catalana. Amb miniatures de quatre edificis construeixes un petit "
            "barri sobre el tauler: has de decidir on va cadascun de manera que, "
            "mirant des dels carrers del voltant, se’n vegin exactament els que "
            "indiquen les pistes. Cada tauler té una sola solució."
        ),
        "section_contents": "Contingut",
        "contents": (
            "Taulers d’Enlairats (graella 4×4 amb pistes al contorn).",
            "Miniatures dels quatre edificis (quatre peces de cada un).",
            "Fitxes de pista (quatre peces amb cada número de 1 a 4).",
        ),
        "section_goal": "Objectiu",
        "goal": (
            "Omple totes les caselles de la graella 4×4 col·locant-hi les "
            "miniatures, de manera que es compleixin totes les pistes del "
            "contorn i la regla de barri."
        ),
        "section_setup": "Preparació",
        "setup_steps": (
            "Tria una carta de tauler (segons el nivell de dificultat).",
            "Col·loca les fitxes de pistes (circulars de l’1 al 4) al contorn, "
            "reproduïnt el que indica la carta.",
            "Deixa a mà les miniatures dels quatre edificis.",
        ),
        "title_buildings": "Els quatre edificis",
        "title_howto": "Com es juga",
        "howto_intro": (
            "Omple totes les caselles amb les miniatures respectant les pistes "
            "del contorn i la regla de barri."
        ),
        "section_neighbourhood": "La regla del barri",
        "neighbourhood_bullets": (
            "A cada fila, els quatre edificis hi apareixen una sola vegada.",
            "A cada columna, els quatre edificis hi apareixen una sola vegada.",
        ),
        "neighbourhood_note": (
            "És a dir, no es pot repetir el mateix edifici a la mateixa fila ni columna."
        ),
        "section_clues": "Les pistes de contorn",
        "clue_bullets": (
            "Els números del contorn indiquen quants edificis es veuen mirant "
            "aquell carrer en línia recta des d’aquell costat.",
            "Posiciona’t al costat de la pista i mira cap a l’altre extrem. "
            "Un edifici és visible només si és més alt que tots els que tens davant.",
            "Els més baixos que queden darrere d’un de més alt queden amagats.",
        ),
        "section_important": "Important",
        "important_bullets": (
            "Si una posició del contorn no té número, no hi ha pista: no aporta informació.",
            "La Masia Freixa no amaga res al darrere; la Torre de la Sagrada Família "
            "amaga tot el que quedi darrere seu.",
            "No cal endevinar: cada pas es pot deduir amb lògica.",
        ),
        "title_examples": "Exemples de visibilitat",
        "examples_intro": "Mira d’esquerra a dreta. El cercle verd és la pista. ",
        "title_finished": "Com saber si has acabat",
        "finished_steps": (
            "Totes les caselles tenen una miniatura.",
            "Cap fila ni columna no repeteix el mateix edifici.",
            "Mirant des de cada pista, es veuen exactament tants edificis "
            "com indica el número.",
            "Ara pots girar la carta de tauler i comprovar si la solució és correcta!",
        ),
        "title_levels": "Nivells de dificultat",
        "level_blurbs": {
            "easy": "Ideal per aprendre les regles i començar a jugar.",
            "medium": "Diversió garantida quan ja coneixes el joc.",
            "hard": "Raonaments més avançats; combina diverses pistes.",
            "expert": "El repte més alt.",
        },
        "levels_note": "Cada tauler porta una flor i el nom del nivell.",
        "closing": "Que gaudeixis construint.",
    },
    "en": {
        "cover_label": "RULES",
        "title_what": "What is Enlairats?",
        "intro": (
            "Enlairats is a logic game set in Catalan Modernista architecture. "
            "With miniatures of four buildings you assemble a small neighbourhood "
            "on the board: decide where each one goes so that, looking in from the "
            "surrounding streets, you see exactly as many buildings as the clues "
            "indicate. Every board has a single solution."
        ),
        "section_contents": "Contents",
        "contents": (
            "Enlairats boards (4×4 grid with clues around the border).",
            "Miniatures of the four buildings (four pieces of each).",
            "Clue tokens (four pieces for each number from 1 to 4).",
        ),
        "section_goal": "Goal",
        "goal": (
            "Fill every cell of the 4×4 grid with miniatures so that all border "
            "clues and the neighbourhood rule are satisfied."
        ),
        "section_setup": "Setup",
        "setup_steps": (
            "Choose a board card (according to the difficulty level).",
            "Place the clue tokens (circles numbered 1 to 4) around the border, "
            "matching what the board card shows.",
            "Keep the miniatures of the four buildings within reach.",
        ),
        "title_buildings": "The four buildings",
        "title_howto": "How to play",
        "howto_intro": (
            "Fill every cell with miniatures while respecting the border clues "
            "and the neighbourhood rule."
        ),
        "section_neighbourhood": "The neighbourhood rule",
        "neighbourhood_bullets": (
            "In every row, each of the four buildings appears exactly once.",
            "In every column, each of the four buildings appears exactly once.",
        ),
        "neighbourhood_note": (
            "In other words, the same building cannot be repeated in the same row or column."
        ),
        "section_clues": "Border clues",
        "clue_bullets": (
            "The numbers around the grid say how many buildings are visible looking "
            "straight along that street from that side.",
            "Stand by the clue and look toward the far end. A building is visible "
            "only if it is taller than every building in front of it.",
            "Shorter buildings behind a taller one are hidden.",
        ),
        "section_important": "Important",
        "important_bullets": (
            "If a border slot has no number, there is no clue there: it gives no information.",
            "Masia Freixa never hides what stands behind it; Torre de la Sagrada Família "
            "hides everything behind it from that viewpoint.",
            "No guessing needed: every step can be deduced with logic.",
        ),
        "title_examples": "Visibility examples",
        "examples_intro": "Look left to right. The green circle is the clue. ",
        "title_finished": "How to know you are done",
        "finished_steps": (
            "Every cell has a miniature.",
            "No row or column repeats the same building.",
            "From each border clue, exactly as many buildings are visible as the number says.",
            "You can now flip the board card and check whether the solution is correct!",
        ),
        "title_levels": "Difficulty levels",
        "level_blurbs": {
            "easy": "Ideal for learning the rules and starting to play.",
            "medium": "Guaranteed fun once you know the game.",
            "hard": "More advanced reasoning; combine several clues.",
            "expert": "The highest challenge.",
        },
        "levels_note": "Each board carries a flower and the level name.",
        "closing": "Enjoy building.",
    },
}

_current_lang = "ca"


def _set_lang(lang: str) -> str:
    global _current_lang
    _current_lang = normalize_lang(lang)
    return _current_lang


def _R() -> dict[str, object]:
    return RULES_COPY[_current_lang]

# Rank badge colors on the buildings page (green / blue / ochre / terracotta).
RANK_BADGE = {
    1: (0.35, 0.52, 0.38),
    2: (0.38, 0.52, 0.68),
    3: (0.72, 0.55, 0.22),
    4: TERRACOTTA,
}


def _draw_page_frame(c: canvas.Canvas) -> None:
    _draw_scalloped_frame(
        c,
        FRAME_INSET,
        FRAME_INSET,
        PAGE - 2 * FRAME_INSET,
        PAGE - 2 * FRAME_INSET,
        SAGE,
        max_flourish=FRAME_FLOURISH_MAX,
        side_scallops=False,
    )


def _new_page(c: canvas.Canvas) -> None:
    _set_fill(c, CREAM)
    c.rect(0, 0, PAGE, PAGE, fill=1, stroke=0)
    _draw_page_frame(c)


def _content_top() -> float:
    """Baseline for the first line, leaving room for title glyph ascent."""
    return PAGE - MARGIN - 0.08 * CM


def _content_bottom() -> float:
    """Lowest baseline allowed for body text (above page number band)."""
    return MARGIN + 0.18 * CM


def _title(c: canvas.Canvas, text: str, y: float) -> float:
    label = text.upper()
    size = TITLE_SIZE
    max_w = PAGE - 2 * MARGIN
    while size > 8.5 and c.stringWidth(label, "EnlairatsDisplay-Bold", size) > max_w:
        size -= 0.35
    c.setFont("EnlairatsDisplay-Bold", size)
    c.setFillColorRGB(*CHOCOLATE)
    c.drawCentredString(PAGE / 2, y, label)
    _set_stroke(c, SAGE, width=0.8)
    rule_w = min(1.4 * CM, max_w * 0.28)
    c.line(PAGE / 2 - rule_w, y - 0.11 * CM, PAGE / 2 + rule_w, y - 0.11 * CM)
    c.setFillColorRGB(*TERRACOTTA)
    c.circle(PAGE / 2, y - 0.11 * CM, 1.2, fill=1, stroke=0)
    return y - 0.62 * CM


def _section(c: canvas.Canvas, text: str, y: float) -> float:
    c.setFont("EnlairatsDisplay-Bold", SECTION_SIZE)
    c.setFillColorRGB(*CHOCOLATE)
    c.drawString(MARGIN, y, text.upper())
    return y - 0.42 * CM


def _body(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "EnlairatsSerif",
    size: float = BODY_SIZE,
    leading: float | None = None,
) -> float:
    line_h = leading if leading is not None else size * 1.24
    c.setFont(font, size)
    c.setFillColorRGB(*CHOCOLATE)
    lines = simpleSplit(text, font, size, width)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_h
    return y


def _bullet(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    size: float = BODY_SIZE,
) -> float:
    c.setFillColorRGB(*SAGE)
    c.circle(x + 0.12 * CM, y + 0.06 * CM, 1.4, fill=1, stroke=0)
    return _body(c, text, x + 0.38 * CM, y, width - 0.38 * CM, size=size)


def _page_number(c: canvas.Canvas, n: int, total: int) -> None:
    # Bottom-right, in the frame band but clear of the corner flourish.
    c.setFont("EnlairatsSerif", 5.5)
    c.setFillColorRGB(CHOCOLATE[0], CHOCOLATE[1], CHOCOLATE[2], alpha=0.45)
    c.drawRightString(PAGE - 0.82 * CM, 0.78 * CM, f"{n} / {total}")
    c.setFillColorRGB(*CHOCOLATE)


def _draw_right_arrow(
    c: canvas.Canvas,
    x: float,
    y: float,
    length: float,
    *,
    rgb: tuple[float, float, float] = SAGE,
) -> None:
    """Modernista whiplash arrow pointing right; (x, y) left end, vertically centered."""
    tip_x = x + length
    wave = 0.055 * CM
    head_w = 0.20 * CM
    head_h = 0.13 * CM

    c.saveState()
    c.setLineCap(1)
    c.setLineJoin(1)

    # Starting bud (viewpoint), echoing the clue disc.
    _set_fill(c, rgb)
    c.circle(x + 0.05 * CM, y, 1.55, fill=1, stroke=0)

    # Gentle undulating stem — Art Nouveau whiplash.
    _set_stroke(c, rgb, width=1.25)
    stem = c.beginPath()
    stem.moveTo(x + 0.12 * CM, y)
    stem.curveTo(
        x + length * 0.28,
        y + wave,
        x + length * 0.58,
        y - wave * 0.85,
        tip_x - head_w * 0.85,
        y,
    )
    c.drawPath(stem, stroke=1, fill=0)

    # Soft leaf-shaped tip (curved chevron, not a hard triangle).
    hx = tip_x - head_w
    head = c.beginPath()
    head.moveTo(tip_x, y)
    head.curveTo(
        tip_x - head_w * 0.35,
        y + head_h * 0.15,
        hx + head_w * 0.15,
        y + head_h * 0.85,
        hx,
        y + head_h,
    )
    head.curveTo(
        hx + head_w * 0.35,
        y + head_h * 0.25,
        hx + head_w * 0.35,
        y - head_h * 0.25,
        hx,
        y - head_h,
    )
    head.curveTo(
        hx + head_w * 0.15,
        y - head_h * 0.85,
        tip_x - head_w * 0.35,
        y - head_h * 0.15,
        tip_x,
        y,
    )
    head.close()
    _set_fill(c, rgb)
    c.drawPath(head, stroke=0, fill=1)

    # Tiny accent speck near the tip, like the title ornaments.
    c.setFillColorRGB(*TERRACOTTA)
    c.circle(tip_x - head_w * 0.55, y, 0.9, fill=1, stroke=0)

    c.restoreState()
    c.setFillColorRGB(*CHOCOLATE)


def _draw_rank_badge(
    c: canvas.Canvas,
    x: float,
    y: float,
    rank: int,
    radius: float,
    *,
    font_size: float,
) -> None:
    """Colored circle with white rank digit (same symbols as the buildings page)."""
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


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def _page_cover(c: canvas.Canvas) -> None:
    t = _R()
    _set_fill(c, CREAM)
    c.rect(0, 0, PAGE, PAGE, fill=1, stroke=0)
    pad = MARGIN * 0.55
    _fit_image(
        c, _COVER, pad, pad + 0.4 * CM, PAGE - 2 * pad, PAGE - 2 * pad - 0.5 * CM
    )
    c.setFont("EnlairatsDisplay-Bold", 8)
    c.setFillColorRGB(*CHOCOLATE)
    c.drawCentredString(PAGE / 2, 0.62 * CM, str(t["cover_label"]))
    _draw_page_frame(c)


def _page_intro(c: canvas.Canvas) -> None:
    t = _R()
    _new_page(c)
    y = _content_top()
    y = _title(c, str(t["title_what"]), y)
    y = _body(c, str(t["intro"]), MARGIN, y, PAGE - 2 * MARGIN)
    y -= 0.14 * CM
    y -= 0.2 * CM

    y = _section(c, str(t["section_contents"]), y)
    for item in t["contents"]:  # type: ignore[union-attr]
        y = _bullet(c, str(item), MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.12 * CM

    y -= 0.2 * CM
    y = _section(c, str(t["section_goal"]), y)
    y = _body(c, str(t["goal"]), MARGIN, y, PAGE - 2 * MARGIN)
    y -= 0.22 * CM

    y = _section(c, str(t["section_setup"]), y)
    for i, step in enumerate(t["setup_steps"], start=1):  # type: ignore[arg-type]
        c.setFillColorRGB(*SAGE)
        c.setFont("EnlairatsDisplay-Bold", 8.5)
        c.drawString(MARGIN, y, f"{i}.")
        y = _body(
            c, str(step), MARGIN + 0.4 * CM, y, PAGE - 2 * MARGIN - 0.4 * CM
        )
        y -= 0.12 * CM


def _page_buildings(c: canvas.Canvas) -> None:
    t = _R()
    _new_page(c)
    y = _content_top()
    y = _title(c, str(t["title_buildings"]), y)

    gap = 0.16 * CM
    usable_w = PAGE - 2 * MARGIN
    usable_h = y - _content_bottom()
    cell_w = (usable_w - gap) / 2
    cell_h = (usable_h - gap) / 2

    for i, b in enumerate(BUILDINGS):
        col, row = i % 2, i // 2
        x0 = MARGIN + col * (cell_w + gap)
        y0 = _content_bottom() + (1 - row) * (cell_h + gap)

        _set_stroke(c, SAGE, width=1.0)
        _set_fill(c, CREAM)
        c.roundRect(x0, y0, cell_w, cell_h, 4, fill=1, stroke=1)

        _draw_rank_badge(
            c,
            x0 + 0.32 * CM,
            y0 + cell_h - 0.32 * CM,
            b["rank"],
            0.25 * CM,
            font_size=7.5,
        )

        img_h = cell_h - 1.0 * CM
        _fit_image(
            c,
            b["file"],
            x0 + 0.1 * CM,
            y0 + 0.52 * CM,
            cell_w - 0.2 * CM,
            img_h,
        )
        c.setFillColorRGB(*CHOCOLATE)
        c.setFont("EnlairatsDisplay-Bold", 5.8)
        name = b["name"].upper()
        if len(name) > 22:
            name = "SAGRADA FAMÍLIA"
        c.drawCentredString(x0 + cell_w / 2, y0 + 0.30 * CM, name)
        c.setFont("EnlairatsSerif", 5.6)
        c.setFillColorRGB(CHOCOLATE[0], CHOCOLATE[1], CHOCOLATE[2], alpha=0.8)
        height = b["height"][_current_lang]
        c.drawCentredString(x0 + cell_w / 2, y0 + 0.10 * CM, height)
        c.setFillColorRGB(*CHOCOLATE)


def _page_howto(c: canvas.Canvas) -> None:
    t = _R()
    _new_page(c)
    y = _content_top()
    y = _title(c, str(t["title_howto"]), y)
    y = _body(c, str(t["howto_intro"]), MARGIN, y, PAGE - 2 * MARGIN)
    y -= 0.2 * CM

    y = _section(c, str(t["section_neighbourhood"]), y)
    for item in t["neighbourhood_bullets"]:  # type: ignore[union-attr]
        y = _bullet(c, str(item), MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.08 * CM
    y -= 0.06 * CM
    y = _body(c, str(t["neighbourhood_note"]), MARGIN, y, PAGE - 2 * MARGIN)

    y -= 0.2 * CM
    y = _section(c, str(t["section_clues"]), y)
    for item in t["clue_bullets"]:  # type: ignore[union-attr]
        y = _bullet(c, str(item), MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.06 * CM

    y -= 0.2 * CM
    y = _section(c, str(t["section_important"]), y)
    for item in t["important_bullets"]:  # type: ignore[union-attr]
        y = _bullet(c, str(item), MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.06 * CM


def _page_examples(c: canvas.Canvas) -> None:
    t = _R()
    examples = ALL_EXAMPLES[_current_lang]
    _new_page(c)
    y = _content_top()
    y = _title(c, str(t["title_examples"]), y)
    y = _body(
        c,
        str(t["examples_intro"]),
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
        size=BODY_SIZE - 0.15,
    )
    y -= 0.28 * CM

    bottom = _content_bottom()
    available = y - bottom
    n = len(examples)
    example_gap = 0.38 * CM
    slot_h = (available - (n - 1) * example_gap) / n
    icon_h = min(0.82 * CM, slot_h * 0.44)

    for i, (ranks, caption, clue) in enumerate(examples):
        slot_top = y - i * (slot_h + example_gap)
        _set_fill(c, SAGE)
        badge_x = MARGIN + 0.26 * CM
        badge_y = slot_top - icon_h * 0.5
        c.circle(badge_x, badge_y, 0.24 * CM, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("EnlairatsDisplay-Bold", 8.5)
        c.drawCentredString(badge_x, badge_y - 0.09 * CM, str(clue))

        # Viewing direction: from the clue toward the buildings (near → far).
        arrow_x = MARGIN + 0.58 * CM
        arrow_len = 0.42 * CM
        _draw_right_arrow(c, arrow_x, badge_y, arrow_len)

        x = MARGIN + 1.12 * CM
        slot_w = (PAGE - 2 * MARGIN - 1.12 * CM) / 4
        for rank in ranks:
            b = BUILDINGS[rank - 1]
            img_w = slot_w - 0.08 * CM
            _fit_image(
                c, b["file"], x, slot_top - icon_h, img_w, icon_h
            )
            _draw_rank_badge(
                c,
                x + img_w - 0.16 * CM,
                slot_top - 0.14 * CM,
                rank,
                0.13 * CM,
                font_size=5.5,
            )
            x += slot_w

        caption_y = slot_top - icon_h - 0.28 * CM
        _body(
            c,
            caption,
            MARGIN,
            caption_y,
            PAGE - 2 * MARGIN,
            size=SMALL_SIZE,
        )


def _page_end(c: canvas.Canvas) -> None:
    t = _R()
    _new_page(c)
    y = _content_top()
    y = _title(c, str(t["title_finished"]), y)
    for i, step in enumerate(t["finished_steps"], start=1):  # type: ignore[arg-type]
        c.setFillColorRGB(*SAGE)
        c.setFont("EnlairatsDisplay-Bold", 8.5)
        c.drawString(MARGIN, y, f"{i}.")
        y = _body(
            c, str(step), MARGIN + 0.4 * CM, y, PAGE - 2 * MARGIN - 0.4 * CM
        )
        y -= 0.06 * CM

    y -= 0.18 * CM
    y = _title(c, str(t["title_levels"]), y)
    blurbs = t["level_blurbs"]  # type: ignore[assignment]
    assert isinstance(blurbs, dict)
    for key in ("easy", "medium", "hard", "expert"):
        name = DIFFICULTY_LABELS[_current_lang][key]
        desc = str(blurbs[key])
        style = LEVEL_STYLE[key]
        _draw_flower(
            c,
            MARGIN + 0.26 * CM,
            y + 0.04 * CM,
            0.20 * CM,
            petals=style["petals"],
            petal_rgb=style["petal"],
            center_rgb=style["center"],
            accent_rgb=style["accent"],
        )
        c.setFillColorRGB(*CHOCOLATE)
        c.setFont("EnlairatsDisplay-Bold", 7.2)
        c.drawString(MARGIN + 0.6 * CM, y, name.upper())
        y = _body(
            c,
            desc,
            MARGIN + 0.6 * CM,
            y - 0.24 * CM,
            PAGE - 2 * MARGIN - 0.6 * CM,
            size=BODY_SIZE - 0.3,
        )
        y -= 0.10 * CM

    y -= 0.06 * CM
    y = _body(
        c,
        str(t["levels_note"]),
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
        size=BODY_SIZE - 0.3,
    )
    c.setFont("EnlairatsDisplay-Bold", 8.5)
    c.setFillColorRGB(*CHOCOLATE)
    # Keep a clear gap under the blurb; sit above the page-number band.
    closing_y = min(y - 0.55 * CM, 1.05 * CM)
    closing_y = max(closing_y, 0.88 * CM)
    c.drawCentredString(PAGE / 2, closing_y, str(t["closing"]))


def _rules_page_fns() -> list:
    return [
        _page_cover,
        _page_intro,
        _page_buildings,
        _page_howto,
        _page_examples,
        _page_end,
    ]


def _ensure_rules_assets() -> None:
    missing = [b["file"] for b in BUILDINGS if not b["file"].is_file()]
    if missing:
        raise FileNotFoundError(
            "missing building images: " + ", ".join(str(p) for p in missing)
        )
    if not _COVER.is_file():
        raise FileNotFoundError(f"missing cover: {_COVER}")


def _register_rules_page_forms(c: canvas.Canvas) -> list[str]:
    """Draw each 10×10 cm page into a Form XObject; return form names."""
    page_fns = _rules_page_fns()
    total = len(page_fns)
    names: list[str] = []
    for i, page_fn in enumerate(page_fns, start=1):
        name = f"enlairats_rules_{i}"
        c.beginForm(name, 0, 0, PAGE, PAGE)
        page_fn(c)
        if i > 1:
            _page_number(c, i, total)
        c.endForm()
        names.append(name)
    return names


def _default_rules_output(lang: str, *, a4: bool) -> Path:
    rules_dir = _PACKAGE_ROOT / "2d_prints" / "rules"
    if lang == "en":
        name = "sample_instructions_en_a4.pdf" if a4 else "sample_instructions_en.pdf"
    else:
        name = "sample_instructions_a4.pdf" if a4 else "sample_instructions.pdf"
    return rules_dir / name


def write_rules_pdf(output_path: Path | None = None, *, lang: str = "ca") -> Path:
    """Build the 10×10 cm rules booklet (one square page per sheet)."""
    lang = _set_lang(lang)
    if output_path is None:
        output_path = _default_rules_output(lang, a4=False)
    output_path = Path(output_path)

    _ensure_rules_assets()
    _register_fonts()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=(PAGE, PAGE))
    for i, name in enumerate(_register_rules_page_forms(c)):
        if i > 0:
            c.showPage()
        c.doForm(name)
    c.save()
    return output_path


def _page_logo_back(c: canvas.Canvas) -> None:
    """Simple back face: parchment matched to cover_v2 + centred art, no frame."""
    _set_fill(c, COVER_PARCHMENT)
    c.rect(0, 0, PAGE, PAGE, fill=1, stroke=0)
    # Cover art is landscape; keep modest padding so it sits in the square.
    pad_x = 0.35 * CM
    pad_y = 1.35 * CM
    _fit_image(
        c, _COVER, pad_x, pad_y, PAGE - 2 * pad_x, PAGE - 2 * pad_y
    )


def write_rules_a4_pdf(output_path: Path | None = None, *, lang: str = "ca") -> Path:
    """
    Impose all six rules pages on one portrait A4 sheet (duplex).

    Front: 2×3 grid of 9×9 cm tiles (content designed at 10×10, scaled down).
    Back: same grid with the game logo only (parchment + cover_v2, no frame),
    column-mirrored for long-edge duplex flip so each cut card has
    rules on the front and an upright logo on the back.
    """
    lang = _set_lang(lang)
    if output_path is None:
        output_path = _default_rules_output(lang, a4=True)
    output_path = Path(output_path)

    _ensure_rules_assets()
    _register_fonts()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Portrait A4: 2 columns × 3 rows of 9×9 cm tiles.
    cols, rows = 2, 3
    page_size = A4
    aw, ah = page_size
    gap = 0.25 * CM
    margin = 0.45 * CM
    avail_w = aw - 2 * margin - (cols - 1) * gap
    avail_h = ah - 2 * margin - (rows - 1) * gap
    # Prefer exact 9 cm tiles; only shrink further if the sheet is too tight.
    scale = min(A4_TILE / PAGE, avail_w / (cols * PAGE), avail_h / (rows * PAGE))
    tile = PAGE * scale
    total_w = cols * tile + (cols - 1) * gap
    total_h = rows * tile + (rows - 1) * gap
    start_x = (aw - total_w) / 2
    start_y = (ah - total_h) / 2

    c = canvas.Canvas(str(output_path), pagesize=page_size)
    names = _register_rules_page_forms(c)
    if len(names) != 6:
        raise RuntimeError(f"expected 6 rules pages, got {len(names)}")

    logo_name = "enlairats_rules_logo_back"
    c.beginForm(logo_name, 0, 0, PAGE, PAGE)
    _page_logo_back(c)
    c.endForm()

    def place_grid(form_names: list[str], *, mirror_cols: bool = False) -> None:
        for index, name in enumerate(form_names):
            col = index % cols
            row = index // cols  # 0 = top
            if mirror_cols:
                col = cols - 1 - col
            x = start_x + col * (tile + gap)
            y = start_y + (rows - 1 - row) * (tile + gap)
            c.saveState()
            c.translate(x, y)
            c.scale(scale, scale)
            c.doForm(name)
            c.restoreState()

    place_grid(names)
    c.showPage()
    place_grid([logo_name] * 6, mirror_cols=True)
    c.save()
    return output_path
