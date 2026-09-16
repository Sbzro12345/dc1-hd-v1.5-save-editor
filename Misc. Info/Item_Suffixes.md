# Defender Chronicles HD v1.5 - Random Enhancements (Suffixes)

In the game code, **Suffixes** (`param_4 = false`) are strictly capped at a **maximum of 1 Suffix per item**.
Any item that already has a suffix will reject subsequent suffix rolls. 

*Move Speed is not affected by Reputation Tier or Grade multipliers.

## Global & Commander Enhancements
These suffixes apply globally or directly to Commander stats across all heroes.
Tier 3 Commander suffixes are strictly restricted to Accessories and require high-tier generation (`param_1 > 0`).

| Suffix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Protection | Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | +1 | All Slots |
| Guardian | Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | +2 | All Slots |
| the Archangel | Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | +3 | Accessory Only |
| the Leprechaun | Extra Initial Gold (`02 00 00 00`) | `FF FF FF FF` | +2 | Accessory Only |
| the Gladiator | Infantry Commander (`EF 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Paladin | Infantry Commander (`EF 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Cyclops | Infantry Commander (`EF 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Marksman | Bowmen Commander (`F0 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Sharpshooter | Bowmen Commander (`F0 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Roc | Bowmen Commander (`F0 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Sage | Mage Commander (`F2 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Archmage | Mage Commander (`F2 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Pegasus | Mage Commander (`F2 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |

## General Limited Suffixes
Rolling any of these suffixes forces the item's usage restriction to **General Only** (`limitUsageTo(this, 1)`).
Tier 3 suffixes are restricted exclusively to Accessories and require high-tier generation (`param_1 > 0`).

| Suffix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| the Conqueror | Combat (`EB 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Titan | Combat (`EB 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Dragon | Combat (`EB 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Hero | Morale (`EC 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Courage | Morale (`EC 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Griffon | Morale (`EC 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Diplomat | Cunning (`EE 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Devious | Cunning (`EE 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Harpy | Cunning (`EE 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Bear | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| the Centaur | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +20 | All Slots |
| the Minotaur | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +30 | Accessory Only |
| the Collossus | Health Rating (`DF 07 00 00`) | `FE FF FF FF` | +50 | All Slots |
| the Hydra | Health Rating (`DF 07 00 00`) | `FE FF FF FF` | +75 | Accessory Only |
| the Sentinel | Armor Rating (`E0 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| the Basilisk | Armor Rating (`E0 07 00 00`) | `FE FF FF FF` | +15 | Accessory Only |
| Rage | Rage (`CD 0B 00 00`) | `FE FF FF FF` | 0 | Headpiece, Weapon |
| Avarice | Greed (`CE 0B 00 00`) | `FE FF FF FF` | 0 | Headpiece, Accessory |
| Venom | Poison Attack (`CF 0B 00 00`) | `FE FF FF FF` | 0 | Weapon, Accessory |
| Antidote | Poison Immunity (`D0 0B 00 00`) | `FE FF FF FF` | 0 | Chestpiece, Accessory |

## Universal Suffixes
In the engine code, these specific suffixes do not call `limitUsageTo` and act as unrestricted, universal enhancements.

| Suffix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| the Mammoth | Health Rating (`DF 07 00 00`) | `FE FF FF FF` | +25 | All Slots |
| Fortitude | Armor Rating (`E0 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| Wind | Move Speed* (`E3 07 00 00`) | `FE FF FF FF` | +1 | All Slots |

## Melwen Limited Suffixes
Rolling any of these suffixes forces the item's usage restriction to **Melwen Only** (`limitUsageTo(this, 4)`).
Tier 3 suffixes are restricted exclusively to Accessories and require high-tier generation (`param_1 > 0`).

| Suffix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| the Witch | Sorcery (`F3 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Genie | Sorcery (`F3 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Phoenix | Sorcery (`F3 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Scholar | Wisdom (`F4 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| Great Owl | Wisdom (`F4 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Wizard | Wisdom (`F4 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| the Alchemist | Power (`F5 03 00 00`) | `FE FF FF FF` | +1 | All Slots |
| the Elders | Power (`F5 03 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Warlock | Power (`F5 03 00 00`) | `FE FF FF FF` | +3 | Accessory Only |
| Element | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +15 | All Slots |
| the Medusa | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +30 | All Slots |
| the Gorgon | Attack Rating (`DD 07 00 00`) | `FE FF FF FF` | +45 | Accessory Only |
| Far Sight | Atk Radius (`DE 07 00 00`) | `FE FF FF FF` | +2 | All Slots |
| the Seer | Atk Radius (`DE 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| the Oracle | Atk Radius (`DE 07 00 00`) | `FE FF FF FF` | +10 | Accessory Only |
| Barrier | Resist Rating (`E8 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| the Force | Resist Rating (`E8 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| the Serpent | Armor Rating (`E0 07 00 00`) | `FE FF FF FF` | +15 | Accessory Only |
| Energy | Spell Power (`E5 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| the Manticore | Spell Power (`E5 07 00 00`) | `FE FF FF FF` | +20 | All Slots |
| the Wyvern | Spell Power (`E5 07 00 00`) | `FE FF FF FF` | +30 | Accessory Only |
| Knowledge | Mana Points (`E6 07 00 00`) | `FE FF FF FF` | +5 | All Slots |
| the Imp | Mana Points (`E6 07 00 00`) | `FE FF FF FF` | +10 | All Slots |
| the Unicorn | Mana Points (`E6 07 00 00`) | `FE FF FF FF` | +15 | Accessory Only |
| Willpower | Mana Recovery (`E7 07 00 00`) | `FE FF FF FF` | +5 | Headpiece, Weapon, Chestpiece |

### Melwen Spell Accessories
Spell accessories for Melwen are handled as suffixes in the data structure and are restricted to Accessories.

**The Spell Modifier is the Value divided by 100.

| Suffix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| Healing Spell | Healing (`D8 0B 00 00`) | `FF FF FF FF` | Spell Modifier** | Accessory Only |
| Armageddon Spell | Armageddon (`DA 0B 00 00`) | `FF FF FF FF` | Spell Modifier** | Accessory Only |
| Meteor Shower Spell | Meteor Shower (`DD 0B 00 00`) | `FF FF FF FF` | Spell Modifier** | Accessory Only |

## Unit-Specific Suffixes
These suffixes apply direct stat boosts and specials to specific unit classes. All unit-specific suffixes roll on All Slots (`0xF`).

| Suffix Name | Effect (Hex ID) | Target | Value | Eligible Slots |
| :--- | :--- | :--- | :--- | :--- |
| the Champion | Attack Rating (`DD 07 00 00`) | Warrior/Paladin (`04 00 00 00`) | +10 | All Slots |
| the Wolf | Health Rating (`DF 07 00 00`) | Warrior/Paladin (`04 00 00 00`) | +40 | All Slots |
| Ironskin | Armor Rating (`E0 07 00 00`) | Warrior/Paladin (`04 00 00 00`) | +5 | All Slots |
| the Wanderer | Movement Speed* (`E3 07 00 00`) | Warrior/Paladin (`04 00 00 00`) | +1 | All Slots |
| Bloodlust | Rage (`CD 0B 00 00`) | Warrior/Paladin (`04 00 00 00`) | 0 | All Slots |
| the Snake | Poison Attack (`CF 0B 00 00`) | Warrior/Paladin (`04 00 00 00`) | 0 | All Slots |
| the Cure | Poison Immunity (`D0 0B 00 00`) | Warrior/Paladin (`04 00 00 00`) | 0 | All Slots |
| the Slayer | Attack Rating (`DD 07 00 00`) | Berserker (`05 00 00 00`) | +20 | All Slots |
| the Tiger | Health Rating (`DF 07 00 00`) | Berserker (`05 00 00 00`) | +80 | All Slots |
| Steelskin | Armor Rating (`E0 07 00 00`) | Berserker (`05 00 00 00`) | +10 | All Slots |
| the Wayfarer | Movement Speed* (`E3 07 00 00`) | Berserker (`05 00 00 00`) | +1 | All Slots |
| the Viper | Poison Attack (`CF 0B 00 00`) | Berserker (`05 00 00 00`) | 0 | All Slots |
| the Remedy | Poison Immunity (`D0 0B 00 00`) | Berserker (`05 00 00 00`) | 0 | All Slots |
| Excellent | Attack Rating (`DD 07 00 00`) | Archer/Marksman (`0B 00 00 00`) | +3 | All Slots |
| Eagle Eyes | Atk Radius (`DE 07 00 00`) | Archer/Marksman (`0B 00 00 00`) | +5 | All Slots |
| the Wicked | Poison Attack (`CF 0B 00 00`) | Archer/Marksman (`0B 00 00 00`) | 0 | All Slots |
| Perfection | Attack Rating (`DD 07 00 00`) | Ranger (`0C 00 00 00`) | +5 | All Slots |
| Hawk Eyes | Atk Radius (`DE 07 00 00`) | Ranger (`0C 00 00 00`) | +5 | All Slots |
| the Arcane | Attack Rating (`DD 07 00 00`) | Mage/Archmage (`0F 00 00 00`) | +15 | All Slots |
| Vision | Atk Radius (`DE 07 00 00`) | Mage/Archmage (`0F 00 00 00`) | +5 | All Slots |
| the Troll | Health Rating (`DF 07 00 00`) | Mage/Archmage (`0F 00 00 00`) | +20 | All Slots |
| Wonder | Attack Rating (`DD 07 00 00`) | Halfling/Lizardman (`17 00 00 00`) | +8 | All Slots |
| the Fox | Health Rating (`DF 07 00 00`) | Halfling/Lizardman (`17 00 00 00`) | +30 | All Slots |
| Stoneskin | Armor Rating (`E0 07 00 00`) | Halfling/Lizardman (`17 00 00 00`) | +3 | All Slots |
| the Nimble | Movement Speed* (`E3 07 00 00`) | Halfling/Lizardman (`17 00 00 00`) | +1 | All Slots |
| Chaos | Rage (`CD 0B 00 00`) | Halfling/Lizardman (`17 00 00 00`) | 0 | All Slots |
| Poison Ward | Poison Immunity (`D0 0B 00 00`) | Halfling/Lizardman (`17 00 00 00`) | 0 | All Slots |