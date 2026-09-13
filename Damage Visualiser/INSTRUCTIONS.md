# Damage Visualiser — Instructions

How to keep the **Roster Battle Map** up to date. It's written for the
owner and for future Claude sessions: follow it step by step, and you
shouldn't need this conversation's history.

- **What it is:** an interactive chart of every playable character.
  - **Damage** = how many of their attacks it takes to kill a typical enemy.
  - **Toughness** = how many attacks a typical enemy needs to kill them.
  - All at Winged D3 with no gear, for the DB Preacher Plays channel.
- **The rules behind the numbers:** `DAMAGE_MODEL.md`.
- **Design decisions and next steps:** `PLAN.md`.

**Live page (private to the owner):**
https://claude.ai/code/artifact/56e1db91-e3a8-45aa-ba58-0d2c9a8b84f8

---

## Files

| File | What it is | Edit by hand? |
|---|---|---|
| `update_game_data.py` | Downloads the game data from tacticustable.com into `cache/gameinfo.json`, only when the game version has changed | No |
| `build_map.py` | Runs the model and writes every output below. The standard setup (rank, stars, ability levels) is at the top | Only to change the setup |
| `active_abilities.csv` | One row per character: how their active ability is counted. **Reviewed data**: the script adds rows but never overwrites your decisions | **Yes** |
| `map_template.html` | The page design and code. `/*DATA*/` is replaced with the model output | Yes, for design changes |
| `roster-battle-map.html` | The built page that gets published | **Never.** It's overwritten on every build |
| `cache/gameinfo.json` | The downloaded game data (about 11 MB), ignored by git | No |
| `../LRE Script/tacticus_stats.csv` | Output: the stats "second tab" (stats, weapons, active ability, all scenario scores) | **Never.** It's overwritten |
| `DAMAGE_MODEL.md` / `PLAN.md` | Rules record and design plan | Yes, whenever a rule or decision changes |

The roster comes from `../LRE Script/tacticus_characters.csv`: every row
except `Is_MoW=Y` and `Do_Not_Use=Y`. That file stays the source of truth
for who exists. This folder never writes to it.

---

## After a patch

Run these from inside `Damage Visualiser/`:

```
python -X utf8 update_game_data.py
python -X utf8 build_map.py
```

1. **`update_game_data.py`** prints the live and cached game versions. It only
   downloads when they differ; add `--force` to download anyway.
   tacticustable.com usually updates a day or two after a patch. If the version
   hasn't moved yet, try again later.
2. **`build_map.py`** prints what needs attention:
   - `WARNING - in the CSV but not in the game data`: a name doesn't match.
     Add a line to `ALIAS` in `build_map.py`, mapping the normalised CSV name to
     the game data name (lowercase letters and digits only, e.g.
     `'commandershadowsun': 'shadowsun'`).
   - `drafted N new row(s)`: new characters now have a best-guess row in
     `active_abilities.csv`. Review them (see below).
   - `ability text changed, now flagged for review`: a patch changed an active
     ability's wording. Re-read those rows.
   - `N row(s) marked Needs_Review=Y`: the full list still waiting for a
     decision.
3. **Review** the flagged rows in `active_abilities.csv` (rules below).
   - Fix the columns, write a short `Notes` entry, and set `Needs_Review=N`.
   - For a genuine judgement call, leave `Needs_Review=Y`, start the note with
     `OWNER:` and ask the owner.
4. **Run `build_map.py` again.**
5. **Optional check** against the owner's Creed test numbers (a file in their
   Downloads, not in the repo):
   `python -X utf8 build_map.py --creed "C:/Users/andyd/Downloads/Tacticus - Castellan Creed Test.csv"`.
   - September 2026 baseline: **148 of 250** within 1%.
   - The file dates from 2024–2026, so the match rate slowly falls as patches
     change characters. A *sudden* big drop means the model or the data broke.
6. **Republish the page to the same link:**
   - Call the Artifact tool with `action: "read"` on the URL above. The tool
     refuses to update a page this conversation hasn't read.
   - Then publish `Damage Visualiser/roster-battle-map.html` with `url` set to
     that URL.
   - Publishing without `url` creates a separate page with a new link.
7. **Commit and push:** `active_abilities.csv`, `roster-battle-map.html`,
   `../LRE Script/tacticus_stats.csv`, and any doc changes. `CLAUDE.md`
   pre-approves commit and push to `main`.

### Quick sanity checks after a build

