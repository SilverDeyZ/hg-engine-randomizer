# scripts_custom

This folder groups the custom helper scripts used to edit, reorder, randomize, or apply data changes to the project.

## Folder overview

## Data

Contains CSV files and other input data used by the scripts.

Examples:
- encounter accessibility order lists
- trainer accessibility order lists
- imported ROM hack change tables

## scripts_randomizer

Contains scripts that randomize gameplay data.

Typical use cases:
- random wild encounters
- random trainer species
- random starters
- random abilities
- random types

## scripts_multipliers

Contains scripts that multiply, divide, enable, disable, or scale existing values.

Typical use cases:
- catch rate scaling
- egg cycle scaling
- EV gain control
- trainer level scaling
- encounter level scaling
- encounter rate scaling

## scripts_mods

Contains standalone project modification scripts.

These are usually used to install or remove a custom feature rather than randomize or scale data.

Current examples:
- `apply_mega_pokemon_drops.py`
- `pc_anywhere_manager.py`
- `set_red_aiflags.py`

## scripts_format

Contains scripts that reformat or reorder structured project files.

Typical use cases:
- expanding trainer blocks to a more configurable format
- filling trainer movesets after trainer expansion
- rerolling trainer nature and shiny data
- reordering encounter blocks
- reordering trainer blocks

## scripts_romhack

Contains import/apply scripts for ROM hack data conversions.

These scripts usually read an external CSV and apply its data to the current project format.

Typical use cases:
- apply BlazeBlack2Redux move changes
- apply mondata changes
- apply hidden abilities
- apply evolution changes

## Other files

## __main__.py

Allows launching supported helper scripts with:

```bash
python3 scripts_custom <script_name>
```

instead of always typing the full path.

## __pycache__

Python cache folder generated automatically by Python.
