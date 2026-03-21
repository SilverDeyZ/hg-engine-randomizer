# scripts_format

This folder contains trainer formatting scripts meant to be used in a specific order.

They are mainly used to convert `armips/data/trainers/trainers.s` to the generalized trainer format, then restore the expected vanilla-like move behavior for regular trainers, and finally reroll nature and shiny odds if needed.

## Recommended order

1. `trainers_expansion.py`
2. `trainers_expansion_moveset_fill.py`
3. `trainers_expansion_reroll.py`

## 1. trainers_expansion.py

This script should be used first.

What it does:
- rewrites `trainers.s` into the generalized trainer format
- adds every major trainer mon subfield used by the full template
- expands `trainermontype` so trainers can support much more configuration
- fills missing template data such as items, ability, ball, IV/EV set, nature, and shiny lock

Why it matters:
- in the generalized format, the move template is always present
- once `TRAINER_DATA_TYPE_MOVES` is enabled, trainer Pokemon are expected to have their moves explicitly defined

Because of that, this first script inserts placeholder move slots using `MOVE_NONE`.

This is especially useful because:
- bosses or important trainers can keep custom semi-vanilla sets with only 2 or 3 real moves defined
- lower-tier trainers can still be processed afterward to recover a normal generated moveset

## 2. trainers_expansion_moveset_fill.py

This script should be used after `trainers_expansion.py`.

What it does:
- scans trainer Pokemon in generalized `trainers.s`
- looks for Pokemon whose 4 move slots are all `MOVE_NONE`
- replaces those placeholders with the last 4 level-up moves that Pokemon should know at its current level

Why it matters:
- before generalized formatting, many regular trainers rely on vanilla automatic move generation
- vanilla behavior gives them the last 4 moves learned by level
- after generalized formatting, explicit move slots exist, so that vanilla auto-fill no longer happens by itself

This script restores that expected behavior for standard trainers while leaving custom trainers alone if they already have real moves defined.

## 3. trainers_expansion_reroll.py

This script is optional and is usually used after the other two.

What it does:
- rerolls every trainer Pokemon nature
- rerolls the shiny chance for every trainer Pokemon
- gives each trainer Pokemon a fresh `1/512` chance to be shiny

This is useful when you want to refresh trainer Pokemon personality data after formatting and move generation.

## Short summary

- `trainers_expansion.py` converts trainers to the full configurable format and inserts `MOVE_NONE` placeholders where needed
- `trainers_expansion_moveset_fill.py` restores vanilla-like generated movesets for Pokemon that still have 4 empty move slots
- `trainers_expansion_reroll.py` rerolls nature and shiny chance for trainer Pokemon
