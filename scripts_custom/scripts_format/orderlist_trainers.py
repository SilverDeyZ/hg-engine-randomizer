#!/usr/bin/env python3
"""Reorder trainerdata blocks in armips/data/trainers/trainers.s."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


class ReorderError(RuntimeError):
    pass


TRAINERDATA_RE = re.compile(r"^\s*trainerdata\s+(?P<id>\d+)\b")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_trainers_path() -> Path:
    return repo_root() / "armips" / "data" / "trainers" / "trainers.s"


def default_order_csv_path() -> Path:
    return repo_root() / "scripts_custom" / "Data" / "orderlist_trainers.csv"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reorder trainerdata blocks in trainers.s by vanilla ID order or accessibility order."
    )
    parser.add_argument(
        "--trainers",
        type=Path,
        default=default_trainers_path(),
        help="Trainer file to reorder.",
    )
    parser.add_argument(
        "--order-csv",
        type=Path,
        default=default_order_csv_path(),
        help="Accessibility order CSV used for mode 1.",
    )
    return parser


def print_intro() -> None:
    print("========================================")
    print(" Trainers Orderlist")
    print("========================================")
    print("This script reorders the trainerdata blocks in trainers.s.")
    print("0 = apply vanilla order (trainerdata ID order)")
    print("1 = apply accessibility order from scripts_custom/Data/orderlist_trainers.csv")
    print("2 = quit\n")


def ask_mode() -> int:
    while True:
        choice = input("Choice: ").strip() or "2"
        if choice in {"0", "1", "2"}:
            return int(choice)
        print("Invalid choice. Use 0, 1, or 2.")


def split_trainer_blocks(text: str) -> tuple[str, list[tuple[int, str]]]:
    lines = text.splitlines(keepends=True)
    start_indexes: list[int] = []

    for index, line in enumerate(lines):
        if TRAINERDATA_RE.match(line):
            start_indexes.append(index)

    if not start_indexes:
        raise ReorderError("No trainerdata blocks found in trainers.s.")

    preamble = "".join(lines[: start_indexes[0]])
    blocks: list[tuple[int, str]] = []

    for block_index, start in enumerate(start_indexes):
        end = start_indexes[block_index + 1] if block_index + 1 < len(start_indexes) else len(lines)
        block_text = "".join(lines[start:end])
        match = TRAINERDATA_RE.match(lines[start])
        if match is None:
            raise ReorderError("Failed to parse a trainerdata block header.")
        blocks.append((int(match.group("id")), block_text))

    return preamble, blocks


def load_accessibility_order(csv_path: Path) -> list[int]:
    ordered_rows: list[tuple[int, int]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                trainer_id = int(row["TrainerData"].strip())
            except (KeyError, ValueError) as exc:
                raise ReorderError(f"Invalid row in {csv_path}: {row!r}") from exc

            raw_order = row.get("OrderID", "").strip()
            if not raw_order:
                continue

            try:
                order_id = int(raw_order)
            except ValueError as exc:
                raise ReorderError(f"Invalid OrderID in {csv_path}: {row!r}") from exc

            ordered_rows.append((order_id, trainer_id))

    if not ordered_rows:
        raise ReorderError(f"No accessibility order rows found in {csv_path}.")

    ordered_rows.sort()
    return [trainer_id for order_id, trainer_id in ordered_rows]


def build_reordered_text(
    preamble: str,
    blocks: list[tuple[int, str]],
    ordered_ids: list[int],
) -> str:
    blocks_by_id: dict[int, str] = {}
    for trainer_id, block_text in blocks:
        if trainer_id in blocks_by_id:
            raise ReorderError(f"Duplicate trainerdata block ID found: {trainer_id}")
        blocks_by_id[trainer_id] = block_text

    ordered_blocks: list[str] = []
    seen_ids: set[int] = set()

    for trainer_id in ordered_ids:
        block_text = blocks_by_id.get(trainer_id)
        if block_text is None:
            continue
        ordered_blocks.append(block_text)
        seen_ids.add(trainer_id)

    for trainer_id, block_text in sorted(blocks, key=lambda item: item[0]):
        if trainer_id not in seen_ids:
            ordered_blocks.append(block_text)

    return preamble + "".join(ordered_blocks)


def reorder_text(text: str, mode: int, order_csv_path: Path) -> tuple[str, int]:
    preamble, blocks = split_trainer_blocks(text)

    if mode == 0:
        ordered_ids = [trainer_id for trainer_id, _ in sorted(blocks, key=lambda item: item[0])]
    else:
        ordered_ids = load_accessibility_order(order_csv_path)

    updated = build_reordered_text(preamble, blocks, ordered_ids)
    return updated, len(blocks)


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def main() -> int:
    print_intro()
    args = build_argument_parser().parse_args()
    mode = ask_mode()
    if mode == 2:
        print("No changes requested.")
        return 0

    try:
        original = args.trainers.read_text(encoding="utf-8")
        updated, block_count = reorder_text(original, mode, args.order_csv)
    except (OSError, ReorderError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if updated != original:
        write_text(args.trainers, updated)

    mode_name = "vanilla order" if mode == 0 else "accessibility order"
    print()
    print("Done.")
    print(f"  Trainer blocks : {block_count}")
    print(f"  Applied mode   : {mode_name}")
    print(f"  Trainers file  : {args.trainers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
