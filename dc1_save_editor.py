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
    {"name": "Coronet of the Supreme Magi", "slot": 0, "sprite": 0x34, "token": 0x02A8,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x04,
     "effects": ((0x03EF, -2, 0x0A), (0x03F0, -2, 0x0A), (0x03F2, -2, 0x0A),
                 (0x03F4, -2, 0x0A), (0x03F5, -2, 0x0A), (0x07E5, -2, 0x0118))},
    
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
     "note": "(IAP Accessory)",
     "effects": ((0x0DC3, -1, 0),)},
    {"name": "Archangel Statue", "slot": 3, "sprite": 0x59, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "note": "(IAP Accessory)",
     "effects": ((0x0DC4, -1, 0),)},
    {"name": "Golden Goose", "slot": 3, "sprite": 0x5A, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "note": "(IAP Accessory)",
     "effects": ((0x0DC5, -2, 0),)},
    {"name": "Book of War", "slot": 3, "sprite": 0x58, "token": -2,
     "prefix": 0, "suffix": 0, "rep": 1, "grade": 0, "hero": 0x0F,
     "note": "(IAP Accessory)",
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
    {"name": "Toerag's Spellbook", "slot": 3, "sprite": 0x58, "token": -1,
     "prefix": 2, "suffix": 1, "rep": 1, "grade": 5, "hero": 0x04,
     "note": "(0 Cost Armageddon)",
     "effects": ((0x0BDA, -1, 0x2E9), (0x0D00, -1, -160),
                 (0x07DD, 0x05, 0x2D), (0x07E5, -2, 0xB8))},
    {"name": "Fun", "slot": 3, "sprite": 0x2A, "token": 0x0F74,
     "prefix": 1, "suffix": 1, "rep": 1, "grade": 5, "hero": 0x04,
     "note": "(0 Cost Meteor Shower)",
     "effects": ((0x0BDD, -1, 0xBE), (0x0D02, -1, -100),
                 (0x07DD, 0x05, 0x2D), (0x07E5, -2, 0xB8))},
    {"name": "IDDQD", "slot": 3, "sprite": 0x2E, "token": 0x0300,
     "prefix": 0, "suffix": 1, "rep": 1, "grade": 5, "hero": 0x04,
     "note": "(0 Cost Healing)",
     "effects": ((0x0BD8, -1, 0x3C3), (0x07E5, -2, 0xB8),
                 (0x0D01, -1, -40), (0x07DD, 0x05, 0x2D))},
)

# ---------------------------------------------------------------- generation data
E_GATE = 0x01; E_GOLD = 0x02; E_CMBT = 0x03EB
E_MORALE = 0x03EC; E_CUNN = 0x03EE; E_INFC = 0x03EF
E_BOWC = 0x03F0; E_MAGC = 0x03F2; E_SORC = 0x03F3
E_WISD = 0x03F4; E_POWR = 0x03F5; E_ATK = 0x07DD
E_RAD = 0x07DE; E_HLTH = 0x07DF; E_ARMOR = 0x07E0
E_MOVE = 0x07E3; E_SPLP = 0x07E5; E_MANA = 0x07E6
E_MANAREC = 0x07E7; E_RES = 0x07E8; E_RAGE = 0x0BCD
E_GREED = 0x0BCE; E_POIS = 0x0BCF; E_POISIM = 0x0BD0
E_ICE = 0x0BD7; E_LTNG = 0x0BD6; E_HEAL = 0x0BD8
E_ARMA = 0x0BDA; E_METR = 0x0BDD

T_HERO = -2; T_ALL = -1
U_WAR = 0x04; U_BER = 0x05; U_ARC = 0x0B
U_RAN = 0x0C; U_MAG = 0x0F; U_HAL = 0x17

