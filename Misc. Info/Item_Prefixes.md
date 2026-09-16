# Defender Chronicles HD v1.5 - Random Enhancements (Prefixes)

In the game code, **Prefixes** (`param_4 = true`) have no hardcoded numerical limit per item, but cannot roll duplicates. 

*Move Speed is not affected by Reputation Tier or Grade multipliers.

## Cost Modifiers
These prefixes modify the Token Price of items and grant no actual stat effects.

| Target | Prefix | Eligible Slots | Effect |
| :--- | :--- | :--- | :--- |
| **General** | Cheap, Expensive | All Slots | Price Only |
| **Melwen** | Unfashionable, Designer | All Slots | Price Only |

## Global & Commander Enhancements
These prefixes apply globally or directly to Commander stats across all heroes.

| Prefix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Defender | Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | +1 | All Slots |
| Clumsy | Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | -1 | Weapon, Chestpiece |
| Glorious | Infantry Commander (`EF 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Loser | Infantry Commander (`EF 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Noble | Bowmen Commander (`F0 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Commoner | Bowmen Commander (`F0 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Mystic | Mage Commander (`F2 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Muggle | Mage Commander (`F2 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |

## Universal Prefixes
In the engine code, these specific prefixes do not call `limitUsageTo` and act as unrestricted, universal enhancements.

| Prefix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Life | Health Rating (`DF 07 00 00`) | `FE FF FF FF` | +25 | All Slots |
| Death | Health Rating (`DF 07 00 00`) | `FE FF FF FF` | -25 | Weapon, Chestpiece |
| Blessed | Armor Rating (`E0 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| Cursed | Armor Rating (`E0 07 00 00`) | `FE FF FF FF` | -5 | Weapon, Chestpiece |
| Bulky | Move Speed* (`E3 07 00 00`) | `FE FF FF FF` | -1 | Headpiece, Weapon, Chestpiece |

## General Limited Prefixes
Rolling any of these prefixes forces the item's usage restriction to **General Only** (`limitUsageTo(this, 1)`).

| Prefix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Might | Combat (`EB 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Feeble | Combat (`EB 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Brave | Morale (`EC 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Coward | Morale (`EC 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Witty | Cunning (`EE 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Dull | Cunning (`EE 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Knight's | Multi-Skill | `FE FF FF FF` | +1 Combat | Weapon Only |
| Lord's | Multi-Skill | `FE FF FF FF` | +1 Combat, +1 Morale | Weapon Only |
| King's | Multi-Skill | `FE FF FF FF` | +1 Combat, +1 Morale, +1 Cunning | Weapon Only |
| Savage | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| Puny | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | -10 | Weapon, Chestpiece |
| Brutal | Rage (`CD 0B 00 00`) | `FE FF FF FF` | 0 | Headpiece, Weapon |
| Greedy | Greed (`CE 0B 00 00`) | `FE FF FF FF` | 0 | Headpiece, Accessory |
| Acidic | Poison (`CF 0B 00 00`) | `FE FF FF FF` | 0 | Weapon, Accessory |
| Lizard's | Poison Immunity (`D0 0B 00 00`) | `FE FF FF FF` | 0 | Chestpiece, Accessory |

## Melwen Limited Prefixes
Rolling any of these prefixes forces the item's usage restriction to **Melwen Only** (`limitUsageTo(this, 4)`).

| Prefix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Enchanted | Sorcery (`F3 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Wooden | Sorcery (`F3 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Clever | Wisdom (`F4 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Foolish | Wisdom (`F4 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Supreme | Power (`F5 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Pathetic | Power (`F5 03 00 00`) | `FE FF FF FF` | -1 | Weapon, Chestpiece |
| Apprentice's | Multi-Skill | `FE FF FF FF` | +1 Sorcery | Weapon Only |
| Master's | Multi-Skill | `FE FF FF FF` | +1 Sorcery, +1 Wisdom | Weapon Only |
| Grandmaster's | Multi-Skill | `FE FF FF FF` | +1 Sorcery, +1 Wisdom, +1 Power | Weapon Only |
| Imbued | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +15 | All Slots |
| Brittle | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | -15 | Weapon, Chestpiece |
| Keen | Atk Radius (`DE 07 00 00`) | `FE FF FF FF` | +2 | All Slots |
| Hazy | Atk Radius (`DE 07 00 00`) | `FE FF FF FF` | -2 | Weapon, Chestpiece |
| Warding | Resist Rating (`E8 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| Dire | Resist Rating (`E8 07 00 00`) | `FE FF FF FF` | -5 | Weapon, Chestpiece |
| Radiant | Spell Power (`E5 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| Murky | Spell Power (`E5 07 00 00`) | `FE FF FF FF` | -10 | Weapon, Chestpiece |
| Chatty | Mana Points (`E6 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| Perplexing | Mana Points (`E6 07 00 00`) | `FE FF FF FF` | -5 | Weapon, Chestpiece |
| Charging | Mana Recovery (`E7 07 00 00`) | `FE FF FF FF` | +5 | Accessory Only |

## Unit-Specific Prefixes
These prefixes apply direct stat boosts to specific unit classes. In the engine, all unit-specific prefixes are restricted exclusively to Accessories and require high-tier generation (`param_1 > 0`).

| Prefix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Valor | Attack Rating (`DD 07 00 00`) | Warrior/Paladin (`04 00 00 00`) | +3 | Accessory Only |
| Merciless | Attack Rating (`DD 07 00 00`) | Berserker (`05 00 00 00`) | +5 | Accessory Only |
| Precision | Attack Rating (`DD 07 00 00`) | Archer/Marksman (`0B 00 00 00`) | +1 | Accessory Only |
| Exacto | Attack Rating (`DD 07 00 00`) | Ranger (`0C 00 00 00`) | +1 | Accessory Only |
| Brilliance | Attack Rating (`DD 07 00 00`) | Mage/Archmage (`0F 00 00 00`) | +5 | Accessory Only |
| Vigilant | Attack Rating (`DD 07 00 00`) | Halfling/Lizardman (`17 00 00 00`) | +2 | Accessory Only |