# Randomizer Guide

This project includes a small set of Python scripts in `scripts_custom/scripts_randomizer` to randomize key Pokemon data directly inside the project files.

These scripts are useful if you want to quickly reshuffle wild Pokemon, trainer teams, starters, abilities, or types without editing each file manually.

Most of them:
- ask for values directly in the terminal
- edit the real project files in-place
- create a backup in the `bak` folder before writing

## randomize_wild_encounters.py

Randomizes wild encounter species in `armips/data/encounters.s`.

What it does:
- replaces wild Pokemon species with random species from a chosen ID range
- asks for `POKEMON_MIN` and `POKEMON_MAX`
- creates `bak/encounters.s.bak`

```bash
python3 scripts_custom/scripts_randomizer/randomize_wild_encounters.py
```

## randomize_trainers.py

Randomizes trainer party species in `armips/data/trainers/trainers.s`.

What it does:
- replaces trainer Pokemon species with random species from a chosen ID range
- asks for `POKEMON_MIN` and `POKEMON_MAX`
- creates `bak/trainers.s.bak`

```bash
python3 scripts_custom/scripts_randomizer/randomize_trainers.py
```

## randomize_starters.py

Randomizes the starter Pokemon in `armips/data/starters.s`.

What it does:
- replaces starter species with random species from a chosen ID range
- asks for `POKEMON_MIN` and `POKEMON_MAX`
- creates `bak/starters.s.bak`

```bash
python3 scripts_custom/scripts_randomizer/randomize_starters.py
```

## randomize_abilities.py

Randomizes Pokemon abilities in `armips/data/mondata.s`.

What it does:
- replaces `ABILITY_*` values on `abilities` lines with random abilities from a chosen ID range
- asks for `ABILITY_MIN` and `ABILITY_MAX`
- does not replace `ABILITY_NONE`
- creates `bak/mondata.s.bak`

```bash
python3 scripts_custom/scripts_randomizer/randomize_abilities.py
```

## randomize_types.py

Randomizes Pokemon types in `armips/data/mondata.s`.

What it does:
- randomizes the `types` line for each Pokemon
- keeps monotype Pokemon monotype
- keeps dual-type Pokemon dual-type
- creates `bak/mondata.s.bak`

```bash
python3 scripts_custom/scripts_randomizer/randomize_types.py
```

## random_trainers_lead.py

Toggles the trainer lead flag logic in `armips/data/trainers/trainers.s`.

What it does:
- adds `0x80 |` to `nummons` for eligible trainers
- affects `SINGLE_BATTLE` trainers with 2 or more Pokemon
- affects `DOUBLE_BATTLE` trainers with 3 or more Pokemon
- can also remove the flag and restore plain `nummons X`

Usage:
- `0` disables the lead flag logic
- `1` enables the lead flag logic

```bash
python3 scripts_custom/scripts_randomizer/random_trainers_lead.py
```
