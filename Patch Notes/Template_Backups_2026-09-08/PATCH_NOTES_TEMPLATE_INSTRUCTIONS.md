# DB Preacher Plays — Patch Notes Video Template Instructions

## Overview

This is the companion doc to `HTML_TEMPLATE_INSTRUCTIONS.md` (the Legendary Event
planner deck), but for a different content type: monthly Patch Notes breakdown
videos. Same underlying idea — a self-contained 2560×1440 HTML file used as an
OBS browser source or screenshot reference during recording — but built around
patch content (new characters, MoW, events, economy, bug fixes) rather than
team-comp data.

This doc captures everything decided and learned while designing the system,
so a new Claude session (or future you) can pick it up without re-deriving it.

---

## Preserve Original Headers and Subject Nesting

Latest rules override earlier conflicting examples:
- Preserve the original approved header: September Update on the left, Version on the right, original italic section title and section accent line. Scale its dimensions proportionally for 2560×1440. Do not add category subtitles or duplicate body section headings in the header.
- Bug Fixes: stack Characters above Guilds & User Experience within the left content area, never side by side. Keep the right character area clear. Smaller body text (approximately 26–27px at 2560×1440) is acceptable to fit one screen.
- Nest character-specific changes beneath their faction when that faction already has a heading. In V1.42, Ûthar belongs under Leagues of Votann, with his abilities beneath him.

## Character Space and Compact Layout: Latest Direction

This section supersedes earlier full-width compact-screen advice and rigid slide-count/font-size targets.

- Always preserve a clear right-hand character composition area on Economy, Monthly Improvements and Bug Fixes. Keep content on the left, with no placeholder, border or text in the character area.
- **Economy:** retain the approved compact Shop Rotations column at its existing text size and width. Remove Offers & Bundles completely from the slide, leaving that right-hand area for Andy's character. Retain offer details in the extraction for reference; do not move them to another slide automatically.
- **Monthly Improvements:** Characters & Traits gets its own screen. Group Operations & Vault under Crusade. Place Other Modes directly below Crusade on the same screen when it fits. Keep Guild Raids together on its own screen when necessary rather than dropping that category. Minimize page changes within this grouping.
- **Bug Fixes:** aim for one screen with alphabetical subjects within sections; two narrow sections may sit side by side inside the left content area, leaving the right side free.
- Smaller body text is acceptable. At 2560×1440, start around 28–29 CSS pixels for compact Monthly Improvements and Bug Fixes, then inspect actual renders. Economy retains its approved 34–36px text. Andy's size-11 reference describes desired visual density, not a requirement to use literal 11px HTML text; point sizes and on-screen sizes differ between tools.
- Validate every heading and bullet against the content area and footer, not only the browser viewport. Ensure Characters & Traits fits fully. Condense copy and reduce unnecessary spacing before adding pages. Keep important mechanics and qualifications intact.
- Current content boundary for Monthly Improvements and Bug Fixes is x=1658 on a 2560px canvas. Reserve approximately x=1740 to 2460, y=315 to 1340 for the character. Economy's existing column ends around x=1248 and leaves more character space.

---

## Compact Reference Screens for Video

This is Andy's approved presentation approach and supersedes the earlier advice to split subjects into many slides or enforce a 48px body-text floor.

- Aim for **one screen per section**, or **two when the section is genuinely substantial**. Do not turn every faction, character or mechanic into a separate slide. V1.42 target: two Monthly Improvements, one Economy, one Bug Fixes.
- Screens remain visible as compact reference sheets while Andy narrates. Show related changes together, with category headings, bold subject labels and short nested bullets. Two bullet levels are appropriate; avoid unnecessarily deep trees.
- Edit copy first: retain what changes for players, key numbers, timing, conditions and exceptions. Remove repeated names, introductory filler, design rationale and unnecessary examples. Keep full details in the extraction for narration; never shorten a mechanic into a misleading claim.
- Use a balanced two-column layout where useful. Maintain the existing navy/gold shell and section colors. The supplied old screenshot demonstrates acceptable density only; do not copy its styling.
- Native canvas remains 2560×1440. For compact reference screens, start around 34–38px body text, 44–50px category headings and 70–80px main titles. Judge actual renders, not an arbitrary font-size floor. Use bold labels and modest spacing to make the hierarchy clear.
- Full-width content is appropriate for these compact sections; reserve a portrait area only when specifically needed for the composition. Do not waste a third of the slide and compensate with extra pages.
- Check clipping, column balance and scaled video previews. Condense and regroup before adding a second screen; do not exceed two screens per section without discussing it with Andy.
- Bug Fixes remain alphabetized within sections. Shop Rotations lead Economy. Avoid em dashes. Preserve the approved V1.42 Calendar and Blessed Requisitions unchanged.

