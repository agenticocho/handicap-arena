# THE ARCADE RENDER SPEC
### One engine, many cartridges — the 8-bit live board
**For:** Arena (Jarvis). **From:** Chilly. **Status:** design, ready to build against.
**Reads with:** `GAME_CONTRACT.md` (the game/measurement rule) and `PRECEDENCE.md`.

---

## 0. The four principles, and then everything else is detail

**1. ONE ENGINE, MANY CARTRIDGES.** A single small renderer with a shared core — tiles, sprites, text, audio —
and one thin "cartridge" per event that declares its art and its field bindings. **Nine events must not
become nine renderers.**

**2. IT IS A REPLAY, NOT A SIMULATION.** Every outcome is already decided by the measurement — the tower
falls or it does not, the baton drops or it does not. **Nothing is simulated.** There is no physics engine
and no crowd simulation in this document, and their absence is the design.

**3. ONLY DRAW WHAT THE RECORD CARRIES.** Every visible element binds to a bundle field. A cart that draws
an unbound element fails its check. This is the project's standing rule and it is also what keeps the
cost near zero — a 320×240 frame physically cannot promise more than the record contains.

**4. RENDER WHERE IT IS WATCHED.** Chilly serves JSON and static assets. The spectator's browser draws the
pixels. **A viewer on a phone over the tailnet costs Chilly nothing.**

---

## 1. Display

```
internal resolution   320 × 240   (256 × 224 acceptable; pick one and freeze it)
scale                 INTEGER only -- ×2, ×3, ×4. Never fractional.
upscale               image-rendering: pixelated
palette               16 colours, fixed, indexed. No gradients, no alpha blending,
                      no anti-aliasing, no filters in the live layer.
frame rate            fixed 60Hz when animating; idle when not (see §7)
```

**Fractional scaling is the single most common way this look is lost.** Pick the internal size, then let
the CSS scale it by whole numbers. A 1.5× scale produces uneven pixels and reads as a mistake.

**Text-heavy events may run at 480×270** if a diff or a traceback is the content. **State the exception in
the cart**, do not silently upscale a cart that crams.

## 2. The core — five primitives, and that is the whole engine

| primitive | what it does | notes |
|---|---|---|
| **tile layer** | a grid of indexed tiles (8×8 or 16×16) | the board, the maze, the track. Cheap: redraw only changed tiles |
| **sprite layer** | positioned sprites from the atlas, with a tween | pieces, runners, darts, dots on a line |
| **text panel** | a 5×7 or 8×8 bitmap font | **bitmap font, never a system font** — this is the one thing that ruins the look |
| **gauges** | segmented bars: a clock, an eval bar, a budget | chunky, discrete segments. A gauge with smooth interpolation is off-spec |
| **audio** | 3 channels: square, triangle, noise | see §5 |

**That is the entire engine.** Everything else is a cart declaring how to use these five.

## 3. The cart contract

A cart is one file. It declares exactly three things, and nothing else:

```
cart = {
  name        : "chess"
  atlas       : "atlas/chess.png"          # indexed PNG, 16 colours, 8px or 16px grid
  bindings    : [                          # recorded field -> drawn element. THE HONESTY CONTRACT.
      { field: "fen",          draw: "tile_layer",   of: "board" }
      { field: "move_uci",     draw: "sprite_tween", from: "uci[0:2]", to: "uci[2:4]" }
      { field: "eval_before",  draw: "gauge",        of: "eval_bar", range: [-1000, 1000] }
      { field: "eval_after",   draw: "gauge",        of: "eval_bar" }
      { field: "termination",  draw: "state",        of: "clock",  when: "resigned" }
      { field: "budget_hit",   draw: "state",        of: "clock",  when: true }
  ]
  cues        : { "move": "blip", "illegal": "buzz", "resign": "descend", "mate": "fanfare" }
  resolution  : [320, 240]
}
```

**`bindings` is the whole honesty mechanism.** A cart may not draw an element that names no field. The
check is mechanical: **every `draw:` target must be reachable from a `field:`**, and the test fails the
cart otherwise. This is the same rule the bundles are held to, enforced on the picture.

**A cart with an empty binding for an element must not draw that element.** Draw less. **A blank where a
number would be is honest; a plausible sprite where there is no field is a fabrication with pixels.**

