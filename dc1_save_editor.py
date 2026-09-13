#!/usr/bin/env python3
"""
Defender Chronicles HD v1.5 save editor.

Finds com.chillingo.defenderchronicleshd.plist, decrypts the profile payload
in memory, edits the hero blocks, then repacks the save. The two campaign
payloads are left exactly as they were found.
"""

import os
import plistlib
import random
import struct
import sys
from datetime import datetime

SAVE_NAME = "com.chillingo.defenderchronicleshd.plist"

# Token Count sits 53 bytes before the General identifier:
# [Token Count 4 bytes][49 bytes][General\0]
TOKEN_BACK = 53

# Hero identifiers are dynamic-length strings including the null terminator.
# Both hero fields below are measured from the end of that terminator.
LEVEL_AFTER = 0          # Hero Level sits directly after the terminator
SKILL_AFTER = 16         # Skill 1 sits 16 bytes past the terminator
SKILL_COUNT = 6

HEROES = (
    ("General", b"General\x00", (
        "Combat",
        "Morale",
        "Cunning",
        "Infantry Commander",
        "Bowmen Commander",
        "Mage Commander",
    )),
    ("Melwen", b"Melwen\x00", (
        "Sorcery",
        "Wisdom",
        "Power",
        "Infantry Commander",
        "Bowmen Commander",
        "Mage Commander",
    )),
)

DWORD_MIN = -2147483648
DWORD_MAX = 2147483647
QUIT_WORDS = {"q", "quit", "exit"}
RULE = "=" * 72
THIN = "-" * 72
PICK = "\nPress the corresponding number and then Enter: "
TITLE = "Defender Chronicles HD v1.5 save editor"

GUIDANCE = """\
Level hack VS Skill hack
  Hero Level   Raise the level, then drink the Potion of Forgetfulness at the
               Elf Hut. The points refunded by that reset are kept, so the
               gain is permanent.

  Skills       Raise a skill directly to push past the cap the developers tied
               to your level, which is the quicker route for grinding (Mythic+
               requires 20 clears per level to get to the next difficulty).
               A Potion of Forgetfulness undoes this and drops the skill back
               to whatever your real level allows.

  Keep the numbers sane either way. Any damage figure that passes roughly
  2,000,000,000 wraps the signed DWORD and comes out as 0 damage."""

LEVEL_WARNING = """\
  Note: Hero Level is 0-indexed, so the in-game level is this value plus one.
  Set it very high and further EXP will push it over the signed DWORD limit
  and into negative numbers, which needs another save edit to undo."""

SKILL_NOTE = """\
  Note: The default cap is 50, up to and including Heroic."""

CUNNING_WARNING = """\
  Note: Cunning raises EXP gain. Set it very high and a single clear can
  overflow the hero level counter into negative numbers, which needs another
  save edit to undo."""


# ---------------------------------------------------------------- crypto

def decrypt_payload(data: bytes) -> bytes:
    buf = bytearray(data)
    size = len(buf)
    out_size = (size - 8) // 4

    for i in range(size):
        buf[i] ^= (i & 0xFF)

    magic1 = buf[2] | (buf[3] << 8)
    magic2 = buf[-4] | (buf[-3] << 8)
    if magic1 != 0x6E58 or magic2 != 0xB864:
        raise ValueError("Invalid magic constants.")

    val_1e = buf[0] | (buf[1] << 8)
    val_20 = buf[-2] | (buf[-1] << 8)
    if (val_1e ^ out_size) != (val_20 ^ 0x38BC):
        raise ValueError("Header checksum mismatch.")

    out_buf = bytearray(out_size)
    for i in range(out_size):
        offset = 4 + i * 4
        b0, b1, b2, b3 = buf[offset:offset + 4]
        mode = b0 & 3
        if mode == 0:
            val, idx = b0 ^ b1, b2 | (b3 << 8)
        elif mode == 1:
            val, idx = b0 ^ b2, b1 | (b3 << 8)
        else:
            val, idx = b0 ^ b3, b1 | (b2 << 8)
        if idx < out_size:
            out_buf[idx] = val

    checksum = 0xA961
    for byte in out_buf:
        checksum = (checksum + byte) & 0xFFFF
    if (val_1e ^ out_size) != checksum:
        raise ValueError("Data payload checksum mismatch.")

    return bytes(out_buf)


