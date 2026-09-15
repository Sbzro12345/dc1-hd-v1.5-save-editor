# Defender Chronicles HD v1.5 - Base Items

Based directly on the initialization logic in the game's engine, here is the completely re-verified list of all base items. 

Items generate as blank slates with these exact base properties before any prefixes or suffixes are applied. If an item's `heroMask` allows for multiple heroes (e.g., `0xf` for all heroes), it has been accurately documented in both the General and Melwen tables below.

---

## General Hero Items

### General Headgear
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Cap | 2 | 2 | Armor +1 |
| Studded Cap | 3 | 2 | Armor +2 |
| Leather Cap | 4 | 30 | Armor +3 |
| Bronze Cap | 5 | 30 | Armor +4 |
| Captain's Cap | 8 | 30 | Armor +4, +1 Morale |
| Bronze Helm | 10 | 2 | Armor +5 |
| Iron Helm | 10 | 0 | Armor +8 |
| Steel Helm | 15 | 0 | Armor +12 |
| Silver Helm | 20 | 0 | Armor +16 |
| Imperial Helm | 30 | 1 | Armor +20 |
| Military Helm | 40 | 34 | Armor +15, +1 Infantry Cmdr, +1 Bowmen Cmdr, +1 Mage Cmdr |
| Crown | 40 | 3 | +5 Infantry Cmdr, +5 Bowmen Cmdr, +5 Mage Cmdr |
| Full Helm | 50 | 31 | Armor +25 |
| Horned Helm | 60 | 33 | Armor +20, Atk Rtg +12 |
| Rider's Helm | 64 | 34 | Armor +24, +4 Bowmen Cmdr, +4 Mage Cmdr |
| Adamantium Helm | 80 | 32 | Armor +30 |
| Grand Helm | 120 | 32 | Armor +30, +5 Combat, +5 Morale, +5 Infantry Cmdr, +5 Bowmen Cmdr |

### General Weapons
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Dagger | 1 | 6 | Atk Rtg +3 |
| Elven Dagger | 2 | 6 | Atk Rtg +7, +1 Combat |
| Iron Shortsword | 2 | 6 | Atk Rtg +5 |
| Steel Shortsword | 3 | 6 | Atk Rtg +7 |
| Silver Shortsword | 4 | 6 | Atk Rtg +10 |
| Iron Sabre | 8 | 40 | Atk Rtg +10 |
| Iron Mace | 12 | 4 | Atk Rtg +35 |
| Steel Sabre | 13 | 40 | Atk Rtg +12 |
| Iron Axe | 16 | 5 | Atk Rtg +60, Move Speed -1 |
| Silver Sabre | 17 | 40 | Atk Rtg +15 |
| Steel Mace | 18 | 4 | Atk Rtg +45 |
| Barbarian Mace | 24 | 4 | Atk Rtg +50, +1 Infantry Cmdr, +1 Bowmen Cmdr |
| Silver Mace | 24 | 4 | Atk Rtg +55 |
| Iron Longsword | 24 | 39 | Atk Rtg +45 |
| Steel Axe | 24 | 5 | Atk Rtg +70, Move Speed -1 |
| War Axe | 30 | 5 | Atk Rtg +70, Move Speed -1, +2 Morale, +2 Cunning |
| Iron Greatsword | 32 | 37 | Atk Rtg +70, Move Speed -1 |
| Silver Axe | 32 | 5 | Atk Rtg +80, Move Speed -1 |
| Steel Longsword | 45 | 39 | Atk Rtg +60 |
| Elven Sword | 60 | 39 | Atk Rtg +65, +2 Combat |
| Steel Greatsword | 60 | 37 | Atk Rtg +85, Move Speed -1 |
| Silver Longsword | 72 | 39 | Atk Rtg +75 |
| Slayer Sword | 75 | 37 | Atk Rtg +90, Move Speed -1, +2 Combat, +2 Cunning |
| Silver Greatsword | 96 | 37 | Atk Rtg +100, Move Speed -1 |
| Adamantium Greatsword | 160 | 38 | Atk Rtg +130, Move Speed -2 |

### General Chestpieces
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Leatherskin | 5 | 12 | Armor +7 |
| Bronze Breastplate | 10 | 9 | Armor +10 |
| Iron Breastplate | 20 | 11 | Armor +15 |
| Bronze Platemail | 25 | 36 | Armor +15 |
| Steel Breastplate | 30 | 11 | Armor +20 |
| Silver Breastplate | 40 | 11 | Armor +25 |
| Orc Breastplate | 45 | 10 | Armor +20, +2 Combat, +2 Infantry Cmdr |
| Iron Platemail | 50 | 35 | Armor +25 |
| Imperial Breastplate | 60 | 7 | Armor +30 |
| Steel Platemail | 70 | 35 | Armor +35 |
| Adamantium Breastplate | 80 | 8 | Armor +40 |
| Silver Platemail | 90 | 35 | Armor +45 |

### General Accessories
*Note: In the game code, all base accessories generate with absolutely zero base stats; their sole purpose in the engine is to serve as carriers for Prefix/Suffix modifiers.*

| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Iron Ring | 1 | 14 | *None* |
| Steel Ring | 3 | 14 | *None* |
| Amulet | 4 | 17 | *None* |
| Silver Ring | 8 | 14 | *None* |
| Necklace | 10 | 16 | *None* |
| Charm | 15 | 43 | *None* |
| Imperial Ring | 18 | 13 | *None* |
| Jewel Ring | 20 | 41 | *None* |
| Leather Bracer | 21 | 45 | *None* |
| Iron Greaves | 22 | 58 | *None* |
| Bracelet | 24 | 47 | *None* |
| Iron Bracer | 25 | 44 | *None* |
| Steel Greaves | 26 | 58 | *None* |
| Steel Bracer | 29 | 44 | *None* |
| Adamantium Ring | 30 | 15 | *None* |
| Silver Greaves | 30 | 58 | *None* |
| Silver Bracer | 33 | 44 | *None* |
| Cape | 40 | 48 | *None* |
---

## Melwen Hero Items

### Melwen Headgear
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Cap | 2 | 2 | Armor +1 |
| Studded Cap | 3 | 2 | Armor +2 |
| Leather Cap | 4 | 30 | Armor +3 |
| Bronze Cap | 5 | 30 | Armor +4 |
| Tiara | 10 | 49 | Spell Power +30 |
| Major Tiara | 18 | 49 | Spell Power +48 |
| Coronet | 25 | 52 | Spell Power +60 |
| Relic Tiara | 28 | 49 | Spell Power +64 |
| Major Coronet | 40 | 52 | Spell Power +75 |
| Crown | 40 | 3 | +5 Infantry Cmdr, +5 Bowmen Cmdr, +5 Mage Cmdr |
| Relic Coronet | 55 | 52 | Spell Power +90 |
| Tiara of Enlightenment | 78 | 49 | Spell Power +36, +5 Sorcery, +5 Wisdom, +5 Power |

### Melwen Weapons
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Ice Wand | 18 | 54 | Ice Wand Spell, Atk Rtg +30 |
| Lightning Wand | 24 | 55 | Lightning Wand Spell, Atk Rtg +55 |
| Major Ice Wand | 42 | 54 | Ice Wand Spell, Atk Rtg +50 |
| Ancient Lightning Wand | 46 | 55 | Lightning Wand Spell, Atk Rtg +68, +1 Wisdom, +1 Power |
| Major Lightning Wand | 54 | 55 | Lightning Wand Spell, Atk Rtg +80 |
| Runic Ice Wand | 74 | 54 | Ice Wand Spell, Atk Rtg +60, +4 Power |
| Relic Ice Wand | 92 | 54 | Ice Wand Spell, Atk Rtg +70 |
| Relic Lightning Wand | 122 | 55 | Lightning Wand Spell, Atk Rtg +105 |

### Melwen Chestpieces
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Leather Mantle | 4 | 61 | Mana Points +6 |
| Dragon Hide Mantle | 4 | 61 | Mana Points +6, Atk Rtg +20 |
| Leatherskin | 5 | 12 | Armor +7 |
| Cotton Mantle | 8 | 61 | Mana Points +10 |
| Leather Cloak | 10 | 60 | Mana Points +12 |
| Silk Mantle | 12 | 61 | Mana Points +14 |
| Cotton Cloak | 25 | 60 | Mana Points +18 |
| Leather Robe | 30 | 59 | Mana Points +20 |
| Silk Cloak | 40 | 60 | Mana Points +25 |
| Cotton Robe | 50 | 59 | Mana Points +30 |
| Vampire's Cowl | 60 | 60 | Mana Points +25, Spell Power +20, +1 Sorcery, +1 Power |
| Silk Robe | 75 | 59 | Mana Points +40 |
| Sorceress Robe | 80 | 59 | Mana Points +30, +2 Sorcery, +2 Mage Cmdr |

### Melwen Accessories
| Name | Token Cost | Sprite Number | Base Stats |
| :--- | :--- | :--- | :--- |
| Iron Ring | 1 | 14 | *None* |
| Steel Ring | 3 | 14 | *None* |
| Amulet | 4 | 17 | *None* |
| Silver Ring | 8 | 14 | *None* |
| Orb of Healing | 10 | 42 | Healing Spell (Value 100), Mana Points +10 |
| Talisman of Healing | 10 | 46 | Healing Spell (Value 100), Spell Power +20 |
| Necklace | 10 | 16 | *None* |
| Charm | 15 | 43 | *None* |
| Imperial Ring | 18 | 13 | *None* |
| Jewel Ring | 20 | 41 | *None* |
| Leather Bracer | 21 | 45 | *None* |
| Bracelet | 24 | 47 | *None* |
| Adamantium Ring | 30 | 15 | *None* |
| Orb of Meteor Shower | 30 | 42 | Meteor Shower Spell (Value 20), Mana Points +10 |
| Talisman of Meteor Shower | 30 | 46 | Meteor Shower Spell (Value 20), Spell Power +20 |
| Cape | 40 | 48 | *None* |
| Orb of Armageddon | 40 | 42 | Armageddon Spell (Value 80), Mana Points +10 |
| Talisman of Armageddon | 40 | 46 | Armageddon Spell (Value 80), Spell Power +20 |