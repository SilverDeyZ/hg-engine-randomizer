#!/usr/bin/env python3
"""Apply item drops from scripts_custom/Data/megapokemondrops.csv to mondata.s."""

from __future__ import annotations

import argparse
import ast
import csv
import re
from pathlib import Path

DEFAULT_MONDATA = Path("armips/data/mondata.s")
DEFAULT_SPECIES_HEADER = Path("include/constants/species.h")
DEFAULT_DROPS_CSV = Path("scripts_custom/Data/megapokemondrops.csv")
DEFAULT_BACKUP = Path("bak/mondata.s.bak")
ITEM_ALIASES = {
    "ITEM_SABLEYITE": "ITEM_SABLENITE",
}

DEFINE_RE = re.compile(r"^\s*#define\s+(?P<name>[A-Z0-9_]+)\s+(?P<expr>.+?)\s*(?://.*)?$")
MONDATA_RE = re.compile(r'^\s*mondata\s+(?P<species>SPECIES_[A-Z0-9_]+)\s*,')
ITEMS_RE = re.compile(
    r"^(?P<indent>\s*)items\s+(?P<first>ITEM_[A-Z0-9_]+)\s*,\s*(?P<second>ITEM_[A-Z0-9_]+)(?P<suffix>\s*(?://.*)?)$"
)


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
        description="Apply item drops from scripts_custom/Data/megapokemondrops.csv to armips/data/mondata.s."
    )
    parser.add_argument(
        "--mondata",
        type=Path,
        default=DEFAULT_MONDATA,
        help=f"Mondata file to edit (default: {DEFAULT_MONDATA}).",
    )
    parser.add_argument(
        "--species-header",
        type=Path,
        default=DEFAULT_SPECIES_HEADER,
        help=f"Species header to read (default: {DEFAULT_SPECIES_HEADER}).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_DROPS_CSV,
        help=f"CSV file to read (default: {DEFAULT_DROPS_CSV}).",
    )
    return parser.parse_args()


def evaluate_expression(expression: str, values: dict[str, int]) -> int:
    tree = ast.parse(expression, mode="eval")
    evaluator = ExpressionEvaluator(values)
    return evaluator.visit(tree)


def load_species_ids(species_header: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    species_ids: dict[str, int] = {}

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
            species_ids[name] = value

    return species_ids


def load_drop_map(csv_path: Path) -> dict[int, tuple[str, str]]:
    drop_map: dict[int, tuple[str, str]] = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            species_id = int(row["id"])
            drop1 = ITEM_ALIASES.get(row["drop1"].strip(), row["drop1"].strip())
            drop2 = ITEM_ALIASES.get(row["drop2"].strip(), row["drop2"].strip())
            drop_map[species_id] = (drop1, drop2)

    return drop_map


def apply_drops(
    text: str,
    species_ids: dict[str, int],
    drop_map: dict[int, tuple[str, str]],
) -> tuple[str, int]:
    updated_lines: list[str] = []
    changed = 0
    current_species_id: int | None = None

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line

        mondata_match = MONDATA_RE.match(body)
        if mondata_match:
            species_name = mondata_match.group("species")
            current_species_id = species_ids.get(species_name)
            updated_lines.append(line)
            continue

        items_match = ITEMS_RE.match(body)
        if items_match and current_species_id in drop_map:
            drop1, drop2 = drop_map[current_species_id]
            updated_body = (
                f"{items_match.group('indent')}items {drop1}, {drop2}"
                f"{items_match.group('suffix')}"
            )
            if updated_body != body:
                changed += 1
            updated_lines.append(updated_body + newline)
            continue

        updated_lines.append(line)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Mega Pokemon Drops")
    print("========================================")
    print("Applying drops from scripts_custom/Data/megapokemondrops.csv.\n")

    args = parse_args()
    species_ids = load_species_ids(args.species_header)
    drop_map = load_drop_map(args.csv)

    original = args.mondata.read_text(encoding="utf-8")
    updated, changed = apply_drops(original, species_ids, drop_map)

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
