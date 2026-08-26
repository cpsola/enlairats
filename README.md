# Skyscrapers board generator (and basic player)

Python package that generates **Skyscrapers** (also known as Towers) logic puzzles: unique `N×N` boards with border clues, a difficulty score, and JSON export.

---

## 1. For players

### 1.1 Goal

Fill an `N×N` grid with building heights so that every clue around the border is satisfied. There is exactly one correct solution for each generated puzzle.

### 1.2 What you place

- Each cell gets a height from **1** (shortest) to **N** (tallest).
- In every **row**, each height appears **exactly once**.
- In every **column**, each height appears **exactly once**.

So the grid is a Latin square of symbols `1…N`.

### 1.3 What the clues mean

Numbers on the four borders tell you how many buildings are **visible** when looking straight into that row or column from that side.

- You look along the line toward the opposite edge.
- A building is visible if it is **strictly taller** than every building in front of it.
- Shorter buildings behind a taller one are hidden.

Empty clue slots (no number / `0` in the JSON) give no information for that edge.

---
## 2. For users

### 2.1 Requirements

- Python 3.10+
- NumPy
- ReportLab (for `print`)
- Tkinter (stdlib; needed for `play`)
- Bundled fonts in `graphics/fonts/` (OFL)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 Generate boards

Run from the project root:

```bash
python3 -m skyscrapers generate
```

Defaults: `--size 4`, `--count 10`, clues `1-4N`, `--max-attempts 1000`, `--output-dir ./boards`.

#### 2.3 Examples

```bash
# Explicit defaults (same as bare `generate`)
python3 -m skyscrapers generate --size 4 --count 10

# Three 4×4 puzzles, clue count between 6 and 12
python3 -m skyscrapers generate --size 4 --count 3 --clues 6-12 --output-dir ./boards

# One 5×5 puzzle (clue interval defaults to 1..4N)
python3 -m skyscrapers generate --size 5 --count 1

# Allow more retries if generation fails often
python3 -m skyscrapers generate --size 6 --count 2 --clues 12-20 --max-attempts 2000

# Generate and print each board (playable view)
python3 -m skyscrapers generate --count 2 --show

# Generate and print each board with the solution filled in
python3 -m skyscrapers generate --count 1 --show --solution

# Show an existing board JSON
python3 -m skyscrapers show boards/<id>.json
python3 -m skyscrapers show boards/<id>.json --solution

# Play a specific board (desktop window)
python3 -m skyscrapers play boards/<id>.json

# Play a random board from ./boards
python3 -m skyscrapers play --random
python3 -m skyscrapers play --random --output-dir ./boards

# Inspect rater technique trace for a board
python3 -m skyscrapers rate boards/<id>.json

# Printable Modernista PDF (all boards in ./boards)
python3 -m skyscrapers print
python3 -m skyscrapers print --board-size 5 --difficulty Oficial --output partida.pdf
```

#### 2.4 CLI options (`generate`)


| Option           | Required | Default    | Description                                               |
| ---------------- | -------- | ---------- | --------------------------------------------------------- |
| `--size`         | no       | `4`        | Board size `N`                                            |
| `--count`        | no       | `10`       | Number of boards to generate                              |
| `--clues`        | no       | `1-4N`     | Inclusive clue-count interval `MIN-MAX`                   |
| `--max-attempts` | no       | `1000`     | Max generation attempts **per board**                     |
| `--output-dir`   | no       | `./boards` | Directory for output JSON files                           |
| `--show`         | no       | off        | Print each board as ASCII art to stdout after writing it  |
| `--solution`     | no       | off        | With `--show`, fill cells with the solution               |


#### 2.5 CLI (`show`)

Print one existing board JSON as a classic bordered ASCII grid (stdout only):

```bash
python3 -m skyscrapers show path/to/board.json
python3 -m skyscrapers show path/to/board.json --solution
```

| Option       | Required | Default | Description                                      |
| ------------ | -------- | ------- | ------------------------------------------------ |
| `path`       | yes      | —       | Path to a board JSON file                        |
| `--solution` | no       | off     | Fill cells with the solution (default: playable) |

Metadata printed with the grid: `id`, `N`, `clue_count`, `difficulty_score`, `difficulty` (label from score), `seed`, and `view`. Colors are used when stdout is a terminal.

#### 2.6 CLI (`play`)

Open a desktop window (Tkinter) to play one board. Clues are shown; the grid starts empty. When every cell is filled, the grid is checked automatically against the stored solution.

