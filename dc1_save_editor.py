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
PICK = "\nPress the corresponding number (or Q to go back/quit) and then Enter: "
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
        heroes[name] = {"base": base, "end": end, "fields": fields}

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
    

def build_melwen_maps(profile):
    # Algorithm I designed
    #1. First, find the Melwen String Identifier.
    #2. Skip 52 bytes after the null string char to go directly to the first Item
    #3. For each of the 5 Items, should begin with 01 00 00 00. Locate the 01 00 00 00, then skip the next 4 bytes, should now be on a char[]. Find the nearest 00 from here to locate the null string char. Then, skip 148 bytes to go to the next item. Repeat for all 5 items to skip past the 5 items.
    #4. After having navigated the 5 items, seek the nearest 01 00 00 00 FF FF FF FF.
    #5. From there, ignore the next 149 bytes, and you will be at the maps array.
    """Navigate Melwen's equipment blocks to locate her map array."""
    melwen_id = b"Melwen\x00"
    start_idx = profile.find(melwen_id)
    if start_idx == -1:
        return None

    # Skip 52 bytes after the null string char to reach the first Item
    curr_idx = start_idx + len(melwen_id) + 52
    
    # Traverse the 5 equipped items
    for _ in range(5):
        curr_idx = profile.find(b"\x01\x00\x00\x00", curr_idx)
        if curr_idx == -1:
            return None
        # Skip 01 00 00 00 and the 4-byte Equipment Slot
        curr_idx += 8 
        # Find nearest 00 for the dynamic String Identifier
        curr_idx = profile.find(b"\x00", curr_idx)
        if curr_idx == -1:
            return None
        # Skip the null terminator and the 148 misc bytes
        curr_idx += 1 + 148 
        
    # Seek the nearest 01 00 00 00 FF FF FF FF
    # In hindsight, should have seeked to the 2nd 01 00 00 00 FF FF FF FF after
    # then apply 149 byte offset
    anchor = profile.find(MAP_ANCHOR, curr_idx)
    if anchor == -1:
        return None
        
    # Ignore the next 149 bytes to land on the maps array
    # +157 cuz there is apparently 2 unused 01 00 00 00 FF FF FF FF
    # 157 is the difference between the 2nd last and last ones
    start = anchor + len(MAP_ANCHOR) + MAP_ARRAY_AFTER + 157
    if start + len(MAP_NAMES) * MAP_ENTRY > len(profile):
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


# ---------------------------------------------------------------- equipment

ITEM_SENTINEL = b"\x01\x00\x00\x00"
ITEM_TAIL = 148
EQUIP_AFTER = 52
EQUIP_SLOTS = (
    ("Headgear", 0),
    ("Weapon", 1),
    ("Chestpiece", 2),
    ("Accessory 1", 3),
    ("Accessory 2", 3),
)
UNEQUIPPED = -1

# Field order inside the 148-byte tail, as index * 4 bytes from the tail start.
ITEM_FIELDS = (
    ("Sprite Number", 0),
    ("Token Value", 1),
    ("Prefix Count", 2),
    ("Suffix Count", 3),
    ("Reputation Tier", 4),
    ("Grade", 5),
    ("Which Hero", 6),
)

SUFFIX_OPTIONS = (("0", 0), ("1", 1))
REPUTATION_OPTIONS = (
    ("Rusty", 0),
    ("None", 1),
    ("Superior", 2),
    ("Elite", 3),
    ("Legendary", 4),
    ("Mythic", 5),
    ("Demigod", 6),
)
GRADE_OPTIONS = (
    ("None", 0),
    ("Defective", 1),
    ("Exceptional", 2),
    ("Flawless", 3),
    ("Masterpiece", 4),
    ("Ultimate", 5),
)
HERO_OPTIONS = (("General Only", 0b0001), ("Melwen Only", 0b0100), ("Both Heroes", 0b0101))
PRESET_HERO_BIT = {"General": 0b0001, "Melwen": 0b0100}
SLOT_OPTIONS = (
    ("Headpiece", 0),
    ("Weapon", 1),
    ("Chestpiece", 2),
    ("Accessory", 3),
    ("No Item", -1),
)

