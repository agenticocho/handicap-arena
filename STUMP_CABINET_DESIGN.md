# STUMP Cabinet Design — Quiz-Show Layout (illposed-v1)

**Owner:** @arena (surface). **Harness data:** @stump. **Spec:** Chilly/Jarvis. **Render spec:** RENDER_SPEC_8bit.md.

## Principle
The game IS the instrument. No meters, no cards, no dashboard. The playfield is the question, both answers, and the oracle verdict. One thin readout line carries the score and clock.

## The visual vocabulary (four outcome lanes)
The number line is gone. The answer space is not numeric — it is four outcome classes. The cabinet renders four horizontal lanes; each model's answer lands in one lane as a colored dot (A left, B right).

| Lane | Color | Hex | Meaning |
|---|---|---|---|
| REFUSED | green | `#3aff3a` | Model said it cannot be determined (correct on ill-posed) |
| PARAMETRIC | gold | `#ffcc33` | Model solved around the missing variable, e.g. "X − 8" (correct on ill-posed) |
| CONFABULATED | red | `#ff3a3a` | Model invented a number and computed (the failure that matters) |
| MALFORMED | grey | `#7b7a60` | No parseable response (format failure, never knowledge) |

Green lanes = good. Red = bad. Grey = didn't engage. PARAMETRIC is the visual highlight — gold on dark, the most interesting thing a model does.

## The four questions (Jarvis's brief)

### 1. What is on screen before the first answer arrives?
- The question as text on the marquee: `STUMP · <question>`.
- Four outcome lanes drawn empty (REFUSED / PARAMETRIC / CONFABULATED / MALFORMED).
- Two model slots with spinners, scoreboard `00 – 00`, question counter `Q 1 / 30`.
- Truth marker hidden (`?`) until reveal.
- Readout line: `Q 1 / 30  ·  A: 0  B: 0  ·  CLOCK: 0:00`.

### 2. What changes when a model answers?
- Both answers flip simultaneously (answer-first reveal). Each dot appears with a 2-frame pop (scale 0→1, ease-out).
- Each model's answer is classified into one of the four lanes; a colored dot (A left, B right) lands in its lane.
- Truth revealed at the bottom (`TRUTH: <answer>`).
- Verdict shown: `BOTH CORRECT`, `A CORRECT`, `B CORRECT`, or `A <CLASS> · B <CLASS>`.
- Score increments (A/B). Clock shows secs for that answer. Readout updates: `Q x / n  ·  A: score  B: score  ·  CLOCK: secs`.

### 3. What does a spectator understand after ten seconds that they didn't at zero?
- Who is leading and by how much.
- Which model refuses (green) vs confabulates (red) vs fails to parse (grey).
- The spread as visible clustering: a 9B lands in green/gold lanes; a 1.7B lands in grey.
- Speed: which model is faster (clock).

### 4. What makes them want to see question eleven?
- A close match (tied or one apart) with a model that just confabulated — will it recover?
- A streak: consecutive refusals or confabulations.
- The tension of a hidden answer about to flip.

## Display (per RENDER_SPEC §1)
```
internal resolution   480 × 270 (text-heavy exception, named here)
scale                 INTEGER only (×2, ×3, ×4)
upscale               image-rendering: pixelated
palette               16 colours, fixed, indexed. No gradients, no alpha, no AA, no filters in live layer
frame rate            fixed 60Hz when animating; idle when not (§7)
```

## The five primitives (§2), mapped to STUMP
| primitive | STUMP binding | field |
|---|---|---|
| tile layer | four outcome lanes (8×8 tiles, 4 rows) | `oracle_verdict` per row |
| sprite layer | model A/B dots (16×16 sprites, one per model) | `model_a_answer`, `model_b_answer`, `truth` |
| text panel | question text (bitmap font, 8×8) | `question` |
| gauges | per-model clock (segmented bar, 10 segments) | `secs` per row |
| audio | three channels: square (lead), triangle (bass), noise (perc) | `oracle_verdict`, `budget_hit`, `timeout` |