---

## Editorial Rules and V1.42 Rebuild Scope

These instructions supersede conflicting older examples in this document.

- **Punctuation:** avoid the em dash (Unicode U+2014) in authored slide copy and scripts unless absolutely necessary. Prefer a heading, colon, comma, full stop or separate bullet. Older examples containing this punctuation are not a style requirement. Preserve source documents and the explicitly protected V1.42 screens rather than applying a global replacement to them.
- **V1.42 protected screens:** Blessed Requisitions and Monthly Calendar are approved. Leave their HTML and PNG files unchanged, including wording, layout and resolution. This specific exception overrides the general native-resolution migration for these two existing screens. Future new builds still use 2560×1440.
- **V1.42 rebuild work:** restructure Monthly Improvements and Monthly Bug Fixes with clear category and subject groupings; reorder and simplify Economy Changes. Build revised slides at native 2560×1440 and regenerate their matching PNGs. Do not start a rebuild merely because these instructions are being recorded.
- **V1.42 Special Events:** omit this slide from the recording sequence and active delivery set. Retain the existing file as an unused asset; do not delete it. Keep event information in the extraction and cover it through the Calendar and narration where appropriate.

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

### Continuing events and repeat content

- **Campaign / Incursion: "No New Event" or "No New"** means no new character or Machine of War has been added. Existing campaigns and Incursions for previously available characters/Machines of War remain available. Keep the scheduled event; do not interpret the label as cancellation or flag the lack of a new featured unit as missing information.
- **Second and third Legendary Release Events:** include the returning character, event name, occurrence number and dates. The character's event requirements do not change between occurrences, and the original video already covers the breakdown. Do not request or rebuild tracks, objectives or special coverage merely because this is a repeat event. Extract any explicitly announced changes if supplied.
- **Existing-character ability rebalances:** place these in Monthly Improvements under Characters and traits. Source X/Y placeholders are acceptable; exact scaling values are not required and their absence does not belong in Unsure.
- **Future events and continuations:** patch text may announce events extending beyond the developer calendar or into the next patch period. Retain explicit text-only continuation dates in Calendar and note the image cutoff. This is a carry-forward reminder for the next patch, not an unresolved conflict; do not silently drop the continuation.

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

## Required PNG Exports

- Whenever the HTML slides are built or updated, also deliver one **2560×1440 PNG for every final HTML slide**, including each continuation page. This is a standard deliverable for every future patch; Andy should not need to request it separately.
- Build HTML slides on a native 2560×1440 CSS-pixel canvas. Set the OBS browser source and PNG capture viewport to 2560×1440; export at device scale factor 1. Preserve the 16:9 composition. Do not use a 1920×1080 canvas with a higher device scale factor for new builds, or upscale an existing screenshot. Smaller browser previews may uniformly scale the complete canvas for viewing only.
- Wait for fonts, images, layout fitting and entrance animations to finish before capture. Export the complete, fully visible slide without browser controls or design guides, retaining any intentionally empty portrait space.
- Check that every PNG is exactly 2560×1440, that the PNG count matches the final HTML slide count, and that text and assets are present without clipping. Regenerate the matching PNG whenever an HTML slide changes.
- Match each PNG's base filename to its HTML file. Keep exports together in a clearly named `PNG_2560x1440` folder within the patch deliverables, and provide a ZIP containing the full PNG set for convenient download.
- This export requirement applies during slide production; it does not change the mandatory extraction-only first pass.

---
## Native HTML Resolution

- All new and revised patch notes HTML slides must be built at **2560×1440**, matching their required PNG exports. This supersedes the former 1920×1080 production size.
- When adapting an older reference, scale layout coordinates, margins, portrait zones and typography proportionally by 4/3 as a starting point, then assess readability. Increasing resolution alone does not make text appear larger in a YouTube player; simplify content and allocate more screen area to key text.
- Update any fixed dimensions, overflow checks, capture settings, OBS instructions and documented portrait overlay coordinates to the new canvas. Verify the complete slide at native size and in a smaller 16:9 preview.
- Keep older patch references as historical examples; do not silently overwrite archived decks solely to change their resolution.

