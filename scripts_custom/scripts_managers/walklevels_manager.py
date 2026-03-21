#!/usr/bin/env python3
"""Scale encounter level values in armips/data/encounters.s."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ENCOUNTERS = Path("armips/data/encounters.s")
DEFAULT_BACKUP = Path("bak/encounters.s.bak")
DEFAULT_SCALAR = 1.0
MIN_SCALAR = 0.1
MAX_SCALAR = 50.0
MIN_LEVEL = 1
MAX_LEVEL = 100

WALKLEVELS_RE = re.compile(
    r"^(?P<indent>\s*)walklevels\s+(?P<values>\d+(?:\s*,\s*\d+){11})(?P<suffix>\s*(?://.*)?)$"
)
ENCOUNTER_RE = re.compile(
    r"^(?P<indent>\s*encounter\s+SPECIES_[A-Z0-9_]+\s*,\s*)(?P<min>\d+)\s*,\s*(?P<max>\d+)(?P<suffix>\s*(?://.*)?)$"
)
SECTION_RE = re.compile(r"^\s*//\s*(?P<section>.+?)\s*$")

LEVEL_SECTIONS = {
    "surf encounters",
    "rock smash encounters",
    "old rod encounters",
    "good rod encounters",
    "super rod encounters",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scale walklevels and water/rod/rock smash encounter levels in armips/data/encounters.s."
    )
    parser.add_argument(
        "--scalar",
        type=float,
        default=None,
        help="Scalar used to multiply encounter levels. Defaults to 1.0.",
    )
    parser.add_argument(
        "--encounters",
        type=Path,
        default=DEFAULT_ENCOUNTERS,
        help=f"Encounter file to edit (default: {DEFAULT_ENCOUNTERS}).",
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
        if value < MIN_SCALAR or value > MAX_SCALAR:
            print(f"    Invalid value. {label} must be between {MIN_SCALAR:.1f} and {MAX_SCALAR:.1f}.")
            continue
        return value


def resolve_scalar(args: argparse.Namespace) -> float:
    if args.scalar is None:
        return ask_scalar("Levels Scalar", DEFAULT_SCALAR)
    return max(MIN_SCALAR, min(MAX_SCALAR, args.scalar))


def clamp_level(value: int) -> int:
    return max(MIN_LEVEL, min(MAX_LEVEL, value))


def scale_level(value: int, scalar: float) -> int:
    if value == 0:
        return 0
    return clamp_level(int(round(value * scalar)))


def scale_levels(text: str, scalar: float) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []
    current_section: str | None = None

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line

        section_match = SECTION_RE.match(body)
        if section_match:
            current_section = section_match.group("section").strip().lower()
            updated_lines.append(line)
            continue

        walklevels_match = WALKLEVELS_RE.match(body)
        if walklevels_match:
            values = [int(part.strip()) for part in walklevels_match.group("values").split(",")]
            scaled_values = [str(scale_level(value, scalar)) for value in values]
            updated_body = (
                f"{walklevels_match.group('indent')}walklevels {', '.join(scaled_values)}"
                f"{walklevels_match.group('suffix')}"
            )
            if updated_body != body:
                changed += 1
            updated_lines.append(updated_body + newline)
            current_section = None
            continue

        encounter_match = ENCOUNTER_RE.match(body)
        if encounter_match and current_section in LEVEL_SECTIONS:
            min_level = scale_level(int(encounter_match.group("min")), scalar)
            max_level = scale_level(int(encounter_match.group("max")), scalar)
            updated_body = (
                f"{encounter_match.group('indent')}{min_level}, {max_level}"
                f"{encounter_match.group('suffix')}"
            )
            if updated_body != body:
                changed += 1
            updated_lines.append(updated_body + newline)
            continue

        updated_lines.append(line)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Walklevels Manager")
    print("========================================")
    print("Multiply walk and water encounter levels by a scalar.\n")

    args = parse_args()
    scalar = resolve_scalar(args)

    original = args.encounters.read_text(encoding="utf-8")
    updated, changed = scale_levels(original, scalar)

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.encounters.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Encounters file : {args.encounters}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
