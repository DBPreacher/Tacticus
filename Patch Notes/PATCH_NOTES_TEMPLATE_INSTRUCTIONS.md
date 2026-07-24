# DB Preacher Plays — Patch Notes Video Template Instructions

## Overview

This is the companion doc to `HTML_TEMPLATE_INSTRUCTIONS.md` (the Legendary Event
planner deck), but for a different content type: monthly Patch Notes breakdown
videos. Same underlying idea — a self-contained 1920×1080 HTML file used as an
OBS browser source or screenshot reference during recording — but built around
patch content (new characters, MoW, events, economy, bug fixes) rather than
team-comp data.

This doc captures everything decided and learned while designing the system,
so a new Claude session (or future you) can pick it up without re-deriving it.

---

## Source Data Priority

- **Discord `#patch-notes` post** (the dev/community write-up) is the primary
  source for everything **except** calendar dates and durations.
- **Snowprint's own developer calendar screenshot**, when shared, is the
  primary source for the **Calendar slide specifically** — it's more reliable
  than inferring dates/durations from prose narration, and has already
  resolved several date conflicts the prose left ambiguous.
- Never invent a date, duration, or category that isn't stated in a source.
  Where two sources conflict (example: TA Power-Ups was "July 13" in the
  Discord text but appeared closer to July 15–17 on the dev calendar), flag it
  visibly rather than silently picking one — either inline on the slide itself
  or as a note back to Andy before finalizing.
- Recurring monthly-cadence categories (Battle Pass, Character Release Event,
  Guild War, Guild Raid, Incursion, Quests, Legendary Release Event) now have
  **exact start/duration formulas** — see the cadence table under Calendar
  below — rather than needing to be inferred loosely from historical
  calendars.
- **Tournament Arena (TA) specifically**: timing is fully formula-driven (see
  cadence table), but the *variant* (Power-Ups, Faction, Conquest, Infested
  Power-Ups, etc., and whether MoW are included) still needs sourcing fresh
  from that month's patch notes each time.
- Home Screen Events (HSE) are the part that actually changes each month —
  always source these fresh from that month's patch notes, never assume from
  past cadence.

### When the developer calendar isn't available yet
The Snowprint calendar sometimes releases *after* the patch notes — don't
block the whole video on waiting for it. When it's missing:
1. Build the Calendar slide as best-effort from the Discord patch notes prose
   plus known monthly cadence for the recurring categories above.
2. Mark any date that's inferred-rather-than-confirmed (a small visual
   footnote on the slide, same treatment as the TA Power-Ups discrepancy
   note) rather than presenting it with false confidence.
3. Once the real calendar drops, diff it against the best-effort version
   together and correct anything that drifted — don't just quietly
   regenerate from scratch, since it's worth knowing *what* changed and
   *why* the inference was off, to sharpen the next month's best-effort guess.

---

## Slide Types

### Built so far
- Bug Fixes
- Requisitions
- Economy Changes
- Calendar (visual system, colorblind-safe palette, exact cadence formulas, and auto-scaling all done; automated generation script not yet built)
- Character reveal cards (single static layout — see below)

### Not yet built
- Machine of War reveal cards — same shell/approach as Character cards should
  largely apply (Primary/Secondary/Mythic instead of Passive/Active/Relic),
  but not yet tested against a real MoW's actual field shape.

### Deliberately not dedicated slides
Per the house script structure, these stay pure narration with no slide:
Hook, Character Updates, Improvements, Final Word.

---

## Visual System

### Shared shell (every slide)
- 1920×1080 canvas, dark navy-black base
  (`linear-gradient(160deg,#0a0e1a,#0d1119,#0a0c14)`), not pure black.
- Gold ornamental frame + header accents — the one constant across every
  slide, matching the gold/bronze ornament (laurels, skull crests, currency
  icon rims) used throughout the actual Tacticus UI. Roughly
  `#c9a227`–`#e8b83c`.
- Logo: `Corner_Icon_Right.png`, top-right, flush against the frame corner
  (not floating mid-corner). `Corner_Icon_Left.png` exists for a possible
  future two-corner treatment (e.g. a title/intro slide) but isn't used yet.
