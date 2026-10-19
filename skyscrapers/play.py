"""Tkinter play UI for a Skyscrapers board JSON."""

from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Any

from .display import load_board_json
from .rater import score_to_label

# Basic palette
_BG = "#f4f1ec"
_CELL = "#ffffff"
_CELL_SELECTED = "#d6eaf8"
_CELL_LOCKED = "#e8e8e8"
_CLUE = "#1a6b7a"
_TEXT = "#1c1c1c"
_COORD = "#b0b0b0"
_META = "#555555"
_BTN = "#e7e0d6"


class PlayApp:
    def __init__(self, root: tk.Tk, board: dict[str, Any], source_path: Path) -> None:
        self.root = root
        self.board = board
        self.source_path = source_path
        self.n = int(board["N"])
        self.solution = [[int(v) for v in row] for row in board["solution"]]
        self.clues = board["clues"]

        self.grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
        self.selected: tuple[int, int] | None = None
        self.undo_stack: list[tuple[int, int, int, int]] = []  # r, c, before, after
        self.solved = False
        self._digit_buffer = ""
        self._digit_job: str | None = None

        # Each cell: (frame, value_label, coord_label)
        self.cell_widgets: list[list[tuple[tk.Frame, tk.Label, tk.Label]]] = []

        root.title(f"Skyscrapers — {board['id']}")
        root.configure(bg=_BG)
        root.protocol("WM_DELETE_WINDOW", self._quit)

        self._build_ui()
        self._refresh_cells()

        root.bind_all("<Key>", self._on_key)
        root.bind_all("<Escape>", lambda _e: self._quit())

    def _make_cell(self, parent: tk.Frame, r: int, c: int, font_cell: tuple) -> tuple[tk.Frame, tk.Label, tk.Label]:
        """Build one playable cell with faint (row,col) and a centered height."""
        cell_w = max(44, 18 + 6 * self.n)
        cell_h = max(44, 18 + 6 * self.n)
        frame = tk.Frame(
            parent,
            bg=_CELL,
            highlightthickness=2,
            highlightbackground="#c8c8c8",
            highlightcolor="#c8c8c8",
            width=cell_w,
            height=cell_h,
        )
        frame.grid_propagate(False)
        frame.pack_propagate(False)

        coord = tk.Label(
            frame,
            text=f"{r},{c}",
            fg=_COORD,
            bg=_CELL,
            font=("Helvetica", 7),
            anchor="nw",
        )
        coord.place(x=3, y=1)

        value = tk.Label(
            frame,
            text="",
            fg=_TEXT,
            bg=_CELL,
            font=font_cell,
        )
        value.place(relx=0.5, rely=0.55, anchor="center")

        def on_click(_event: tk.Event, rr: int = r, cc: int = c) -> None:
            self._select(rr, cc)

        for widget in (frame, coord, value):
            widget.bind("<Button-1>", on_click)

        return frame, value, coord

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=_BG, padx=16, pady=12)
        outer.pack(fill="both", expand=True)

        score = float(self.board["difficulty_score"])
        label = self.board.get("difficulty") or score_to_label(score)
        meta = (
            f"id: {self.board['id']}   "
            f"N: {self.n}   "
            f"clues: {self.board['clue_count']}   "
            f"score: {score} ({label})   "
            f"seed: {self.board['seed']}\n"
            f"file: {self.source_path}"
        )
        tk.Label(
            outer,
            text=meta,
            justify="left",
            anchor="w",
            fg=_META,
            bg=_BG,
            font=("Helvetica", 10),
        ).pack(fill="x", pady=(0, 10))

        board_frame = tk.Frame(outer, bg=_BG)
        board_frame.pack()

        cell_font_size = max(12, 18 - max(0, self.n - 4))
        font_cell = ("Helvetica", cell_font_size, "bold")
        font_clue = ("Helvetica", 12, "bold")

        # column weights: 0=left clues, 1..n=cells, n+1=right clues
        # row weights: 0=top clues, 1..n=cells, n+1=bottom clues

        for c in range(self.n):
            val = self.clues["top"][c]
            text = "" if val == 0 else str(val)
            tk.Label(
                board_frame,
                text=text,
                fg=_CLUE,
                bg=_BG,
                font=font_clue,
                width=3,
            ).grid(row=0, column=c + 1, padx=2, pady=2)

        for r in range(self.n):
            left_val = self.clues["left"][r]
            tk.Label(
                board_frame,
                text="" if left_val == 0 else str(left_val),
                fg=_CLUE,
                bg=_BG,
                font=font_clue,
                width=3,
            ).grid(row=r + 1, column=0, padx=2, pady=2)

            row_cells: list[tuple[tk.Frame, tk.Label, tk.Label]] = []
            for c in range(self.n):
                frame, value, coord = self._make_cell(board_frame, r, c, font_cell)
                frame.grid(row=r + 1, column=c + 1, padx=2, pady=2)
                row_cells.append((frame, value, coord))
            self.cell_widgets.append(row_cells)

            right_val = self.clues["right"][r]
            tk.Label(
                board_frame,
                text="" if right_val == 0 else str(right_val),
                fg=_CLUE,
                bg=_BG,
                font=font_clue,
                width=3,
            ).grid(row=r + 1, column=self.n + 1, padx=2, pady=2)

        for c in range(self.n):
            val = self.clues["bottom"][c]
            tk.Label(
                board_frame,
                text="" if val == 0 else str(val),
                fg=_CLUE,
                bg=_BG,
                font=font_clue,
                width=3,
            ).grid(row=self.n + 1, column=c + 1, padx=2, pady=2)

        controls = tk.Frame(outer, bg=_BG, pady=14)
        controls.pack()

        for text, cmd in (
            ("Undo", self._undo),
            ("Clear cell", self._clear_selected),
            ("Reset", self._reset),
        ):
            tk.Button(
                controls,
                text=text,
                command=cmd,
                bg=_BTN,
                fg=_TEXT,
                activebackground=_CELL_SELECTED,
                padx=10,
                pady=4,
                font=("Helvetica", 11),
            ).pack(side="left", padx=4)

        help_text = (
            "Click a cell, type 1–N to place a height. "
            "Delete/Backspace clears the selected cell. "
            "The puzzle is checked automatically when the grid is full."
        )
        tk.Label(
            outer,
            text=help_text,
            fg=_META,
            bg=_BG,
            font=("Helvetica", 9),
        ).pack(pady=(4, 0))

    def _select(self, r: int, c: int) -> None:
        if self.solved:
            return
        self.selected = (r, c)
        self._digit_buffer = ""
        self._refresh_cells()
        self.root.focus_set()

    def _refresh_cells(self) -> None:
        for r in range(self.n):
            for c in range(self.n):
                frame, value_lbl, coord_lbl = self.cell_widgets[r][c]
                val = self.grid[r][c]
                value_lbl.configure(text="" if val == 0 else str(val))
                if self.solved:
                    bg = _CELL_LOCKED
                    border = "#a8a8a8"
                elif self.selected == (r, c):
                    bg = _CELL_SELECTED
                    border = _CLUE
                else:
                    bg = _CELL
                    border = "#c8c8c8"
                frame.configure(bg=bg, highlightbackground=border, highlightcolor=border)
                value_lbl.configure(bg=bg)
                coord_lbl.configure(bg=bg)

    def _push_change(self, r: int, c: int, new_val: int) -> None:
        old = self.grid[r][c]
        if old == new_val:
            return
        self.undo_stack.append((r, c, old, new_val))
        self.grid[r][c] = new_val
        self._refresh_cells()
        self._autosubmit_if_full()

    def _is_full(self) -> bool:
        return all(self.grid[r][c] != 0 for r in range(self.n) for c in range(self.n))

    def _autosubmit_if_full(self) -> None:
        if self.solved or not self._is_full():
            return
        for r in range(self.n):
            for c in range(self.n):
                if self.grid[r][c] != self.solution[r][c]:
                    messagebox.showwarning(
                        "Not solved",
                        "This is not the correct solution yet.\nKeep going!",
                        parent=self.root,
                    )
                    return
        self.solved = True
        self._refresh_cells()
        messagebox.showinfo(
            "Solved",
            "Correct — puzzle solved!",
            parent=self.root,
        )

    def _on_key(self, event: tk.Event) -> None:
        if self.solved:
            return
        key = event.keysym
        if key in ("BackSpace", "Delete"):
            self._clear_selected()
            return
        if key == "u" and (event.state & 0x4):  # Ctrl+U optional; ignore
            return

        ch = event.char
        if not ch:
            return
        if ch.isdigit():
            self._handle_digit(ch)

    def _handle_digit(self, ch: str) -> None:
        if self.selected is None:
            return
        if self.n < 10:
            value = int(ch)
            if 1 <= value <= self.n:
                r, c = self.selected
                self._push_change(r, c, value)
            return

        # Multi-digit N: buffer digits briefly, commit when valid / complete.
        self._digit_buffer += ch
        if self._digit_job is not None:
            self.root.after_cancel(self._digit_job)
        self._digit_job = self.root.after(700, self._flush_digit_buffer)

        value = int(self._digit_buffer)
        if 1 <= value <= self.n and len(self._digit_buffer) >= len(str(self.n)):
            r, c = self.selected
            self._push_change(r, c, value)
            self._digit_buffer = ""
            if self._digit_job is not None:
                self.root.after_cancel(self._digit_job)
                self._digit_job = None
        elif value > self.n:
            self._digit_buffer = ch
            value = int(ch)
            if 1 <= value <= self.n:
                r, c = self.selected
                self._push_change(r, c, value)
                self._digit_buffer = ""

    def _flush_digit_buffer(self) -> None:
        self._digit_job = None
        if not self._digit_buffer or self.selected is None or self.solved:
            self._digit_buffer = ""
            return
        value = int(self._digit_buffer)
        self._digit_buffer = ""
        if 1 <= value <= self.n:
            r, c = self.selected
            self._push_change(r, c, value)

    def _clear_selected(self) -> None:
        if self.solved or self.selected is None:
            return
        r, c = self.selected
        self._push_change(r, c, 0)

    def _undo(self) -> None:
        if self.solved or not self.undo_stack:
            return
        r, c, before, _after = self.undo_stack.pop()
        self.grid[r][c] = before
        self.selected = (r, c)
        self._refresh_cells()

    def _reset(self) -> None:
        if self.solved:
            return
        # Snapshot whole board as individual undos would be noisy; one composite:
        # push each non-empty clear so repeated Undo restores step-by-step,
        # or clear stack after reset. Spec: unlimited undo — push clears then
        # allow undo to refill. Simpler UX: reset clears history.
        for r in range(self.n):
            for c in range(self.n):
                self.grid[r][c] = 0
        self.undo_stack.clear()
        self.selected = None
        self._digit_buffer = ""
        self._refresh_cells()

    def _quit(self) -> None:
        self.root.destroy()


def pick_random_board(output_dir: Path) -> Path:
    if not output_dir.is_dir():
        raise FileNotFoundError(f"output directory not found: {output_dir}")
    files = sorted(output_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no board JSON files in {output_dir}")
    return random.choice(files)


def load_playable_board(path: Path) -> dict[str, Any]:
    board = load_board_json(path)
    if "solution" not in board:
        raise ValueError(f"board JSON has no solution (needed to play): {path}")
    n = int(board["N"])
    solution = board["solution"]
    if len(solution) != n or any(len(row) != n for row in solution):
        raise ValueError(f"solution grid is not {n}×{n}: {path}")
    return board


def run_play(path: Path) -> int:
    """
    Open the play window for ``path``.

    Returns 0 on normal close (quit, window close, or after solving).
    """
    board = load_playable_board(path)
    root = tk.Tk()
    PlayApp(root, board, path)
    root.mainloop()
    return 0
