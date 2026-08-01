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
├── le_analysis.py                ← analysis script (see Running a New LE Analysis)
├── le[N]_[character].yaml        ← one conditions file per LE
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
| `Parrying` | Last-resort tiebreak only — see definitions below |
| `Shielding` | Last-resort tiebreak only — see definitions below |
| `Spawner` | Last-resort tiebreak only — see definitions below |

**`Parrying` / `Shielding` / `Spawner` Columns (Y/N)**

These three are separate meta-tag columns, not part of the 43 wiki traits — they exist purely as the lowest-priority tiebreak in `le_analysis.py` (see Meta Notes → Full tiebreak hierarchy). Confirmed definitions (owner-provided):

- `Parrying` — `Y` if the character has the `Parry` trait. This always mirrors the `Parry` trait column exactly — if `Parry=Y` in the trait block, `Parrying=Y` too, and vice versa. Example: Forcas.
- `Shielding` — `Y` if any of the character's abilities grant a shield / block-damage bonus to **another** friendly character (not just to themselves — check whether the effect extends to allies). Example: Wrask (his passive shields allies).
- `Spawner` — `Y` if any of the character's abilities summon/create another unit onto the battlefield. Example: Tan Gi'da, Archimatos.

When adding a new character: `Parrying` is read straight off the trait list (no separate lookup needed). For `Shielding` and `Spawner`, read every ability description the same way you would for `Has_[DamageType]` — look for shield-granting or summon language in the full ability text, not just the primary attack stats.

**Damage Type Columns (Y/N) — `Has_[DamageType]`**

There are 21 `Has_[DamageType]` boolean columns, one per damage type in the game:

`Has_Bio`, `Has_Blast`, `Has_Bolter`, `Has_Chain`, `Has_Direct`, `Has_Energy`, `Has_Eviscerating`, `Has_Flame`, `Has_Heavy_Round`, `Has_Las`, `Has_Melta`, `Has_Molecular`, `Has_Particle`, `Has_Physical`, `Has_Piercing`, `Has_Plasma`, `Has_Power`, `Has_Projectile`, `Has_Psychic`, `Has_Pulse`, `Has_Toxic`

