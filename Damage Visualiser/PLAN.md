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
- **A "this one ramps" note in the character panel** (owner, 2026-09-16 - not
  built yet, just parked). Build-up effects are not counted, so a character
  who grows through a battle is charted as he is on turn 1. Titus is the
  extreme: Fuelled by Fury gives +84.6 Damage for every active a friendly
  character has used this battle, so he reads 91st for Damage at 0 stacks,
  25th at 8 and 9th at 12 - realistic for a five-turn fight with four allies.
  23 passives and about a dozen actives have a component left out for this
  reason (Kharn, Ragnar, Haarken, Shiron, Macer, Tanksmasha, Wrask and the
  rest). Proposal: flag the ones whose rank would move by more than ~20
  places over a battle and say so in the pinned panel - no assumed stack
  counts, no model change, nothing arbitrary to decide.
  Worth knowing while this is open: the model already handles build-up three
  different ways - zero (Titus and most), an assumed midpoint (Blessings of
  Khorne at 4 of 8 stacks, All triggered only) and one stack (Kimm's Modified
  Exoarmour, from the second attack on). That split is by trait vs ability,
  not by principle.

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

## Video idea: the chart shows the floor, not the ceiling (owner, 2026-09-16)

Came out of three community questions in a row that were all really the same
question. Every conditional in the model is pinned at its worst case, on
purpose, because the alternative is inventing a battle and a team. That is the
right rule - but it means a whole category of character reads low, and they are
all characters who reward playing them properly. The episode is "who is this
chart most unfair to, and why that is the point".

The cast, with the numbers already worked out (Diamond III, all triggered,
gear on):

- **Titus** - Fuelled by Fury, +84.6 Damage per ally active used this battle,
  counted as zero. Damage 91st at no stacks, 25th at 8, 9th at 12. Realistic
  for a five-turn fight with four allies. The largest single gap in the roster.
- **Forcas** - +20% Damage per adjacent unit (counted as one, the target he is
  hitting) and +135/+400 Damage per adjacent Dark Angel (counted as zero).
  Alone he is 54th at level 36 and 75th at level 50; surrounded by four Dark
  Angels and five enemies he is **3rd at either level**.
- **Laviscus** - Outrage, teammate-powered; see the note above. 101st alone.
- **Wrask** - the shield he only gets after a melee kill or a Deep Strike
  arrival, which is why he reads tougher than Angrax on the median while losing
  105 of 117 individual matchups.
- **Lucien, as the counterpoint.** He is the one the chart is hardest on and
  most right about: Black Rage sets him to 50% Health, so with Active: On he is
  **dead last of 53 Imperials** (1.27) and 116th of 117 overall, while sitting
  10th-12th for Damage. Active: Off puts him 17th of 53 and 47th overall. It is
  not a bug and he is not being double-counted - his active is used against 112
  of the 117 defenders, so he really is paying for what he gets. The purest
  glass cannon in the game, and a good way to end on "the chart is doing its
  job".

Pairs naturally with the parked "this one ramps" note in Ideas above; widen
that note to cover positional conditions (Forcas) as well as build-up over a
battle (Titus), because they look identical to a viewer.

## Video idea: the best and worst factions (owner, 2026-09-16)

Every faction ranked on both axes at once - who actually has the best roster,
rather than the best single character. The page already has a faction filter,
so it can be driven live on camera.

