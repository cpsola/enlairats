"""
Generate a 10×10 cm Modernista-styled Enlairats rules booklet PDF.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

from .boards_pdf import (
    CM,
    CREAM,
    CHOCOLATE,
    SAGE,
    TERRACOTTA,
    LEVEL_STYLE,
    _draw_flower,
    _draw_scalloped_frame,
    _register_fonts,
    _set_fill,
    _set_stroke,
)

PAGE = 10 * CM  # 10×10 cm square
# Safe content inset clear of the triple frame and corner curls.
MARGIN = 1.35 * CM
FRAME_INSET = 0.14 * CM
FRAME_FLOURISH_MAX = 0.22 * CM

# Typography defaults
TITLE_SIZE = 11.0
SECTION_SIZE = 8.5
BODY_SIZE = 7.5
BODY_LEADING = 9.6
SMALL_SIZE = 6.5

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_GRAPHICS = _PACKAGE_ROOT / "graphics"
_BUILDINGS = _GRAPHICS / "buildings"
_COVER = _GRAPHICS / "cover_v2.png"

BUILDINGS = [
    {
        "key": "masia_freixa",
        "name": "Masia Freixa",
        "height": "La més baixa",
        "rank": 1,
        "file": _BUILDINGS / "masia_freixa.png",
    },
    {
        "key": "casa_amatller",
        "name": "Casa Amatller",
        "height": "Mitjana-baixa",
        "rank": 2,
        "file": _BUILDINGS / "casa_amatller.png",
    },
    {
        "key": "torre_galatea",
        "name": "Torre Galatea",
        "height": "Mitjana-alta",
        "rank": 3,
        "file": _BUILDINGS / "torre_galatea.png",
    },
    {
        "key": "torre_sagrada_familia",
        "name": "Torre de la Sagrada Família",
        "height": "La més alta",
        "rank": 4,
        "file": _BUILDINGS / "torre_sagrada_familia.png",
    },
]

ALL_EXAMPLES: list[tuple[list[int], str, int]] = [
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
]

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
    _set_fill(c, CREAM)
    c.rect(0, 0, PAGE, PAGE, fill=1, stroke=0)
    pad = MARGIN * 0.55
    _fit_image(
        c, _COVER, pad, pad + 0.4 * CM, PAGE - 2 * pad, PAGE - 2 * pad - 0.5 * CM
    )
    c.setFont("EnlairatsDisplay-Bold", 8)
    c.setFillColorRGB(*CHOCOLATE)
    c.drawCentredString(PAGE / 2, 0.62 * CM, "INSTRUCCIONS")
    _draw_page_frame(c)


def _page_intro(c: canvas.Canvas) -> None:
    _new_page(c)
    y = _content_top()
    y = _title(c, "Què és Enlairats?", y)
    y = _body(
        c,
        "Enlairats és un joc de lògica ambientat en l’arquitectura modernista "
        "catalana. Amb miniatures de quatre edificis construeixes un petit "
        "barri sobre el tauler: has de decidir on va cadascun de manera que, "
        "mirant des dels carrers del voltant, se’n vegin exactament els que "
        "indiquen les pistes. Cada tauler té una sola solució.",
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
    )
    y -= 0.14 * CM
    y -= 0.2 * CM

    y = _section(c, "Contingut", y)
    for item in (
        "Taulers d’Enlairats (graella 4×4 amb pistes al contorn).",
        "Miniatures dels quatre edificis (quatre peces de cada un).",
        "Fitxes de pista (quatre peces amb cada número de 1 a 4).",
    ):
        y = _bullet(c, item, MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.12 * CM

    y -= 0.2 * CM
    y = _section(c, "Objectiu", y)
    y = _body(
        c,
        "Omple totes les caselles de la graella 4×4 col·locant-hi les "
        "miniatures, de manera que es compleixin totes les pistes del "
        "contorn i la regla de barri.",
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
    )
    y -= 0.22 * CM

    y = _section(c, "Preparació", y)
    steps = [
        "Tria una carta de tauler (segons el nivell de dificultat).",
        "Col·loca les fitxes de pistes (circulars de l’1 al 4) al contorn, "
        "reproduïnt el que indica la carta.",
        "Deixa a mà les miniatures dels quatre edificis.",
    ]
    for i, step in enumerate(steps, start=1):
        c.setFillColorRGB(*SAGE)
        c.setFont("EnlairatsDisplay-Bold", 8.5)
        c.drawString(MARGIN, y, f"{i}.")
        y = _body(
            c, step, MARGIN + 0.4 * CM, y, PAGE - 2 * MARGIN - 0.4 * CM
        )
        y -= 0.12 * CM


def _page_buildings(c: canvas.Canvas) -> None:
    _new_page(c)
    y = _content_top()
    y = _title(c, "Els quatre edificis", y)

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
        c.drawCentredString(x0 + cell_w / 2, y0 + 0.10 * CM, b["height"])
        c.setFillColorRGB(*CHOCOLATE)


def _page_howto(c: canvas.Canvas) -> None:
    _new_page(c)
    y = _content_top()
    y = _title(c, "Com es juga", y)
    y = _body(
        c,
        "Omple totes les caselles amb les miniatures respectant les pistes "
        "del contorn i la regla de barri.",
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
    )
    y -= 0.2 * CM

    y = _section(c, "La regla del barri", y)
    for item in (
        "A cada fila, els quatre edificis hi apareixen una sola vegada.",
        "A cada columna, els quatre edificis hi apareixen una sola vegada.",
    ):
        y = _bullet(c, item, MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.08 * CM
    y -= 0.06 * CM
    y = _body(
        c,
        "És a dir, no es pot repetir el mateix edifici a la mateixa fila ni columna.",
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
    )

    y -= 0.2 * CM
    y = _section(c, "Les pistes de contorn", y)
    for item in (
        "Els números del contorn indiquen quants edificis es veuen mirant "
        "aquell carrer en línia recta des d’aquell costat.",
        "Posiciona’t al costat de la pista i mira cap a l’altre extrem. Un edifici és visible només si és més alt que tots els que tens davant.",
        "Els més baixos que queden darrere d’un de més alt queden amagats.",
    ):
        y = _bullet(c, item, MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.06 * CM

    y -= 0.2 * CM
    y = _section(c, "Important", y)
    for item in (
        "Si una posició del contorn no té número, no hi ha pista: no aporta informació.",
        "La Masia Freixa no amaga res al darrere; la Torre de la Sagrada Família "
        "amaga tot el que quedi darrere seu.",
        "No cal endevinar: cada pas es pot deduir amb lògica.",
    ):
        y = _bullet(c, item, MARGIN, y, PAGE - 2 * MARGIN)
        y -= 0.06 * CM


def _page_examples(c: canvas.Canvas) -> None:
    _new_page(c)
    y = _content_top()
    y = _title(c, "Exemples de visibilitat", y)
    y = _body(
        c,
        "Mira d’esquerra a dreta. El cercle verd és la pista. ",
        MARGIN,
        y,
        PAGE - 2 * MARGIN,
        size=BODY_SIZE - 0.15,
    )
    y -= 0.28 * CM

    bottom = _content_bottom()
    available = y - bottom
    n = len(ALL_EXAMPLES)
    example_gap = 0.38 * CM
    slot_h = (available - (n - 1) * example_gap) / n
    icon_h = min(0.82 * CM, slot_h * 0.44)

    for i, (ranks, caption, clue) in enumerate(ALL_EXAMPLES):
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
    _new_page(c)
    y = _content_top()
    y = _title(c, "Com saber si has acabat", y)
    steps = [
        "Totes les caselles tenen una miniatura.",
        "Cap fila ni columna no repeteix el mateix edifici.",
        "Mirant des de cada pista, es veuen exactament tants edificis "
        "com indica el número.",
        "Ara pots girar la carta de tauler i comprovar si la solució és correcta!",
    ]
    for i, step in enumerate(steps, start=1):
        c.setFillColorRGB(*SAGE)
        c.setFont("EnlairatsDisplay-Bold", 8.5)
        c.drawString(MARGIN, y, f"{i}.")
        y = _body(
            c, step, MARGIN + 0.4 * CM, y, PAGE - 2 * MARGIN - 0.4 * CM
        )
        y -= 0.06 * CM

    y -= 0.18 * CM
    y = _title(c, "Nivells de dificultat", y)
    levels = [
        ("Aprenent", "Ideal per aprendre les regles i començar a jugar."),
        ("Oficial", "Diversió garantida quan ja coneixes el joc."),
        ("Mestre artesà", "Raonaments més avançats; combina diverses pistes."),
        ("Arquitecte", "El repte més alt."),
    ]
    for name, desc in levels:
        style = LEVEL_STYLE[name]
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
        "Cada tauler porta una flor i el nom del nivell.",
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
    c.drawCentredString(PAGE / 2, closing_y, "Que gaudeixis construint.")


def write_rules_pdf(output_path: Path | None = None) -> Path:
    """Build the 10×10 cm rules booklet. Returns the output path."""
    if output_path is None:
        output_path = _PACKAGE_ROOT / "physicalgame" / "instruccions.pdf"
    output_path = Path(output_path)

    missing = [b["file"] for b in BUILDINGS if not b["file"].is_file()]
    if missing:
        raise FileNotFoundError(
            "missing building images: " + ", ".join(str(p) for p in missing)
        )
    if not _COVER.is_file():
        raise FileNotFoundError(f"missing cover: {_COVER}")

    _register_fonts()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pages = [
        _page_cover,
        _page_intro,
        _page_buildings,
        _page_howto,
        _page_examples,
        _page_end,
    ]
    total = len(pages)

    c = canvas.Canvas(str(output_path), pagesize=(PAGE, PAGE))
    for i, page_fn in enumerate(pages, start=1):
        if i > 1:
            c.showPage()
        page_fn(c)
        if i > 1:
            _page_number(c, i, total)
    c.save()
    return output_path
