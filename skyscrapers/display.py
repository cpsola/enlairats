"""ASCII (Unicode) terminal rendering of Skyscrapers boards."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from .rater import score_to_label

# ANSI styles (used only when stdout is a TTY, unless forced).
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[1;32m"
_RESET = "\033[0m"


def _paint(text: str, style: str, enabled: bool) -> str:
    if not enabled or not text:
        return text
    return f"{style}{text}{_RESET}"


def _clue_text(value: int, width: int) -> str:
    if value == 0:
        return " " * width
    return str(value).rjust(width)


def _cell_text(value: int | None, width: int, show_solution: bool) -> str:
    if show_solution and value is not None:
        return str(value).rjust(width)
    return "·".center(width) if width == 1 else "·".rjust(width)


def _edge_clue_slot(value: int, digit_width: int, inner: int, use_color: bool) -> str:
    """Center a clue digit in a cell-wide slot; color only the digit."""
    if value == 0:
        return " " * inner
    digit = str(value).rjust(digit_width)
    pad = inner - digit_width
    left_pad = pad // 2
    right_pad = pad - left_pad
    return (" " * left_pad) + _paint(digit, _CYAN, use_color) + (" " * right_pad)


def _horizontal_clues_line(
    values: list[int],
    digit_width: int,
    inner: int,
    use_color: bool,
) -> str:
    """
    Align top/bottom clues with grid columns.

    Matches border layout: ┌───┬───┐  →  ' ' + slot + ' ' + slot …
    (leading space under the corner; spaces under ┬/┴ junctions).
    """
    parts = [" "]  # under ┌ / └
    for i, value in enumerate(values):
        parts.append(_edge_clue_slot(value, digit_width, inner, use_color))
        if i < len(values) - 1:
            parts.append(" ")  # under ┬ / ┴
    return "".join(parts)


def render_board(
    board: dict[str, Any],
    *,
    show_solution: bool = False,
    use_color: bool | None = None,
) -> str:
    """
    Render a classic bordered grid with edge clues and a metadata block.

    Empty cells use '·' unless ``show_solution`` fills heights from ``solution``.
    """
    if use_color is None:
        use_color = sys.stdout.isatty()

    n = int(board["N"])
    clues = board["clues"]
    top = clues["top"]
    bottom = clues["bottom"]
    left = clues["left"]
    right = clues["right"]
    solution = board.get("solution")
    if show_solution and solution is None:
        raise ValueError("board JSON has no solution grid to display")

    w = max(1, len(str(n)))
    inner = w + 2  # padding around cell content
    line_seg = "─" * inner
    top_border = "┌" + "┬".join([line_seg] * n) + "┐"
    mid_border = "├" + "┼".join([line_seg] * n) + "┤"
    bot_border = "└" + "┴".join([line_seg] * n) + "┘"

    left_gutter = w + 1  # left clue + space before grid

    def indent_grid(s: str) -> str:
        return (" " * left_gutter) + s

    lines: list[str] = []

    # --- metadata ---
    score = float(board["difficulty_score"])
    label = board.get("difficulty") or score_to_label(score)
    meta = [
        f"id:               {board['id']}",
        f"N:                {n}",
        f"clue_count:       {board['clue_count']}",
        f"difficulty_score: {score}",
        f"difficulty:       {label}",
        f"seed:             {board['seed']}",
    ]
    if show_solution:
        meta.append("view:             solution")
    else:
        meta.append("view:             playable")
    for row in meta:
        lines.append(_paint(row, _DIM, use_color))
    lines.append("")

    # --- top clues ---
    lines.append(
        indent_grid(_horizontal_clues_line(top, w, inner, use_color))
    )

    # --- grid ---
    lines.append(_paint(indent_grid(top_border), _DIM, use_color))
    for r in range(n):
        left_raw = _clue_text(left[r], w)
        left_cell = _paint(left_raw, _CYAN, use_color) if left[r] else left_raw

        pieces: list[str] = [f"{left_cell} ", _paint("│", _DIM, use_color)]
        for c in range(n):
            raw_val = int(solution[r][c]) if show_solution else None
            body = _cell_text(raw_val, w, show_solution)
            if show_solution:
                body = _paint(body, _GREEN, use_color)
            else:
                body = _paint(body, _DIM, use_color)
            pieces.append(f" {body} ")
            pieces.append(_paint("│", _DIM, use_color))
        right_raw = _clue_text(right[r], w)
        right_cell = _paint(right_raw, _CYAN, use_color) if right[r] else right_raw
        pieces.append(f" {right_cell}")
        lines.append("".join(pieces))

        if r < n - 1:
            lines.append(_paint(indent_grid(mid_border), _DIM, use_color))
    lines.append(_paint(indent_grid(bot_border), _DIM, use_color))

    # --- bottom clues ---
    lines.append(
        indent_grid(_horizontal_clues_line(bottom, w, inner, use_color))
    )

    return "\n".join(lines)


def print_board(
    board: dict[str, Any],
    *,
    show_solution: bool = False,
    use_color: bool | None = None,
    file: TextIO | None = None,
) -> None:
    text = render_board(board, show_solution=show_solution, use_color=use_color)
    print(text, file=file or sys.stdout)


def load_board_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"board file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    required = ("id", "N", "clues", "clue_count", "difficulty_score", "seed")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"board JSON missing fields: {', '.join(missing)}")
    clues = data["clues"]
    for side in ("top", "bottom", "left", "right"):
        if side not in clues:
            raise ValueError(f"board JSON missing clues.{side}")
    return data