---

## Visual System

### Shared shell (every slide)
- Native 2560×1440 canvas, dark navy-black base
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
- Use the Monthly Improvements hierarchy: section/category, then a named character, enemy, faction or system, then short fix bullets. Express hierarchy with headings and grouped blocks; avoid deeply indented bullet trees.
- **Alphabetize subjects within each section**, case-insensitively by displayed character/enemy/system name. Keep every subject's related fix bullets together. When there is no named subject, use the leading descriptive fix label as the sorting key. Alphabetize separately within each section, not across the whole deck; preserve that order across continuation slides.
- Write each fix as a concise statement of the corrected behavior. Keep important conditions attached to the fix. Avoid em dashes; put the subject in its heading rather than repeating it before a punctuation separator.
- Use the same readable text sizes, short blocks, spacing and small-preview checks as Monthly Improvements. Add continuation pages before shrinking text below the readability floor. Preserve complete details in the extraction and narration.
- Retain the section's red/rust accent and shared shell. Group related bullets visually and check the final HTML and PNGs for overlap or clipping.

### Requisitions
- Grid column count should auto-flow based on how many requisitions exist
  that month. Current mockup hardcodes 2 columns for exactly 7 items — needs
  to become responsive (1 column for a short list, 2 for medium, 3 +
  smaller text if a month is unusually packed).
- Date range as a pill/chip, not inline text.
- Character lists use a middle-dot (`·`) separator, matching the in-game
  convention seen in Requisition screens.

### Economy Changes
- **Shop Rotations come first.** Place other shop/economy changes next; offers and bundles come afterwards and must not dominate the page or receive the strongest emphasis.
- Use clear section headings and subject/change blocks, following Monthly Improvements' readable hierarchy. Put supporting details directly beneath their parent change, avoiding dense paragraphs and deep indentation.
- Keep dates and important availability conditions with the relevant shop item. Use short lines, bold key changes, generous spacing and the same video readability checks. Split into continuation slides if needed, maintaining the priority order.
- Avoid em dashes in authored copy. Retain the purple section accent and any intended empty portrait area.

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
| Incursion | 6 days | Recurs every 5 weeks, starting Monday of the 4th week and ending Saturday |
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
- **Incursion duration confirmed as 6 days (September 8, 2026)**: Monday of week 4 through Saturday. V1.41 ran August 24–29; the V1.42 developer calendar shows September 28–October 3. Andy approved updating the cadence from 5 to 6 days after these two observations.
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
- **Create a dedicated Special Events slide only when a new game mode is introduced**, unless Andy explicitly requests an exception. A returning event, new edition of an existing event, anniversary or Legendary Event teaser alone does not require this slide.
- For V1.42, omit the existing Special Events slide from the recording sequence and active deliverables. Preserve the source information in the extraction and relevant Calendar/narration coverage.
- When a new mode warrants the slide, use the gold accent and a clear mode title with short grouped explanations of its purpose, core mechanics and confirmed timing. Split dense explanations into additional slides instead of shrinking text.
- Use the shared shell without a portrait zone unless a specific composition calls for one. Apply the same native 2560×1440 production and PNG export requirements.

### Monthly Improvements

Use the shared navy/gold shell and steel-blue section accent. Organize changes for a narrated YouTube video using **category → subject → change group → detail**. The extraction keeps the full hierarchy; the slide expresses it through headings and grouped blocks rather than four levels of indented bullets.

**Hierarchy on screen:**
- Small section label: Monthly Improvements.
- Category label: Characters & Traits, Guild Raids, or Modes & Features, as appropriate to the source.
- Main slide title: the faction, character, enemy or mode being discussed, such as Leagues of Votann. Keep subjects together on the section reference screen; use a second screen only for a substantial section.
- Separate change blocks: named trait/ability, stat change, or mechanic, such as Prioritised Efficiency and Movement 2 → 3.
- Inside each block: short, left-aligned bullets explaining that change. Use concise subject bullets with supporting sub-bullets when useful. Place affected character names directly beneath the relevant change, so its scope is explicit.

