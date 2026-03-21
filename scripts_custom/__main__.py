#!/usr/bin/env python3
"""Allow running scripts_custom helpers via `python3 scripts_custom <script>`."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def resolve_script(script_arg: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    search_dirs = [
        base_dir,
        base_dir / "scripts_randomizer",
        base_dir / "scripts_romhack",
        base_dir / "scripts_multipliers",
        base_dir / "scripts_mods",
    ]

    script_names = [script_arg]
    candidate_path = Path(script_arg)
    if candidate_path.suffix != ".py":
        script_names.append(f"{script_arg}.py")

    for search_dir in search_dirs:
        for script_name in script_names:
            candidate = search_dir / script_name
            if candidate.is_file():
                return candidate

    raise FileNotFoundError(f"Unknown scripts_custom helper: {script_arg}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts_custom <script_name.py> [args...]")
        return 1

    script_path = resolve_script(sys.argv[1])
    sys.argv = [str(script_path), *sys.argv[2:]]
    runpy.run_path(str(script_path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
