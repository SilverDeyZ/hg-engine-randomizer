#!/usr/bin/env python3
"""Scale trainer Pokemon levels in armips/data/trainers/trainers.s."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_TRAINERS = Path("armips/data/trainers/trainers.s")
DEFAULT_BACKUP = Path("bak/trainers.s.bak")
DEFAULT_SCALAR = 1.0
MIN_LEVEL = 1
MAX_LEVEL = 100

LEVEL_RE = re.compile(
    r"^(?P<indent>\s*)level\s+(?P<value>-?\d+)(?P<suffix>\s*(?://.*)?)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multiply trainer Pokemon levels in armips/data/trainers/trainers.s by a scalar."
    )
    parser.add_argument(
        "--scalar",
        type=float,
        default=None,
        help="Scalar used to multiply trainer Pokemon levels. Defaults to 1.0.",
    )
    parser.add_argument(
        "--trainers",
        type=Path,
        default=DEFAULT_TRAINERS,
        help=f"Trainer file to edit (default: {DEFAULT_TRAINERS}).",
    )
    return parser.parse_args()


def ask_scalar(label: str, default: float) -> float | None:
    while True:
        raw = input(f"  - {label:<16} [{default:.1f}] : ").strip()
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            print(f"    Invalid value. Please enter a number for {label}.")


def resolve_scalar(args: argparse.Namespace) -> float | None:
    return args.scalar if args.scalar is not None else ask_scalar("Levels Scalar", DEFAULT_SCALAR)


def clamp_level(value: int) -> int:
    return max(MIN_LEVEL, min(MAX_LEVEL, value))


def scale_levels(text: str, scalar: float) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = LEVEL_RE.match(body)

        if not match:
            updated_lines.append(line)
            continue

        original_value = int(match.group("value"))
        if original_value == 0:
            updated_lines.append(line)
            continue

        scaled_value = clamp_level(int(round(original_value * scalar)))
        updated_body = (
            f"{match.group('indent')}level {scaled_value}"
            f"{match.group('suffix')}"
        )
        if updated_body != body:
            changed += 1
        updated_lines.append(updated_body + newline)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Trainer Levels Multiplier")
    print("========================================")
    print("Multiply trainer Pokemon levels by a scalar.\n")

    args = parse_args()
    scalar = resolve_scalar(args)
    if scalar is None:
        print("No changes requested.")
        return 0

    original = args.trainers.read_text(encoding="utf-8")
    updated, changed = scale_levels(original, scalar)

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.trainers.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Trainers file   : {args.trainers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