BASE_ITEMS = {
    "General": {
        0: [
            ("Cap", 2, 2, [(E_ARMOR, T_HERO, 1)]),
            ("Studded Cap", 3, 2, [(E_ARMOR, T_HERO, 2)]),
            ("Leather Cap", 4, 30, [(E_ARMOR, T_HERO, 3)]),
            ("Bronze Cap", 5, 30, [(E_ARMOR, T_HERO, 4)]),
            ("Captain's Cap", 8, 30, [(E_ARMOR, T_HERO, 4), (E_MORALE, T_HERO, 1)]),
            ("Bronze Helm", 10, 2, [(E_ARMOR, T_HERO, 5)]),
            ("Iron Helm", 10, 0, [(E_ARMOR, T_HERO, 8)]),
            ("Steel Helm", 15, 0, [(E_ARMOR, T_HERO, 12)]),
            ("Silver Helm", 20, 0, [(E_ARMOR, T_HERO, 16)]),
            ("Imperial Helm", 30, 1, [(E_ARMOR, T_HERO, 20)]),
            ("Military Helm", 40, 34, [(E_ARMOR, T_HERO, 15), (E_INFC, T_HERO, 1), (E_BOWC, T_HERO, 1), (E_MAGC, T_HERO, 1)]),
            ("Crown", 40, 3, [(E_INFC, T_HERO, 5), (E_BOWC, T_HERO, 5), (E_MAGC, T_HERO, 5)]),
            ("Full Helm", 50, 31, [(E_ARMOR, T_HERO, 25)]),
            ("Horned Helm", 60, 33, [(E_ARMOR, T_HERO, 20), (E_ATK, T_HERO, 12)]),
            ("Rider's Helm", 64, 34, [(E_ARMOR, T_HERO, 24), (E_BOWC, T_HERO, 4), (E_MAGC, T_HERO, 4)]),
            ("Adamantium Helm", 80, 32, [(E_ARMOR, T_HERO, 30)]),
            ("Grand Helm", 120, 32, [(E_ARMOR, T_HERO, 30), (E_CMBT, T_HERO, 5), (E_MORALE, T_HERO, 5), (E_INFC, T_HERO, 5), (E_BOWC, T_HERO, 5)]),
        ],
        1: [
            ("Dagger", 1, 6, [(E_ATK, T_HERO, 3)]),
            ("Elven Dagger", 2, 6, [(E_ATK, T_HERO, 7), (E_CMBT, T_HERO, 1)]),
            ("Iron Shortsword", 2, 6, [(E_ATK, T_HERO, 5)]),
            ("Steel Shortsword", 3, 6, [(E_ATK, T_HERO, 7)]),
            ("Silver Shortsword", 4, 6, [(E_ATK, T_HERO, 10)]),
            ("Iron Sabre", 8, 40, [(E_ATK, T_HERO, 10)]),
            ("Iron Mace", 12, 4, [(E_ATK, T_HERO, 35)]),
            ("Steel Sabre", 13, 40, [(E_ATK, T_HERO, 12)]),
            ("Iron Axe", 16, 5, [(E_ATK, T_HERO, 60), (E_MOVE, T_HERO, -1)]),
            ("Silver Sabre", 17, 40, [(E_ATK, T_HERO, 15)]),
            ("Steel Mace", 18, 4, [(E_ATK, T_HERO, 45)]),
            ("Barbarian Mace", 24, 4, [(E_ATK, T_HERO, 50), (E_INFC, T_HERO, 1), (E_BOWC, T_HERO, 1)]),
            ("Silver Mace", 24, 4, [(E_ATK, T_HERO, 55)]),
            ("Iron Longsword", 24, 39, [(E_ATK, T_HERO, 45)]),
            ("Steel Axe", 24, 5, [(E_ATK, T_HERO, 70), (E_MOVE, T_HERO, -1)]),
            ("War Axe", 30, 5, [(E_ATK, T_HERO, 70), (E_MOVE, T_HERO, -1), (E_MORALE, T_HERO, 2), (E_CUNN, T_HERO, 2)]),
            ("Iron Greatsword", 32, 37, [(E_ATK, T_HERO, 70), (E_MOVE, T_HERO, -1)]),
            ("Silver Axe", 32, 5, [(E_ATK, T_HERO, 80), (E_MOVE, T_HERO, -1)]),
            ("Steel Longsword", 45, 39, [(E_ATK, T_HERO, 60)]),
            ("Elven Sword", 60, 39, [(E_ATK, T_HERO, 65), (E_CMBT, T_HERO, 2)]),
            ("Steel Greatsword", 60, 37, [(E_ATK, T_HERO, 85), (E_MOVE, T_HERO, -1)]),
            ("Silver Longsword", 72, 39, [(E_ATK, T_HERO, 75)]),
            ("Slayer Sword", 75, 37, [(E_ATK, T_HERO, 90), (E_MOVE, T_HERO, -1), (E_CMBT, T_HERO, 2), (E_CUNN, T_HERO, 2)]),
            ("Silver Greatsword", 96, 37, [(E_ATK, T_HERO, 100), (E_MOVE, T_HERO, -1)]),
            ("Adamantium Greatsword", 160, 38, [(E_ATK, T_HERO, 130), (E_MOVE, T_HERO, -2)]),
        ],
        2: [
            ("Leatherskin", 5, 12, [(E_ARMOR, T_HERO, 7)]),
            ("Bronze Breastplate", 10, 9, [(E_ARMOR, T_HERO, 10)]),
            ("Iron Breastplate", 20, 11, [(E_ARMOR, T_HERO, 15)]),
            ("Bronze Platemail", 25, 36, [(E_ARMOR, T_HERO, 15)]),
            ("Steel Breastplate", 30, 11, [(E_ARMOR, T_HERO, 20)]),
            ("Silver Breastplate", 40, 11, [(E_ARMOR, T_HERO, 25)]),
            ("Orc Breastplate", 45, 10, [(E_ARMOR, T_HERO, 20), (E_CMBT, T_HERO, 2), (E_INFC, T_HERO, 2)]),
            ("Iron Platemail", 50, 35, [(E_ARMOR, T_HERO, 25)]),
            ("Imperial Breastplate", 60, 7, [(E_ARMOR, T_HERO, 30)]),
            ("Steel Platemail", 70, 35, [(E_ARMOR, T_HERO, 35)]),
            ("Adamantium Breastplate", 80, 8, [(E_ARMOR, T_HERO, 40)]),
            ("Silver Platemail", 90, 35, [(E_ARMOR, T_HERO, 45)]),
        ],
        3: [
            ("Iron Ring", 1, 14, []), ("Steel Ring", 3, 14, []), ("Amulet", 4, 17, []),
            ("Silver Ring", 8, 14, []), ("Necklace", 10, 16, []), ("Charm", 15, 43, []),
            ("Imperial Ring", 18, 13, []), ("Jewel Ring", 20, 41, []), ("Leather Bracer", 21, 45, []),
            ("Iron Greaves", 22, 58, []), ("Bracelet", 24, 47, []), ("Iron Bracer", 25, 44, []),
            ("Steel Greaves", 26, 58, []), ("Steel Bracer", 29, 44, []), ("Adamantium Ring", 30, 15, []),
            ("Silver Greaves", 30, 58, []), ("Silver Bracer", 33, 44, []), ("Cape", 40, 48, []),
        ]
    },
    "Melwen": {
        0: [
            ("Cap", 2, 2, [(E_ARMOR, T_HERO, 1)]),
            ("Studded Cap", 3, 2, [(E_ARMOR, T_HERO, 2)]),
            ("Leather Cap", 4, 30, [(E_ARMOR, T_HERO, 3)]),
            ("Bronze Cap", 5, 30, [(E_ARMOR, T_HERO, 4)]),
            ("Tiara", 10, 49, [(E_SPLP, T_HERO, 30)]),
            ("Major Tiara", 18, 49, [(E_SPLP, T_HERO, 48)]),
            ("Coronet", 25, 52, [(E_SPLP, T_HERO, 60)]),
            ("Relic Tiara", 28, 49, [(E_SPLP, T_HERO, 64)]),
            ("Major Coronet", 40, 52, [(E_SPLP, T_HERO, 75)]),
            ("Crown", 40, 3, [(E_INFC, T_HERO, 5), (E_BOWC, T_HERO, 5), (E_MAGC, T_HERO, 5)]),
            ("Relic Coronet", 55, 52, [(E_SPLP, T_HERO, 90)]),
            ("Tiara of Enlightenment", 78, 49, [(E_SPLP, T_HERO, 36), (E_SORC, T_HERO, 5), (E_WISD, T_HERO, 5), (E_POWR, T_HERO, 5)]),
        ],
        1: [
            ("Ice Wand", 18, 54, [(E_ICE, T_ALL, -1), (E_ATK, T_HERO, 30)]),
            ("Lightning Wand", 24, 55, [(E_LTNG, T_ALL, -1), (E_ATK, T_HERO, 55)]),
            ("Major Ice Wand", 42, 54, [(E_ICE, T_ALL, -1), (E_ATK, T_HERO, 50)]),
            ("Ancient Lightning Wand", 46, 55, [(E_LTNG, T_ALL, -1), (E_ATK, T_HERO, 68), (E_WISD, T_HERO, 1), (E_POWR, T_HERO, 1)]),
            ("Major Lightning Wand", 54, 55, [(E_LTNG, T_ALL, -1), (E_ATK, T_HERO, 80)]),
            ("Runic Ice Wand", 74, 54, [(E_ICE, T_ALL, -1), (E_ATK, T_HERO, 60), (E_POWR, T_HERO, 4)]),
            ("Relic Ice Wand", 92, 54, [(E_ICE, T_ALL, -1), (E_ATK, T_HERO, 70)]),
            ("Relic Lightning Wand", 122, 55, [(E_LTNG, T_ALL, -1), (E_ATK, T_HERO, 105)]),
        ],
        2: [
            ("Leather Mantle", 4, 61, [(E_MANA, T_HERO, 6)]),
            ("Dragon Hide Mantle", 4, 61, [(E_MANA, T_HERO, 6), (E_ATK, T_HERO, 20)]),
            ("Leatherskin", 5, 12, [(E_ARMOR, T_HERO, 7)]),
            ("Cotton Mantle", 8, 61, [(E_MANA, T_HERO, 10)]),
            ("Leather Cloak", 10, 60, [(E_MANA, T_HERO, 12)]),
            ("Silk Mantle", 12, 61, [(E_MANA, T_HERO, 14)]),
            ("Cotton Cloak", 25, 60, [(E_MANA, T_HERO, 18)]),
            ("Leather Robe", 30, 59, [(E_MANA, T_HERO, 20)]),
            ("Silk Cloak", 40, 60, [(E_MANA, T_HERO, 25)]),
            ("Cotton Robe", 50, 59, [(E_MANA, T_HERO, 30)]),
            ("Vampire's Cowl", 60, 60, [(E_MANA, T_HERO, 25), (E_SPLP, T_HERO, 20), (E_SORC, T_HERO, 1), (E_POWR, T_HERO, 1)]),
            ("Silk Robe", 75, 59, [(E_MANA, T_HERO, 40)]),
            ("Sorceress Robe", 80, 59, [(E_MANA, T_HERO, 30), (E_SORC, T_HERO, 2), (E_MAGC, T_HERO, 2)]),
        ],
        3: [
            ("Iron Ring", 1, 14, []), ("Steel Ring", 3, 14, []), ("Amulet", 4, 17, []),
            ("Silver Ring", 8, 14, []), ("Necklace", 10, 16, []), ("Charm", 15, 43, []),
            ("Imperial Ring", 18, 13, []), ("Jewel Ring", 20, 41, []), ("Leather Bracer", 21, 45, []),
            ("Bracelet", 24, 47, []), ("Adamantium Ring", 30, 15, []), ("Cape", 40, 48, []),
            ("Orb of Healing", 10, 42, [(E_HEAL, T_ALL, 100), (E_MANA, T_HERO, 10)]),
            ("Talisman of Healing", 10, 46, [(E_HEAL, T_ALL, 100), (E_SPLP, T_HERO, 20)]),
            ("Orb of Meteor Shower", 30, 42, [(E_METR, T_ALL, 20), (E_MANA, T_HERO, 10)]),
            ("Talisman of Meteor Shower", 30, 46, [(E_METR, T_ALL, 20), (E_SPLP, T_HERO, 20)]),
            ("Orb of Armageddon", 40, 42, [(E_ARMA, T_ALL, 80), (E_MANA, T_HERO, 10)]),
            ("Talisman of Armageddon", 40, 46, [(E_ARMA, T_ALL, 80), (E_SPLP, T_HERO, 20)]),
        ]
    }
}

