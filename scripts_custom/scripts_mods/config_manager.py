#!/usr/bin/env python3
"""Interactively manage selected toggles in config.s and config.h."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_S_PATH = ROOT / "armips" / "include" / "config.s"
CONFIG_H_PATH = ROOT / "include" / "config.h"
CONFIG_S_BACKUP_PATH = ROOT / "bak" / "config.s.config_manager.bak"
CONFIG_H_BACKUP_PATH = ROOT / "bak" / "config.h.config_manager.bak"

CONFIG_S_OPTIONS = [
    "BATTLE_MODE_FORCE_SET",
    "ALWAYS_HAVE_NATIONAL_DEX",
    "ALWAYS_UNCAPPED_FRAME_RATE",
    "BATTLES_UNCAPPED_FRAME_RATE",
    "FAST_TEXT_PRINTING",
]

CONFIG_H_OPTIONS = [
    "IMPLEMENT_TRANSPARENT_TEXTBOXES",
    "IMPLEMENT_CAPTURE_EXPERIENCE",
    "IMPLEMENT_CRITICAL_CAPTURE",
    "IMPLEMENT_NEW_EV_IV_VIEWER",
    "UPDATE_OVERWORLD_POISON",
    "DISABLE_END_OF_TURN_WEATHER_MESSAGE",
    "FRIENDSHIP_EFFECTS",
    "RESTORE_ITEMS_AT_BATTLE_END",
    "AI_CAN_GRAB_ITEMS",
    "IMPLEMENT_REUSABLE_REPELS",
    "DISABLE_ITEMS_IN_TRAINER_BATTLE",
    "REUSABLE_TMS",
    "DELETABLE_HMS",
    "THUNDER_STORM_WEATHER_ELECTRIC_TERRAIN",
    "FOG_WEATHER_MISTY_TERRAIN",
]

CONFIG_S_LABELS = {
    "BATTLE_MODE_FORCE_SET": "Force Set battle mode",
    "ALWAYS_HAVE_NATIONAL_DEX": "Always have National Dex",
    "ALWAYS_UNCAPPED_FRAME_RATE": "Always uncap frame rate",
    "BATTLES_UNCAPPED_FRAME_RATE": "Uncap frame rate only in battles",
    "FAST_TEXT_PRINTING": "Fast text printing",
}

CONFIG_H_LABELS = {
    "IMPLEMENT_TRANSPARENT_TEXTBOXES": "Transparent textboxes",
    "IMPLEMENT_CAPTURE_EXPERIENCE": "Capture experience",
    "IMPLEMENT_CRITICAL_CAPTURE": "Critical capture",
    "IMPLEMENT_NEW_EV_IV_VIEWER": "New EV/IV viewer",
    "UPDATE_OVERWORLD_POISON": "Update overworld poison",
    "DISABLE_END_OF_TURN_WEATHER_MESSAGE": "Disable end-of-turn weather message",
    "FRIENDSHIP_EFFECTS": "Friendship effects",
    "RESTORE_ITEMS_AT_BATTLE_END": "Restore items at battle end",
    "AI_CAN_GRAB_ITEMS": "AI can grab items",
    "IMPLEMENT_REUSABLE_REPELS": "Reusable repels",
    "DISABLE_ITEMS_IN_TRAINER_BATTLE": "Disable items in trainer battle",
    "REUSABLE_TMS": "Reusable TMs",
    "DELETABLE_HMS": "Deletable HMs",
    "THUNDER_STORM_WEATHER_ELECTRIC_TERRAIN": "Thunder/Storm sets Electric Terrain",
    "FOG_WEATHER_MISTY_TERRAIN": "Fog sets Misty Terrain",
}

CONFIG_S_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Z0-9_]+)(?P<middle>\s+equ\s+)(?P<value>[01])(?P<suffix>\s*(?://.*)?)$"
)
CONFIG_H_RE = re.compile(
    r"^(?P<indent>\s*)(?P<comment>//)?(?P<body>#define\s+(?P<name>[A-Z0-9_]+)\b.*?)(?P<suffix>\s*)$"
)


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


def ask_yes_no(label: str, current_enabled: bool) -> bool:
    current_label = "yes" if current_enabled else "no"
    print(f"{label} [{current_label}]")

    while True:
        answer = input("  Enter yes/no (Enter keeps current): ").strip().lower()
        if answer == "":
            return current_enabled
        if answer in {"y", "yes", "1"}:
            return True
        if answer in {"n", "no", "0"}:
            return False
        print("  Please answer yes, no, 1, 0, or press Enter to keep the current value.")


def parse_config_s(lines: list[str]) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}

    for index, line in enumerate(lines):
        body, newline = split_line_ending(line)
        match = CONFIG_S_RE.match(body)
        if not match:
            continue

        name = match.group("name")
        if name not in CONFIG_S_OPTIONS:
            continue

        entries[name] = {
            "index": index,
            "indent": match.group("indent"),
            "name": name,
            "middle": match.group("middle"),
            "value": match.group("value"),
            "suffix": match.group("suffix"),
            "newline": newline,
        }

    return entries


def parse_config_h(lines: list[str]) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}

    for index, line in enumerate(lines):
        body, newline = split_line_ending(line)
        match = CONFIG_H_RE.match(body)
        if not match:
            continue

        name = match.group("name")
        if name not in CONFIG_H_OPTIONS:
            continue

        entries[name] = {
            "index": index,
            "indent": match.group("indent"),
            "body": match.group("body"),
            "suffix": match.group("suffix"),
            "newline": newline,
            "enabled": match.group("comment") is None,
        }

    return entries


def format_config_s_line(entry: dict[str, object], enabled: bool) -> str:
    value = "1" if enabled else "0"
    return (
        f"{entry['indent']}{entry['name']}{entry['middle']}{value}"
        f"{entry['suffix']}{entry['newline']}"
    )


def format_config_h_line(entry: dict[str, object], enabled: bool) -> str:
    prefix = "" if enabled else "//"
    return f"{entry['indent']}{prefix}{entry['body']}{entry['suffix']}{entry['newline']}"


def update_config_s() -> int:
    original = read_text(CONFIG_S_PATH)
    lines = original.splitlines(keepends=True)
    entries = parse_config_s(lines)

    missing = [name for name in CONFIG_S_OPTIONS if name not in entries]
    if missing:
        raise RuntimeError(f"Missing config.s option(s): {', '.join(missing)}")

    print()
    print("armips/include/config.s")
    desired: dict[str, bool] = {}

    for name in CONFIG_S_OPTIONS:
        if name == "BATTLES_UNCAPPED_FRAME_RATE" and desired.get("ALWAYS_UNCAPPED_FRAME_RATE") is True:
            continue
        current_enabled = str(entries[name]["value"]) == "1"
        desired[name] = ask_yes_no(CONFIG_S_LABELS.get(name, name), current_enabled)

    updated_lines = lines[:]
    changes = 0

    for name, entry in entries.items():
        if name not in desired:
            continue
        updated_line = format_config_s_line(entry, desired[name])
        index = int(entry["index"])
        if updated_line != lines[index]:
            updated_lines[index] = updated_line
            changes += 1

    if changes > 0:
        write_text(CONFIG_S_BACKUP_PATH, original)
        write_text(CONFIG_S_PATH, "".join(updated_lines))

    return changes


def update_config_h() -> int:
    original = read_text(CONFIG_H_PATH)
    lines = original.splitlines(keepends=True)
    entries = parse_config_h(lines)

    missing = [name for name in CONFIG_H_OPTIONS if name not in entries]
    if missing:
        raise RuntimeError(f"Missing config.h option(s): {', '.join(missing)}")

    print()
    print("include/config.h")
    desired: dict[str, bool] = {}

    for name in CONFIG_H_OPTIONS:
        current_enabled = bool(entries[name]["enabled"])
        desired[name] = ask_yes_no(CONFIG_H_LABELS.get(name, name), current_enabled)

    updated_lines = lines[:]
    changes = 0

    for name, entry in entries.items():
        updated_line = format_config_h_line(entry, desired[name])
        index = int(entry["index"])
        if updated_line != lines[index]:
            updated_lines[index] = updated_line
            changes += 1

    if changes > 0:
        write_text(CONFIG_H_BACKUP_PATH, original)
        write_text(CONFIG_H_PATH, "".join(updated_lines))

    return changes


def main() -> int:
    print("========================================")
    print(" Config Manager")
    print("========================================")
    print("Manage selected yes/no options in config.s and config.h.")

    config_s_changes = update_config_s()
    config_h_changes = update_config_h()

    print()
    if config_s_changes == 0 and config_h_changes == 0:
        print("No changes were needed.")
        return 0

    print("Done.")
    print(f"  config.s updated lines : {config_s_changes}")
    print(f"  config.h updated lines : {config_h_changes}")
    if config_s_changes > 0:
        print(f"  config.s backup        : {CONFIG_S_BACKUP_PATH}")
    if config_h_changes > 0:
        print(f"  config.h backup        : {CONFIG_H_BACKUP_PATH}")
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