Unlike `Melee_Damage_Type` and `Ranged_Damage_Type` (which only capture the character's *primary* attack types and are kept unchanged as reference text columns), a `Has_[DamageType]` column is `Y` if the character deals that damage type from **any** source — primary melee/ranged attack **or** an active/passive ability. A character can have multiple damage types marked `Y` (e.g. a character with a Piercing melee attack whose ability triggers a Plasma-damage effect has both `Has_Piercing=Y` and `Has_Plasma=Y`).

**Why this matters for LE analysis:** LE damage-type conditions (e.g. "PIERCING DMG", "PSYCHIC DMG") should usually be checked against the relevant `Has_[DamageType]` column rather than `Melee_Damage_Type`/`Ranged_Damage_Type`, since some characters only deal a given damage type through an ability and would otherwise be missed (e.g. Abaddon deals Piercing only via his Drach'nyen bonus attack, not his primary Power melee attack).

**Damage sourced only from a summoned/independently-acting unit is excluded.** If a character's ability summons a separate unit (e.g. a Guardsman, Bloodletter, Spore Mine) that takes its own turn and attacks with its own stat line, that summon's damage type is **not** counted toward the summoning character's own `Has_[DamageType]` columns — only damage the character (or its own ability effects, like a mine or bonus-attack) deals directly is counted. When adding new characters, watch for this distinction and check ability text carefully.

This rule is confirmed (owner-reviewed) as the correct approach — apply it consistently on future updates rather than re-litigating per character. In the July 2026 pass it changed the result for: Abraxas (Physical, Power excluded — from summoned Pink Horror / Screamer of Tzeentch), Ammuk (Energy excluded — from summoned Ironkin Steeljack), Anuphet (Physical, Molecular excluded — from summoned Necron Warriors), Archimatos (Piercing excluded — from summoned Bloodletter), Atlacoya (Psychic excluded — she only *takes/reduces* Psychic damage, doesn't deal it), Gibbascrapz (Blast excluded — from summoned Grot Tank), Hollan (Physical excluded — from summoned Aberrant Hypermorph), Commissar Yarrick (Physical, Las excluded — from summoned Cadian Guardsman), Corrodius (Physical excluded — from summoned Poxwalkers), Marshal Dreir (Physical excluded — from summoned Death Riders), Vynn (Plasma excluded — from summoned E-COG unit), Winged Prime (Physical excluded — from summoned Tyranid Warrior/Hormagaunt), Xybia (Physical, Projectile excluded — from summoned Neophyte Hybrid), and The Patermine (Bio excluded — from summoned Purestrain Genestealer).

**Legacy damage type name — `Gauss` = `Molecular`.** Some sources (notably tacticustable.com, whose data appears to retain older internal labels) will show a weapon's damage type as "Gauss". This is not a current damage type — the wiki.gg `Damage_Types_and_Pierce_Ratio` page's changelog confirms *"July 2023: Gauss and Enmitic damage types combined and renamed Molecular."* Any weapon/ability labeled Gauss should be recorded as **Molecular** in `Melee_Damage_Type`/`Ranged_Damage_Type` and `Has_Molecular`, not as a new column. First encountered on Lhykhis (patch 1.41), confirmed by the owner. If a source ever shows an unrecognized damage-type label, check the wiki.gg changelog for a similar rename before creating a new `Has_[DamageType]` column for it.

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

### Using tacticustable.com for brand-new characters

`tacticus.wiki.gg` community pages usually lag behind a patch by a few days — a character can be live in-game with no wiki.gg page yet (404). For characters that new, use **tacticustable.com** instead: `https://www.tacticustable.com/wiki/heroes/[slug]` (lowercase, e.g. `lysander`, `sekhetar`).

**tacticustable.com is a JS-rendered React app — `WebFetch` only sees an empty shell** (`"Tacticus TableReact App"`, no actual content). It must be opened with the **Browser tool** (`preview_start` / `navigate` to the URL, then `get_page_text` with a high `max_chars`, e.g. 9000–10000, since the page is long) so the JS actually renders. This is the single most important gotcha in this workflow — a plain fetch will look successful but return nothing usable.

Once rendered, pull the following from the page text and map it to CSV columns:

| Page section | CSV column(s) |
|---|---|
| `FACTION` field (e.g. `AdeptusAstartes`, `LeaguesOfVotann`) | `Faction` — insert spaces to match existing convention: "Adeptus Astartes", "Leagues of Votann" |
| `ALLIANCE` field | `Alliance` |
| `MELEE WEAPON` row (`[Type] HITS: [n] PIERCING: [%]`) | `Melee_Hits`, `Melee_Damage_Type` (map legacy names — see Gauss/Molecular above; "Eviscerate" → "Eviscerating") |
| `RANGE WEAPON` row, if present | `Has_Ranged=Y`, `Ranged_Hits`, `Ranged_Damage_Type`. If no `RANGE WEAPON` section appears at all, `Has_Ranged=N` |
| `TRAITS` section (exact trait names listed) | the corresponding trait columns — `Y` only for traits actually listed, everything else `N` |
| `ACTIVE ABILITY`, `PASSIVE ABILITY`, and `RELIC` text (relic only if one is shown equipped) | read the **full ability text** for: any damage type mentioned beyond the primary attack (→ `Has_[DamageType]`), whether it heals the character's own HP (→ `Self_Heal`), whether it grants a shield/block bonus to *another* friendly character (→ `Shielding`), whether it summons/creates a unit (→ `Spawner`) |
| `TRAITS` section contains `Parry` | `Parrying=Y` (mirrors the trait exactly — see the Parrying/Shielding/Spawner section above) |

Apply the same judgment rules used for the wiki.gg pass: a damage type or effect that's only a **trigger condition referencing damage other units dealt** (not the character's own) doesn't count (same as the Farsight/Shadowsun Psychic-exclusion precedent); a shield/heal/summon effect that only affects **the character itself**, not allies, doesn't count as `Shielding`/`Spawner` (though it can still count as `Self_Heal`, which is self-only by definition).

If wiki.gg *does* have a page for the character already, prefer it as the primary source and use tacticustable.com only to cross-check — wiki.gg's community-written prose is easier to parse unambiguously than tacticustable.com's raw ability-chart text. If a value looks unusual or doesn't match any known damage type/trait, don't guess — flag it to the owner before adding it, the way the Gauss/Molecular case was caught.

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
2. Print the track's Enemies and Eligible factions (if provided in the yaml), followed by each battle condition's own qualifying pool size, flagging any pool with fewer than 6 chars (⚠️)
3. Calculate the most efficient starting team (3–5 characters — whichever size scores highest; **not** a fixed 3- or 4-man team)
4. Solve for the true points-maximizing set of 5-man Full Coverage teams (see "Full Coverage algorithm" below) — token count only ever matters as a tiebreak between options that score identically on points
5. Apply the reuse tiebreak within a track, and carry it across tracks (Alpha → Beta → Gamma) so later tracks get credit for reusing a character already committed earlier in the event
6. Flag healers, self-healers, mechanics, and tanks in each team, plus a `★ High-priority investment` note when a character appears on 2+ teams within a track
7. Print a `📝` note when a team reuses a character from an earlier team in the same track, and a `🔗 Cross-track win` note when it reuses a character already committed in a *different* track
8. Print a final **Cross-Track Investment Summary** (every character used in 2+ tracks) and a **Champion Usage Leaderboard** — every character used more than once this event, grouped into Healers (Healers + Mechanics) / Tanks / Self-Heal + Damage Reduction / Most used overall — for the whole event. The analysis prints the full list per category; trimming to a top-N for video display is a presentation choice, not something the script does

### Full Coverage algorithm — no dilution, exact optimization

The Full Coverage search is an **exact optimizer**, not a greedy/anchored search:

1. Enumerate every non-empty subset of a track's battle conditions (≤31 subsets for 5 conditions) and check whether at least **5** characters individually satisfy **every** condition in that subset at once. If fewer than 5 do, that combination is simply unachievable — there is no fallback to a wider pool, no diluted team padded out with characters who don't actually qualify. A trait only counts toward a condition if **every** member of the team has it (intersection, never union).
2. Among all achievable combinations, solve exactly (via small memoized recursion — at most 32 states) for the combination of teams that **maximizes total points**. Token count is only used as a tiebreak between options that score identically on points — the analysis never trades points away to save a token.
3. Present the winning teams in descending point order, then build each team's actual roster sequentially, applying the reuse tiebreak (see Meta Notes) as it goes.

### Key scoring rules (important context for Claude)

- **All team members must share a trait** for the team to earn those bonus points — score = sum of point values for traits ALL members share (intersection, not union), with no exceptions
- Full Coverage teams are always exactly 5 characters; the Fastest-Method starting team can be 3, 4, or 5 (whichever scores highest)
- 1 token = 1 team deployment for 1 stage attempt
- Points accumulate across all Alpha, Beta, and Gamma stages cleared
- "Defeat all enemies" objectives are always ignored — they're a base reward, not a team-composition condition

---

## Meta Notes

### Full tiebreak hierarchy (in priority order)

Raw battle points always come first and are never traded away. Below that, `le_analysis.py` breaks ties between equally-scoring teams in this order:

1. **Named priority picks** — Tyrant Guard, Thothmek, and any configured priority pairs (see Special tanks below)
2. **Meta composition** — Healers/Mechanics (support), Self-Heal, Tanks (trait-based)
3. **Reuse** — prefer a character already committed to an earlier team, **within the current track**
4. **Reuse — cross-track** — the same reuse preference, but carried forward across tracks in Alpha → Beta → Gamma order, so Beta/Gamma teams get credit for reusing a character Alpha already committed to. This only ever sets a *pattern* for later tracks to follow — Alpha itself never benefits from what Beta/Gamma will need, since it's processed first
5. **Resilient** — minor bonus
6. **Parrying / Shielding / Spawner** — last-resort differentiators, weighted below everything above including Resilient. No preference between the three; they only ever matter once every stronger tier is fully tied

This hierarchy is why the analysis's reuse notes come in two flavors: a plain `📝` note for reuse within the same track, and a `🔗 Cross-track win` note when the reused character was actually committed in a *different* track — the latter is the bigger deal for leveling investment, since it means one fewer character to invest in for the whole event, not just one track.

### Recommended team composition (priority order)

When selecting the 5 characters for a team, the trait intersection score determines point eligibility — but composition determines how far into the 18 stages you can push. The current recommended meta for deep-stage runs is:

**2 Healers + 2 Tanks + 1 Self-Healer**

Apply this as a tiebreaker when multiple characters are eligible for a team slot: always prefer the composition above over raw damage output.

**If the team is predominantly Mechanical characters**, substitute Mechanics for Healers — Mechanical characters cannot be healed, only repaired:

→ **2 Mechanics + 2 Tanks + 1 Self-Healer** for Mechanical-heavy teams

A team is considered Mechanical when 3+ members have `Mechanical=Y` **or** `Living_Metal=Y`. Living Metal is a Necron faction trait that confers Mechanical status — Imospekh, Aleph-Null, Anuphet, Thutmose, Makhotep and other Necrons with Living Metal all count toward this threshold. This is handled automatically by `le_analysis.py`. Good Mechanical team pairings: Re'vas + Aleph-Null, Tan Gi'da + Actus.

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

**July 2026 correction:** Makhotep was missing `Self_Heal=Y` — he has a passive that heals himself (as well as others) and was fixed after review flagged him as an unexplained gap in an otherwise-consistent character-usage check. If a "characters with zero tiebreak traits" sanity check ever flags a well-known character with strong abilities, treat that as a signal to double-check their `Self_Heal` (and trait columns generally) rather than assuming the check is wrong.

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
| July 2026 | Added Lysander, Kimm, Sekhetar, Lhykhis (Ramus already present, verified unchanged) via tacticustable.com since wiki.gg pages didn't exist yet for these; documented the tacticustable.com breakdown workflow and the Gauss→Molecular legacy damage-type mapping in this file | 1.41 |
| July 2026 | Added `Parrying`, `Shielding`, `Spawner` as new Y/N trait columns (populated across the roster) and wired them into `le_analysis.py` as the lowest-priority tiebreak tier — see Meta Notes | 1.37 |
| July 2026 | Fixed Makhotep missing `Self_Heal=Y` (he has a self-healing passive) — caught via a "characters with zero tiebreak traits" sanity check | 1.37 |
| July 2026 | Rewrote `le_analysis.py`'s Full Coverage team search from an anchor-based greedy bundler (which could pick a low-value combo before ever trying the highest-value one, and could dilute a too-small pool with non-qualifying filler characters) to an exact optimizer: enumerate every achievable objective-subset with a genuine 5+ character pool, then solve exactly for the point-maximizing combination of teams, tiebreaking on fewest tokens only when points are exactly equal. No more diluted "pure intersection pool" teams — a combination is only ever presented if 5+ characters can genuinely satisfy every condition in it | 1.37 |
| July 2026 | Added a reuse tiebreak (`REUSE_BONUS`) to `meta_score` — among equally-scoring teams, prefers reusing a character already committed to an earlier team, to reduce total unique characters needed. Weighted below meta composition (support/self-heal/tanks) but above Resilient, per confirmed priority: points > named priority/DR > meta composition > reuse > Resilient > Parrying/Shielding/Spawner | 1.37 |
| July 2026 | Extended the reuse tiebreak across tracks (Alpha → Beta → Gamma) via a shared usage/track-history dict, so Beta and Gamma teams get credit for reusing a character Alpha already committed to. Reuse notes now come in two flavors: `📝` for within-track reuse, `🔗 Cross-track win` for reuse across tracks (the bigger investment saving) | 1.37 |
| July 2026 | Added a per-track "Enemies" / "Eligible factions" line to the analysis output, printed directly above that track's objective list, sourced from the yaml's `enemies` and `allowed_alliances` fields | 1.37 |
| July 2026 | Added a **Cross-Track Investment Summary** (every character used in 2+ tracks, for the whole event) and a **Champion Usage Leaderboard** to the end of the analysis output, tallied automatically across every team in every track — built to be usable directly for video content without further manual tallying | 1.37 |
| July 2026 | Reworked the Champion Usage Leaderboard to match the Monthly Plan's four video cards exactly: **Healers (Healers + Mechanics)**, **Tanks** (trait-based only — `Terminator_Armour`/`Mk_X_Gravis`), **Self-Heal / Damage Reduction** (`Self_Heal=Y` plus Tyrant Guard/Thothmek — the two ability-based DR picks now live here, not in Tanks), **Most used overall**. The script prints the full list of every character used more than once per category (no cap) — trimming to the top 4 for the video card layout is done in the HTML template, not the script. Categories intentionally overlap (e.g. Toth appears in both Tanks and Self-Heal/DR) — they're independent tallies, not a partition | 1.37 |
| July 2026 | Fixed a real bug in `best_team_from_pool`'s >25-character fallback path: named `PRIORITY_PAIRS` (e.g. Aleph-Null + Re'vas) were invisible to it, since it sorted individuals by their own trait score with no way to express "only valuable if a specific partner is also picked" — so a pairing worth +60 as a team could lose to a stronger-looking individual pick (e.g. a Mechanic with a reuse bonus) even when both pair members were sitting right there in the pool. Fixed by force-including any complete pair (or `PRIORITY_SOLO` member) present in the pool into a shortlist, then running the same exact combo scorer used for pools ≤25 on that shortlist, instead of a blind per-character top-5 cut | 1.37 |
| July 2026 | Living Metal now counts as Mechanical for team detection — Necrons with `Living_Metal=Y` (Imospekh, Aleph-Null, etc.) correctly trigger the Mechanic-over-Healer pathway when 3+ appear in a team | 1.36 |
| July 2026 | Full wiki pass: re-verified all 44 trait columns for all 112 characters against wiki infoboxes (fixing known errors); added 21 new `Has_[DamageType]` columns capturing damage types from any source (primary attack or ability); added 10 Machines of War rows (`Is_MoW=Y`); regenerated `tacticus_characters.xlsx` with Y-cell highlighting, frozen panes, and auto-fit columns | 1.36 |
| July 2026 | Initial database built from wiki (Hits, Factions, Melee, Ranged, Trait pages) | 1.36 |
