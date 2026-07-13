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
and transfer the results into the HTML.

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

---

## Slide Structure

Each template contains 5 slides in order:

| Slide | Content | States |
|-------|---------|--------|
| Fastest Method | Most efficient starting team per track | Empty boxes → Alpha fills → Beta fills → Gamma fills |
| Alpha Track | Info → Objectives → Overview → T1 pool → T1 highlight → T2 → T3 pool → T3 highlight → Summary |
| Beta Track | Same structure as Alpha |
| Gamma Track | Same structure as Alpha |
| Monthly Plan | Empty sections → Healers → Tanks → Self-Heal/DR → Most Relevant |

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

- Track names, enemies, eligible factions, restriction (from patch notes)
- All objectives with their point values
- Most efficient starting team (pool + recommended)
- Full coverage teams 1–3 (pool + recommended 5 for each)
- Monthly plan characters (your judgment call)

### Step 2 — Copy and update the HTML

1. Duplicate the previous LE's HTML file, rename it (e.g. `dbpreacher_le15_newchar.html`)
2. Open in a text editor
3. Find and replace the data sections — everything is clearly labelled in the Python
   data blocks at the top of the generator script

**Alternatively:** Ask Claude to regenerate it by providing:
- The analysis `.txt` output
- The patch notes (for track info, enemies, restrictions)
- Any team selection changes you want to make

Claude will regenerate the full HTML in one response.

### Step 3 — Team data to update per track

For each track (Alpha, Beta, Gamma), update:

```
TRACK_TEAMS = [
    (team_num, total_pts, [(cond_name, cond_pts), ...], [chosen 5 chars], {roles}, locked?),
    ...
]
TRACK_POOLS = [
    [pool chars for team 1],
    [pool chars for team 2],
    [pool chars for team 3],
]
TRACK_POOL_NOTES = ["note for T1", "note for T2", "note for T3"]
```

**Fastest Method** — update the 3 starting team sections:
- Track name, conditions, pts/stage, character list

**Monthly Plan** — update the 4 category lists based on your meta judgment.

---

## Character Role Colour Coding

When listing characters in team pools or recommended teams, the HTML
applies visual role colours based on the `roles` dict:

| Role key | Colour | When to use |
|----------|--------|-------------|
| `"healer"` | Green | Character has `Healer = Y` in CSV |
| `"tank"` | Blue | `Terminator_Armour = Y` or `Mk_X_Gravis = Y` |
| `"self-heal"` | Purple | `Self_Heal = Y` in CSV |
| `"resilient"` | Purple | Has `Resilient = Y` (used for Adeptus Custodes etc.) |
| `"chosen"` | White | Default for chosen characters |

Tyrant Guard and Thothmek are ability-based tanks — flag them manually in
the roles dict when they appear in a recommended team.

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
