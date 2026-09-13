# Damage Visualiser — Instructions

How to keep the **Roster Battle Map** up to date. It's written for the
owner and for future Claude sessions: follow it step by step, and you
shouldn't need this conversation's history.

- **What it is:** an interactive chart of every playable character.
  - **Damage** = how many of their attacks it takes to kill a typical character (the middle result against the whole roster).
  - **Toughness** = how many attacks a typical character needs to kill them.
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
| `passive_abilities.csv` | The same, for passive abilities: `Attack` and `Defence` tokens | **Yes** |
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
     `active_abilities.csv` and `passive_abilities.csv`. Review them (see
     below).
   - `ability text changed, now flagged for review`: a patch changed an active
     ability's wording. Re-read those rows.
   - `N row(s) marked Needs_Review=Y`: the full list still waiting for a
     decision.
3. **Review** the flagged rows in both ability files (rules below).
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
7. **Commit and push:** `active_abilities.csv`, `passive_abilities.csv`, `roster-battle-map.html`,
   `../LRE Script/tacticus_stats.csv`, and any doc changes. `CLAUDE.md`
   pre-approves commit and push to `main`.

### Quick sanity checks after a build

| Check | Expected | If it doesn't |
|---|---|---|
| Creed against himself (click Castellan Creed; the Sparring line) | About **3,260** per attack, matching the Creed test | The stat or formula handling broke |
| Kharn, Map view, Ability level 50, Active on | Damage **below 1 attack** | Active parsing broke |
| Re'vas detail panel, Ability level 50 | Passive shows "+3× Particle 749 on each attack" | Passive parsing broke |
| Number of characters | Same as the non-MoW, non-Do_Not_Use rows in the CSV | A name didn't match; see the `ALIAS` warning |

---

## Adding a new character

1. Add them to `../LRE Script/tacticus_characters.csv` first, using the
   normal LE workflow in `../LRE Script/INSTRUCTIONS.md`. Leave
   `Do_Not_Use=Y` until they're released.
2. Wait until tacticustable.com has them: `update_game_data.py` reports the new
   version.
3. Run `build_map.py`. It drafts their `active_abilities.csv` and `passive_abilities.csv` rows. Review them
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
| `Defence` | How the active protects the character itself (Toughness), as tokens separated by `;` (see below). Blank = nothing |
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

**`Defence` tokens.** `VAR` is an ability variable name. `A+B` adds two
variables together. The scope can be `all` (the default), `melee`, `ranged`
or `one`:

| Token | Meaning | Example |
|---|---|---|
| `pct:VAR[:scope]` | Takes −VAR% damage | Aesoth `pct:dmgReductionPct`; Azkor `pct:dmgReductionPct:ranged` |
| `flat:VAR[:scope]` | Enemies deal −VAR Damage per hit, before armour | Calandis `flat:dmgReduction:ranged`; Jaeger `flat:dmgReduction:one` |
| `epct:VAR[:scope]` | Enemies deal −VAR% | Dante `epct:dmgReductionPct:melee` |
| `suppress[:scope]` / `stun[:scope]` | Enemies deal −30% / −50% | Thothmek `suppress:all`; Arjac `stun:one` |
| `heal:VAR[+VAR]` | Extra health (heal, repair, revive) | Rotbone `heal:hpToHeal+hpToHeal_2` |
| `lose:VAR` / `setpct:VAR` | Costs health: loses VAR% / is set to VAR% | Macer `lose:hpPct`; Lucien `setpct:hpPct` |

What each scope means:
- `all`: every enemy attack in the turn.
- `one`: the first attack only. Use it for effects on a single target.
- `melee`: use it for "adjacent enemies".
- `ranged`: ranged attacks only.

The build stops with an error on a token it doesn't know.

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
7. **Defence: only protection for the character itself.**
   - Heals that also reach allies count for the character, e.g. Incisus uses
     his Imperial amount.
   - Protecting an ally doesn't count (Xybia, Aun'Shi).
   - Block bonuses need block gear, so they don't count.
   - Conditional heals don't count (rule 3).
   - An area suppress or stun is scope `all`; one on the target or a line of
     enemies is `one`.