GEN_SUFFIXES = [
    ("Protection", [(E_GATE, T_ALL, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Guardian", [(E_GATE, T_ALL, 2)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Archangel", [(E_GATE, T_ALL, 3)], [3], ["General", "Melwen"]),
    ("the Leprechaun", [(E_GOLD, T_ALL, 2)], [3], ["General", "Melwen"]),
    ("the Gladiator", [(E_INFC, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Paladin", [(E_INFC, T_HERO, 2)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Cyclops", [(E_INFC, T_HERO, 3)], [3], ["General", "Melwen"]),
    ("the Marksman", [(E_BOWC, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Sharpshooter", [(E_BOWC, T_HERO, 2)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Roc", [(E_BOWC, T_HERO, 3)], [3], ["General", "Melwen"]),
    ("the Sage", [(E_MAGC, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Archmage", [(E_MAGC, T_HERO, 2)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Pegasus", [(E_MAGC, T_HERO, 3)], [3], ["General", "Melwen"]),
    
    ("the Conqueror", [(E_CMBT, T_HERO, 1)], [0, 1, 2, 3], ["General"]),
    ("Titan", [(E_CMBT, T_HERO, 2)], [0, 1, 2, 3], ["General"]),
    ("the Dragon", [(E_CMBT, T_HERO, 3)], [3], ["General"]),
    ("the Hero", [(E_MORALE, T_HERO, 1)], [0, 1, 2, 3], ["General"]),
    ("Courage", [(E_MORALE, T_HERO, 2)], [0, 1, 2, 3], ["General"]),
    ("the Griffon", [(E_MORALE, T_HERO, 3)], [3], ["General"]),
    ("the Diplomat", [(E_CUNN, T_HERO, 1)], [0, 1, 2, 3], ["General"]),
    ("Devious", [(E_CUNN, T_HERO, 2)], [0, 1, 2, 3], ["General"]),
    ("the Harpy", [(E_CUNN, T_HERO, 3)], [3], ["General"]),
    ("the Bear", [(E_ATK, T_HERO, 10)], [0, 1, 2, 3], ["General"]),
    ("the Centaur", [(E_ATK, T_HERO, 20)], [0, 1, 2, 3], ["General"]),
    ("the Minotaur", [(E_ATK, T_HERO, 30)], [3], ["General"]),
    ("the Collossus", [(E_HLTH, T_HERO, 50)], [0, 1, 2, 3], ["General"]),
    ("the Hydra", [(E_HLTH, T_HERO, 75)], [3], ["General"]),
    ("the Sentinel", [(E_ARMOR, T_HERO, 10)], [0, 1, 2, 3], ["General"]),
    ("the Basilisk", [(E_ARMOR, T_HERO, 15)], [3], ["General"]),
    ("Rage", [(E_RAGE, T_HERO, 0)], [0, 1], ["General"]),
    ("Avarice", [(E_GREED, T_HERO, 0)], [0, 3], ["General"]),
    ("Venom", [(E_POIS, T_HERO, 0)], [1, 3], ["General"]),
    ("Antidote", [(E_POISIM, T_HERO, 0)], [2, 3], ["General"]),
    
    ("the Mammoth", [(E_HLTH, T_HERO, 25)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Fortitude", [(E_ARMOR, T_HERO, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Wind", [(E_MOVE, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    
    ("the Witch", [(E_SORC, T_HERO, 1)], [0, 1, 2, 3], ["Melwen"]),
    ("Genie", [(E_SORC, T_HERO, 2)], [0, 1, 2, 3], ["Melwen"]),
    ("the Phoenix", [(E_SORC, T_HERO, 3)], [3], ["Melwen"]),
    ("the Scholar", [(E_WISD, T_HERO, 1)], [0, 1, 2, 3], ["Melwen"]),
    ("Great Owl", [(E_WISD, T_HERO, 2)], [0, 1, 2, 3], ["Melwen"]),
    ("the Wizard", [(E_WISD, T_HERO, 3)], [3], ["Melwen"]),
    ("the Alchemist", [(E_POWR, T_HERO, 1)], [0, 1, 2, 3], ["Melwen"]),
    ("the Elders", [(E_POWR, T_HERO, 2)], [0, 1, 2, 3], ["Melwen"]),
    ("the Warlock", [(E_POWR, T_HERO, 3)], [3], ["Melwen"]),
    ("Element", [(E_ATK, T_HERO, 15)], [0, 1, 2, 3], ["Melwen"]),
    ("the Medusa", [(E_ATK, T_HERO, 30)], [0, 1, 2, 3], ["Melwen"]),
    ("the Gorgon", [(E_ATK, T_HERO, 45)], [3], ["Melwen"]),
    ("Far Sight", [(E_RAD, T_HERO, 2)], [0, 1, 2, 3], ["Melwen"]),
    ("the Seer", [(E_RAD, T_HERO, 5)], [0, 1, 2, 3], ["Melwen"]),
    ("the Oracle", [(E_RAD, T_HERO, 10)], [3], ["Melwen"]),
    ("Barrier", [(E_RES, T_HERO, 5)], [0, 1, 2, 3], ["Melwen"]),
    ("the Force", [(E_RES, T_HERO, 10)], [0, 1, 2, 3], ["Melwen"]),
    ("the Serpent", [(E_ARMOR, T_HERO, 15)], [3], ["Melwen"]),
    ("Energy", [(E_SPLP, T_HERO, 10)], [0, 1, 2, 3], ["Melwen"]),
    ("the Manticore", [(E_SPLP, T_HERO, 20)], [0, 1, 2, 3], ["Melwen"]),
    ("the Wyvern", [(E_SPLP, T_HERO, 30)], [3], ["Melwen"]),
    ("Knowledge", [(E_MANA, T_HERO, 5)], [0, 1, 2, 3], ["Melwen"]),
    ("the Imp", [(E_MANA, T_HERO, 10)], [0, 1, 2, 3], ["Melwen"]),
    ("the Unicorn", [(E_MANA, T_HERO, 15)], [3], ["Melwen"]),
    ("Willpower", [(E_MANAREC, T_HERO, 5)], [0, 1, 2], ["Melwen"]),
    ("Healing Spell", [(E_HEAL, T_ALL, 100)], [3], ["Melwen"]),
    ("Armageddon Spell", [(E_ARMA, T_ALL, 80)], [3], ["Melwen"]),
    ("Meteor Shower Spell", [(E_METR, T_ALL, 20)], [3], ["Melwen"]),
    
    ("the Champion", [(E_ATK, U_WAR, 10)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Wolf", [(E_HLTH, U_WAR, 40)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Ironskin", [(E_ARMOR, U_WAR, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Wanderer", [(E_MOVE, U_WAR, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Bloodlust", [(E_RAGE, U_WAR, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Snake", [(E_POIS, U_WAR, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Cure", [(E_POISIM, U_WAR, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Slayer", [(E_ATK, U_BER, 20)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Tiger", [(E_HLTH, U_BER, 80)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Steelskin", [(E_ARMOR, U_BER, 10)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Wayfarer", [(E_MOVE, U_BER, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Viper", [(E_POIS, U_BER, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Remedy", [(E_POISIM, U_BER, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Excellent", [(E_ATK, U_ARC, 3)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Eagle Eyes", [(E_RAD, U_ARC, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Wicked", [(E_POIS, U_ARC, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Perfection", [(E_ATK, U_RAN, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Hawk Eyes", [(E_RAD, U_RAN, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Arcane", [(E_ATK, U_MAG, 15)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Vision", [(E_RAD, U_MAG, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Troll", [(E_HLTH, U_MAG, 20)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Wonder", [(E_ATK, U_HAL, 8)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Fox", [(E_HLTH, U_HAL, 30)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Stoneskin", [(E_ARMOR, U_HAL, 3)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("the Nimble", [(E_MOVE, U_HAL, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Chaos", [(E_RAGE, U_HAL, 0)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Poison Ward", [(E_POISIM, U_HAL, 0)], [0, 1, 2, 3], ["General", "Melwen"])
]

GEN_PREFIXES = [
    ("Defender", [(E_GATE, T_ALL, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Glorious", [(E_INFC, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Noble", [(E_BOWC, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Mystic", [(E_MAGC, T_HERO, 1)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Life", [(E_HLTH, T_HERO, 25)], [0, 1, 2, 3], ["General", "Melwen"]),
    ("Blessed", [(E_ARMOR, T_HERO, 5)], [0, 1, 2, 3], ["General", "Melwen"]),
    
    ("Might", [(E_CMBT, T_HERO, 1)], [0, 1, 2, 3], ["General"]),
    ("Brave", [(E_MORALE, T_HERO, 1)], [0, 1, 2, 3], ["General"]),
    ("Witty", [(E_CUNN, T_HERO, 1)], [0, 1, 2, 3], ["General"]),
    ("Knight's", [(E_CMBT, T_HERO, 1)], [1], ["General"]),
    ("Lord's", [(E_CMBT, T_HERO, 1), (E_MORALE, T_HERO, 1)], [1], ["General"]),
    ("King's", [(E_CMBT, T_HERO, 1), (E_MORALE, T_HERO, 1), (E_CUNN, T_HERO, 1)], [1], ["General"]),
    ("Savage", [(E_ATK, T_HERO, 10)], [0, 1, 2, 3], ["General"]),
    ("Brutal", [(E_RAGE, T_HERO, 0)], [0, 1], ["General"]),
    ("Greedy", [(E_GREED, T_HERO, 0)], [0, 3], ["General"]),
    ("Acidic", [(E_POIS, T_HERO, 0)], [1, 3], ["General"]),
    ("Lizard's", [(E_POISIM, T_HERO, 0)], [2, 3], ["General"]),
    
    ("Enchanted", [(E_SORC, T_HERO, 1)], [0, 1, 2, 3], ["Melwen"]),
    ("Clever", [(E_WISD, T_HERO, 1)], [0, 1, 2, 3], ["Melwen"]),
    ("Supreme", [(E_POWR, T_HERO, 1)], [0, 1, 2, 3], ["Melwen"]),
    ("Apprentice's", [(E_SORC, T_HERO, 1)], [1], ["Melwen"]),
    ("Master's", [(E_SORC, T_HERO, 1), (E_WISD, T_HERO, 1)], [1], ["Melwen"]),
    ("Grandmaster's", [(E_SORC, T_HERO, 1), (E_WISD, T_HERO, 1), (E_POWR, T_HERO, 1)], [1], ["Melwen"]),
    ("Imbued", [(E_ATK, T_HERO, 15)], [0, 1, 2, 3], ["Melwen"]),
    ("Keen", [(E_RAD, T_HERO, 2)], [0, 1, 2, 3], ["Melwen"]),
    ("Warding", [(E_RES, T_HERO, 5)], [0, 1, 2, 3], ["Melwen"]),
    ("Radiant", [(E_SPLP, T_HERO, 10)], [0, 1, 2, 3], ["Melwen"]),
    ("Chatty", [(E_MANA, T_HERO, 5)], [0, 1, 2, 3], ["Melwen"]),
    ("Charging", [(E_MANAREC, T_HERO, 5)], [3], ["Melwen"]),
    
    ("Valor", [(E_ATK, U_WAR, 3)], [3], ["General", "Melwen"]),
    ("Merciless", [(E_ATK, U_BER, 5)], [3], ["General", "Melwen"]),
    ("Precision", [(E_ATK, U_ARC, 1)], [3], ["General", "Melwen"]),
    ("Exacto", [(E_ATK, U_RAN, 1)], [3], ["General", "Melwen"]),
    ("Brilliance", [(E_ATK, U_MAG, 5)], [3], ["General", "Melwen"]),
    ("Vigilant", [(E_ATK, U_HAL, 2)], [3], ["General", "Melwen"])
]

# ---------------------------------------------------------------- string translation dictionaries
EFF_STR = {
    E_GATE: "Gate Defense", E_GOLD: "Initial Gold", E_CMBT: "Combat",
    E_MORALE: "Morale", E_CUNN: "Cunning", E_INFC: "Infantry Cmdr",
    E_BOWC: "Bowmen Cmdr", E_MAGC: "Mage Cmdr", E_SORC: "Sorcery",
    E_WISD: "Wisdom", E_POWR: "Power", E_ATK: "Attack Rating",
    E_RAD: "Atk Radius", E_HLTH: "Health Rating", E_ARMOR: "Armor Rating",
    E_MOVE: "Move Speed", E_SPLP: "Spell Power", E_MANA: "Mana Points",
    E_MANAREC: "Mana Recovery", E_RES: "Resist Rating", E_RAGE: "Rage",
    E_GREED: "Greed", E_POIS: "Poison Attack", E_POISIM: "Poison Immunity",
    E_ICE: "Ice Wand Spell", E_LTNG: "Lightning Wand Spell", E_HEAL: "Healing Spell",
    E_ARMA: "Armageddon Spell", E_METR: "Meteor Shower Spell"
}

TGT_STR = {
    T_HERO: "Hero", T_ALL: "Global",
    U_WAR: "Warrior/Paladin", U_BER: "Berserker",
    U_ARC: "Archer/Marksman", U_RAN: "Ranger",
    U_MAG: "Mage/Archmage", U_HAL: "Halfling/Lizardman"
}

def format_eff_list(eff_list):
    """Converts a list of effect tuples into human-readable stat strings."""
    strs = []
    for eff, tgt, val in eff_list:
        t_str = TGT_STR.get(tgt, "Unknown Target")
        e_str = EFF_STR.get(eff, "Unknown Effect")
        if val == 0 or val == -1:
            strs.append("%s %s" % (t_str, e_str))
        else:
            sign = "+" if val > 0 else ""
            strs.append("%s %s %s%d" % (t_str, e_str, sign, val))
    return ", ".join(strs)

def get_max_filtered_enhancements(source_list, hero, slot):
    valid = [e for e in source_list if hero in e[3] and slot in e[2]]
    max_vals = {}
    for entry in valid:
        for eff, tgt, val in entry[1]:
            max_vals[(eff, tgt)] = max(max_vals.get((eff, tgt), -999999), val)
            
    filtered = []
    for entry in valid:
        if all(val >= max_vals[(eff, tgt)] for eff, tgt, val in entry[1]):
            filtered.append(entry)
    return filtered

def generate_item_page(profile, baseline, bundle, page, item, hero, expected_slot):
    rep_mults = {0: "(x0.5)", 1: "(x1)", 2: "(x2)", 3: "(x3)", 4: "(x4)", 5: "(x5)", 6: "(x6)"}
    grade_mults = {0: "(x1.0)", 1: "(x0.8)", 2: "(x1.1)", 3: "(x1.2)", 4: "(x1.3)", 5: "(x1.5)"}
    slot_map = {0: "Headpiece", 1: "Weapon", 2: "Chestpiece", 3: "Accessory"}
    
    step = 1
    chosen_base = None
    chosen_suffix = None
    chosen_prefixes = []
    chosen_grade_name, chosen_grade_val = "None", 0
    chosen_rep_name, chosen_rep_val = "None", 1

    while True:
        if step == 1:
            header("%s > Base Item" % page)
            print(THIN)
            base_options = BASE_ITEMS[hero].get(expected_slot, [])
            if not base_options:
                pause("  No Base Items available.")
                return False
                
            for n, (b_name, b_token, b_sprite, b_effects) in enumerate(base_options, 1):
                print("  %d. %-24s (%s)" % (n, b_name, format_eff_list(b_effects)))
            print("  %d. Back" % (len(base_options) + 1))
            
            choice = menu_choice(len(base_options) + 1)
            if choice is None or choice == len(base_options) + 1:
                return False
            chosen_base = base_options[choice - 1]
            step = 2

        elif step == 2:
            # Melwen Spell Accessories and Tiara of Enlightenment cannot receive additional suffixes
            if chosen_base[0] in ("Orb of Healing", "Talisman of Healing", 
                                  "Orb of Meteor Shower", "Talisman of Meteor Shower", 
                                  "Orb of Armageddon", "Talisman of Armageddon",
                                  "Tiara of Enlightenment"):
                chosen_suffix = None
                step = 3
                continue

            header("%s > Suffix" % page)
            print(THIN)
            valid_suffixes = get_max_filtered_enhancements(GEN_SUFFIXES, hero, expected_slot)
            print("  1. None")
            for n, s_entry in enumerate(valid_suffixes, 2):
                print("  %d. %-20s (%s)" % (n, s_entry[0], format_eff_list(s_entry[1])))
            print("  %d. Back" % (len(valid_suffixes) + 2))
            
            s_choice = menu_choice(len(valid_suffixes) + 2)
            if s_choice is None or s_choice == len(valid_suffixes) + 2:
                step = 1
                continue
            chosen_suffix = None if s_choice == 1 else valid_suffixes[s_choice - 2]
            step = 3

        elif step == 3:
            header("%s > Prefixes" % page)
            print(THIN)
            valid_prefixes = get_max_filtered_enhancements(GEN_PREFIXES, hero, expected_slot)
            for n, p_entry in enumerate(valid_prefixes, 1):
                print("  Key %-2d: %-18s (%s)" % (n, p_entry[0], format_eff_list(p_entry[1])))
            
            print("\n  Note: Enter prefix key(s) separated by space (e.g. '1 3')")
            print("  Or just press Enter to proceed without Prefixes.")
            
            while True:
                p_raw = ask("  Keys (or Enter for none, Q to back): ")
                if p_raw is None: 
                    if chosen_base[0] in ("Orb of Healing", "Talisman of Healing", 
                                          "Orb of Meteor Shower", "Talisman of Meteor Shower", 
                                          "Orb of Armageddon", "Talisman of Armageddon"):
                        step = 1
                    else:
                        step = 2
                    break
                if p_raw == "": 
                    chosen_prefixes = []
                    step = 4
                    break
                
                parts = p_raw.split()
                try:
                    indices = [int(p) for p in parts]
                    if not all(1 <= idx <= len(valid_prefixes) for idx in indices):
                        print("  Invalid keys. Make sure the numbers match the list.")
                        continue
                    if len(indices) > 2:
                        print("  Error: A maximum of 2 prefixes is allowed.")
                        continue
                    if len(set(indices)) != len(indices):
                        print("  Error: Duplicate prefixes are not allowed.")
                        continue
                        
                    chosen_prefixes = [valid_prefixes[idx - 1] for idx in indices]
                    step = 4
                    break
                except ValueError:
                    print("  Invalid format. Enter numbers separated by spaces.")

        elif step == 4:
            header("%s > Reputation Tier" % page)
            print(THIN)
            for n, (r_name, r_val) in enumerate(REPUTATION_OPTIONS, 1):
                print("  %d. %s %s" % (n, r_name, rep_mults.get(r_val, "")))
            print("  %d. Back" % (len(REPUTATION_OPTIONS) + 1))
            
            r_choice = menu_choice(len(REPUTATION_OPTIONS) + 1)
            if r_choice is None or r_choice == len(REPUTATION_OPTIONS) + 1:
                step = 3
                continue
            chosen_rep_name, chosen_rep_val = REPUTATION_OPTIONS[r_choice - 1]
            step = 5

        elif step == 5:
            header("%s > Grade" % page)
            print(THIN)
            for n, (g_name, g_val) in enumerate(GRADE_OPTIONS, 1):
                print("  %d. %s %s" % (n, g_name, grade_mults.get(g_val, "")))
            print("  %d. Back" % (len(GRADE_OPTIONS) + 1))
            
            g_choice = menu_choice(len(GRADE_OPTIONS) + 1)
            if g_choice is None or g_choice == len(GRADE_OPTIONS) + 1:
                step = 4
                continue
            chosen_grade_name, chosen_grade_val = GRADE_OPTIONS[g_choice - 1]
            step = 6
            
        elif step == 6:
            # 6. Computation and Summary Preview
            grade_mult = {0: 1.0, 1: 0.8, 2: 1.1, 3: 1.2, 4: 1.3, 5: 1.5}.get(chosen_grade_val, 1.0)
            rep_mult = {0: 0.5, 1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0, 5: 5.0, 6: 6.0}.get(chosen_rep_val, 1.0)
            
            # Combine all effects additively
            all_effs = list(chosen_base[3])
            if chosen_suffix: all_effs.extend(chosen_suffix[1])
            for p in chosen_prefixes: all_effs.extend(p[1])
            
            merged_effs = {}
            for eff, tgt, val in all_effs:
                merged_effs[(eff, tgt)] = merged_effs.get((eff, tgt), 0) + val
                
            # Apply multipliers
            final_eff_tuples = []
            
            # Effects that should ignore Reputation and Grade multipliers
            EXCLUDED_MULT_EFFS = {
                E_MOVE, E_ICE, E_LTNG,
                E_RAGE, E_GREED, E_POIS, E_POISIM
            }
            
            for (eff, tgt), val in merged_effs.items():
                if eff not in EXCLUDED_MULT_EFFS:
                    val = int(val * grade_mult)
                    val = int(val * rep_mult)
                final_eff_tuples.append((eff, tgt, val))
                
            # String Compilation
            final_name = chosen_base[0]
            if chosen_prefixes:
                final_name = " ".join([p[0] for p in chosen_prefixes]) + " " + final_name
            if chosen_rep_val not in (0, 1):
                final_name = chosen_rep_name + " " + final_name
            if chosen_grade_val != 0:
                final_name = chosen_grade_name + " " + final_name
            if chosen_suffix:
                final_name = final_name + " Of " + chosen_suffix[0]
                
            final_token = int(int(chosen_base[1] * grade_mult) * rep_mult)
            hero_mask = 0b0001 if hero == "General" else 0b0100
            
            # Draw Summary
            header("%s > Summary" % page)
            print(THIN)
            print("  1. %-20s %s" % ("Name", final_name))
            print("  2. %-20s %s" % ("Equipment Slot", slot_map.get(expected_slot, "Unknown")))
            print("  3. %-20s %d" % ("Sprite Number", chosen_base[2]))
            print("  4. %-20s %d" % ("Token Value", final_token))
            print("  5. %-20s %d" % ("Prefix Count", len(chosen_prefixes)))
            print("  6. %-20s %d" % ("Suffix Count", 1 if chosen_suffix else 0))
            print("  7. %-20s %s" % ("Reputation Tier", chosen_rep_name))
            print("  8. %-20s %s" % ("Grade", chosen_grade_name))
            print("  9. %-20s %s" % ("Which Hero", "Melwen Only" if hero == "Melwen" else "General Only"))
            
            for i, (eff, tgt, val) in enumerate(final_eff_tuples):
                print(" %2d. %-20s %s" % (10 + i, "Effect %d" % (i + 1), format_eff_list([(eff, tgt, val)])))
                
            print("\n  Proceed with Item Generation?")
            print("  1. Yes")
            print("  2. No (Go Back)")
            
            ans = menu_choice(2)
            if ans == 2 or ans is None:
                step = 5
                continue
            
            # Inject
            preset = {
                "name": final_name, "slot": expected_slot, "sprite": chosen_base[2],
                "token": final_token, "prefix": len(chosen_prefixes),
                "suffix": 1 if chosen_suffix else 0, "rep": chosen_rep_val,
                "grade": chosen_grade_val, "hero": hero_mask,
                "effects": final_eff_tuples[:10]
            }
            record = preset_record(preset)
            splice(profile, baseline, bundle, item["start"], item_end(profile, item["start"]), record)
            return True


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
        
        print("  10. Effect Entries")
        print("  11. Delete Item")
        print("  12. Back")

        choice = menu_choice(12)
        if choice is None or choice == 12:
            return
        if choice == 1:
            edit_item_name(profile, baseline, bundle, page, item)
        elif choice == 2:
            choose_dword(profile, page, "Equipment Slot", item["start"] + 4, SLOT_OPTIONS)
        elif choice == 10:
            effect_entries_page(profile, baseline,
                                "%s > Manual Editing" % page, item)
        elif choice == 11:
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
        print("  2. Generate Item")
        print("  3. Manual Editing")
        print("  4. Delete Item")
        print("  5. Back")

        choice = menu_choice(5)
        if choice is None or choice == 5:
            return
        
        if choice == 1:
            if preset_page(profile, baseline, bundle, page, item, hero, slot_value):
                return
        elif choice == 2:
            if generate_item_page(profile, baseline, bundle, page, item, hero, slot_value):
                return
        elif choice == 3:
            manual_editing_page(profile, baseline, bundle, page, item)
            return
        elif choice == 4:
            delete_item(profile, baseline, bundle, item)
            return


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

EFFECT_ENTRIES = 10
EFFECT_BASE = 7          # tail DWORD index where the 10 effect entries begin
EFFECT_PARTS = ("Effect ID", "Target", "Value")


def hex_bytes(value):
    """A signed DWORD as the little-endian byte string the docs use."""
    return " ".join("%02X" % b for b in struct.pack("<i", value))


def ask_hex_dword(text):
    """Hex bytes in file order. DD 07 00 00, DD070000 and DD07 are the same
    DWORD. A 0x prefix switches to plain number entry instead."""
    while True:
        answer = ask(text)
        if answer is None:
            return None
        cleaned = "".join(answer.split())
        try:
            if cleaned[:2].lower() == "0x":
                value = int(cleaned, 16)
            else:
                if not cleaned or len(cleaned) % 2 or len(cleaned) > 8:
                    raise ValueError
                raw = bytes.fromhex(cleaned)
                value = int.from_bytes(raw.ljust(4, b"\x00"), "little")
        except ValueError:
            print("  Enter the bytes as they appear in the file, for example")
            print("  DD 07 00 00, DD070000 or DD07. For a plain number use 0x7DD.")
            continue
        if value > DWORD_MAX:
            value -= 0x100000000
        if not DWORD_MIN <= value <= DWORD_MAX:
            print("  That is outside the signed DWORD range.")
            continue
        return value


def effect_index(entry, part):
    return EFFECT_BASE + entry * 3 + part


def effect_cell(value, part):
    """Effect ID and Target render as hex bytes, Value as decimal."""
    return "%d" % value if part == 2 else hex_bytes(value)


def effect_values(buf, start, entry):
    return [read_dword(buf, item_field_offset(buf, start, effect_index(entry, part)))
            for part in range(3)]


def effect_preview(profile, item, entry, part):
    idx = effect_index(entry, part)
    new = read_dword(profile, item_field_offset(profile, item["start"], idx))
    old = read_dword(item["original"], item_field_offset(item["original"], 0, idx))
    if old == new:
        return effect_cell(new, part)
    return "%s -> %s" % (effect_cell(old, part), effect_cell(new, part))


def edit_hex_field(profile, baseline, page, label, offset):
    header("%s > %s" % (page, label))
    print(THIN)
    current = read_dword(baseline, offset)
    pending = read_dword(profile, offset)
    print("  Current value: %s" % hex_bytes(current))
    if pending != current:
        print("  Pending value: %s" % hex_bytes(pending))

    value = ask_hex_dword(
        "\n  Enter the bytes (DD 07 00 00, DD070000 or DD07), or Q to cancel: ")
    if value is not None:
        write_dword(profile, offset, value)


def effect_entry_page(profile, baseline, page, item, entry):
    title = "%s > Entry %d" % (page, entry + 1)
    while True:
        header(title)
        print(THIN)
        for n, label in enumerate(EFFECT_PARTS, 1):
            print("  %d. %-12s %s"
                  % (n, label, effect_preview(profile, item, entry, n - 1)))
        print("  4. Back")

        choice = menu_choice(4)
        if choice is None or choice == 4:
            return
        offset = item_field_offset(profile, item["start"],
                                   effect_index(entry, choice - 1))
        if choice == 3:
            edit_field(profile, baseline, title, "Value", offset)
        else:
            edit_hex_field(profile, baseline, title, EFFECT_PARTS[choice - 1], offset)


def effect_entries_page(profile, baseline, page, item):
    title = "%s > Effect Entries" % page
    while True:
        header(title)
        print(THIN)
        print("   %-3s %-13s %-13s %12s"
              % ("#", "Effect ID", "Target", "Value"))
        for entry in range(EFFECT_ENTRIES):
            # Unsaved entries print their original underneath rather than
            # inline, so the columns stay aligned either way.
            new = effect_values(profile, item["start"], entry)
            old = effect_values(item["original"], 0, entry)
            print()
            print("   %2d. %-13s %-13s %12s"
                  % (entry + 1, hex_bytes(new[0]), hex_bytes(new[1]), new[2]))
            if old != new:
                print("   was %-13s %-13s %12s"
                      % (hex_bytes(old[0]), hex_bytes(old[1]), old[2]))
                print()
        print()
        print("   %2d. Back" % (EFFECT_ENTRIES + 1))

        choice = menu_choice(EFFECT_ENTRIES + 1)
        if choice is None or choice == EFFECT_ENTRIES + 1:
            return
        effect_entry_page(profile, baseline, title, item, choice - 1)


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