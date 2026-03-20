#!/usr/bin/env python3
"""Allow running scripts_custom helpers via `python3 scripts_custom <script>`."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def resolve_script(script_arg: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    candidate = base_dir / script_arg

    if candidate.is_file():
        return candidate

    if candidate.suffix != ".py":
        with_suffix = candidate.with_suffix(".py")
        if with_suffix.is_file():
            return with_suffix

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
