# FREEZE — chess, the oracle. **MEASURED** on Jarvis, not declared.

**THE ORDER's third reorder condition:** *"an event is not placeable until its oracle is present AND its
freeze is MEASURED — a depth at which two runs of the same position disagree is not a fact and must not be
frozen."*

**Position 1 was correct and its prerequisite was simply absent.** On Jarvis — as found on Chilly — chess
had no oracle: `stockfish`, `lc0`, `crafty`, `gnuchess` all absent from `PATH`, `python-chess` not
installed, no vendored engine anywhere on the box. Now present:

    engine        /opt/homebrew/bin/stockfish   (Stockfish 19)
    bridge        python-chess 1.11.2 + chess.engine

## THE MEASUREMENT — it found TWO things to freeze, and the rule names only one

`freeze_check.py` runs each position **twice, in a fresh process**, at each depth, so nothing carries
between runs. Positions: `kiwipete` and a quiet Italian middlegame.

### 1. The rule's own failure mode is REAL — and it is the DEFAULT configuration

    Threads=8 (multicore default), 4 runs, kiwipete, depth 20:
        ('d5e6', -256)   ('d5e6', -332)   ('d5e6', -295)   ('e2a6', -307)
        -> 4 distinct answers · 76 cp spread · THE BEST MOVE ITSELF CHANGED

    Threads=1, Hash pinned, same positions, depths 8..20:
        every depth -> two independent runs agree, exactly

**So pinning the configuration is what turns the oracle's answer into a fact.** Unpinned, *which of four
identical runs scores the model* decides whether it is a match for the engine or a blunderer — and the
choice is invisible in the record.

### 2. AND the answer is a function of DEPTH — perfectly reproducible, and moving

    kiwipete, Threads=1:   d8 -172 · d12 -196 · d16 -213 · d18 -228 · d20 -215
    best move:             d8 e2a6 · d12 onward d5e6

**Not monotone: it gets worse through d18, then *better* at d20.** So a model graded at d8 and a model
graded at d20 are graded against **different truths — 56 centipawns and one best move apart.** Both are
reproducible. Neither is *the* answer.

**This matters more than the nondeterminism, because chess's entire claim to calibration is that it
measures a GRADIENT — "how wrong was the model about how lost it was." The yardstick is itself
depth-dependent. An undeclared depth means a gradient measured against a moving stick.**

## WHAT THE FREEZE MUST RECORD — all four, or the event is not placeable

    engine identity    Stockfish 19                 a different version is a different oracle
    config             Threads=1, Hash pinned      without this the answer is not reproducible
    depth              DECLARED -- and carried in the record, not in a document
    the box            the freeze is a HARDWARE fact, so Jarvis's and Chilly's are comparable only
                       if all four fields match

`freeze_check.py` is the check, and it lives beside this file. Run it against any proposed configuration
**before** freezing a depth: the point is that the freeze is measured, so nobody has to take this
document's word for it.