| Check | Expected | If it doesn't |
|---|---|---|
| Creed against himself (click Castellan Creed; the Sparring line) | About **3,260** per attack, matching the Creed test | The stat or formula handling broke |
| Kharn, Map view, Active Level 50 | Damage **below 1 attack** | Active parsing broke |
| Kharn, Active Level 36 | No better than his normal attack (see "The level 36 finding" below) | Active parsing broke |
| Number of characters | Same as the non-MoW, non-Do_Not_Use rows in the CSV | A name didn't match; see the `ALIAS` warning |

---

## Adding a new character

1. Add them to `../LRE Script/tacticus_characters.csv` first, using the
   normal LE workflow in `../LRE Script/INSTRUCTIONS.md`. Leave
   `Do_Not_Use=Y` until they're released.
2. Wait until tacticustable.com has them: `update_game_data.py` reports the new
   version.
3. Run `build_map.py`. It drafts their `active_abilities.csv` row. Review it
   against the rules below, then build again and republish.

---

## `active_abilities.csv`: columns and review rules

The model assumes each character **opens with their active ability**, then
carries on with normal attacks. It uses the active only if that kills
faster than a normal attack alone. **Damage only counts against one
target, and only the first use counts.**

| Column | Meaning |
|---|---|
| `Name` | Matches `tacticus_characters.csv` |
| `Active` | Ability name (refreshed from the game data on each build) |
| `Kind` | `damage` (the only kind that changes the numbers), `summon`, `heal`, `defence`, `support` |
| `Damage_Parts` | Which damage values in the ability text count, separated by `;` (see below). Blank = none |
| `Normal_Attack` | `Y` = the ability includes a normal attack by the character; `PCT` = a normal attack at `{[dmgPct]}`% of their Damage, capped at `{[maxDmg]}` a hit; `N` = no |
| `Normal_Bonus` | Extra damage on that normal attack (see below). Blank = none |
| `Same_Turn` | `Y` if the text says using it **does not end the turn**: the character also makes a normal attack that turn |
| `Needs_Review` | `Y` = waiting for a decision. The build lists these |
| `Notes` | What was and wasn't counted, in plain words. Start with `OWNER:` for anything the owner must decide |
| `Ability_Text` | The ability text with `{[placeholders]}`. Refreshed on each build; a change flags the row for review |

**`Damage_Parts` tokens:**
- `1`, `2`, `3` = the `{[minDmg]}`-`{[maxDmg]}` damage value, then the `_2` and
  `_3` ones.
  - The hit count is read from the text in front of that value:
    `{[nrOfHits]}x {[minDmg]}`, or a number written into the text like
    Imospekh's `6x`.
  - The damage type is `damageProfile`, `damageProfile_2`, and so on.
- `key[i]` = entry `i` of a comma-separated flat damage value, e.g. Aethana's
  `dmg[0]` (first target of her wave).

**`Normal_Bonus`:**
- A variable name, e.g. `dmg`, adds that many extra hits of flat damage to the
  normal attack (Pestillian, Shadowsun).
- `+key`, e.g. `+extraDmg`, adds that variable to the character's Damage stat
  for the attack (Ragnar, Celestine, Lucien, Jaeger, Farsight, Gulgortz).
- It applies to the first normal attack in the opening turn, whether that
  attack comes from `Normal_Attack` or `Same_Turn`.

**Review rules.** These are the precedents set in September 2026; apply them
consistently:

