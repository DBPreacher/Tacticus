# DB Preacher Plays — HTML Video Template Instructions

## Overview

The HTML video template is a self-contained browser file that produces all
the slides for a "Plan Now" video. It runs at 1920×1080, is controlled with
keyboard/mouse, and can be used as:

- An **OBS browser source** for live screen recording with progressive reveals
- A **screenshot source** for static overlays in HitFilm
- A **reference document** for the final team picks

Each new LE needs:
1. A new conditions YAML (for the analysis script)
2. A new HTML file (for the video graphics)

Both are generated from the same underlying data, so do the analysis first
and transfer the results into the HTML. If you re-run the analysis on the
**same** LE later (roster updated, new characters unlocked, etc.), rebuild
the HTML again the same way — team compositions can change even though the
track info/objectives don't.

---

## File Structure

```
tacticus-le-planner/
├── data/
│   └── tacticus_characters.csv       ← character database (see INSTRUCTIONS.md)
├── le_analysis.py                     ← analysis script
├── conditions_template.yaml           ← copy this for each new LE
├── le14_uthar.yaml                    ← example conditions file
├── HTML_TEMPLATE_INSTRUCTIONS.md      ← this file
└── video_templates/
    └── dbpreacher_uthar_v4.html       ← video template (one per LE)
```

Note: in practice, the HTML is authored directly as static markup per
phase (pool list + recommended/chosen list per team) rather than rendered
from a separate JS data array. There's no build step — Claude (or you,
by hand) edits the HTML sections directly per the analysis output. If you
later build a proper generator script, treat this file's markup as the
target output format.

---

## Slide Structure

Each template contains 5 slides in order:

| Slide | Content | States |
|-------|---------|--------|
| Fastest Method | Most efficient starting team per track | Empty boxes → Alpha fills → Beta fills → Gamma fills |
| Alpha Track | Info → Objectives → Overview → T1 pool → T1 highlight → T2 → ... → Tn pool → Tn highlight → Summary |
| Beta Track | Same structure as Alpha |
| Gamma Track | Same structure as Alpha |
| Monthly Plan | Empty sections → Healers → Tanks → Self-Heal/Damage Reduction → Most Relevant |

**Important:** the number of Full Coverage teams per track is NOT fixed at
3. It equals the `Tokens:` value reported by the analysis for that track
(check the "FULL COVERAGE TEAMS (5-man)" section — `Tokens: N`). Some LEs
will have 3 teams on every track; others (like LE 14 Uthar's Alpha track)
have 4. Build one team phase (`<track>-t1`, `<track>-t2`, ... `<track>-tN`)
per token, and make sure:

- The Team Overview phase (`*-ov`) has one `.ov-card` per team
- The Summary phase (`*-end`) has one `.ov-card` per team
- The JS `SLIDES` array has a `swap`/`sub` step sequence covering every team
  phase in order, ending with a swap into `*-end`
- If a track has 4+ teams, add `cols-4` (or similar) to the `.ov-row` class
  on both the Overview and Summary phases so the cards don't overflow the
  3-column grid. CSS already includes an `.ov-row.cols-4` modifier that
  shrinks font sizes slightly — reuse it, or add `cols-N` variants as needed.

---

## Objective Chips — "Newly Covers" Only

Each team's `.obj-chips` (shown in the team-bar, Overview card, and Summary
card) must list **only the conditions that team newly covers**, matching
the analysis's "Newly covers:" line for that team — not every condition the
team happens to satisfy. The chip point values must sum exactly to that
team's `Pts/deployment` value. Double check this arithmetic before shipping;
a stale/carried-over chip that doesn't belong to that team is an easy
copy-paste mistake (this happened in the v4_3 file on Gamma Team 3, which
showed a redundant "No Power DMG" chip already covered by Team 2).

---

## Navigation

| Key | Action |
|-----|--------|
| `Space` or `Click` | Advance one step (next reveal within slide) |
| `← Left arrow` | Go back one step (full history, works within and across slides) |

No other UI is visible on screen — no counters, no hints.

---

## Updating for a New LE

### Step 1 — Run the analysis

```bash
python3 le_analysis.py le15_newchar.yaml --csv data/tacticus_characters.csv
```

Open the output `.txt` file. You need these values for the HTML:

