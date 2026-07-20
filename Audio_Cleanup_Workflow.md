# Audio/Video Cleanup Workflow — Reference Guide

This documents the process worked out across several editing sessions for cleaning up
OBS recordings (voiceover + slides) before video assembly. Paste or summarize this at
the start of a new session so Claude can pick up the same process without
re-discovering it from scratch.

---

## 0. Before starting: check the video track

Ask (or state up front) whether the video in these files matters:
- **Disposable** (blank desktop capture, nothing needed) → audio can be freely cut,
  video ignored entirely, output as audio-only.
- **Matters** (slides, facecam, anything the viewer sees) → every audio cut must be
  mirrored on the video track at the exact same timestamp, so pacing edits don't
  desync picture from voice.

For a slides-based channel, assume video matters unless told otherwise.

---

## 1. Extract audio and transcribe

```bash
ffmpeg -y -i INPUT.mp4 -vn -c:a pcm_s16le raw.wav
ffmpeg -y -i raw.wav -ar 16000 -ac 1 16k.wav
```

Transcribe with word-level timestamps using `pocketsphinx` (installable via
`pip install pocketsphinx --break-system-packages` — the wheel bundles its own
acoustic model, no network access to a model host needed):

```python
from pocketsphinx import Decoder, get_model_path
import os

model_path = get_model_path()
config = Decoder.default_config()
config.set_string('-hmm', os.path.join(model_path, 'en-us', 'en-us'))
config.set_string('-lm', os.path.join(model_path, 'en-us', 'en-us.lm.bin'))
config.set_string('-dict', os.path.join(model_path, 'en-us', 'cmudict-en-us.dict'))

decoder = Decoder(config)
decoder.start_utt()
with open('16k.wav', 'rb') as f:
    f.read(44)  # skip WAV header
    while True:
        buf = f.read(1024)
        if not buf: break
        decoder.process_raw(buf, False, False)
decoder.end_utt()

for seg in decoder.seg():
    print(f'{seg.word}\t{seg.start_frame/100:.2f}\t{seg.end_frame/100:.2f}')
```

**Important caveat:** pocketsphinx's word *recognition* is often poor, especially on
proper nouns/game character names — expect gibberish like "in sizes" for "Incisus" or
"snag wrongs" for "Necrons". That's fine. What matters is the *timing/structure* it
gives you: word boundaries, pause locations, and — critically — **repeated phrase
patterns**, which show up as recognizable repeats even when the exact words are
misheard. Don't trust the transcribed words literally; do trust the rhythm.

---

## 2. Find retakes by comparing against the script

If a script/outline document is provided, always compare the transcript against it
section by section. Look for:

- **Exact or near-exact n-gram repeats** with a pause in between (a quick Python
  sliding-window check over 2–5 word sequences catches most of these).
- **A sentence that trails off oddly, a pause, then restarts** — even if the reworded
  version doesn't match word-for-word, matching it against the script's actual
  phrasing tells you which take is the "real" one.
- **Stacked/multiple retakes** — don't assume only one repeat. A single flubbed line
  can get attempted 3–5 times in a row before landing; keep scanning past the first
  repeat you find in a cluster.

**Always keep the *last* (most final) take, cut everything before it**, unless told
otherwise. When the wording shifts between attempts (not an exact repeat), match each
attempt against the script to judge which one is actually the intended final version —
usually whichever one flows on cleanly into the next scripted line.

### Handling recurring content that *isn't* a mistake

Scripts often deliberately repeat phrases (e.g. a recurring "★ High-priority
investment:" callout used for multiple characters/teams, or a character name that
legitimately appears in several team rosters). Before cutting anything, check the
script for whether the repeated content is supposed to recur. Cutting a real recurring
scripted line by mistake is a bigger error than leaving in a genuine one.

### Low-confidence spots — flag, don't guess