TOKEN_VALUE_NOTE = """\
  Note: use -1 to set the item as a Quest Item."""


def hero_label(mask):
    """Only bits 0 and 2 matter. Elwin and Lovell are not in the game."""
    general = mask & 0b0001
    melwen = mask & 0b0100
    if general and melwen:
        return "Both Heroes"
    if general:
        return "General Only"
    if melwen:
        return "Melwen Only"
    return "Neither"

# Each preset is the whole record: slot, name, the seven tail DWORDs, then the
# effect entries. Unlisted effect entries are zero-filled out to 10.
PRESETS = (
    {"name": "Argonath's Full Helm", "slot": 0, "sprite": 0x40, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Red Pack)",
     "effects": ((0x07E0, -2, 0xB4), (0x0CFB, 0x05, 0), (0x0FAD, -1, 0))},
    {"name": "Branston's Full Helm", "slot": 0, "sprite": 0x43, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Blue Pack)",
     "effects": ((0x07E0, -2, 0xA0), (0x0CFD, 0x05, 0), (0x0FAD, -1, 1))},
    {"name": "Leandro's Spike Helm", "slot": 0, "sprite": 0x46, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Guardian Pack)",
     "effects": ((0x07E0, -2, 200), (0x07E3, 0x04, 2), (0x0FAD, -1, 2))},
    {"name": "Hiram's Cap", "slot": 0, "sprite": 0x49, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Destroyer Pack)",
     "effects": ((0x07E0, -2, 0x96), (0x0BCF, 0x0C, 0), (0x0FAD, -1, 3))},
    {"name": "Myrtharnith's Mask", "slot": 0, "sprite": 0x4C, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Red Pack)",
     "effects": ((0x0BE1, 0x12, 4), (0x07E5, -2, 0x21C), (0x0FAD, -1, 4))},
    {"name": "Orleaear's Circlet", "slot": 0, "sprite": 0x4F, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Blue Pack)",
     "effects": ((0x0BE2, 0x12, 4), (0x07E5, -2, 0x1E0), (0x0FAD, -1, 5))},
    {"name": "Tyrghymn's Headband", "slot": 0, "sprite": 0x52, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Industrious Pack)",
     "effects": ((0x0D04, 0x1A, 0), (0x07E5, -2, 0x1FE), (0x0FAD, -1, 6))},
    {"name": "Killevalsa's Barrette", "slot": 0, "sprite": 0x55, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Avarice Pack)",
     "effects": ((0x0D03, 0x17, 0), (0x07E5, -2, 0x23A), (0x0FAD, -1, 7))},
    {"name": "Regalia of Dominion", "slot": 0, "sprite": 0x32, "token": -1,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0BDB, -2, 0),)},
    {"name": "Overlord's Helm", "slot": 0, "sprite": 0x20, "token": 0x02EE,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x03,
     "effects": ((0x03EB, -2, 0x0A), (0x03EC, -2, 0x0A), (0x03EF, -2, 0x0A),
                 (0x03F0, -2, 0x0A), (0x03F2, -2, 0x0A), (0x07E0, -2, 0x50))},
    {"name": "Devil's Helm", "slot": 0, "sprite": 0x21, "token": 0x029A,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x03,
     "effects": ((0x03EB, -2, 0x10), (0x03EC, -2, -6), (0x03EE, -2, 0x10),
                 (0x07DD, -2, 0x42), (0x07E0, -2, 0x42), (0x0BCD, -2, 0),
                 (0x0BCE, -2, 0), (0x0BCF, -2, 0))},
    
    {"name": "Argonath's Blade", "slot": 1, "sprite": 0x3F, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Red Pack)",
     "effects": ((0x07DD, -2, 0x1C2), (0x0CFB, -2, 0), (0x0FAD, -1, 0))},
    {"name": "Branston's Greatsword", "slot": 1, "sprite": 0x42, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Blue Pack)",
     "effects": ((0x07DD, -2, 0x1E0), (0x0CFD, -2, 0), (0x0FAD, -1, 1))},
    {"name": "Leandro's Long Dagger", "slot": 1, "sprite": 0x45, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Guardian Pack)",
     "effects": ((0x07DD, -2, 0x1A4), (0x07E3, -2, 2), (0x0FAD, -1, 2))},
    {"name": "Hiram's Scimitar", "slot": 1, "sprite": 0x48, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Destroyer Pack)",
     "effects": ((0x07DD, -2, 500), (0x0BCF, -2, 0), (0x0FAD, -1, 3))},
    {"name": "Myrtharnith's Lightning Wand", "slot": 1, "sprite": 0x4B, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Red Pack)",
     "effects": ((0x0BDF, -1, 0), (0x07DD, -2, 0x1D8), (0x03F3, -2, 20), (0x0FAD, -1, 4))},
    {"name": "Orleaear's Ice Wand", "slot": 1, "sprite": 0x4E, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Blue Pack)",
     "effects": ((0x0BE0, -1, 0), (0x07DD, -2, 0x181), (0x03F3, -2, 20), (0x0FAD, -1, 5))},
    {"name": "Tyrghymn's Ice Wand", "slot": 1, "sprite": 0x51, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Industrious Pack)",
     "effects": ((0x0BE0, -1, 0), (0x07DD, -2, 0x1C7), (0x03F3, -2, 20), (0x0FAD, -1, 6))},   
    {"name": "Killevalsa's Lightning Wand", "slot": 1, "sprite": 0x54, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Avarice Pack)",
     "effects": ((0x0BDF, -1, 0), (0x07DD, -2, 0x20D), (0x03F3, -2, 20), (0x0FAD, -1, 7))},
    {"name": "Tahl Asel", "slot": 1, "sprite": 0x1D, "token": 0x8C,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "effects": ((0x07DD, -2, 0x78), (0x0BD2, -2, 0))},
    {"name": "True Tahl Asel", "slot": 1, "sprite": 0x1D, "token": -1,
     "prefix": 3, "suffix": 1, "rep": 1, "grade": 5, "hero": 0x01,
     "note": "(Tahl Asel, but with Golem Slayer for all infantry and mage units)",
     "effects": ((0x07DD, -2, 0x78), (0x0BD2, -2, 0), (0x0BD2, 0x04, 0), (0x0BD2, 0x05, 0), (0x0BD2, 0x13, 0), (0x0BD2, 0x19, 0), (0x0BD2, 0x0F, 0), (0x0BD2, 0x12, 0), (0x0BD2, 0x17, 0), (0x0BD2, 0x1A, 0))},

    {"name": "Argonath's Breastplate", "slot": 2, "sprite": 0x41, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Red Pack)",
     "effects": ((0x07E0, -2, 0xF0), (0x0CFC, -2, 0), (0x0FAD, -1, 0))},
    {"name": "Branston's Breastplate", "slot": 2, "sprite": 0x44, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Blue Pack)",
     "effects": ((0x07E0, -2, 0xD2), (0x0CFE, -2, 0), (0x0FAD, -1, 1))},
    {"name": "Leandro's Platemail", "slot": 2, "sprite": 0x47, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Guardian Pack)",
     "effects": ((0x07E0, -2, 200), (0x0CFF, -2, 0), (0x0FAD, -1, 2))},
    {"name": "Hiram's Platemail", "slot": 2, "sprite": 0x4A, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x01,
     "note": "(IAP General Destroyer Pack)",
     "effects": ((0x07E0, -2, 0x10E), (0x0BD0, -2, 0), (0x0FAD, -1, 3))},
    {"name": "Myrtharnith's Sun Robe", "slot": 2, "sprite": 0x4D, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Red Pack)",
     "effects": ((0x0D00, -1, -40), (0x07E6, -2, 200), (0x0FAD, -1, 4))},
    {"name": "Orleaear's Moon Robe", "slot": 2, "sprite": 0x50, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Blue Pack)",
     "effects": ((0x0D01, -1, -20), (0x07E6, -2, 240), (0x0FAD, -1, 5))},
    {"name": "Tyrghymn's Witch Robe", "slot": 2, "sprite": 0x53, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Industrious Pack)",
     "effects": ((0x07E6, -2, 220), (0x07E7, -2, 30), (0x0FAD, -1, 6))},     
    {"name": "Killevalsa's Sorcerer Robe", "slot": 2, "sprite": 0x56, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "note": "(IAP Melwen Avarice Pack)",
     "effects": ((0x0D02, -1, -30), (0x07E6, -2, 210), (0x03F5, -2, 10), (0x0FAD, -1, 7))},
    
    {"name": "Imperial Seal", "slot": 3, "sprite": 0x57, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0DC3, -1, 0),)},
    {"name": "Archangel Statue", "slot": 3, "sprite": 0x59, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0DC4, -1, 0),)},
    {"name": "Golden Goose", "slot": 3, "sprite": 0x5A, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0DC5, -2, 0),)},
    {"name": "Book of War", "slot": 3, "sprite": 0x58, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0DC6, -2, 0),)},
    {"name": "Cloak of Invisibility", "slot": 2, "sprite": 0x13, "token": 0x05,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0BD1, -1, 0),)},
    {"name": "Merry Roper's Ale Bottle", "slot": 3, "sprite": 0x33, "token": -1,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x0BDC, -2, 0), (0, -2, 0))},
    {"name": "Endless Purse of Gold", "slot": 3, "sprite": 0x12, "token": 0x11,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x02, -1, 0x0A),)},
    {"name": "Vahn's Amulet", "slot": 3, "sprite": 0x14, "token": 0x21,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x07DF, -2, 0x03E8),)},
    {"name": "Juleck's Amulet", "slot": 3, "sprite": 0x16, "token": 0x16,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "effects": ((0x07DF, -2, 0x0258),)},
)