First pass (Diamond III, all triggered, abilities 36, active on, standard gear;
each faction's **median rank** among the 117, so lower is better):

| Faction | n | Attack | Toughness | Combined |
|---|---|---|---|---|
| Adeptus Astartes | 3 | 14 | 27 | 20.5 |
| Adeptus Custodes | 5 | 53 | 15 | 29.0 |
| Leagues of Votann | 5 | 25 | 44 | 29.5 |
| Black Legion | 5 | 33 | 37 | 38.5 |
| Black Templars | 5 | 65 | 12 | 38.5 |
| ... | | | | |
| Adepta Sororitas | 5 | 85 | 74 | 79.0 |
| Adeptus Mechanicus | 5 | 87 | 70 | 79.5 |
| Genestealer Cults | 5 | 66 | 110 | 91.5 |

The story is in the splits, not the combined column:

- **Black Templars 65th attack / 12th toughness** and **Death Guard 97th / 21st**
  are the anvils - they do not kill anyone, nobody kills them.
- **Aeldari 33rd / 94th** and **Thousand Sons 45th / 100th** are the opposite:
  hit hard, fold.
- **Genestealer Cults, 110th for toughness**, are the worst defensive faction in
  the game by a distance. Good hook for the bottom of the episode.
- By alliance: Xenos have the best attack (median 56) and the worst defence
  (76); Imperials are the most balanced (58/49); Chaos sit behind on attack (68)
  with defence in the middle (54).

Caveats before recording: Adeptus Astartes is only 3 characters, so its top spot
is a small-sample artefact - either say so or set the cut at 5. The numbers are
one scenario; check Always-on too, because factions built on triggered kit
(World Eaters, Black Legion) move. And the median-vs-matchups caveat from the
Wrask discussion applies to faction medians just as much.

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

## The sweep: the same bugs, on every other character (September 2026)

Calibrating against the owner's videos turned up six *kinds* of mistake, not six
mistakes. Each one was found on one character and then turned out to apply to
several. The sweep below is the to-do list: work through it and check each
against the ability text, the way Kariyan's and Atlacoya's were.

| The kind of thing | Found on | Swept (September 2026) |
|---|---|---|
| An active that keeps giving for the rest of the battle | Abaddon (`extra:A1:after`) | **Godswyl** done: his after-moving attack was counted, his -653 Armour was not. **Haarken** and **Lucien** need kills or charging, so nothing to count. **Havyr**'s is on his active, which the token grammar can't reach yet |
| A different attack against a Big Target | Kariyan (`extra:1\|2`) | nothing else found |
| An ability that grows with each turn its owner has fought | Kariyan (`RAMP`) | nothing else found |
| An ability that grows with each use | Atlacoya (`RAMP_FLAT`) | **Titus** done (`RAMP_TEAM`): +148 on everything he does for each active the team has used, worth +1,480 a round by the end. **Shiron** done (`RAMP_STACK`): +196 a turn to a cap of 6. **Snappawrecka** needs repairs, **Wrask** needs to be attacked, **Kîmm** needs to charge |
| A damage type that changes with the target or the team | Atlacoya (`DIRECT`) | Farsight's is already right |
| Hits that scale with what the team has done | Sekhetar (`PSYCHIC_HITS`) | **Ahriman** needs Fire hexes and **Adamatar** needs kills. Adamatar's other half, the +718 enemies take from ranged attacks, was already a support row |

Two things the sweep settled that are worth keeping in mind. First, the ability
CSVs were in better shape than a keyword scan suggests: Adamatar and Godswyl's
extra attack were already handled, and the scan only flagged them because it
cannot read the Notes column properly. Second, a character's own Armour
reduction is no good against a **Boss** - they are Immune - so `member_damage`
strips `armignore` and `armpct` from a character's own passive in a raid, while
the Roster Battle Map keeps them.

Titus's and Shiron's ramps are Guild Raid only. They build over six rounds, and
a one-on-one kill on the map is over in two to five attacks.

Two more, from the same hunt, that are about the model rather than one character:

- **A character gets its own buff.** Anything that lands on the enemy helps the
  one who cast it; an ally buff skips its caster only when the text says "other
  friendly". This was worth about 15% on a real team.
- **"The first attack that is not a normal attack"** is the attack a passive adds
  on any round where nobody uses an active, not the active itself.

Run `python -X utf8 check_guild.py` after each one. It scores the owner's real
runs in half a second, and every fix above should move those numbers toward the
video, not away.

## The Biovore (September 2026)

The owner's round-by-round had it doing 42,825 where the model said 19,013. Two
things, and the per-mine damage was not one of them:

- **A Machine of War takes the rarity bonus.** Its abilities are rarity-boosted
  in the data exactly like a character's, and a Mythic machine doubles them. The
  model was building its parts with the boss helper, which deliberately skips the
  bonus - right for a boss, which is not a unit you levelled, wrong for a machine.
  A Spore Mine went from 3,948 to 7,896, which matches the 6,128-8,300 a mine on
  screen.
- **Bio-Minefield sends three mines at once.** The machine acts once a round: most
  rounds it launches one mine, and when Bio-Minefield is off cooldown it gathers
  every mine on the board and sends them in. Over five fighting rounds that is
  four launches and one Bio-Minefield, about seven mines - the video's count.

It now reads 44,290 against 42,825.

## What is left (September 2026, after the calibration)

All three of the owner's real runs land 6-8% under (worst miss 7.9% after the
buff-order fix). The model is short of something, not over-counting. Most of the
original candidate list has since been ruled out by the owner, so what remains is
below - and after item 1 the list is thin, which is itself the finding:

