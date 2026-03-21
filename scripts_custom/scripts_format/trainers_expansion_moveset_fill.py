#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SPECIAL_FORM_RANGES = {
    "SPECIES_DEOXYS": (3, 495),
    "SPECIES_WORMADAM": (2, 498),
    "SPECIES_GIRATINA": (1, 500),
    "SPECIES_SHAYMIN": (1, 501),
    "SPECIES_ROTOM": (5, 502),
}


class TransformError(RuntimeError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def strip_inline_comment(line: str) -> str:
    return line.split("//", 1)[0].rstrip()


def parse_species_constants(species_header_path: Path) -> tuple[dict[str, int], dict[int, str]]:
    name_to_num: dict[str, int] = {}
    num_to_name: dict[int, str] = {}
    pattern = re.compile(r"#define\s+(SPECIES_[A-Z0-9_]+)\s+([0-9]+)")

    for raw_line in species_header_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw_line.strip())
        if not match:
            continue
        species_name = match.group(1)
        species_num = int(match.group(2))
        name_to_num[species_name] = species_num
        num_to_name[species_num] = species_name

    if not name_to_num:
        raise TransformError(f"Could not parse species constants from {species_header_path}")
    return name_to_num, num_to_name


def parse_form_table(form_table_path: Path) -> dict[str, list[str]]:
    table: dict[str, list[str]] = {}
    current_species: str | None = None
    current_entries: list[str] = []
    start_pattern = re.compile(r"\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{")

    for raw_line in form_table_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line).strip()
        if not line:
            continue

        if current_species is None:
            start_match = start_pattern.search(line)
            if start_match:
                current_species = start_match.group(1)
                current_entries = []
            continue

        if line.startswith("}"):
            table[current_species] = current_entries
            current_species = None
            current_entries = []
            continue

        species_tokens = re.findall(r"SPECIES_[A-Z0-9_]+", line)
        if species_tokens:
            current_entries.append(species_tokens[-1])

    return table


def resolve_form_species(
    base_species: str,
    form_no: int,
    species_name_to_num: dict[str, int],
    species_num_to_name: dict[int, str],
    form_table: dict[str, list[str]],
) -> str:
    if form_no == 0:
        return base_species

    special_case = SPECIAL_FORM_RANGES.get(base_species)
    if special_case is not None:
        max_form, start_num = special_case
        if form_no <= max_form:
            adjusted_num = start_num + form_no
            adjusted_species = species_num_to_name.get(adjusted_num)
            if adjusted_species is None:
                raise TransformError(
                    f"Could not resolve adjusted species number {adjusted_num} for {base_species} form {form_no}"
                )
            return adjusted_species

    entries = form_table.get(base_species, [])
    if 0 < form_no <= len(entries):
        return entries[form_no - 1]

    if base_species not in species_name_to_num:
        raise TransformError(f"Unknown species constant {base_species}")
    return base_species


def load_learnsets(learnsets_path: Path) -> dict[str, dict]:
    with learnsets_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TransformError(f"Unexpected learnsets format in {learnsets_path}")
    return data


def parse_mon_species_and_level(
    mon_lines: list[str],
    species_name_to_num: dict[str, int],
    species_num_to_name: dict[int, str],
    form_table: dict[str, list[str]],
) -> tuple[str, str, int]:
    level: int | None = None
    base_species: str | None = None
    form_no = 0

    for raw_line in mon_lines:
        line = strip_inline_comment(raw_line).strip()
        if not line:
            continue
        level_match = re.match(r"level\s+([0-9]+)", line)
        if level_match:
            level = int(level_match.group(1), 0)
            continue
        pokemon_match = re.match(r"pokemon\s+(SPECIES_[A-Z0-9_]+)", line)
        if pokemon_match:
            base_species = pokemon_match.group(1)
            form_no = 0
            continue
        form_match = re.match(r"monwithform\s+(SPECIES_[A-Z0-9_]+)\s*,\s*([0-9]+)", line)
        if form_match:
            base_species = form_match.group(1)
            form_no = int(form_match.group(2), 0)
            continue

    if level is None or base_species is None:
        raise TransformError("Could not determine mon level/species while processing trainer file")

    resolved_species = resolve_form_species(
        base_species,
        form_no,
        species_name_to_num,
        species_num_to_name,
        form_table,
    )
    return base_species, resolved_species, level


def get_last_four_level_moves(
    species_candidates: list[str],
    level: int,
    learnsets: dict[str, dict],
) -> list[str]:
    if species_candidates and species_candidates[0] == "SPECIES_NONE":
        return ["MOVE_NONE"] * 4

    species_entry = None
    selected_species = None
    for candidate in species_candidates:
        species_entry = learnsets.get(candidate)
        if species_entry is not None:
            selected_species = candidate
            break
    if species_entry is None:
        raise TransformError(f"No learnset entry found for {' / '.join(species_candidates)}")

    level_moves = species_entry.get("LevelMoves", [])
    eligible_moves = [
        entry["Move"]
        for entry in level_moves
        if isinstance(entry, dict)
        and "Level" in entry
        and "Move" in entry
        and int(entry["Level"]) <= level
    ]

    recent_moves = list(eligible_moves[-4:])
    while len(recent_moves) < 4:
        recent_moves.insert(0, "MOVE_NONE")
    return recent_moves


