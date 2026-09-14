# Defender Chronicles HD v1.5 - Random Enhancements (Prefixes)

In the game code, **Prefixes** are generated less frequently (rarer) than Suffixes. They also house all the negative stat modifiers and cost-only modifiers.

## Cost Modifiers
These prefixes only modify the Token Price of items and grant no actual stat effects.

| Target | Modifiers |
| :--- | :--- |
| **General** | Cheap, Expensive |
| **Melwen** | Unfashionable, Designer |

## Global & Commander Enhancements
These prefixes apply globally or directly to Commander stats.

| Effect (Hex ID) | Target | Enhancements & Value |
| :--- | :--- | :--- |
| Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | Defender (+1), Clumsy (-1) |
| Infantry Cmdr (`EF 03 00 00`) | `FE FF FF FF` | Glorious (+1), Paladin (+2), Loser (-1) |
| Bowmen Cmdr (`F0 03 00 00`) | `FE FF FF FF` | Noble (+1), Sharpshooter (+2), Commoner (-1) |
| Mage Cmdr (`F2 03 00 00`) | `FE FF FF FF` | Mystic (+1), Archmage (+2), Muggle (-1) |

## General-Exclusive Prefixes
These prefixes target the General specifically (`FE FF FF FF`), skipping Melwen.

| Effect (Hex ID) | Enhancements & Value |
| :--- | :--- |
| Combat (`EB 03 00 00`) | Might (+1), Titan (+2), Feeble (-1) |
| Morale (`EC 03 00 00`) | Brave (+1), Courage (+2), Coward (-1) |
| Cunning (`EE 03 00 00`) | Witty (+1), Devious (+2), Dull (-1) |
| Multi-Skill | Knight's (+1 Combat), Lord's (+1 Combat+Morale), King's (+1 Combat+Morale+Cunning) |
| Attack Rtg (`DD 07 00 00`) | Savage (+10), Puny (-10) |
| Health Rtg (`DF 07 00 00`) | Life (+25), Death (-25) |
| Armor Rtg (`E0 07 00 00`) | Blessed (+5), Cursed (-5) |
| Move Speed (`E3 07 00 00`) | Bulky (-1) |
| Special Effects | Brutal (Rage `CD 0B`), Greedy (Greed `CE 0B`), Acidic (Poison `CF 0B`), Lizard's (Poison Immunity `D0 0B`) |

## Melwen-Exclusive Prefixes
These prefixes target Melwen specifically (`FE FF FF FF`), skipping the General.

| Effect (Hex ID) | Enhancements & Value |
| :--- | :--- |
| Sorcery (`F3 03 00 00`) | Enchanted (+1), Genie (+2), Wooden (-1) |
| Wisdom (`F4 03 00 00`) | Clever (+1), Foolish (-1) |
| Power (`F5 03 00 00`) | Supreme (+1), Pathetic (-1) |
| Multi-Skill | Apprentice's (+1 Sorcery), Master's (+1 Sorcery+Wisdom), Grandmaster's (+1 Sorcery+Wisdom+Power) |
| Attack Rtg (`DD 07 00 00`) | Imbued (+15), Brittle (-15) |
| Atk Radius (`DE 07 00 00`) | Keen (+2), Hazy (-2) |
| Resist Rtg (`E8 07 00 00`) | Warding (+5), Dire (-5) |
| Spell Power (`E5 07 00 00`) | Radiant (+10), Murky (-10) |
| Mana Points (`E6 07 00 00`) | Chatty (+5), Perplexing (-5) |
| Mana Recovery Rate (`E7 07 00 00`) | Charging (+5) |

## Unit-Specific Prefixes
These prefixes apply their respective stat boosts directly to specific unit targets rather than the Hero.

| Target Class (Hex ID) | Stat Modifiers | Enhancements |
| :--- | :--- | :--- |
| **Warrior/Paladin** (`04 00 00 00`) | Atk Rtg (+3) | Valor |
| **Berserker** (`05 00 00 00`) | Atk Rtg (+5) | Merciless |
| **Archer/Marksman** (`0B 00 00 00`) | Atk Rtg (+1) | Precision |
| **Ranger** (`0C 00 00 00`) | Atk Rtg (+1) | Exacto |
| **Mage/Archmage** (`0F 00 00 00`) | Atk Rtg (+5) | Brilliance |
| **Halfling/Lizardman** (`17 00 00 00`)| Atk Rtg (+2) | Vigilant |
