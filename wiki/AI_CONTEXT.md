# hg-engine AI Context

This file is a compact recovery guide for an AI editing `hg-engine`.

## Purpose

`hg-engine` is an overhaul of Pokemon HeartGold focused on modern battle mechanics, expanded data, and more flexible content systems.

The wiki is useful, but the best editing context is usually:

1. This file for quick orientation
2. One task-specific wiki page
3. The actual repository files mentioned by that page

## What To Ignore By Default

Skip these unless the task explicitly needs them:

- `.git/`
- `resources/`
- `Notepad---ARM-Language-Highlighting.md`

Why:

- `.git/` is repository metadata only
- `resources/` is mostly screenshots, gifs, palettes, and example binaries for human tutorials
- the Notepad++ page is editor setup, not engine behavior

## High-Signal Wiki Pages

- `Getting-Started.md`: onboarding and reading order
- `Troubleshooting.md`: common migration and build issues
- `Editing-Pokémon-Data.md`: species data and many related tables
- `Move-Data-Structure-Documentation.md`: move fields in `armips/data/moves.s`
- `Move-Scripting-Systems-Documentation.md`: move battle behavior concepts and script flow
- `Trainer-Pokémon-Structure-Documentation.md`: trainer data and trainer party macros
- `Wild-Pokémon-Table-Documentation.md`: encounter table format and form support
- `Item-System-Documentation.md`: item data and icon pipeline
- `Form-System-Documentation.md`: how extra forms are mapped
- `New-Evolution-Methods-Documentation.md`: supported evolution method constants and behavior
- `Overworld-System-Documentation.md`: overworld-specific edits

## Important Caveats

- `Move-Scripting-Systems-Documentation.md` is useful but explicitly outdated in places after scripting refactors. Use it for concepts and examples, then verify against the current repo before editing.
- `Move-Animation-Scripting-System-Documentation.md` is lower-confidence reference than the main battle scripting doc.
- Mixed text encoding exists in the wiki. If a page renders accented characters strangely, prefer filenames and code identifiers over display text.

## Where Common Edits Usually Happen

### Pokemon data

Primary doc:

- `Editing-Pokémon-Data.md`

Common files mentioned there:

- `armips/data/mondata.s`
- `armips/data/evodata.s`
- `armips/data/levelupdata.s`
- `armips/data/eggmoves.s`
- `armips/data/tmlearnset.txt`
- `armips/data/tutordata.txt`
- `armips/data/pokedex/*`
- `data/BaseExperienceTable.c`
- `data/HiddenAbilityTable.c`

Use this area for:

- stats
- typings
- abilities
- learnsets
- egg moves
- dex data
- area data

### Move data

Primary docs:

- `Move-Data-Structure-Documentation.md`
- `Move-Scripting-Systems-Documentation.md`

Common files:

- `armips/data/moves.s`
- `armips/move/battle_move_seq/*`
- `armips/move/battle_eff_seq/*`
- `armips/move/battle_sub_seq/*`

Mental model:

- move data chooses a `battleeffect`
- the move script chain usually flows through `battle_move_seq` -> `battle_eff_seq` -> sometimes `battle_sub_seq`
- many moves just jump to the current effect script

Use this area for:

- power, type, accuracy, PP, targeting, flags
- move battle behavior
- secondary effects

### Move visuals

Primary doc:

- `Move-Animation-Scripting-System-Documentation.md`

Common files:

- `armips/move/move_anim/*`
- related particle resources in the main repo

Use only if the task is about animation or particles. Skip for normal battle logic edits.

### Trainers

Primary doc:

- `Trainer-Pokémon-Structure-Documentation.md`

Common files:

- `armips/data/trainers/trainers.s`
- `armips/data/trainers/trainertext.s`

Key ideas:

- trainer header controls parsing via `data_type`
- hg-engine extends trainer mons with optional ability, ball, per-stat IVs/EVs, nature, shiny lock, forced stats, custom types, nickname, and more
- battle type can define double battles without a partner NPC

Use this area for:

- trainer teams
- trainer battle setup
- custom competitive sets

### Wild encounters

Primary doc:

- `Wild-Pokémon-Table-Documentation.md`

Common file:

- `armips/data/encounters.s`

Key idea:

- wild species fields now support forms via `(form << 11) | species`
- macros like `monwithform` and `encounterwithform` are the safe way to define form encounters

Use this area for:

- route encounters
- fishing and surfing tables
- swarm slots
- time-of-day wild data

### Evolutions

Primary doc:

- `New-Evolution-Methods-Documentation.md`

Common file family:

- evolution data in the main data tables, especially `armips/data/evodata.s`

Use this area for:

- adding later-gen evolution methods
- checking which method constants already exist

### Forms

Primary doc:

- `Form-System-Documentation.md`

Common files:

- `src/pokemon.c`
- form-related species/data tables in the main repo

Key ideas:

- expanded species occupy new indices beyond vanilla
- extra form routing is handled by `PokeFormDataTbl`
- adding a new form is usually similar to adding a species plus mapping the form data correctly

Use this area for:

- regional forms
- mega/primal handling
- custom forms

### Items

Primary doc:

- `Item-System-Documentation.md`

Common files:

- `data/itemdata/itemdata.c`
- `src/item.c`
- `data/graphics/item/*`

Key ideas:

- item expansion maps new items to new data/gfx entries instead of rewriting the original table directly
- item behavior is mostly data-driven
- icon art must respect indexed/4bpp expectations

Use this area for:

- adding items
- changing item pockets or usage behavior
- held effect and field/battle use configuration

## Fast Routing Rules

If the task says:

- "species", "stats", "learnset", "typing", "dex", "ability table": go to `Editing-Pokémon-Data.md`
- "move power/type/accuracy/flags": go to `Move-Data-Structure-Documentation.md`
- "move effect/script/behavior": go to `Move-Scripting-Systems-Documentation.md`
- "trainer team" or "trainer battle": go to `Trainer-Pokémon-Structure-Documentation.md`
- "wild encounter" or "route table": go to `Wild-Pokémon-Table-Documentation.md`
- "evolution method": go to `New-Evolution-Methods-Documentation.md`
- "form" or "regional variant": go to `Form-System-Documentation.md`
- "item": go to `Item-System-Documentation.md`
- "animation" or "particle": go to `Move-Animation-Scripting-System-Documentation.md`
- "build issue", "migration issue", "submodule issue": go to `Troubleshooting.md`

## Safe Working Heuristics

- Prefer documented macros and existing patterns over inventing new structure layouts
- If a wiki page names the exact repo file, open that file next instead of reading more wiki
- For scripting docs, trust current repo constants and macros over old prose if they disagree
- Rebuild and test after one focused change at a time
- If an edit touches forms, encounters, or trainer species fields, verify whether the project expects plain species or `(form << 11) | species`

## Minimal Context Pack

If only a few files can be loaded, use:

1. `AI_CONTEXT.md`
2. `Getting-Started.md`
3. `Troubleshooting.md`
4. One task-specific wiki page

That is usually enough to recover and move into the real source tree without loading the whole wiki.
