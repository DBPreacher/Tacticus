# Damage Model — Rules Record

This is the record of exactly what the damage visualiser counts and what it
leaves out, and why. When a result looks odd, or a trait gets reworked,
check this file first. The design and build plan is in `PLAN.md`.

---

## Standard setup

The page has a **Progression** switch with three tiers (owner, September
2026). Every character in a tier is compared under the same conditions, and
each tier is compared within itself:

| Tier | Rarity (ability ×) | Rank | Stars | Ability levels | Standard gear |
|---|---|---|---|---|---|
| Gold | Epic (×1.6) | Gold I | 8 | 26 / 35 | Epic items, top level (9) |
| Diamond III | Legendary (×1.8) | Diamond III | 11 (Winged) | 36 / 50 | Legendary items, top level (11) |
| Mythic | Mythic (×2.0) | Adamantine II (`MYTHIC II` in the data) | 14 | 50 / 60 | Mythic items, top level (10), **plus the character's relic at level 10** |

The table below describes the Diamond III tier, the original video
standard. The other tiers differ only as in the table above.
Check: Bellator at Mythic comes out at 11,350 Health / 1,334 Damage / 1,735
Armour, exactly the wiki's Mythic 14★ Adamantine II values.

Every character is compared under the same conditions:

| Setting | Value |
|---|---|
| Rank | Diamond III |
| Stars | Winged (Legendary star) = 11 stars = ×2.1 on the 0-star rank stats |
| Abilities | Level 36 (video standard) and level 50 (Legendary cap), Legendary rarity. Only used in the "Active ability" scenarios |
| Equipment | A switch: **None**, or **Standard**: the best Legendary items at top level for the character's own slots, boosters included (owner) |
| Relics | None (a Mythic + relics view is a later, separate step) |
| Terrain | Flat ground, no hex effects, no buffs or debuffs |
| Damage roll | Middle of the ±20% range, which is what the Creed test numbers show |

Rank and stars multiply Health, Armour and Damage by the same factor for
every character. So the **basic-attack** comparison doesn't change at any
rank, as long as everyone is at the same rank. Rank only matters once
ability arrows are added, because ability damage doesn't scale with stars
or rank.

---

## Core formula (per hit)

```
hit      = max(Damage − Armour, Damage × Pierce)
Mk X Gravis target: hit = max(hit − Armour, hit × Pierce)   (second pass uses the reduced value)
attack   = hit × hits × multipliers
```

- Pierce comes from the weapon's damage type (tacticustable weapon data):
  Physical 1%, Las 10%, Blast/Projectile 15%, Bolter/Chain/Pulse 20%,
  Flame 25%, Bio/Energy 30%, Particle 35%, Power 40%, Eviscerating 50%,
  Heavy Round 55%, Molecular 60%, Plasma 65%, Toxic 70%, Melta 75%,
  Piercing 80%, Psychic/Direct 100%.
- A character's attack is the better of its melee and ranged attack
  against each target.
- Damage types with a built-in rule: Melta +50% against Vehicles (counted).
  Psychic can't be blocked (no blocks in this model anyway).

---

## The trait rule

> **Count a trait only if it is always on for that matchup.** It may
> depend only on who is attacking whom and with which weapon.
> **Leave it off** if it depends on movement, turn order, position or
> terrain, kills or deaths, allies, or a random roll.

Traits that are left off are talked about on camera, not charted.

### Counted

| Trait | Effect in the model |
|---|---|
| Terminator Armour | First attack each turn against it: −75% on every hit of that attack. Psychic and Direct hits excluded. (Changed from "first hit" to "first attack" in September 2024.) In the Toughness number, only the first enemy attack each turn is reduced |
| Mk X Gravis | Incoming damage goes through armour twice (see formula). The game skips this on crits, but there are no crits here |
| Parry | Incoming melee multi-hit attacks −1 hit (min 1) |
| Terrifying | −30% damage from melee attacks. It does nothing against ranged attacks, and each attacker picks its better weapon *after* it applies, so it often just pushes them into shooting instead. Across its 11 holders it is worth an effective −25% (−20% Atlacoya to −31% Azkor), not −30%. Jain Zar's melee reduction is not this trait: it is her passive, Terror's Lament |
| Martial Ka'tah | Normal attacks against it deal −20% |
| Camouflage | Ranged attacks against it −1 hit (min 1). The −2 at range 3+ and −3 in Tall Grass are left off (position and terrain) |
| Beast Slayer | +20% melee damage against Big Targets and Vehicles. Its block chance is left off (random) |

