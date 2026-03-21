# scripts_multipliers

This folder contains utility scripts used to multiply, divide, or otherwise scale gameplay values in the project files.

## catchrate_multiplier.py

Scales Pokemon catch rates in `armips/data/mondata.s`.

```bash
python3 scripts_custom/scripts_multipliers/catchrate_multiplier.py
```

## eggcycles_multiplier.py

Scales egg hatch cycles in `armips/data/mondata.s`.

```bash
python3 scripts_custom/scripts_multipliers/eggcycles_multiplier.py
```

## evgain_multiplier.py

Enables, disables, or scales EV gain in `armips/data/mondata.s`.

```bash
python3 scripts_custom/scripts_multipliers/evgain_multiplier.py
```

## shiny_odds_manager.py

Lets you choose a shiny odds preset, then applies it to both `include/config.h`
and `scripts_custom/scripts_format/trainers_expansion_reroll.py` after confirmation.

```bash
python3 scripts_custom/scripts_multipliers/shiny_odds_manager.py
```

## trainer_levels_multiplier.py

Scales trainer Pokemon levels in `armips/data/trainers/trainers.s`.

```bash
python3 scripts_custom/scripts_multipliers/trainer_levels_multiplier.py
```

## walklevels_multiplier.py

Scales wild encounter levels in `armips/data/encounters.s`.

```bash
python3 scripts_custom/scripts_multipliers/walklevels_multiplier.py
```

## walkrate_multiplier.py

Disables wild encounters or scales walk encounter rates in `armips/data/encounters.s`.

```bash
python3 scripts_custom/scripts_multipliers/walkrate_multiplier.py
```
