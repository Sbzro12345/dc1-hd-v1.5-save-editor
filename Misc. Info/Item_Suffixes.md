# Defender Chronicles HD v1.5 - Random Enhancements (Suffixes)

In the game code, **Suffixes** are generated more frequently than Prefixes and generally lack negative effects or standalone cost modifiers.

## Global & Commander Enhancements
These suffixes apply globally or directly to Commander stats.

| Effect (Hex ID) | Target | Enhancements & Value |
| :--- | :--- | :--- |
| Extra Gate Defense (`01 00 00 00`) | `FF FF FF FF` | Protection (+1), Guardian (+2), the Archangel (+3) |
| Extra Initial Gold (`02 00 00 00`) | `FF FF FF FF` | the Leprechaun (+2) |
| Infantry Cmdr (`EF 03 00 00`) | `FE FF FF FF` | the Gladiator (+1), the Cyclops (+3) |
| Bowmen Cmdr (`F0 03 00 00`) | `FE FF FF FF` | the Marksman (+1), the Roc (+3) |
| Mage Cmdr (`F2 03 00 00`) | `FE FF FF FF` | the Sage (+1), the Pegasus (+3) |

## General-Exclusive Suffixes
These suffixes target the General specifically (`FE FF FF FF`), skipping Melwen.

| Effect (Hex ID) | Enhancements & Value |
| :--- | :--- |
| Combat (`EB 03 00 00`) | the Conqueror (+1), the Dragon (+3) |
| Morale (`EC 03 00 00`) | the Hero (+1), the Griffon (+3) |
| Cunning (`EE 03 00 00`) | the Diplomat (+1), the Harpy (+3) |
| Attack Rtg (`DD 07 00 00`) | the Bear (+10), the Centaur (+20), the Minotaur (+30) |
| Health Rtg (`DF 07 00 00`) | the Mammoth (+25), the Collossus (+50), the Hydra (+75) |
| Armor Rtg (`E0 07 00 00`) | Fortitude (+5), the Sentinel (+10), the Basilisk (+15) |
| Move Speed (`E3 07 00 00`) | Wind (+1) |
| Special Effects | Rage (Rage `CD 0B`), Avarice (Greed `CE 0B`), Venom (Poison `CF 0B`), Antidote (Poison Immunity `D0 0B`) |

## Melwen-Exclusive Suffixes
These suffixes target Melwen specifically (`FE FF FF FF`), skipping the General.

| Effect (Hex ID) | Enhancements & Value |
| :--- | :--- |
| Sorcery (`F3 03 00 00`) | the Witch (+1), the Phoenix (+3) |
| Wisdom (`F4 03 00 00`) | the Scholar (+1), Great Owl (+2), the Wizard (+3) |
| Power (`F5 03 00 00`) | the Alchemist (+1), the Elders (+2), the Warlock (+3) |
| Attack Rtg (`DD 07 00 00`) | Element (+15), the Medusa (+30), the Gorgon (+45) |
| Atk Radius (`DE 07 00 00`) | Far Sight (+2), the Seer (+5), the Oracle (+10) |
| Resist Rtg (`E8 07 00 00`) | Barrier (+5), the Force (+10) |
| Armor Rtg (`E0 07 00 00`) | the Serpent (+15) |
| Spell Power (`E5 07 00 00`) | Energy (+10), the Manticore (+20), the Wyvern (+30) |
| Mana Points (`E6 07 00 00`) | Knowledge (+5), the Imp (+10), the Unicorn (+15) |
| Mana Recovery Rate (`E7 07 00 00`) | Willpower (+5) |

## Unit-Specific Suffixes
These suffixes apply their respective stat boosts and special effects directly to specific unit targets rather than the Hero.

| Target Class (Hex ID) | Stat Modifiers | Enhancements |
| :--- | :--- | :--- |
| **Warrior/Paladin** (`04 00 00 00`) | Atk Rtg (+10), HP (+40), Armor (+5), Move (+1) | the Champion, the Wolf, Ironskin, the Wanderer |
| | *Specials:* Rage, Poison Attack, Poison Immunity | Bloodlust, the Snake, the Cure |
| **Berserker** (`05 00 00 00`) | Atk Rtg (+20), HP (+80), Armor (+10), Move (+1) | the Slayer (+20), the Tiger, Steelskin, the Wayfarer |
| | *Specials:* Poison Attack, Poison Immunity | the Viper, the Remedy |
| **Archer/Marksman** (`0B 00 00 00`) | Atk Rtg (+3), Atk Radius (+5) | Excellent (+3), Eagle Eyes |
| | *Specials:* Poison Attack | the Wicked |
| **Ranger** (`0C 00 00 00`) | Atk Rtg (+5), Atk Radius (+5) | Perfection (+5), Hawk Eyes |
| **Mage/Archmage** (`0F 00 00 00`) | Atk Rtg (+15), HP (+20), Atk Radius (+5) | the Arcane (+15), the Troll, Vision |
| **Halfling/Lizardman** (`17 00 00 00`)| Atk Rtg (+8), HP (+30), Armor (+3), Move (+1) | Wonder (+8), the Fox, Stoneskin, the Nimble |
| | *Specials:* Rage, Poison Immunity | Chaos, Poison Ward |
