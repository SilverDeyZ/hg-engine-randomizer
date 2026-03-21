#!/usr/bin/env python3
"""Scale eggcycles values in armips/data/mondata.s by dividing them by a scalar."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_MONDATA = Path("armips/data/mondata.s")
DEFAULT_BACKUP = Path("bak/mondata.s.bak")
DEFAULT_SCALAR = 1.0
MIN_EGGCYCLES = 1
MAX_EGGCYCLES = 120

EGGCYCLES_RE = re.compile(
    r"^(?P<indent>\s*)eggcycles\s+(?P<value>-?\d+)(?P<suffix>\s*(?://.*)?)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Divide eggcycles values in armips/data/mondata.s by a scalar."
    )
    parser.add_argument(
        "--scalar",
        type=float,
        default=None,
        help="Scalar used to divide eggcycles values. Defaults to 1.0.",
    )
    parser.add_argument(
        "--mondata",
        type=Path,
        default=DEFAULT_MONDATA,
        help=f"Mondata file to edit (default: {DEFAULT_MONDATA}).",
    )
    return parser.parse_args()


def ask_scalar(label: str, default: float) -> float:
    while True:
        raw = input(f"  - {label:<16} [{default:.1f}] : ").strip()
        if not raw:
            return default
        try:
            value = float(raw)
        except ValueError:
            print(f"    Invalid value. Please enter a number for {label}.")
            continue
        if value <= 0:
            print(f"    Invalid value. {label} must be greater than 0.")
            continue
        return value


def resolve_scalar(args: argparse.Namespace) -> float:
    if args.scalar is None:
        return ask_scalar("Eggcycles Scalar", DEFAULT_SCALAR)
    if args.scalar <= 0:
        raise ValueError("Eggcycles scalar must be greater than 0.")
    return args.scalar


def clamp_eggcycles(value: int) -> int:
    return max(MIN_EGGCYCLES, min(MAX_EGGCYCLES, value))


def scale_eggcycles(text: str, scalar: float) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = EGGCYCLES_RE.match(body)

        if not match:
            updated_lines.append(line)
            continue

        original_value = int(match.group("value"))
        scaled_value = clamp_eggcycles(int(round(original_value / scalar)))
        updated_body = (
            f"{match.group('indent')}eggcycles {scaled_value}"
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
    print(" Eggcycles Manager")
    print("========================================")
    print("Divide eggcycles values by a scalar.")
    print("One eggcycle equals 255 steps.\n")

    args = parse_args()
    scalar = resolve_scalar(args)

    original = args.mondata.read_text(encoding="utf-8")
    updated, changed = scale_eggcycles(original, scalar)

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.mondata.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Mondata file    : {args.mondata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
