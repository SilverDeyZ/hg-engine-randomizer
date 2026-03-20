#!/usr/bin/env python3
"""Apply BlazeBlack2Redux evolution changes to armips/data/evodata.s."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

DEFAULT_EVO_DATA = Path("armips/data/evodata.s")
DEFAULT_CHANGES_CSV = Path("scripts_custom/Data/BlazeBlack2Redux_evolution_changes.csv")
DEFAULT_BACKUP = Path("bak/evodata.s.bak")
MAX_EVO_SLOTS = 9

EVODATA_RE = re.compile(r"^(?P<indent>\s*)evodata\s+(?P<species>SPECIES_[A-Z0-9_]+)\s*$")
EVOLUTION_RE = re.compile(
    r"^(?P<indent>\s*)evolution\s+"
    r"(?P<method>[A-Z0-9_]+)\s*,\s*(?P<param>[^,]+)\s*,\s*(?P<target>[A-Z0-9_]+)"
    r"(?P<suffix>\s*(?://.*)?)$"
)
TERMINATE_RE = re.compile(r"^(?P<indent>\s*)terminateevodata\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply evolution changes from BlazeBlack2Redux_evolution_changes.csv "
            "to armips/data/evodata.s."
        )
    )
    parser.add_argument(
        "--evodata",
        type=Path,
        default=DEFAULT_EVO_DATA,
        help=f"Evolution data file to edit (default: {DEFAULT_EVO_DATA}).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CHANGES_CSV,
        help=f"CSV file to read (default: {DEFAULT_CHANGES_CSV}).",
    )
    return parser.parse_args()


def load_changes(csv_path: Path) -> dict[str, dict[int, tuple[str, str, str]]]:
    changes: dict[str, dict[int, tuple[str, str, str]]] = {}

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            species_name = row["source_species"].strip()
            slot = int(row["evo_slot"].strip())
            if not 1 <= slot <= MAX_EVO_SLOTS:
                raise ValueError(f"Invalid evo_slot {slot} for {species_name}")

            species_changes = changes.setdefault(species_name, {})
            species_changes[slot] = (
                row["method"].strip(),
                row["param"].strip(),
                row["target_species"].strip(),
            )

    return changes


def build_species_block(
    species_name: str,
    indent: str,
    evo_indent: str,
    changes: dict[int, tuple[str, str, str]],
) -> list[str]:
    lines = [f"{indent}evodata {species_name}\n"]

    for slot in range(1, MAX_EVO_SLOTS + 1):
        method, param, target = changes.get(slot, ("EVO_NONE", "0", "SPECIES_NONE"))
        lines.append(f"{evo_indent}evolution {method}, {param}, {target}\n")

    lines.append(f"{evo_indent}terminateevodata\n")
    return lines


def apply_changes(text: str, changes: dict[str, dict[int, tuple[str, str, str]]]) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    updated_lines: list[str] = []
    index = 0
    changed = 0

    while index < len(lines):
        line = lines[index]
        match = EVODATA_RE.match(line.rstrip("\n"))
        if not match:
            updated_lines.append(line)
            index += 1
            continue

        species_name = match.group("species")
        block_lines = [line]
        index += 1

        while index < len(lines):
            block_lines.append(lines[index])
            if TERMINATE_RE.match(lines[index].rstrip("\n")):
                index += 1
                break
            index += 1

        species_changes = changes.get(species_name)
        if species_changes is None:
            updated_lines.extend(block_lines)
            continue

        evo_indent = "    "
        for block_line in block_lines[1:]:
            evo_match = EVOLUTION_RE.match(block_line.rstrip("\n"))
            if evo_match:
                evo_indent = evo_match.group("indent")
                break

        rebuilt = build_species_block(
            species_name=species_name,
            indent=match.group("indent"),
            evo_indent=evo_indent,
            changes=species_changes,
        )

        if rebuilt != block_lines:
            changed += 1
        updated_lines.extend(rebuilt)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" BlazeBlack2Redux Evolutions")
    print("========================================")
    print("Applying evolution changes from the CSV.\n")

    args = parse_args()
    changes = load_changes(args.csv)

    original = args.evodata.read_text(encoding="utf-8")
    updated, changed = apply_changes(original, changes)

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.evodata.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Evodata file    : {args.evodata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
