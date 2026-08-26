"""Clue helpers and edge-slot indexing."""

from __future__ import annotations

from typing import Iterable

# Side name -> clue array key used in JSON / generator.
SIDES = ("top", "bottom", "left", "right")


def max_clues(n: int) -> int:
    return 4 * n


def clue_count(clues: dict[str, list[int]]) -> int:
    return sum(1 for side in SIDES for v in clues[side] if v != 0)


def copy_clues(clues: dict[str, list[int]]) -> dict[str, list[int]]:
    return {side: list(clues[side]) for side in SIDES}


def all_slots(n: int) -> list[tuple[str, int]]:
    """Every border slot as (side, index)."""
    slots: list[tuple[str, int]] = []
    for side in SIDES:
        for i in range(n):
            slots.append((side, i))
    return slots


def zero_clues(n: int) -> dict[str, list[int]]:
    return {side: [0] * n for side in SIDES}


def iter_nonzero_slots(clues: dict[str, list[int]]) -> Iterable[tuple[str, int]]:
    for side in SIDES:
        for i, value in enumerate(clues[side]):
            if value != 0:
                yield side, i


def canonical_clues_blob(n: int, clues: dict[str, list[int]]) -> bytes:
    """
    Stable encoding of N + clues for hashing IDs.

    Layout: n as decimal, then top, bottom, left, right values
    separated by commas / semicolons.
    """
    parts = [str(n)]
    for side in SIDES:
        parts.append(",".join(str(int(v)) for v in clues[side]))
    return ";".join(parts).encode("ascii")
