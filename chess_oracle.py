#!/usr/bin/env python3
"""Evaluate positions with a FROZEN engine at a FROZEN depth, and prove it is reproducible.

GAME1_CHESS_tech-and-promo.md:33 -- "The ground truth is a reference engine at a FROZEN DEPTH...
Not an opinion and not a second model." And :123 -- "The engine and its depth must be frozen with
the positions. A shallow engine's 'lost' is not a fact."

A UCI ENGINE MUST BE DRIVEN, NOT PUMPED AND ABANDONED. `communicate(script)` closes stdin, and
Stockfish exits on EOF BEFORE the search finishes -- which is why the first version of this file
returned empty lists and reported DIVERGED for every position. The harness was broken; the engine
was fine. So: keep stdin OPEN, read until `bestmove`, then quit.
"""
import subprocess
import sys

BIN = "/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal"
DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 18

POSITIONS = {
    "quiet_opening": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
    "kq_vs_k_lost":   "8/8/8/8/8/6k1/6q1/6K1 w - - 0 1",
    "down_a_piece":   "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 6",
}
identity = [None]


def evaluate(fen, depth=DEPTH):
    """Drive one search to completion. -> (score_kind, score_value) or None."""
    p = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(cmd):
        p.stdin.write(cmd + "\n"); p.stdin.flush()
    send("uci")
    score = None
    while True:                                     # drain the uci handshake to uciok
        line = p.stdout.readline()
        if not line: break
        if line.startswith("id name") and identity[0] is None:
            identity[0] = line.strip()
        if line.strip() == "uciok": break
    send("isready")
    while p.stdout.readline().strip() != "readyok":
        pass
    send(f"position fen {fen}")
    send(f"go depth {depth}")
    while True:                                     # read until the search ENDS
        line = p.stdout.readline()
        if not line: break
        if line.startswith("info ") and f" depth {depth} " in line and " score " in line:
            toks = line.split()
            for i, t in enumerate(toks):
                if t == "score":
                    score = (toks[i + 1], int(toks[i + 2]))
        if line.startswith("bestmove"):
            break
    send("quit")
    p.wait(timeout=10)
    return score


print("=" * 88)
print(f"FROZEN ORACLE -- depth {DEPTH}, each position evaluated TWICE")
print("=" * 88)
rows = []
for name, fen in POSITIONS.items():
    a, b = evaluate(fen), evaluate(fen)
    same = (a == b)
    rows.append((name, a, b, same))
    print(f"  {name:16s} run1={str(a):16s} run2={str(b):16s} {'IDENTICAL' if same else 'DIVERGED'}")
print(f"\n  {identity[0]}")
print(f"  depth FROZEN at {DEPTH}")
print(f"\n  reproducible: {sum(1 for r in rows if r[3])}/{len(rows)}")
print("  A depth at which two runs of the same position disagree is NOT a fact and must not be frozen.")
