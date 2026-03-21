# scripts_mods

This folder contains standalone project modification scripts.

## apply_mega_pokemon_drops.py

Applies item drops from `scripts_custom/Data/megapokemondrops.csv` to Pokemon item drops in `armips/data/mondata.s`.

```bash
python3 scripts_custom/scripts_mods/apply_mega_pokemon_drops.py
```

## asm_custom_manager.py

Enables or disables custom ASM includes in `armips/global.s` by commenting or uncommenting
the `armips/asm/custom/*.s` include lines.

```bash
python3 scripts_custom/scripts_mods/asm_custom_manager.py
```

## config_manager.py

Interactively manages selected yes/no toggles in `armips/include/config.s` and `include/config.h`.

```bash
python3 scripts_custom/scripts_mods/config_manager.py
```

## mart_manager.py

Installs either `scripts_custom/Data/mart_vanilla.c` or `scripts_custom/Data/mart_modded.c`
into `src/field/mart.c`.

```bash
python3 scripts_custom/scripts_mods/mart_manager.py
```

## pc_anywhere_manager.py

Installs or removes the PC Anywhere project modifications.

When installed, it works by pressing `L` in the overworld to open the PC.

```bash
python3 scripts_custom/scripts_mods/pc_anywhere_manager.py
```

## set_red_aiflags.py

Copies Red's trainer AI flags to every trainer entry in `armips/data/trainers/trainers.s`.

This is useful if you want every trainer to use the same AI flag set as Red.

```bash
python3 scripts_custom/scripts_mods/set_red_aiflags.py
```