### Left off: depends on what happens in the battle

| Trait | Why it's off | Creed test numbers |
|---|---|---|
| Rapid Assault | Only the first attack of each battle. **Owner decision, September 2026** | **Included** +25% |
| Heavy Weapon | Only if it hasn't moved this turn | Not included |
| Crushing Strike | Only if it hasn't moved this turn | Not included |
| Ranged Specialist | Only if it didn't start its turn adjacent to an enemy | **Included** +33% (Sho'Syl) |
| Prioritised Efficiency | +25% dealt / −25% taken, lost after moving 3+ hexes | No data |
| Contagions of Nurgle | Aura, position-based, grows over rounds | Not included (Typhus, Corrodius, Rotbone) |
| Weaver of Fate | Needs 3+ enemies to have taken Psychic damage that turn | Not included |
| Blessings of Khorne | Builds up with melee kills | — |
| Act of Faith | Builds up with Imperial deaths and kills; needs a crit item | — |
| Thrill Seekers | Crit chance only; no crits without gear | — |
| Shadow in the Warp | Only against enemy Psykers within 2 hexes | — |

### Left off: random

| Trait | Effect |
|---|---|
| Daemon | Extra 25% chance to block up to 50% of its own Damage |
| Get Stuck In | 30% chance of an extra hit per 2 hits (100% with enough allies adjacent) |
| Let the Galaxy Burn | 33% chance of an extra hit (guaranteed on a hex with an effect) |

### No effect on a normal attack or the kill count

These affect things outside a normal attack: survival, what happens on
death, healing between turns, movement, or allies.

Resilient, Final Vengeance, Ambush, Explodes, Putrid Explosion,
Living Metal (heals between turns), Healer, Mechanic, Mechanical,
Psyker (splash onto a different enemy), Suppressive Fire (weakens the
enemy afterwards), Overwatch, Infiltrate, Deep Strike, Flying, Unstoppable,
Indirect Fire, Synapse, Big Target (protects allies; only matters as a
Beast Slayer / Melta target), Vehicle (only matters as a Melta / Beast
Slayer target).

Not on any current character: Diminutive, Dakka, Instinctive Behaviour.

---

## Gear

With **Gear: Standard**, every character gets its own item slots (fixed
per character in the game data) filled with the best **Legendary** item it
can equip (faction rules apply), at the item's **top level (11)**,
boosters included (owner). Relics are never used.

- **Which item:** crit and block items trade chance against damage (e.g.
  35% / 1,024 against 20% / 1,808), so the highest chance is used, because
  it keeps chains going across multi-hit attacks. Defensive items: Health +
  Armour where the faction allows it, otherwise Armour only (Votann's
  Greaves).
- **Two crit items** (Calandis, Judh, Tarvakh):
  chance = 1 − (1 − c₁)(1 − c₂), plus the booster (wiki `HDTW_TwoCrit`).
- **Defensive items** add Health and Armour directly. They don't scale with
  stars or rank.
- **Crits** count at their average, using the wiki's chain rule: the chain
  starts on hit 1 and each later hit re-rolls until one fails. A crit adds
  Crit Damage **before** armour and **skips Mk X Gravis**. That's why
  Gravis tanks (Bellator, Nubari) lose toughness with gear on. Ability hits
  crit too, unless the ability "cannot Crit".
- **Blocks** count at their average with the same chain rule. They come
  last, after every other modifier. Psychic can't be blocked.
- **Crit and block parts of kits** are in the `Gear` column of both ability
  files and only count with gear on:
  - Titus always crits.
  - Ragnar, Shiron and Laviscus get +crit chance; Ulf's Ice gives +25% Crit
    Damage.
  - Trajann, Uthar, Lysander and Arjac gain block chance or Block
    Damage; Lysander's Damage also grows with his block value.
  - Marshal Dreir reduces attackers' crits.
  - Maugan Ra and Ragnar's charge get crit bonuses with Traits: All
    triggered.
- **Traits with gear, when triggered:** Act of Faith at one stack (+10%
  crit chance, +25% Crit Damage) and Thrill Seekers (+15%).

