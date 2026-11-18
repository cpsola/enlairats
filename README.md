# Enlairats

<img src="2d_prints/graphics/cover_v2.png" alt="Enlairats cover" width="420">

**Enlairats** is a Catalan Modernista edition of the classic **Skyscrapers** (also known as Towers) logic puzzle: fill a grid with building heights so every border clue is satisfied.

This repository contains everything needed to create a complete, printable version of the game, including a 3D-printable board and pieces, 2D-printable (paper or cardstock) rules and game boards, and the software used to generate all these materials.

Enlairats is an original presentation built on the well-known genre of Skyscrapers/Towers mechanic.

**License:** [CC BY-NC 4.0](LICENSE) (non-commercial). Bundled fonts are under the SIL OFL — see [NOTICE](NOTICE).

## Contents

1. [What’s in the repo](#1-whats-in-the-repo)
2. [How to play Skyscrapers/Enlairats](#2-how-to-play-skyscrapersenlairats)
3. [How to print the game](#3-how-to-print-the-game)
4. [Software (CLI)](#4-software-cli)
5. [For developers](#5-for-developers)
6. [License and attribution](#6-license-and-attribution)

---

## 1. What’s in the repo

```text
enlairats/
├── skyscrapers/          # Python package: generate, play, rate, print PDFs
├── sample_boards/        # Sample 4×4 puzzles (JSON)
├── 2d_prints/
│   ├── graphics/         # Cover art, building art, OFL fonts
│   ├── rules/            # Catalan rules source + sample PDFs
│   └── boards/           # Sample printable board PDF
├── 3d_prints/            # 3D STLs, photos, print guide
├── scripts/              # Helpers (e.g. trim boards per difficulty)
├── LICENSE               # CC BY-NC 4.0
└── NOTICE                # Third-party font notices (OFL)
```
---

## 2. How to play Skyscrapers/Enlairats

The classical (abstract) Skyscrapers game works as follows.

The **goal** is to fill an `N×N` grid with building heights so that every clue around the border is satisfied.
- Each cell gets a height from **1** (shortest) to **N** (tallest).
- In every **row** and every **column**, each height appears **exactly once** (a Latin square of `1…N`).
- Numbers on the four borders tell you how many buildings are **visible** looking straight into that row or column from that side. A building is visible if it is **strictly taller** than every building in front of it. Empty clue slots give no information for that edge.

There is exactly one correct solution for each generated puzzle.

Enlairats brings this abstract puzzle to life: instead of entering numbers in a grid, players place Modernista building miniatures on a physical game board. For instructions on how to play Enlairats, refer to its game [rulebook](2d_prints/rules/sample_instructions.pdf).

---

## 3. How to print the game

### 3.1 2D prints (aka paper / cardboard)

The [rulebook](2d_prints/rules/sample_instructions_a4.pdf) and [sample puzzle boards](2d_prints/boards/sample_boards.pdf) ready to print can be found in the [2d_prints](2d_prints/) folder.

You can also use the accompanying Python code to generate new puzzle boards and regenerate the rulebook (see [Section 4](#4-software-cli)). The scripts allow you to customize the board size and other settings.

**Recommended print settings:** 100% scale, colour, cardstock 250–300 g/m², duplex, flip on the **long edge**, bind with a Chicago screw or ring (rulebook).

### 3.2 3D prints

STL files for buildings, board, clue tokens, and box are under `3d_prints/stl/`. See [`3d_prints/README.md`](3d_prints/README.md) for the full-game print table, settings, and box remix attribution.

---

## 4. Software (CLI)

The Python package in `skyscrapers/` is a command-line toolkit for the digital side of Enlairats. With it you can:

- **Generate** uniquely solvable Skyscrapers/Enlairats puzzles as JSON
- **Show**, **play**, and **rate** boards (ASCII view, desktop UI, difficulty trace)
- **Print** the Catalan rules booklet and Modernista board cards as PDFs

The subsections below cover setup and each command.

### 4.1 Setup

**Requirements:** Python 3.10+, NumPy, ReportLab (for PDF commands), Tkinter (for `play`). Fonts are bundled under `2d_prints/graphics/fonts/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Quick start

```bash
# Generate boards
python3 -m skyscrapers generate

# Show / play / rate a sample
python3 -m skyscrapers show sample_boards/<id>.json
python3 -m skyscrapers play --random
python3 -m skyscrapers rate sample_boards/<id>.json

# Printable PDFs
python3 -m skyscrapers print_rules --a4
python3 -m skyscrapers print_boards
```

Defaults write JSON to `./sample_boards` and PDFs under `./2d_prints/`.

### 4.3 `generate`

Creates uniquely solvable puzzle boards and writes each one as a JSON file (with clues, solution, and difficulty metadata).

```bash
python3 -m skyscrapers generate
python3 -m skyscrapers generate --size 4 --count 3 --clues 6-12 --output-dir ./sample_boards
python3 -m skyscrapers generate --count 2 --show
python3 -m skyscrapers generate --count 1 --show --solution
```

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--size` | `4` | Board size `N` |
| `--count` | `10` | Number of boards |
| `--clues` | `1-4N` | Clue-count interval `MIN-MAX` |
| `--max-attempts` | `1000` | Max attempts per board |
| `--output-dir` | `./sample_boards` | Output directory |
| `--show` | off | ASCII art after each write |
| `--solution` | off | With `--show`, fill the grid |

### 4.4 `show` / `play` / `rate`

Inspect an existing board in the terminal (`show`), solve it in a desktop window (`play`), or re-score it and print a full technique-ladder trace (`rate`).

```bash
python3 -m skyscrapers show sample_boards/<id>.json
python3 -m skyscrapers show sample_boards/<id>.json --solution
python3 -m skyscrapers play sample_boards/<id>.json
python3 -m skyscrapers play --random --output-dir ./sample_boards
python3 -m skyscrapers rate sample_boards/<id>.json
```

**Play window:** click a cell, type `1…N`, **Undo** / **Clear cell** / **Reset**. Delete/Backspace clears the selection.

### 4.5 `print_rules`

Builds the printable Enlairats rules booklet PDF from the Catalan rules text and art under `2d_prints/graphics/`.

```bash
python3 -m skyscrapers print_rules
python3 -m skyscrapers print_rules --a4
python3 -m skyscrapers print_rules --output 2d_prints/rules/sample_instructions.pdf
```

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--output` | `2d_prints/rules/sample_instructions.pdf` (or `…_a4.pdf` with `--a4`) | Output path |
| `--a4` | off | Impose all 6 pages on one portrait A4 (9×9 cm tiles); backs = logo |

With `--a4`, print **duplex, flip on the long edge**, then cut six **9×9 cm** cards.

### 4.6 `print_boards`

Builds a home-printable A4 PDF of Enlairats board cards (Modernista style): puzzle fronts plus mirrored solution backs for duplex printing. Only **4×4** boards are accepted.

```bash
python3 -m skyscrapers print_boards
python3 -m skyscrapers print_boards --input-dir ./sample_boards --output 2d_prints/boards/sample_boards.pdf
python3 -m skyscrapers print_boards --board-size 6 --difficulty easy --difficulty "Mestre artesà"
```

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--input-dir` | `./sample_boards` | Board JSON folder |
| `--output` | `./2d_prints/boards/sample_boards.pdf` | Output PDF |
| `--board-size` | `6` | Outer square card side (**cm**) |
| `--difficulty` | all | Filter (repeatable); English or Catalan labels |

| JSON `difficulty` | Printed label |
| ----------------- | ------------- |
| `easy` | Aprenent |
| `medium` | Oficial |
| `hard` | Mestre artesà |
| `expert` | Arquitecte |

### 4.7 Board JSON

Each generated puzzle is stored as one JSON file under `sample_boards/`, named with the puzzle id.

```text
sample_boards/<id>.json
```

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

- `0` in a clue array = no clue on that edge.
- `id` = first 16 hex chars of SHA-256 over canonical `N` + clues.
- `difficulty` is derived from `difficulty_score`.

### 4.8 Trim boards per difficulty

Keeps a random sample of boards per difficulty level from `./sample_boards` and moves the rest to `sample_boards/to_delete/` (gitignored). Asks for confirmation before moving.

```bash
scripts/keep_boards.sh 10 15 10 5
```

---

## 5. For developers

### 5.1 Package layout

```text
skyscrapers/
  __main__.py      # python -m skyscrapers
  cli.py           # argparse CLI
  display.py       # ASCII board rendering
  play.py          # Tkinter play UI
  boards_pdf.py    # printable board cards
  rules_pdf.py     # rules booklet PDF
  latin.py         # random Latin-square solutions
  visibility.py    # visible-count + clues-from-grid
  clues.py         # clue slots, counting, encoding
  solver.py        # backtracking; uniqueness
  generator.py     # fill → reduce clues → validate → rate
  rater.py         # technique-ladder difficulty
  serialize.py     # puzzle id + JSON write
```

### 5.2 Generation pipeline

1. **Solution-first** — random Latin square of size `N`.
2. **Full clues** — all `4N` border visibility counts.
3. **Target clue count** — pick `k` in `[lo, hi]` (default `1…4N`).
4. **Removal** — drop clues while the puzzle stays **uniquely** solvable; stop at `k` when possible.
5. **Accept** if final clue count is in `[lo, hi]`; else retry.
6. **Rate** with the technique ladder; write JSON.

Uniqueness is mandatory (solver limit 2).

### 5.3 Architecture choices

| Decision | Rationale |
| -------- | --------- |
| Solution-first + clue removal | Real solution; uniqueness easier than clue-first |
| Uniform random clue removal | No positional bias |
| Nearest count inside interval | Exact `k` not always reachable |
| Separate solver vs rater | Validity vs human-like hardness |
| Stdlib + NumPy | Simple grids for v1 |
| Hash id from `N` + clues | Stable playable identity |
| Per-board seed | Reproducible singles; batches stay non-deterministic |

### 5.4 Difficulty model (`rater.py`)

Techniques always run easy → hard. After any progress, the rater **restarts from `direct`**.

1. **`direct`** — edge facts (clue `1` → place `N`; clue `N` → line `1…N`).
2. **`latin`** — naked / hidden singles.
3. **`visibility`** — tallest-building bounds.
4. **`line_enum`** — permute remaining Latin lines vs end clues.
5. **`shallow_case`** — depth-1 case split on 2–3 candidates.
6. **`deep_search`** — branch until the unique solution.

```text
score = Σ (weight[technique] × count[technique])
      + 3.0 × deep_search_nodes
      + 8.0 × deep_search_max_depth
```

| Technique | Weight |
| --------- | ------ |
| `direct` | 1.0 |
| `latin` | 2.0 |
| `visibility` | 4.0 |
| `line_enum` | 8.0 |
| `shallow_case` | 20.0 |
| `deep_search` | 40.0 |

| Label | Score |
| ----- | ----- |
| easy | < 25 |
| medium | < 70 |
| hard | < 150 |
| expert | ≥ 150 |

Coordinates in the `rate` trace are `(row, col)` with `(0,0)` at the top-left.

---

## 6. License and attribution

- **Project** (code, art, rules, sample boards, PDFs, STLs, photos): [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — see [`LICENSE`](LICENSE).
- **Fonts** (Cormorant Garamond, Cinzel): SIL Open Font License 1.1 — see [`NOTICE`](NOTICE) and `2d_prints/graphics/fonts/`.

The 3D designs (board, buildings, clue tokens, and related STLs) are by [cpsola](https://github.com/cpsola). The box is remixed from [Magnetic Box (Parametric)](https://www.printables.com/model/643648-magnetic-box-parametric) (CC BY 4.0). The 2D art, rules materials, and software were created by [cpsola](https://github.com/cpsola) with Cursor as AI coding assistant.

Please credit **Enlairats** and link back to this repository when you share non-commercial derivatives.
