#!/usr/bin/env python3
"""Apply BlazeBlack2Redux hidden abilities to data/HiddenAbilityTable.c."""

from __future__ import annotations

import argparse
import ast
import csv
import re
from pathlib import Path

DEFAULT_TABLE = Path("data/HiddenAbilityTable.c")
DEFAULT_SPECIES_HEADER = Path("include/constants/species.h")
DEFAULT_ABILITY_HEADER = Path("include/constants/ability.h")
DEFAULT_CHANGES_CSV = Path("scripts_custom/Data/BlazeBlack2Redux_mondata_changes.csv")
DEFAULT_BACKUP = Path("bak/HiddenAbilityTable.c.bak")

ABILITY_ALIASES = {
    "ABILITY_SYNCHRONISE": "ABILITY_SYNCHRONIZE",
    "ABILITY_LIGHTNINGROD": "ABILITY_LIGHTNING_ROD",
}

DEFINE_RE = re.compile(r"^\s*#define\s+(?P<name>[A-Z0-9_]+)\s+(?P<expr>.+?)\s*(?://.*)?$")
TABLE_ENTRY_RE = re.compile(
    r"^(?P<indent>\s*)\[(?P<species>SPECIES_[A-Z0-9_]+)\s*\]\s*=\s*(?P<ability>ABILITY_[A-Z0-9_]+)(?P<suffix>\s*,\s*(?://.*)?)$"
)


class ExpressionEvaluator(ast.NodeVisitor):
    """Evaluate simple integer expressions used in headers."""

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
            "Apply hidden abilities from BlazeBlack2Redux_mondata_changes.csv "
            "to data/HiddenAbilityTable.c."
        )
    )
    parser.add_argument(
        "--table",
        type=Path,
        default=DEFAULT_TABLE,
        help=f"Hidden ability table to edit (default: {DEFAULT_TABLE}).",
    )
    parser.add_argument(
        "--species-header",
        type=Path,
        default=DEFAULT_SPECIES_HEADER,
        help=f"Species header to read (default: {DEFAULT_SPECIES_HEADER}).",
    )
    parser.add_argument(
        "--ability-header",
        type=Path,
        default=DEFAULT_ABILITY_HEADER,
        help=f"Ability header to read (default: {DEFAULT_ABILITY_HEADER}).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CHANGES_CSV,
        help=f"CSV file to read (default: {DEFAULT_CHANGES_CSV}).",
    )
    return parser.parse_args()


def evaluate_expression(expression: str, values: dict[str, int]) -> int:
    tree = ast.parse(expression, mode="eval")
    evaluator = ExpressionEvaluator(values)
    return evaluator.visit(tree)


def load_named_ids(header_path: Path, prefix: str) -> dict[str, int]:
    values: dict[str, int] = {}
    named_ids: dict[str, int] = {}

    for line in header_path.read_text(encoding="utf-8").splitlines():
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
        if name.startswith(prefix):
            named_ids[name] = value

    return named_ids


def normalize_ability_name(name: str) -> str:
    normalized = name.strip()
    if not normalized or normalized == "-":
        return "ABILITY_NONE"

    normalized = normalized.upper()
    normalized = normalized.replace(".", "")
    normalized = normalized.replace("'", "")
    normalized = re.sub(r"[^A-Z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    ability_name = f"ABILITY_{normalized}"
    return ABILITY_ALIASES.get(ability_name, ability_name)


def load_hidden_ability_changes(csv_path: Path, valid_abilities: set[str]) -> dict[int, str]:
    changes: dict[int, str] = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_hidden = row["HiddenAbility3"].strip()
            if not raw_hidden:
                continue

            hidden_ability = normalize_ability_name(raw_hidden)
            if hidden_ability not in valid_abilities:
                raise ValueError(f"Unknown hidden ability from CSV: {row['HiddenAbility3']}")

            species_id = int(row["ID"])
            changes[species_id] = hidden_ability

    return changes


def apply_hidden_ability_changes(
    text: str,
    species_ids: dict[str, int],
    changes: dict[int, str],
) -> tuple[str, int]:
    updated_lines: list[str] = []
    changed = 0

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = TABLE_ENTRY_RE.match(body)

        if not match:
            updated_lines.append(line)
            continue

        species_name = match.group("species")
        species_id = species_ids.get(species_name)
        if species_id is None or species_id not in changes:
            updated_lines.append(line)
            continue

        updated_body = (
            f"{match.group('indent')}[{species_name:<36}] = {changes[species_id]}"
            f"{match.group('suffix')}"
        )
        if updated_body != body:
            changed += 1
        updated_lines.append(updated_body + newline)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" BlazeBlack2Redux Hidden Abilities")
    print("========================================")
    print("Applying HiddenAbility3 values from the CSV.\n")

    args = parse_args()
    species_ids = load_named_ids(args.species_header, "SPECIES_")
    ability_ids = load_named_ids(args.ability_header, "ABILITY_")
    changes = load_hidden_ability_changes(args.csv, set(ability_ids))

    original = args.table.read_text(encoding="utf-8")
    updated, changed = apply_hidden_ability_changes(original, species_ids, changes)

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.table.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Hidden table    : {args.table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