1. **Summons - counted now (September 2026).** Every ability with a `summonDmg`
   and a `unitId` puts its npc on the board and attacks for the rest of the
   fight: Boss Gulgortz's Ork Boyz, the Patermine's Genestealers, Anuphet's
   Scarabs, Marshal Dreir's Death Riders, Re'vas's Shield Drones. The Norn Crown
   names friendly Summons, so it lifts them too. It was worth about +0.6% on the
   Mortarion runs, which is less than hoped - the gap is mostly elsewhere. What
   is still uncounted: summons that arrive from something other than a
   `summonDmg` variable, and anything a summon does besides attack.
2. **Bombs: not a candidate (owner, 2026-09-16).** They don't count towards the
   raid score in game.
3. **Overwatch: not a candidate (owner, 2026-09-16).** Nobody uses it.
4. **The other ten Machines of War: a much smaller worry than it looked.** Across
   the whole build the model only ever picks two of the eleven - the **Biovore**,
   the one checked against a video, or the **Rukkatrukk** when the Biovore is
   banned (Tyranid bosses, 31 of the 81 fights). The other nine never win
   anywhere. Where both are allowed and the Rukkatrukk still wins, it wins by a
   hair: on Szarekh Mythic 2 with the side battles cleared it is 2,445,414
   against 2,441,722, 0.15%, because its +20% is melee-only and every other
   machine's third place is 14% back. So what rests on a guess is narrow: how
   often the Rukkatrukk fires, and only against Tyranid bosses. The owner reports
   that in game it is mostly the Biovore that gets picked, which is what the
   model does wherever it is allowed and the fight is not a coin-flip.

Smaller, and structural rather than numeric:

- **Havyr's active** takes 653 Armour off for the rest of the battle. The `A`
  prefix on a token can read an active's numbers, but only for `extra:`; this
  needs the same for `armignore:`.
- ~~**The search is greedy**~~ - **settled (September 2026): there is no search.**
  `brute_all.js` scores every possible five, 2,092,558,347 of them, in about two
  hours, and the page publishes the winners. The greedy search it replaced was
  already optimal on 7 of the 14 fights and up to 9.2% short on the rest.
- **Xybia: settled (owner, 2026-09-16) - she does not work on a boss.** Proved in
  game: Mind Control needs the Taunt to land and a Boss cannot be Taunted. The
  model already drops it, so nothing to change.

And the things that would need the board simulated, which this tool does not try
to do: the partial second round, positioning, and terrain beyond the high-ground
switch.

**Where the remaining 6-8% is most likely to be.** With bombs, Overwatch, Xybia
and the machines struck off, the leading candidate is **round 1**. The model
gives it zero: `MOVING = 1`, so only five of the six rounds fight. The owner's
words were "we barely get any damage in round 1" - and *barely any* is not
*none*.

