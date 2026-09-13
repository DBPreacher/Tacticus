# Damage Model — Rules Record

This is the record of exactly what the damage visualiser counts and what it
leaves out, and why. When a result looks odd, or a trait gets reworked,
check this file first. The design and build plan is in `PLAN.md`.

---

## Standard setup

Every character is compared under the same conditions:

| Setting | Value |
|---|---|
| Rank | Diamond III |
| Stars | Winged (Legendary star) = 11 stars = ×2.1 on the 0-star rank stats |
| Abilities | Level 36, Legendary rarity (for ability arrows only) |
| Equipment | None. No crits, no blocks from gear |
| Relics | None (a Mythic + relics view is a later, separate step) |
| Terrain | Flat ground, no hex effects, no buffs or debuffs |
| Damage roll | Middle of the ±20% range, the same as the in-game damage preview |

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
| Terrifying | −30% damage from melee attacks. It does nothing against ranged attacks, which is why it rarely feels defensive in practice (Jain Zar) |
| Martial Ka'tah | Normal attacks against it deal −20% |
| Camouflage | Ranged attacks against it −1 hit (min 1). The −2 at range 3+ and −3 in Tall Grass are left off (position and terrain) |
| Beast Slayer | +20% melee damage against Big Targets and Vehicles. Its block chance is left off (random) |

### Left off: depends on what happens in the battle

| Trait | Why it's off | In-game preview (Creed test) |
|---|---|---|
| Rapid Assault | Only the first attack of each battle. **Owner decision, September 2026** | Preview **does** apply +25% |
| Heavy Weapon | Only if it hasn't moved this turn | Preview did not apply +25% |
| Crushing Strike | Only if it hasn't moved this turn | Preview did not apply +50% |
| Ranged Specialist | Only if it didn't start its turn adjacent to an enemy | Preview **did** apply +33% (Sho'Syl) |
| Prioritised Efficiency | +25% dealt / −25% taken, lost after moving 3+ hexes | No data |
| Contagions of Nurgle | Aura, position-based, grows over rounds | Preview did not apply it (Typhus, Corrodius, Rotbone) |
| Weaver of Fate | Needs 3+ enemies to have taken Psychic damage that turn | Not applied |
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

## Validation: the Castellan Creed test

The owner's old video data (`Tacticus - Castellan Creed Test.csv`, not in
the repo) holds in-game preview numbers from a developer build. They are for
104 characters attacking Creed (melee, ranged) and taking Creed's attack,
all at Winged D3 with no equipment. The numbers were captured bit by bit
from 2024 to 2026 and never updated for patches.

Run against the September 2026 (1.42.110) game data, with the rules above:

- Creed hitting Creed: game **3,260**, model **3,258**.
- **150 of the 256** in-game numbers match to within 1%, using stats and
  traits alone.
- Several mismatches came in groups at one exact ratio. Those groups
  confirmed trait behaviour:
  - Terminator Armour works per attack (×0.40 before the fix).
  - Heavy Weapon ×0.80 and Crushing Strike ×0.67 are not in the preview.
  - Rapid Assault ×1.25 and Ranged Specialist ×1.33 are in the preview.
- The remaining mismatches are one-off per character. Two causes:
  - passive abilities, which the in-game preview includes (e.g. Jain Zar,
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
- Formula: tacticus.wiki.gg `HDTW_Damage`, `Damage_Types_and_Pierce_Ratio`,
  `HDTW_Shields`, and the trait pages.

---

## Changelog

| Date | Change |
|---|---|
| September 2026 | First version. Trait rule agreed; Rapid Assault left off (owner); Terminator Armour per attack (owner-confirmed, changed September 2024); validated against the Creed test data |
