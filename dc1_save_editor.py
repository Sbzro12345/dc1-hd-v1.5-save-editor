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

# Skills carry their own distance past the terminator, because the block does
# not sit at the same place for both heroes and Melwen stores hers out of order:
#   General: [16 bytes][Skill1][Skill2][Skill3][Skill4][Skill5][Skill6]
#   Melwen:  [28 bytes][Skill4][Skill5][Skill6][Skill1][Skill2][Skill3]
# Each list is in Skill 1 to 6 order, which is the order the game displays.
HEROES = (
    ("General", b"General\x00", (
        ("Combat", 16),
        ("Morale", 20),
        ("Cunning", 24),
        ("Infantry Commander", 28),
        ("Bowmen Commander", 32),
        ("Mage Commander", 36),
    )),
    ("Melwen", b"Melwen\x00", (
        ("Sorcery", 40),
        ("Wisdom", 44),
        ("Power", 48),
        ("Infantry Commander", 28),
        ("Bowmen Commander", 32),
        ("Mage Commander", 36),
    )),
)

# The General map array follows the closest 01 00 00 00 FF FF FF FF block above
# the Elwin identifier: [01 00 00 00 FF FF FF FF][149 bytes][9 maps x 8 bytes]
ELWIN_ID = b"Elwin\x00"
MAP_ANCHOR = b"\x01\x00\x00\x00\xff\xff\xff\xff"
MAP_ARRAY_AFTER = 149
MAP_ENTRY = 8
MAP_NAMES = (
    "Greatsands",
    "Cloudpass",
    "Marshwood",
    "Silverkeep",
    "Breewich",
    "Gardbridge",
    "Tarnwood",
    "Helegom",
    "Siria",
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
  
  Note: Setting Hero Level very high and further EXP will push it over the
  signed DWORD limit and into negative numbers, which needs another save edit to undo.
  """

SKILL_NOTE = """\
  Note: The default cap is 50 per skill, up to and including Heroic."""

STARS_NOTE = """  
  Note: Setting the stars with Save Editor changes reputation, and also unlocks
  their associated unlocks, including Melwen. It won't give Regalia of Dominion
  or Merry Roper's Ale Bottle though, you need to actually beat the associated levels.
  
  Note: Heroic is 6 stars and Legend+ is 7.
  To make Legend difficulty appear, all must be 6+.
  To make Mythic+ diffuclty appear, all must be 7.
  """

RANK_NOTE = """\
  Note: Clears past Mythic, 0-indexed. Ultima does not have a cap.
  For next difficulties to unlock, all must be at the R1 level.
  e.g. To unlock Immortal, all levels must minimum have 20 value.
  Otherwise, they will be capped at R!
  
  Mythic R1 = 0, Mythic R20 = 19
  Immortal R1 = 20, Immortal R20 = 39
  Demigod R1 = 40, Demigod R20 = 59
  Ultima R1 = 60, Ultima R20 = 79 ... and so on
  """

GARDBRIDGE_NOTE = """\
  Note: Gardbridge takes a value whether or not the Secret is unlocked, but
  without it, the map stays unplayable and shows no stars."""

CUNNING_WARNING = """\
  Note: Cunning raises EXP gain. Set it very high and a single clear can
  overflow the hero level counter into negative numbers, which needs another
  save edit to undo."""

MORALE_WARNING = """\
  Note: Morale raises Token gain. Set it very high and a single clear can
  overflow the Token Count into negative numbers, which needs another
  save edit to undo."""

# Skills that carry a warning of their own on top of the shared cap note.
SKILL_WARNINGS = {
    "Cunning": CUNNING_WARNING,
    "Morale": MORALE_WARNING,
}


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


def find_hero_blocks(profile, ident, skills):
    """Offsets of every hero record whose fields fit inside the payload."""
    span = len(ident) + max(after for _, after in skills) + 4
    blocks, start = [], 0
    while True:
        found = profile.find(ident, start)
        if found == -1:
            return blocks
        if found + span <= len(profile):
            blocks.append(found)
        start = found + 1


def choose_block(profile, name, ident, blocks, skills):
    """Pick one record when an identifier turns up more than once."""
    if len(blocks) == 1:
        return blocks[0]

    header("%s appears %d times. Pick the real hero record."
           % (name, len(blocks)))
    print(THIN)
    for n, base in enumerate(blocks, 1):
        end = base + len(ident)
        level = read_dword(profile, end + LEVEL_AFTER)
        values = [read_dword(profile, end + after) for _, after in skills]
        print("  %d. offset 0x%X  level %d  skills %s" % (n, base, level, values))

    choice = menu_choice(len(blocks))
    return None if choice is None else blocks[choice - 1]


def build_heroes(profile):
    """Both heroes exist in every valid save, so a miss means a broken file."""
    heroes = {}
    for name, ident, skills in HEROES:
        blocks = find_hero_blocks(profile, ident, skills)
        if name == "General":
            blocks = [b for b in blocks if b >= TOKEN_BACK]
        if not blocks:
            print("\nNo %s record in the profile payload, so this save is not"
                  " readable by the game either. Nothing has been changed."
                  % name)
            return None

        base = choose_block(profile, name, ident, blocks, skills)
        if base is None:
            return None

        end = base + len(ident)
        fields = [("%s Level" % name, end + LEVEL_AFTER, (LEVEL_WARNING,))]
        for label, after in skills:
            extra = SKILL_WARNINGS.get(label)
            notes = (SKILL_NOTE, extra) if extra else (SKILL_NOTE,)
            fields.append((label, end + after, notes))
        heroes[name] = {"base": base, "fields": fields}

    return heroes


def build_maps(profile):
    """Locate the General map array from the anchor above the Elwin identifier."""
    elwin = profile.find(ELWIN_ID)
    if elwin == -1:
        print("\nNo Elwin identifier in the profile payload, so the map array"
              " cannot be located. Nothing has been changed.")
        return None

    anchor = profile.rfind(MAP_ANCHOR, 0, elwin)
    if anchor == -1:
        print("\nNo map array anchor above the Elwin identifier."
              " Nothing has been changed.")
        return None

    start = anchor + len(MAP_ANCHOR) + MAP_ARRAY_AFTER
    if start + len(MAP_NAMES) * MAP_ENTRY > len(profile):
        print("\nThe map array runs past the end of the profile payload."
              " Nothing has been changed.")
        return None

    maps = []
    for i, name in enumerate(MAP_NAMES):
        base = start + i * MAP_ENTRY
        extra = (GARDBRIDGE_NOTE,) if name == "Gardbridge" else ()
        maps.append({
            "name": name,
            "fields": [
                ("Number of Stars", base, (STARS_NOTE,) + extra),
                ("Mythic+ R number", base + 4, (RANK_NOTE,) + extra),
            ],
        })
    return maps


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


def field_page(profile, baseline, title, fields, intro=None):
    """List a set of DWORD fields and hand the chosen one to edit_field."""
    while True:
        header(title)
        if intro:
            print(intro)
        print(THIN)
        for n, (label, offset, _) in enumerate(fields, 1):
            print("  %d. %-24s %s" % (n, label, preview(profile, baseline, offset)))
        print("  %d. Back" % (len(fields) + 1))

        choice = menu_choice(len(fields) + 1)
        if choice is None or choice == len(fields) + 1:
            return
        label, offset, notes = fields[choice - 1]
        edit_field(profile, baseline, title, label, offset, notes)


def maps_page(profile, baseline, maps):
    while True:
        header("GENERAL MAPS")
        print(THIN)
        for n, entry in enumerate(maps, 1):
            stars = preview(profile, baseline, entry["fields"][0][1])
            rank = preview(profile, baseline, entry["fields"][1][1])
            print("  %2d. %-12s Stars %-14s R %s"
                  % (n, entry["name"], stars, rank))
        print("  %2d. Back" % (len(maps) + 1))

        choice = menu_choice(len(maps) + 1)
        if choice is None or choice == len(maps) + 1:
            return
        entry = maps[choice - 1]
        field_page(profile, baseline, "GENERAL MAPS > %s" % entry["name"],
                   entry["fields"])


def main_menu(profile, baseline, heroes, maps, token_offset, state, commit):
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

        map_offsets = [off for entry in maps for _, off, _ in entry["fields"]]
        changed = count_pending(profile, baseline, map_offsets)
        note = ("(%d unsaved change%s)"
                % (changed, "" if changed == 1 else "s")) if changed else ""
        row = "  4. General Maps"
        print(row.ljust(28) + note if note else row)

        print("  5. Save")
        print("  6. Exit")
        if status:
            print("\n" + status)

        choice = menu_choice(6)
        if choice is None:
            choice = 6
        status = ""

        if choice == 1:
            edit_field(profile, baseline, "MAIN MENU", "Token Count", token_offset)

        elif choice in (2, 3):
            name = "General" if choice == 2 else "Melwen"
            field_page(profile, baseline, "%s STATS \n" % name.upper(),
                       heroes[name]["fields"], GUIDANCE)

        elif choice == 4:
            maps_page(profile, baseline, maps)

        elif choice == 5:
            status = commit(profile)
            if status is None:
                baseline[:] = profile
                status = ""

        else:
            all_offsets = [token_offset] + map_offsets
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

    maps = build_maps(profile)
    if maps is None:
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

    main_menu(profile, baseline, heroes, maps, token_offset, state, commit)


if __name__ == "__main__":
    main()