Sometimes the transcript is just gibberish with no clear structure (a bad stumble, or
a filler sound like "umm"/"nn" that pocketsphinx can't parse into anything). When the
data doesn't give a confident cut boundary, **don't guess** — cutting the wrong content
is worse than leaving a minor issue in. Flag it in the change note with the
approximate timestamp and ask the person to confirm the exact wording/boundary, or
re-describe what they actually said.

### Checking suspiciously long pauses

Any gap longer than ~2s is worth a second look before just compressing it — it's
sometimes a sign a retake happened but the "bad" attempt was silent (e.g. they
paused, thought better of it, and never actually voiced the first attempt). Re-run
silence detection over just that window at a much lower/more sensitive threshold
(e.g. -50 to -55dB) to check if anything quiet is hiding in there:

```bash
ffmpeg -i raw.wav -ss START -t DURATION -af "silencedetect=noise=-55dB:d=0.2" -f null -
```

If it's genuinely silent even at that sensitivity, it's just a long thinking pause —
compress it like any other gap, don't treat it as a mistake.

---

## 3. Check for blow-outs and clicks

**Clipping check** (run once over the whole file):
```bash
ffmpeg -i raw.wav -af astats -f null - 2>&1 | grep "Peak level dB"
```
Anything approaching 0dBFS is a blow-out risk worth flagging.

**Click check:** this is hard to do reliably without actually hearing the audio.
The method that works reasonably well:
1. Get a continuous per-frame peak trace across the whole file (~20-40ms windows,
   via `astats` + `asetnsamples`, NOT by trimming into small clips with `-ss`/`-t`
   per-window — cutting into arbitrary sample windows introduces artificial
   discontinuities/pops at the cut boundary that get mistaken for real clicks).
2. Cross-reference peak spikes against the transcript's silence gaps — a genuine
   click will spike during a moment that should otherwise be quiet.
3. **Before cutting anything, check whether the spike is actually a word onset**
   (a consonant like a plosive or sibilant can produce the same kind of brief
   broadband spike a click does). Compare the spike's timestamp against where the
   next transcribed word starts.
4. Be upfront that this can't fully replace the person's own ears — flag any
   candidate spikes, explain the false-positive risk, and if it's ambiguous, don't
   cut it.

---

## 4. Trim silence — ⚠️ threshold matters a lot

This is the step most likely to go wrong. Two settings control it:
- **Threshold** (dB level below which audio counts as "silence")
- **Minimum duration** (how long it must stay below that level to count)

### The mistake to avoid
A trailing fricative consonant (S, F, TH) is genuinely quieter than a vowel —
typically sitting around **-25 to -40dB** — while true room-tone silence in a decent
mic setup usually doesn't hit bottom until **-60dB or lower**. If the silence
threshold is set too high (e.g. -20dB, which sounds reasonable but isn't), the
detector catches the *tail end of the word itself* as silence and cuts into it —
producing dropped final consonants ("template" → "templar" losing its S, etc).

**Confirmed by direct measurement**: sampling the amplitude envelope in ~10ms steps
across a word ending in a fricative showed the consonant sustaining around -25 to
-40dB for several hundred ms before actually reaching the true noise floor.

### Settings that worked reliably
```bash
ffmpeg -i raw.wav -af "silencedetect=noise=-45dB:d=0.3" -f null - 2>&1 | grep -i silence
```
- **Threshold: -45dB** (safely below where consonant tails decay to, comfortably
  above true room noise)
- **Minimum duration: 0.3s** (only flags gaps that are actually pauses)
- **Truncate target: 0.25s** (compress any qualifying gap down to this length,
  removing time symmetrically from the middle of the gap so a small buffer is kept
  on both sides — never cut flush against the detected boundary)

If someone gives you settings from another tool (e.g. Audacity's Truncate Silence,
which might reasonably use -20dB), don't assume they transfer directly — different
tools measure/smooth the signal differently. If in doubt, verify empirically:
sample the amplitude trace around a word ending in a fricative and confirm the
chosen threshold sits below the consonant's decay range.

### Compressing a gap (in Python, given a detected silence_start/silence_end)
```python
TARGET_GAP = 0.25
half = TARGET_GAP / 2
if (silence_end - silence_start) > TARGET_GAP:
    cut_start = silence_start + half
    cut_end = silence_end - half
    # remove [cut_start, cut_end], keep the rest of the gap as a buffer
```
Apply a similar but distinct rule for the very start (small lead-in, e.g. 0.25s)
and very end (slightly longer trail-out, e.g. 0.3s) of the file.

---

## 5. Cutting audio+video in sync

Build a list of "keep" segments (the complement of everything cut: hard retake cuts
+ silence compressions), then encode each segment individually and concatenate —
this is far more memory-stable in a constrained environment than one giant
`filter_complex` graph with dozens of trim branches (which can OOM-kill ffmpeg).

```bash
# Per segment (repeat for each keep-range):
ffmpeg -y -ss START -i INPUT.mp4 -t DURATION \
  -c:v libx264 -crf 18 -preset veryfast \
  -c:a aac -b:a 192k \
  -avoid_negative_ts make_zero \
  seg_NNN.mp4

# Then concatenate:
ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy output.mp4
```

If encoding many segments in one go times out, batch it (e.g. 25-30 at a time) and
resume — check for zero-byte/tiny output files afterward (a sign a segment got cut
off mid-encode) and re-encode just those before concatenating.

If the video track is disposable, skip all of this video-handling complexity — just
cut the audio and drop the video entirely (or keep a simple pass-through), and output
audio in whatever container is requested (an audio-only .mp4/.m4a works fine for
most NLEs).

---

## 6. Loudness — measure, don't blindly normalize

**Don't use `loudnorm` to apply the correction directly** — even its "linear" mode
can audibly dull high-frequency detail in ways that aren't easily explained by the
target numbers (confirmed by A/B testing: a loudnorm pass measurably lost ~40% of a
clip's zero-crossing rate — a proxy for high-frequency content — that a plain gain
adjustment of the same size did not). Loudnorm is fine as a *measurement* tool; don't
trust it as the *processing* step.

**Correct approach — measure, then apply plain gain:**
```bash
ffmpeg -i raw.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null -
```
This reports `input_i` (integrated loudness) and `input_tp` (true peak) without
altering anything. From there:

1. Target is usually -16 LUFS integrated for spoken-word YouTube content.
2. Gain needed to reach that target = `-16 - input_i`.
3. Gain allowed before true peak exceeds -1.5dBTP = `-1.5 - input_tp`.
4. **Use whichever is smaller.** True peak is very often the binding constraint —
   landing a bit quieter than -16 LUFS (e.g. -18 to -20 LUFS) with a clean, safe
   peak is a better outcome than hitting -16 LUFS exactly and risking distortion or
   coloration.
5. Apply as a plain filter, nothing fancier:
   ```bash
   ffmpeg -i input.mp4 -c:v copy -af "volume=X.XdB" -c:a aac -b:a 192k output.mp4
   ```
6. Re-measure the output with the same `loudnorm` print_format=json call to confirm
   the final numbers are safe before delivering.

Don't apply noise reduction unless something is actually broken (background hiss,
audible hum) — a clean recording doesn't need it, and aggressive `afftdn` settings
(especially a `noise_floor` set high/less-negative, like -25 instead of the -50
default) can also dull high-frequency detail the same way loudnorm can. If the
person specifically says "only fix blow-outs and clicks, don't touch anything else,"
respect that — don't run a blanket cleanup pass "just in case."

---

## 7. Deliver a change note every time

For each processed file, write a short markdown note covering:
- Original vs. new duration
- Every retake found: rough timestamp, what was cut vs. kept, and *why* (what in the
  script confirms it)
- Anything checked but deliberately **not** cut, and why (recurring scripted content,
  long-but-genuinely-silent pause, ambiguous stumble flagged for the person to
  confirm)
- Blow-out/click check result
- What loudness/gain was applied and the before/after numbers
- A short "worth a spot-check" list — point at the riskiest edits specifically
  (a big multi-take cut, a place where the wording shifted between takes) rather
  than asking for a blanket re-listen to everything

This is the person's QA checklist — the point is to let them spot-check a few
specific places instead of re-listening to the entire file.

---

## 8. Honest limits — say so, don't guess past them

- There's no ability to actually *listen* to the audio — only amplitude/spectral/
  transcript analysis. Say this plainly when it's relevant (e.g. click detection,
  judging whether a pause "feels" natural).
- When two automated checks disagree, or the transcript is unreliable, flag it
  rather than picking an answer with false confidence.
- If a fix requires a setting borrowed from a tool that works differently
  internally (like the Audacity threshold example above), verify empirically rather
  than assuming a 1:1 transfer.
- If something goes wrong (like the -20dB fricative-clipping bug), explain the root
  cause plainly when asked, not just "it's fixed now."