Biggest effects at level 36: Judh (111th → 19th for damage) and Calandis
(85th → 31st), who both have two crit items. Psychic attackers such as
Mephiston (32nd → 4th) gain a lot, because every point of Crit Damage gets
through. Bellator (9th → 37th for toughness) and Nubari (3rd → 14th) lose
the most, because crits skip Mk X Gravis.

## Relics (Mythic tier)

Every character can go Mythic. The 65 characters with a relic (32 relics,
19 unique and 13 shared) get it at level 10 when **Gear: Standard** is on.

- **Who owns which relic** comes from the wiki's relic pages
  (`relic_owners.csv`, written by `update_game_data.py`). The game data
  doesn't say.
- **The relic's item stats** replace the standard Mythic item in its slot.
  If the character has no slot of exactly that type, it takes the nearest
  one, e.g. Aethana's Phoenix Gem (a block booster) takes her booster slot.
- **Relic values have no rarity multiplier.** Talon of Horus at level 1 is
  exactly the wiki's 1,175–1,565.
- **The relic's effect** works like a passive (always on), reviewed in
  `relic_abilities.csv` with the same Attack / Defence / Gear tokens and the
  same rules. 13 relic effects count, for example:
  - Relic Bolt Pistol: melee pierce and ranged Crit Damage, doubled vs Chaos
    or Xenos.
  - Paragon Spear: Tyrith's start-of-turn attack.
  - Lakrimae and Orbs of Decay: Contamination, −30% target Armour.
  - Maugetar: a Direct hit on crits, triggered only.
  - Monster Slayer of Caliban: +Damage vs Big Targets and a block.
  - Phoenix Gem: a revive.

  19 don't count: they need kills, summons, allies or other targets (e.g.
  Talon of Horus only hits enemies next to the target).

## Turns: one enemy turn = 5 attacks

Toughness counts the attacks a typical character needs to kill, assuming a
**full enemy team of 5 focuses on the character**. So one enemy turn is 5
attacks (`ATTACKS_PER_TURN` in `build_map.py`; owner, September 2026).

- **An active's protection lasts one round**, so it only covers attacks 1–5,
  then wears off: damage reduction, flat reduction, suppress or stun on
  nearby enemies. This matters for Aesoth, Thoread, Azkor, Calandis, Dante,
  Darkstrider, Deathleaper, Hascule and Thothmek, and the page notes it.
  - Before this rule, Aesoth's −66% let him soak 14.6 attacks, more than a
    team can make in a turn. Now it's 8.3.
- **A single-target stun or suppress** from an active only weakens attack 1.
- **"First attack each turn" effects come back every 5 attacks** (attacks 1,
  6, 11 …): Terminator Armour, Thothmek's Timesplinter Mantle, Judh's cap.
- **Passive protection works on every attack.** Extra health (heals,
  revives, bodyguards) is used up once.
- Kill counts are worked out attack by attack. A fraction means the last
  attack was only partly needed.

## Scenarios

The page offers eight combinations of three switches, plus the plain stat line as a reference:

| Switch | Options |
|---|---|
| Traits | **Always-on** (the rule above) or **All triggered**: every situational trait's condition met, random traits at their average, Blessings of Khorne at 4 of 8 kills |
| Ability level | **36** or **50**, for passives (always on) and the active |
| Active ability | **Off** or **On** (open with it) |

"All triggered" assumes each trait's condition is met:

- Rapid Assault +25%; Heavy Weapon +25% ranged; Crushing Strike +50% melee;
  Ranged Specialist +33% ranged.
- Prioritised Efficiency +25% dealt / −25% taken.
- Weaver of Fates: maximum damage roll, i.e. ×1.2 before armour.
- Contagions of Nurgle: −20% target armour on melee attacks.
- Blessings of Khorne +12% dealt and −32% Psychic taken.
- Shadow in the Warp −25% Psychic from Psykers.
- Camouflage −2 hits against range 3+ weapons.
- Random traits at their average:
  - Get Stuck In: +0.3 hits per 2 hits.
  - Let the Galaxy Burn: +0.33 hits.
  - Daemon: a 25% block chain of 50% of its Damage.
  - Beast Slayer: a 10% block chain of its Armour.

## Passive abilities

Passives are **always on** in every view except the plain stat line, which
is only a reference. They use the chosen ability level (36 or 50).

