# Damage Visualiser — Plan

**Status (September 2026): built.** The Roster Battle Map is the video graphic
(owner's decision). It runs as a private web page for exploring, and as an OBS
browser source for recording (broadcast mode). How to update and use it is in
`INSTRUCTIONS.md`; the damage rules are in `DAMAGE_MODEL.md`.

The goal was a simple on-screen graphic for DB Preacher Plays that shows where
a character sits in Tacticus, for both attack and defence. It replaces the old
"damage against Castellan Creed" bar charts.

---

## Decisions

| Topic | Decision |
|---|---|
| Comparison | Against the **whole roster**, not a single "Mr Average" (see Why below) |
| The two numbers | **Damage**: attacks needed to kill a typical character. **Toughness**: attacks a typical character needs to kill them. "Typical" = the middle result against every playable character (Machines of War and `Do_Not_Use` rows excluded) |
| Progression | **Gold / Diamond III / Mythic** switch (owner). Gold = Epic 8★ Gold I, abilities 26/35, Epic gear. Diamond III = Legendary, Winged, abilities 36/50, Legendary gear. Mythic = 14★ Adamantine II, abilities 50/60, Mythic gear + relic at level 10. Every character can be Mythic |
| Ability level | Two levels per tier. At Diamond III, 36 is the video standard: defensive abilities step up at 36 (e.g. Thoread 31% → 33%) |
| Abilities | **Passives always on** (owner). **Active ability: Off / On** switch. Worked out from `passive_abilities.csv`, `active_abilities.csv` and, at Mythic, `relic_abilities.csv` |
| Gear | **None / Standard** switch (owner): standard = the best items of the tier's rarity at top level, boosters included |
| Situational traits | Two settings, owner's idea: **Always-on** (the trait rule) and **All triggered**. Rapid Assault is off in Always-on (owner) |
| Views | **Attack**, **Defence** and **Map** (owner's idea). Attack/Defence spread the dots so most names fit |
| Alliance colours | From the in-game alliance icons: Imperial gold, Chaos red, Xenos light blue (owner) |
| Reference characters | **None** (owner): the charts work as they are |
| Enemy turn | 5 attacks (a full team). An active's one-round protection only covers those 5 (owner, after the Aesoth case) |
| Data | Separate file `LRE Script/tacticus_stats.csv` (one row per character per tier). `tacticus_characters.csv` and `le_analysis.py` are untouched |
| Video | Broadcast mode for OBS: a 1920×1080 stage that scales to the browser source size (1080p, 1440p or 4K), keyboard shortcuts, and URL settings for each scene |

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

The Creed test lives on in the detail panel's **Sparring Creed** line, and as
the model check (`build_map.py --creed`).

---

## How it was built

1. `update_game_data.py`: the game data from tacticustable.com (only
   downloaded when the version changes), plus relic owners from the wiki.
2. `build_map.py`: the model, run for every tier and switch combination.
   It writes `roster-battle-map.html`, `roster-battle-map-obs.html` and
   `../LRE Script/tacticus_stats.csv`.
3. Reviewed data: `active_abilities.csv`, `passive_abilities.csv`,
   `relic_abilities.csv`. All 117 characters and 32 relics reviewed, and the
   owner's calls are recorded in their `Notes`.
4. `map_template.html`: the page (explorer and broadcast mode).

Earlier ideas that were replaced:
- **Scripted video scenes** (damage line → toughness line → map) became the
  live Attack / Defence / Map views.
- **Ability arrows** became the Active switch, plus the "shift from the plain
  stat line" arrows.
- **A separate Mythic view** became the Progression switch.

---

## Open questions

- Optional: 5–6 fresh Creed test numbers at the current patch (e.g. Jain Zar,
  Morvenn Vahl, one Terminator Armour character). They would confirm that the
  leftover mismatches in the Creed check are passives and old data, not a
  model error.
