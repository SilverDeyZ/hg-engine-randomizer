#!/usr/bin/env python3
"""Randomize Pokemon types in armips/data/mondata.s."""

from __future__ import annotations

import argparse
import random
import re
from pathlib import Path

DEFAULT_MONDATA = Path("armips/data/mondata.s")
DEFAULT_CONSTANTS = Path("armips/include/constants.s")
DEFAULT_BACKUP = Path("bak/mondata.s.bak")
TYPE_MIN = 0
TYPE_MAX = 17

TYPE_DEFINE_RE = re.compile(
    r"^\s*\.equ\s+(?P<name>TYPE_[A-Z0-9_]+)\s*,\s*(?P<value>\d+)\s*(?://.*)?$"
)
TYPES_LINE_RE = re.compile(
    r"^(?P<indent>\s*)types\s+(?P<left>.+?)\s*,\s*(?P<right>.+?)(?P<suffix>\s*(?://.*)?)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Randomize Pokemon types in armips/data/mondata.s using "
            "type IDs from armips/include/constants.s."
        )
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible results.",
    )
    parser.add_argument(
        "--mondata",
        type=Path,
        default=DEFAULT_MONDATA,
        help=f"Mondata file to edit (default: {DEFAULT_MONDATA}).",
    )
    parser.add_argument(
        "--constants",
        type=Path,
        default=DEFAULT_CONSTANTS,
        help=f"Constants file to read (default: {DEFAULT_CONSTANTS}).",
    )
    return parser.parse_args()


def load_type_map(constants_path: Path) -> dict[int, str]:
    types_by_id: dict[int, str] = {}

    for line in constants_path.read_text(encoding="utf-8").splitlines():
        match = TYPE_DEFINE_RE.match(line)
        if not match:
            continue

        name = match.group("name")
        value = int(match.group("value"))
        if TYPE_MIN <= value <= TYPE_MAX:
            types_by_id[value] = name

    missing = [type_id for type_id in range(TYPE_MIN, TYPE_MAX + 1) if type_id not in types_by_id]
    if missing:
        raise ValueError(f"Missing type definitions for IDs: {', '.join(str(type_id) for type_id in missing)}")

    return types_by_id


def randomize_types(text: str, types_by_id: dict[int, str], rng: random.Random) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []
    all_type_ids = list(range(TYPE_MIN, TYPE_MAX + 1))

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line

        types_match = TYPES_LINE_RE.match(body)
        if not types_match:
            updated_lines.append(line)
            continue

        left = types_match.group("left").strip()
        right = types_match.group("right").strip()

        first_id = rng.choice(all_type_ids)
        if left == right:
            second_id = first_id
        else:
            remaining_ids = [type_id for type_id in all_type_ids if type_id != first_id]
            second_id = rng.choice(remaining_ids)

        updated_body = (
            f"{types_match.group('indent')}types "
            f"{types_by_id[first_id]}, {types_by_id[second_id]}"
            f"{types_match.group('suffix')}"
        )
        updated_lines.append(updated_body + newline)
        changed += 1

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Type Randomizer")
    print("========================================")
    print("Using random type IDs from 0 to 17.\n")

    args = parse_args()
    types_by_id = load_type_map(args.constants)

    rng = random.Random(args.seed)
    original = args.mondata.read_text(encoding="utf-8")
    updated, changed = randomize_types(original, types_by_id, rng)

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
