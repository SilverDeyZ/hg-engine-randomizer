#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path


class RerollError(RuntimeError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def strip_inline_comment(line: str) -> str:
    return line.split("//", 1)[0].rstrip()


def parse_natures(constants_path: Path) -> list[str]:
    names_by_index: dict[int, str] = {}
    pattern = re.compile(r"\.equ\s+(NATURE_[A-Z0-9_]+),\s*\((\d+)\)")

    for raw_line in constants_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line).strip()
        match = pattern.match(line)
        if match:
            names_by_index[int(match.group(2))] = match.group(1)

    if len(names_by_index) != 25:
        raise RerollError(f"Expected 25 natures in {constants_path}, found {len(names_by_index)}")
    return [names_by_index[idx] for idx in sorted(names_by_index)]


def reroll_trainer_file(input_path: Path, constants_path: Path) -> tuple[str, int, int]:
    nature_names = parse_natures(constants_path)
    nature_replacements = 0
    shiny_replacements = 0
    output_lines: list[str] = []

    with input_path.open("r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()

    for raw_line in lines:
        newline = "\n" if raw_line.endswith("\n") else ""
        nature_match = re.match(r"(\s*)nature\s+\S+(\s*(?://.*)?)$", raw_line.rstrip("\n"))
        if nature_match:
            indent, comment = nature_match.groups()
            output_lines.append(f"{indent}nature {random.choice(nature_names)}{comment}{newline}")
            nature_replacements += 1
            continue

        shiny_match = re.match(r"(\s*)shinylock\s+\S+(\s*(?://.*)?)$", raw_line.rstrip("\n"))
        if shiny_match:
            indent, comment = shiny_match.groups()
            shiny_value = "1" if random.randrange(512) == 0 else "0"
            output_lines.append(f"{indent}shinylock {shiny_value}{comment}{newline}")
            shiny_replacements += 1
            continue

        output_lines.append(raw_line)

    return "".join(output_lines), nature_replacements, shiny_replacements


def build_argument_parser() -> argparse.ArgumentParser:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Reroll trainer Pokemon natures and shiny odds in a trainer assembly file.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=root / "armips" / "data" / "trainers" / "trainers.s",
        help="Trainer file to update.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output path. Defaults to overwriting the input file.",
    )
    parser.add_argument(
        "--constants",
        type=Path,
        default=root / "armips" / "include" / "constants.s",
        help="Constants file used to load the 25 nature names.",
    )
    return parser


def print_intro() -> None:
    print("========================================")
    print(" Trainer Nature/Shiny Reroll")
    print("========================================")
    print("This script rerolls every trainer Pokemon nature")
    print("and gives each trainer Pokemon a 1/512 chance to be shiny.\n")


def ask_mode() -> int:
    print("0 = quit")
    print("1 = reroll")

    while True:
        choice = input("Choice: ").strip() or "0"
        if choice in {"0", "1"}:
            return int(choice)
        print("Invalid choice. Use 0 or 1.")


def main() -> int:
    print_intro()
    if ask_mode() == 0:
        print("Aborted.")
        return 0

    parser = build_argument_parser()
    args = parser.parse_args()

    input_path = args.input.resolve()
    output_path = (args.output or args.input).resolve()
    constants_path = args.constants.resolve()

    try:
        transformed_text, nature_count, shiny_count = reroll_trainer_file(input_path, constants_path)
    except (OSError, RerollError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(transformed_text)

    print(f"Updated {nature_count} nature lines and {shiny_count} shinylock lines in {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
