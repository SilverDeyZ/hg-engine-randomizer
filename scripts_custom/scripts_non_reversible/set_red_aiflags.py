#!/usr/bin/env python3
"""Copy Red's trainer AI flags to every trainer entry in trainers.s."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_TRAINERS = Path("armips/data/trainers/trainers.s")
DEFAULT_BACKUP = Path("bak/trainers_red_aiflags.bak")
RED_TRAINERCLASS = "TRAINERCLASS_PKMN_TRAINER_RED"

TRAINER_START_RE = re.compile(r'^\s*trainerdata\s+\d+,\s*"(?P<name>[^"]*)"')
TRAINERCLASS_RE = re.compile(r"^\s*trainerclass\s+(?P<trainerclass>\w+)")
AIFLAGS_RE = re.compile(r"^(?P<indent>\s*)aiflags\s+(?P<flags>.+?)(?P<suffix>\s*(?://.*)?)$")
TRAINER_END_RE = re.compile(r"^\s*endentry\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Set every trainer aiflags entry in armips/data/trainers/trainers.s "
            "to the same flag combination used by Red."
        )
    )
    parser.add_argument(
        "--trainers",
        type=Path,
        default=DEFAULT_TRAINERS,
        help=f"Trainer file to edit (default: {DEFAULT_TRAINERS}).",
    )
    parser.add_argument(
        "--backup",
        type=Path,
        default=DEFAULT_BACKUP,
        help=f"Backup file to write before modifying the trainer file (default: {DEFAULT_BACKUP}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show how many trainer entries would be updated without writing the file.",
    )
    return parser.parse_args()


def split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def extract_red_aiflags(text: str) -> str:
    in_entry = False
    entry_name = ""
    entry_trainerclass = ""
    entry_flags: str | None = None

    for line in text.splitlines():
        start_match = TRAINER_START_RE.match(line)
        if start_match:
            in_entry = True
            entry_name = start_match.group("name")
            entry_trainerclass = ""
            entry_flags = None
            continue

        if not in_entry:
            continue

        trainerclass_match = TRAINERCLASS_RE.match(line)
        if trainerclass_match:
            entry_trainerclass = trainerclass_match.group("trainerclass")
            continue

        flags_match = AIFLAGS_RE.match(line)
        if flags_match:
            entry_flags = flags_match.group("flags")
            continue

        if TRAINER_END_RE.match(line):
            if entry_trainerclass == RED_TRAINERCLASS or entry_name == "Red":
                if entry_flags is None:
                    raise ValueError("Red trainer entry was found, but it has no aiflags line.")
                return entry_flags

            in_entry = False
            entry_name = ""
            entry_trainerclass = ""
            entry_flags = None

    raise ValueError("Could not find Red's trainer entry in the trainer file.")


def set_all_aiflags(text: str, target_flags: str) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        body, newline = split_line_ending(line)
        flags_match = AIFLAGS_RE.match(body)
        if not flags_match:
            updated_lines.append(line)
            continue

        replacement = (
            f"{flags_match.group('indent')}aiflags {target_flags}{flags_match.group('suffix')}{newline}"
        )
        if replacement != line:
            changed += 1
        updated_lines.append(replacement)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    original = args.trainers.read_text(encoding="utf-8")
    red_flags = extract_red_aiflags(original)
    updated, changed = set_all_aiflags(original, red_flags)

    print("========================================")
    print(" Red AI Flags For All Trainers")
    print("========================================")
    print(f"Red aiflags : {red_flags}")
    print(f"Entries hit : {changed}")
    print(f"Trainer file: {args.trainers}")

    if args.dry_run:
        print("Dry run only. No files were written.")
        return 0

    if updated != original:
        write_backup(original, args.backup)
        args.trainers.write_text(updated, encoding="utf-8")
        print(f"Backup saved: {args.backup}")
    else:
        print("No changes were needed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