```bash
python3 -m skyscrapers play path/to/board.json
python3 -m skyscrapers play --random
python3 -m skyscrapers play --random --output-dir ./boards
```

| Option         | Required | Default    | Description                                      |
| -------------- | -------- | ---------- | ------------------------------------------------ |
| `path`         | one of\* | —          | Path to a board JSON file                        |
| `--random`     | one of\* | off        | Pick a random `*.json` from `--output-dir`       |
| `--output-dir` | no       | `./boards` | Directory used with `--random`                   |

\*Provide either `path` or `--random` (not both).

**In the window:** click a cell, type `1…N` to place a height. Buttons: **Undo**, **Clear cell**, **Reset**. Delete/Backspace also clears the selected cell. Close the window to exit. Metadata (id, N, clue count, score/label, seed, file) is shown above the grid.

Exit codes: `0` on normal close (window close, or after solving); `1` on startup errors (missing file, invalid JSON, empty directory, no display).

#### 2.7 CLI (`rate`)

Re-run the technique-ladder rater on a board JSON and print the score breakdown plus a **full step-by-step trace** (placements, candidate eliminations, shallow cases, deep-search branches).

```bash
python3 -m skyscrapers rate boards/<id>.json
```

| Option | Required | Default | Description               |
| ------ | -------- | ------- | ------------------------- |
| `path` | yes      | —       | Path to a board JSON file |

Coordinates in the trace are 0-based `(row, col)`.

#### 2.8 CLI (`print`)

Build a home-printable **A4 PDF** of boards for the physical game **Enlairats** (Catalan Modernista / Amatller-inspired). Multiple boards per page; packing adapts to `--board-size`. Portrait or landscape is chosen automatically to fit more cards.

```bash
python3 -m skyscrapers print
python3 -m skyscrapers print --input-dir ./boards --output enlairats-boards.pdf
python3 -m skyscrapers print --board-size 6 --difficulty easy --difficulty "Mestre artesà"
```

| Option         | Required | Default                 | Description |
| -------------- | -------- | ----------------------- | ----------- |
| `--input-dir`  | no       | `./boards`              | Folder of board JSON files (sorted by filename) |
| `--output`     | no       | `./enlairats-boards.pdf` | Output PDF path |
| `--board-size` | no       | `6`                     | Outer **square card** side length in **cm** |
| `--difficulty` | no       | all                     | Filter (repeatable). English `easy/medium/hard/expert` or Catalan `Aprenent/Oficial/Mestre artesà/Arquitecte` |

Each card shows: clues + empty grid (no solution), Catalan level name with a distinct floral motif (4–7 petals by level), and a small centred id. Only **4×4** boards are accepted; any other size aborts the run.

Printed level names:

| JSON `difficulty` | Printed label   |
| ----------------- | --------------- |
| easy              | Aprenent        |
| medium            | Oficial         |
| hard              | Mestre artesà   |
| expert            | Arquitecte      |

Requires ReportLab and the bundled fonts under `graphics/fonts/` (see `requirements.txt`; use the project venv).

### 2.9 Output

Each board is written as its own JSON file, named with the puzzle id:

```text
boards/<id>.json
```

The CLI also prints a human-readable difficulty label (`easy` / `medium` / `hard` / `expert`) derived from the numeric score.

Example fields in each file:

```json
{
  "id": "57d4d1d3146b0ff6",
  "N": 4,
  "clues": {
    "top": [1, 2, 3, 0],
    "bottom": [3, 3, 1, 2],
    "left": [1, 2, 2, 2],
    "right": [0, 0, 0, 2]
  },
  "solution": [[4, 3, 2, 1], [1, 4, 3, 2], [3, 2, 1, 4], [2, 1, 4, 3]],
  "clue_count": 12,
  "difficulty_score": 50.0,
  "difficulty": "medium",
  "seed": 3930816346819978606
}
```

- `0` in a clue array means **no clue** on that edge cell.
- `id` is the first 16 hex characters of SHA-256 over a canonical encoding of `N` + clues.
- `difficulty` is the label derived from `difficulty_score` (`easy` / `medium` / `hard` / `expert`).
- `seed` is the RNG seed used to build that board (solution + clue removal).

---

## 3. For developers

### 3.1 Package layout

