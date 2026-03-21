#!/usr/bin/env python3
from __future__ import annotations

import math
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


FULL_TEMPLATE_FLAGS = [
    "TRAINER_DATA_TYPE_ITEMS",
    "TRAINER_DATA_TYPE_MOVES",
    "TRAINER_DATA_TYPE_ABILITY",
    "TRAINER_DATA_TYPE_BALL",
    "TRAINER_DATA_TYPE_IV_EV_SET",
    "TRAINER_DATA_TYPE_NATURE_SET",
    "TRAINER_DATA_TYPE_SHINY_LOCK",
]

SPECIAL_FORM_RANGES = {
    "SPECIES_DEOXYS": (3, 495),
    "SPECIES_WORMADAM": (2, 498),
    "SPECIES_GIRATINA": (1, 500),
    "SPECIES_SHAYMIN": (1, 501),
    "SPECIES_ROTOM": (5, 502),
}

KNOWN_MON_FIELDS = {
    "ivs",
    "abilityslot",
    "level",
    "pokemon",
    "monwithform",
    "item",
    "move",
    "ability",
    "ball",
    "setivs",
    "setevs",
    "nature",
    "shinylock",
    "additionalflags",
    "status",
    "stathp",
    "statatk",
    "statdef",
    "statspeed",
    "statspatk",
    "statspdef",
    "types",
    "ppcounts",
    "nickname",
    "ballseal",
}

MON_FIELD_ORDER = [
    "ivs",
    "abilityslot",
    "level",
    "pokemon",
    "monwithform",
    "item",
    "move",
    "ability",
    "ball",
    "setivs",
    "setevs",
    "nature",
    "shinylock",
    "additionalflags",
    "status",
    "stathp",
    "statatk",
    "statdef",
    "statspeed",
    "statspatk",
    "statspdef",
    "types",
    "ppcounts",
    "nickname",
    "ballseal",
]


class ParseError(RuntimeError):
    pass


@dataclass
class MonEntry:
    fields: dict[str, str] = field(default_factory=dict)
    moves: list[str] = field(default_factory=list)


@dataclass
class TrainerEntry:
    trainer_id: int
    name: str
    trainermontype_flags: list[str]
    trainerclass: str
    nummons: int
    nummons_expr: str
    items: list[str]
    aiflags: str
    battletype: str
    mons: list[MonEntry]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def strip_inline_comment(line: str) -> str:
    return line.split("//", 1)[0].rstrip()


def parse_numeric(raw: str, context: str) -> int:
    try:
        return int(raw.strip(), 0)
    except ValueError as exc:
        raise ParseError(f"Expected numeric value for {context}, got {raw!r}") from exc


def parse_nummons(raw: str) -> tuple[str, int]:
    expr = raw.strip()
    match = re.fullmatch(r"(?:(?:0x80\s*\|\s*)?)(\d+)", expr)
    if not match:
        raise ParseError(f"Expected nummons value, got {raw!r}")
    return expr, int(match.group(1), 0)


def ceil_iv_scale(ivs: int) -> int:
    if ivs < 0 or ivs > 255:
        raise ParseError(f"IV byte must be between 0 and 255, got {ivs}")
    return math.ceil(ivs * 31 / 255)


def parse_species_constants(species_header_path: Path) -> tuple[dict[str, int], dict[int, str]]:
    name_to_num: dict[str, int] = {}
    num_to_name: dict[int, str] = {}
    pattern = re.compile(r"#define\s+(SPECIES_[A-Z0-9_]+)\s+([0-9]+)")

    for line in species_header_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        name = match.group(1)
        value = int(match.group(2))
        name_to_num[name] = value
        num_to_name[value] = name

    if not name_to_num:
        raise ParseError(f"Could not parse species constants from {species_header_path}")
    return name_to_num, num_to_name


