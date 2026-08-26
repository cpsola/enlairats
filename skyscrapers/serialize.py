"""Board identity, JSON serialization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .clues import SIDES, canonical_clues_blob


def puzzle_id(n: int, clues: dict[str, list[int]]) -> str:
    """First 16 hex chars of SHA-256 over canonical N + clues."""
    digest = hashlib.sha256(canonical_clues_blob(n, clues)).hexdigest()
    return digest[:16]


def board_to_dict(
    *,
    n: int,
    clues: dict[str, list[int]],
    solution: np.ndarray,
    clue_count: int,
    difficulty_score: float,
    difficulty: str,
    seed: int,
) -> dict[str, Any]:
    pid = puzzle_id(n, clues)
    return {
        "id": pid,
        "N": n,
        "clues": {side: list(clues[side]) for side in SIDES},
        "solution": solution.astype(int).tolist(),
        "clue_count": clue_count,
        "difficulty_score": difficulty_score,
        "difficulty": difficulty,
        "seed": seed,
    }


def write_board_json(board: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{board['id']}.json"
    path.write_text(json.dumps(board, indent=2) + "\n", encoding="utf-8")
    return path
