#!/usr/bin/env bash
# Keep a random sample of board JSON files per difficulty; move the rest aside.
#
# Usage:
#   scripts/keep_boards.sh <easy> <medium> <hard> <expert>
#
# Example:
#   scripts/keep_boards.sh 10 15 10 5
#
# Directory: ./boards (only top-level *.json). Excess boards go to boards/to_delete
# (created if needed; same basename overwrites). Confirmation before moving.

set -euo pipefail

DIR="./boards"
TRASH="$DIR/to_delete"
LEVELS=(easy medium hard expert)

usage() {
  cat <<'EOF'
Usage: scripts/keep_boards.sh <easy> <medium> <hard> <expert>

Keep that many boards per difficulty (chosen at random); move the rest to
boards/to_delete/ (created if needed; existing same-name files are overwritten).
If a level has fewer boards than requested, all are kept and a warning is printed.

Only ./boards/*.json at the top level are considered (not boards/to_delete/).
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 4 ]]; then
  usage >&2
  exit 1
fi

for arg in "$@"; do
  if ! [[ "$arg" =~ ^[0-9]+$ ]]; then
    echo "error: keep counts must be non-negative integers (got: $arg)" >&2
    exit 1
  fi
done

KEEP_easy=$1
KEEP_medium=$2
KEEP_hard=$3
KEEP_expert=$4

if [[ ! -d "$DIR" ]]; then
  echo "error: directory not found: $DIR" >&2
  exit 1
fi

shopt -s nullglob
mapfile -t ALL_JSON < <(printf '%s\n' "$DIR"/*.json | sort)
if [[ ${#ALL_JSON[@]} -eq 0 ]]; then
  echo "error: no *.json files in $DIR" >&2
  exit 1
fi

# difficulty → newline-separated paths
declare -A BY_LEVEL
for level in "${LEVELS[@]}"; do
  BY_LEVEL[$level]=""
done

while IFS=$'\t' read -r path difficulty; do
  case "$difficulty" in
    easy|medium|hard|expert)
      BY_LEVEL[$difficulty]+="${path}"$'\n'
      ;;
    *)
      echo "warning: skipping $path (unknown difficulty: ${difficulty:-empty})" >&2
      ;;
  esac
done < <(
  python3 - "$DIR" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
for path in sorted(root.glob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(f"{path}\t?", file=sys.stderr)
        continue
    print(f"{path}\t{data.get('difficulty', '')}")
PY
)

TO_MOVE=()
echo "Plan (directory: $DIR → $TRASH):"
echo

for level in "${LEVELS[@]}"; do
  keep_var="KEEP_${level}"
  keep=${!keep_var}
  mapfile -t files < <(printf '%s' "${BY_LEVEL[$level]}" | sed '/^$/d')
  total=${#files[@]}

  if [[ $total -eq 0 ]]; then
    echo "  $level: 0 boards — nothing to do"
    continue
  fi

  if [[ $total -le $keep ]]; then
    echo "  $level: keep all $total (requested $keep)"
    if [[ $total -lt $keep ]]; then
      echo "    warning: fewer boards than requested"
    fi
    continue
  fi

  drop=$((total - keep))
  mapfile -t doomed < <(printf '%s\n' "${files[@]}" | shuf -n "$drop")
  TO_MOVE+=("${doomed[@]}")
  echo "  $level: keep $keep of $total → move $drop"
done

echo
if [[ ${#TO_MOVE[@]} -eq 0 ]]; then
  echo "Nothing to move."
  exit 0
fi

echo "Will move ${#TO_MOVE[@]} file(s) to $TRASH/:"
printf '  %s\n' "${TO_MOVE[@]}"
echo
read -r -p "Proceed with move? [y/N] " answer
case "$answer" in
  y|Y|yes|YES) ;;
  *)
    echo "Aborted."
    exit 0
    ;;
esac

mkdir -p "$TRASH"
for path in "${TO_MOVE[@]}"; do
  mv -f -- "$path" "$TRASH/"
done

echo "Moved ${#TO_MOVE[@]} file(s) to $TRASH/."