Measured, by scoring each calibration team over six fighting rounds instead of
five and asking how much of that extra round the gap is worth:

| Run | Model, 5 rounds | Real | Short by | A 6th round is worth | The gap is |
|---|---:|---:|---:|---:|---:|
| Mortarion M3 | 1,528,669 | 1,632,137 | 103,468 (+6.8%) | 316,823 | **0.33 of a round** |
| Szarekh M2 | 2,445,414 | 2,620,000 | 174,586 (+7.1%) | 458,665 | **0.38 of a round** |

Two different bosses, two different teams, and both want about a third of a
round. That is the signature of one missing partial round rather than scattered
per-character errors - if the model were wrong about characters, the two runs
would not agree this closely.

The caveat: a *sixth* round is the model's strongest (every ramp at maximum),
while round 1 would be its weakest (no buffs up, no stacks). So in round-1 terms
the gap is worth more than a third of a round - closer to half the team getting
a swing in, which is more than "barely any". So either round 1 gives more than it
looks like on camera, or a few per cent of the gap is somewhere else.

**Not changed without the owner's say-so**, because `MOVING` sets every number on
the page and the "damage in 5 fighting rounds" line under the total. The question
to answer from a video: in round 1, does anyone actually swing?

After that it is luck and terrain: two or three runs is a small sample for crit
and block chains, and the model only knows about terrain through the high-ground
switch.

## The Calculate button (September 2026)

The page's five are the best the search could find. "Score the five *I* picked"
is a different problem: 117 characters make 138 million teams, so it cannot be
precomputed, and it cannot be composed either - per-character values added came
out 39-56% low and multiplied 29-113% out on Laviscus teams, because Outrage and
the buffs compound.

**Settled: the page runs the model.** Python resolves every ability to numbers
(`calc_data.py`), JavaScript does the arithmetic (`calc.js`), and 50 exact
scores from `guild_raid.py` ship with the page so it can prove the two agree
before it shows a number. A five scores in about 4 ms, which includes trying all
eleven Machines of War the way the model picks one.

The calculator is fixed at the setting the videos use - Mythic, abilities 60,
standard gear, all triggered, actives on - and follows the page's boss, side
battles and high-ground switches. Offering every setting would mean shipping
every setting's resolved roster; if that is ever wanted, `calc_data.SETTING`
becomes a list and the page picks one.

The port had to be taught six things the Python already knew (listed in
INSTRUCTIONS.md, "The Calculate button"). Every one of them was a real rule the
JS was silently missing, which is the argument for keeping the check scores: a
model change that is not mirrored shows up as a failing vector, not as a wrong
number on camera.

## A buff was counted twice on the character casting it (September 2026)

Found because the owner asked why Ragnar was out-damaging Laviscus on
Ghazghkull. It was not his active repeating - he has no `cooldownTurns`, so it
fires once. It was that his Saga of the Warrior Born was written down twice:

- `passive_abilities.csv` records what an ability does **for its owner**
  (`hits:extraHits:melee`, and `critdmg` in the Gear column);
- `support_abilities.csv` records what the same ability does **for everyone
  else** (`hits:extraHits:melee:who=Space Wolves`, `critdmg:...`).

`helps_itself()` then handed the caster the support row as well, so Ragnar got
+3 hits from his passive and +3 hits again from his own support row, and the
same for his Crit Damage. Nine characters were affected - and three of them were
the most-picked characters on the whole page: Ragnar in 89.5% of the best fives,
Lhykhis 83.3%, Vitruvius 66.0%.

