"""
Technique-ladder difficulty rating for Skyscrapers puzzles.

Techniques (easy → hard):
  1. Direct clue placements (clue 1 / clue N)
  2. Latin singles (naked / hidden)
  3. Visibility candidate pruning
  4. Full-line permutation intersection
  5. Shallow case reasoning (depth-1 contradiction)
  6. Deep search (branching)

The numeric score is a weighted sum of technique usage. Labels are derived
from thresholds that we can tune later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from typing import Optional

import numpy as np

from .visibility import visible_count

# --- weights & label thresholds (initial defaults; refine later) ---

TECHNIQUE_WEIGHTS = {
    "direct": 1.0,
    "latin": 2.0,
    "visibility": 4.0,
    "line_enum": 8.0,
    "shallow_case": 20.0,
    "deep_search": 40.0,
}

# Extra cost per deep-search decision node / max depth.
DEEP_NODE_WEIGHT = 3.0
DEEP_DEPTH_WEIGHT = 8.0

DIFFICULTY_THRESHOLDS = (
    ("easy", 25.0),
    ("medium", 70.0),
    ("hard", 150.0),
    # anything >= 150 → expert
)


def score_to_label(score: float) -> str:
    label = "expert"
    for name, upper in DIFFICULTY_THRESHOLDS:
        if score < upper:
            return name
        label = "expert"
    return label


@dataclass
class RatingResult:
    score: float
    label: str
    technique_counts: dict[str, int] = field(default_factory=dict)
    deep_nodes: int = 0
    deep_max_depth: int = 0
    trace: list[str] = field(default_factory=list)
    solved: bool = False


@dataclass
class _State:
    n: int
    clues: dict[str, list[int]]
    # cand[r][c] = set of possible heights
    cand: list[list[set[int]]]
    grid: np.ndarray  # 0 empty, else placed height

    def clone(self) -> "_State":
        return _State(
            n=self.n,
            clues=self.clues,
            cand=[[set(s) for s in row] for row in self.cand],
            grid=self.grid.copy(),
        )


def _empty_state(n: int, clues: dict[str, list[int]]) -> _State:
    cand = [[set(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
    return _State(n=n, clues=clues, cand=cand, grid=np.zeros((n, n), dtype=np.int8))


def _place(state: _State, r: int, c: int, h: int) -> bool:
    """Place height h at (r,c). Return False if contradiction."""
    if h not in state.cand[r][c]:
        return False
    state.grid[r, c] = h
    state.cand[r][c] = {h}
    for cc in range(state.n):
        if cc != c:
            state.cand[r][cc].discard(h)
            if not state.cand[r][cc]:
                return False
    for rr in range(state.n):
        if rr != r:
            state.cand[rr][c].discard(h)
            if not state.cand[rr][c]:
                return False
    return True


def _apply_direct(state: _State) -> int:
    """Clue 1 → N at near edge; clue N → strictly increasing 1..N."""
    changes = 0
    n = state.n
    top, bottom = state.clues["top"], state.clues["bottom"]
    left, right = state.clues["left"], state.clues["right"]

    for c, clue in enumerate(top):
        if clue == 1 and n in state.cand[0][c] and state.grid[0, c] != n:
            if _place(state, 0, c, n):
                changes += 1
            else:
                return -1
        if clue == n:
            for r in range(n):
                if state.grid[r, c] != r + 1:
                    if not _place(state, r, c, r + 1):
                        return -1
                    changes += 1

    for c, clue in enumerate(bottom):
        if clue == 1 and n in state.cand[n - 1][c] and state.grid[n - 1, c] != n:
            if _place(state, n - 1, c, n):
                changes += 1
            else:
                return -1
        if clue == n:
            for i in range(n):
                r = n - 1 - i
                h = i + 1
                if state.grid[r, c] != h:
                    if not _place(state, r, c, h):
                        return -1
                    changes += 1

    for r, clue in enumerate(left):
        if clue == 1 and n in state.cand[r][0] and state.grid[r, 0] != n:
            if _place(state, r, 0, n):
                changes += 1
            else:
                return -1
        if clue == n:
            for c in range(n):
                if state.grid[r, c] != c + 1:
                    if not _place(state, r, c, c + 1):
                        return -1
                    changes += 1

    for r, clue in enumerate(right):
        if clue == 1 and n in state.cand[r][n - 1] and state.grid[r, n - 1] != n:
            if _place(state, r, n - 1, n):
                changes += 1
            else:
                return -1
        if clue == n:
            for i in range(n):
                c = n - 1 - i
                h = i + 1
                if state.grid[r, c] != h:
                    if not _place(state, r, c, h):
                        return -1
                    changes += 1

    return changes


def _apply_latin(state: _State) -> int:
    """Naked singles and hidden singles."""
    changes = 0
    n = state.n

    # Naked singles
    for r in range(n):
        for c in range(n):
            if state.grid[r, c] == 0 and len(state.cand[r][c]) == 1:
                h = next(iter(state.cand[r][c]))
                if not _place(state, r, c, h):
                    return -1
                changes += 1

    # Hidden singles in rows
    for r in range(n):
        for h in range(1, n + 1):
            positions = [c for c in range(n) if h in state.cand[r][c]]
            if len(positions) == 0:
                return -1
            if len(positions) == 1:
                c = positions[0]
                if state.grid[r, c] != h:
                    if not _place(state, r, c, h):
                        return -1
                    changes += 1

    # Hidden singles in cols
    for c in range(n):
        for h in range(1, n + 1):
            positions = [r for r in range(n) if h in state.cand[r][c]]
            if len(positions) == 0:
                return -1
            if len(positions) == 1:
                r = positions[0]
                if state.grid[r, c] != h:
                    if not _place(state, r, c, h):
                        return -1
                    changes += 1

    return changes


def _visibility_bounds_ok(line: list[int], near_clue: int, far_clue: int) -> bool:
    if near_clue and visible_count(line) != near_clue:
        return False
    if far_clue and visible_count(list(reversed(line))) != far_clue:
        return False
    return True


def _apply_visibility(state: _State) -> int:
    """
    Eliminate candidates that cannot participate in any visibility-legal
    completion of their row/column, using the tallest-building position rule:

    If the near clue is k > 0, height n must sit at index i >= k - 1
    (at most k visibles are possible when n is at i, and visibles = vis(prefix)+1).
    """
    changes = 0
    n = state.n

    def prune_line(
        cells: list[set[int]],
        near: int,
        far: int,
        write_back,
    ) -> int:
        local_changes = 0
        if near == 1:
            if n not in cells[0]:
                return -1
            before = set(cells[0])
            cells[0] = {n}
            if cells[0] != before:
                local_changes += 1
        if far == 1:
            if n not in cells[-1]:
                return -1
            before = set(cells[-1])
            cells[-1] = {n}
            if cells[-1] != before:
                local_changes += 1
        if near > 0:
            # n requires index >= near - 1
            min_i = near - 1
            for i, cell in enumerate(cells):
                if i < min_i and n in cell:
                    cell.discard(n)
                    local_changes += 1
                    if not cell:
                        return -1
        if far > 0:
            # from far side: j = n-1-i >= far-1  =>  i <= n - far
            max_i = n - far
            for i, cell in enumerate(cells):
                if i > max_i and n in cell:
                    cell.discard(n)
                    local_changes += 1
                    if not cell:
                        return -1
        write_back(cells)
        return local_changes

    for r in range(n):
        cells = [set(s) for s in state.cand[r]]

        def wb_row(cells_r, row=r):
            for c, s in enumerate(cells_r):
                state.cand[row][c] = s

        ch = prune_line(cells, state.clues["left"][r], state.clues["right"][r], wb_row)
        if ch < 0:
            return -1
        changes += ch

    for c in range(n):
        cells = [set(state.cand[r][c]) for r in range(n)]

        def wb_col(cells_c, col=c):
            for r, s in enumerate(cells_c):
                state.cand[r][col] = s

        ch = prune_line(cells, state.clues["top"][c], state.clues["bottom"][c], wb_col)
        if ch < 0:
            return -1
        changes += ch

    return changes


def _valid_line_perms(
    cell_cands: list[set[int]],
    near_clue: int,
    far_clue: int,
) -> list[tuple[int, ...]]:
    n = len(cell_cands)
    heights = list(range(1, n + 1))
    valid: list[tuple[int, ...]] = []
    for perm in permutations(heights):
        if any(h not in cell_cands[i] for i, h in enumerate(perm)):
            continue
        if not _visibility_bounds_ok(list(perm), near_clue, far_clue):
            continue
        valid.append(perm)
    return valid


def _apply_line_enum(state: _State) -> int:
    """Intersect candidates with visibility-legal Latin permutations of each line."""
    changes = 0
    n = state.n

    for r in range(n):
        cells = [set(state.cand[r][c]) for c in range(n)]
        perms = _valid_line_perms(cells, state.clues["left"][r], state.clues["right"][r])
        if not perms:
            return -1
        for c in range(n):
            allowed = {p[c] for p in perms}
            before = set(state.cand[r][c])
            state.cand[r][c] &= allowed
            if not state.cand[r][c]:
                return -1
            if state.cand[r][c] != before:
                changes += 1
            if len(state.cand[r][c]) == 1 and state.grid[r, c] == 0:
                if not _place(state, r, c, next(iter(state.cand[r][c]))):
                    return -1

    for c in range(n):
        cells = [set(state.cand[r][c]) for r in range(n)]
        perms = _valid_line_perms(cells, state.clues["top"][c], state.clues["bottom"][c])
        if not perms:
            return -1
        for r in range(n):
            allowed = {p[r] for p in perms}
            before = set(state.cand[r][c])
            state.cand[r][c] &= allowed
            if not state.cand[r][c]:
                return -1
            if state.cand[r][c] != before:
                changes += 1
            if len(state.cand[r][c]) == 1 and state.grid[r, c] == 0:
                if not _place(state, r, c, next(iter(state.cand[r][c]))):
                    return -1

    return changes


def _propagate_easy(
    state: _State,
    counts: dict[str, int],
    trace: list[str] | None = None,
) -> bool:
    """
    Apply techniques 1–4 to quiescence.
    Returns False on contradiction.
    """
    order = (
        ("direct", _apply_direct),
        ("latin", _apply_latin),
        ("visibility", _apply_visibility),
        ("line_enum", _apply_line_enum),
    )
    while True:
        progressed = False
        for name, fn in order:
            before = _snapshot(state) if trace is not None else None
            ch = fn(state)
            if ch < 0:
                if trace is not None:
                    trace.append(f"{name}: contradiction")
                return False
            if ch > 0:
                counts[name] = counts.get(name, 0) + ch
                if trace is not None and before is not None:
                    trace.extend(_diff_messages(before, state, name))
                progressed = True
                break  # restart from the easiest technique
        if not progressed:
            return True


def _snapshot(state: _State) -> dict:
    return {
        "grid": state.grid.copy(),
        "cand": [[set(s) for s in row] for row in state.cand],
    }


def _diff_messages(before: dict, after: _State, technique: str) -> list[str]:
    """Describe placements and candidate shrinks between two states."""
    messages: list[str] = []
    n = after.n
    for r in range(n):
        for c in range(n):
            old_h = int(before["grid"][r, c])
            new_h = int(after.grid[r, c])
            if old_h == 0 and new_h != 0:
                messages.append(
                    f"{technique}: place {new_h} at ({r},{c})"
                )
            old_cands = before["cand"][r][c]
            new_cands = after.cand[r][c]
            removed = old_cands - new_cands
            if removed and not (old_h == 0 and new_h != 0 and new_cands == {new_h}):
                # Skip pure placement shrink noise when we already logged place;
                # still log extra eliminations on other cells / partial shrinks.
                if old_h == 0 and new_h != 0 and removed == old_cands - {new_h} and new_cands == {new_h}:
                    continue
                left = "{" + ",".join(str(x) for x in sorted(new_cands)) + "}"
                gone = "{" + ",".join(str(x) for x in sorted(removed)) + "}"
                messages.append(
                    f"{technique}: candidates at ({r},{c}) remove {gone} → {left}"
                )
    if not messages:
        messages.append(f"{technique}: progress ({after.n}×{after.n} state changed)")
    return messages


def _is_solved(state: _State) -> bool:
    return bool(np.all(state.grid != 0))


def _pick_branch_cell(state: _State) -> Optional[tuple[int, int]]:
    best = None
    best_len = 10**9
    for r in range(state.n):
        for c in range(state.n):
            if state.grid[r, c] != 0:
                continue
            k = len(state.cand[r][c])
            if k < best_len and k >= 2:
                best_len = k
                best = (r, c)
    return best


def _apply_shallow_cases(
    state: _State,
    counts: dict[str, int],
    trace: list[str] | None = None,
) -> int:
    """
    Depth-1 contradiction: for a bivalue (or small) cell, try each candidate
    with easy propagation; eliminate those that contradict.
    """
    changes = 0
    n = state.n
    cells = [
        (r, c)
        for r in range(n)
        for c in range(n)
        if state.grid[r, c] == 0 and 2 <= len(state.cand[r][c]) <= 3
    ]
    for r, c in cells:
        survivors: set[int] = set()
        options = list(state.cand[r][c])
        rejected: list[int] = []
        for h in options:
            trial = state.clone()
            trial_counts: dict[str, int] = {}
            if not _place(trial, r, c, h):
                rejected.append(h)
                continue
            if not _propagate_easy(trial, trial_counts, trace=None):
                rejected.append(h)
                continue
            survivors.add(h)
        if not survivors:
            if trace is not None:
                trace.append(f"shallow_case: contradiction at ({r},{c})")
            return -1
        before = set(state.cand[r][c])
        if survivors != before:
            state.cand[r][c] = survivors
            changes += 1
            if trace is not None:
                rej = "{" + ",".join(str(x) for x in sorted(rejected)) + "}"
                left = "{" + ",".join(str(x) for x in sorted(survivors)) + "}"
                trace.append(
                    f"shallow_case: at ({r},{c}) reject {rej} → candidates {left}"
                )
            if len(survivors) == 1 and state.grid[r, c] == 0:
                h = next(iter(survivors))
                if not _place(state, r, c, h):
                    return -1
                if trace is not None:
                    trace.append(f"shallow_case: place {h} at ({r},{c})")
    if changes:
        counts["shallow_case"] = counts.get("shallow_case", 0) + changes
    return changes


def _deep_search(
    state: _State,
    counts: dict[str, int],
    stats: dict[str, int],
    depth: int,
    trace: list[str] | None = None,
) -> bool:
    """Return True if a solution is found (assumes uniqueness already known)."""
    if not _propagate_easy(state, counts, trace=trace):
        return False
    while True:
        ch = _apply_shallow_cases(state, counts, trace=trace)
        if ch < 0:
            return False
        if ch == 0:
            break
        if not _propagate_easy(state, counts, trace=trace):
            return False

    if _is_solved(state):
        return True

    cell = _pick_branch_cell(state)
    if cell is None:
        return False
    r, c = cell
    options = sorted(state.cand[r][c])
    stats["nodes"] = stats.get("nodes", 0) + 1
    stats["max_depth"] = max(stats.get("max_depth", 0), depth + 1)
    counts["deep_search"] = counts.get("deep_search", 0) + 1
    if trace is not None:
        opts = "{" + ",".join(str(x) for x in options) + "}"
        trace.append(
            f"deep_search: branch depth={depth} at ({r},{c}) options {opts}"
        )

    for h in options:
        if trace is not None:
            trace.append(f"deep_search: try {h} at ({r},{c}) (depth {depth})")
        trial = state.clone()
        if not _place(trial, r, c, h):
            if trace is not None:
                trace.append(
                    f"deep_search: try {h} at ({r},{c}) failed immediately"
                )
            continue
        if _deep_search(trial, counts, stats, depth + 1, trace=trace):
            state.grid[:] = trial.grid
            state.cand = trial.cand
            if trace is not None:
                trace.append(
                    f"deep_search: accepted {h} at ({r},{c}) (depth {depth})"
                )
            return True
        if trace is not None:
            trace.append(
                f"deep_search: backtrack from {h} at ({r},{c}) (depth {depth})"
            )
    return False


def rate_puzzle(
    n: int,
    clues: dict[str, list[int]],
    *,
    collect_trace: bool = False,
) -> RatingResult:
    """
    Solve with the technique ladder and return a numeric difficulty score.

    Assumes the puzzle has exactly one solution (generator enforces this).
    Set ``collect_trace=True`` to fill ``RatingResult.trace`` with step details.
    """
    state = _empty_state(n, clues)
    counts: dict[str, int] = {}
    stats = {"nodes": 0, "max_depth": 0}
    trace: list[str] | None = [] if collect_trace else None

    if trace is not None:
        trace.append(f"start: empty {n}×{n} grid with given clues")

    if not _propagate_easy(state, counts, trace=trace):
        if trace is not None:
            trace.append("end: contradiction during easy propagation")
        return RatingResult(
            score=10_000.0,
            label="expert",
            technique_counts=counts,
            trace=trace or [],
            solved=False,
        )

    while not _is_solved(state):
        ch = _apply_shallow_cases(state, counts, trace=trace)
        if ch < 0:
            break
        if ch > 0:
            if not _propagate_easy(state, counts, trace=trace):
                break
            continue
        if not _deep_search(state, counts, stats, 0, trace=trace):
            break
        break

    solved = _is_solved(state)
    if trace is not None:
        if solved:
            trace.append("end: grid solved")
        else:
            trace.append("end: incomplete (rater failed to finish)")

    score = 0.0
    for name, weight in TECHNIQUE_WEIGHTS.items():
        score += weight * counts.get(name, 0)
    score += DEEP_NODE_WEIGHT * stats.get("nodes", 0)
    score += DEEP_DEPTH_WEIGHT * stats.get("max_depth", 0)

    return RatingResult(
        score=round(score, 2),
        label=score_to_label(score),
        technique_counts=counts,
        deep_nodes=stats.get("nodes", 0),
        deep_max_depth=stats.get("max_depth", 0),
        trace=trace or [],
        solved=solved,
    )


def format_rating_report(result: RatingResult) -> str:
    """Human-readable score breakdown + optional full trace."""
    lines: list[str] = []
    lines.append(f"solved:            {result.solved}")
    lines.append(f"difficulty_score:  {result.score}")
    lines.append(f"difficulty:        {result.label}")
    lines.append(f"deep_nodes:        {result.deep_nodes}")
    lines.append(f"deep_max_depth:    {result.deep_max_depth}")
    lines.append("technique_counts:")
    for name in TECHNIQUE_WEIGHTS:
        count = result.technique_counts.get(name, 0)
        if count:
            contrib = TECHNIQUE_WEIGHTS[name] * count
            lines.append(
                f"  {name:14} × {count:<4} (weight {TECHNIQUE_WEIGHTS[name]:g}) "
                f"→ {contrib:g}"
            )
    if result.deep_nodes:
        lines.append(
            f"  {'deep_nodes':14} × {result.deep_nodes:<4} "
            f"(weight {DEEP_NODE_WEIGHT:g}) → {DEEP_NODE_WEIGHT * result.deep_nodes:g}"
        )
    if result.deep_max_depth:
        lines.append(
            f"  {'deep_max_depth':14} × {result.deep_max_depth:<4} "
            f"(weight {DEEP_DEPTH_WEIGHT:g}) → {DEEP_DEPTH_WEIGHT * result.deep_max_depth:g}"
        )
    if result.trace:
        lines.append("")
        lines.append("trace:")
        for i, step in enumerate(result.trace, start=1):
            lines.append(f"  {i:4}. {step}")
    return "\n".join(lines)