def encrypt_payload(plaintext: bytes) -> bytes:
    out_size = len(plaintext)
    size = out_size * 4 + 8
    buf = bytearray(size)

    checksum = 0xA961
    for byte in plaintext:
        checksum = (checksum + byte) & 0xFFFF

    val_1e = checksum ^ out_size
    val_20 = checksum ^ 0x38BC

    buf[0], buf[1] = val_1e & 0xFF, (val_1e >> 8) & 0xFF
    buf[2], buf[3] = 0x58, 0x6E
    buf[-4], buf[-3] = 0x64, 0xB8
    buf[-2], buf[-1] = val_20 & 0xFF, (val_20 >> 8) & 0xFF

    chunk_indices = list(range(out_size))
    random.shuffle(chunk_indices)

    for orig_idx, val in enumerate(plaintext):
        offset = 4 + chunk_indices[orig_idx] * 4
        mode = random.randint(0, 3)
        b0 = (random.randint(0, 63) << 2) | mode
        if mode == 0:
            b1, b2, b3 = b0 ^ val, orig_idx & 0xFF, (orig_idx >> 8) & 0xFF
        elif mode == 1:
            b2, b1, b3 = b0 ^ val, orig_idx & 0xFF, (orig_idx >> 8) & 0xFF
        else:
            b3, b1, b2 = b0 ^ val, orig_idx & 0xFF, (orig_idx >> 8) & 0xFF
        buf[offset:offset + 4] = [b0, b1, b2, b3]

    for i in range(size):
        buf[i] ^= (i & 0xFF)

    return bytes(buf)


# ---------------------------------------------------------------- screen

def clear_screen():
    if not sys.stdout.isatty():
        print()
        return
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()


def header(subtitle, path=None):
    clear_screen()
    print(TITLE)
    if path:
        print("  " + path)
    print(RULE)
    print(subtitle)


def ask(text):
    """Return the stripped answer, or None if the user wants out."""
    try:
        answer = input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    return None if answer.lower() in QUIT_WORDS else answer


def menu_choice(count):
    """Return 1..count, or None if the user backed out."""
    while True:
        answer = ask(PICK)
        if answer is None:
            return None
        try:
            number = int(answer)
        except ValueError:
            number = 0
        if 1 <= number <= count:
            return number
        print("  Enter a number between 1 and %d." % count)


def ask_dword(text):
    """Prompt until a valid signed DWORD arrives, or None to cancel."""
    while True:
        answer = ask(text)
        if answer is None:
            return None
        cleaned = answer.replace(",", "").replace("_", "")
        try:
            base = 16 if cleaned.lower().startswith(("0x", "-0x")) else 10
            value = int(cleaned, base)
        except ValueError:
            print("  Enter a whole number, for example 5000 or -1 or 0x1F.")
            continue
        if not DWORD_MIN <= value <= DWORD_MAX:
            print("  That is outside the signed DWORD range.")
            continue
        return value


# ---------------------------------------------------------------- location

def script_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def locate_plist():
    home = script_dir()
    local = os.path.join(home, SAVE_NAME)
    if os.path.isfile(local):
        return local

    print("No " + SAVE_NAME + " found in:")
    print("  " + home)
    while True:
        print("\nType the full path to a .plist save or to the folder holding it,")
        answer = ask("or type Q and press Enter to quit: ")
        if answer is None:
            return None
        answer = answer.strip('"').strip("'")
        if os.path.isfile(answer):
            return os.path.abspath(answer)
        if os.path.isdir(answer):
            candidate = os.path.join(answer, SAVE_NAME)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            print("  That folder does not contain " + SAVE_NAME + ".")
            continue
        print("  Nothing found at that path.")


