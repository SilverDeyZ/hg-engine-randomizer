#!/usr/bin/env python3
"""Control Pokemon EV gain in armips/data/mondata.s."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_MONDATA = Path("armips/data/mondata.s")
DEFAULT_BACKUP = Path("bak/mondata.s.bak")
DEFAULT_SCALAR = 1.0
EV_COMMENT_PREFIX = "evyields original:"

EVYIELDS_RE = re.compile(
    r"^(?P<indent>\s*)evyields\s+"
    r"(?P<values>-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+)"
    r"(?P<suffix>\s*(?://.*)?)$"
)
COMMENT_RE = re.compile(rf"//\s*{re.escape(EV_COMMENT_PREFIX)}\s*(?P<values>-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+)\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enable, disable, and scale EV yields in armips/data/mondata.s."
    )
    parser.add_argument(
        "--ev-gain",
        dest="ev_gain",
        choices=("YES", "NO", "yes", "no"),
        help="Use YES to enable EV gain or NO to disable it.",
    )
    parser.add_argument(
        "--scalar",
        type=float,
        default=None,
        help="Multiplier applied to EV yields when EV gain is enabled. Defaults to 1.0.",
    )
    parser.add_argument(
        "--mondata",
        type=Path,
        default=DEFAULT_MONDATA,
        help=f"Mondata file to edit (default: {DEFAULT_MONDATA}).",
    )
    return parser.parse_args()


def ask_yes_no(label: str, default: str) -> str | None:
    while True:
        raw = input(f"  - {label:<14} [{default}] : ").strip()
        if not raw:
            return None
        upper = raw.upper()
        if upper in {"YES", "NO"}:
            return upper
        print(f"    Invalid value. Please enter YES or NO for {label}.")


def ask_float(label: str, default: float) -> float | None:
    while True:
        raw = input(f"  - {label:<14} [{default:.1f}] : ").strip()
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            print(f"    Invalid value. Please enter a number for {label}.")


def resolve_options(args: argparse.Namespace) -> tuple[str | None, float | None]:
    ev_gain = args.ev_gain.upper() if args.ev_gain is not None else ask_yes_no("EV Gain", "YES")
    if ev_gain is None:
        return None, None
    scalar = args.scalar if args.scalar is not None else ask_float("EV Gain Scalar", DEFAULT_SCALAR)
    if scalar is None:
        return None, None
    scalar = max(-10.0, min(10.0, scalar))
    return ev_gain, scalar


def parse_values(values_text: str) -> list[int]:
    return [int(part.strip()) for part in values_text.split(",")]


def format_values(values: list[int]) -> str:
    return ", ".join(str(value) for value in values)


def scale_values(values: list[int], scalar: float) -> list[int]:
    return [int(round(value * scalar)) for value in values]


def strip_comment(suffix: str) -> str:
    comment_match = COMMENT_RE.search(suffix)
    if comment_match:
        suffix = suffix[: comment_match.start()].rstrip()
    return suffix


def extract_original_values(current_values: list[int], suffix: str) -> list[int]:
    comment_match = COMMENT_RE.search(suffix)
    if comment_match:
        return parse_values(comment_match.group("values"))
    return current_values


def transform_evyields(text: str, ev_gain: str, scalar: float) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = EVYIELDS_RE.match(body)

        if not match:
            updated_lines.append(line)
            continue

        indent = match.group("indent")
        current_values = parse_values(match.group("values"))
        suffix = match.group("suffix")
        original_values = extract_original_values(current_values, suffix)
        clean_suffix = strip_comment(suffix)

        if ev_gain == "NO":
            new_values = [0, 0, 0, 0, 0, 0]
            new_suffix = f" // {EV_COMMENT_PREFIX} {format_values(original_values)}"
        else:
            new_values = scale_values(original_values, scalar)
            new_suffix = clean_suffix

        updated_body = f"{indent}evyields {format_values(new_values)}{new_suffix}"
        if updated_body != body:
            changed += 1
        updated_lines.append(updated_body + newline)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" EV Gain Multiplier")
    print("========================================")
    print("Choose whether EV gain is enabled and set the EV scalar.\n")

    args = parse_args()
    ev_gain, scalar = resolve_options(args)
    if ev_gain is None or scalar is None:
        print("No changes requested.")
        return 0

    original = args.mondata.read_text(encoding="utf-8")
    updated, changed = transform_evyields(original, ev_gain, scalar)

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