RENAME_NOTE = "(Renamed to remove hardcoded Reputation requirement)"


def _renamed(source, new_name):
    """A copy of a preset under a name the reputation check will not match."""
    copy = dict(source)
    copy["name"] = new_name
    copy["note"] = RENAME_NOTE
    return copy


def _with_renames(presets):
    """Place each renamed duplicate directly below the item it copies."""
    renames = {
        "Regalia of Dominion": "Regalia of Dominian",
        "Tahl Asel": "Thal Asel",
        "Merry Roper's Ale Bottle": "Merry Roper'z Ale Bottle",
    }
    out = []
    for preset in presets:
        out.append(preset)
        if preset["name"] in renames:
            out.append(_renamed(preset, renames[preset["name"]]))
    return tuple(out)


PRESETS = _with_renames(PRESETS)


def preset_record(preset):
    """Assemble a preset into the full on-disk record."""
    tail = struct.pack("<7i", preset["sprite"], preset["token"], preset["prefix"],
                       preset["suffix"], preset["rep"], preset["grade"],
                       preset["hero"])
    for effect in preset["effects"]:
        tail += struct.pack("<3i", *effect)
    tail += b"\x00" * (ITEM_TAIL - len(tail))
    return (ITEM_SENTINEL + struct.pack("<i", preset["slot"])
            + preset["name"].encode("latin-1") + b"\x00" + tail)