```text
skyscrapers/
  __main__.py      # python -m skyscrapers
  cli.py           # argparse CLI
  display.py       # ASCII board rendering (show / generate --show)
  play.py          # Tkinter play UI
  print_pdf.py     # Modernista printable PDF (print)
  latin.py         # random Latin-square solutions
  visibility.py    # visible-count + clues-from-grid
  clues.py         # clue slots, counting, canonical encoding
  solver.py        # backtracking; counts solutions up to a limit
  generator.py     # fill → reduce clues → validate → rate
  rater.py         # technique-ladder difficulty scoring
  serialize.py     # puzzle id + JSON write
graphics/
  cover.png        # Enlairats cover art (style reference)
  fonts/           # OFL fonts for PDF printing
```

### 3.2 Generation pipeline

1. **Solution-first** — generate a random Latin square of size `N` (this is the intended solution).
2. **Full clues** — compute all `4N` border visibility counts from that grid.
3. **Target clue count** — pick `k` uniformly in `[lo, hi]` (default `1…4N`).
4. **Removal-from-full** — drop clues in random order while the puzzle stays **uniquely** solvable; stop at `k` or when no further removal is possible.
5. **Interval acceptance** — keep the board if the final clue count lies in `[lo, hi]` (nearest achievable to `k` inside the interval). Otherwise retry (up to `--max-attempts` per board).
6. **Rate** — run the technique-ladder rater; store `difficulty_score` and `difficulty` (label) in JSON.
7. **Serialize** — one JSON file per board, filename = puzzle id.

Uniqueness is mandatory: every published clue set has exactly one solution. The checker searches until it finds a second solution (limit 2) and rejects if it does.

### 3.3 Architecture choices


| Decision                           | Rationale                                                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------------------- |
| Solution-first + clue removal      | Always has a real solution; uniqueness is easier to control than clue-first generation    |
| Uniform random clue removal        | Matches the “uniform random kept slots” requirement without biasing positions             |
| Nearest count inside interval      | Exact `k` is not always reachable; retry only when the result falls outside `[lo, hi]`    |
| Separate solver vs rater           | Solver proves uniqueness; rater estimates *human-like* hardness without changing validity |
| Stdlib + NumPy                     | Grids stay simple (`ndarray`); no heavier constraint libraries required for v1            |
| Hash id from `N` + clues only      | Stable identity for the playable puzzle; solution is derived/unique from clues            |
| Per-board seed, no global `--seed` | Reproducible single boards via metadata; batch runs stay non-deterministic by design      |
| Slow OK                            | Correct uniqueness and readable technique rating preferred over micro-optimizations       |


### 3.4 Difficulty model (`rater.py`)

The rater does **not** decide uniqueness (the solver already did). It re-solves the puzzle with a fixed ladder of human-like techniques and scores how much work that took.

Techniques run from easy to hard. After any progress, the rater restarts from the top of the ladder. Only when easy steps stall does it move on.

1. **Direct clue placements** — Immediate edge facts: clue `1` places `N` on the near cell; clue `N` forces the strictly increasing line `1…N` from that edge.
2. **Latin singles** — Row/column uniqueness: a cell with one candidate (naked single), or a height that fits in only one cell of a row/column (hidden single).
3. **Visibility pruning** — Drop candidates that break tallest-building bounds (e.g. where `N` may sit given a near/far clue).
4. **Line enumeration** — For each row/column, list Latin permutations still allowed by cell candidates and both end clues; intersect to shrink candidates.
5. **Shallow case reasoning** — For a cell with 2–3 options, try each with easy propagation; eliminate options that contradict (depth-1 “what if”).
6. **Deep search** — Branch on a remaining cell and recurse until the unique solution is found.

Each successful application of a technique increments a counter. The numeric score is:

```text
score = Σ (weight[technique] × count[technique])
      + 3.0 × deep_search_nodes
      + 8.0 × deep_search_max_depth
```

| Technique       | Weight |
| --------------- | ------ |
| `direct`        | 1.0    |
| `latin`         | 2.0    |
| `visibility`    | 4.0    |
| `line_enum`     | 8.0    |
| `shallow_case`  | 20.0   |
| `deep_search`   | 40.0   |

Harder steps cost more per use; deep search also adds cost for how wide/deep the branching was. JSON stores both `difficulty_score` and `difficulty` (label).

| Label  | Score |
| ------ | ----- |
| easy   | < 25  |
| medium | < 70  |
| hard   | < 150 |
| expert | ≥ 150 |

Weights and thresholds are module-level constants in `rater.py` (intended to be tuned later).


