#!/usr/bin/env python3
"""Randomize Pokemon abilities in armips/data/mondata.s."""

from __future__ import annotations

import argparse
import ast
import random
import re
from pathlib import Path

DEFAULT_MONDATA = Path("armips/data/mondata.s")
DEFAULT_ABILITY_HEADER = Path("include/constants/ability.h")
DEFAULT_BACKUP = Path("bak/mondata.s.bak")
DEFAULT_MIN = 1
DEFAULT_MAX = 310

DEFINE_RE = re.compile(r"^\s*#define\s+(?P<name>[A-Z0-9_]+)\s+(?P<expr>.+?)\s*(?://.*)?$")
ABILITIES_LINE_RE = re.compile(r"^(?P<prefix>\s*abilities\s+)(?P<body>.+?)(?P<suffix>\s*(?://.*)?)$")
ABILITY_TOKEN_RE = re.compile(r"\bABILITY_[A-Z0-9_]+\b")


class ExpressionEvaluator(ast.NodeVisitor):
    """Evaluate simple integer expressions used in ability defines."""

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
            "Randomize Pokemon abilities in armips/data/mondata.s using "
            "ability IDs from include/constants/ability.h."
        )
    )
    parser.add_argument("--min", dest="min_ability", type=int, help="Lowest allowed ability ID.")
    parser.add_argument("--max", dest="max_ability", type=int, help="Highest allowed ability ID.")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible results.",
    )
    parser.add_argument(
        "--mondata",
        type=Path,
        default=DEFAULT_MONDATA,
        help=f"Mondata file to edit (default: {DEFAULT_MONDATA}).",
    )
    parser.add_argument(
        "--ability-header",
        type=Path,
        default=DEFAULT_ABILITY_HEADER,
        help=f"Ability header to read (default: {DEFAULT_ABILITY_HEADER}).",
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
    min_ability = args.min_ability if args.min_ability is not None else ask_for_int("ABILITY_MIN", DEFAULT_MIN)
    max_ability = args.max_ability if args.max_ability is not None else ask_for_int("ABILITY_MAX", DEFAULT_MAX)
    if min_ability > max_ability:
        raise ValueError(f"ABILITY_MIN ({min_ability}) cannot be greater than ABILITY_MAX ({max_ability}).")
    return min_ability, max_ability


def evaluate_expression(expression: str, values: dict[str, int]) -> int:
    tree = ast.parse(expression, mode="eval")
    evaluator = ExpressionEvaluator(values)
    return evaluator.visit(tree)


def load_ability_map(ability_header: Path) -> dict[int, str]:
    values: dict[str, int] = {}
    abilities_by_id: dict[int, str] = {}

    for line in ability_header.read_text(encoding="utf-8").splitlines():
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
        if name.startswith("ABILITY_"):
            abilities_by_id[value] = name

    return abilities_by_id


def build_allowed_abilities(abilities_by_id: dict[int, str], min_ability: int, max_ability: int) -> list[str]:
    allowed = [
        ability_name
        for ability_id, ability_name in sorted(abilities_by_id.items())
        if min_ability <= ability_id <= max_ability and ability_name != "ABILITY_NONE"
    ]
    if not allowed:
        raise ValueError("No valid abilities found in the requested range.")
    return allowed


def randomize_abilities(text: str, allowed_abilities: list[str], rng: random.Random) -> tuple[str, int]:
    changed = 0
    updated_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line

        abilities_match = ABILITIES_LINE_RE.match(body)
        if abilities_match:
            line_changed = 0

            def replace_ability(match: re.Match[str]) -> str:
                nonlocal line_changed
                original = match.group(0)
                if original == "ABILITY_NONE":
                    return original
                line_changed += 1
                return rng.choice(allowed_abilities)

            replaced_body = ABILITY_TOKEN_RE.sub(replace_ability, abilities_match.group("body"))
            body = f"{abilities_match.group('prefix')}{replaced_body}{abilities_match.group('suffix')}"
            changed += line_changed
            updated_lines.append(body + newline)
            continue

        updated_lines.append(line)

    return "".join(updated_lines), changed


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8")


def main() -> int:
    print("========================================")
    print(" Ability Randomizer")
    print("========================================")
    print("Choose the ability ID range to use.\n")

    args = parse_args()
    min_ability, max_ability = resolve_range(args)
    abilities_by_id = load_ability_map(args.ability_header)
    allowed_abilities = build_allowed_abilities(abilities_by_id, min_ability, max_ability)

    rng = random.Random(args.seed)
    original = args.mondata.read_text(encoding="utf-8")
    updated, changed = randomize_abilities(original, allowed_abilities, rng)

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