def item_name_bounds(buf, start):
    """Offsets of the string identifier: its first byte and its terminator."""
    nul = buf.find(b"\x00", start + 8)
    return start + 8, nul


def item_end(buf, start):
    return item_name_bounds(buf, start)[1] + 1 + ITEM_TAIL


def item_name(buf, start):
    first, nul = item_name_bounds(buf, start)
    return bytes(buf[first:nul]).decode("latin-1")


def item_slot(buf, start):
    return read_dword(buf, start + 4)


def item_field_offset(buf, start, index):
    return item_name_bounds(buf, start)[1] + 1 + index * 4


def item_changed(profile, item):
    return bytes(profile[item["start"]:item_end(profile, item["start"])]) \
        != item["original"]


def item_preview(profile, item, index):
    """Current value of a tail field, or 'old -> new' against the original."""
    new = read_dword(profile, item_field_offset(profile, item["start"], index))
    old = read_dword(item["original"], item_field_offset(item["original"], 0, index))
    return "%d" % new if old == new else "%d -> %d" % (old, new)


def build_equipment(profile, heroes):
    """The five equipment records following each hero block."""
    equip = {}
    for name in ("General", "Melwen"):
        pos = heroes[name]["end"] + EQUIP_AFTER
        slots = []
        for _ in EQUIP_SLOTS:
            if profile[pos:pos + 4] != ITEM_SENTINEL:
                return None
            first, nul = item_name_bounds(profile, pos)
            if nul == -1:
                return None
            end = nul + 1 + ITEM_TAIL
            if end > len(profile):
                return None
            slots.append({"start": pos, "original": bytes(profile[pos:end])})
            pos = end
        equip[name] = slots
    return equip


