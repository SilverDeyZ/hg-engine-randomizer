#!/usr/bin/env python3
"""Update shiny odds in config.h and trainers_expansion_reroll.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_H_PATH = ROOT / "include" / "config.h"
TRAINER_REROLL_PATH = ROOT / "scripts_custom" / "scripts_format" / "trainers_expansion_reroll.py"
CONFIG_H_BACKUP = ROOT / "bak" / "config.h.shiny_odds_manager.bak"
TRAINER_REROLL_BACKUP = ROOT / "bak" / "trainers_expansion_reroll.py.shiny_odds_manager.bak"

OPTIONS = [
    {"menu": "1", "label": "Default", "denominator": 8192, "value": 8},
    {"menu": "2", "label": "Modern", "denominator": 4096, "value": 16},
    {"menu": "3", "label": "Boosted", "denominator": 2048, "value": 32},
    {"menu": "4", "label": "Very High", "denominator": 1024, "value": 64},
    {"menu": "5", "label": "Extreme", "denominator": 512, "value": 128},
]

SHINY_ODDS_RE = re.compile(
    r"^(?P<prefix>\s*#define\s+SHINY_ODDS\s+)(?P<value>\d+)(?P<suffix>\s*(?://.*)?)$",
    re.MULTILINE,
)
TRAINER_DENOMINATOR_RE = re.compile(
    r"^(?P<prefix>\s*DEFAULT_SHINY_DENOMINATOR\s*=\s*)(?P<value>\d+)(?P<suffix>\s*)$",
    re.MULTILINE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def replace_define(text: str, pattern: re.Pattern[str], new_value: int, path: Path) -> tuple[str, int]:
    for line in text.splitlines(keepends=True):
        body = line[:-1] if line.endswith("\n") else line
        match = pattern.match(body)
        if not match:
            continue
        newline = "\n" if line.endswith("\n") else ""
        updated_line = f"{match.group('prefix')}{new_value}{match.group('suffix')}{newline}"
        return text.replace(line, updated_line, 1), int(match.group("value"))
    raise RuntimeError(f"Expected shiny odds setting not found in {path}")


def odds_label(denominator: int, value: int) -> str:
    return f"1/{denominator} (SHINY_ODDS = {value})"


def read_current_values() -> tuple[int, int]:
    config_text = read_text(CONFIG_H_PATH)
    reroll_text = read_text(TRAINER_REROLL_PATH)

    config_match = SHINY_ODDS_RE.search(config_text)
    reroll_match = TRAINER_DENOMINATOR_RE.search(reroll_text)

    if config_match is None:
        raise RuntimeError(f"Could not find SHINY_ODDS in {CONFIG_H_PATH}")
    if reroll_match is None:
        raise RuntimeError(f"Could not find DEFAULT_SHINY_DENOMINATOR in {TRAINER_REROLL_PATH}")

    return int(config_match.group("value")), int(reroll_match.group("value"))


def ask_option() -> dict[str, int | str] | None:
    print("========================================")
    print(" Shiny Odds Manager")
    print("========================================")
    print("Select the shiny odds to apply to both files.\n")

    current_value, current_denominator = read_current_values()
    print(f"Current config.h              : {odds_label(65536 // current_value, current_value)}")
    print(f"Current trainers reroll script: 1/{current_denominator}")
    print()

    print("0 = cancel")
    for option in OPTIONS:
        print(f"{option['menu']} = {option['label']:<8}  {odds_label(option['denominator'], option['value'])}")

    while True:
        choice = input("\nChoice: ").strip() or "0"
        if choice == "0":
            return None
        for option in OPTIONS:
            if option["menu"] == choice:
                return option
        print("Invalid choice. Use 0, 1, 2, 3, 4, or 5.")


def confirm_changes(selected: dict[str, int | str]) -> bool:
    denominator = int(selected["denominator"])
    value = int(selected["value"])

    print()
    print("Planned changes:")
    print(f"  include/config.h                          -> {odds_label(denominator, value)}")
    print(f"  scripts_format/trainers_expansion_reroll.py -> 1/{denominator}")
    print()

    while True:
        answer = input("Confirm changes? [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no", ""}:
            return False
        print("Please answer yes or no.")


def main() -> int:
    selected = ask_option()
    if selected is None:
        print("Cancelled.")
        return 0

    if not confirm_changes(selected):
        print("Cancelled.")
        return 0

    denominator = int(selected["denominator"])
    value = int(selected["value"])

    config_original = read_text(CONFIG_H_PATH)
    reroll_original = read_text(TRAINER_REROLL_PATH)

    config_updated, old_config_value = replace_define(config_original, SHINY_ODDS_RE, value, CONFIG_H_PATH)
    reroll_updated, old_reroll_denominator = replace_define(
        reroll_original,
        TRAINER_DENOMINATOR_RE,
        denominator,
        TRAINER_REROLL_PATH,
    )

    if config_updated == config_original and reroll_updated == reroll_original:
        print("No changes were needed.")
        return 0

    if config_updated != config_original:
        write_text(CONFIG_H_BACKUP, config_original)
        write_text(CONFIG_H_PATH, config_updated)
    if reroll_updated != reroll_original:
        write_text(TRAINER_REROLL_BACKUP, reroll_original)
        write_text(TRAINER_REROLL_PATH, reroll_updated)

    print()
    print("Done.")
    print(f"  config.h                    : {odds_label(65536 // old_config_value, old_config_value)} -> {odds_label(denominator, value)}")
    print(f"  trainers_expansion_reroll.py: 1/{old_reroll_denominator} -> 1/{denominator}")
    if config_updated != config_original:
        print(f"  config.h backup             : {CONFIG_H_BACKUP}")
    if reroll_updated != reroll_original:
        print(f"  reroll script backup        : {TRAINER_REROLL_BACKUP}")
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