1. **One target.** Count only damage that hits the main target. If damage
   also hits "all adjacent enemies", "enemies behind the target", or "another
   random enemy" through a separate value (`_2`), leave that part out:
   - Kimm, Mataneo, Sarquael, Typhus, Tyrant Guard and Maugan Ra are `1` only.
   - If every attack prioritises the same target, count them all (Kharn's
     `1;2;3`, Nubari's `1;2`).
2. **Summons never count.** This is the same rule as the `Has_[DamageType]`
   columns in the LE CSV. A summoned unit's attack isn't the character's.
   Also not the character's: an attack by a possessed enemy (Thaumachus), by
   other units (Makhotep), or by the summon itself (Winged Prime's Warrior).
3. **Conditional extras don't count:** "+X for each…", "if the target is…",
   "doubles at low health", chance-based hits. Count the base value and name
   what was left out in `Notes`.
4. **"If X has not moved"** conditions on an active *are* counted. The player
   chooses to use it (Dante, Dreir, Ragnar, Gulgortz, Lucien).
5. **Effects that last the rest of the battle** (Abaddon's Drach'nyen) or
   **damage that lands next turn** (Azkor, Sho'syl): count one use in the
   opening turn, and say so in `Notes`.
6. **Damage that only hits enemies moving away** (Trajann) is defence, not
   damage.
7. **Defensive actives** (heals, shields, damage reduction) are `defence` or
   `heal` and **aren't modelled yet**. Toughness ignores them. This is a
   planned later step.

The six `OWNER:` rows waiting on the owner in September 2026: Abaddon,
Ahriman, Asmodai, Azrael, Thaddeus Noble, Titus.

---

## Changing the setup

The constants at the top of `build_map.py`:

| Constant | Now | Meaning |
|---|---|---|
| `RANK` | `DIAMOND III` | The rank row used from the game data (`STONE I` … `ADAMANTINE II`, also `MYTHIC I`/`II` in the data) |
| `STARS` | `11` | Winged. Rank stats are stored at 0 stars; each star adds 10% (`STAR_MULT = 1 + 0.1 × STARS`) |
| `ABILITY_LEVELS` | `(36, 50)` | One "Active ability" button per level on the page |
| `RARITY_MULT` | `1.8` | Legendary. Ability values = the level's entry × this, only for variables listed in `variablesAffectedByRarityBonus`. Common 1.0 … Mythic 2.0 |

For the planned **Mythic view**: 14 stars, `ADAMANTINE II`, levels up to 60,
`RARITY_MULT = 2.0`, plus relic effects, which aren't in the model yet. Run it
as a separate build rather than replacing the D3 page.

## Changing the page

- Edit **`map_template.html` only**, then run `build_map.py`. Never edit
  `roster-battle-map.html`.
- The page is deliberately **dark only**, to match the channel's video
  template.
- Fonts are Cinzel (headings), Rajdhani (numbers and labels) and Inter (text),
  the same as the LE video template.
- **Alliance colours** come from the in-game alliance icons: Imperial gold
  `#d9ad3f`, Chaos red `#dc4638`, Xenos light blue `#5cbfe0`.
  - Gold and light blue are brighter than the chart skill's preferred band.
    That's owner-chosen and accepted.
  - The colourblind separation check passes (ΔE 15.9).
  - Everything else on the page is neutral grey or white, so no interface
    colour can be mistaken for an alliance.
- **Views:**
  - **Map** is the scatter plot.
  - **Attack** keeps the damage axis and spreads the dots sideways, so they
    don't overlap.
  - **Defence** does the same for toughness.
- **Scenario keys** in the data: `base`, `trig`, `base_a36`, `trig_a36`,
  `base_a50`, `trig_a50`. The first part is the traits setting, the suffix is
  the active ability level.

---

## Gotchas

- **tacticustable.com data comes from one public address,** so no browser is
  needed: `https://api.tacticustable.com/game-info` (version at `/version`).
  - The website itself only renders in a browser. That's the gotcha in
    `../LRE Script/INSTRUCTIONS.md`, but that applies to the web pages, not
    this API.
  - Download it once per game version. It's a fan site, so don't hammer it.
- **Hero names:** `name` is the short name (e.g. "Creed", "Tigurius"), and
  `longName` is usually the CSV name. The script matches on `longName`, `name`
  and `id`, then `ALIAS`.
- **Damage type names in the game data:**
  - `Eviscerate` = Eviscerating, `Gauss` = Molecular, `HeavyRound` = Heavy
    Round, `DirectDamage` = Direct.
  - `Acid` exists in the data but no character uses it.
- **Ability arrays** hold one entry per level: entry `level − 1`, so level 36
  = index 35.
- **Terminator Armour** has reduced the whole first *attack* each turn since
  September 2024, not the first hit. In kill counts, only the first attack is
  reduced; the enemy is assumed to focus fire in one turn.
- **Creed test numbers** include Rapid Assault and Ranged Specialist, which
  the game shows. The chart's always-on scenario leaves them out, by the
  owner's decision. `--creed` adds them back for the comparison only.
- **The level 36 finding.** At Winged D3, only about 18 of the 82 damaging
  actives beat a normal attack at level 36; at level 50, about 60 do. So
  "Active: Level 36" barely moves the chart. That's correct, not a bug, and
  it's why both levels are offered.

---

## Changelog

| Date | Change |
|---|---|
| September 2026 | First version: `update_game_data.py`, `build_map.py`, `active_abilities.csv` (all 117 reviewed; 6 left for the owner), Attack/Defence/Map views, Active ability at level 36/50, alliance colours from the in-game icons |
