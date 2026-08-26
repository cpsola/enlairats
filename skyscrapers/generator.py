"""Generate unique Skyscrapers puzzles with target clue counts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .clues import (
    all_slots,
    clue_count,
    copy_clues,
    max_clues,
)
from .latin import generate_latin_square
from .rater import RatingResult, rate_puzzle
from .serialize import board_to_dict
from .solver import has_unique_solution
from .visibility import clues_from_grid


@dataclass
class GenerateResult:
    board: dict
    rating: RatingResult
    attempts_used: int


class GenerationError(Exception):
    pass


def _reduce_clues_toward_target(
    n: int,
    full_clues: dict[str, list[int]],
    target: int,
    rng: np.random.Generator,
) -> dict[str, list[int]] | None:
    """
    Start from a full clue set and remove clues in random order until
    we reach `target` or can remove no more without losing uniqueness.

    Returns the reduced clue dict, or None if the full set itself is not unique
    (should not happen for clues derived from a Latin square).
    """
    clues = copy_clues(full_clues)
    if not has_unique_solution(n, clues):
        return None

    slots = all_slots(n)
    rng.shuffle(slots)

    for side, index in slots:
        if clue_count(clues) <= target:
            break
        if clues[side][index] == 0:
            continue
        saved = clues[side][index]
        clues[side][index] = 0
        if has_unique_solution(n, clues):
            continue
        clues[side][index] = saved

    return clues


def _nearest_in_interval(value: int, lo: int, hi: int) -> bool:
    return lo <= value <= hi


def generate_one(
    n: int,
    clue_lo: int,
    clue_hi: int,
    max_attempts: int,
    rng: np.random.Generator | None = None,
) -> GenerateResult:
    """
    Attempt to generate one unique puzzle with clue_count in [clue_lo, clue_hi],
    aiming for a random target inside that interval (nearest achievable allowed).
    """
    if n < 1:
        raise ValueError("size N must be >= 1")
    upper = max_clues(n)
    if clue_lo < 1 or clue_hi > upper or clue_lo > clue_hi:
        raise ValueError(f"clue interval must satisfy 1 <= lo <= hi <= {upper}")

    for attempt in range(1, max_attempts + 1):
        seed = int(np.random.default_rng().integers(0, 2**63 - 1)) if rng is None else int(rng.integers(0, 2**63 - 1))
        board_rng = np.random.default_rng(seed)

        solution = generate_latin_square(n, board_rng)
        full = clues_from_grid(solution)
        target = int(board_rng.integers(clue_lo, clue_hi + 1))

        reduced = _reduce_clues_toward_target(n, full, target, board_rng)
        if reduced is None:
            continue

        count = clue_count(reduced)
        if not _nearest_in_interval(count, clue_lo, clue_hi):
            # Stuck above the interval (could not remove enough).
            continue

        if not has_unique_solution(n, reduced):
            continue

        rating = rate_puzzle(n, reduced)
        board = board_to_dict(
            n=n,
            clues=reduced,
            solution=solution,
            clue_count=count,
            difficulty_score=rating.score,
            difficulty=rating.label,
            seed=seed,
        )
        return GenerateResult(board=board, rating=rating, attempts_used=attempt)

    raise GenerationError(
        f"Failed to generate a unique {n}×{n} board with clues in "
        f"[{clue_lo}, {clue_hi}] after {max_attempts} attempts"
    )


def generate_many(
    n: int,
    count: int,
    clue_lo: int,
    clue_hi: int,
    max_attempts: int,
) -> list[GenerateResult]:
    results: list[GenerateResult] = []
    seen_ids: set[str] = set()
    # Extra attempts across the batch in case of ID collisions (rare).
    batch_guard = 0
    while len(results) < count:
        batch_guard += 1
        if batch_guard > count * max_attempts:
            raise GenerationError(
                f"Could only produce {len(results)}/{count} distinct boards"
            )
        result = generate_one(n, clue_lo, clue_hi, max_attempts)
        pid = result.board["id"]
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        results.append(result)
    return results
