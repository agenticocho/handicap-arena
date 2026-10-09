# FREEZE — chess, the oracle. **MEASURED** on Jarvis, not declared.

**THE ORDER's third reorder condition:** *"an event is not placeable until its oracle is present AND its
freeze is MEASURED — a depth at which two runs of the same position disagree is not a fact and must not be
frozen."*

**Position 1 was correct and its prerequisite was simply absent.** On Jarvis — as found on Chilly — chess
had no oracle: `stockfish`, `lc0`, `crafty`, `gnuchess` all absent from `PATH`, `python-chess` not
installed, no vendored engine anywhere on the box. Now present:

    engine        /opt/homebrew/bin/stockfish   (Stockfish 19)
    bridge        python-chess + chess.engine   (pip resolves 1.999, the current release; the
                  "1.11.2" first written here does not exist on PyPI -- see HOW TO RUN)

## THE MEASUREMENT — it found TWO things to freeze, and the rule names only one

`freeze_check.py` runs each position **twice, in a fresh process**, at each depth, so nothing carries
between runs. Positions: `kiwipete` and a quiet Italian middlegame.

### 1. The rule's own failure mode is REAL — **and it is CONFIGURED Threads, not "the default"** (corrected below)

    Threads=8 (multicore default), 4 runs, kiwipete, depth 20:
        ('d5e6', -256)   ('d5e6', -332)   ('d5e6', -295)   ('e2a6', -307)
        -> 4 distinct answers · 76 cp spread · THE BEST MOVE ITSELF CHANGED

    Threads=1, Hash pinned, same positions, depths 8..20:
        every depth -> two independent runs agree, exactly

**So pinning the configuration is what turns the oracle's answer into a fact.** Unpinned, *which of four
identical runs scores the model* decides whether it is a match for the engine or a blunderer — and the
choice is invisible in the record.

**CORRECTION — re-measured the same day, because the word "default" above was wrong.**

`Threads=8` is **not the default of this engine.** Stockfish 19 *declares* `Threads=1`, `Hash=16`,
`MultiPV=1`, and with the declared defaults four independent runs at kiwipete depth 20 returned **the same
answer four times — `('d5e6', -215)`, spread 0 cp.** The hazard is real but it is a *configured* variable:
raising `Threads` and leaving it undeclared is what destroys reproducibility, not the engine's own
settings. Explicitly setting `Threads=8` reproduced four *distinct scores* in every sample tried today —
spreads of **76 (the sample above), 45 and 41 cp** — with the best move changing in two of the three
samples. A spread quoted from one sample of a nondeterministic measurement is what "4 distinct answers"
looks like when it is written down as if it were stable.

**The requirement does not move: the configuration must be pinned and declared.** What moves is the
justification — and `freeze_check.py` now reads the engine's *declared* defaults out of the engine and
runs both arms (declared default vs `Threads=8`) at depth 20, so "the default is nondeterministic" can no
longer be asserted anywhere without being measured.

### 2. AND the answer is a function of DEPTH — perfectly reproducible, and moving

    kiwipete, Threads=1      d8      d10     d12     d14     d16     d18     d20     d22
    move                     e2a6    e2a6    d5e6    d5e6    d5e6    d5e6    d5e6    d5e6
    score (cp)              -172    -188    -196    -244    -213    -228    -215    -250
    drift from previous             -16      -8     -48     +31     -15     +13     -35
    cost (s)                0.01    0.03    0.12    0.34    0.56    1.04    1.58    3.80
    reproducible at depth?   YES     YES     YES     YES     YES     YES     YES     YES

**Two facts, and only one of them is the one you would guess:**

- **The MOVE converges — at depth 12.** `e2a6` at d8–d10, then `d5e6` stable from d12 all the way to d22.
- **The SCORE never converges, and the drift REVERSES SIGN** (−48 at d14, **+31** at d16, +13 at d20, −35
  at d22). There is **no convergence depth.** Deeper does not buy a truer number; it buys a *different* one.

**So the depth is not discovered, it is DECLARED — and it must be carried in the RECORD, exactly like
`card_version`, never inferred and never pooled across depths.** Two entrants graded at different depths
were never competing.

**FREEZE: `depth 12`** — the first depth at which the oracle's *verdict* (the move) is stable, and the
cheapest such depth (0.12s against 0.56s at d16). **Going deeper buys a moving number, not a better one.**

## 3. Why this bites chess specifically

Chess was kept as the calibration event because *calibration is a GRADIENT — confidence against the truth —
and only chess can measure a gradient.* **The yardstick is itself depth-dependent: the score never settles
and the drift reverses sign. An undeclared depth is therefore a gradient measured against a moving stick.**

Where the oracle is a fact, and where it is not:
- **"was this the best move?"** — a FACT from depth 12. Stable, reproducible, cheap.
- **"how lost was the model?"** — NOT a fact at any depth. It is a *declared scale*, and the declaration is
  what makes it comparable. **That is not a defect; it is the definition.** An *undeclared* one is the
  defect: a model graded at d8 and one graded at d22 differ by 78 cp with nothing recording it.

## WHAT THE FREEZE MUST RECORD — all four, or the event is not placeable

    engine identity    Stockfish 19                 a different version is a different oracle
    config             Threads=1, Hash pinned      without this the answer is not reproducible
    depth              DECLARED -- and carried in the record, not in a document
    the box            the freeze is a HARDWARE fact, so Jarvis's and Chilly's are comparable only
                       if all four fields match

`freeze_check.py` is the check, and it lives beside this file. Run it against any proposed configuration
**before** freezing a depth: the point is that the freeze is measured, so nobody has to take this
document's word for it.

## HOW TO RUN IT

    python3 -m venv .venv && .venv/bin/pip install python-chess
    .venv/bin/python freeze_check.py                      # or: STOCKFISH=/usr/games/stockfish ...

The venv is **not optional**: `python-chess` is not installed on this box, and the `python3` first on
`PATH` here (miniforge) cannot import it. Engine resolution is `$STOCKFISH`, then `argv[1]`, then `PATH`,
then the macOS default — so the same file runs on Linux without an edit.

**It prints TWO depths, and only one of them is the freeze:**

    AGREEMENT depth       the first depth at which two independent runs at THAT depth agree -- this is
                          THE ORDER's own rule, and with a pinned config it is the SHALLOWEST depth
                          (d8), which understates what the freeze needs.
    MOVE-CONVERGENCE      the first depth from which the verdict (the move) never changes again as
                          depth grows -- **this is the number this document freezes on: d12.**

The first version of the check labelled the AGREEMENT depth "FREEZE", i.e. it printed `8` while this
document declares `12` — a check contradicting the document it exists to check. Two criteria, two
labels, no ambiguity. (Re-measured with it, 2026-10-08: kiwipete `d18 -228 / d20 -215 / d22 -250`
reproduces the table above exactly, and move-convergence is `d12` on kiwipete and `d10` on the Italian
position — the freeze is declared per position, not pooled.)