def replace_four_none_moves_in_mon(
    mon_lines: list[str],
    learnsets: dict[str, dict],
    species_name_to_num: dict[str, int],
    species_num_to_name: dict[int, str],
    form_table: dict[str, list[str]],
) -> tuple[list[str], bool]:
    move_line_indexes: list[int] = []
    move_values: list[str] = []

    for idx, raw_line in enumerate(mon_lines):
        stripped = strip_inline_comment(raw_line).strip()
        move_match = re.match(r"move\s+(\S+)", stripped)
        if move_match:
            move_line_indexes.append(idx)
            move_values.append(move_match.group(1))

    if len(move_line_indexes) != 4:
        return mon_lines, False

    if any(value != "MOVE_NONE" for value in move_values):
        return mon_lines, False

    first_index = move_line_indexes[0]
    if move_line_indexes != list(range(first_index, first_index + 4)):
        return mon_lines, False

    base_species, resolved_species, level = parse_mon_species_and_level(
        mon_lines,
        species_name_to_num,
        species_num_to_name,
        form_table,
    )
    species_candidates = [resolved_species]
    if base_species != resolved_species:
        species_candidates.append(base_species)
    replacement_moves = get_last_four_level_moves(species_candidates, level, learnsets)

    updated_lines = list(mon_lines)
    for offset, line_index in enumerate(move_line_indexes):
        indentation_match = re.match(r"(\s*)move\s+", mon_lines[line_index])
        indentation = indentation_match.group(1) if indentation_match else ""
        newline = "\n" if mon_lines[line_index].endswith("\n") else ""
        updated_lines[line_index] = f"{indentation}move {replacement_moves[offset]}{newline}"

    return updated_lines, True


def transform_trainer_file(
    input_path: Path,
    learnsets_path: Path,
    species_header_path: Path,
    form_table_path: Path,
) -> tuple[str, int]:
    species_name_to_num, species_num_to_name = parse_species_constants(species_header_path)
    form_table = parse_form_table(form_table_path)
    learnsets = load_learnsets(learnsets_path)

    with input_path.open("r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()

    output_lines: list[str] = []
    current_mon: list[str] | None = None
    replacements = 0

    for raw_line in lines:
        stripped = strip_inline_comment(raw_line).strip()

        if stripped.startswith("ivs "):
            if current_mon is not None:
                updated_mon, changed = replace_four_none_moves_in_mon(
                    current_mon,
                    learnsets,
                    species_name_to_num,
                    species_num_to_name,
                    form_table,
                )
                output_lines.extend(updated_mon)
                if changed:
                    replacements += 1
            current_mon = [raw_line]
            continue

        if current_mon is not None and stripped == "endparty":
            updated_mon, changed = replace_four_none_moves_in_mon(
                current_mon,
                learnsets,
                species_name_to_num,
                species_num_to_name,
                form_table,
            )
            output_lines.extend(updated_mon)
            if changed:
                replacements += 1
            current_mon = None
            output_lines.append(raw_line)
            continue

        if current_mon is not None:
            current_mon.append(raw_line)
        else:
            output_lines.append(raw_line)

    if current_mon is not None:
        updated_mon, changed = replace_four_none_moves_in_mon(
            current_mon,
            learnsets,
            species_name_to_num,
            species_num_to_name,
            form_table,
        )
        output_lines.extend(updated_mon)
        if changed:
            replacements += 1

    return "".join(output_lines), replacements


def build_argument_parser():
    root = repo_root()
    import argparse

    parser = argparse.ArgumentParser(
        description="Fill trainer MOVE_NONE slots with the Pokemon's last four level-up moves.",
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
        "--learnsets",
        type=Path,
        default=root / "data" / "learnsets" / "learnsets.json",
        help="Level-up learnset JSON file.",
    )
    parser.add_argument(
        "--species-header",
        type=Path,
        default=root / "include" / "constants" / "species.h",
        help="Species constant header used for form resolution.",
    )
    parser.add_argument(
        "--form-table",
        type=Path,
        default=root / "data" / "PokeFormDataTbl.c",
        help="Form mapping table used for monwithform support.",
    )
    return parser


def print_intro() -> None:
    print("========================================")
    print(" Trainer Four-Move Filler")
    print("========================================")
    print("This script fills trainer Pokemon with their last four level-up moves")
    print("when all four move slots are still MOVE_NONE in generalized trainers.s.")
    print("It mimics the automatic move fill behavior you would normally expect.\n")


def ask_mode() -> int:
    print("0 = quit")
    print("1 = launch")

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

    try:
        transformed_text, replacements = transform_trainer_file(
            input_path=input_path,
            learnsets_path=args.learnsets.resolve(),
            species_header_path=args.species_header.resolve(),
            form_table_path=args.form_table.resolve(),
        )
    except TransformError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(transformed_text)
    print(f"Updated {replacements} mon entries in {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
