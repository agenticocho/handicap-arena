#!/usr/bin/env python3
"""Measure -- do not declare -- the depth at which this engine's answer becomes a FACT.

THE ORDER's rule: "an event is not placeable until its oracle is present AND its freeze is
MEASURED -- a depth at which two runs of the same position disagree is not a fact and must not
be frozen." This runs each position twice at each depth and reports where the two runs agree.
"""
import chess, chess.engine, sys
ENG = "/opt/homebrew/bin/stockfish"
POSITIONS = {
    "kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "italian":  "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
}
DEPTHS = [8, 10, 12, 14, 16]

def one(fen, depth, cfg):
    """One independent run: fresh process, so no hash or state carries between runs."""
    eng = chess.engine.SimpleEngine.popen_uci(ENG)
    try:
        if cfg: eng.configure(cfg)
        info = eng.analyse(chess.Board(fen), chess.engine.Limit(depth=depth))
    finally:
        eng.quit()
    pv = info.get("pv") or []
    return (pv[0].uci() if pv else None,
            info["score"].pov(chess.WHITE).score(mate_score=100000))

print(f"oracle: {ENG}")
print(f"id    : ", end="", flush=True)
e = chess.engine.SimpleEngine.popen_uci(ENG); print(e.id.get("name")); e.quit()
print()

print("A. Threads=1, Hash pinned  (the proposed freeze config)")
print(f"   {'position':10} {'depth':>5}  {'run1 (move, cp)':>22}  {'run2':>22}  agree")
stable = {}
for name, fen in POSITIONS.items():
    first_agree = None
    for d in DEPTHS:
        a = one(fen, d, {"Threads": 1, "Hash": 16})
        b = one(fen, d, {"Threads": 1, "Hash": 16})
        ok = a == b
        if ok and first_agree is None: first_agree = d
        print(f"   {name:10} {d:>5}  {str(a):>22}  {str(b):>22}  {'YES' if ok else 'NO  <-- not a fact'}")
    stable[name] = first_agree

print()
print("B. DEFAULT threading  (what happens if the freeze is not pinned)")
for name, fen in POSITIONS.items():
    d = 14
    a = one(fen, d, None); b = one(fen, d, None)
    print(f"   {name:10} {d:>5}  {str(a):>22}  {str(b):>22}  {'YES' if a==b else 'NO  <-- NOT reproducible'}")

print()
print("FREEZE (first depth where two independent runs agree):")
for n, d in stable.items():
    print(f"   {n:10} depth {d}" if d else f"   {n:10} NO AGREEMENT UP TO depth {DEPTHS[-1]} -- not freezable")