- Track names, enemies, eligible factions, restriction (from patch notes —
  these don't come from the analysis output, carry them over from the
  previous HTML or patch notes if the LE hasn't changed)
- All objectives with their point values
- Most efficient starting team (pool + **Recommended**, usually 3 characters)
- Every Full Coverage team (`Tokens: N` of them) — pool + Recommended 5 +
  "Newly covers" conditions + pts/deployment
- Any `★ High-priority investment (multi-team)` lines
- Monthly plan characters (built from usage frequency — see below)

### Step 2 — Copy and update the HTML

1. Duplicate the previous LE's HTML file, rename it (e.g. `dbpreacher_le15_newchar.html`)
2. Open in a text editor
3. Find and replace each phase's markup directly (Overview cards, team-bar
   chips, pool/highlight character lists, Summary cards)

**Alternatively:** Ask Claude to regenerate it by providing:
- The analysis `.txt` output
- The patch notes (for track info, enemies, restrictions)
- Any team selection changes you want to make

Claude will regenerate the full HTML in one response.

### Step 3 — Team data to update per track

For each track, update every team phase (`<track>-t1` … `<track>-tN`,
where N = Tokens for that track):

- Team Overview card (pts, "Team N · Token N" label, obj-chips)
- Team-bar (same pts/chips, repeated in the per-team phase)
- Pool list (`.chars-pool`) — every eligible character, in the order the
  analysis lists them
- Highlight list (`.chars-hi`) — same characters, marked `chosen`/`unchosen`
  (or `healer` for HEALER-tagged chosen characters — see coloring notes below)
- If pool size == 5 (team size), it's a **locked** team: use
  `<p class="pnote lock">⚠ Only 5 eligible — all required</p>`, collapse
  `.chars-pool` and `.chars-hi` into a single always-visible block (see
  Beta Team 2 / Gamma Team 1 in the Uthar template for the exact pattern),
  and skip the `sub` reveal step for that phase in the JS.
- Summary card (`.ov-chars`) — the Recommended 5 only, with `healer` class
  applied to any HEALER-tagged character (this is the only role color
  actually used in ov-chars/team lists in practice — see below)

**Fastest Method** — update the 3 starting team sections using the
analysis's "MOST EFFICIENT STARTING TEAM → Recommended" list (not the full
pool) for each track: track name, conditions/chips, pts/stage, character list.

**Monthly Plan** — see dedicated section below.

---

## Character Role Colour Coding

CSS supports four role classes on `.charlist li` / `.ov-chars li`:

| Role key | Colour | When to use |
|----------|--------|-------------|
| `"healer"` | Green | Character has `Healer = Y` in CSV |
| `"tank"` | Blue | `Terminator_Armour = Y` or `Mk_X_Gravis = Y` |
| `"self-heal"` / `"resilient"` | Purple | `Self_Heal = Y` or `Resilient = Y` (CSS only defines a `.resilient` class — reuse it for self-heal characters too, since they share the same purple/✦ styling) |
| `"chosen"` | White | Default for chosen characters |

**Observed convention in practice:** team pool/highlight lists (`.chars-pool`,
`.chars-hi`) stay plain `chosen`/`unchosen` even when a character is a
tank/healer/self-heal/resilient — role colouring is NOT applied there, to
keep the reveal clean. The **only** place role colour is actually applied
is the `healer` class on Summary (`*-end`) `.ov-chars` lists, so the
recap cards show at a glance which teams have healer coverage. Keep this
convention unless you deliberately want to expand it — if you do, apply
tank/resilient consistently across ALL team phases at once, not just some.

Tyrant Guard and Thothmek are ability-based tanks — flag them manually in
the roles dict when they appear in a recommended team, since the CSV won't
tag them via `Terminator_Armour`/`Mk_X_Gravis`.

---

## High-Priority Investment Notes

When the analysis flags a character with `★ High-priority investment
(multi-team)` on a team, add a dim note line to **both** the pool and
highlight views of that team's `chars-wrap`:

```html
<p class="pnote dim">★ High-priority investment: Incisus, Marneus Calgar</p>
```

If a locked team (pool == 5) also has a flagged investment, append it as a
second `<p class="pnote dim">` line under the existing `lock` note.

These notes exist to call out characters worth prioritising with resources
because they show up across multiple full-coverage teams (and often the
Fastest Method team too) — reuse the exact character names/grouping from
the analysis's `★ High-priority investment` line.

---

## Monthly Plan — Build From Usage Frequency

Don't use "your judgment call" here — build the Monthly Plan directly from
how often each character is actually recommended across the whole LE:

1. Collect every **Recommended** list from the analysis: the 3-man Fastest
   Method team for each track, plus the Recommended 5 for every Full
   Coverage team on every track.
