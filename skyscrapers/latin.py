"""Random Latin-square style grids for Skyscrapers solutions."""

from __future__ import annotations

import numpy as np


def generate_latin_square(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Build a random n×n Latin square with symbols 1..n via backtracking.

    Each row and each column contains every height exactly once.
    """
    grid = np.zeros((n, n), dtype=np.int8)
    row_used = [set() for _ in range(n)]
    col_used = [set() for _ in range(n)]

    def place(cell: int) -> bool:
        if cell == n * n:
            return True
        r, c = divmod(cell, n)
        heights = np.arange(1, n + 1)
        rng.shuffle(heights)
        for h in heights:
            h = int(h)
            if h in row_used[r] or h in col_used[c]:
                continue
            grid[r, c] = h
            row_used[r].add(h)
            col_used[c].add(h)
            if place(cell + 1):
                return True
            grid[r, c] = 0
            row_used[r].remove(h)
            col_used[c].remove(h)
        return False

    if not place(0):
        raise RuntimeError(f"Failed to generate a Latin square of size {n}")
    return grid