- A passive counts if it adds to the **character's own normal attacks** or
  **protects the character itself**. For example:
  - extra hits after each attack: Kharn, Re'vas, Gulgortz, Lucien
  - +Damage or +%: Lysander, Forcas, Nubari
  - a follow-up ranged attack: Commander Farsight
  - damage or hits taken off attackers: Jain Zar, Thothmek
  - extra Armour: Gibbascrapz
- **Not counted:**
  - buffs for other units only
  - summons, reactions and counter-attacks
  - effects that build up, and target-health conditions
  - regeneration at the start of the character's own turn
  - crit and block bonuses without gear (with Gear: Standard they count; see Gear)
- **Bodyguards count** (owner): Kell takes the hits for Creed with his own
  health and Armour. Geminae Superia takes Celestine's post-Armour damage, so
  two of them count as extra health.
- **Uthar** uses Hostile Acquisition (ignores Armour) for his attack and
  Fortify Takeover (an extra Armour pass) for his defence (owner).
- **Movement conditions:** passives that need charging or moving (Kut
  Skoden, Deathleaper, Ragnar, Tanksmasha) only count with **Traits: All
  triggered**.
- **How each character's passive is counted** is in `passive_abilities.csv`
  (41 characters). The token formats and rules are in `INSTRUCTIONS.md`.

## Active abilities

Every character is assumed to **open with their active ability**, then
carry on with normal attacks. The active is only used if that kills faster
than normal attacks alone.

- **One target, first use only.** Damage to other enemies doesn't count.
  Neither do persistent effects after the first use.
- **Summons never count**, the same rule as the LE CSV's `Has_[DamageType]`
  columns.
- **Conditional extras don't count:** "+X for each…", "if the target is…",
  chance-based hits.
- "Does not end the turn" means the character also makes a normal attack that
  turn.
- **Ability damage** uses the middle of the ability's own damage range, times
  the rarity multiplier (Legendary ×1.8).
  - It goes through armour, pierce, Mk X Gravis and Terminator Armour
    (−75% on the first attack of the turn).
  - Trait bonuses and Parry, Terrifying, Martial Ka'tah and Camouflage are
    **not** applied to it: those traits are written for normal, melee or
    ranged *attacks*, and many abilities say they ignore attacker modifiers.
  - A normal attack made as part of an ability follows the normal-attack
    rules.
- **Defensive actives count for Toughness.** Each character's active is
  assumed to be in place before the enemy turn. Each effect is recorded in
  the `Defence` column of `active_abilities.csv`:
  - **Damage reduction on itself:** −X% (Aesoth, Thoread, Hascule; Azkor
    against ranged only).
  - **Flat reduction:** −X Damage per hit, taken off the attacker's Damage
    before armour (Calandis against ranged; Jaeger against the taunted enemy;
    Darkstrider against adjacent enemies).
  - **Extra health:** heals, repairs and revives count as extra health
    (Incisus, Actus, Rotbone, Isabella, Trajann, Lysander, Baldr).
  - **Weakened enemies:** Suppressed deals −30% and Stunned −50% (wiki);
    Dante's target and the enemies around it deal −30%.
  - **Costs to itself:** Macer and Snappawrecka lose a % of health; Lucien
    drops to 50%.
- **Scope of those effects.** Kill counts assume the enemy focuses fire in
  one turn, so:
  - An **area** effect (Thothmek suppressing everything within 2 hexes) covers
    every enemy attack.
  - A **single-target** stun or suppress only weakens the **first** attack,
    the same logic as Terminator Armour.
  - Effects on "adjacent enemies" apply to melee attackers only.