def refresh_equipment(profile, equipment):
    """Re-snapshot every record so a saved change stops counting as pending."""
    if not equipment:
        return
    for slots in equipment.values():
        for item in slots:
            item["original"] = bytes(
                profile[item["start"]:item_end(profile, item["start"])])


def shift_bundle(bundle, pos, delta):
    """Move every cached offset at or past pos, after a length change."""
    def s(off):
        return off + delta if off >= pos else off

    bundle["token"] = s(bundle["token"])
    for hero in bundle["heroes"].values():
        hero["base"] = s(hero["base"])
        hero["end"] = s(hero["end"])
        hero["fields"] = [(l, s(o), n) for l, o, n in hero["fields"]]
    for key in ("gmaps", "mmaps"):
        if bundle[key]:
            for entry in bundle[key]:
                entry["fields"] = [(l, s(o), n) for l, o, n in entry["fields"]]
    if bundle["equip"]:
        for slots in bundle["equip"].values():
            for item in slots:
                item["start"] = s(item["start"])


def splice(profile, baseline, bundle, a, b, new):
    """Replace profile[a:b], keeping baseline the same length and aligned."""
    delta = len(new) - (b - a)
    profile[a:b] = new
    baseline[a:b] = new
    if delta:
        shift_bundle(bundle, b, delta)


def pause(message):
    print("\n" + message)
    try:
        input("\n  Press Enter to continue: ")
    except (EOFError, KeyboardInterrupt):
        pass


def choose_dword(profile, page, label, offset, options):
    """Pick a value from a fixed list rather than typing one."""
    header("%s > %s" % (page, label))
    print(THIN)
    current_val = read_dword(profile, offset)
    current_str = next((text for text, val in options if val == current_val), str(current_val))
    print("  Current value: %s" % current_str)
    print()
    for n, (text, _) in enumerate(options, 1):
        print("  %d. %s" % (n, text))
    print("  %d. Back" % (len(options) + 1))

    choice = menu_choice(len(options) + 1)
    if choice is None or choice == len(options) + 1:
        return
    write_dword(profile, offset, options[choice - 1][1])


def edit_item_name(profile, baseline, bundle, page, item):
    first, nul = item_name_bounds(profile, item["start"])
    header("%s > Name" % page)
    print(THIN)
    current = bytes(profile[first:nul]).decode("latin-1")
    print("  Current name: %s" % (current if current else "(empty)"))

    answer = ask("\n  Enter the new name, or Q to cancel: ")
    if answer is None:
        return
    try:
        raw = answer.encode("latin-1")
    except UnicodeEncodeError:
        pause("  That name uses characters the game cannot store.")
        return
    splice(profile, baseline, bundle, first, nul + 1, raw + b"\x00")


