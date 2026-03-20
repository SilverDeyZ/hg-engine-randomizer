from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

SCRIPT_COMMANDS_PATH = ROOT / "src" / "field" / "script_commands.c"
COMMONSCRIPT_PATH = ROOT / "armips" / "scr_seq" / "scr_seq_00003_commonscript.s"
HOOKS_PATH = ROOT / "hooks"
ASM_PATH = ROOT / "asm" / "field" / "pc_anywhere.s"
MAP_EVENTS_INCLUDE = '#include "../../include/map_events_internal.h"\n'

SCRIPT_COMMANDS_BLOCK = """\
// PC Anywhere custom block start
/**
 *  @brief clear overworld request flags
 *
 *  @param req OVERWORLD_REQUEST_FLAGS structure to clear
 */
void ClearOverworldRequestFlags(OVERWORLD_REQUEST_FLAGS *req)
{
    req->TalkCheck    = 0;
    req->StepCheck    = 0;
    req->MenuOpen     = 0;
    req->unk0_0018    = 0;
    req->CnvButton    = 0;
    req->MatCheck     = 0;
    req->PushCheck    = 0;
    req->MoveCheck    = 0;
    req->FloatCheck   = 0;
    req->DebugMenu    = 0;
    req->DebugBattle  = 0;
    req->DebugHook    = 0;
    req->DebugKeyPush = 0;

    req->OpenPCCheck  = 0;

    req->Site = 0xFF;
    req->PushSite = 0xFF;
}

/**
 *  @brief set new overworld request flags depending on buttons pressed
 *
 *  @param req OVERWORLD_REQUEST_FLAGS structure to set flags in
 *  @param trg buttons that are pressed on this frame
 */
void SetOverworldRequestFlags(OVERWORLD_REQUEST_FLAGS *req, u16 trg)
{
    if (trg & PAD_BUTTON_L) {
        req->OpenPCCheck = TRUE;
    }
}

/**
 *  @brief handle overworld request flags
 *
 *  @param req OVERWORLD_REQUEST_FLAGS structure to set flags in
 */
void CheckOverworldRequestFlags(OVERWORLD_REQUEST_FLAGS *req, FieldSystem *fsys)
{
    if (req->OpenPCCheck) {
        SetScriptFlag(0x18F);
        EventSet_Script(fsys, 2010, NULL);
    }
}
// PC Anywhere custom block end
"""

HOOKS_BLOCK = """\
# pc anywhere
0001 ClearOverworldRequestFlags 021E6880 1
# hook from where y button is checked
0001 SetOverworldRequestFlags_hook 021E6982 0
# hook from near beginning of function
0001 CheckOverworldRequestFlags_hook 021E6AF6 3
"""

ASM_CONTENT = """\
.thumb
.align 4

// r4 is fsys, r5 is request structure
.global SetOverworldRequestFlags_hook
SetOverworldRequestFlags_hook:
mov r0, r5
ldr r1, [sp]
bl SetOverworldRequestFlags

ldr r0, [sp, #4] // icon0received
cmp r0, #0
beq returnToNoIcon0
mov r1, #2
ldr r0, [sp] // trg
ldr r2, =0x021E698C | 1
bx r2

returnToNoIcon0:
ldr r0, =0x021E6992 | 1
bx r0

.global CheckOverworldRequestFlags_hook
CheckOverworldRequestFlags_hook:
push {r0-r7}

bl CheckOverworldRequestFlags

pop {r0-r7}
mov r5, r0
ldrh r0, [r5]
mov r4, r1
lsl r0, r0, #0x12
lsr r0, r0, #0x1F
bne returnTo21E6B12
ldr r2, =0x021E6B02 | 1
bx r2

returnTo21E6B12:
ldr r0, =0x021E6B12 | 1
bx r0
"""

SCRIPT_REPLACEMENTS_INSTALL = [
    (
        """_0A18:
    scrcmd_500 90
    scrcmd_501 90
    scrcmd_308 90
    return
""",
        """_0A18:
    goto_if_set 0x18F, _skipPCOnOff
    scrcmd_500 90
    scrcmd_501 90
    scrcmd_308 90
_skipPCOnOff:
    return
""",
    ),
    (
        """_0DF0:
    closemsg
    play_se SEQ_SE_DP_PC_LOGOFF
    call _0A23
    touchscreen_menu_show
    releaseall
    end
""",
        """_0DF0:
    closemsg
    play_se SEQ_SE_DP_PC_LOGOFF
    goto_if_set 0x18F, _skipPCOff
    call _0A23
_skipPCOff:
    clearflag 0x18F
    touchscreen_menu_show
    releaseall
    end
""",
    ),
    (
        """_0E16:
    fade_screen 6, 1, 0, RGB_BLACK
    wait_fade
    scrcmd_309 90
    return
""",
        """_0E16:
    fade_screen 6, 1, 0, RGB_BLACK
    wait_fade
    goto_if_set 0x18F, _skipPCTransition
    scrcmd_309 90
_skipPCTransition:
    return
""",
    ),
]

