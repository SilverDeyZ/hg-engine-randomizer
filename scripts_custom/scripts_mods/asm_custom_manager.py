#!/usr/bin/env python3
"""Enable or disable custom ASM includes in armips/global.s."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GLOBAL_S_PATH = ROOT / "armips" / "global.s"
BACKUP_PATH = ROOT / "bak" / "global.s.asm_custom_manager.bak"

INCLUDE_RE = re.compile(
    r'^(?P<indent>\s*)(?P<comment>//)?(?P<body>\.include\s+"(?P<include>armips/asm/custom/(?P<name>[^"]+)\.s)")(?P<suffix>\s*)$'
)

DESCRIPTIONS = {
    "enable_surf_without_knowing_move": "Allow Surf interaction without a party member knowing Surf.",
    "encounter_rates": "Adjust encounter slot rates for walking, surfing, fishing, rock smash, and headbutt.",
    "remove_obedience_check": "Remove traded Pokemon disobedience badge checks.",
    "roamers": "Change the levels of roaming Pokemon.",
    "rock_climb": "Let Jasmine's Mineral Badge unlock Rock Climb from the menu.",
    "waterfall": "Allow going down waterfalls without needing Waterfall in the party.",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def prettify_name(raw_name: str) -> str:
    return raw_name.replace("_", " ")


def parse_custom_lines(lines: list[str]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []

    for index, line in enumerate(lines):
        body, newline = split_line_ending(line)
        match = INCLUDE_RE.match(body)
        if not match:
            continue

        name = match.group("name")
        entries.append(
            {
                "index": index,
                "line": line,
                "newline": newline,
                "indent": match.group("indent"),
                "body": match.group("body"),
                "suffix": match.group("suffix"),
                "name": name,
                "enabled": match.group("comment") is None,
                "include_path": match.group("include"),
            }
        )

    return entries


def ask_yes_no(name: str, current_enabled: bool, description: str | None) -> bool:
    current_label = "yes" if current_enabled else "no"

    print()
    print(f"{prettify_name(name)} [{current_label}]")
    if description:
        print(f"  {description}")

    while True:
        answer = input("  Set to yes or no? [y/n, Enter keeps current]: ").strip().lower()
        if answer == "":
            return current_enabled
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("  Please answer yes, no, y, n, or press Enter to keep the current value.")


def format_line(entry: dict[str, object], enabled: bool) -> str:
    indent = str(entry["indent"])
    body = str(entry["body"])
    suffix = str(entry["suffix"])
    newline = str(entry["newline"])
    prefix = "" if enabled else "//"
    return f"{indent}{prefix}{body}{suffix}{newline}"


def main() -> int:
    print("========================================")
    print(" Custom ASM Manager")
    print("========================================")
    print(f"File: {GLOBAL_S_PATH}")

    original = read_text(GLOBAL_S_PATH)
    lines = original.splitlines(keepends=True)
    entries = parse_custom_lines(lines)

    if not entries:
        print("No custom ASM include lines were found in armips/global.s.")
        return 1

    print()
    print("Current custom ASM status:")
    for entry in entries:
        status = "yes" if bool(entry["enabled"]) else "no"
        print(f"  [{status}] {entry['name']}.s")

    desired_states: dict[int, bool] = {}
    for entry in entries:
        name = str(entry["name"])
        desired_states[int(entry["index"])] = ask_yes_no(
            name=name,
            current_enabled=bool(entry["enabled"]),
            description=DESCRIPTIONS.get(name),
        )

    updated_lines = lines[:]
    changes = 0

    for entry in entries:
        index = int(entry["index"])
        enabled = desired_states[index]
        updated_line = format_line(entry, enabled)
        if updated_line != lines[index]:
            changes += 1
            updated_lines[index] = updated_line

    if changes == 0:
        print()
        print("No changes were needed.")
        return 0

    write_text(BACKUP_PATH, original)
    write_text(GLOBAL_S_PATH, "".join(updated_lines))

    print()
    print("Done.")
    print(f"  Updated lines : {changes}")
    print(f"  Backup saved  : {BACKUP_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