2. Tally how many times each character name appears across all of those
   lists.
3. Populate the four cards:
   - **Healers** — HEALER-tagged characters that appear in any recommended
     list, most-used first.
   - **Tanks** — TANK(trait)-tagged characters that appear in any
     recommended list, most-used first. Group single-use tanks together on
     one line with `·` separators to keep the card to ~5 lines (e.g.
     `Arjac · Angrax · Wrask`).
   - **Self-Heal / Damage Reduction** — SELF-HEAL-tagged characters that
     appear in any recommended list, most-used first. (Card title was
     previously "Self-Heal / DR" — always render it as **"Self-Heal /
     Damage Reduction"** now.)
   - **Most Relevant** — the top 3–4 characters by raw usage count across
     ALL recommended lists (regardless of role), with a `<small>` note
     showing count + which teams, e.g.
     `Incisus <small>4 teams — Alpha T2/T3/T4 + Gamma T3</small>`. This
     card should overlap heavily with the `★ High-priority investment`
     flags from the analysis — if a character has that flag, they almost
     certainly belong here.

Only include characters that actually appear in this LE's recommended
teams — don't carry over holdover picks from a previous LE's Monthly Plan
just because they're generally good units.

---

## Using in OBS

1. Add a **Browser Source** in OBS
2. Set URL to the local file path: `file:///path/to/dbpreacher_uthar_v4.html`
3. Set width to **1920**, height to **1080**
4. Enable **Shutdown source when not visible** to reset between recordings
5. Use **Interact** mode in OBS to click/space through slides while recording

Alternatively, open in Chrome in full-screen (F11), use OBS Window Capture.

## Using in HitFilm

Screenshot each slide state:
1. Open the HTML in Chrome
2. Set zoom to fit (or set window to 1920×1080)
3. Press Space to advance, take a screenshot after each reveal
4. Import screenshots as image overlays in HitFilm, time them to your voiceover

---

## Meta Composition Reminder

When reviewing the analysis output and finalising team picks, the target
meta for pushing deep into stages is:

**2 Healers + 2 Tanks + 1 Self-Healer**

For Mechanical-heavy teams (Necrons / AdMech):
**2 Mechanics + 2 Tanks + 1 Self-Healer**

Special tanks (ability-based, not trait-based):
- **Tyrant Guard** — always treat as high-priority tank when eligible
- **Thothmek** — always treat as high-priority tank when eligible

The analysis script now uses meta composition as a tiebreaker when multiple
5-man combinations score equally — so its recommended teams will prefer
Healers, Tanks, and Self-Healers automatically. You can still override any
pick by specifying it directly in the HTML data.

---

## Transitioning to a New Session

When starting a new Claude session to continue this work, share:

1. **The analysis output** (`.txt` file) for the current LE
2. **The current HTML file** if making visual changes
3. **The current `le_analysis.py`** if making script changes
4. **The current `tacticus_characters.csv`** if the character data needs updating

And state: *"Continue the DB Preacher Plays LE planning workflow — see
INSTRUCTIONS.md and HTML_TEMPLATE_INSTRUCTIONS.md in the Tacticus repo."*

The project knowledge in Claude.ai should contain:
- `INSTRUCTIONS.md` (character database + LE analysis workflow)
- `HTML_TEMPLATE_INSTRUCTIONS.md` (this file)
- `DB_Preacher_Production_Process.md` (video production workflow)
- Example scripts (Plan Now, Patch Notes, Does XXX Do Anything?)

---

## Changelog

| Date | Change |
|------|--------|
| July 2026 | Initial HTML template built for LE 14 Uthar (v4) |
| July 2026 | Meta-aware team selection added to `le_analysis.py` — uses meta composition (2H+2T+1SH) as tiebreaker when multiple combinations score equally |
| July 2026 | Rebuilt LE 14 Uthar HTML (v6) from a re-run analysis with updated roster data. Documented that team count per track is variable (matches `Tokens:`, not fixed at 3) and added the `.ov-row.cols-4` CSS pattern for tracks with 4+ teams. Clarified that obj-chips must reflect only "newly covers" conditions per team (found and fixed a stale redundant chip from the old file). Documented the actual role-colouring convention (healer-only, applied in Summary cards). Added the `★ High-priority investment` note convention. Replaced "judgment call" Monthly Plan guidance with an explicit usage-frequency tally method. Renamed "Self-Heal / DR" to "Self-Heal / Damage Reduction" everywhere. |