# ---------------------------------------------------------------- fields

def read_dword(buf, offset):
    return struct.unpack_from("<i", buf, offset)[0]


def write_dword(buf, offset, value):
    struct.pack_into("<i", buf, offset, value)


def preview(profile, baseline, offset):
    """Value on its own, or 'old -> new' while the change is unsaved."""
    old = read_dword(baseline, offset)
    new = read_dword(profile, offset)
    return "%d" % new if old == new else "%d -> %d" % (old, new)


def count_pending(profile, baseline, offsets):
    return sum(1 for off in offsets
               if read_dword(profile, off) != read_dword(baseline, off))


def find_hero_blocks(profile, ident):
    """Offsets of every hero record whose fields fit inside the payload."""
    span = len(ident) + SKILL_AFTER + SKILL_COUNT * 4
    blocks, start = [], 0
    while True:
        found = profile.find(ident, start)
        if found == -1:
            return blocks
        if found + span <= len(profile):
            blocks.append(found)
        start = found + 1


def choose_block(profile, name, ident, blocks):
    """Pick one record when an identifier turns up more than once."""
    if len(blocks) == 1:
        return blocks[0]

    header("%s appears %d times. Pick the real hero record."
           % (name, len(blocks)))
    print(THIN)
    for n, base in enumerate(blocks, 1):
        end = base + len(ident)
        level = read_dword(profile, end + LEVEL_AFTER)
        skills = [read_dword(profile, end + SKILL_AFTER + i * 4)
                  for i in range(SKILL_COUNT)]
        print("  %d. offset 0x%X  level %d  skills %s" % (n, base, level, skills))

    choice = menu_choice(len(blocks))
    return None if choice is None else blocks[choice - 1]


def build_heroes(profile):
    """Both heroes exist in every valid save, so a miss means a broken file."""
    heroes = {}
    for name, ident, skill_names in HEROES:
        blocks = find_hero_blocks(profile, ident)
        if name == "General":
            blocks = [b for b in blocks if b >= TOKEN_BACK]
        if not blocks:
            print("\nNo %s record in the profile payload, so this save is not"
                  " readable by the game either. Nothing has been changed."
                  % name)
            return None

        base = choose_block(profile, name, ident, blocks)
        if base is None:
            return None

        end = base + len(ident)
        fields = [("%s Level" % name, end + LEVEL_AFTER, (LEVEL_WARNING,))]
        for i, skill in enumerate(skill_names):
            notes = (SKILL_NOTE, CUNNING_WARNING) if skill == "Cunning" \
                else (SKILL_NOTE,)
            fields.append((skill, end + SKILL_AFTER + i * 4, notes))
        heroes[name] = {"base": base, "fields": fields}

    return heroes


# ---------------------------------------------------------------- editing

def edit_field(profile, baseline, page, label, offset, notes=()):
    """Draw the value entry screen and apply whatever the user enters."""
    header("%s > %s" % (page, label))
    print(THIN)
    for note in notes:
        print(note)
        print()
    print("  Current value: %d" % read_dword(baseline, offset))
    if read_dword(profile, offset) != read_dword(baseline, offset):
        print("  Pending value: %d" % read_dword(profile, offset))

    value = ask_dword(
        "\n  Enter the new value (%d to %d), or Q to cancel: "
        % (DWORD_MIN, DWORD_MAX))
    if value is not None:
        write_dword(profile, offset, value)


def hero_page(profile, baseline, name, fields):
    while True:
        header("%s STATS" % name.upper())
        print(GUIDANCE)
        print(THIN)
        for n, (label, offset, _) in enumerate(fields, 1):
            print("  %d. %-24s %s" % (n, label, preview(profile, baseline, offset)))
        print("  %d. Back" % (len(fields) + 1))

        choice = menu_choice(len(fields) + 1)
        if choice is None or choice == len(fields) + 1:
            return
        label, offset, notes = fields[choice - 1]
        edit_field(profile, baseline, "%s STATS" % name.upper(),
                   label, offset, notes)