8. **Overwatch set up by an active counts as that turn's attack:** one
   normal attack, with any +Damage the ability gives (`Normal_Attack=Y`,
   `Normal_Bonus=+extraDmg`). Re'vas was the first case; she was wrongly
   logged as a summon at first.
9. **Percentage values step at level 36**, e.g. Thoread 31% → 33%. The build
   reads the value for each level from the game data, so no manual numbers
   are needed.

All six owner questions from September 2026 (Abaddon, Ahriman, Asmodai,
Azrael, Thaddeus Noble, Titus) were answered and are recorded in their
`Notes` as "Owner-confirmed".

---

## `passive_abilities.csv`: columns and review rules

Passives are **always on** in every view: they're the character's own kit.
The plain stat line, with no abilities at all, is kept only as the reference
for the "Stat line" column and the shift arrows.

| Column | Meaning |
|---|---|
| `Name`, `Passive`, `Ability_Text` | As in the actives file |
| `Attack` | Effects on the character's **own normal attacks**, as tokens separated by `;` |
| `Defence` | Effects protecting the character itself: the same tokens as the actives' `Defence`, plus the extra ones below |
| `Needs_Review`, `Notes` | As in the actives file. Start the note with `OWNER:` for owner questions |

**Token format:** `kind:VAR[:scope][:vsTrait|Trait][@trig]`.
- `VAR` is an ability variable name, or a plain number.
- The scope can be `all` (the default), `melee`, `ranged`, `after` (every
  attack except the first) or `one` (the first attack only).
- `vs…` limits the effect to targets with one of those traits, using the game
  data trait IDs: `Psyker`, `BigTarget`, `MkXGravis`, `TerminatorArmour`,
  `Mechanical`, `Vehicle`. In a `Defence` token, `vs…` means the *attacker*
  has that trait.
- `@trig` means the effect only counts with **Traits: All triggered**. Use it
  when the passive needs charging, moving or not moving, e.g. Kut Skoden
  `flat:extraDmg:melee@trig`.

**`Attack` tokens:**

| Token | Meaning | Example |
|---|---|---|
| `extra:PART` | Extra ability hits after each normal attack (`PART` as in `Damage_Parts`) | Kharn `extra:1`; Burchard `extra:1:ranged` |
| `flat:VAR` | +VAR Damage on each hit | Lysander `flat:extraDmg`; Roswitha `flat:extraDmg::vsPsyker` |
| `pct:VAR` | +VAR% damage | Forcas `pct:extraDmgPct:melee` |
| `pierce:VAR` | +VAR% pierce ratio | Sy-Gex `pierce:extraPierceRatio:ranged:vsMkXGravis\|TerminatorArmour\|Mechanical` |
| `hits:VAR` | +VAR hits | Vitruvius `hits:nrOfHits:after` |
| `armignore:VAR` | Ignores VAR Armour | Snappawrecka `armignore:armorIgnored` |
| `ramp:VAR` | Each hit deals +VAR more than the last | Lhykhis `ramp:extraDmg:after` |
| `follow:ranged` | Melee attacks are followed by a normal ranged attack | Commander Farsight |

**Extra `Defence` tokens** (for passives, though actives can use them too):

| Token | Meaning | Example |
|---|---|---|
| `armour:VAR` | +VAR Armour | Gibbascrapz `armour:extraArmor_2` |
| `hitsless:VAR[:scope]` | Attackers score −VAR hits (min 1) | Jain Zar `hitsless:hitsReduction:melee` |
| `pctcap:PCT/CAP` | Takes −PCT% damage, at most −CAP per hit | Tyrant Guard `pctcap:dmgReductionPct/dmgReduction@trig` |
| `cap_first:VAR` | The first attack each turn takes at most VAR% of health | Judh `cap_first:hpPct` |
| `armourpass:VAR` | Attacks go through an extra Armour pass of VAR (like Mk X Gravis with a set value) | Uthar `armourpass:extraArmor` |
| `guard:HP/ARMOUR` | A bodyguard takes the attacks first, with its own health and Armour | Creed (Kell) `guard:summonHp/summonArmor` |
| scope `psychic` | Only against Psychic damage | Atlacoya `flat:dmgReduction:psychic` |

