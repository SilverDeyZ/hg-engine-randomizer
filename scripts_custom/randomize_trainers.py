#!/usr/bin/env python3
"""Randomize trainer party species in armips/data/trainers/trainers.s."""

from __future__ import annotations

import argparse
import ast
import random
import re
from pathlib import Path

DEFAULT_TRAINERS = Path("armips/data/trainers/trainers.s")
DEFAULT_SPECIES_HEADER = Path("include/constants/species.h")
DEFAULT_BACKUP = Path("bak/trainers.s.bak")
DEFAULT_MIN = 1
DEFAULT_MAX = 1075
EXCLUDED_IDS = set(range(494, 545))

DEFINE_RE = re.compile(r"^\s*#define\s+(?P<name>[A-Z0-9_]+)\s+(?P<expr>.+?)\s*(?://.*)?$")
POKEMON_RE = re.compile(r"^(?P<prefix>\s*pokemon\s+)(?P<species>SPECIES_[A-Z0-9_]+)(?P<suffix>\s*(?://.*)?)$")


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
            "Randomize trainer party species in armips/data/trainers/trainers.s using "
            "species IDs from include/constants/species.h."
        )
    )
    parser.add_argument("--min", dest="min_species", type=int, help="Lowest allowed species ID.")
    parser.add_argument("--max", dest="max_species", type=int, help="Highest allowed species ID.")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible results.",
    )
    parser.add_argument(
        "--trainers",
        type=Path,
        default=DEFAULT_TRAINERS,
        help=f"Trainer file to edit (default: {DEFAULT_TRAINERS}).",
    )
    parser.add_argument(
        "--species-header",
        type=Path,
        default=DEFAULT_SPECIES_HEADER,
        help=f"Species header to read (default: {DEFAULT_SPECIES_HEADER}).",
    )
    return parser.parse_args()


def ask_for_int(label: str, default: int) -> int:
    while True:
        raw = input(f"  - {label:<12} [{default}] : ").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print(f"    Invalid value. Please enter a whole number for {label}.")


def resolve_range(args: argparse.Namespace) -> tuple[int, int]:
    min_species = args.min_species if args.min_species is not None else ask_for_int("POKEMON_MIN", DEFAULT_MIN)
    max_species = args.max_species if args.max_species is not None else ask_for_int("POKEMON_MAX", DEFAULT_MAX)
    if min_species > max_species:
        raise ValueError(f"POKEMON_MIN ({min_species}) cannot be greater than POKEMON_MAX ({max_species}).")
    return min_species, max_species


def evaluate_expression(expression: str, values: dict[str, int]) -> int:
    tree = ast.parse(expression, mode="eval")
    evaluator = ExpressionEvaluator(values)
    return evaluator.visit(tree)


def load_species_map(species_header: Path) -> dict[int, str]:
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


def build_allowed_species(species_by_id: dict[int, str], min_species: int, max_species: int) -> list[str]:
    allowed = [
        species_name
        for species_id, species_name in sorted(species_by_id.items())
        if min_species <= species_id <= max_species
        and species_id not in EXCLUDED_IDS
        and species_name != "SPECIES_NONE"
    ]
    if not allowed:
        raise ValueError(
            "No valid species found in the requested range after excluding IDs 494 to 544."
        )
    return allowed


def randomize_trainers(text: str, allowed_species: list[str], rng: random.Random) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line

        pokemon_match = POKEMON_RE.match(body)
        if pokemon_match:
            original = pokemon_match.group("species")
            if original != "SPECIES_NONE":
                replacement = rng.choice(allowed_species)
                body = f"{pokemon_match.group('prefix')}{replacement}{pokemon_match.group('suffix')}"
                changed += 1
            updated_lines.append(body + newline)
            continue

        updated_lines.append(line)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Trainer Party Randomizer")
    print("========================================")
    print("Choose the species ID range to use.\n")

    args = parse_args()
    min_species, max_species = resolve_range(args)
    species_by_id = load_species_map(args.species_header)
    allowed_species = build_allowed_species(species_by_id, min_species, max_species)

    rng = random.Random(args.seed)
    original = args.trainers.read_text(encoding="utf-8")
    updated, changed = randomize_trainers(original, allowed_species, rng)

    if updated != original:
        print(f"\nCreating backup: {DEFAULT_BACKUP}")
        write_backup(original, DEFAULT_BACKUP)
        args.trainers.write_text(updated, encoding="utf-8")

    print()
    print("Done.")
    print(f"  Updated entries : {changed}")
    print(f"  Trainers file   : {args.trainers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