def parse_mondata_abilities(mondata_path: Path) -> dict[str, tuple[str, str]]:
    abilities_by_species: dict[str, tuple[str, str]] = {}
    current_species: str | None = None
    mondata_pattern = re.compile(r"mondata\s+(SPECIES_[A-Z0-9_]+),")
    abilities_pattern = re.compile(r"abilities\s+([^,]+),\s*(\S+)")

    for raw_line in mondata_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line).strip()
        if not line:
            continue

        mon_match = mondata_pattern.match(line)
        if mon_match:
            current_species = mon_match.group(1)
            continue

        if current_species is None:
            continue

        ability_match = abilities_pattern.match(line)
        if ability_match:
            abilities_by_species[current_species] = (
                ability_match.group(1).strip(),
                ability_match.group(2).strip(),
            )
            current_species = None

    if not abilities_by_species:
        raise ParseError(f"Could not parse mondata abilities from {mondata_path}")
    return abilities_by_species


def parse_hidden_abilities(hidden_ability_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    pattern = re.compile(r"\[\s*(SPECIES_[A-Z0-9_]+)\s*\]\s*=\s*(ABILITY_[A-Z0-9_]+)")

    for raw_line in hidden_ability_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line).strip()
        match = pattern.search(line)
        if match:
            mapping[match.group(1)] = match.group(2)

    if not mapping:
        raise ParseError(f"Could not parse hidden ability table from {hidden_ability_path}")
    return mapping


def parse_natures(constants_path: Path) -> list[str]:
    names_by_index: dict[int, str] = {}
    pattern = re.compile(r"\.equ\s+(NATURE_[A-Z0-9_]+),\s*\((\d+)\)")

    for raw_line in constants_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line).strip()
        match = pattern.match(line)
        if match:
            names_by_index[int(match.group(2))] = match.group(1)

    if len(names_by_index) != 25:
        raise ParseError(f"Expected 25 natures in {constants_path}, found {len(names_by_index)}")
    return [names_by_index[idx] for idx in sorted(names_by_index)]


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


def parse_flag_list(raw_flags: str) -> list[str]:
    flags: list[str] = []
    for token in (part.strip() for part in raw_flags.split("|")):
        if not token or token == "0" or token == "TRAINER_DATA_TYPE_NOTHING":
            continue
        flags.append(token)
    return flags


def parse_monwithform(raw_value: str) -> tuple[str, int]:
    match = re.fullmatch(r"(SPECIES_[A-Z0-9_]+)\s*,\s*([0-9]+)", raw_value.strip())
    if not match:
        raise ParseError(f"Invalid monwithform value: {raw_value!r}")
    return match.group(1), int(match.group(2), 0)


def parse_pokemon_ref(mon: MonEntry) -> tuple[str, int]:
    if "pokemon" in mon.fields:
        return mon.fields["pokemon"].strip(), 0
    if "monwithform" in mon.fields:
        return parse_monwithform(mon.fields["monwithform"])
    raise ParseError("Mon is missing pokemon/monwithform field")


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
                raise ParseError(f"Could not resolve adjusted species number {adjusted_num} for {base_species} form {form_no}")
            return adjusted_species

    entries = form_table.get(base_species, [])
    if 0 < form_no <= len(entries):
        return entries[form_no - 1]

    if base_species not in species_name_to_num:
        raise ParseError(f"Unknown species constant {base_species}")
    return base_species


def resolve_ability_for_mon(
    mon: MonEntry,
    abilities_by_species: dict[str, tuple[str, str]],
    hidden_abilities: dict[str, str],
    species_name_to_num: dict[str, int],
    species_num_to_name: dict[int, str],
    form_table: dict[str, list[str]],
) -> str:
    base_species, form_no = parse_pokemon_ref(mon)
    adjusted_species = resolve_form_species(
        base_species,
        form_no,
        species_name_to_num,
        species_num_to_name,
        form_table,
    )

    try:
        ability1, ability2 = abilities_by_species[adjusted_species]
    except KeyError as exc:
        raise ParseError(f"Could not resolve regular abilities for {adjusted_species}") from exc

    abilityslot = parse_numeric(mon.fields["abilityslot"], "abilityslot")
    if abilityslot == 2:
        try:
            return hidden_abilities[adjusted_species]
        except KeyError as exc:
            raise ParseError(f"Could not resolve hidden ability for {adjusted_species}") from exc

    if abilityslot == 32 or (abilityslot & 1):
        return ability2 if ability2 != "ABILITY_NONE" else ability1

    return ability1


