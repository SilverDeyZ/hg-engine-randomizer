#!/usr/bin/env python3
"""Toggle the 0x80 lead flag on trainer `nummons` entries."""

from __future__ import annotations

import re
from pathlib import Path

DEFAULT_TRAINERS = Path("armips/data/trainers/trainers.s")
NUMMONS_RE = re.compile(
    r"^(?P<indent>\s*)nummons\s+(?:(?:0x80\s*\|\s*)?)(?P<count>\d+)(?P<suffix>\s*(?://.*)?)$"
)
BATTLETYPE_RE = re.compile(r"^\s*battletype\s+(?P<type>\w+)")
TRAINER_START_RE = re.compile(r"^\s*trainerdata\b")
TRAINER_END_RE = re.compile(r"^\s*endentry\b")


def print_intro() -> None:
    print("========================================")
    print(" Trainers Lead Flag")
    print("========================================")
    print("Toggles the trainer lead flag logic in `armips/data/trainers/trainers.s`.\n")


def ask_mode() -> bool:
    print("0 = disable")
    print("1 = enable")

    while True:
        choice = input("Choice: ").strip() or "1"
        if choice == "0":
            return False
        if choice == "1":
            return True
        print("Invalid choice. Use 0 or 1.")


def should_enable(battle_type: str, count: int) -> bool:
    if battle_type == "SINGLE_BATTLE":
        return count >= 2
    if battle_type == "DOUBLE_BATTLE":
        return count >= 3
    return False


def transform_block(lines: list[str], activate: bool) -> tuple[list[str], bool]:
    battle_type = None
    nummons_index = None
    nummons_match = None

    for index, line in enumerate(lines):
        if nummons_index is None:
            match = NUMMONS_RE.match(line.rstrip("\n"))
            if match:
                nummons_index = index
                nummons_match = match
                continue

        battle_match = BATTLETYPE_RE.match(line)
        if battle_match:
            battle_type = battle_match.group("type")

    if nummons_index is None or nummons_match is None:
        return lines, False

    count = int(nummons_match.group("count"))
    indent = nummons_match.group("indent")
    suffix = nummons_match.group("suffix")

    if activate and battle_type and should_enable(battle_type, count):
        replacement = f"{indent}nummons 0x80 | {count}{suffix}\n"
    else:
        replacement = f"{indent}nummons {count}{suffix}\n"

    if lines[nummons_index] == replacement:
        return lines, False

    updated = lines.copy()
    updated[nummons_index] = replacement
    return updated, True


def transform_text(text: str, activate: bool) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    block: list[str] | None = None
    modified_blocks = 0

    for line in lines:
        if block is None and TRAINER_START_RE.match(line):
            block = [line]
            continue

        if block is not None:
            block.append(line)
            if TRAINER_END_RE.match(line):
                updated_block, changed = transform_block(block, activate)
                output.extend(updated_block)
                modified_blocks += int(changed)
                block = None
            continue

        output.append(line)

    if block is not None:
        updated_block, changed = transform_block(block, activate)
        output.extend(updated_block)
        modified_blocks += int(changed)

    return "".join(output), modified_blocks


def main() -> int:
    print_intro()
    activate = ask_mode()
    original = DEFAULT_TRAINERS.read_text(encoding="utf-8")
    updated, modified_blocks = transform_text(original, activate)

    if updated != original:
        DEFAULT_TRAINERS.write_text(updated, encoding="utf-8")

    state = "activated" if activate else "deactivated"
    print(f"random_trainers_lead: {state}; updated {modified_blocks} trainer entries in {DEFAULT_TRAINERS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