**Layout and pacing:**
- Group related changes into compact sections across one or two columns with an obvious reading order.
- Aim for 2–3 short bullets per block, usually one line each and no more than two lines. These are starting limits, not a reason to omit information. Split complex mechanics or long affected-character lists across clearly titled continuation slides.
- Keep a trait's conditions and exceptions with its effect. Do not simplify away mechanically important distinctions or invent a shared change for characters whose changes differ.
- Use direct before/after notation for confirmed numeric changes (for example Movement 2 → 3). This example is illustrative, not source data. Use X/Y where the source uses scaling placeholders.
- Avoid repeating the faction or character name in every bullet when the heading already establishes it. For miscellaneous changes, group by the relevant subject; do not manufacture unnecessary subcategories for one short item.
- Preserve the reserved portrait area when Andy intends to composite a render. Keep it free of guides and placeholder text. If no render is planned, content may use the available width, while keeping line lengths short.
- Repeat category and subject on continuation pages, adding a descriptive focus or page number. Default to one screen per section and at most two for substantial content, as described above.

**Typography and video readability at 2560×1440:**
- Use the typography ranges in Compact Reference Screens for Video. The earlier large-text slide sequence was too fragmented for Andy’s videos.
- Give blocks generous separation, use roughly 1.2–1.3 body line height, and keep text left aligned. Use bright body text on dark backgrounds; steel-blue accents support headings, not low-contrast paragraph text.
- Bold the changed value or key effect rather than whole paragraphs. Use labels, grouping and spacing alongside color so meaning does not depend on color perception.
- Keep narration conversational and fuller than the slide. Preserve complete source details in the extraction and ensure any detail removed from slide copy remains available for the script.
- Render and check every slide for clipping and overlaps, then inspect a 640×360 preview to judge the actual video hierarchy and readability. Higher PNG resolution alone is not a readability fix.

**Content conventions:**
- Existing-character rebalances belong under Characters & Traits; new debut cards remain in Characters / Machine of War.
- Relics: name, equipped character and a plain-English effect; omit the Crit Chance/Crit Damage stat line as previously agreed.
- Mode changes: lead with the mode/system in the group heading. Dates normally belong on the Calendar.

This hierarchy supersedes the earlier flat Economy-style lists and the old preference to compress Monthly Improvements into 2–3 categories on a slide. Group related information by subject and use additional slides when needed.

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
1. **Official Discord patch notes reveal text** remains the primary source for patch content; the developer calendar remains primary for dates/durations.
2. **For every new character, check https://tacticus.wiki.gg first for detailed character information.** Open the actual character page and check Alliance, Faction, rarity, attack profiles, traits, lore, active/passive abilities and relic. Record the page URL and check date in the extraction. A page existing does not mean every field is complete; placeholders such as XXX are missing information.
3. **If a character page is absent or required details are missing, tell Andy exactly what is missing; Andy will obtain another source.** Do not independently substitute other creators' videos/screenshots as the default fallback. If access is blocked, distinguish inability to verify from a missing page. Continue with verified fields and retain missing fields as TBD until Andy supplies them.
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
| September 8, 2026 | Updated Incursion cadence from 5 to 6 days, Monday of week 4 through Saturday, with Andy's approval. V1.41 (August 24–29) and V1.42 (September 28–October 3) both support six days. Resolved the duration validation note and removed the obsolete open item; recurrence remains every 5 weeks. |
| September 8, 2026 | Recorded Andy's conventions for No New campaign/Incursion labels, repeat Legendary Events, acceptable X/Y rebalance placeholders, and future-event continuations. |
| September 8, 2026 | New-character sourcing: check actual tacticus.wiki.gg character pages first for detailed fields, record availability and gaps, and ask Andy to obtain missing material rather than automatically using other creator sources. |
| September 8, 2026 | Made one 2560×1440 PNG per final HTML slide a standard deliverable for future patches, with proportional rendering, export checks, matching filenames and a ZIP of the complete set. |
| September 8, 2026 | Switched future and revised HTML builds to native 2560×1440 with matching PNG capture. Replaced flat Monthly Improvements lists with category/subject/change blocks and video readability guidance, including continuation slides and readable typography. |
| September 8, 2026 | Recorded minimal em-dash use; protected the approved V1.42 Calendar and Requisitions files; added grouped, alphabetized Bug Fixes; prioritized Shop Rotations in Economy; limited Special Events slides to new modes and omitted the V1.42 slide from the recording sequence. |
| September 8, 2026 | Replaced the fragmented 22-slide approach with compact reference screens: one per section, two for substantial sections, concise player-focused wording and nested subject bullets. |
| September 8, 2026 | Restored right-hand character space; removed Economy offers from the slide; reduced compact body text; separated Characters & Traits and nested Operations & Vault under Crusade with Other Modes below. |