SCRIPT_REPLACEMENTS_UNINSTALL = [(after, before) for before, after in SCRIPT_REPLACEMENTS_INSTALL]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def replace_once(content: str, old: str, new: str, path: Path) -> str:
    if new in content:
        return content
    if old not in content:
        raise RuntimeError(f"Expected snippet not found in {path}")
    return content.replace(old, new, 1)


def remove_once(content: str, block: str, path: Path) -> str:
    if block not in content:
        return content
    return content.replace(block, "", 1)


def install_script_commands() -> None:
    content = read_text(SCRIPT_COMMANDS_PATH)
    if MAP_EVENTS_INCLUDE not in content:
        anchor = '#include "../../include/constants/generated/learnsets.h"\n'
        if anchor in content:
            content = content.replace(anchor, anchor + MAP_EVENTS_INCLUDE, 1)
        else:
            script_include = '#include "../../include/script.h"\n'
            if script_include not in content:
                raise RuntimeError("Could not find include insertion anchor in script_commands.c")
            content = content.replace(script_include, script_include + MAP_EVENTS_INCLUDE, 1)
    if "PC Anywhere custom block start" in content:
        write_text(SCRIPT_COMMANDS_PATH, content)
        return
    if "void ClearOverworldRequestFlags(OVERWORLD_REQUEST_FLAGS *req)" in content:
        raise RuntimeError("script_commands.c already contains a ClearOverworldRequestFlags definition")
    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + SCRIPT_COMMANDS_BLOCK
    write_text(SCRIPT_COMMANDS_PATH, content)


def uninstall_script_commands() -> None:
    content = read_text(SCRIPT_COMMANDS_PATH)
    start = "// PC Anywhere custom block start"
    end = "// PC Anywhere custom block end\n"
    if start not in content:
        content = content.replace(MAP_EVENTS_INCLUDE, "", 1)
        write_text(SCRIPT_COMMANDS_PATH, content)
        return
    start_index = content.index(start)
    if end not in content[start_index:]:
        raise RuntimeError("Could not find the end of the PC Anywhere block in script_commands.c")
    end_index = content.index(end, start_index) + len(end)
    prefix = content[:start_index].rstrip()
    suffix = content[end_index:].lstrip("\n")
    if prefix and suffix:
        content = prefix + "\n\n" + suffix
    elif prefix:
        content = prefix + "\n"
    else:
        content = suffix
    content = content.replace(MAP_EVENTS_INCLUDE, "", 1)
    write_text(SCRIPT_COMMANDS_PATH, content)


def install_commonscript() -> None:
    content = read_text(COMMONSCRIPT_PATH)
    for old, new in SCRIPT_REPLACEMENTS_INSTALL:
        content = replace_once(content, old, new, COMMONSCRIPT_PATH)
    write_text(COMMONSCRIPT_PATH, content)


def uninstall_commonscript() -> None:
    content = read_text(COMMONSCRIPT_PATH)
    for old, new in SCRIPT_REPLACEMENTS_UNINSTALL:
        content = replace_once(content, old, new, COMMONSCRIPT_PATH)
    write_text(COMMONSCRIPT_PATH, content)


def install_hooks() -> None:
    content = read_text(HOOKS_PATH)
    if HOOKS_BLOCK in content:
        return
    anchor = "arm9 PartyMenu_ItemUseFunc_ReuseItem_hook 0208138C 3\n"
    if anchor not in content:
        raise RuntimeError("Could not find hook insertion anchor")
    content = content.replace(anchor, anchor + "\n" + HOOKS_BLOCK, 1)
    write_text(HOOKS_PATH, content)


def uninstall_hooks() -> None:
    content = read_text(HOOKS_PATH)
    updated = remove_once(content, "\n" + HOOKS_BLOCK, HOOKS_PATH)
    updated = remove_once(updated, HOOKS_BLOCK, HOOKS_PATH)
    write_text(HOOKS_PATH, updated)


def install_asm() -> None:
    if ASM_PATH.exists():
        existing = read_text(ASM_PATH)
        if existing == ASM_CONTENT:
            return
        raise RuntimeError(f"{ASM_PATH} already exists and does not match the expected pc_anywhere.s content")
    write_text(ASM_PATH, ASM_CONTENT)


def uninstall_asm() -> None:
    if not ASM_PATH.exists():
        return
    existing = read_text(ASM_PATH)
    if existing != ASM_CONTENT:
        raise RuntimeError(f"{ASM_PATH} exists but was modified outside this script")
    ASM_PATH.unlink()


def install() -> None:
    install_script_commands()
    install_commonscript()
    install_hooks()
    install_asm()


def uninstall() -> None:
    uninstall_asm()
    uninstall_hooks()
    uninstall_commonscript()
    uninstall_script_commands()


def main() -> int:
    print("0 = install pc anywhere and modify files")
    print("1 = uninstall pc anywhere modifications and revert to vanilla")
    choice = input("Choice: ").strip()

    if choice == "0":
        install()
        print("pc anywhere installed")
        return 0

    if choice == "1":
        uninstall()
        print("pc anywhere uninstalled")
        return 0

    print("Invalid choice. Use 0 or 1.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