def delete_item(profile, baseline, bundle, item):
    """Overwrite the item with an unequipped slot and zeroed fields."""
    record = ITEM_SENTINEL + struct.pack("<i", -1) + b"\x00" * (1 + ITEM_TAIL)
    splice(profile, baseline, bundle, item["start"], item_end(profile, item["start"]), record)


def preset_page(profile, baseline, bundle, page, item, hero, expected_slot):
    """Replace the whole record with a preset that fits this slot and hero."""
    bit = PRESET_HERO_BIT[hero]
    matching = [p for p in PRESETS
                if p["slot"] == expected_slot and p["hero"] & bit]

    header("%s > Preset Items" % page)
    print(THIN)
    if not matching:
        pause("  No presets are available for this slot.")
        return
    for n, preset in enumerate(matching, 1):
        note = preset.get("note")
        print("  %d. %s%s" % (n, preset["name"], " %s" % note if note else ""))
    print("  %d. Back" % (len(matching) + 1))

    choice = menu_choice(len(matching) + 1)
    if choice is None or choice == len(matching) + 1:
        return False # <-- Now returns False instead of None
    record = preset_record(matching[choice - 1])
    splice(profile, baseline, bundle, item["start"],
           item_end(profile, item["start"]), record)
    return True # <-- Added to signal a successful edit


def manual_editing_page(profile, baseline, bundle, page, item):
    rep_map = {v: k for k, v in REPUTATION_OPTIONS}
    grade_map = {v: k for k, v in GRADE_OPTIONS}
    slot_map = {v: k for k, v in SLOT_OPTIONS}
    suffix_map = {v: k for k, v in SUFFIX_OPTIONS}
    
    header("%s > WARNING" % page)
    print(THIN)
    print("  Editing values manually, especially an unequipped slot,")
    print("  can result in a corrupted record and brick your save.")
    print("  Only proceed if you know exactly what you are doing.")
    print()
    print("  1. I understand, continue")
    print("  2. Go back")
    
    if menu_choice(2) != 1:
        return

    while True:
        header("%s > Manual Editing" % page)
        print(THIN)
        print("  1. %-20s %s" % ("Name", item_name(profile, item["start"]) or "(empty)"))
        
        raw_new_slot = item_slot(profile, item["start"])
        raw_old_slot = item_slot(baseline, item["start"])
        str_new_slot = slot_map.get(raw_new_slot, str(raw_new_slot))
        str_old_slot = slot_map.get(raw_old_slot, str(raw_old_slot))
        slot_shown = str_new_slot if raw_old_slot == raw_new_slot else "%s -> %s" % (str_old_slot, str_new_slot)
        
        print("  2. %-20s %s" % ("Equipment Slot", slot_shown))
        
        for n, (name, idx) in enumerate(ITEM_FIELDS, 3):
            raw_new = read_dword(profile, item_field_offset(profile, item["start"], idx))
            raw_old = read_dword(item["original"], item_field_offset(item["original"], 0, idx))
            
            if name == "Which Hero":
                shown = hero_label(raw_new) if raw_old == raw_new else "%s -> %s" % (hero_label(raw_old), hero_label(raw_new))
            elif name == "Reputation Tier":
                str_new = rep_map.get(raw_new, str(raw_new))
                str_old = rep_map.get(raw_old, str(raw_old))
                shown = str_new if raw_old == raw_new else "%s -> %s" % (str_old, str_new)
            elif name == "Grade":
                str_new = grade_map.get(raw_new, str(raw_new))
                str_old = grade_map.get(raw_old, str(raw_old))
                shown = str_new if raw_old == raw_new else "%s -> %s" % (str_old, str_new)
            elif name == "Suffix Count":
                str_new = suffix_map.get(raw_new, str(raw_new))
                str_old = suffix_map.get(raw_old, str(raw_old))
                shown = str_new if raw_old == raw_new else "%s -> %s" % (str_old, str_new)
            else:
                shown = item_preview(profile, item, idx)
                
            print("  %d. %-20s %s" % (n, name, shown))
        
        print("  10. Delete Item")
        print("  11. Back")

        choice = menu_choice(11)
        if choice is None or choice == 11:
            return
        if choice == 1:
            edit_item_name(profile, baseline, bundle, page, item)
        elif choice == 2:
            choose_dword(profile, page, "Equipment Slot", item["start"] + 4, SLOT_OPTIONS)
        elif choice == 10:
            delete_item(profile, baseline, bundle, item)
            #return
        else:
            name, idx = ITEM_FIELDS[choice - 3]
            offset = item_field_offset(profile, item["start"], idx)
            if name == "Suffix Count":
                choose_dword(profile, page, name, offset, SUFFIX_OPTIONS)
            elif name == "Reputation Tier":
                choose_dword(profile, page, name, offset, REPUTATION_OPTIONS)
            elif name == "Grade":
                choose_dword(profile, page, name, offset, GRADE_OPTIONS)
            elif name == "Which Hero":
                choose_dword(profile, page, name, offset, HERO_OPTIONS)
            else:
                notes = (TOKEN_VALUE_NOTE,) if name == "Token Value" else ()
                edit_field(profile, baseline, page, name, offset, notes)