def synthesize_trainermontype(flags: list[str]) -> str:
    rendered = list(FULL_TEMPLATE_FLAGS)
    for flag in flags:
        if flag not in rendered:
            rendered.append(flag)
    return " | ".join(rendered + ["0"])


def parse_trainer_entries(trainer_s_path: Path) -> tuple[list[str], list[TrainerEntry]]:
    lines = trainer_s_path.read_text(encoding="utf-8").splitlines()
    preamble: list[str] = []
    trainers: list[TrainerEntry] = []
    idx = 0

    while idx < len(lines) and not lines[idx].strip().startswith("trainerdata"):
        preamble.append(lines[idx])
        idx += 1

    while idx < len(lines):
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        if idx >= len(lines):
            break

        trainer_line = strip_inline_comment(lines[idx]).strip()
        trainer_match = re.fullmatch(r'trainerdata\s+([0-9]+),\s*"([^"]*)"', trainer_line)
        if not trainer_match:
            raise ParseError(f"Expected trainerdata line at {idx + 1}, got {lines[idx]!r}")

        trainer_id = int(trainer_match.group(1))
        name = trainer_match.group(2)
        idx += 1

        trainermontype_flags: list[str] = []
        trainerclass: str | None = None
        nummons: int | None = None
        nummons_expr: str | None = None
        trainer_items: list[str] = []
        aiflags: str | None = None
        battletype: str | None = None

        while idx < len(lines):
            stripped = strip_inline_comment(lines[idx]).strip()
            idx += 1

            if not stripped:
                continue
            if stripped == "endentry":
                break
            if stripped.startswith("trainermontype "):
                trainermontype_flags = parse_flag_list(stripped[len("trainermontype "):])
                continue
            if stripped.startswith("trainerclass "):
                trainerclass = stripped[len("trainerclass "):].strip()
                continue
            if stripped.startswith("nummons "):
                nummons_expr, nummons = parse_nummons(stripped[len("nummons "):])
                continue
            if stripped.startswith("item "):
                trainer_items.append(stripped[len("item "):].strip())
                continue
            if stripped.startswith("aiflags "):
                aiflags = stripped[len("aiflags "):].strip()
                continue
            if stripped.startswith("battletype "):
                battletype = stripped[len("battletype "):].strip()
                continue

            raise ParseError(f"Unexpected trainer field on line {idx}: {stripped}")

        if trainerclass is None or nummons is None or nummons_expr is None or aiflags is None or battletype is None:
            raise ParseError(f"Trainer {trainer_id} is missing required trainerdata fields")

        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        if idx >= len(lines):
            raise ParseError(f"Trainer {trainer_id} is missing its party block")

        party_line = strip_inline_comment(lines[idx]).strip()
        party_match = re.fullmatch(r"party\s+([0-9]+)", party_line)
        if not party_match:
            raise ParseError(f"Expected party block for trainer {trainer_id} at line {idx + 1}, got {lines[idx]!r}")
        party_id = int(party_match.group(1))
        if party_id != trainer_id:
            raise ParseError(f"Trainerdata id {trainer_id} does not match party id {party_id}")
        idx += 1

        mons: list[MonEntry] = []
        current_mon: MonEntry | None = None

        while idx < len(lines):
            raw_line = lines[idx]
            stripped = strip_inline_comment(raw_line).strip()
            idx += 1

            if not stripped:
                continue
            if stripped == "endparty":
                if current_mon is not None:
                    mons.append(current_mon)
                current_mon = None
                break
            if stripped.startswith("//"):
                continue
            if stripped.startswith("ivs "):
                if current_mon is not None:
                    mons.append(current_mon)
                current_mon = MonEntry(fields={"ivs": stripped[len("ivs "):].strip()})
                continue

            if current_mon is None:
                continue

            parts = stripped.split(None, 1)
            if len(parts) != 2:
                raise ParseError(f"Unexpected mon line at {idx}: {stripped}")
            key, value = parts[0], parts[1].strip()
            if key not in KNOWN_MON_FIELDS:
                raise ParseError(f"Unknown mon field {key!r} on line {idx}")
            if key == "move":
                current_mon.moves.append(value)
                continue
            if key in current_mon.fields:
                raise ParseError(f"Duplicate mon field {key!r} on line {idx}")
            current_mon.fields[key] = value

        if len(trainer_items) > 4:
            raise ParseError(f"Trainer {trainer_id} has more than 4 trainer items")
        while len(trainer_items) < 4:
            trainer_items.append("ITEM_NONE")

        trainers.append(
            TrainerEntry(
                trainer_id=trainer_id,
                name=name,
                trainermontype_flags=trainermontype_flags,
                trainerclass=trainerclass,
                nummons=nummons,
                nummons_expr=nummons_expr,
                items=trainer_items,
                aiflags=aiflags,
                battletype=battletype,
                mons=mons,
            )
        )

    return preamble, trainers