def main_menu(profile, baseline, heroes, token_offset, state, commit):
    """Returns when the user exits. commit(profile) performs the save."""
    status = ""
    while True:
        header("MAIN MENU", state["path"])

        print("  1. Token Count            %s"
              % preview(profile, baseline, token_offset))

        for n, name in enumerate(("General", "Melwen"), 2):
            offsets = [off for _, off, _ in heroes[name]["fields"]]
            changed = count_pending(profile, baseline, offsets)
            note = ("(%d unsaved change%s)"
                    % (changed, "" if changed == 1 else "s")) if changed else ""
            row = "  %d. %s Stats" % (n, name)
            print(row.ljust(28) + note if note else row)

        print("  4. Save")
        print("  5. Exit")
        if status:
            print("\n" + status)

        choice = menu_choice(5)
        if choice is None:
            choice = 5
        status = ""

        if choice == 1:
            edit_field(profile, baseline, "MAIN MENU", "Token Count", token_offset)

        elif choice in (2, 3):
            name = "General" if choice == 2 else "Melwen"
            hero_page(profile, baseline, name, heroes[name]["fields"])

        elif choice == 4:
            status = commit(profile)
            if status is None:
                baseline[:] = profile
                status = ""

        else:
            all_offsets = [token_offset]
            for hero in heroes.values():
                all_offsets += [off for _, off, _ in hero["fields"]]
            changed = count_pending(profile, baseline, all_offsets)
            if changed:
                header("EXIT")
                print(THIN)
                print("%d unsaved change%s will be lost."
                      % (changed, "" if changed == 1 else "s"))
                print("  1. Exit without saving")
                print("  2. Go back to the menu")
                if menu_choice(2) == 2:
                    continue
            return


# ---------------------------------------------------------------- saving

def save_plist(original_path, plist, profile):
    """Repack the profile payload and replace the save file. Returns the path."""
    blob = encrypt_payload(profile)
    if decrypt_payload(blob) != profile:
        raise ValueError("Round-trip check failed for the profile payload.")
    plist["profile"] = blob

    folder = os.path.dirname(original_path) or "."
    target = os.path.join(folder, SAVE_NAME)
    temp = target + ".tmp"

    with open(temp, "wb") as handle:
        plistlib.dump(plist, handle, fmt=plistlib.FMT_BINARY)

    backup = original_path + datetime.now().strftime(".%Y%m%d-%H%M%S.bak")
    os.replace(original_path, backup)
    os.replace(temp, target)
    return target


# ---------------------------------------------------------------- main

def main():
    clear_screen()
    print(TITLE)
    print(RULE)

    path = locate_plist()
    if path is None:
        return

    try:
        with open(path, "rb") as handle:
            plist = plistlib.load(handle)
        blob = plist.get("profile")
        if not isinstance(blob, bytes):
            print("\nThat save has no profile payload, so there is nothing to edit.")
            return
        profile = bytearray(decrypt_payload(blob))
    except Exception as error:
        print("\nCould not read that save: %s" % error)
        return

    heroes = build_heroes(profile)
    if heroes is None:
        return

    baseline = bytearray(profile)
    token_offset = heroes["General"]["base"] - TOKEN_BACK
    state = {"path": path}

    def commit(current):
        """Returns None on success, or a status line describing the failure."""
        try:
            state["path"] = save_plist(state["path"], plist, bytes(current))
        except Exception as error:
            return "  Save failed, so the save file was left alone: %s" % error
        return None

    main_menu(profile, baseline, heroes, token_offset, state, commit)


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            input("\nPress Enter to close this window: ")
        except (EOFError, KeyboardInterrupt):
            pass
