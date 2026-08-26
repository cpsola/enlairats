"""Backtracking solver used to count solutions (0, 1, or 2+)."""

from __future__ import annotations

import numpy as np

from .visibility import visible_count


def count_solutions(
    n: int,
    clues: dict[str, list[int]],
    limit: int = 2,
) -> int:
    """
    Count solutions up to `limit` (typically 2 for uniqueness checks).

    Empty cells are 0. Clue value 0 means no constraint on that edge.
    """
    grid = np.zeros((n, n), dtype=np.int8)
    row_used = [0] * n  # bitmasks, bit h set => height h used (h in 1..n)
    col_used = [0] * n
    found = 0

    top = clues["top"]
    bottom = clues["bottom"]
    left = clues["left"]
    right = clues["right"]

    def row_ok(r: int) -> bool:
        line = grid[r, :]
        if left[r] and visible_count(line) != left[r]:
            return False
        if right[r] and visible_count(line[::-1]) != right[r]:
            return False
        return True

    def col_ok(c: int) -> bool:
        line = grid[:, c]
        if top[c] and visible_count(line) != top[c]:
            return False
        if bottom[c] and visible_count(line[::-1]) != bottom[c]:
            return False
        return True

    def partial_row_possible(r: int, filled_through: int) -> bool:
        """Prune using left clue while the row is only partly filled."""
        if not left[r]:
            return True
        prefix = grid[r, : filled_through + 1]
        return visible_count(prefix) <= left[r]

    def place(cell: int) -> bool:
        nonlocal found
        if found >= limit:
            return True
        if cell == n * n:
            # Full grid: verify all clues (partial checks may have been soft).
            for r in range(n):
                if not row_ok(r):
                    return False
            for c in range(n):
                if not col_ok(c):
                    return False
            found += 1
            return found >= limit

        r, c = divmod(cell, n)
        for h in range(1, n + 1):
            bit = 1 << h
            if row_used[r] & bit or col_used[c] & bit:
                continue
            grid[r, c] = h
            row_used[r] |= bit
            col_used[c] |= bit

            ok = True
            if c == n - 1 and not row_ok(r):
                ok = False
            if ok and r == n - 1 and not col_ok(c):
                ok = False
            # Soft left-clue prune on partial row
            if ok and not partial_row_possible(r, c):
                ok = False

            if ok:
                place(cell + 1)

            grid[r, c] = 0
            row_used[r] &= ~bit
            col_used[c] &= ~bit
            if found >= limit:
                return True
        return found >= limit

    place(0)
    return found


def has_unique_solution(n: int, clues: dict[str, list[int]]) -> bool:
    return count_solutions(n, clues, limit=2) == 1