def enrich_mon(
    mon: MonEntry,
    nature_names: list[str],
    abilities_by_species: dict[str, tuple[str, str]],
    hidden_abilities: dict[str, str],
    species_name_to_num: dict[str, int],
    species_num_to_name: dict[int, str],
    form_table: dict[str, list[str]],
) -> None:
    required_base_fields = ["ivs", "abilityslot", "level", "ballseal"]
    for field_name in required_base_fields:
        if field_name not in mon.fields:
            raise ParseError(f"Mon is missing required field {field_name}")
    if "pokemon" not in mon.fields and "monwithform" not in mon.fields:
        raise ParseError("Mon is missing pokemon/monwithform field")

    if "item" not in mon.fields:
        mon.fields["item"] = "ITEM_NONE"

    if len(mon.moves) > 4:
        raise ParseError("Mon has more than 4 move entries")
    while len(mon.moves) < 4:
        mon.moves.append("MOVE_NONE")

    if "ability" not in mon.fields:
        mon.fields["ability"] = resolve_ability_for_mon(
            mon,
            abilities_by_species,
            hidden_abilities,
            species_name_to_num,
            species_num_to_name,
            form_table,
        )

    if "ball" not in mon.fields:
        mon.fields["ball"] = "ITEM_POKE_BALL"

    if "setivs" not in mon.fields:
        ivs = parse_numeric(mon.fields["ivs"], "ivs")
        scaled = ceil_iv_scale(ivs)
        mon.fields["setivs"] = ", ".join([str(scaled)] * 6)

    if "setevs" not in mon.fields:
        mon.fields["setevs"] = "0, 0, 0, 0, 0, 0"

    if "nature" not in mon.fields:
        mon.fields["nature"] = random.choice(nature_names)

    if "shinylock" not in mon.fields:
        mon.fields["shinylock"] = "1" if random.randrange(512) == 0 else "0"


def render_mon(mon: MonEntry, index: int) -> list[str]:
    lines = [f"        // mon {index}"]
    for field_name in MON_FIELD_ORDER:
        if field_name == "move":
            for move in mon.moves:
                lines.append(f"        move {move}")
            continue
        value = mon.fields.get(field_name)
        if value is not None:
            lines.append(f"        {field_name} {value}")
    return lines