| Character | Ability | Counted twice |
|---|---|---|
| Ragnar | Saga of the Warrior Born | +hits, +Crit Damage |
| Ragnar | War Howl | +crit chance |
| Vitruvius | Master Annihilator | +hits |
| Lhykhis | Whispering Web | ramp |
| Ahriman | Psychic Stalk | +%, +Damage |
| Lysander | Icon of Obstinacy | +Damage, damage from block |
| High Marshal Helbrecht | Destroy The Witch | +Damage |
| Uthar | Grim Efficiency | Armour ignored |
| Commander Farsight | Way of the Short Blade | follow-up attack |

**The rule now:** `own_side_kinds()` reads both ability files, and `buffs_for`
drops a self-token whose kind the character already gets from its own copy of
that ability. The other sixteen self-helping rows are untouched, because their
ability file entry is the active's *damage parts*, not the buff - Roswitha's
Brazier, Boss Gulgortz's Waaagh!, Haarken, Havyr, Yazaghor, Cyrus, Snappawrecka,
Godswyl.

What it costs, and it is worth writing down: for an **active**, the ability
file's Gear entry only applies on the turn the active goes off, while the
support row carries the buff for its full duration. Dropping the token there
means Ragnar's War Howl crit chance now lasts one turn instead of two. That is a
small undercount, taken deliberately over a larger overcount.

On Ghazghkull Mythic 2 the old best five falls 20.8%: Ragnar -34.8%, Vitruvius
-57.4%, Lhykhis -17.8%, Laviscus -4.6% (his Outrage feeds on their hits). The
calibration runs do not move at all - none of the nine is in the owner's teams -
which is the sign that the fix is aimed at the right thing.

## A conditional debuff applied to every enemy (September 2026)

Found in the same sitting, by asking why Roswitha kept turning up. Her Brazier of
Holy Fire is "+60% damage taken" **against Daemons**, and `support_model.buffed`
was applying it to everything.

The reason is structural. `buffed()` runs before the enemy is known, so a
"+damage taken" token is folded straight into the character's numbers. For the
normal attack that is fine - the condition rides along on the effect and
`_applies` settles it later - but the same branch also bumps the **ability parts
and the hits a passive adds**, and that bump ignored the condition. Kariyan's
Legacy of Combat is exactly such a part, so on Ghazghkull - an Ork, no Daemon
anywhere - his attack read 86,392 instead of 59,672. 45% of thin air.

Two rows were affected, and both matter: Roswitha (vs Daemon) and **Atlacoya (vs
Psyker), who is in the owner's own team**. On Mortarion, a Psyker and a Daemon,
both conditions are true, which is why the calibration runs never showed it.

**The rule now:** a conditional "+damage taken" hangs the condition on the part
(`mods`), and `build_map.mods_for` settles it against the enemy actually in front
of it - flat first, then percentages, like everywhere else. Ghazghkull now reads
the same with Roswitha on the team as without; Mortarion still gets the full
+60%. `support_model.buffed` also stops outright if a conditional token ever
turns up on an ability scope, which no row needs today and which would leak the
same way.

## The sweep for other double counts (September 2026)

After Ragnar, the owner asked whether there were more. The sweep looked at every
way the same effect could be recorded twice, and found two more:

| Checked | Result |
|---|---|
| A support row's self-token against the character's own ability file | **9 characters** - fixed, see above |
| A conditional debuff applied to every enemy | **2 rows** - fixed, see above |
| Variables `guild_raid.py` reads directly (the ramps, Outrage, the parasite) against the same character's CSV rows | **1: the Neurothrope** |
| `helps_itself` handing a whole row to its caster when only half of it lands on the enemy | **1: Commander Farsight** |
| The same ability written twice in `support_abilities.csv` | none |
| An ability that is both a passive and an active | none |
| A trait the model hardcodes that is also written as a token | none |
| Relic rows on the support side | none - `buffs_for` skips `Source = Relic` outright |

