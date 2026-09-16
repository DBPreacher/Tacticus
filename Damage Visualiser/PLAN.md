# Damage Visualiser — Plan

**Status (September 2026): built.** The Roster Battle Map is the video graphic
(owner's decision). It's a private web page that zooms up to fill the screen,
recorded with screen capture for videos. How to update and use it is in
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
| Video | Record the normal page with screen capture, pressing the buttons on camera (owner). It zooms up to fill wide screens. An OBS broadcast mode was tried and removed |

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
   It writes `roster-battle-map.html` and
   `../LRE Script/tacticus_stats.csv`.
3. Reviewed data: `active_abilities.csv`, `passive_abilities.csv`,
   `relic_abilities.csv`. All 117 characters and 32 relics reviewed, and the
   owner's calls are recorded in their `Notes`.
4. `map_template.html`: the page.

Earlier ideas that were replaced:
- **Scripted video scenes** (damage line → toughness line → map) became the
  live Attack / Defence / Map views.
- **Ability arrows** became the Active switch, plus the "shift from the plain
  stat line" arrows.
- **A separate Mythic view** became the Progression switch.

---

## Ideas under discussion (September 2026)

- **Support Map (in progress).** Attack and Defence assessed separately, like
  the roster map. Owner decisions (September 2026): conditional buffs follow
  the Traits switch, support actives follow the Active switch, and the owner's
  old sheet is not to sway the choices. Proposed: "boost per ally" is the
  main score (doesn't depend on range); range only affects the team total,
  through a "Team spacing" switch (Typical: adjacent 2 allies, 2 hexes 3,
  team 4; Tight 3/4/4; Spread 1/2/4); single-target buffs always 1. Step 1
  done: `support_abilities.csv` (Attack side), all 22 owner questions
  answered (A-G, September 2026). Step 2 done: `support_model.py` works out
  each support's boost for every ally who benefits (per ally = the middle
  boost among allies it helps; team = per ally x allies reached). Findings:
  pierce buffs are strongest (Helbrecht's active, Nicodemus's active), then
  extra hits (Vitruvius, Thoread, Gulgortz) and extra attacks (Actus,
  Anuphet, Mephiston); flat Damage is modest (Calgar about +20%); small
  armour reductions barely matter at Diamond III because most attacks are
  already on their pierce floor. Owner decisions: buffs that only work
  against some enemies are scored across the whole roster, and the team
  figure assumes a team built for the buff. Step 3 done: `support-map.html`
  (Map, Ranking, For one; all tiers and settings; built in parallel by
  `build_support.py`). Next: the Defence side, on the same page with a Side switch (owner).
  Done (September 2026): Defence rows in `support_abilities.csv` (62,
  incl. every Healer/Mechanic heal action and Big Target, owner-reviewed),
  `run_defence` (Toughness boost), and the page's Attack / Defence switch
  with an Enemy focus switch (Focused default, Spread) and a 10-turn
  horizon. Finding: with Focused enemies, damage reduction and suppress
  lead (Thothmek, Darkstrider, Thoread, Uthar); with Spread, heal actions
  lead by a distance (Gibbascrapz, Vynn, Aleph-Null, Baldr, Nicodemus).
  Then (owner): a Whole character switch (Isabella's three rows add up to
  #9 on Defence, Tyrant Guard #10), and Aun'Shi's cycle fixed to a third in
  both settings (All triggered had put him #3 by counting -43% as always on).
- **Support value page, first notes** (owner's idea; notes in his "Boosting champions"
  sheet). Proposed method: measure each ally buff / enemy debuff with the
  same model, as how much faster each eligible ally kills a typical enemy,
  plus how many characters can use it and for how long. Worked example:
  Calgar at level 36 (+437 Damage to adjacent Imperials, +304 to others)
  gives Imperial allies a median +23% damage per attack; many-hit, low-pierce
  characters gain most (Titus +60%), high-pierce one-hitters least (Incisus,
  Vitruvius about +10%). Needs a reviewed `support_abilities.csv` and owner
  decisions (allies in range, buff duration, whether healing belongs here).
- **Teammate-powered damage:** Laviscus's Outrage (+120% of the highest hit a
  friend lands on an enemy next to him, +Crit Damage per Chaos friend) isn't
  counted. Alone he's 101st for damage at defaults; with one 1,500 hit from a
  Chaos friend he'd be about 15th; with 3,000 and two Chaos friends, 3rd.
- **Guild raid boss chart:** the game data has `guildBossSeasons`,
  `guildRaidUnits` and `bossDebuffs`, so damage per attack against each boss
  could be mapped, then best teams once support buffs exist.
- Cheaper views from data we already have: upgrade priority (who gains most
  from ability levels, gear, Mythic), faction strength, counters (who kills a
  given character fastest), and power creep over release dates.

## Guild Raid (built, September 2026)

`guild_raid.py`: the best 5 for a boss. A raid attack is 6 turns, 5 characters,
and the boss's own faction is banned. Rules read from the game data: 25 boss
fights per season (6 tiers, Common to Mythic, 27,000 up to 52.5M health), every
boss is **Immune** (no Armour/hits/Movement/Range reduction, no Stun, Suppress or
Taunt), bosses block, and two side battles apply a chain of debuffs (a switch:
mostly -30% Armour and -15% block chance).

Owner decisions: start with "best 5 for this boss", assume a full 6-turn run and
as much real support as possible, and a side-battle debuff switch. Terrain height
matters in the game but isn't modelled. Not counted yet: summons and bombs.

**The Machine of War slot** is counted. Every machine has a Mythic ability that
works on friendly Mythic characters, and it is worth far more than the machine's
own damage: the Biovore's Hyper Corrosive Acid is +20% damage taken from
anything a Spore Mine has hit, which is every attack the five make, so it wins
almost everywhere - exactly the machine the real teams bring. The Rukkatrukk's
version is melee-only and the Malleus Rocket Launcher's ranged-only; the
Reanimator and Z'Kar give +20% Damage to Mechanical and Psyker characters, which
is why a Mech team brings the Reanimator instead; the Plagueburst Crawler's
Blighted Land needs your characters to stand on the hexes it contaminates, so it
follows the All triggered switch. The other five are defensive. The boss's
faction is banned for machines too (so no Reanimator against Szarekh).

**Terrain is counted, as a switch.** The wiki's rule is +50% Damage for a unit
on high ground against one below it. Watching real runs, the two biggest hitters
take the high ground, so the switch gives it to the two who gain most - and the
model picks the same two the videos show (Laviscus and Kariyan). It was the last
third of the calibration gap.

How many stand on it barely matters: two, three or all five come out within 5%
of each other, because the damage is concentrated in one or two characters.
Owner (2026-09-16) watched a Szarekh run with three on high ground most of the
battle and five by the last round; the model's two-character version is 5% under
that run and 8% over the Mortarion one.

**The search is greedy:** it builds the five one at a time, then swaps each slot
for anything better until nothing improves. That finds the best five almost
always, but it can stop at a five where only changing two characters at once
would help - anchoring the Neurothrope against Szarekh beats the free search by
about 1.5%. If that starts to matter, seed the search from a second starting
five and keep the better run.

**Two things the first cut got wrong, found by the owner (2026-09-16) noticing
that Trajann and Kariyan never appeared:**
- The `Condition` column in `support_abilities.csv` says whether a row follows
  the Actives switch. It does *not* say the row is an active ability. Trajann's
  Legendary Commander is a passive that needs *someone* to have used an active
  this turn, which in a five-character team is every turn - it was being counted
  for two turns in six.
- A character gets its active off again whenever the cooldown allows, not once a
  battle: turn 1, then every `cooldownTurns + 1` turns.
- Kariyan's Legacy of Combat hits a **Big Target** with 1x Piercing instead of
  3x Power to everything adjacent, and every boss is a Big Target. That branch is
  worth about 2.7x the other one against Mortarion.
Both are counted now (owner, 2026-09-16): Kariyan's Martial Inspiration ramps
+33% for every turn he has already fought (so his turn-4 use is worth double),
and Laviscus gets +1,044 Crit Damage for every friendly Chaos character feeding
his Outrage, which is worth about +12% a Chaos ally on his own attack and needs
gear, because crits do.

**Only five actives come back.** Baraqiel (cooldown 1), Ramus (3), Aesoth (2),
Tyrith (2) and Kariyan (2) are the only characters whose active declares a
`cooldownTurns`; every other active is once a battle. The first cut let every
character re-use its active every third turn, which flattered everybody.

**Buffs only count while they are up.** A support ability that lasts the battle
counts for all six turns; one that lasts a round or two counts for that long,
and an active comes back whenever its cooldown allows (a 2-round buff on a
2-turn cooldown covers four of the six turns). Before this was counted, teams
of short-lived actives looked far better than they are.

`build_guild.py` builds **guild-raid.html** (https://claude.ai/artifact/UD8MrdUc4q5NfWPAnG8Ejz) from these numbers: every boss and
tier, every roster setting, the side battles on and off, with the five, the
machine, and the eight characters who came closest to making the team.

Each boss brings its own rules: Mortarion's Revoltingly Resilient (only the first
hit of an attack lands in full, each one after that half the last), Szarekh's
Noctilith Beacons (-40% from Psykers) and Obeisance Generators (-2 hits for
charging), the Lion's Emperor's Shield (his block chance climbs with each melee
hit). Laviscus's Outrage reads the team's biggest hits at face value, and the
Neurothrope's Neuroparasite and Norn Crown are counted. Xybia's Mind Control
isn't: it needs a Taunt to land and a Boss is immune to Taunt.

**`--deaths` (the boss killing your characters), in progress.** Off by default,
because the owner asked for a full 6-turn run. On, it reads what the boss puts
out in an enemy turn from its own abilities (Mortarion's Arch-Contaminator, the
Lion's Fealty and Martial Exemplar, each boss's normal attack), stands every
character that fights in melee next to it (a Big Target, so everything adjacent
is in range), shares the single-target attacks over that front line, counts the
character's own defensive passives and the team's Defence-side buffs, and stops a
character's damage on the turn it dies. Telegraphed attacks you can walk out of
(Szarekh's Annihilator Beam, the Lion's Instruments of Vengeance) and the summons
are left out.

It says: nobody dies to Szarekh, the Lion kills the front line around turn 4
(451k -> 336k for the owner's team), and **Mortarion kills everything next to him
on enemy turn 1** - Arch-Contaminator alone is 7 hits of ~2,000 Toxic plus a fifth
of the character's health, against Mythic characters with about 12,000 health.
That can't be what happens in a real run, and the likely reason is the boss's
GuildBossRunAway passive: the boss walks away from your team, so it isn't
adjacent to five characters at the start of each of its turns. Needs the owner:
in a real Mortarion run, how often does a melee character actually eat
Arch-Contaminator?

## Open questions

- **Havyr's passive: settled (owner, 2026-09-16) - count it as written.** Fury
  from the Dêlve adds a 2-hit Eviscerating attack after a normal attack against
  an enemy at or below 50% health, so it lands on every attack made once the
  target is already at or below half, and not on the attack that takes them
  there. `extrahalf:` in `passive_abilities.csv`, handled inside `kill_count`.
  His Damage goes from 2.37 to 2.28 attacks (Diamond III, ability 36, no gear).
  Against a Guild Raid boss it never fires, because your five only take a couple
  of per cent off the boss - unless the guild has already taken it below half,
  which the page doesn't offer a switch for (owner declined, 2026-09-16).

- Optional: 5–6 fresh Creed test numbers at the current patch (e.g. Jain Zar,
  Morvenn Vahl, one Terminator Armour character). They would confirm that the
  leftover mismatches in the Creed check are passives and old data, not a
  model error.
