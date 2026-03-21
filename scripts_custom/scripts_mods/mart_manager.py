#!/usr/bin/env python3
"""Install vanilla or modded mart data into src/field/mart.c."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET_PATH = ROOT / "src" / "field" / "mart.c"
VANILLA_PATH = ROOT / "scripts_custom" / "Data" / "mart_vanilla.c"
MODDED_PATH = ROOT / "scripts_custom" / "Data" / "mart_modded.c"
BACKUP_PATH = ROOT / "bak" / "mart.c.mart_manager.bak"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def install(source_path: Path, label: str) -> int:
    if not source_path.is_file():
        raise FileNotFoundError(f"Missing source file: {source_path}")

    source_text = read_text(source_path)
    current_text = read_text(TARGET_PATH)

    if current_text == source_text:
        print(f"mart.c already matches {label}. No changes were needed.")
        return 0

    write_text(BACKUP_PATH, current_text)
    write_text(TARGET_PATH, source_text)

    print(f"Installed {label}.")
    print(f"  Source      : {source_path}")
    print(f"  Target      : {TARGET_PATH}")
    print(f"  Backup saved: {BACKUP_PATH}")
    return 0


def main() -> int:
    print("========================================")
    print(" Mart Manager")
    print("========================================")
    print("0 = install mart_vanilla")
    print("1 = install mart_modded")
    print("2 = quit")

    choice = input("Choice: ").strip() or "2"

    if choice == "0":
        return install(VANILLA_PATH, "mart_vanilla")

    if choice == "1":
        return install(MODDED_PATH, "mart_modded")

    if choice == "2":
        print("No changes requested.")
        return 0

    print("Invalid choice. Use 0, 1, or 2.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
