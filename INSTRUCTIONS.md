# Tacticus LE Planner — Instructions

## Overview

This repo contains a master character database (`data/tacticus_characters.csv`) used to generate optimal team recommendations for Legendary Events (LEs) in Warhammer 40,000: Tacticus.

The workflow is:
1. Keep `tacticus_characters.csv` up to date after each patch
2. When a new LE is announced, provide Claude with the track conditions
3. Claude reads the CSV, runs the analysis, and outputs recommended teams for Alpha, Beta, and Gamma tracks

---

## Repository Structure

```
tacticus-le-planner/
├── data/
│   └── tacticus_characters.csv   ← master character database
├── README.md                     ← brief description for GitHub
└── INSTRUCTIONS.md               ← this file
```

---

## The Character Database (tacticus_characters.csv)

### Column Reference

**Identity**
| Column | Description |
|--------|-------------|
| `Name` | Character name (matches wiki exactly) |
| `Faction` | Faction name (e.g. Ultramarines, Death Guard) |
| `Alliance` | Imperial / Xenos / Chaos |
| `Is_MoW` | Y/N — is this a Machine of War? |

**Attack Profile**
| Column | Description |
|--------|-------------|
| `Has_Ranged` | Y/N — does this character have a ranged attack? |
| `Melee_Hits` | Number of melee hits |
| `Ranged_Hits` | Number of ranged hits (blank if no ranged attack) |
| `X_Hits_Restriction` | The hit count used for LE restrictions (ranged if available, else melee) |
| `Melee_Damage_Type` | Damage type of melee attack (e.g. Physical, Piercing, Power, Bolter) |
| `Ranged_Damage_Type` | Damage type of ranged attack (blank if no ranged attack) |

**Meta / Strategy**
| Column | Description |
|--------|-------------|
| `Self_Heal` | Y/N — does this character heal themselves via abilities? (manual input) |
| `Notes` | Free text for meta observations, team synergies, etc. |

**Trait Columns (Y/N)**

All 44 character-applicable traits from the wiki are tracked as Y/N columns. Key ones for LE analysis:

| Trait | LE Relevance |
|-------|-------------|
| `Resilient` | Direct LE condition |
| `Mechanical` | Direct LE condition |
| `Living_Metal` | Necrons — includes Mechanical |
| `Terminator_Armour` | Direct LE condition + meta (tanky) |
| `Mk_X_Gravis` | Meta (tanky) |
| `Big_Target` | Direct LE condition |
| `Psyker` | Used for NO PSYKER condition (invert) |
| `Healer` | Meta — important for deep stage pushes |
| `Mechanic` | Can repair Mechanical units |

---

## How LE Conditions Map to the Database

When a new LE is announced, derive eligibility from the CSV as follows:

| LE Condition | Derived From |
|-------------|--------------|
| ULTRAMARINES | `Faction = "Ultramarines"` |
| [Any faction name] | `Faction = "[faction name]"` |
| RESILIENT | `Resilient = Y` |
| MECHANICAL | `Mechanical = Y` |
| TERMINATOR ARMOUR | `Terminator_Armour = Y` |
| BIG TARGET | `Big_Target = Y` |
| NO PSYKER | `Psyker = N` |
| MELEE | `Has_Ranged = N` |
| RANGED | `Has_Ranged = Y` |
| MAX 1 HITS | `X_Hits_Restriction <= 1` |
| MAX 2 HITS | `X_Hits_Restriction <= 2` |
| MIN 5 HITS | `X_Hits_Restriction >= 5` |
| PIERCING DMG | `Melee_Damage_Type = "Piercing"` OR `Ranged_Damage_Type = "Piercing"` |
| BOLTER DMG | `Melee_Damage_Type = "Bolter"` OR `Ranged_Damage_Type = "Bolter"` |
| PSYCHIC DMG | `Melee_Damage_Type = "Psychic"` OR `Ranged_Damage_Type = "Psychic"` |
| NO POWER DMG | `Melee_Damage_Type != "Power"` AND `Ranged_Damage_Type != "Power"` |
| NO XENOS | `Alliance != "Xenos"` (Alpha track filter) |
| NO IMPERIALS | `Alliance != "Imperial"` (Beta track filter) |
| NO CHAOS | `Alliance != "Chaos"` (Gamma track filter) |

---

## Updating the Database

### When a new character is released