- Motion is ambient, never required for comprehension — frame-top sheen,
  breathing glow behind the portrait zone, a pulsing category dot, staggered
  rise-in on load. **Exception: the Calendar slide dials this back to just the
  frame sheen**, since it's the one slide meant to survive being frozen as a
  screenshot at an arbitrary moment — nothing should be mid-animation when
  someone screenshots it.

### Section accent colors
Borrowed from the game's own real semantic colors rather than invented where
possible:

| Slide | Accent | Source |
|---|---|---|
| Bug Fixes | Red/rust | Matches in-game defeat/negative-state red |
| Requisitions | Fire-orange | Matches in-game event/featured-character promo art |
| Economy Changes | Purple | **Not** sourced from an actual game screen — the one invented accent so far, open to revisiting if a better on-brand color turns up |
| Character/MoW reveals | Teal | Matches the in-game legendary/mythic glow (seen clearly on the Thothmek legendary character screen). Confirmed working in the built Cezare card. |

### Typography
- **Display headers** (big italic titles like "Monthly Bug Fixes"): Cinzel
  Decorative.
- **Labels, category headers, numbers, short HUD-style text**: Rajdhani.
  Good for short punchy tags, not built for paragraph reading.
- **Body/bullet text**: Public Sans. Chosen over Inter for being more
  condensed and slightly easier to scan at a glance; over Rajdhani because
  Rajdhani's technical/display letterforms slow down full-sentence reading.
- **Character/MoW cards, confirmed split**: **Spectral** (serif, italic)
  reserved specifically for the in-game lore paragraph; everything else
  (traits/damage/passive/active/relic breakdown) stays in Public Sans. Built
  and tested on the Cezare card — narrative voice vs. data/UI convention,
  worth judging on a few more characters to confirm it holds up rather than
  just looking right once.
- Rationale: sans survives YouTube's re-encode better at small sizes than thin
  serif strokes; serif was deliberately kept for the one place (lore text)
  where a different reading register actually helps.

### Portrait / character-render zone
- Reserved space, bottom-anchored, with a breathing radial glow behind it.
- The dashed border seen in mockups (`.portrait-slot.guide`) is a
  **design-guide only** — it must be removed (delete the `guide` class, or
  the whole rule) in any file actually delivered for production use.
- Two supported workflows, both fine:
  1. **Andy supplies renders per patch** → Claude drops the image directly
     into the slot when building that patch's deck. No border in the
     delivered file.
  2. **Andy composites the render in post-production** → deliver the file
     with a fully transparent/empty portrait zone (no border, no fill) so
     nothing shows through on the recording. Give the exact box
     dimensions/position so it's easy to align an overlay in the edit.

---

## Content-Specific Layout Notes

### Bug Fixes
- Category columns (currently Characters / User Experience) — count isn't
  fixed, could be more or fewer depending on the patch.
- Alternating row tint + left accent bar to break up a dense bullet wall.
- **Not yet implemented**: bullet count varies patch to patch, but current
  mockups hardcode font size for one month's example count. Needs, before
  real production use:
  - Auto-shrink on overflow (step font-size/line-gap down if a category runs
    long)
  - A floor size, past which the answer is a second "Bug Fixes, continued"
    slide rather than shrinking text below legibility

### Requisitions
- Grid column count should auto-flow based on how many requisitions exist
  that month. Current mockup hardcodes 2 columns for exactly 7 items — needs
  to become responsive (1 column for a short list, 2 for medium, 3 +
  smaller text if a month is unusually packed).
- Date range as a pill/chip, not inline text.
- Character lists use a middle-dot (`·`) separator, matching the in-game
  convention seen in Requisition screens.

### Economy Changes
- More hierarchical/nested than the other sections (e.g. weekly relic
  rotation schedules) — uses a single stacked column rather than a grid, so
  sub-lists have room to nest.
- Sub-list items get lighter color + smaller size + deeper indent, so they
  read as "detail under this bullet" rather than a new peer-level item.