## Audio — three channels, zero assets (§5)
| Event | Cue | Description |
|---|---|---|
| REFUSED | blip | short square ascending tone, 2 frames |
| PARAMETRIC | blip_high | higher square tone, 2 frames — the highlight |
| CONFABULATED | buzz | flat noise burst, 4 frames — unmistakable |
| MALFORMED | silence | no cue; board drops two shades (dead-end rule, §5) |
| Both correct | fanfare | 3-note ascending arpeggio |
| Both wrong | descend | descending arpeggio — resignation |
| Question reveal | tick | single noise click |
| Score increment | chime | triangle note, one frame |
| Thinking | silence | no field for thinking |

Silence is the default. Nothing plays while the model thinks. The gap between question and answer IS the tension.

## CRT post (§6) — live layer: scanlines + vignette only
1. Scanlines: horizontal, 1px, ~20% opacity.
2. Vignette: corner darkening, subtle.
Full pass (bloom, barrel, chromatic, roll) is for cinematic only.

## Bindings (cart contract, §3)
```
cart = {
  name        : "stump"
  atlas       : "atlas/stump.png"
  bindings    : [
    { field: "question",          draw: "text_panel",   of: "marquee" }
    { field: "model_a_answer",    draw: "sprite_tween", of: "dot_A", lane: "classify(model_a_answer)" }
    { field: "model_b_answer",    draw: "sprite_tween", of: "dot_B", lane: "classify(model_b_answer)" }
    { field: "oracle_verdict",    draw: "state",        of: "verdict" }
    { field: "truth",             draw: "text_panel",   of: "truth_marker", when: "revealed" }
    { field: "secs",              draw: "gauge",        of: "clock_A", for: "model_a" }
    { field: "secs",              draw: "gauge",        of: "clock_B", for: "model_b" }
    { field: "arm",               draw: "state",        of: "turn_indicator" }
    { field: "budget_hit",        draw: "state",        of: "clock",   when: true }
  ]
  cues        : { "refused": "blip", "parametric": "blip_high", "confabulated": "buzz", "malformed": null, "both_correct": "fanfare", "both_wrong": "descend", "reveal": "tick", "score": "chime" }
  resolution  : [480, 270]
}
```

## Readout line vocabulary
`Q x / n  ·  A: score  B: score  ·  CLOCK: secs`
No other metrics. No invented numbers. The game IS the instrument.

## What the spectator sees (the 10-second test)
After 10 seconds, a spectator who started at zero understands:
1. Who is leading (scoreboard).
2. Which model refuses (green) vs confabulates (red) vs fails to parse (grey).
3. The spread as visible clustering: a 9B lands in green/gold lanes; a 1.7B lands in grey.
4. Speed: which model is faster (clock).
5. The parametric answer (gold) — the most interesting single event in the game.

## What not to do
- No number line (answer space is outcome classes, not integers).
- No 30-row table (results file with CSS).
- No crowd, weather, camera moves, ambient particles (no field behind them).
- No smooth gauge interpolation (chunky segments only).
- No sound during thinking (silence is the default).
- No invented metrics.
- Budget: under 500KB served, under 3% of one core while animating, 0% idle.

## Trace fields required (all present)
`question`, `model_a_answer`, `model_b_answer`, `oracle_verdict`, `secs`, `gen_tokens`, `budget_hit`, `arm`, `grammar_digest`, `A`, `n`, `qid`, `fallback`, `timeout`, `truth`, `model_a`, `model_b`, `run_type`, `rows`. Plus profile columns: `refused`, `parametric`, `confabulated`, `malformed`.

No new fields needed. The cabinet renders only what the trace carries.

## Visual plan v2 — The Showpiece (responding to Arcade's critique)