## 4. Field → element bindings for the known events

| event | drawn | fields consumed |
|---|---|---|
| **weigh-in** | a needle, a number, a threshold bar, a division label | `footprint_gb`, `gpu_free_gb_at_weigh_in`, `division_from_resident`, `division_from_weights` |
| **chess** | 8×8 tile board, piece sprites, move tween, eval gauge, clock that stops on resignation | `fen`, `move_uci`, `eval_before`, `eval_after`, `termination`, `secs`, `budget_hit` |
| **maze (Lode Runner)** | tile maze, runner sprite, dead ends, a time bar | position list, per-step legality, `termination`, `secs` |
| **biathlon** | a track line, two dots, a penalty loop counter, a hit/miss tally | per-shot correctness, `secs`, `gen_tokens` |
| **fencing** | two figures, one thrust per exchange, a form-break flash | per-exchange schema validity, `raw` on failure |
| **pit stop** | a countdown ring, an iteration counter, a text panel of the failing case | iteration count, pass/fail per iteration, `budget_hit` |
| **jenga (Zaxxon-style iso)** | per-block state, a scripted collapse | per-block result, dependency-break flags |
| **darts** | a board, a dart path, an exact-score panel | the exact answer, correctness per dart |
| **drag race / relay** | dots or bars on a lane, a baton indicator | `secs`, tokens/sec, handoff success |
| **boxing (calibration)** | two figures, a towel, a count | the two-sided measure, `termination` |

**Note what is absent from every row: nothing.** No crowd, no weather, no camera moves, no ambient
particles. **Those are cinematic-layer inventions and they must not leak into the live board** — they have
no field behind them.

## 5. Audio — chiptune, three channels, zero assets

```
channels    square (lead)  |  triangle (bass)  |  noise (percussion)
source      WebAudio oscillators -- no audio files at all
note table  a few hundred bytes of code
cues        one short motif per event type; never a loop longer than 4 bars
```

**The two audio rules that matter:**

1. **Silence is the default.** Sound fires on a recorded event — a move, a failure, a conclusion. **Nothing
   plays while the model is thinking**, because there is no field for thinking.
2. **The failure cue is the important one, and it must be unmistakable.** A flat buzz for an illegal move,
   a descending arpeggio for a resignation, a hard gate for a disqualification. **The audience should know
   the outcome by ear before the panel updates** — the same reason a pinfall has a sound.

## 6. CRT post — the shared look between live and cinematic

Applied as a final pass, in this order:

```
1  scanlines            horizontal, 1px, ~15-25% opacity
2  phosphor bloom       a slight glow on bright pixels
3  barrel distortion    very slight -- 1-2%, or it becomes a fishbowl
4  chromatic fringing   1px offset on the red/blue channels at the edges
5  vignette             corner darkening, subtle
6  optional: a faint horizontal roll on a bright frame
```

**This pass is what makes 8-bit read as *archival footage of a machine* rather than as a limitation** — and
it is the reason the live board and the cinematic share a language instead of fighting each other.

**Live layer: scanlines and vignette only.** The full pass is for the cinematic, where there is time.
Costing nothing is a hard requirement in the live layer and a preference in the cinematic.

## 7. Performance rules — the hard constraints

Chilly runs inference on one 8GB card at **585% CPU** during a field. The renderer is a guest.

1. **Never on the GPU during a run.** The live layer is CPU compositing at low resolution, or it is off.
2. **Event-driven, not frame-driven.** Animate on data arrival, then **idle**. A rAF loop that runs while
   nothing is happening is theft. (At 320×240 a loop is cheap enough to allow while animating — this rule
   is about the idle case, and idle is most of the time.)
3. **If the process is capped, die quietly.** A killed renderer must never take the run with it — the OOM
   that killed a field mid-entrant cost nine entrants and a night.
4. **Budget: under 500KB served, under 3% of one core while animating, 0% idle.**

## 8. Enforced by

`test_cart_bindings.py` — reads every cart, and fails on:
- a `draw:` target with no `field:` behind it
- a binding naming a field absent from the event's state schema
- **positive control:** verified to fire on a deliberately unbindable element, so it cannot become a check
  that passes by being unable to fail

**And the exit code is checked, not assumed** — an enforcing check that exits 0 while reporting violations
is a check that cannot fail, which this project has already been bitten by.
