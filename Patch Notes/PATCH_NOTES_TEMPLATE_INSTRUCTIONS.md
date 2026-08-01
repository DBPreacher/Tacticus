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

## Patch Notes Extraction Workflow

Before any slide gets built, raw patch notes (Discord text + calendar
screenshot, sometimes a separate dev calendar) get parsed into a single
structured extraction `.md` first. This is a distinct, mandatory first pass —
don't jump straight to slide-building from the raw text.

**Fixed categories, always used, in this order:**
1. Overview
2. Characters / Machine of War
3. Calendar
4. Economy
5. Monthly Improvements
6. Blessed Requisitions
7. Bug Fixes
8. Unsure

Everything from the raw patch notes must land in one of these — nothing gets
silently dropped. If genuinely unsure which bucket something belongs in, or
unsure of a date/fact, it goes in "Unsure" rather than being guessed into a
category.

**"Monthly Improvements" added as a category after V1.41.** The original
seven-category list had no home for character rebalances, new Relics for
*existing* characters, or mode/feature reworks — this content kept getting
folded into Characters/MoW or Economy by default, purely for lack of a
better bucket. Andy caught this only after V1.41's extraction doc and
scripting were already well underway, which meant re-sorting content that
had already been placed elsewhere. Starting the categorization with all
eight buckets from the start avoids that rework. Rule of thumb for what goes
here: if it's a change to something that already existed before this patch
(a rebalance, an existing character's new Relic, a mode getting reworked),
it's Monthly Improvements — Characters/MoW is only for *new* characters/MoW
debuting this patch.

**Conflict handling.** When the Discord text and the calendar screenshot
disagree on a date, don't silently pick one — log both in a small table
(item / what the text says / what the calendar shows) inside the extraction
doc, and flag it back to Andy rather than resolving it yourself. See "Reading
the calendar image reliably" below — this session, nearly every flagged
"conflict" turned out to be Claude misreading calendar pixel columns, not an
actual Snowprint inconsistency, so don't over-trust a manual image read.

**Bug Fixes can legitimately be empty.** V1.41 shipped with no bug fixes
section in the patch notes at all — first time this happened. Don't assume
missing Bug Fixes content means the extraction failed; note it plainly in
the extraction doc and confirm with Andy rather than guessing.

### Reading the calendar image reliably

Manually reading which day-column an event bar starts/ends under is
error-prone — this session repeatedly misread bars by one day (HSEs, TA
Power-Ups, a Quest, all initially misread, all off by exactly one column).
**Whenever a category has an entry in the recurring-cadence formula table
below, compute its date from the formula and treat that as authoritative
over a manual pixel-read of the calendar image** — cross-check the image
against the formula's answer rather than the other way around. Only fall
back to a careful manual read for categories with no formula yet (new,
one-off, or brand-new-mode content — e.g. Crusade this patch), and if still
uncertain, ask Andy directly rather than guessing from the image.

---

## Slide Types

### Built so far
- Bug Fixes
- Requisitions
- Economy Changes
- Calendar (visual system, colorblind-safe palette, exact cadence formulas, and auto-scaling all done; automated generation script not yet built)
- Character reveal cards (single static layout — see below)
- Special Events (new this session — see below)
- Monthly Improvements (new this session — see below)

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
| Reddish-purple/magenta | Guild War — single color for both phases (Pre-Season and Season). Originally tried as one hue family with Pre-Season as a lighter tint, but Andy found that inconsistent shading made Guild War harder to visually track across weeks — reverted to one flat color for both, distinguished only by label text ("Guild War — Pre-Season" vs "Guild War Season NN") |
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

**V1.41 validation notes:**
- **Campaign Event formula confirmed correct**: Andy caught that the
  initially-built calendar showed Campaign Event as short, disconnected
  2-day snippets each week instead of one continuous bar. Corrected to a
  single bar, Thursday of week 1 through the formula's 14-day end point —
  matched Andy's own read exactly (Thu Aug 6 → Wed Aug 19). Good confirming
  data point for this formula.
- **Incursion duration may need revisiting**: the table says 5 days, but
  Andy confirmed V1.41's Incursion (Tau Broadside Revamp) ran Monday of
  week 4 through Saturday — 6 days, not 5. One data point isn't enough to
  change the formula outright, but flag this and check duration again on
  the next Incursion before updating the table.
- **Crusade has no cadence entry yet**: brand-new permanent mode, only one
  data point so far (Season 1 start date, tied to a specific character
  debut). Treated as a single-day start marker for now, same visual
  treatment as Guild Raid. Revisit once a second Crusade season's start
  date is available to check whether it follows a fixed formula the way
  Guild War does.

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

**Row-count minimization**: when two bars in the same week don't overlap in
days (e.g. an HSE ending early in the week + a different HSE starting late
in the week, or a short single-day marker sitting in a gap next to another
bar), put them in the same `bar-row` as sibling `.bar` divs rather than
stacking separate rows — keeps dense weeks (patches with 7+ concurrent
categories) from growing an excessive number of lanes.

**Anchor categories should hold a fixed row position across weeks.**
Guild War specifically caused real confusion this session because its row
position drifted between weeks (last row one week, third row the next,
first row after that) purely as a side effect of how many other bars
happened to be stacked above it that week. Fix: for any category that spans
multiple consecutive weeks (Guild War, multi-week Character Release Events,
etc.), pick one row position — first row worked well — and place it there
in every week it appears, even if that means other categories shuffle
around it. Don't let row position be an incidental side effect of that
week's row-count; treat it as a first-class layout decision for anything
the viewer needs to track continuously across weeks.

**Raid Boss tags always show both call-outs explicitly**, even when the
Legendary and Mythic bosses are the same unit that week (e.g.
"Riptide / Riptide") — don't collapse to a single name just because it
repeats.

**Not yet built**: the actual automated extraction/generation script. The
current calendar is still hand-authored from a reasoned-through data table —
same "author the markup directly, no build step" approach the LE deck
instructions describe.

### Special Events
New slide type, built this session, for content too significant/narrative
to compress into a Requisitions-style bullet list but that doesn't fit
Character/MoW reveal cards either — new game modes, anniversaries, and
teaser call-outs for an upcoming LE covered in full elsewhere in the video.

- Uses the reserved **gold "Special/Important"** accent, matching the
  Calendar's gold convention (big-deal moments only) — reused here rather
  than inventing a new color, since Crusade's launch + the 4th Anniversary
  genuinely qualify as "bigger than the normal monthly rhythm."
- Layout: vertical stack of event blocks (not the 2-column
  bullet-grid/portrait layout Requisitions and Economy use), since each
  entry needs 2–3 sentences of description rather than a single line.
  Each block: small pill-tag (e.g. "New Game Mode," "4th Anniversary,"
  "Character Release Event," "Legendary Release Event") + title + date pill
  + description lines.
- No portrait zone on this slide — it covers multiple unrelated topics
  rather than one character, so a single-portrait zone doesn't make sense
  here the way it does on Requisitions/Economy/Character cards.
- First built for V1.41: Crusade (new mode launch), War Amongst the Stars
  (4th Anniversary), Veiled Machinations (Sekhetar Robot character release),
  and a short Heroes of the Chapter (Lysander LRE) teaser pointing to the
  full Alpha/Beta/Gamma breakdown covered in the Characters segment.
- **Open item**: only tested with 4 event blocks in one patch so far — not
  yet clear how this should adapt for a lighter or heavier patch (e.g. a
  month with just one standout announcement, or five+).

### Monthly Improvements
New slide type, built this session, to fix a real gap: earlier patches had
been quietly folding "everything else" content (character rebalances, new
Relics for existing characters, mode reworks) into whichever section felt
closest, rather than giving it a proper home. Andy caught this after V1.41's
first draft was already fully scripted — the extraction doc had Cezare's
balance note and both new Relics sitting under Characters/MoW (despite not
being new-character content), and the Guild War reward changes sitting
under Economy. Monthly Improvements is the correct home for all of it.

- **Reuses the Economy Changes shell** (categorized bullet lists, portrait
  column) rather than inventing new layout, since the content shape is
  similar — categorized lists of changes, some with nested sub-detail.
- **New dedicated accent color: steel-blue.** Deliberately not Economy's
  purple, even though this slide can absorb Economy's content in months
  where Economy is skipped (as in V1.41) — keeps the two slides visually
  distinct in any future patch that needs both simultaneously.
- **Category set, as built for V1.41**: New Relics, Mode & Feature Changes.
  Started as four categories (Character Improvements, New Relics, Mode &
  Feature Reworks, Guild War all separate) but Andy had it condensed down
  to two after seeing it — Guild War folded into Mode & Feature Changes as
  its own bullet (with a nested sub-list for the individual reward lines
  rather than one dense run-on sentence), and the standalone "Character
  Improvements" category merged into Mode & Feature Changes too, since a
  single-bullet category wasn't worth its own header. **Treat 2–3 categories
  as the target, not 4** — merge sparse categories rather than giving every
  content type its own header.
- **Relic entries**: drop the Crit Chance/Crit Damage stat line entirely
  (not needed for the video) and reword the effect text in the same
  conversational readability-pass style used for Character Card
  Active/Passive text — see that convention above. Relic name + who
  equips it, then one plain-English sentence on what it actually does.
- **Bullet phrasing**: lead with the mode/system name, not the character
  name — "Tournament Arena Faction War — Cezare now deployed with the
  Blood Angels..." rather than "Cezare — now deployed with...". Drop
  parenthetical mode-context asides once the mode already opens the
  sentence (redundant). No dates needed in this slide's bullets — that's
  the Calendar's job.
- **No portrait guide border** — same "invisible reserved zone" convention
  as Character Cards (see above), since this was built directly as a
  production file rather than a mockup.
- **Overflow-checking technique, worth reusing**: rendered the file with
  `wkhtmltoimage` and a small injected `<script>` that measures
  `.cats.getBoundingClientRect().height` against `.body-wrap`'s height and
  writes the numbers directly onto the rendered image, rather than just
  eyeballing a screenshot. Confirmed content fit comfortably (~600px used
  of ~824px available) before declaring it done. Worth doing this on any
  category-heavy slide (Bug Fixes, Requisitions) once those get their
  auto-shrink treatment, rather than relying on visual inspection alone.


### Character reveal cards
Single static layout (not a click-through reveal sequence — Andy narrates
over one fully-visible card rather than advancing through beats), built and
tested against Cezare's real wiki data.

**Structure, top to bottom — finalized order as of V1.41:**
1. Header bar: "New Character" tag + patch version (same convention as every
   other slide)
2. Name (large, Cinzel Decorative) + title, with a teal-glow title-line
3. Badge row: **Alliance / Faction / Rarity, in that order** (not
   Faction/Alliance/Rarity — Andy corrected this) — quick-glance chips
4. **Unlock line** — a small teal-dot line reading "Unlocks via [method] —
   begins [date]", sourced from the extraction doc's confirmed dates. New
   as of V1.41: Andy pointed out this info "comes first" in the video (the
   character segment airs before the Calendar slide), so it can't just rely
   on the Calendar to tell the viewer when/how to get the character —
   needs to live on the card itself.
5. Damage-type badges (Melee/Ranged), **as their own row below the unlock
   line, above Traits** — not merged into the top Alliance/Faction/Rarity
   badge row. Format: "Melee — N hit [type]" / "Ranged — N range, N hit
   [type]", spelling out hit count and range explicitly rather than just
   naming the damage type. Omit a badge entirely for any profile that's
   N/A (e.g. a melee-only character gets no Ranged badge at all) — don't
   show a placeholder or "N/A" badge.
6. Trait pills (Terminator Armour, Rapid Assault, Deep Strike, etc.) — a
   compact row, not prose
7. Lore — Spectral serif italic, left-accent border, deliberately distinct
   texture from everything below it. If the source is an in-game quote,
   keep the quotation marks; if it's Andy's own researched summary rather
   than a direct quote, present it unquoted. Keep it to one tight paragraph
   — condense multi-paragraph source material rather than reproducing it
   in full, and tidy/reword rough source material for flow rather than
   pasting it verbatim if it reads awkwardly.
8. Active ability — name + description, left-accent block
9. Passive ability — same treatment
10. Relic — same treatment, gold-accented instead of teal (ties to the same
    gold used for Special/Important elsewhere) since it's a distinct
    "equipment" category rather than a character mechanic. TBD tag is just
    the word **"TBD"** — earlier "TBD — confirm before recording" wording
    was dropped as unnecessarily verbose.
11. Portrait zone, right side — see the updated portrait convention below.

**Ability-text readability pass (new convention, V1.41).** Don't just
paraphrase the tooltip mechanically — rewrite Active/Passive descriptions
in a conversational, spoken-out-loud register, the way Andy would actually
say it on camera. Lead with the plain-English effect, bold the one detail
that matters most (e.g. a cooldown-removal condition), and close with a
one-line "in short" takeaway if the mechanic has a few moving parts. This
is a step beyond the numeric-scaling rule below — it's about phrasing and
flow, not just which numbers to omit.

**Damage badge format, confirmed exact wording (V1.41):** lead with the
category, not the weapon type — "Melee — 1 hit Melta" / "Ranged — 3 range,
1 hit Bolter", not "Bolter — 1 hit, Range 3". Category first, then the
specifics.

**Portrait zone — updated convention (V1.41).** The two-column
grid/portrait-space layout stays (don't remove the column — Andy wants the
reserved space for his own compositing in post), but the zone itself must
be **completely empty** in any file used for actual recording: no dashed
guide border, no "character render drops in here" placeholder text, just
an empty div with the breathing glow behind it. The dashed-border version
is fine for early mockups/discussion only — as soon as a card is meant for
real use, strip the guide entirely rather than leaving a visible border.

**Layout bug to watch for:** the unlock line was originally added inside
the fixed-height, absolutely-positioned `.hdr` block (after the badges),
which pushed the header's real content height past the hardcoded pixel
offset the body content below assumes — caused the traits row to visually
collide with the unlock line. Fixed by moving the unlock line into the
normally-flowing `.left-col` instead (first child, above traits), which
sidesteps the fixed-offset math entirely. **Any time new content gets added
inside `.hdr`, double-check it doesn't push past the top offset the body
content assumes** — flowing layout is safer than fixed pixel math whenever
there's a choice.

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
  (a plain "TBD" tag — see the updated Relic convention above) rather than
  guessing or omitting silently.
- Ability numeric values (damage multipliers, thresholds) scale per character
  level — don't quote a specific number unless the source gives one plainly;
  paraphrase mechanically ("bonus Damage," "regenerates Health") rather than
  inventing a figure.
- **Source material isn't always in English.** For Sekhetar Robot (V1.41),
  the only available screenshot of one ability was in Spanish. Translated it
  directly and used the translated name on the card, but flagged in the
  extraction doc that the exact official English ability name should be
  double-checked against the wiki/EN patch notes once available — a
  translation is a reasonable stopgap, not a substitute for confirming the
  real localized term once it exists.

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
- Incursion's cadence-table duration (5 days) may be wrong — V1.41 measured
  6 days (Monday of week 4 through Saturday). Needs a second data point
  before changing the formula.
- Crusade has no cadence formula yet — only one data point (Season 1 start,
  tied to Lhykis's debut). Currently treated as a single-day marker like
  Guild Raid; revisit once a second season's start date is known.
- Special Events slide only tested with 4 blocks in one patch — not yet
  clear how it should scale for a lighter or heavier patch.
- Monthly Improvements only tested with 2 categories in one patch — not yet
  clear how it holds up in a month with more content (e.g. several existing
  characters getting rebalanced at once, or 3+ new Relics).
- Sekhetar Robot's "Heavy Warpflamer" ability name is a translation from
  Spanish-only source material — confirm against the real English text once
  available, in case Snowprint's actual EN name differs.

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
| August 2026 | First full real-patch run-through, V1.41. Formalized the patch-notes extraction workflow as a mandatory first pass: raw Discord text + calendar screenshot → single structured `.md` sorted into fixed categories (Overview, Characters/MoW, Calendar, Economy, Blessed Requisitions, Bug Fixes, Unsure), with text-vs-calendar conflicts logged in a table rather than silently resolved. Learned the hard way that most flagged "conflicts" this round were Claude misreading calendar pixel-columns by one day, not real Snowprint inconsistencies — documented that recurring-cadence formulas should be treated as authoritative over a manual image read whenever a formula exists. Confirmed the Campaign Event formula (Thu week 1, 14 days) exactly against a real patch for the first time. Flagged a possible Incursion duration discrepancy (6 days observed vs. 5 in the table) to recheck next time rather than changing the formula on one data point. Built the first Special Events slide (gold accent, vertical block layout, no portrait zone) for content that doesn't fit Requisitions/Economy/Character-card shapes — new modes, anniversaries, LE teasers. Reverted Guild War's two-tint color scheme (Pre-Season lighter, Season full) back to one flat color for both phases, and fixed Guild War's row position to be pinned consistently at the top of its lane across every week it spans — Andy found the drifting position across weeks made it hard to track. Established that Raid Boss tags should always show both Legendary/Mythic call-outs explicitly, even when it's the same boss both times. Confirmed Bug Fixes can legitimately be empty in a given patch — V1.41 had none. |
| August 2026 | Built all four V1.41 Character Cards (Ramus, Lhykis, Lysander, Sekhetar Robot) and finalized real production conventions from Andy's feedback across them: badge order is Alliance/Faction/Rarity (not Faction/Alliance/Rarity); damage-type badges get their own row below a new "Unlocks via [method] — begins [date]" line, both sitting above Traits; damage badges lead with Melee/Ranged category first, then hit/range specifics; Relic TBD tag simplified to just "TBD"; Active/Passive text gets a full conversational readability pass, not just mechanical paraphrasing; and the portrait zone must be completely invisible (no guide border, no placeholder text) in any real production file, though the reserved column itself stays since Andy composites his own renders in post. Fixed a layout bug where the new unlock line, added inside the fixed-height header block, pushed real header height past the hardcoded offset the body content assumed, causing a visual collision with the traits row — resolved by moving it into the normally-flowing left column instead. Handled a non-English source for the first time (Sekhetar Robot's ability was only found in Spanish) by translating directly and flagging the translation for later confirmation against the real EN text. Discovered a real gap in the extraction workflow after the fact: existing-character rebalances, new Relics for existing characters, and mode reworks had nowhere to go and were being folded into Characters/MoW or Economy by default — added "Monthly Improvements" as an eighth fixed extraction category (Characters/MoW is now new-character-debut content only), and built the corresponding slide (steel-blue accent, reusing the Economy Changes shell) to hold this content going forward — condensed from an initial 4-category draft down to 2 (New Relics, Mode & Feature Changes) after Andy found the extra headers weren't earning their space, with Guild War's reward changes folded in as a labeled sub-list. Verified the finished slide's actual fit using `wkhtmltoimage` plus an injected measurement script rather than eyeballing a screenshot — worth reusing this technique on other category-heavy slides once they get auto-shrink treatment. |
