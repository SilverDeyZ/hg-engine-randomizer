## Guides

- [RANDOMIZER.md](scripts_custom/scripts_randomizer/RANDOMIZER.md).

# hg-engine
## About
 `hg-engine` is an engine overhaul for ***English** Pokémon HeartGold* with a focus on bringing battles up to par with recent mainline Pokémon games and their mechanics.

### Disclaimer
 This repository and its assets are a [community endeavor](CREDITS.md).  By its nature, using it and subsequently profiting off of it is profiting on the backs of all of our work, all of which is intended to be used to further hobbies and for everyone to have fun.  You have my blessing to use code and assets from this repository as you please as long as there is *no money involved*, including optional donations through whichever platform to play your hack.  The creations that stem from this repository must be freely accessible and not hidden at all behind any paywall, including those that prompt the player to pay optionally (Ko-Fi's style comes to mind here).  The [Credits](CREDITS.md) should also be replicated in your hack's repository and/or the post to your hack--we all sit on the shoulders of giants here.

## Table of Contents
- [Features](#features)
- [Randomizer Guide](#randomizer-guide)
- [Build Instructions](#build-instructions-all-platforms-continued-from-further-setup-instructions)
- [Credits](#credits)


## Features:
* Dex Expansion (through Gen 6 almost entirely implemented)
* Ability Expansion up to 512 (through Gen 6 almost entirely implemented)
* Move Expansion with future generation moves
* Item Expansion with future generation items
* Mega Evolutions + Primal Reversions
* New Weathers
* Dynamic Speed
* Accurate Turn Sequence
* Accurate End-turn Resolution Order
* Much More Customizable Trainers
* Fairy Type
* Hidden Abilities
* Updated Effects for Existing [Moves](https://github.com/users/BluRosie/projects/3) and [Abilities](https://github.com/users/BluRosie/projects/2)
* 30 PC Boxes

*A more comprehensive list of features + a roadmap can be found by visiting the [hg-engine wiki](https://github.com/BluRosie/hg-engine/wiki).  Please read this README and the Wiki thoroughly before asking questions.*

If you are looking to contribute to hg-engine, please see the [CONTRIBUTING.md](CONTRIBUTING.md).

## Build Instructions (All Platforms) (Continued from Further Setup Instructions)

1. Get your ROM, rename it to **rom.nds** and place it in `~/git/hg-engine`.
    * \[Windows\] You can easily find where this is on MSYS2 or WSL by running the command `explorer.exe .` from the WSL terminal.  This will open the File Explorer to the folder where hg-engine is located.
        * For WSL this will likely be in the Linux drive that has newly been appended to the bottom of your files.  From there, it will likely be at `Linux\Ubuntu\home\[USERNAME]\git\hg-engine`.
        * For MSYS2 this will likely be in the `C:\msys64\home\[USERNAME]\git\hg-engine` directory.
2. In Terminal/WSL, type `make`.  It will start with building all the tools necessary, then move to the code, then the rest of the files in the folders.
    * `make` is initially very slow.  It can be sped up by specifying a certain amount of threads through the `-j#` flag, where # is a number.  The ideal amount of threads is typically the number that is given from `nproc`--so my `make` command, with `nproc` giving me `8`, is typically `make -j8`.
    * If you are a macOS user who is on arm64 (an Apple M Processor), you may have issues running this command due to `libpng` linker issues caused by an expected architecture mismatch. You can get around this issue by going to `Applications/Utilities/`, right clicking on Terminal, Clicking "Get Info", and clicking the "Open using Rosetta" checkbox so it becomes blue. Close Terminal if you had it open, then open it again and run the following:
        * ```cd ~/git/hg-engine```
        * ```make tools/nitrogfx```
        * ```make tools/ENCODE_IMG```
    * Make sure to undo your changes to Terminal after you are done so it will run as a native arm64 application again (uncheck the checkbox from before).
3. After the process completes, a new file will appear in the `hg-engine` folder named **test.nds**.
   * It is important to note that this alone will not add new Pokémon to the wild, trainers, etc...; it simply makes them available in your game. It is up to you to place them.
   * You can edit various game data such as trainers, dex entries, Pokémon stats, and more in the files in `armips/data`.

# Credits
* [CREDITS.md](CREDITS.md).
* [**Bubble (Base Mega Code)**][TEMPLATE]
* [**Skeli (FR template)**][CFRU]
* [**PokeDiamond decompilation projects (nitrogfx, msgenc)**][diamond]
* [**Mikelan98, Nomura (ARM9 Expansion Subroutine )**][ARM9]
* Rafael Vuijk (ndstool)
* Come swing by the [Kingdom of DS Hacking](https://discord.gg/zAtqJDW2jC) or [DS Modding Community](https://discord.gg/YBtdN3aXfv) Discord servers for any help with this!

[MONEXPAND]: https://github.com/BluRosie/hgss-monexpansion
[CFRU]: https://github.com/Skeli789/Complete-Fire-Red-Upgrade
[G5T]: https://github.com/CodenamePU/Gen5Tools
[ARM9]: https://pokehacking.com/tutorials/ramexpansion/
[diamond]:https://github.com/pret/pokediamond
[TEMPLATE]: https://github.com/Bubble791/Pokemon-Heart-Gold-Engine
[LUNOS]: https://www.pokecommunity.com/showthread.php?t=432351
