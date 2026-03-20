#!/usr/bin/env python3
"""Apply BlazeBlack2Redux learnset changes to data/learnsets/learnsets.json."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from pathlib import Path

DEFAULT_LEARNSETS = Path("data/learnsets/learnsets.json")
DEFAULT_SPECIES_HEADER = Path("include/constants/species.h")
DEFAULT_MOVES_HEADER = Path("include/constants/moves.h")
DEFAULT_MOVES_CSV = Path("scripts_custom/Data/BlazeBlack2Redux_moves_compat.csv")
DEFAULT_BACKUP = Path("bak/learnsets.json.bak")

DEFINE_RE = re.compile(r"^\s*#define\s+(?P<name>[A-Z0-9_]+)\s+(?P<expr>.+?)\s*(?://.*)?$")

MOVE_ALIASES = {
    "MOVE_FAINT_ATTACK": "MOVE_FEINT_ATTACK",
    "MOVE_SELF_DESTRUCT": "MOVE_SELFDESTRUCT",
}


class ExpressionEvaluator(ast.NodeVisitor):
    """Evaluate simple integer expressions used in species defines."""

    def __init__(self, values: dict[str, int]) -> None:
        self.values = values

    def visit_Expression(self, node: ast.Expression) -> int:
        return self.visit(node.body)

    def visit_Name(self, node: ast.Name) -> int:
        if node.id not in self.values:
            raise KeyError(node.id)
        return self.values[node.id]

    def visit_Constant(self, node: ast.Constant) -> int:
        if not isinstance(node.value, int):
            raise ValueError(f"Unsupported constant: {node.value!r}")
        return node.value

    def visit_UnaryOp(self, node: ast.UnaryOp) -> int:
        value = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise ValueError("Unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp) -> int:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Div):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.LShift):
            return left << right
        if isinstance(node.op, ast.RShift):
            return left >> right
        if isinstance(node.op, ast.BitOr):
            return left | right
        if isinstance(node.op, ast.BitAnd):
            return left & right
        raise ValueError("Unsupported binary operator")

    def generic_visit(self, node: ast.AST) -> int:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply level-up moves and TM compatibility from BlazeBlack2Redux_moves_compat.csv "
            "to data/learnsets/learnsets.json."
        )
    )
    parser.add_argument(
        "--learnsets",
        type=Path,
        default=DEFAULT_LEARNSETS,
        help=f"Learnsets JSON to edit (default: {DEFAULT_LEARNSETS}).",
    )
    parser.add_argument(
        "--species-header",
        type=Path,
        default=DEFAULT_SPECIES_HEADER,
        help=f"Species header to read (default: {DEFAULT_SPECIES_HEADER}).",
    )
    parser.add_argument(
        "--moves-header",
        type=Path,
        default=DEFAULT_MOVES_HEADER,
        help=f"Moves header to read (default: {DEFAULT_MOVES_HEADER}).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_MOVES_CSV,
        help=f"CSV file to read (default: {DEFAULT_MOVES_CSV}).",
    )
    return parser.parse_args()


def evaluate_expression(expression: str, values: dict[str, int]) -> int:
    tree = ast.parse(expression, mode="eval")
    evaluator = ExpressionEvaluator(values)
    return evaluator.visit(tree)


def load_species_names(species_header: Path) -> dict[int, str]:
    values: dict[str, int] = {}
    species_by_id: dict[int, str] = {}

    for line in species_header.read_text(encoding="utf-8").splitlines():
        match = DEFINE_RE.match(line)
        if not match:
            continue

        name = match.group("name")
        expression = match.group("expr").strip()

        try:
            value = evaluate_expression(expression, values)
        except (SyntaxError, ValueError, KeyError):
            continue

        values[name] = value
        if name.startswith("SPECIES_"):
            species_by_id[value] = name

    return species_by_id


def load_move_names(moves_header: Path) -> set[str]:
    move_names: set[str] = set()

    for line in moves_header.read_text(encoding="utf-8").splitlines():
        match = DEFINE_RE.match(line)
        if not match:
            continue
        name = match.group("name")
        if name.startswith("MOVE_"):
            move_names.add(name)

    return move_names


def normalize_move_name(move_name: str, valid_moves: set[str]) -> str:
    normalized = re.sub(r"\[[^\]]*\]", "", move_name).strip().upper()
    normalized = re.sub(r"^MOVE_", "", normalized)
    normalized = normalized.replace(".", "")
    normalized = normalized.replace("'", "")
    normalized = normalized.replace(":", "")
    normalized = re.sub(r"[^A-Z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    move = f"MOVE_{normalized}"
    if move in valid_moves:
        return move

    aliased = MOVE_ALIASES.get(move)
    if aliased and aliased in valid_moves:
        return aliased

    raise ValueError(f"Unknown move name from CSV: {move_name}")


def parse_level_moves(level_moves_text: str, valid_moves: set[str]) -> list[dict[str, object]]:
    level_moves: list[dict[str, object]] = []
    text = level_moves_text.strip()
    if not text:
        return level_moves

    for entry in text.split("|"):
        part = entry.strip()
        if not part:
            continue

        if "-" not in part:
            raise ValueError(f"Invalid level-up move entry: {part}")

        level_text, move_text = part.split("-", 1)
        level_moves.append(
            {
                "Level": int(level_text.strip()),
                "Move": normalize_move_name(move_text.strip(), valid_moves),
            }
        )

    return level_moves


def parse_move_list(
    moves_text: str,
    all_machine_moves: list[str],
    valid_moves: set[str],
) -> tuple[list[str], list[str]]:
    machine_moves: list[str] = []
    tutor_moves: list[str] = []
    text = moves_text.strip()
    if not text:
        return machine_moves, tutor_moves

    if text.upper() == "ALL TMS/HMS":
        return list(all_machine_moves), tutor_moves

    for entry in text.split("|"):
        part = entry.strip()
        if not part:
            continue

        if "-" not in part:
            raise ValueError(f"Invalid compatibility entry: {part}")

        prefix, move_text = part.split("-", 1)
        move_name = normalize_move_name(move_text.strip(), valid_moves)
        prefix = prefix.strip().upper()

        if prefix.startswith("TM") or prefix.startswith("HM"):
            machine_moves.append(move_name)
        elif prefix == "TUTOR":
            tutor_moves.append(move_name)
        else:
            raise ValueError(f"Unsupported compatibility prefix: {prefix}")

    return machine_moves, tutor_moves


def collect_all_machine_moves(learnsets: dict[str, object]) -> list[str]:
    machine_moves: set[str] = set()

    for entry in learnsets.values():
        if not isinstance(entry, dict):
            continue
        for move in entry.get("MachineMoves", []):
            if isinstance(move, str):
                machine_moves.add(move)

    return sorted(machine_moves)


def load_learnset_changes(
    csv_path: Path,
    species_by_id: dict[int, str],
    all_machine_moves: list[str],
    valid_moves: set[str],
) -> dict[str, dict[str, object]]:
    changes: dict[str, dict[str, object]] = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            species_id = int(row["ID"])
            species_name = species_by_id.get(species_id)
            if species_name is None:
                continue

            machine_moves, tutor_moves = parse_move_list(
                row["Tm compatibility"],
                all_machine_moves,
                valid_moves,
            )
            changes[species_name] = {
                "LevelMoves": parse_level_moves(row["Level-up moves"], valid_moves),
                "MachineMoves": machine_moves,
                "TutorMoves": tutor_moves,
            }

    return changes


def apply_learnset_changes(
    learnsets: dict[str, object],
    changes: dict[str, dict[str, object]],
) -> int:
    changed = 0

    for species_name, learnset_changes in changes.items():
        entry = learnsets.get(species_name)
        if not isinstance(entry, dict):
            continue

        species_changed = False
        for field in ("LevelMoves", "MachineMoves", "TutorMoves"):
            new_value = learnset_changes[field]
            if entry.get(field) != new_value:
                entry[field] = new_value
                species_changed = True

        if species_changed:
            changed += 1

    return changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" BlazeBlack2Redux Level-Up Moves")
    print("========================================")
    print("Applying level-up moves and TM compatibility from the CSV.\n")

    args = parse_args()
    species_by_id = load_species_names(args.species_header)
    valid_moves = load_move_names(args.moves_header)

    original = args.learnsets.read_text(encoding="utf-8")
    learnsets = json.loads(original)
    all_machine_moves = collect_all_machine_moves(learnsets)
    changes = load_learnset_changes(args.csv, species_by_id, all_machine_moves, valid_moves)
    changed = apply_learnset_changes(learnsets, changes)
    updated = json.dumps(learnsets, indent=2) + "\n"

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.learnsets.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Learnsets file  : {args.learnsets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
