"""Visibility counts for Skyscrapers lines."""

from __future__ import annotations

import numpy as np


def visible_count(line: np.ndarray | list[int]) -> int:
    """How many buildings are visible looking from index 0 toward the end."""
    tallest = 0
    count = 0
    for height in line:
        h = int(height)
        if h > tallest:
            count += 1
            tallest = h
    return count


def clues_from_grid(grid: np.ndarray) -> dict[str, list[int]]:
    """Compute all four border clue arrays from a completed grid."""
    n = grid.shape[0]
    top = [visible_count(grid[:, j]) for j in range(n)]
    bottom = [visible_count(grid[::-1, j]) for j in range(n)]
    left = [visible_count(grid[i, :]) for i in range(n)]
    right = [visible_count(grid[i, ::-1]) for i in range(n)]
    return {"top": top, "bottom": bottom, "left": left, "right": right}
