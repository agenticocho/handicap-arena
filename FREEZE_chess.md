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

### 2b. CROSS-MACHINE — this series is CONFIG-specific, and both boxes agree to the centipawn

The table above is **Jarvis, `Threads=1, Hash=16`** — a measurement, not a property of chess, and not to be
quoted as one. Ocho re-measured kiwipete on **Chilly** (same engine asset, Stockfish 19) and reported a
different *shape*, which is what prompted this section. It does not survive the parity rule:

    Chilly, reported as "Threads=1, depths 8..20":  -172  -196  -213  -255  -274   reported MONOTONE
    Jarvis, Threads=1, Hash=64, same five depths:   -172  -196  -213  -255  -274   identical
    Jarvis, Threads=1, Hash=16, same five depths:   -172  -196  -213  -228  -215   NOT monotone

**Every one of Chilly's five numbers is Jarvis's number, under `Hash=64`.** Measured here — same engine,
one field at a time, kiwipete at depth 18, two runs per arm (spread 0 unless stated):

    declared default (no configure)   ('d5e6', -228) x2     = Chilly's "default Threads"     -228
    Threads=1, Hash=16                ('d5e6', -228) x2
    Threads=1, Hash=64                ('d5e6', -255) x2     = Chilly's Threads=1 + Hash=64   -255
    Threads=8, Hash=16                ('e2a6', -301) ('e2a6', -312)   spread 11 cp
    Threads=8, Hash=64                ('e2a6', -263) ('e2a6', -313)   spread 50 cp

So:

- **The oracle does NOT differ across the two boxes.** At matched configuration it agrees to the
  centipawn — on *both* of Chilly's arms. The 27 cp was attributed to `Threads` and it is **`Hash`'s**:
  the two arms in that message differed in two fields at once, and the field that moved was `Hash` (16 to 64).
- **"Depth-monotonicity is a property of the machine" is therefore not supported.** It is a property of the
  *configuration*, and it reproduces machine-independently.
- **The MONOTONE reading is a sampling artifact.** The five sampled depths (8/12/16/18/20) skip d14 and d22.
  With `Hash=64` on Jarvis the full series is `-172, -188, -196, -244, -213, -255, -274, -270` — **not
  monotone**: `+31` at d14->d16 and `+4` at d20->d22, and the same `-48` dip at d14 the §2 table shows at
  `Hash=16`. The verdict still converges by d12; the score still never settles. **That was a fact about the
  engine and the depth, not about this machine.**

**What stands is sharper than either of us had it:** the score is moved by *both* undeclared settings —
`Hash` 16->64 shifts it 27 cp deterministically (13.5% of the card's 200 cp grey band, and decisive at the
edge: -290 is grey under one and -317 is LOST under the other), while `Threads` 1->8 both shifts it
(44-84 cp) AND destroys reproducibility (spread 11-50 cp, best move flipping to `e2a6`). The four-field
record, and comparison **only at matched fields**, is exactly what the cross-machine run needs.

## 3. Why this bites chess specifically

Chess was kept as the calibration event because *calibration is a GRADIENT — confidence against the truth —
and only chess can measure a gradient.* **The yardstick is itself depth-dependent: the score never settles
and the drift reverses sign (§2b: re-measured across two configurations and two boxes — that shape is the
engine's and the depth's, not one machine's; the *score* moves with `Hash` as well, the *verdict* does not).
An undeclared depth is therefore a gradient measured against a moving stick.**

Where the oracle is a fact, and where it is not:
- **"was this the best move?"** — a FACT from depth 12. Stable, reproducible, cheap.
- **"how lost was the model?"** — NOT a fact at any depth. It is a *declared scale*, and the declaration is
  what makes it comparable. **That is not a defect; it is the definition.** An *undeclared* one is the
  defect: a model graded at d8 and one graded at d22 differ by 78 cp with nothing recording it.

## WHAT THE FREEZE MUST RECORD — all four, or the event is not placeable

    engine identity    Stockfish 19                 a different version is a different oracle
    config             Threads=1, Hash=16          without this the answer is not reproducible --
                                                     and BOTH settings move the score (§2b): Hash
                                                     by 27 cp, Threads by 44-84 cp plus the spread
    depth              DECLARED -- and carried in the record, not in a document
    the box            the freeze is a HARDWARE fact, so Jarvis's and Chilly's are comparable only
                       if all four fields match -- and §2b shows what that buys: at matched
                       fields the two boxes agree to the centipawn, and every apparent
                       disagreement so far was an undeclared field, not a different machine

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