def item_page(profile, baseline, bundle, hero, index, item):
    label, slot_value = EQUIP_SLOTS[index]
    page = "%s ITEMS > %s" % (hero.upper(), label)

    while True:
        header(page)
        print(THIN)
        print("  1. Preset Items")
        print("  2. Manual Editing")
        print("  3. Delete Item")
        print("  4. Back")

        choice = menu_choice(4)
        if choice is None or choice == 4:
            return
        
        if choice == 1:
            # Check for the True flag from preset_page
            if preset_page(profile, baseline, bundle, page, item, hero, slot_value):
                return
        elif choice == 2:
            manual_editing_page(profile, baseline, bundle, page, item)
            return
        elif choice == 3:
            delete_item(profile, baseline, bundle, item)
            return # <-- Added so simple deletion bounces back a menu


def items_page(profile, baseline, bundle, hero):
    while True:
        header("%s ITEMS" % hero.upper())
        print(THIN)
        slots = bundle["equip"][hero]
        for n, ((label, _), item) in enumerate(zip(EQUIP_SLOTS, slots), 1):
            if item_slot(profile, item["start"]) == UNEQUIPPED:
                shown = "No Item"
            else:
                shown = item_name(profile, item["start"]) or "(empty)"
            if item_changed(profile, item):
                shown += "   (edited)"
            print("  %d. %-14s %s" % (n, label, shown))
        print("  %d. Back" % (len(slots) + 1))

        choice = menu_choice(len(slots) + 1)
        if choice is None or choice == len(slots) + 1:
            return
        item_page(profile, baseline, bundle, hero, choice - 1, slots[choice - 1])


def equipment_page(profile, baseline, bundle):
    while True:
        header("EQUIPMENT EDITOR")
        print(THIN)
        for n, hero in enumerate(("General", "Melwen"), 1):
            changed = sum(1 for item in bundle["equip"][hero]
                          if item_changed(profile, item))
            note = ("(%d edited)" % changed) if changed else ""
            row = "  %d. %s Items" % (n, hero)
            print(row.ljust(28) + note if note else row)
        print("  3. Back")

        choice = menu_choice(3)
        if choice is None or choice == 3:
            return
        items_page(profile, baseline, bundle, "General" if choice == 1 else "Melwen")


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


def maps_page(profile, baseline, maps, title="GENERAL MAPS"):
    while True:
        header(title)
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
        field_page(profile, baseline, "%s > %s" % (title, entry["name"]),
                   entry["fields"])