- **Not counted:**
  - Block bonuses: they need block gear, which the model leaves out (Trajann,
    Lysander, Uthar).
  - Conditional heals (Cezare below 50% health, Neurothrope's % of damage).
  - Abaddon's "set to X Health": an emergency heal.
  - Deathleaper vanishing for a round.
  - Njal's stun, which only hits Flying enemies.
- **How each character's active is counted** is in `active_abilities.csv`,
  one reviewed row per character. The review rules are in `INSTRUCTIONS.md`.

**Percentage effects step up at level 36.** For example, Thoread goes from
31% to 33%, Aesoth 62% to 66%, Hascule and Dante 25% to 30%, Azkor 56% to 64%.
They stay flat after that up to level 50. This confirms the owner's choice of
36 over 35.

**The level 36 finding.** At Winged D3, only about 18 of the 82 actives that
deal damage beat a normal attack at level 36. At level 50, about 60 do.
Ability damage climbs steeply between level 35 and 50, while the D3 stat line
is already high. So at level 36 the stat line is most of the story; at level
50, kits like Ragnar's War Howl and Kharn's Kill! Maim! Burn! take over.

---

## Validation: the Castellan Creed test

The owner's old video data (`Tacticus - Castellan Creed Test.csv`, not in
the repo) holds the Creed test numbers, read in-game in a developer build. They are for
104 characters attacking Creed (melee, ranged) and taking Creed's attack,
all at Winged D3 with no equipment. The numbers were captured bit by bit
from 2024 to 2026 and never updated for patches.

Run against the September 2026 (1.42.110) game data, with the rules above:

- Creed hitting Creed: game **3,260**, model **3,258**.
- **150 of the 256** Creed test numbers match to within 1%, using stats and
  traits alone.
- Several mismatches came in groups at one exact ratio. Those groups
  confirmed trait behaviour:
  - Terminator Armour works per attack (×0.40 before the fix).
  - Heavy Weapon ×0.80 and Crushing Strike ×0.67 are not in the Creed test numbers.
  - Rapid Assault ×1.25 and Ranged Specialist ×1.33 are in the Creed test numbers.
- The remaining mismatches are one-off per character. Two causes:
  - passive abilities, which the Creed test numbers include (e.g. Jain Zar,
    Gibbascrapz, Morvenn Vahl's ranged)
  - balance changes since that character was captured (e.g. Anuphet's
    August 2026 rework)

---

## Sources

- Game data: tacticustable.com public API, `https://api.tacticustable.com/game-info`.
  The patch version is at `/game-info/version`. It has stats for every rank,
  weapons and pierce, traits, and every ability variable for every level.
  An ability's value = the level's entry × its rarity multiplier (Legendary
  ×1.8, Mythic ×2.0). Only re-download when the version changes.
- **Cross-check, September 2026:** tacticustable's base stats and weapons
  were compared with the wiki for all 117 characters. Only 3 differed, and
  the owner confirmed tacticustable is right each time:
  - Lysander base Damage 50 (the wiki says 25).
  - Titus base Damage 26 (the wiki says 25).
  - Uthar 4 ranged hits (the wiki says 2).
- Formula: tacticus.wiki.gg `HDTW_Damage`, `Damage_Types_and_Pierce_Ratio`,
  `HDTW_Shields`, and the trait pages.

---

## Changelog

| Date | Change |
|---|---|
| September 2026 | Progression switch: Gold / Diamond III / Mythic tiers; relics at Mythic (owners from the wiki, effects reviewed in relic_abilities.csv) |
| September 2026 | Azrael's Lion Helm only helps other characters (owner), so it doesn't count for him |
| September 2026 | Gear switch: standard Legendary top-level loadouts per character, crits and blocks at their average, `Gear` column for crit/block kit effects (owner decisions: switch, top-level Legendary, boosters) |
| September 2026 | One enemy turn = 5 attacks: an active's one-round protection only covers the first 5 attacks; first-attack-each-turn effects repeat every 5. Aesoth (active on) 14.6 → 8.3 |
| September 2026 | Owner answers on passives: bodyguards (Kell, Geminae), Uthar split stance, Varro not counted, Tyrant Guard always on |
| September 2026 | Passives added, always on, with Attack/Defence tokens. Re'vas's Overwatch active counted. Scenarios are now traits × ability level × active on/off |
| September 2026 | Cross-checked tacticustable against the wiki. Tacticustable is right on all 3 differences (owner-confirmed), so no model change |
| September 2026 | Defensive actives now count for Toughness (Defence column: damage reduction, flat reduction, extra health, weakened enemies, self-costs). The six owner questions on actives were answered; the model already matched them |
| September 2026 | Added the Scenarios and Active abilities sections (All triggered; opening with the active at level 36 or 50). The Creed check is built into `build_map.py --creed`: 148 of 250 within 1% |
| September 2026 | First version. Trait rule agreed; Rapid Assault left off (owner); Terminator Armour per attack (owner-confirmed, changed September 2024); validated against the Creed test data |
