#!/usr/bin/env python3
"""Control walkrate values in armips/data/encounters.s."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ENCOUNTERS = Path("armips/data/encounters.s")
DEFAULT_BACKUP = Path("bak/encounters.s.bak")
DEFAULT_SCALAR = 1.0
MIN_SCALAR = 0.2
MAX_SCALAR = 2.0
MIN_WALKRATE = 1
MAX_WALKRATE = 50
WALKRATE_COMMENT_PREFIX = "walkrate original:"

WALKRATE_RE = re.compile(
    r"^(?P<indent>\s*)walkrate\s+(?P<value>-?\d+)(?P<suffix>\s*(?://.*)?)$"
)
COMMENT_RE = re.compile(
    rf"//\s*{re.escape(WALKRATE_COMMENT_PREFIX)}\s*(?P<value>-?\d+)\s*$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deactivate wild encounters or scale walkrate values in armips/data/encounters.s."
    )
    parser.add_argument(
        "--deactivate",
        choices=("YES", "NO", "yes", "no"),
        default=None,
        help="Use YES to set walkrate values to 0, or NO to scale them.",
    )
    parser.add_argument(
        "--scalar",
        type=float,
        default=None,
        help="Scalar used to multiply walkrate values when not deactivating. Defaults to 1.0.",
    )
    parser.add_argument(
        "--encounters",
        type=Path,
        default=DEFAULT_ENCOUNTERS,
        help=f"Encounter file to edit (default: {DEFAULT_ENCOUNTERS}).",
    )
    return parser.parse_args()


def ask_yes_no(label: str, default: str) -> str:
    while True:
        raw = input(f"  - {label:<26} [{default}] : ").strip()
        if not raw:
            return default
        value = raw.upper()
        if value in {"YES", "NO"}:
            return value
        print(f"    Invalid value. Please enter YES or NO for {label}.")


def ask_scalar(label: str, default: float) -> float:
    while True:
        raw = input(f"  - {label:<26} [{default:.1f}] : ").strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print(f"    Invalid value. Please enter a number for {label}.")


def resolve_options(args: argparse.Namespace) -> tuple[str, float]:
    deactivate = args.deactivate.upper() if args.deactivate is not None else ask_yes_no(
        "Deactivate wild encounters?", "NO"
    )
    if deactivate == "YES":
        return deactivate, DEFAULT_SCALAR

    scalar = args.scalar if args.scalar is not None else ask_scalar("Walkrate Scalar", DEFAULT_SCALAR)
    scalar = round(scalar, 1)
    scalar = max(MIN_SCALAR, min(MAX_SCALAR, scalar))
    return deactivate, scalar


def strip_comment(suffix: str) -> str:
    comment_match = COMMENT_RE.search(suffix)
    if comment_match:
        return suffix[: comment_match.start()].rstrip()
    return suffix


def extract_original_value(current_value: int, suffix: str) -> int:
    comment_match = COMMENT_RE.search(suffix)
    if comment_match:
        return int(comment_match.group("value"))
    return current_value


def clamp_walkrate(value: int) -> int:
    return max(MIN_WALKRATE, min(MAX_WALKRATE, value))


def scale_walkrate(value: int, scalar: float) -> int:
    if value == 0:
        return 0
    return clamp_walkrate(int(round(value * scalar)))


def transform_walkrates(text: str, deactivate: str, scalar: float) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = WALKRATE_RE.match(body)

        if not match:
            updated_lines.append(line)
            continue

        indent = match.group("indent")
        current_value = int(match.group("value"))
        suffix = match.group("suffix")
        original_value = extract_original_value(current_value, suffix)
        clean_suffix = strip_comment(suffix)

        if deactivate == "YES":
            new_value = 0
            new_suffix = f" // {WALKRATE_COMMENT_PREFIX} {original_value}"
        else:
            new_value = scale_walkrate(original_value, scalar)
            if scalar == DEFAULT_SCALAR:
                new_suffix = clean_suffix
            else:
                new_suffix = f" // {WALKRATE_COMMENT_PREFIX} {original_value}"

        updated_body = f"{indent}walkrate {new_value}{new_suffix}"
        if updated_body != body:
            changed += 1
        updated_lines.append(updated_body + newline)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Walkrate Manager")
    print("========================================")
    print("Control walkrate values in encounters.s.")
    print("This only affects walkrate lines.\n")

    args = parse_args()
    deactivate, scalar = resolve_options(args)

    original = args.encounters.read_text(encoding="utf-8")
    updated, changed = transform_walkrates(original, deactivate, scalar)

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
