# Damage Visualiser — Plan

**Status:** the Roster Battle Map explorer is built and is meant to become the video graphic (the owner's call, September 2026). How to update it is in `INSTRUCTIONS.md`. Still to do: the video version (recording reveals, reference characters).

The goal is a simple on-screen graphic for DB Preacher Plays that shows
where a new character sits in Tacticus, for both attack and defence. It
replaces the old "damage against Castellan Creed" bar charts. The damage
rules behind it are in `DAMAGE_MODEL.md`.

---

## Decisions so far

| Topic | Decision |
|---|---|
| Comparison | Against the **whole roster**, not a single "Mr Average" (see Why below) |
| Setup | Winged D3, no equipment, no relics, flat ground |
| Abilities | **Passives always on** (owner). **Ability level: 36 / 50** and **Active ability: Off / On** switches, worked out from `passive_abilities.csv` and `active_abilities.csv`. The "Show the shift from the plain stat line" arrows cover what the ability arrows were for |
| Ability level | 36 at Legendary. Defensive abilities often cross a breakpoint at 36 (e.g. −30% → −33% damage reduction) |
| Situational traits | Two scores, owner's idea: **Always-on** (the trait rule) and **All triggered** (situational traits on, random ones at their average). Rapid Assault is off in Always-on (owner) |
| Views | **Attack** (damage only), **Defence** (toughness only) and **Map** (both), owner's idea. Switching animates the dots between views |
| Alliance colours | From the in-game alliance icons: Imperial gold, Chaos red, Xenos light blue (owner) |
| Reference characters | Long-standing characters that players already have a picture of (not recent releases like Nubari). Different characters for attack and defence |
| Data | Separate file `tacticus_stats.csv`. `tacticus_characters.csv` and `le_analysis.py` are untouched |
| Mythic | A later step: Mythic 14★ A2, level 60 abilities, relic effects |

### Why not one reference character

Tested on the real roster (September 2026):

- **Damage dealt *to* one ordinary character** ranks everyone almost exactly
  as the whole roster does (about 99% agreement), as long as the reference
  character has no defensive traits. Creed was a good target.
- **Damage taken *from* one character** is fragile. It depends on the
  reference character's damage type and hit count:
  - Against Creed's low-pierce Las attack, Kut Skoden jumps from 44th to
    7th toughest.
  - Bellator (Mk X Gravis) drops from 16th to 43rd.
  - Against a Psychic attacker, Nubari falls from 3rd to 65th.
- Measuring against the whole roster removes this.

---

## The two numbers

Both are counted in **attacks**, which is how viewers already think about
the game:

- **Damage** — how many of this character's attacks it takes to kill a
  typical enemy.
- **Toughness** — how many attacks a typical enemy needs to kill this
  character.

"Typical" is the middle (median) result across every playable character.
Machines of War and `Do_Not_Use` rows are excluded.

On screen: *"Kills a typical character in 3 attacks. It takes a typical
character 8 attacks to bring him down."*

---

## Scenes

1. **Damage line.** All characters appear as faint dots on one line. The
   damage reference characters and Creed are labelled. The new character
   drops in, then their ability arrow extends.
2. **Toughness line.** The same, with the tank reference characters.
3. **The map.** The two lines turn into the axes of a scatter plot, and the
   new character lands where they meet. The corners are labelled, e.g.
   glass cannon / juggernaut / tank / relies on kit.
4. **Creed sparring card (optional).** This keeps the old practical-test
   segment:
   - The new character's damage against Creed (melee, ranged).
   - What Creed does back.
   - How many hits each needs to kill the other.

   The numbers come from the model, so they're always there. After testing
   in the developer build, the owner can type in the in-game numbers and they
   replace the model's, with no other changes.

The icon on each dot shows whether the character's better attack is melee
or ranged.

Recording works like the LE template: 1920×1080, Space or click to
advance, Left arrow to go back, the same fonts and frame, and it runs as an
OBS browser source.

### Reference characters (shortlist, owner to pick)

Positions are from the stat-line model (rank out of 117).

| Scene | Top | Middle | Low |
|---|---|---|---|
| Damage | Kharn (#2), Jain Zar (#5) | Creed (#32), Abaddon (#58) | Ragnar (#104; his kit, not his stats, makes him a damage dealer, so a big arrow) |
| Toughness | Marneus Calgar (#2), Typhus (#5), Bellator (#16) | Tyrant Guard (#32, ability arrow), Creed (#67) | Varro (#110) or Celestine (#112) |

---

## Ability arrows

These were replaced by the roster-wide **Active ability** switch. The rules
are in `DAMAGE_MODEL.md` (Active abilities), and each character's handling
is in `active_abilities.csv`. For a video, the "Show the shift from the plain
stat line" arrows do the same job, and more clearly: the dot moves from the
stat line to where the kit puts the character. Defensive actives count
too (build step 5).

---

## Build steps

1. ~~`fetch_stats.py`~~ Done as `update_game_data.py` (download) and
   `build_map.py`, which writes `../LRE Script/tacticus_stats.csv`.
2. ~~`damage_model.py`~~ Done inside `build_map.py`, with the Creed check as
   `--creed`.
3. ~~Interactive explorer~~ Done: `roster-battle-map.html`, published
   privately.
4. **Video version:** 1920×1080, Space/click reveals like the LE template,
   featured character highlighted, reference characters labelled.
5. ~~Defensive actives~~ Done: the `Defence` column in `active_abilities.csv`.
6. **Later:** the Mythic view with relics.

---

## Open questions

- Pick the reference characters for each view, now that the explorer shows
  who is where.
- Which traits setting (or both) to show in videos.
- Places where tacticustable.com data disagrees with the game (owner to bring
  examples).
- Optional: 5–6 fresh Creed test numbers at the current patch, e.g. Jain
  Zar, Morvenn Vahl, one Terminator Armour character. They would confirm that
  the leftover mismatches are passives, not a model error.