**Review rules for passives:** the same as the actives' rules 1–3 and 7
(one target; no summons; no conditional extras; only the character itself).
Also:
- **Buffs that reach "friendly units" also count for the character if the
  text includes them** ("Lysander and all friendly adjacent…"). Buffs for
  other units only don't count (Abaddon, Calgar, Thaddeus Noble).
- **Effects that hit adjacent enemies every turn** (Cezare, Mephiston,
  Godswyl, Typhus) count as `extra:1:melee`, because the melee target is
  adjacent.
- **Effects the character switches on with its own first attack** (Ahriman's
  Fire, Lhykhis's Web, Vitruvius's mark, Neurothrope's first Neuroparasite
  level) use scope `after`.
- **Things that build up** (per kill, per time attacked, per active used),
  **target-health conditions** ("at or below 50% health"), **regeneration at
  the start of the character's own turn**, **reactions** (counter-attacks,
  Overwatch shots) and **crit bonuses** (no gear) don't count.

Owner decisions (September 2026), recorded in each row's `Notes`:
- **Bodyguards count**, even though they're summons. Kell swaps in for Creed
  (`guard`: attackers get through Kell's health and Armour first). Geminae
  Superia takes Celestine's post-Armour damage (`heal`: two Geminae as extra
  health).
- **Uthar:** Hostile Acquisition for his attack, Fortify Takeover for his
  defence.
- **Varro:** Psychic Fortress only protects the units around him, so it
  doesn't count for him.
- **Tyrant Guard:** Guardian Organism is always on.

---

## Changing the setup

The constants at the top of `build_map.py`:

| Constant | Now | Meaning |
|---|---|---|
| `RANK` | `DIAMOND III` | The rank row used from the game data (`STONE I` … `ADAMANTINE II`, also `MYTHIC I`/`II` in the data) |
| `STARS` | `11` | Winged. Rank stats are stored at 0 stars; each star adds 10% (`STAR_MULT = 1 + 0.1 × STARS`) |
| `ABILITY_LEVELS` | `(36, 50)` | One "Ability level" button per level on the page (passives and actives) |
| `STANDARD` | `base_l36` | The scenario the Creed sparring line uses |
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
- **Controls:** Traits (always-on / all triggered), Ability level (36 / 50)
  and Active ability (off / on). Clicking a selected character again
  unselects them.
- **Scenario keys** in the data: `base` is the plain stat line (reference
  only). The others are `{base|trig}_l{level}` with passives on, plus `_a`
  when the active is on, e.g. `base_l36`, `trig_l50_a`.

---

## Gotchas

- **tacticustable.com data comes from one public address,** so no browser is
  needed: `https://api.tacticustable.com/game-info` (version at `/version`).
  - The website itself only renders in a browser. That's the gotcha in
    `../LRE Script/INSTRUCTIONS.md`, but that applies to the web pages, not
    this API.
  - Download it once per game version. It's a fan site, so don't hammer it.
- **Where tacticustable and the wiki disagree on stats or weapons,
  tacticustable has been right so far:** Lysander, Titus and Uthar, all
  confirmed by the owner in September 2026. Still flag new disagreements to
  the owner rather than assuming.
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
  turning the active on at ability level 36 barely moves the chart. That's
  correct, not a bug, and it's why both levels are offered.

---

## Changelog

| Date | Change |
|---|---|
| September 2026 | Owner answers: Kell and Geminae Superia count as bodyguards, Uthar split stance, Varro not counted, Tyrant Guard always on. New `guard` and `armourpass` tokens. The page's "Reading the chart" lists every trait in each setting and explains "typical character" |
| September 2026 | Passives added (`passive_abilities.csv`, always on; 41 characters counted, 5 owner questions). Controls are now Ability level + Active on/off. Actives re-checked. Clicking a selected character again unselects it |
| September 2026 | Defensive actives added (`Defence` column); owner answered the six OWNER rows |
| September 2026 | First version: `update_game_data.py`, `build_map.py`, `active_abilities.csv` (all 117 reviewed; 6 left for the owner), Attack/Defence/Map views, Active ability at level 36/50, alliance colours from the in-game icons |
