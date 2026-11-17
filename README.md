# Enlairats

**Enlairats** is a Catalan Modernista edition of the classic **Skyscrapers** (also known as **Towers**) logic puzzle: fill a grid with building heights so every border clue is satisfied.

This repository is the themed digital + physical edition — puzzle generator, printable paper cards, rules, artwork, and (soon) 3D-printable game pieces. It is **not** a claim to have invented the underlying Skyscrapers/Towers mechanic; Enlairats is an original presentation and physical product built on that well-known genre.

**Rules text** is in Catalan (`paper_prints/rules/instruccions.md`). This README is in English.

**License:** [CC BY-NC 4.0](LICENSE) (non-commercial). Bundled fonts are under the SIL OFL — see [NOTICE](NOTICE).

## Contents

1. [What’s in the repo](#1-whats-in-the-repo)
2. [Play the puzzle](#2-play-the-puzzle)
3. [Build the physical game](#3-build-the-physical-game)
4. [Quick start (software)](#4-quick-start-software)
5. [CLI reference](#5-cli-reference)
6. [For developers](#6-for-developers)
7. [License and attribution](#7-license-and-attribution)

---

## 1. What’s in the repo

```text
enlairats/
├── skyscrapers/          # Python package: generate, play, rate, print PDFs
├── sample_boards/        # Sample 4×4 puzzles (JSON)
├── paper_prints/
│   ├── graphics/         # Cover art, building art, OFL fonts
│   ├── rules/            # Catalan rules source + sample PDFs
│   └── boards/           # Sample printable board PDF
├── 3d_prints/            # 3D STLs, photos, print guide (STLs coming soon)
├── scripts/              # Helpers (e.g. trim boards per difficulty)
├── LICENSE               # CC BY-NC 4.0
└── NOTICE                # Third-party font notices (OFL)
```

| Path | Contents |
| ---- | -------- |
| `sample_boards/*.json` | Sample puzzles (12 per difficulty: easy / medium / hard / expert) |
| `paper_prints/rules/sample_instructions.pdf` | Rules booklet, **10×10 cm** pages |
| `paper_prints/rules/sample_instructions_a4.pdf` | Home print: six **9×9 cm** cards on one A4 (duplex) |
| `paper_prints/boards/sample_boards.pdf` | Board cards (default **6×6 cm**) with solution backs |
| `3d_prints/` | 3D print project — see [`3d_prints/README.md`](3d_prints/README.md) |

---

## 2. Play the puzzle

### 2.1 Goal

Fill an `N×N` grid with building heights so that every clue around the border is satisfied. There is exactly one correct solution for each generated puzzle.

### 2.2 What you place

- Each cell gets a height from **1** (shortest) to **N** (tallest).
- In every **row** and every **column**, each height appears **exactly once** (a Latin square of `1…N`).

### 2.3 What the clues mean

Numbers on the four borders tell you how many buildings are **visible** looking straight into that row or column from that side.

- A building is visible if it is **strictly taller** than every building in front of it.
- Empty clue slots (`0` in JSON) give no information for that edge.

In the physical game you place Modernista building miniatures on a board and set numbered clue tokens around the border.

---

## 3. Build the physical game

### 3.1 Paper (print at home)

```bash
python3 -m skyscrapers print_rules --a4
python3 -m skyscrapers print_boards
```

Or use the sample PDFs already in `paper_prints/`.

**Common settings:** 100% scale, colour, cardstock **250–300 g/m²**, duplex, flip on the **long edge**.

| Component | Cut size | Notes |
| --------- | -------- | ----- |
| Rules (`--a4`) | **9×9 cm** | 2×3 on A4; logo on backs |
| Board cards | **6×6 cm** (default) | Override with `--board-size` |

Details: [Printing the physical paper game](#55-printing-the-physical-paper-game) below.

### 3.2 3D pieces

STL files for buildings, board, clue tokens, and box will live under `3d_prints/stl/`. See [`3d_prints/README.md`](3d_prints/README.md) (guide scaffolded; files pending).

---

## 4. Quick start (software)

**Requirements:** Python 3.10+, NumPy, ReportLab (for PDF commands), Tkinter (for `play`). Fonts are bundled under `paper_prints/graphics/fonts/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

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

Defaults write JSON to `./sample_boards` and PDFs under `./paper_prints/`.

---

## 5. CLI reference

### 5.1 `generate`

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

### 5.2 `show` / `play` / `rate`

```bash
python3 -m skyscrapers show sample_boards/<id>.json
python3 -m skyscrapers show sample_boards/<id>.json --solution
python3 -m skyscrapers play sample_boards/<id>.json
python3 -m skyscrapers play --random --output-dir ./sample_boards
python3 -m skyscrapers rate sample_boards/<id>.json
```

**Play window:** click a cell, type `1…N`, **Undo** / **Clear cell** / **Reset**. Delete/Backspace clears the selection.

**Rate:** re-runs the technique-ladder rater and prints a full step-by-step trace.

### 5.3 `print_rules`

Builds the rules booklet from Catalan copy and art under `paper_prints/graphics/`.

```bash
python3 -m skyscrapers print_rules
python3 -m skyscrapers print_rules --a4
python3 -m skyscrapers print_rules --output paper_prints/rules/sample_instructions.pdf
```

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--output` | `paper_prints/rules/sample_instructions.pdf` (or `…_a4.pdf` with `--a4`) | Output path |
| `--a4` | off | Impose all 6 pages on one portrait A4 (9×9 cm tiles); backs = logo |

With `--a4`, print **duplex, flip on the long edge**, then cut six **9×9 cm** cards.

### 5.4 `print_boards`

Home-printable A4 of Enlairats board cards (Modernista / Amatller-inspired). Fronts + mirrored solution backs for duplex. Only **4×4** boards are accepted.

```bash
python3 -m skyscrapers print_boards
python3 -m skyscrapers print_boards --input-dir ./sample_boards --output paper_prints/boards/sample_boards.pdf
python3 -m skyscrapers print_boards --board-size 6 --difficulty easy --difficulty "Mestre artesà"
```

| Option | Default | Meaning |
| ------ | ------- | ------- |
| `--input-dir` | `./sample_boards` | Board JSON folder |
| `--output` | `./paper_prints/boards/sample_boards.pdf` | Output PDF |
| `--board-size` | `6` | Outer square card side (**cm**) |
| `--difficulty` | all | Filter (repeatable); English or Catalan labels |

| JSON `difficulty` | Printed label |
| ----------------- | ------------- |
| `easy` | Aprenent |
| `medium` | Oficial |
| `hard` | Mestre artesà |
| `expert` | Arquitecte |

### 5.5 Printing the physical paper game

```bash
python3 -m skyscrapers print_rules --a4
python3 -m skyscrapers print_boards
```

**Rules (`--a4`):** duplex, portrait, long-edge flip → cut **9×9 cm**. Optional: rounded corners; bind with a Chicago screw, stitch, or ring.

Without `--a4`: six separate **10×10 cm** pages (`sample_instructions.pdf`) — front only.

**Boards:** duplex, long-edge flip → cut **6 cm** squares (default). Test one sheet first.

Checklist:

- [ ] 100% scale
- [ ] Rules (`--a4`): duplex, long-edge flip; cut **9×9 cm**
- [ ] Boards: duplex, long-edge flip; cut **6 cm**
- [ ] Cardstock ≥250 g/m²
- [ ] Test sheet before a full run

### 5.6 Board JSON

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

### 5.7 Trim boards per difficulty

```bash
scripts/keep_boards.sh 10 15 10 5
```

Keeps a random sample per level from `./sample_boards`; moves the rest to `sample_boards/to_delete/` (gitignored). Asks for confirmation before moving.

---

## 6. For developers

### 6.1 Package layout

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

### 6.2 Generation pipeline

1. **Solution-first** — random Latin square of size `N`.
2. **Full clues** — all `4N` border visibility counts.
3. **Target clue count** — pick `k` in `[lo, hi]` (default `1…4N`).
4. **Removal** — drop clues while the puzzle stays **uniquely** solvable; stop at `k` when possible.
5. **Accept** if final clue count is in `[lo, hi]`; else retry.
6. **Rate** with the technique ladder; write JSON.

Uniqueness is mandatory (solver limit 2).

### 6.3 Architecture choices

| Decision | Rationale |
| -------- | --------- |
| Solution-first + clue removal | Real solution; uniqueness easier than clue-first |
| Uniform random clue removal | No positional bias |
| Nearest count inside interval | Exact `k` not always reachable |
| Separate solver vs rater | Validity vs human-like hardness |
| Stdlib + NumPy | Simple grids for v1 |
| Hash id from `N` + clues | Stable playable identity |
| Per-board seed | Reproducible singles; batches stay non-deterministic |

### 6.4 Difficulty model (`rater.py`)

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

## 7. License and attribution

- **Project** (code, art, rules, sample boards, PDFs, STLs, photos): [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — see [`LICENSE`](LICENSE).
- **Fonts** (Cormorant Garamond, Cinzel): SIL Open Font License 1.1 — see [`NOTICE`](NOTICE) and `paper_prints/graphics/fonts/`.

Please credit **Enlairats** and link back to this repository when you share non-commercial derivatives.