### Calendar
The biggest automation opportunity, and the one slide meant to be
screenshotted standalone by viewers — it must look complete without the
surrounding frame/header context.

**Color legend — finalized system (superseding the earlier "carried over
unchanged" version below).** Every recurring category now gets its own
dedicated color; gray is reserved specifically for Home Screen Events (the
part that changes every month), and gold is reserved for genuinely rare
"this is a big deal" moments (Armageddon-style celebrations, Mythic events).

| Color | Meaning |
|---|---|
| Yellow | Battle Pass |
| Bluish-green | Incursion |
| Blue | Tournament Arena |
| Vermillion | Quests — format is always "Character vs Faction" (e.g. "Baldr vs Thousand Sons"), one character leading against a faction |
| Sky-blue | Character Release Event (HRE) |
| Red | Legendary Release Event (LRE) — the one true "alarm" color, always full-width/bold/glowing |
| Orange | Campaign Event |
| Reddish-purple/magenta | Guild War — one hue family covering both phases: Pre-Season as a lighter tint, Season at full saturation |
| White | Guild Raid — single-day start marker only (duration isn't visually spanned — see cadence table below) |
| **Gold** | **Special/Important Event** — reserved, rare use only (Armageddon-style celebrations, Mythic events, anything bigger than the normal monthly rhythm) |
| Gray | **Home Screen Event** — the variable part of the month; anything NOT in the recurring-cadence table below defaults here |

This palette is built on Okabe-Ito, a color set specifically validated to stay
distinguishable under red-green color blindness. Confirmed working well
directly with Andy (deuteranomaly-type, with knock-on difficulty on
desaturated/dark tones generally) after an earlier translucent-pastel version
didn't work for him. Solid, high-saturation fills — not translucent tints —
with per-swatch text color chosen for contrast (dark text on bright fills,
light text on dark fills).

### Recurring event cadence — exact formulas

These categories follow a fixed, calculable rhythm relative to the season/
month structure — precise enough to place them on the calendar **without
needing patch notes text at all**, only the season start date as an anchor.
Contrast with Home Screen Events, which still need fresh sourcing from that
month's patch notes every time.

| Event | Duration | Start rule |
|---|---|---|
| Battle Pass | Full season | Starts and ends with the season |
| Incursion | 5 days | Recurs every 5 weeks, starting Monday of the 4th week |
| Tournament Arena | 4 days | Twice per season — Wednesday of week 1, and Tuesday of week 3 |
| Quests | 3 days | Twice per season — Wednesday of week 2, and Wednesday of week 5 |
| Character Release Event (HRE) | 14 days | Starts Sunday of week 2 |
| Legendary Release Event (LRE) | 7 days | Starts Sunday of week 5 |
| Campaign Event | 14 days | Starts Thursday of week 1 |
| Guild Raid | 14 days | **Only the start day is marked**, not the full span. 2–3 per month depending on how they fall — always confirm exact dates from that month's patch notes rather than inferring |
| Guild War — Pre-Season | 3 days | Starts Wednesday of week 2 |
| Guild War — Season | 15 days | Starts Saturday of week 2 |

Anything that doesn't match one of the rows above is a Home Screen Event —
source it fresh from the patch notes every month, render it gray, and don't
try to infer its cadence.

- **Tournament Arena (TA) note**: the *timing* is fully formula-driven per the
  table above, but the *variant* (Power-Ups, Faction, Conquest, Infested
  Power-Ups, MoW or not) still needs sourcing fresh from that month's patch
  notes each time.

**New elements, discovered from Snowprint's own developer calendar:**
- Permanent recurring header tags: light purple/pink on Sunday ("Always
  Double XP"), yellow on Saturday ("Always Double Gold"). Rendered as small
  header subtext, not as event bars, since they're standing features rather
  than monthly news.
- Small blue "Raid Boss" tags (`L – <name> · M – <name>` format) marking that
  week's Legendary/Mythic Guild Raid boss rotation.

**Naming convention**: drop Snowprint's internal jargon prefix (`HSE:`) and
internal shorthand (e.g. "Faction Focus") in favor of Andy's own plain
community-facing naming ("Faction Boost"), matching how his past calendars
have always been written. Where Snowprint's internal label and the
community-facing event name differ, merge them, e.g.:
`Character Release Event — Cezare ("Insanguination")`.

**Layout**: vertical month label on the left edge of each month's block —
implemented as `position:absolute` over the month's weeks rather than as a
spanning grid item (a spanning grid item can inflate the shortest auto-sized
rows in its span, which caused real layout bugs — see Changelog). Each week's
events render into independent stacked "lanes" (not fixed row slots) so a
light week and a heavily-stacked week both render cleanly.

**Not yet built**: the actual automated extraction/generation script. The
current calendar is still hand-authored from a reasoned-through data table —
same "author the markup directly, no build step" approach the LE deck
instructions describe.

### Character reveal cards
Single static layout (not a click-through reveal sequence — Andy narrates
over one fully-visible card rather than advancing through beats), built and
tested against Cezare's real wiki data.

**Structure, top to bottom:**
1. Header bar: "New Character" tag + patch version (same convention as every
   other slide)
2. Name (large, Cinzel Decorative) + title, with a teal-glow title-line
3. Badge row: Faction, Alliance, Rarity, Damage type — quick-glance chips
4. Trait pills (Terminator Armour, Rapid Assault, Deep Strike, etc.) — a
   compact row, not prose
5. Lore quote — Spectral serif italic, left-accent border, deliberately
   distinct texture from everything below it
6. Active ability — name + description, left-accent block
7. Passive ability — same treatment
8. Relic — same treatment, gold-accented instead of teal (ties to the same
   gold used for Special/Important elsewhere) since it's a distinct
   "equipment" category rather than a character mechanic
9. Portrait zone, right side, same guide-border convention as every slide

**Content-sourcing workflow, specific to this slide type.** Andy no longer
has pre-patch build access (previously had creator access, now doesn't), so
new-character content requires a different sourcing plan than everything
else in the deck:
1. **Official Discord patch notes reveal text** — usually has the lore
   blurb, sometimes a partial trait/ability teaser. Available immediately.
2. **Tacticus wiki** (fan-maintained, tacticus.wiki.gg) — has a genuinely
   good structured format that maps almost directly onto this card's fields
   (stats, traits, damage type, active/passive text, relic). Best structured
   source, but since it's community-maintained rather than official, it can
   lag hours-to-days behind a brand-new character's release.
3. **Other creators' early videos/screenshots** — fallback for anything
   still missing once actually recording, especially "how it plays in
   practice" observations for a verdict/notable-mentions angle.
- **Never fabricate a missing field.** If a value (e.g. a Relic name) isn't
  confirmed from any source yet, mark it visibly as TBD on the card itself
  (dashed border + explicit "unconfirmed" tag was the treatment used on the
  Cezare mockup) rather than guessing or omitting silently.
- Ability numeric values (damage multipliers, thresholds) scale per character
  level — don't quote a specific number unless the source gives one plainly;
  paraphrase mechanically ("bonus Damage," "regenerates Health") rather than
  inventing a figure.

---

## Open Items / Known Gaps

- Auto-shrink/overflow handling not yet implemented for Bug Fixes or
  Requisitions (currently hardcoded to one month's example content) — the
  Calendar has this solved and could serve as the reference implementation.
- Economy Changes' purple accent isn't sourced from an actual game screen —
  worth revisiting if something more on-brand turns up.
- Machine of War reveal cards not yet built — same shell/approach as
  Character cards should largely transfer (Primary/Secondary/Mythic instead
  of Passive/Active/Relic), but untested against a real MoW's actual field
  shape.
- TA Power-Ups date conflict (July 13 vs. ~July 15–17 on the dev calendar)
  unresolved as of the last Calendar build — confirm before finalizing that
  patch's video.
- No automated generator script yet for the Calendar (or anything else) —
  everything is still hand-built HTML per patch.

---

## Changelog

| Date | Change |
|---|---|
| July 2026 | Initial design session. Established shared shell (frame, logo, header, portrait zone, motion system) and built Bug Fixes, Requisitions, and Economy Changes mockups. Corrected initial invented accent-color system to one grounded in real Tacticus UI colors (gold ornament, teal legendary glow, red defeat state, orange event promos) after reviewing in-game screenshots. |
| July 2026 | Body-text font decided: Public Sans over Inter (more condensed, easier to scan) and over Rajdhani (not built for paragraph reading). Agreed to reserve Spectral (serif) for lore-text specifically once Character/MoW cards are built, rather than choosing one font for the whole card. |
| July 2026 | Built full Calendar mockup (two-week slice on Feb 1.36 data, then full five-week July 1.40 data) after Andy shared his own historical calendars (six months of examples) plus Snowprint's own developer-calendar screenshots. Resolved several date ambiguities from the Discord patch notes using the developer calendar as ground truth. Documented developer calendar as the preferred primary source for calendar data going forward. Added Raid Boss tags and recurring Double XP/Double Gold header treatment, both new relative to Andy's past calendars. |
| July 2026 | Documented that the developer calendar sometimes releases after the patch notes, so the Calendar slide needs a best-effort fallback workflow (infer from prose + known cadence, flag inferred dates, reconcile once the real calendar lands) rather than blocking production. Documented Tournament Arena's fixed-timing/variable-type cadence specifically, since its date can be trusted from prose even without calendar confirmation. |
| July 2026 | Rebuilt the Calendar's color palette from scratch after Andy identified he's colorblind (deuteranomaly-type, red-green, with knock-on difficulty on desaturated/dark tones). Replaced translucent pastel fills with a solid, high-saturation Okabe-Ito-based palette — confirmed working well by Andy. Corrected the calendar's proportions (it had incorrectly gone full-width; fixed to ~55% width with portrait space alongside, matching every other slide). Added and then fixed real auto-scaling logic (measure natural height, compress proportionally with a legibility floor, matching the Bug Fixes overflow philosophy). |
| July 2026 | Fixed two structural bugs in the vertical month-label system: (1) each week had been its own isolated CSS grid, so a label couldn't actually span multiple weeks — caused a duplicated "Feb" label and a missing "Mar" label; (2) after restructuring to a shared grid, a CSS Grid quirk where a row-spanning item inflates the shortest auto-sized rows in its span caused large blank gaps under every week's day-numbers and pushed the auto-fit script to its overflow floor. Fixed by making the month label `position:absolute` (removed from grid-sizing calculations entirely) rather than a spanning grid item. Also moved the Calendar's corner "stamp" text to bottom-right (was colliding with the legend at bottom-left once the calendar's height grew). |
| July 2026 | Finalized the full recurring-event color system with Andy: every named recurring category (Battle Pass, Incursion, TA, Quests, HRE, LRE, Campaign Event, Guild War, Guild Raid) now gets its own dedicated color instead of defaulting to gray. Gray is now reserved specifically for Home Screen Events (renamed from "Default/recurring"). Added a new reserved gold color for rare Special/Important events (Armageddon-style celebrations, Mythic events). Captured Andy's exact cadence formulas (start day + duration relative to season week number) for every recurring category — precise enough to place these on the calendar without patch notes text at all, contrasted with Home Screen Events which still need fresh sourcing every month. Initially mislabeled the "Character vs Faction" bars (e.g. "Baldr vs Thousand Sons") as a Guild War sub-element — Andy corrected this: they're actually Quests, which are always formatted as one character leading against a faction. Reassigned those bars from the Guild War color to Quests/vermillion. |
| July 2026 | Built the first Character reveal card (Cezare), confirming the teal accent and the Spectral/Public-Sans typography split in a real layout for the first time. Decided against a click-through reveal sequence — Andy narrates over one fully-visible static card instead. Documented the content-sourcing workflow specific to this slide type: Andy no longer has pre-patch build access, so new-character content now depends on the Discord reveal text, the fan-maintained Tacticus wiki (which has a genuinely well-matched field structure but can lag on brand-new characters), and other creators' footage as a last resort. Established the convention of marking any unconfirmed field (e.g. an unknown Relic) visibly as TBD rather than fabricating or silently omitting it. |
