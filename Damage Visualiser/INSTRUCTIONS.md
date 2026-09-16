# Damage Visualiser — Instructions

How to keep the **Roster Battle Map**, the **"typical character" graphic**,
the **Support Map** and the **Guild Raid page** up to date. It's written for the owner and for future
Claude sessions: follow it step by step, and you shouldn't need this
conversation's history.

| Page | Built by | Live link (private) |
|---|---|---|
| `roster-battle-map.html` | `build_map.py` | https://claude.ai/code/artifact/56e1db91-e3a8-45aa-ba58-0d2c9a8b84f8 |
| `typical-character.html` | `build_map.py` (same run) | https://claude.ai/artifact/SEssFu6qK5qQyXgUAmGjrz |
| `support-map.html` | `build_support.py` (after `build_map.py`) | https://claude.ai/artifact/MBWNzAY2cDkcJetmmCJp3y |
| `guild-raid.html` | `build_guild.py` (after `build_map.py`) | https://claude.ai/artifact/UD8MrdUc4q5NfWPAnG8Ejz |

Republish each to its own link after a rebuild (read it first with the
Artifact tool, then publish with `url`).

- **What it is:** an interactive chart of every playable character.
  - **Damage** = how many of their attacks it takes to kill a typical character (the middle result against the whole roster).
  - **Toughness** = how many attacks a typical character needs to kill them.
  - At Gold, Diamond III or Mythic, with or without standard gear, for the
    DB Preacher Plays channel.
  - It's a private web page, recorded with screen capture for videos (see
    "Recording it for a video").
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
| `passive_abilities.csv` | The same, for passive abilities: `Attack`, `Defence` and `Gear` tokens | **Yes** |
| `relic_abilities.csv` | One row per relic: its effect as `Attack` / `Defence` / `Gear` tokens (Mythic tier, gear on) | **Yes** |
| `support_abilities.csv` | One row per ability that helps allies attack (buffs) or weakens enemies (debuffs), for the Support Map. Reviewed by the owner (September 2026). See "Support Map" | **Yes** |
| `guild_raid.py` | **In progress.** The best 5 characters for a Guild Raid boss over its 6 turns, with team buffs and a side-battle debuff switch: `python -X utf8 guild_raid.py --boss "Belisarius" [--debuffs] [--gear] [--tier mythic] [--ability 60] [--anchor NAME] [--team "A,B,C,D,E"] [--deaths]`. It reads each boss's own rules (Mortarion's diminishing hits, Szarekh's -40% vs Psykers and -2 hits when charging, the Lion's block ramp), and counts Laviscus's Outrage, the Neurothrope's Neuroparasite and the Norn Crown. A Boss is Immune, so Armour reduction and Xybia's Mind Control are dropped. `--deaths` counts the boss killing your characters (in progress - see PLAN.md). See PLAN.md | Yes |
| `support_model.py` | Runs `support_abilities.csv` through the damage model: how much each buff helps every ally who can use it. `python -X utf8 support_model.py [--defence [--spread]] [--active] [--gear] [--trig] [--level 50]` prints the Diamond III rankings | Only to change the rules |
| `build_support.py` | Builds `support-map.html`: every tier and setting, both sides and both Enemy focus settings, in parallel (about 5 minutes on this PC). `--page-only` rebuilds just the page from the template with the last numbers (for design changes) | No |
| `support_template.html` | The Support Map's design (its CSS starts as a copy of `map_template.html`'s) | Yes, for design changes |
| `build_guild.py` | Builds `guild-raid.html`: the best five for every boss and tier at every setting, with the side battles on and off, in parallel (about 10 minutes on this PC). `--page-only` rebuilds just the page from the template | No |
| `guild_template.html` | The Guild Raid page's design | Yes, for design changes |
| `calc_data.py` | Everything the page's Calculate button needs: every character with its abilities already resolved to numbers, the buffs they hand each other, each boss twice (side battles cleared or not) with what every Machine of War does to it, and 50 exact scores from `guild_raid.py` for the page to check itself against. `build_guild.py` embeds it | Only to add something the model learned |
| `calc.js` | The arithmetic half of `guild_raid.py`, in JavaScript, so the page can score a five it has never seen. Run it under node against the check scores before trusting it (see "The Calculate button") | Yes, but only alongside the Python it mirrors |
| `guild-raid.html` | The built Guild Raid page | **Never.** It's overwritten |
| `support-map.html` | The built Support Map | **Never.** It's overwritten |
| `relic_owners.csv` | Which characters can equip each relic, read from the wiki by `update_game_data.py` | Only to fix a wiki mistake |
| `map_template.html` | The page design and code. `/*DATA*/` is replaced with the model output | Yes, for design changes |
| `roster-battle-map.html` | The built page that gets published | **Never.** It's overwritten on every build |
| `typical_template.html` | The "what is a typical character?" graphic's design; `build_map.py` fills it (see below) | Yes, for design changes |
| `typical-character.html` | That graphic, built | **Never.** It's overwritten |
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
python -X utf8 build_support.py
```

1. **`update_game_data.py`** prints the live and cached game versions. It only
   downloads when they differ; add `--force` to download anyway. After a
   download it also refreshes `relic_owners.csv` from the wiki. Use
   `--relics` to refresh only that, e.g. when a new relic's wiki page
   appears after the patch.
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
| Judh, Gear: Standard | Two Monstrous Boneswords + a Lash-Whip; damage about 2.4 attacks (about 19th) | Gear loading broke |
| Bellator, Progression: Mythic | 11,350 Health / 1,334 Damage / 1,735 Armour (the wiki's Mythic 14★ A2 values) | Tier settings broke |
| Every relic placed | The build warns if a relic has no owner in the roster | Check `relic_owners.csv` / the wiki page |
| Number of characters | Same as the non-MoW, non-Do_Not_Use rows in the CSV | A name didn't match; see the `ALIAS` warning |


---

## Guild Raid

`guild-raid.html` answers one question: **who are the best five against this
boss?** A raid attack is 6 turns with five characters and a Machine of War, and
the boss's own faction is banned.

- `guild_raid.py` is the model and a command line; `build_guild.py` runs it for
  every boss, tier and setting and writes the page.
- The page's switches are the Roster Battle Map's (roster tier, ability level,
  gear, All triggered, actives) plus **Side battles cleared**, which applies the
  two debuff chains to the boss (mostly -30% Armour, -15% block chance), and
  **High ground**, which gives the two characters who gain most +50% Damage
  (the wiki's terrain rule). Both are on by default, because that is what a real
  run looks like.
- The boss picker lists every fight a boss appears in, named the way the game
  names it: Mythic 1, Mythic 2 and Mythic 3 are three different fights (levels
  23, 24 and 25), not one Mythic tier. **A boss only appears in the slots its
  seasons give it** - Mortarion is Mythic 1 in the Lion El'Jonson season and
  Mythic 3 in his own, and he is never Mythic 2 - so the page names the season
  next to the slot. Where a boss has two fights with the same name in different
  seasons, the page adds the level.
- **Machine of War.** Every machine has a Mythic ability that works on friendly
  Mythic characters, and it is usually worth more than the machine's own damage:
  the Biovore's Hyper Corrosive Acid (+20% damage taken, anything a Spore Mine
  has hit), the Rukkatrukk's (melee only), the Malleus Rocket Launcher's (ranged
  only), the Reanimator's Guardian Construct and Z'Kar's Cabal of Sorcerers
  (+20% Damage for Mechanical or Psyker characters), the Plagueburst Crawler's
  Blighted Land (+20% Damage, but you have to stand on its contaminated hexes,
  so it follows the All triggered switch). The rest are defensive and do nothing
  for a damage run. **How often a machine fires**: each one has a single ability
  that costs a munition and one that is free, and a machine acts once a round, so
  the free one goes off most rounds and the munition one about once a fight. Its
  abilities take the rarity bonus like a character's - a Mythic machine doubles
  them. Anything that waits for the enemy to walk onto marked hexes is left out
  (the Rukkatrukk's Squig Mine, both of Galatian's).
  On damage alone the Biovore now wins for every team, including Mech, where real
  players bring the **Reanimator**. That is not a contradiction: the Reanimator
  repairs, and survivability is not modelled.
  The page brings the best machine for the five it picked, and
  the boss's faction is banned here too (the owner confirmed in game, September
  2026, that a banned-faction machine can't be brought).
  **+20% damage taken beats +20% Damage**, because Armour is taken off each hit
  before the multiplier: that is why the Rukkatrukk wins over the Plagueburst
  Crawler even though its version only works on normal melee attacks, and it is
  worth saying out loud on camera. A machine's **own** damage is a rough
  estimate - its damaging abilities at their cooldown, aimed at the boss - and it
  is small next to its Mythic ability either way. The Biovore's Spore Mines are
  Toxic, which only the ability text says, so `MOW_SHOTS` carries the type.
- **Boss rules** are read from each boss's own abilities: Mortarion's Revoltingly
  Resilient, Szarekh's Noctilith Beacons and Obeisance Generators, the Lion's
  Emperor's Shield. **The side battles weaken some of them**, which is what the
  chains in `bossDebuffs` say: Mortarion's two chains both carry
  `RevoltinglyResilient_hits_1`, so clearing both makes the first *three* hits of
  an attack land in full instead of one, and the Lion's carries
  `TheEmperorsShield`, which stops his block building up. The page shows whichever
  set of rules matches the switch. Most other steps in those chains weaken the
  boss's attacks or its summons, which this tool doesn't model - including
  Belisarius Cawl's `SelfRepairMechanism`, so his numbers assume you have cleared
  the side battles that stop him repairing himself. Magnus is the one Mythic boss
  whose chains take no Armour off at all. Laviscus's Outrage, the Neurothrope's Neuroparasite and the
  Norn Crown are counted; Xybia's Mind Control is not, because a Boss cannot be
  Taunted.
- **Not counted:** the boss killing your characters (`--deaths` on the command
  line, see PLAN.md), terrain height, bombs and summons.

### Calibration (September 2026)

The owner found videos of real runs and the model was scoring the teams people
actually play at about a third of what they do. It now lands inside 10%:

| Real run | The team | Real | The model |
|---|---|---:|---:|
| Mortarion Mythic 3 | Laviscus, Atlacoya, Boss Gulgortz, Trajann, Kariyan + Biovore | 1,632,137 and ~1,660,000 | 1,528,669 |
| Szarekh Mythic 2 | Aesoth, Boss Gulgortz, Trajann, Laviscus, Kariyan + Biovore | ~2,620,000 | 2,445,414 |

Mortarion with the side battles **not** cleared and Szarekh with them cleared -
`check_guild.py` prints both states and takes the closer one, because which side
battles a guild had done is not in the videos. Both at Mythic, ability 60,
standard gear, All triggered, High ground on. Worst miss: 7.9%. **Ability 60 is the game's maximum today** (owner, September
2026); 65 arrives with Adamantine III, so don't raise the tier until it does.

If the numbers drift again, the things that turned out to matter were: what
Laviscus's Outrage feeds on (the biggest *hit* of any kind, crits included), the
buffs that reach the hits a passive adds, Atlacoya's Direct damage, and terrain.
Check those first.

### What the Guild Raid work changed in the other pages

A Guild Raid is six fixed turns against something that cannot die, so several
things matter there that do not matter in a one-on-one fight. When a rule is
about the *character*, it belongs in `build_map.py` and reaches every page; when
it is about the *fight*, it stays in `guild_raid.py`.

| Learning | Where it lives | Does it change the Roster Battle Map or the Support Map? |
|---|---|---|
| Kariyan's Legacy of Combat has a Big Target branch (1x Piercing instead of 3x Power) | `passive_abilities.csv` as `extra:1|2:melee`, handled in `normal_attack` | **Yes** - 9 characters are Big Targets (Aesoth, Boss Gulgortz, Commander Farsight, Kut Skoden, Morvenn Vahl, Re'vas, Snappawrecka, Tyrant Guard, Volk) |
| Havyr's Fury from the Dêlve, counted as written | `extrahalf:` in `passive_abilities.csv`, handled in `kill_count` | **Yes** - 2.37 to 2.28 attacks |
| A character re-uses its active when its cooldown allows | `guild_raid.py` only | **No.** Measured: of 580 matchups on the map, one lasts long enough for a repeatable active to come back (median kill is under three attacks, an enemy turn is five) |
| Kariyan's active ramps with every turn he has fought | `guild_raid.py` only | **No** - it starts from turn 2 and a map kill is over inside turn 1 |
| Laviscus's +Crit Damage per Chaos ally | `guild_raid.py` only | **No** - it needs team-mates feeding his Outrage, and the map is one-on-one |
| A buff only counts for the turns it is up | `guild_raid.py` only | **No** - the Support Map measures a buff's boost to *one attack*, so how long it lasts isn't part of that question (the Defence side already handles round-only effects) |
| Boss rules, side-battle debuffs, the Machine of War slot, high ground | `guild_raid.py` only | **No** - there are no bosses, machines or terrain on the other pages |
| "+Damage taken" and "not a normal attack" buffs reach the hits a passive adds | `support_model.py`, so both pages | **Yes** - it makes those buffs worth more on the Support Map |
| Buffs land in a fixed order, so a team's score doesn't depend on the order its five are listed in | `support_model._tok_order`, so both pages | **Yes** - see below |

**The order buffs land in.** A buff that lifts damage only lifts the parts that
exist when it lands: "+60% damage taken" applied before a team-mate's extra
attack has been added misses that attack entirely. Buffs used to land in
whatever order the five happened to be listed in, so the same team scored up to
**35% differently depending on the order it was written down** - and the search
kept whichever order it built the team in. `support_model._tok_order` fixes the
order: everything that adds to the character's own attacks, then the
ability-scope multipliers on those, then what the enemy takes, flat before
percentages, the way a normal attack does it. Found by the page's Calculate
button disagreeing with the page's own precomputed five (September 2026).

The one finding worth saying on camera rather than coding: **+20% damage taken is
worth more than +20% Damage**, because Armour comes off every hit before the
multiplier.

To rebuild after a game update: `python -X utf8 build_map.py`, then
`python -X utf8 build_guild.py`, then republish the artifact.

### Changing the model without waiting half an hour

A full build is 81 fights x 48 settings x side battles x high ground, about
31,000 searched answers and half an hour. Don't run it while you are still
checking a change:

1. `python -X utf8 check_guild.py` - scores the real runs from the owner's
   videos against what they actually did. Half a second. If a change swings one
   of those, that is the change to look at.
2. `python -X utf8 build_guild.py --settings mythic:trig_l60_a_g` - rebuilds
   just the setting the videos use (about 80 seconds) and keeps the rest of the
   last build, so the page is right where you are looking.
3. The full `build_guild.py` once, when the model has settled.

(A job is a whole setting in a full build, so they spread over the cores; with
`--settings` there is nothing to spread, so jobs become chunks of three fights
instead - that is what turns 20 minutes into about a minute.)

**What the full build costs, and the levers.** Every model change makes each
search dearer, so re-measure rather than trusting an old figure. As of September
2026 it is about 28 minutes, after three things:

- each of a fight's four answers (side battles x high ground) seeds its search
  from the last one, because they nearly always land on the same five;
- "who else fits" tries each character in the five's weakest slot rather than all
  five slots, for the same list at a fifth of the cost;
- **Gold is not built at all** (`TIERS` at the top of `build_guild.py`). A Gold
  roster is not attacking a raid boss. Every tier dropped halves the build, so
  `TIERS = ['mythic']` takes it to about 14 minutes if Diamond III stops being
  useful too.

### The Calculate button

The page ships the best five for every boss, but "score *these* five" cannot be
precomputed: 117 characters make 138 million teams, and a team's damage does not
come apart into per-character pieces. Adding or multiplying per-character values
was measured at 39-113% out, so the page runs the model itself.

The split is: **Python resolves, JavaScript adds up.** `calc_data.py` exports
each character with its weapons, traits, gear, the effects of its passive, the
parts of its active and its summons - all already numbers at Mythic, abilities
60, standard gear, all triggered - plus the buff rows, the bosses and the
machines. `calc.js` is `guild_raid.py`'s arithmetic: `normalAttack`,
`openerDamage`, `memberDamage`, `outrage`, `summonDamage`, `teamTotal`,
`scoreTeam`. `build_guild.py` inlines both into the page.

The two have to agree, so `calc_data.py` also ships `N_VECTORS` exact scores for
random fives, and the page runs them before it shows a number. To check a change
headlessly (node is on this PC):

    python -c "import json,guild_raid as gr,calc_data as cd; g=gr.game();       open('calc.json','w').write(json.dumps(cd.build(g, gr.fights(g))))"
    node -e "const c=require('./calc.js'), D=c.load(require('./calc.json'));       console.log(c.check(D).length + ' of ' + D.vec.length + ' disagree')"

Raise `cd.N_VECTORS` to a few hundred for a real sweep - 400 fives take about
two seconds to score in Python and a third of a second in the browser. They
agree to 0.002%, which is the rounding in the export.

**Anything the model learns has to be taught twice.** If a change touches
`build_map.normal_attack`, `support_model.buffed` or the team maths in
`guild_raid.py`, mirror it in `calc.js` and re-run the sweep. Things the port
had to be told, all found this way: an active with no damage parts is still an
active; a buff's `who` is resolved against the character receiving it; Mind
Control needs a Taunt, so it is out against a Boss; an active can carry gear
effects of its own; a boss can take crit chance off its attackers; a melee swing
that also fires the ranged weapon; and a summon's weapon has a damage profile
that has to be read as one.

---

## Recording it for a video

Record the page itself with screen capture, pressing the buttons on camera
(owner's choice, September 2026; the separate OBS broadcast mode was tried and
removed).

- **It fills the screen.** On a window wider than 1440 pixels the page lays
  itself out at 1440 and zooms up, as big as the window allows while the
  header and the whole chart stay on screen (`fitPage()` in the template).
  - Use the browser's full screen (**F11**) so the chart gets the full
    height. At 2560×1440 full screen it zooms about 1.7 times.
  - The layout is chart | character card | controls, side by side, so the
    buttons you click and the card they change are both on screen. A long
    card scrolls inside its own panel (it jumps back to the top when you pin
    someone new).
  - The alliance chips and the melee/ranged key sit under the chart, so
    they're always in shot.
  - Below 1440 pixels wide it's the normal page, with no zoom.
- **Fonts** come from Google Fonts, so the PC needs internet access.
  Without it the page falls back to standard fonts.
- Open the local file `Damage Visualiser/roster-battle-map.html`, or the live
  page above. After a rebuild, refresh the page.

---

## The "typical character" graphic

`typical-character.html` explains what "a typical character" means, for
videos. `build_map.py` writes it in the same run as the map: `run_scenarios`
keeps every scenario's full matchup table (117 × 117, attacks × 100) and
`write_typical` puts them all in the page (about 5 MB), so it has **the same
switches as the map**: Progression, Traits, Ability level, Gear and Active.
The page shows one character's 117 answers as bars.

- **Three steps, as buttons to press on camera:** 1 · Every answer (roster
  order), 2 · Line them up (quickest to slowest), 3 · Pick the middle (the
  59th answer is highlighted, with the two halves bracketed).
- **Damage / Toughness:** the character attacking everyone, or everyone
  attacking them. The middle answers are exactly the map's Damage and
  Toughness for every character and setting (checked: 5,616 of 5,616).
- **Character** picker: opens on Kharn, any character works.
- **The bar scale stops at 4× the middle answer,** so one freak matchup
  (Ammuk against Uthar is over 4,000 attacks) can't flatten every other bar;
  the end label then says "off the scale".
- It's a fixed 1600×900 stage zoomed to fit the window, so it fills any
  screen. Hover a bar for that matchup.
- **Live page (private):** https://claude.ai/code/artifact/cc647bac-9f07-40ac-af58-ce3572c44933
  (republish `typical-character.html` to it the same way as the map).

---

## Support Map

`support-map.html` shows how much each support helps its allies, on two
sides picked by the **Attack / Defence** switch at the top.
**Live page (private):** https://claude.ai/artifact/MBWNzAY2cDkcJetmmCJp3y
(republish `support-map.html` to it the same way as the map).

- **The numbers** (`support_model.py`): for each ally who can use a buff,
  their Damage score (the middle of their 117 matchups) with and without it,
  at the same settings as the Roster Battle Map. **Boost** = how much faster
  they kill a typical character (k without / k with − 1).
  - **Boost per ally** = the middle boost among the allies it helps (a boost
    over 0.5%). **Allies helped** = how many of the other characters.
  - **Team boost** = boost per ally × allies reached in a turn: the Reach
    column and the **Team spacing** switch (Typical: adjacent 2, 2 hexes 3;
    Tight 3/4; Spread 1/2; team and target 4; one ally and next attack 1).
    It assumes a team built to use the buff (owner).
  - A buff that only works against some enemies (`vs=`) is scored across the
    whole roster: its boost against them × the share of the roster they are
    (owner). The panel also shows the full figure.
  - +Damage buffs work on normal attacks, like the map's own passives; enemy
    debuffs and `ability` buffs also reach the ally's active. The support
    never buffs itself here. Conditional parts follow Traits, actives the
    Active switch, relics Mythic with gear.
- **Defence side** (`support_model.run_defence`): for each ally a Defence row
  protects, their Toughness (the middle of the 117 attackers' attacks to
  kill them) with and without it. **Protection** = k with / k without − 1.
  Heals, shields and heals-after-each-hit use an optional `regen` in
  `build_map.kill_count` (the roster map never passes it). Owner decisions:
  - **Enemy focus** switch (Defence only): Focused = 5 enemy attacks a turn
    on one ally (the roster map's rule, the default) or Spread = 2. Heals
    between turns only land if the ally survives a turn, so they look
    narrow when Focused and dominant when Spread.
  - Counting stops after **10 enemy turns** (`HORIZON_TURNS`); those allies
    show a "+" ("10+ turns").
  - Supports that cost health (Nicodemus's Blood Chalice) score below zero:
    in the Ranking and card, not on the map (log scale).
- **Each ability / Whole character** switch (header, owner, September 2026):
  whole character adds up a support's rows on that side. Team = the sum of
  the rows' team figures; per ally = the sum of their per-ally figures (a
  typical ally getting all of it); across = team ÷ per ally (between 1 and
  4, so the team curves still hold); "can use it" = allies any row helps.
  Worked out in the page from the row numbers, so nothing extra is built.
- **The page**: Map (boost or protection per ally up, log scale), Ranking (team)
  and For one (the best supports for one character). The Map's **Across**
  switch (above the chart): **Allies reached** (default: 1-4 teammates a
  turn from Reach and Team spacing, dots spread sideways in each column,
  dashed curves of equal team boost) or **Can use it** (how many of the
  other characters it helps: the roster-building view; owner's choice,
  September 2026).
  a support card (numbers, who it helps most, what it gives at this level,
  the notes and game text) and a table. Same switches as the map, plus Team
  spacing. The Active switch starts **on** here, since many supports are
  actives.
- **Findings (September 2026, Diamond III):** pierce buffs are strongest
  (Helbrecht's and Nicodemus's actives), then extra hits (Vitruvius,
  Thoread, Gulgortz) and extra attacks (Actus, Anuphet, Mephiston); flat
  Damage is modest (Calgar about +20%); small armour reductions barely
  matter, because most attacks against a typical enemy are already on
  their pierce floor.

### Support abilities

`support_abilities.csv` is the data, one row per ability and side. `Side` is
**Attack** (abilities that make allies hit harder, or make an enemy take
more) or **Defence** (heals, shields, revives, damage reduction, armour,
blocks, and weakening or suppressing enemies; drafted September 2026, not
used by the page yet). `Source` is Passive, Active, Relic or **Trait**:
every Healer and Mechanic gets a Heal / Repair action row (their Damage x
their most hits, on one ally every turn, from the game's trait text), and
every Big Target a row for its trait (adjacent allies take one hit fewer
from ranged attacks). New characters need
a row adding by hand (the build doesn't draft support rows yet).

Columns:

| Column | Meaning |
|---|---|
| `Name`, `Source`, `Ability` | The support, and whether it's their Passive, Active or Relic (Mythic only) |
| `Effect` | Tokens, `;`-separated (below). Empty = considered but not counted (the note says why) |
| `Receives` | Who can get it: `all`, an alliance, a faction, a trait (e.g. `TerminatorArmour`), `has:ranged` or `no:ranged`; `|` means "or" |
| `Reach` | `adjacent`, `2 hexes`, `team` (every friendly unit), `one` (one ally), `target` (everyone attacking the enemy it's on), `next attack` |
| `Lasts` | For the reader: battle, turn, 2 rounds, next attack… |
| `Condition` | `always`, `trig` (All triggered only) or `active` (Active switch on) |
| `Values_D3` | What the tokens come to at Diamond III, ability levels 36 and 50 (relics: Mythic). Written by the draft, for checking; don't edit |
| `Needs_Review`, `Notes` | As in the other files; `OWNER:` marks a question for the owner |
| `Ability_Text` | The game's text |

Effect tokens, `kind:value[:scope][:option=value…][@trig]`. Values are
game-data variable names, so they follow the ability level and rarity.

- **Ally buffs:** `flat` (+Damage a hit), `pct` (+% damage), `hits` (extra
  hits), `pierce` (+% pierce), `critchance`, `critdmg`, `armignore` (ignore
  Armour), `ramp` (each hit +X more than the last), `extra:1xType(min-max)`
  (an extra hit of that type), `attack` (an extra normal attack at X% of the
  ally's Damage), `follow` (a free ranged attack after melee), `reuse` (the
  ally uses their active again), `partner:NxType(min-max)` (the support's own
  hits, set off by each ally attack), `dmgfromblock` (a share of the ally's
  Block Damage as Damage).
- **Enemy debuffs:** `armour` (enemy Armour lowered), `taken` (enemy takes
  +X Damage a hit), `takenpct` (enemy takes +X% damage).
- **Scopes:** `all`, `melee`, `ranged`, `normal`, `normal-melee`,
  `normal-ranged`, `ability` (attacks that aren't normal attacks).
- **Options:** `who=` (only these allies; `!` = everyone else), `vs=` (only
  against enemies with this trait), `type=` / `notype=` (the ally's damage
  type), `cap=` (maximum per hit), `reach=` (for the reader: the team figure uses the row's Reach),
  `chance=` (a % chance), `trig=` (a different value with All triggered),
  `trigmult=`, `mult=`, `avg=` (a share of the value in both settings, for a
  buff that cycles, e.g. Aun'Shi's one round in three; owner, September 2026), `gearonly` (only helps
  allies who already have a crit chance).
- `@trig` on a token: that part only counts with All triggered.
- **Defence tokens** use the same grammar as the Defence column of the other
  ability files (`pct`, `epct`, `flat`, `hitsless`, `pctcap`, `armour`,
  `armourpass`, `heal`, `setpct`, `suppress:one|all`; scopes `melee`,
  `ranged`, `one` = the first attack of each enemy turn, `psychic`), plus:
  `blockchance`, `blockdmg` (an added block, gear or not), `regen` (health
  every enemy turn), `regenhit` (health after each attack), `shield` (a
  shield every turn), `revive` (extra health once, owner decision),
  `revivepct` (a share of the ally's own health, once), `healdmg:pct(min-max)`
  (a share of an ability's damage as health). `healaction` = the support's
  Damage x their most hits. `vs=` on a Defence token means the attacker.
  Owner decisions (September 2026): heals that repeat count every enemy turn;
  revives count as extra health once; suppress, stun and -damage count as
  weaker enemy attacks (a Suppressed enemy deals 30% less, Stunned 50% less,
  as on the roster map); area effects cover the enemy turn, single-target
  ones one attack.

---

## Adding a new character

1. Add them to `../LRE Script/tacticus_characters.csv` first, using the
   normal LE workflow in `../LRE Script/INSTRUCTIONS.md`. Leave
   `Do_Not_Use=Y` until they're released.
2. Wait until tacticustable.com has them: `update_game_data.py` reports the new
   version.
3. Run `build_map.py`. It drafts their `active_abilities.csv` and `passive_abilities.csv` rows. Review them
   against the rules below, then build again and republish.
4. **Support Map:** add their rows to `support_abilities.csv` by hand (the
   build doesn't draft them): an Attack row for anything that makes allies
   hit harder or enemies take more, and a Defence row for anything that
   heals, shields, revives, reduces damage or weakens enemies. If they have
   the Healer, Mechanic or Big Target trait, add the matching Trait row
   (copy another character's). Flag judgement calls with `OWNER:`. Then run
   `build_support.py` and republish.

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
  the start of the character's own turn** and **reactions** (counter-attacks,
  Overwatch shots) don't count. **Crit and block bonuses** go in the `Gear`
  column (only used with Gear: Standard).

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

## The `Gear` column (both ability files)

Crit and block effects of a kit only count with **Gear: Standard**, because
without gear nobody can crit or block. They go in the `Gear` column, with
the same token format as the other columns:

| Token | Meaning | Example |
|---|---|---|
| `critchance:VAR[:scope]` | +VAR% crit chance | Ragnar's active `critchance:extraCritChance:melee` |
| `critdmg:VAR[:scope]` | +VAR Crit Damage | Titus `critdmg:extraCritDmg` |
| `critdmgpct:VAR` | +VAR% Crit Damage | Ulf `critdmgpct:25` (Ice) |
| `alwayscrit` | Every hit crits (active only) | Titus |
| `dmgfromblock:VAR` | +VAR% of its own Block Damage as Damage | Lysander's passive `dmgfromblock:chance` |
| `blockchance:VAR` / `blockdmg:VAR` | Its own block improves | Trajann `blockchance:blockChance;blockdmg:blockDmg` |
| `critreduce:CHANCE/DMG` | Attackers get −CHANCE% crit chance and −DMG Crit Damage | Dreir `critreduce:critChanceReduction/critDmgReduction` |

- An active's `Gear` effects only apply on the turn it's used (offence) or
  for its one round (defence).
- A passive's `Gear` effects apply all the time. `@trig` works as usual.
- **Not counted:** conditional crit bonuses (Judh per free hex, Tarvakh
  against targets at or below 50% health), and bonuses for allies only.
  Abilities marked "cannot Crit" are detected from their text automatically.

## `relic_abilities.csv`: relic effects

One row per relic (not per character: shared relics apply to all their
owners). Columns: `Relic`, `Owners` (refreshed each build), `Attack`,
`Defence`, `Gear`, `Needs_Review`, `Notes`, `Ability_Text`. The tokens are
the same as for passives, and values are read at relic level 10
(`RELIC_LEVEL`) with no rarity multiplier. The review rules are the
passives' rules.

Relic-only token features:
- `armpct:VAR` (target Armour −VAR%, for Contamination).
- `critextra:PART` in `Gear` (extra hits only when the attack crits;
  Maugetar).
- `vs` filters can name an alliance, e.g. `:vsChaos|Xenos` for the Relic
  Bolt Pistol.

## Changing the setup

**Progression tiers** are the `TIERS` list at the top of `build_map.py`.
Each tier sets rank, stars, rarity multiplier, the two ability levels,
standard gear rarity and whether relics apply. `set_tier()` applies one, and
the build loops over all of them (about 25 seconds). Add or change a tier
there; the page picks it up automatically.

The other constants at the top of `build_map.py`:

| Constant | Now | Meaning |
|---|---|---|
| `RELIC_LEVEL` | `10` | Relic effect level (max) |
| `ATTACKS_PER_TURN` | `5` | One enemy turn = a full team attacking |

Inside a tier: the rank row name (`GOLD I`, `DIAMOND III`, `MYTHIC II` =
Adamantine II); stars (rank stats are stored at 0 stars, and each star adds
10%); the rarity multiplier, which applies only to ability variables listed
in `variablesAffectedByRarityBonus`; the gear rarity (each item at its top
level); and the Creed sparring scenario (`base_l{first level}`).

The **Mythic tier** is built in (September 2026).

## Changing the page

- Edit **`map_template.html` only**, then run `build_map.py`. Never edit
  `roster-battle-map.html`.
- **Filling the screen** is `fitPage()` at the end of the script and the
  `.wrap.fit` CSS: above 1440 pixels wide the page is laid out at 1440 and
  zoomed with CSS `zoom`. The tooltip divides by that zoom when it positions
  itself. The chart is 1000×670 so that at 2560×1440 full screen the page
  fills the whole width with the header and chart on screen.
- **Layout:** `.main` is a three-column grid (chart, 316px character card,
  232px controls). The two side panels use `contain: size` so they take the
  chart's height instead of stretching it, and scroll inside if longer.
  Below 1280px wide they stack under the chart. "Reading the chart" sits
  under the main row in three text columns.
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
- **Attack / Defence views** keep the measured axis exact and spread the dots across the other one, each dot reserving room for its name (`spread()` in the template). About 100 of 117 names fit in Attack and all of them in Defence; the rest show on hover.
- **Views:**
  - **Map** is the scatter plot.
  - **Attack** keeps the damage axis and spreads the dots sideways, so they
    don't overlap.
  - **Defence** does the same for toughness.
- **Controls:** Progression (Gold / Diamond III / Mythic), Traits
  (always-on / all triggered), Ability level (the tier's two levels), Gear
  (none / standard) and Active ability (off / on). Clicking a selected
  character again unselects them.
- **Page data** is nested by tier: `c.t[tier].s[key]`, plus each tier's
  stats, gear, ability texts and relic text.
- **Scenario keys** in the data: `base` is the plain stat line (reference
  only). The others are `{base|trig}_l{level}` with passives on, plus `_a`
  when the active is on and `_g` with standard gear, e.g. `base_l36`,
  `trig_l50_a_g`.
- **`tacticus_stats.csv`** has one row per character per tier. Its columns
  use `lv1`/`lv2` for the tier's two ability levels, e.g.
  `Damage_base_lv1_g`, with `Ability_Level_1/2` giving the actual levels.

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
  September 2024, not the first hit.
- **One enemy turn = 5 attacks** (`ATTACKS_PER_TURN`). An active's defensive
  effects cover only the first 5 attacks. Passives cover every attack.
  Terminator Armour and other "first attack each turn" effects come back
  every 5 attacks. If an active's `Defence` has a round-long effect, the page
  notes it for that character automatically.
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
| September 2026 | Support Map: Each ability / Whole character switch; Aun'Shi's cycle counts a third in both settings (it read as always on with All triggered) |
| September 2026 | Support Map Defence side: Attack / Defence switch, Enemy focus (Focused / Spread), heal actions from the Healer and Mechanic traits, 10-turn horizon, compact data |
| September 2026 | Support Map: Across switch, allies reached (default, with team-boost curves) or can use it; `build_support.py --page-only` |
| September 2026 | Support Map (Attack side): `support_model.py`, `build_support.py`, `support-map.html`. Owner decisions: enemy-specific buffs scored across the roster, team boost assumes a team built for the buff |
| September 2026 | `support_abilities.csv` drafted: Attack-side support for the planned Support Map (55 abilities counted, 22 owner questions) |
| September 2026 | The typical-character page gets the map's switches (Progression, Traits, Ability level, Gear, Active); `build_map.py` now writes it and `build_typical.py` is gone |
| September 2026 | `build_typical.py` and `typical-character.html`: the "what is a typical character?" graphic (one character's 117 answers, lined up, middle picked out) |
| September 2026 | OBS broadcast mode removed (owner prefers to record the normal page and press the buttons on camera). The page now zooms up to fill wide screens. Layout is chart | character card | controls side by side (owner), with the alliance and melee/ranged key under the chart ("Ranged is their best attack") and "Reading the chart" below; the chart is 1000×670 |
| September 2026 | Broadcast mode for OBS (1920×1080 stage scaling to any 16:9 size, keyboard shortcuts, URL settings, `roster-battle-map-obs.html`); Attack/Defence views spread so most names fit; no reference characters (owner) |
| September 2026 | Progression tiers (Gold / Diamond III / Mythic), relics at Mythic (`relic_owners.csv` from the wiki, `relic_abilities.csv` reviewed), long-format `tacticus_stats.csv` |
| September 2026 | Gear switch (standard Legendary loadouts, crits/blocks at their average) and the `Gear` column |
| September 2026 | One enemy turn = 5 attacks (`ATTACKS_PER_TURN`); round-limited actives noted on the page |
| September 2026 | Owner answers: Kell and Geminae Superia count as bodyguards, Uthar split stance, Varro not counted, Tyrant Guard always on. New `guard` and `armourpass` tokens. The page's "Reading the chart" lists every trait in each setting and explains "typical character" |
| September 2026 | Passives added (`passive_abilities.csv`, always on; 41 characters counted, 5 owner questions). Controls are now Ability level + Active on/off. Actives re-checked. Clicking a selected character again unselects it |
| September 2026 | Defensive actives added (`Defence` column); owner answered the six OWNER rows |
| September 2026 | First version: `update_game_data.py`, `build_map.py`, `active_abilities.csv` (all 117 reviewed; 6 left for the owner), Attack/Defence/Map views, Active ability at level 36/50, alliance colours from the in-game icons |
