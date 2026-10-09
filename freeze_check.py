#!/usr/bin/env python3
"""Measure -- do not declare -- the depth at which this engine's answer becomes a FACT.

THE ORDER's rule: "an event is not placeable until its oracle is present AND its freeze is
MEASURED -- a depth at which two runs of the same position disagree is not a fact and must not
be frozen."  This runs each position twice at each depth and reports where the two runs agree.

TWO CRITERIA, TWO LABELS -- they give different numbers and this document's freeze uses the second:

  AGREEMENT DEPTH    first depth at which two independent runs AT THAT DEPTH return the same
                     (move, score).  This is THE ORDER's own test; below it the answer is not a
                     fact.  With a pinned config this is normally the shallowest depth tried,
                     because a pinned engine is deterministic -- so on its own it UNDERSTATES the
                     depth the freeze needs.
  MOVE-CONVERGENCE   first depth from which the chosen MOVE never changes again as depth grows.
                     This is what FREEZE_chess.md freezes on (d12): the verdict is stable while
                     the SCORE never settles.

Reporting one number under the label "FREEZE" is how a check and the document it checks end up
contradicting each other (the first version of this file did exactly that: it printed the
AGREEMENT depth, 8, while the document froze 12).

The BOX is one of the four fields the freeze must record, so the header prints it: a result pasted
without it is not comparable with a result from another machine.  The score series is machine-specific
until parity is held field by field -- see FREEZE_chess.md section 2b.

Needs python-chess -- the box's PATH python3 may not have it:
    python3 -m venv .venv && .venv/bin/pip install python-chess
Engine: $STOCKFISH, else argv[1], else PATH, else the macOS default.
Run:    .venv/bin/python freeze_check.py [/path/to/stockfish]
"""
import os
import platform
import shutil
import sys

import chess
import chess.engine

DEFAULT_ENGINE = {"darwin": "/opt/homebrew/bin/stockfish",
                  "linux": "/usr/games/stockfish"}.get(sys.platform, "stockfish")
ENGINE = (os.environ.get("STOCKFISH") or (sys.argv[1] if len(sys.argv) > 1 else "")
          or shutil.which("stockfish") or DEFAULT_ENGINE)

POSITIONS = {
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "italian":  "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
}
DEPTHS = [8, 10, 12, 14, 16, 18, 20, 22]   # covers the table in FREEZE_chess.md
PINNED = {"Threads": 1, "Hash": 16}        # the proposed freeze config
HAZARD = {"Threads": 8, "Hash": 16}        # a config that must not be left undeclared
RUNS = 4                                   # runs per arm in section B
HAZARD_DEPTH = 20                          # the depth FREEZE_chess.md's config finding cites


def one(fen, depth, cfg):
    """One independent run: fresh process, so no hash or state carries between runs."""
    eng = chess.engine.SimpleEngine.popen_uci(ENGINE)
    try:
        if cfg:
            eng.configure(cfg)
        info = eng.analyse(chess.Board(fen), chess.engine.Limit(depth=depth))
    finally:
        eng.quit()
    pv = info.get("pv") or []
    return (pv[0].uci() if pv else None,
            info["score"].pov(chess.WHITE).score(mate_score=100000))


def move_convergence(moves):
    """First depth from which the move never changes again (None if it never settles)."""
    for i in range(len(moves)):
        if all(m == moves[i] for m in moves[i:]):
            return DEPTHS[i]
    return None


def main():
    if not os.path.exists(ENGINE):
        sys.exit(f"engine not found: {ENGINE}\n  set $STOCKFISH, or pass the path as argv[1]")

    print(f"oracle: {ENGINE}")
    print(f"box   : {platform.system()} {platform.release()} {platform.machine()}"
          f" · node {platform.node()} · {os.cpu_count()} logical cores")
    print("id    : ", end="", flush=True)
    e = chess.engine.SimpleEngine.popen_uci(ENGINE)
    print(e.id.get("name"))
    print("declared defaults -- read from the engine, not assumed:")
    for opt in ("Threads", "Hash", "MultiPV"):
        if opt in e.options:
            print(f"      {opt:8} = {e.options[opt].default}")
    e.quit()
    print()

    print(f"A. PINNED config {PINNED}  -- two independent runs per depth")
    print(f"   {'position':10} {'depth':>5}  {'run1 (move, cp)':>22}  {'run2':>22}  agree")
    agreement, convergence = {}, {}
    for name, fen in POSITIONS.items():
        first_agree, moves = None, []
        for d in DEPTHS:
            a = one(fen, d, PINNED)
            b = one(fen, d, PINNED)
            moves.append(a[0])
            ok = a == b
            if ok and first_agree is None:
                first_agree = d
            print(f"   {name:10} {d:>5}  {str(a):>22}  {str(b):>22}  "
                  f"{'YES' if ok else 'NO  <-- not a fact at this depth'}")
        agreement[name] = first_agree
        convergence[name] = move_convergence(moves)

    print()
    print(f"B. WHAT MUST BE DECLARED -- {RUNS} runs at depth {HAZARD_DEPTH}, one position,")
    print("   varying ONLY the configuration.  The engine's own declared default is one arm,")
    print("   because 'the default is nondeterministic' is a measurement, not an assumption.")
    fen = POSITIONS["kiwipete"]
    for label, cfg in (("declared default (no configure)", None),
                       (f"explicit {HAZARD}", HAZARD)):
        res = [one(fen, HAZARD_DEPTH, cfg) for _ in range(RUNS)]
        for r in res:
            print(f"      {label:28}  {r}")
        scores = [s for _, s in res]
        print(f"      -> {label:28}  distinct moves {sorted({m for m, _ in res})}"
              f"  distinct scores {sorted(set(scores))}"
              f"  spread {max(scores) - min(scores)} cp")

    print()
    print("FREEZE, both criteria (they are not the same number):")
    for name in POSITIONS:
        a, c = agreement[name], convergence[name]
        print(f"   {name:10} AGREEMENT depth "
              f"{a if a else 'NONE up to d' + str(DEPTHS[-1])}"
              f"   ·   MOVE-CONVERGENCE depth {c if c else 'NONE'}"
              f"{'   <-- the freeze uses this one' if c else ''}")


if __name__ == "__main__":
    main()