1. Check their wiki page at `https://tacticus.wiki.gg/wiki/[CharacterName]`
2. Find: faction, alliance, melee/ranged hits, X Hits Restriction, damage types, traits
3. Add one row to the CSV with all fields populated
4. Commit the change with a message like: `Add [Name] - [Faction] (patch 1.XX)`

Key wiki pages for reference:
- All characters by hits: https://tacticus.wiki.gg/wiki/Hits
- Melee-only characters: https://tacticus.wiki.gg/wiki/Melee
- Ranged characters: https://tacticus.wiki.gg/wiki/Ranged
- All factions: https://tacticus.wiki.gg/wiki/Factions
- All traits: https://tacticus.wiki.gg/wiki/Trait
- Damage types: https://tacticus.wiki.gg/wiki/Damage_Types_and_Pierce_Ratio

### When a character is reworked

Find the character's row and update the relevant fields. Common rework changes:
- Hit count changes → update `Melee_Hits`, `Ranged_Hits`, `X_Hits_Restriction`
- Damage type changes → update `Melee_Damage_Type` or `Ranged_Damage_Type`
- Trait added/removed → update the relevant Y/N column

### When a trait is retired or renamed

Update the column header and all affected rows. Document in git commit message with the patch version.

---

## Running a New LE Analysis

When a new LE is announced, provide Claude with:

1. The raw CSV (or the GitHub raw URL)
2. The three tracks and their conditions, in this format:

```
LE 15 - [Character Name]
Alliance restrictions: Alpha=No Xenos, Beta=No Imperials, Gamma=No Chaos

Alpha battles: [CONDITION] ([pts]), [CONDITION] ([pts]), ...
Beta battles: [CONDITION] ([pts]), [CONDITION] ([pts]), ...
Gamma battles: [CONDITION] ([pts]), [CONDITION] ([pts]), ...
```

Claude will then:
1. Filter eligible characters per track (applying alliance restriction)
2. Find characters eligible for each battle condition
3. Calculate the most token-efficient starting team (4-man intersection)
4. Find the minimum 5-man teams covering all battle conditions
5. Flag character overlaps between teams
6. Note which battle conditions have limited character pools (high risk)
7. Flag healers, self-healers, and tanky characters in each team

### Key scoring rules (important context for Claude)

- **All team members must share a trait** for the team to earn those bonus points
- Score = sum of point values for traits ALL members share (intersection, not union)
- Teams: minimum 3 characters, maximum 5
- 3-man teams typically reach stage 8-10 before difficulty peaks
- 5-man teams push further but intersection score is usually lower
- 1 token = 1 team deployment for 1 stage attempt
- Points accumulate across all Alpha, Beta, and Gamma stages cleared

---

## Meta Notes

### Tanky characters (good for pushing harder stages)

Characters with these traits survive longer in high-difficulty stages:
- `Terminator_Armour = Y` — first hit each turn deals -75% damage
- `Mk_X_Gravis = Y` — all incoming damage goes through armour twice
- `Resilient = Y` — survives lethal hits at 1 HP (unless overkilled)

### Healers

- `Healer = Y` — can heal a friendly unit as their action (replaces attack)
- `Self_Heal = Y` — heals themselves via ability (does not sacrifice action)
- `Mechanic = Y` — can repair Mechanical characters (functionally equivalent to Healer for Necron/AdMech teams)

### Mechanical characters note

Mechanical characters (`Mechanical = Y`) **cannot be healed** — only repaired by a Mechanic. When building teams for Necron or Adeptus Mechanicus characters, check for a Mechanic in the team rather than a Healer.

---

## Fields Needing Manual Verification

The following fields were populated from game knowledge and LE14 sheet data but should be verified against wiki character pages when time permits:

- `Melee_Damage_Type` and `Ranged_Damage_Type` for new characters (Ammuk, Cyrus, Havyr, Thothmek, Z'kar, Cezare, Hascule, Shiron)
- `Self_Heal` for all characters (requires checking individual ability descriptions)
- Individual traits for newer characters where game knowledge is uncertain

To verify a damage type, check the character's wiki page and look at the infobox: `Melee Attack: [DamageType] / [X] hits`

---

## Changelog

| Date | Change | Patch |
|------|--------|-------|
| July 2026 | Initial database built from wiki (Hits, Factions, Melee, Ranged, Trait pages) | 1.36 |
