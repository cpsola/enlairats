"""Command-line interface for the Skyscrapers generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .clues import max_clues
from .display import load_board_json, print_board
from .generator import GenerationError, generate_many
from .serialize import write_board_json


def _parse_clues(value: str | None, n: int) -> tuple[int, int]:
    upper = max_clues(n)
    if value is None:
        return 1, upper
    text = value.strip()
    if "-" not in text:
        raise argparse.ArgumentTypeError(
            "clues must look like MIN-MAX, e.g. 8-12"
        )
    left, right = text.split("-", 1)
    try:
        lo, hi = int(left), int(right)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("clues bounds must be integers") from exc
    if lo < 1 or hi > upper or lo > hi:
        raise argparse.ArgumentTypeError(
            f"clues must satisfy 1 <= MIN <= MAX <= {upper} for N={n}"
        )
    return lo, hi


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skyscrapers",
        description="Generate Skyscrapers (Towers) logic puzzles.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate puzzle boards as JSON files")
    gen.add_argument(
        "--size",
        type=int,
        default=4,
        help="Board size N (default: 4)",
    )
    gen.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of boards to generate (default: 10)",
    )
    gen.add_argument(
        "--clues",
        type=str,
        default=None,
        help="Clue-count interval MIN-MAX (default: 1-4N)",
    )
    gen.add_argument(
        "--max-attempts",
        type=int,
        default=1000,
        help="Max generation attempts per board (default: 1000)",
    )
    gen.add_argument(
        "--output-dir",
        type=Path,
        default=Path("boards"),
        help="Directory for per-board JSON files (default: ./boards)",
    )
    gen.add_argument(
        "--show",
        action="store_true",
        help="Print each board as ASCII art after writing its JSON",
    )
    gen.add_argument(
        "--solution",
        action="store_true",
        help="With --show, fill the grid with the solution (default: playable view)",
    )

    show = sub.add_parser("show", help="Print an existing board JSON as ASCII art")
    show.add_argument(
        "path",
        type=Path,
        help="Path to a board JSON file",
    )
    show.add_argument(
        "--solution",
        action="store_true",
        help="Fill the grid with the solution (default: playable view)",
    )

    play = sub.add_parser("play", help="Play a board in a desktop window")
    play.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="Path to a board JSON file (required unless --random)",
    )
    play.add_argument(
        "--random",
        action="store_true",
        help="Pick a random board JSON from --output-dir",
    )
    play.add_argument(
        "--output-dir",
        type=Path,
        default=Path("boards"),
        help="Directory used with --random (default: ./boards)",
    )

    rate = sub.add_parser(
        "rate",
        help="Re-rate a board JSON and print the full rater technique trace",
    )
    rate.add_argument(
        "path",
        type=Path,
        help="Path to a board JSON file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        return _cmd_generate(args)
    if args.command == "show":
        return _cmd_show(args)
    if args.command == "play":
        return _cmd_play(args)
    if args.command == "rate":
        return _cmd_rate(args)
    parser.error(f"unknown command {args.command}")
    return 2


def _cmd_generate(args: argparse.Namespace) -> int:
    n = args.size
    if n < 1:
        print("error: --size must be >= 1", file=sys.stderr)
        return 2
    if args.count < 1:
        print("error: --count must be >= 1", file=sys.stderr)
        return 2
    if args.max_attempts < 1:
        print("error: --max-attempts must be >= 1", file=sys.stderr)
        return 2

    try:
        clue_lo, clue_hi = _parse_clues(args.clues, n)
    except argparse.ArgumentTypeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"Generating {args.count} board(s): N={n}, clues=[{clue_lo}, {clue_hi}], "
        f"max_attempts/board={args.max_attempts}"
    )

    try:
        results = generate_many(
            n=n,
            count=args.count,
            clue_lo=clue_lo,
            clue_hi=clue_hi,
            max_attempts=args.max_attempts,
        )
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for i, result in enumerate(results, start=1):
        path = write_board_json(result.board, args.output_dir)
        board = result.board
        print(
            f"[{i}/{args.count}] id={board['id']}  "
            f"clues={board['clue_count']}  "
            f"score={board['difficulty_score']}  "
            f"difficulty={board.get('difficulty', result.rating.label)}  "
            f"attempts={result.attempts_used}  "
            f"→ {path}"
        )
        if args.show:
            print()
            print_board(board, show_solution=args.solution)
            print()

    print(f"Done. Wrote {len(results)} file(s) to {args.output_dir.resolve()}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        board = load_board_json(args.path)
        print_board(board, show_solution=args.solution)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_play(args: argparse.Namespace) -> int:
    import tkinter as tk

    from .play import pick_random_board, run_play

    if args.random and args.path is not None:
        print("error: use either a board path or --random, not both", file=sys.stderr)
        return 1
    if not args.random and args.path is None:
        print(
            "error: provide a board JSON path, or pass --random",
            file=sys.stderr,
        )
        return 1

    try:
        path = pick_random_board(args.output_dir) if args.random else args.path
        assert path is not None
        print(f"Playing {path}")
        return run_play(path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except tk.TclError as exc:
        print(f"error: cannot open play window: {exc}", file=sys.stderr)
        return 1


def _cmd_rate(args: argparse.Namespace) -> int:
    from .rater import format_rating_report, rate_puzzle

    try:
        board = load_board_json(args.path)
        n = int(board["N"])
        result = rate_puzzle(n, board["clues"], collect_trace=True)
        print(f"file: {args.path}")
        print(f"id:   {board.get('id', '?')}")
        print(f"N:    {n}")
        print(f"stored_difficulty_score: {board.get('difficulty_score', '?')}")
        print(f"stored_difficulty:       {board.get('difficulty', '?')}")
        print()
        print(format_rating_report(result))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
