# Damage Visualiser — Plan

**Status: draft for owner sign-off. Nothing is built yet.**

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
| Abilities | Option B: the stat-line dot comes from normal attacks, plus an **ability arrow** for the featured character and the labelled reference characters only |
| Ability level | 36 at Legendary. Defensive abilities often cross a breakpoint at 36 (e.g. −30% → −33% damage reduction) |
| Situational traits | Left off the chart and talked about on camera. Rapid Assault left off (owner) |
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

- Ability numbers are pulled automatically at level 36 Legendary from the
  game data.
- Deciding what an ability *means* still needs judgement: area damage,
  conditions, summons. So each video gets a small abilities file covering
  only the featured character and the reference characters on screen, about
  6 characters.
- **Damage arrows:** how much the kit shortens "attacks to kill", e.g.
  extra hits from passives, or the active used once.
- **Toughness arrows:** only the clear-cut effects are modelled: percentage
  damage reduction, flat damage reduction, shields, extra health.
  Situational effects are flagged for the owner to cover on camera.
- The exact arrow definition gets fixed on the first real example.

---

## Build steps

1. **`fetch_stats.py`.** Downloads the game data (cached; only downloads
   again when the patch version changes) and writes `tacticus_stats.csv`:
   - Health, Damage and Armour at Winged D3
   - melee and ranged damage type, hits and pierce
   - movement

   The wiki is the fallback source.
2. **`damage_model.py`.** Applies `DAMAGE_MODEL.md` and writes the Damage and
   Toughness numbers for everyone, plus the Creed card numbers. It re-checks
   itself against the Creed test data.
3. **HTML template and generator.** One command builds the video page for a
   named character.
4. **Ability arrows.** The per-video abilities file, with values filled in
   automatically at level 36.
5. **Later:** the Mythic view with relics.

---

## Open questions

- Pick the reference characters for each scene.
- **Ranged Specialist** is left off under the trait rule, but the in-game
  preview does apply it. Keep it off?
- **Terminator Armour in Toughness:** reducing only the first enemy attack
  each turn assumes the enemy focuses fire on the character in one turn.
  OK?
- Optional: 5–6 current in-game previews, e.g. Jain Zar, Morvenn Vahl, one
  Terminator Armour character. They would confirm that the leftover
  mismatches are passives, not a model error.