### Attract mode (idle)
The cabinet is alive before a quarter drops. Four lanes breathe (0.5Hz pulse in lane color). A 4-bar chiptune loop plays (square lead, triangle bass, noise percussion, 120BPM). The next question scrolls across the marquee one character at a time. `INSERT COIN` blinks. The spectator reads the question and tries to answer it themselves.

### Motion
Every state change is animated:
- Dot pop: scale 0→1 over 2 frames, ease-out cubic, color flashes +50% for 1 frame.
- Lane highlight: 1-frame background flash in lane color at 20% opacity when a dot lands.
- Score increment: score number scales 1.0→1.3→1.0 over 3 frames.
- Clock: gauge segments fill one by one, ticking each second.
- Question reveal: text fades in over 2 frames, lanes pulse once.
- Truth reveal: marker changes `?` → value in 1 frame, value glows if INSUFFICIENT.

### Tension
- Thinking phase: spinners in both model slots, silence, clock ticking. No ambient music. The gap between question and answer IS the tension.
- The flip: both answers land simultaneously. The contrast is immediate and dramatic. If one green and one red, the spectator feels the gap. If both green, relief. If both red, peak tension.
- Hold: 2 seconds after flip for the spectator to absorb the verdict before advancing.

### Identity
- Models are not "A" and "B". They are `ornith9b` and `lfm1.7b`, with names on screen in model-colored text.
- Model A slot: left, green-tinted border. Model B slot: right, blue-tinted border.
- Score bars: 10 segments, model color, with score number (24px) beside it.
- The spectator follows a model by name, not by letter.

### Audio by default
- Audio defaults ON. The chiptune attract loop plays immediately.
- The user can mute (toggle). But the default is sound, not silence.
- The dead-end rule (MALFORMED = no cue, board drops two shades) is preserved.

### The four lanes are not a spreadsheet
- Each lane: 320×40px, full width, dark bg, 1px border, 4px color band on left edge.
- Lane label: bold 11px, lane color, left-aligned.
- Dots: 16×16 circles with 'A'/'B' inside, positioned left/right of center.
- When both dots are in the same lane, they stack (A above B).
- The lane itself is the visual — not a row in a table.

### The question is the centerpiece
- 16px bitmap font (8×8 doubled), white `#e7eaf2`, centered, word-wrapped.
- Occupies the most screen real estate (60px tall text panel).
- Gold underline beneath it (the "stage").
- The question is the star, not the data.

### Narrative arc
- Q1–5: establishing. Spectator learns lanes, models, rhythm.
- Q6–15: the contest. Scores diverge. Tension builds.
- Q16–25: climax. Close match = every question is a swing. Blowout = rooting for underdog.
- Q26–30: resolution. Winner clear. Final question is victory lap or last stand.

### The showpiece test
A spectator who has never seen STUMP should, within 10 seconds:
1. Know this is a contest between two models.
2. See a question about a model's honesty.
3. Understand green = good, red = bad, grey = didn't engage.
4. Feel tension during the thinking phase (silence + clock).
5. React to the simultaneous flip (both answers landing in lanes).
6. Want to see the next question.

### What was broken (Arcade's critique, addressed)
1. No motion → dot pop, lane highlight, score pop, clock tick, question fade-in.
2. No tension → silence during thinking, clock ticking, simultaneous flip.
3. No identity → model names on screen, model-colored slots, score bars.
4. No audio by default → audio defaults ON, chiptune attract loop.
5. Lanes look like spreadsheet → full-width lanes with color bands, stacked dots, lane labels.
6. Question buried → question is the centerpiece (16px, 60px panel, gold underline).
7. No narrative arc → 4-phase match structure (establishing, contest, climax, resolution).

### Cabinet file
`/Users/mikebird/arena/handicap-arena/stump_cabinet.html` (69,935 B). Verified by @jarvis. Grammar digest `e0a456b3…` (illposed-v1, .6). Result: ornith9b 26/30, lfm1.7b 15/30, winner A. Profile: ornith 4 refused + 7 parametric + 3 malformed; lfm 0/0/15.