**The Neurothrope.** `passive_abilities.csv` counts one Neuroparasite level
(`flat:extraDmg:after`), which is all the Roster Battle Map can know, while
`member_extra` counts the parasite at its cap. He was getting cap + 1 levels.
`MODEL_OWN` now names the kinds the Guild Raid model works out for itself, and
`guild_unit()` takes the character's own copy out. That helper also does the
Immune Armour-reduction strip, which `member_damage` did and `biggest_hit`
did not - so a character's own Armour reduction used to inflate what it fed
Laviscus's Outrage against a Boss.

**Commander Farsight.** His Way of the Short Blade does two things: *other*
friendly characters' ranged attacks ignore Armour and hit harder, and he and
other T'au perform a free ranged attack after a melee one. `helps_itself()`
judged the whole row at once, and because `armignore` was on the debuff list it
returned "yes, it helps him too" - so he handed himself a buff his own ability
text gives to *other* characters. `armignore` is off that list now ("your attacks
ignore X Armour" is a buff on the attacker, not something on the enemy), and
`helps_itself` judges one token at a time.

**Counted now (September 2026):** a relic that buffs allies used to reach nobody,
because `buffs_for` skipped every `Source = Relic` row. It no longer does -
`relic_live()` checks that the character is actually carrying that relic and that
the setting has one (Mythic, gear on), and the row then behaves like any other
buff, reach and duration included. Two relics do this on the Attack side:

- **Norn Crown** (Neurothrope): +1,308 Damage to other Psykers within Synapse
  range. It was already written out by hand inside `parasite()`, which gave it to
  *every* Psyker on the team with no reach limit and no All-triggered gate. That
  copy is gone; the row is the authority now, so it reaches the three biggest
  hitters and only with All triggered. `summon_damage` keeps its own copy,
  because summons are not team members and no support row can describe them.
- **Chalice of Baal** (Nicodemus): +728 Damage on normal melee attacks to the two
  biggest hitters next to him. Worth knowing before it goes on camera: it only
  fires after a unit next to Nicodemus dies, so it rides on the All triggered
  switch, and in a raid where your five are not dying that is generous. He is
  still nowhere near worth a slot - swapping him for Boss Gulgortz on Mortarion
  is 1,319,702 against 1,528,669.

## Open questions

### How far do these buffs actually reach? (owner testing in game, September 2026)

Six Attack rows carry a **per-token reach** that `buffs_for` never reads - it only
ever uses the row-level `Reach` column. The owner is settling these by playing
them rather than by reading the ability text, so the model is deliberately left
alone until then. What to watch for, and what the model currently assumes:

| Ability | The text says | The model gives it to | If the text is right |
|---|---|---|---|
| **Commander Shadowsun**, Defender of the Greater Good | non-Tau allies adjacent, **Tau allies at 2 hexes** | 2 allies either way | 3 allies for a Tau team - **undercounted** |
| **Darkstrider**, Structural Analyser | the same split | 2 allies | 3 for a Tau team - **undercounted** |
| **Boss Gulgortz**, Waaagh! | **the whole team** | 2 allies | 4 allies - **undercounted, the biggest of the six** |
| **Aun'Shi**, Serene Unifier | 2 hexes | 2 allies | 3 allies - undercounted |
| **Asmodai**, Exemplar of Hate | **one** ally | 4 allies | 1 ally - **overcounted** |
| **Haarken Worldclaimer**, Herald of the Apocalypse | next attack | the same | no change |

The test in game is the same each time: put the buffed character at each distance
from the caster and see whether the buff icon appears. For Boss Gulgortz, whether
every character on the team gets the Waaagh! or only the two beside him.

Why it matters beyond the numbers: **Shadowsun, Darkstrider and Boss Gulgortz are
in the proven five on 8 of the 14 fights**, so if the text is right, those teams
are stronger than the page says and the order behind them may change. Fixing it
means re-running `brute_all.js` (about two hours), so it is worth doing once, with
the answers in hand, rather than twice.

A reminder of what "proven" does and doesn't cover: `brute_all.js` proves no other
five scores higher **according to the model**. It removes search error, not model
error. This is model error, and it is the kind only the game can settle.



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