def main_menu(profile, baseline, bundle, state, commit):
    """Returns when the user exits. commit(profile) performs the save."""
    status = ""
    while True:
        # Re-read every loop: editing an item name changes the payload length
        # and shifts every offset after it.
        heroes = bundle["heroes"]
        general_maps = bundle["gmaps"]
        melwen_maps = bundle["mmaps"]
        equipment = bundle["equip"]
        token_offset = bundle["token"]

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

        gen_map_offsets = [off for entry in general_maps for _, off, _ in entry["fields"]] if general_maps else []
        changed = count_pending(profile, baseline, gen_map_offsets)
        note = ("(%d unsaved change%s)"
                % (changed, "" if changed == 1 else "s")) if changed else ""
        row = "  4. General Maps"
        print(row.ljust(28) + note if note else row)

        mel_map_offsets = [off for entry in melwen_maps for _, off, _ in entry["fields"]] if melwen_maps else []
        changed = count_pending(profile, baseline, mel_map_offsets)
        note = ("(%d unsaved change%s)"
                % (changed, "" if changed == 1 else "s")) if changed else ""
        row = "  5. Melwen Maps"
        if melwen_maps:
            print(row.ljust(28) + note if note else row)
        else:
            print(row.ljust(28) + "(Not found)")

        row = "  6. Equipment Editor"
        if equipment:
            changed = sum(1 for slots in equipment.values()
                          for item in slots if item_changed(profile, item))
            note = ("(%d edited)" % changed) if changed else ""
            print(row.ljust(28) + note if note else row)
        else:
            print(row.ljust(28) + "(Not found)")

        print("  7. Save")
        print("  8. Exit")
        if status:
            print("\n" + status)

        choice = menu_choice(8)
        if choice is None:
            choice = 8
        status = ""

        if choice == 1:
            edit_field(profile, baseline, "MAIN MENU", "Token Count", token_offset)

        elif choice in (2, 3):
            name = "General" if choice == 2 else "Melwen"
            field_page(profile, baseline, "%s STATS \n" % name.upper(),
                       heroes[name]["fields"], GUIDANCE)

        elif choice == 4:
            maps_page(profile, baseline, general_maps, "GENERAL MAPS")
            
        elif choice == 5 and melwen_maps:
            maps_page(profile, baseline, melwen_maps, "MELWEN MAPS")

        elif choice == 6 and equipment:
            equipment_page(profile, baseline, bundle)

        elif choice == 7:
            status = commit(profile)
            if status is None:
                baseline[:] = profile
                refresh_equipment(profile, equipment)
                status = ""

        else:
            all_offsets = [token_offset] + gen_map_offsets + mel_map_offsets
            for hero in heroes.values():
                all_offsets += [off for _, off, _ in hero["fields"]]
            changed = count_pending(profile, baseline, all_offsets)
            if equipment:
                changed += sum(1 for slots in equipment.values()
                               for item in slots if item_changed(profile, item))
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

    #backup = original_path + datetime.now().strftime(".%Y%m%d-%H%M%S.bak")
    #os.replace(original_path, backup)
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

    general_maps = build_maps(profile)
    if general_maps is None:
        return
        
    melwen_maps = build_melwen_maps(profile)

    equipment = build_equipment(profile, heroes)

    baseline = bytearray(profile)
    bundle = {
        "heroes": heroes,
        "gmaps": general_maps,
        "mmaps": melwen_maps,
        "equip": equipment,
        "token": heroes["General"]["base"] - TOKEN_BACK,
    }
    state = {"path": path}

    def commit(current):
        """Returns None on success, or a status line describing the failure."""
        try:
            state["path"] = save_plist(state["path"], plist, bytes(current))
        except Exception as error:
            return "  Save failed, so the save file was left alone: %s" % error
        return None

    main_menu(profile, baseline, bundle, state, commit)


if __name__ == "__main__":
    main()
