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

**Machines of War note:** Rows with `Is_MoW = Y` are Machines of War (Galatian, Reanimator, Tson'ji, Exorcist, Storm Speeder, Malleus Rocket Launcher, Rukkatrukk, Biovore, Forgefiend, Plagueburst Crawler). Most of these have no base on-battlefield stat block — they act purely through off-board abilities — so `Melee_Hits`, `Ranged_Hits`, `X_Hits_Restriction`, and sometimes the damage-type columns are left blank where the wiki gives no confirmed value. **MoW eligibility for a given Legendary Event depends on that event's specific rules** — always confirm whether MoW are permitted before including one in a recommended team.

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

**Damage Type Columns (Y/N) — `Has_[DamageType]`**

There are 21 `Has_[DamageType]` boolean columns, one per damage type in the game:

`Has_Bio`, `Has_Blast`, `Has_Bolter`, `Has_Chain`, `Has_Direct`, `Has_Energy`, `Has_Eviscerating`, `Has_Flame`, `Has_Heavy_Round`, `Has_Las`, `Has_Melta`, `Has_Molecular`, `Has_Particle`, `Has_Physical`, `Has_Piercing`, `Has_Plasma`, `Has_Power`, `Has_Projectile`, `Has_Psychic`, `Has_Pulse`, `Has_Toxic`

Unlike `Melee_Damage_Type` and `Ranged_Damage_Type` (which only capture the character's *primary* attack types and are kept unchanged as reference text columns), a `Has_[DamageType]` column is `Y` if the character deals that damage type from **any** source — primary melee/ranged attack **or** an active/passive ability. A character can have multiple damage types marked `Y` (e.g. a character with a Piercing melee attack whose ability triggers a Plasma-damage effect has both `Has_Piercing=Y` and `Has_Plasma=Y`).

**Why this matters for LE analysis:** LE damage-type conditions (e.g. "PIERCING DMG", "PSYCHIC DMG") should usually be checked against the relevant `Has_[DamageType]` column rather than `Melee_Damage_Type`/`Ranged_Damage_Type`, since some characters only deal a given damage type through an ability and would otherwise be missed (e.g. Abaddon deals Piercing only via his Drach'nyen bonus attack, not his primary Power melee attack).

**Damage sourced only from a summoned/independently-acting unit is excluded.** If a character's ability summons a separate unit (e.g. a Guardsman, Bloodletter, Spore Mine) that takes its own turn and attacks with its own stat line, that summon's damage type is **not** counted toward the summoning character's own `Has_[DamageType]` columns — only damage the character (or its own ability effects, like a mine or bonus-attack) deals directly is counted. When adding new characters, watch for this distinction and check ability text carefully.

This rule is confirmed (owner-reviewed) as the correct approach — apply it consistently on future updates rather than re-litigating per character. In the July 2026 pass it changed the result for: Abraxas (Physical, Power excluded — from summoned Pink Horror / Screamer of Tzeentch), Ammuk (Energy excluded — from summoned Ironkin Steeljack), Anuphet (Physical, Molecular excluded — from summoned Necron Warriors), Archimatos (Piercing excluded — from summoned Bloodletter), Atlacoya (Psychic excluded — she only *takes/reduces* Psychic damage, doesn't deal it), Gibbascrapz (Blast excluded — from summoned Grot Tank), Hollan (Physical excluded — from summoned Aberrant Hypermorph), Commissar Yarrick (Physical, Las excluded — from summoned Cadian Guardsman), Corrodius (Physical excluded — from summoned Poxwalkers), Marshal Dreir (Physical excluded — from summoned Death Riders), Vynn (Plasma excluded — from summoned E-COG unit), Winged Prime (Physical excluded — from summoned Tyranid Warrior/Hormagaunt), Xybia (Physical, Projectile excluded — from summoned Neophyte Hybrid), and The Patermine (Bio excluded — from summoned Purestrain Genestealer).

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
| PIERCING DMG | `Has_Piercing = Y` (preferred over `Melee_Damage_Type`/`Ranged_Damage_Type`, which miss ability-only sources) |
| BOLTER DMG | `Has_Bolter = Y` |
| PSYCHIC DMG | `Has_Psychic = Y` |
| NO POWER DMG | `Has_Power = N` |
| [Any damage type] LE condition | `Has_[DamageType] = Y` (or `= N` for "NO [DamageType]" conditions) — see the 21 `Has_[DamageType]` columns below |
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

### Step 1 — Parse the patch notes

Patch notes use plain English descriptions that must be translated into CSV column conditions. The raw patch note format looks like this:

```
Alpha battles Enemies: Necrons Eligible factions: Imperial & Chaos Objectives
Defeat all enemies (30p) Full Ultramarine lineup (75p) Full Resilient lineup (95p)
Max 2 hits lineup (50p) Full Melee lineup (65p) Full Piercing Damage lineup (90p)
```

**Translation rules:**

| Patch note wording | CSV condition |
|-------------------|---------------|
| `Eligible factions: Imperial & Chaos` | `Alliance != "Xenos"` (No Xenos track) |
| `Eligible factions: Chaos & Xenos` | `Alliance != "Imperial"` (No Imperials track) |
| `Eligible factions: Imperial & Xenos` | `Alliance != "Chaos"` (No Chaos track) |
| `Full [Faction] lineup` | `Faction = "[Faction]"` |
| `Full Resilient lineup` | `Resilient = Y` |
| `Full Mechanical lineup` | `Mechanical = Y` |
| `Full Terminator Armour lineup` | `Terminator_Armour = Y` |
| `Full Big Target lineup` | `Big_Target = Y` |
| `Full Melee lineup` | `Has_Ranged = N` |
| `Full Ranged lineup` | `Has_Ranged = Y` |
| `Max 2 hits lineup` | `X_Hits_Restriction <= 2` |
| `Max 1 hits lineup` | `X_Hits_Restriction <= 1` |
| `Min 5 hits lineup` | `X_Hits_Restriction >= 5` |
| `Full [DamageType] Damage lineup` | `Has_[DamageType] = Y` |
| `No [DamageType] Damage lineup` | `Has_[DamageType] = N` |
| `No Psyker lineup` | `Psyker = N` |
| `Defeat all enemies` | **Ignore** — base objective, not a team composition condition |

Always ignore the "Defeat all enemies" objective line — it applies to all stages regardless of team and is not a trait condition.

### Step 2 — Provide Claude with the analysis input

Share the raw CSV (or the GitHub raw URL: `https://raw.githubusercontent.com/DBPreacher/Tacticus/main/tacticus_characters.csv`) and the parsed track data in this format:

```
LE [number] - [Character Name]
Alpha (No Xenos): [CONDITION] ([pts]), [CONDITION] ([pts]), ...
Beta (No Imperials): [CONDITION] ([pts]), [CONDITION] ([pts]), ...
Gamma (No Chaos): [CONDITION] ([pts]), [CONDITION] ([pts]), ...
```

### Step 3 — What Claude will output

Claude will:
1. Filter eligible characters per track (alliance restriction applied first)
2. Find characters eligible for each battle condition, flagging any pool with fewer than 6 chars (⚠️ limited pool)
3. Calculate the **most token-efficient starting team** — the team (3, 4, or 5 characters) that earns the highest total intersection score per token deployed. Do not default to any fixed team size. Evaluate all sizes and recommend whichever scores highest. A 5-man covering three high-value conditions in one deployment will beat a 3-man covering one low-value condition.
4. Build 5-man teams for full condition coverage using actual point values to prioritise high-value conditions first. **Point values must be provided before analysis begins** — do not substitute equal weighting, as this produces wrong prioritisation.
5. **Character overlap between teams is allowed and encouraged.** A character appearing in two teams allows the player to invest in one character and unlock two team slots. Always prefer solutions that reuse characters across teams, keeping the total number of unique characters required as low as possible. Never reject a recommendation solely because a character appears in more than one team.
6. Show the full eligible pool for each team's conditions alongside the recommended 5, so players can make substitutions based on their own roster.
7. Flag healers, self-healers, tanky characters, and mechanics in each team, noting any meta composition gaps (see Meta Notes below).

### Key scoring rules (important context for Claude)

- **All team members must share a condition** for the team to earn those bonus points
- Score = sum of point values for conditions ALL members satisfy (intersection, not union)
- Teams: minimum 3 characters, maximum 5
- 3-man teams typically reach stage 8-10 before difficulty peaks; 5-man teams push further
- 1 token = 1 team deployment for 1 stage attempt
- Points accumulate across all Alpha, Beta, and Gamma stages cleared
- **Point values are mandatory.** Do not begin analysis without them.
- **The most token-efficient team is whichever size (3, 4, or 5) earns the most points per token.** Always evaluate all sizes rather than assuming smaller is more efficient.
- **Overlap between teams is a feature, not a flaw.** Shared characters reduce the number of unique characters a player must develop. Always highlight which characters appear in multiple teams as high-priority investments.
- **Each team earns its intersection points independently per stage cleared.** A condition covered by two different teams earns points twice across deployments — this is not wasteful, it accumulates.

---

## Meta Notes

### Recommended team composition (priority order)

When selecting the 5 characters for a team, the trait intersection score determines point eligibility — but composition determines how far into the 18 stages you can push. The current recommended meta for deep-stage runs is:

**2 Healers + 2 Tanks + 1 Self-Healer**

Apply this as a tiebreaker when multiple characters are eligible for a team slot: always prefer the composition above over raw damage output.

**If the team is predominantly Mechanical characters** (Mechanical = Y), substitute Mechanics for Healers — Mechanical characters cannot be healed, only repaired:

→ **2 Mechanics + 2 Tanks + 1 Self-Healer** for Mechanical-heavy teams

When flagging team compositions after the analysis, Claude should identify which slots in each recommended team are filled by Healers, Tanks, Self-Healers, and Mechanics, and note any gaps (e.g. "no healer available in this pool").

### Tanks

Characters with these traits survive longest in high-difficulty stages:

| Trait | Effect | Priority |
|-------|--------|----------|
| `Terminator_Armour = Y` | First hit each turn deals -75% damage | High |
| `Mk_X_Gravis = Y` | All incoming damage goes through armour twice | High |
| `Resilient = Y` | Survives a lethal hit at 1 HP (unless overkilled) | Medium |

**Special tanks — ability-based, not trait-based:**

Two characters are among the best tanks in the game due to their abilities rather than their trait flags. Their `Terminator_Armour`, `Mk_X_Gravis`, and `Resilient` columns may all be N, but they should always be treated as high-priority tank options when eligible:

- **Tyrant Guard** — exceptional damage mitigation through abilities; treat as a top-tier tank regardless of trait flags
- **Thothmek** — exceptional survivability through abilities; treat as a top-tier tank regardless of trait flags

When building teams, if Tyrant Guard or Thothmek are eligible for the track and battle conditions, prioritise them in tank slots before other non-trait-tanky characters.

Trait assumptions: Do not assume any trait is faction-exclusive without verifying the CSV. For example, Unstoppable is an individual trait shared across multiple factions (Space Wolves, World Eaters, Adeptus Mechanicus, Orks, Genestealer Cults etc.) — not a Space Wolves faction trait. Always derive trait eligibility from the CSV columns, never from faction lore assumptions.

### Healers

- `Healer = Y` — heals a friendly unit as their action (sacrifices that turn's attack)
- `Self_Heal = Y` — heals themselves via ability (does not sacrifice the attack action — most efficient)
- `Mechanic = Y` — repairs Mechanical characters (functionally equivalent to Healer for Mechanical teams)

Prefer Self-Healers in the dedicated self-heal slot since they contribute offensively on the same turn. Healers and Mechanics occupy the remaining two support slots.

### Mechanical characters note

Mechanical characters (`Mechanical = Y`) **cannot be healed** — only repaired by a Mechanic. When building teams where most members are Mechanical, prioritise Mechanics over Healers. If a team has a mix, include at least one Mechanic if any Mechanical character is in the team.

---

## Fields Needing Manual Verification

### `Self_Heal` — always manual

`Self_Heal` is **not** derived from the wiki pass and must be populated by hand: read the character's individual ability descriptions and mark `Y` only if an ability restores the character's **own** HP (as opposed to healing/repairing an ally, or a generic team buff). This column is intentionally left untouched by any automated wiki update — when a new character is added, check their abilities and set `Self_Heal` manually before relying on it for team analysis.

Traits and the 44+21 Y/N columns for all 112 base characters plus the 10 Machines of War were re-verified against wiki pages directly (infobox traits + all ability text for damage types) as of the July 2026 full wiki pass — see Changelog. Newly added characters going forward should have their traits/damage types checked the same way (infobox for traits, full ability text for damage types) rather than assumed from game knowledge.

---

## Regenerating the XLSX

`tacticus_characters.xlsx` is a formatted, human-readable mirror of the CSV — **the CSV is always the source of truth**; never hand-edit the XLSX and expect it to persist, always regenerate it from the CSV after any CSV change.

The formatting rules are:
- Light green background (`#C6EFCE`) on every cell whose value is exactly `Y`
- Top row and first column frozen (freeze pane at B2)
- Column widths auto-fit to content
- Arial 10pt, bold header row

If a Python environment with `openpyxl` is available, regenerate with a short script that reads the CSV, writes each cell, applies a `PatternFill` of `C6EFCE` to `Y` cells, sets `sheet.freeze_panes = "B2"`, and auto-fits column widths from content length, then saves to `tacticus_characters.xlsx`.

If no Python/openpyxl is available (as was the case for this pass), the `.xlsx` can be built directly as a raw OOXML zip package (a `.xlsx` is just a zip of XML parts): `[Content_Types].xml`, `_rels/.rels`, `xl/workbook.xml`, `xl/_rels/workbook.xml.rels`, `xl/styles.xml`, `xl/worksheets/sheet1.xml`. Use inline strings (`t="inlineStr"`) to avoid needing a separate shared-strings part, define a `cellXfs` style with a solid `C6EFCE` fill for `Y` cells, and **write zip entry names with forward slashes** (e.g. `xl/worksheets/sheet1.xml`) — some zip APIs (like .NET's `ZipFile.CreateFromDirectory` on Windows) silently write OS-native backslashes instead, which produces a file Excel cannot open even though the zip itself is technically valid.

---

## Changelog

| Date | Change | Patch |
|------|--------|-------|
| July 2026 | Analysis methodology corrections: most efficient starting team is now evaluated across all sizes (3/4/5) not defaulted to a fixed size — whichever scores most points per token is recommended; character overlap between teams confirmed as desirable (minimises unique characters needed); point values now required before any analysis begins; overlap highlighted in output as high-priority investment signal | 1.36 |
| July 2026 | Added meta composition priority (2 Healers + 2 Tanks + 1 Self-Heal); Tyrant Guard and Thothmek noted as ability-based tanks; patch notes translation table added; Mechanics substitution rule for Mechanical teams added | 1.36 |
| July 2026 | Full wiki pass: re-verified all 44 trait columns for all 112 characters against wiki infoboxes (fixing known errors); added 21 new `Has_[DamageType]` columns capturing damage types from any source (primary attack or ability); added 10 Machines of War rows (`Is_MoW=Y`); regenerated `tacticus_characters.xlsx` with Y-cell highlighting, frozen panes, and auto-fit columns | 1.36 |
| July 2026 | Initial database built from wiki (Hits, Factions, Melee, Ranged, Trait pages) | 1.36 |