def render_trainers(preamble: list[str], trainers: list[TrainerEntry]) -> str:
    output_lines = list(preamble)
    if output_lines and output_lines[-1].strip():
        output_lines.append("")

    for trainer in trainers:
        output_lines.append(f'trainerdata {trainer.trainer_id}, "{trainer.name}"')
        output_lines.append(f"    trainermontype {synthesize_trainermontype(trainer.trainermontype_flags)}")
        output_lines.append(f"    trainerclass {trainer.trainerclass}")
        output_lines.append(f"    nummons {trainer.nummons_expr}")
        for item in trainer.items[:4]:
            output_lines.append(f"    item {item}")
        output_lines.append(f"    aiflags {trainer.aiflags}")
        output_lines.append(f"    battletype {trainer.battletype}")
        output_lines.append("    endentry")
        output_lines.append("")
        output_lines.append(f"    party {trainer.trainer_id}")
        for index, mon in enumerate(trainer.mons):
            if index:
                output_lines.append("")
            output_lines.extend(render_mon(mon, index))
        output_lines.append("    endparty")
        output_lines.append("")

    return "\n".join(output_lines).rstrip() + "\n"


def default_input_path() -> Path:
    return repo_root() / "armips" / "data" / "trainers" / "trainers.s"


def default_backup_path() -> Path:
    return repo_root() / "bak" / "trainers.s.bak"


def write_backup(source_text: str, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(source_text, encoding="utf-8", newline="\n")


def ask_mode() -> int:
    print("========================================")
    print(" Generalize Trainers")
    print("========================================")
    print("This script rewrites trainers.s in-place to use the generalized full-template trainer format.")
    print("It fills missing template fields such as items, abilities, balls, IV/EV sets, natures, and shiny lock.\n")
    print("0 = abort")
    print("1 = apply template and create bak/trainers.s.bak")
    print("2 = apply template without bak")

    while True:
        choice = input("Choice: ").strip() or "0"
        if choice in {"0", "1", "2"}:
            return int(choice)
        print("Invalid choice. Use 0, 1, or 2.")


def main() -> int:
    input_path = default_input_path().resolve()
    backup_path = default_backup_path().resolve()
    mode = ask_mode()

    if mode == 0:
        print("Aborted.")
        return 0

    root = repo_root()
    species_header = root / "include" / "constants" / "species.h"
    mondata_path = root / "armips" / "data" / "mondata.s"
    hidden_ability_path = root / "data" / "HiddenAbilityTable.c"
    nature_constants_path = root / "armips" / "include" / "constants.s"
    form_table_path = root / "data" / "PokeFormDataTbl.c"

    try:
        original = input_path.read_text(encoding="utf-8")
        species_name_to_num, species_num_to_name = parse_species_constants(species_header)
        abilities_by_species = parse_mondata_abilities(mondata_path)
        hidden_abilities = parse_hidden_abilities(hidden_ability_path)
        nature_names = parse_natures(nature_constants_path)
        form_table = parse_form_table(form_table_path)
        preamble, trainers = parse_trainer_entries(input_path)

        for trainer in trainers:
            if trainer.trainer_id != 0 and len(trainer.mons) != trainer.nummons:
                raise ParseError(
                    f"Trainer {trainer.trainer_id} nummons is {trainer.nummons}, but parsed {len(trainer.mons)} mons"
                )
            for mon in trainer.mons:
                enrich_mon(
                    mon,
                    nature_names,
                    abilities_by_species,
                    hidden_abilities,
                    species_name_to_num,
                    species_num_to_name,
                    form_table,
                )

        updated = render_trainers(preamble, trainers)
        if mode == 1 and updated != original:
            print(f"\nCreating backup: {backup_path.relative_to(root)}")
            write_backup(original, backup_path)
        input_path.write_text(updated, encoding="utf-8", newline="\n")
    except ParseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print()
    print("Done.")
    print(f"  Trainers file   : {input_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
