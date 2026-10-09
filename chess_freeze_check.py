#!/usr/bin/env python3
"""Reproduce Jarvis's finding ON THIS BOX, before amending CARD_chess.md on the strength of it.

The claim to test: at Stockfish's DEFAULT Threads (core count), the oracle does not have a stable
answer -- four runs of the same position at the same depth give different evaluations AND a different
best move. At Threads=1 with a pinned Hash, runs agree exactly.

A FINDING ARRIVES AS A CLAIM. This box is the one that will score event 1, so the box that will score
it is the box that must reproduce it.
"""
import subprocess
import sys

BIN = "/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal"
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def search(fen, depth, threads=None, hash_mb=None, timeout=300):
    """-> (score_kind, score_value, bestmove). None where the search did not report."""
    p = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    send("uci")
    while p.stdout.readline().strip() != "uciok":
        pass
    if threads is not None:
        send(f"setoption name Threads value {threads}")
    if hash_mb is not None:
        send(f"setoption name Hash value {hash_mb}")
    send("isready")
    while p.stdout.readline().strip() != "readyok":
        pass
    send(f"position fen {fen}")
    send(f"go depth {depth}")
    score = None
    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if line.startswith("info ") and f" depth {depth} " in line and " score " in line:
            t = line.split()
            for i, x in enumerate(t):
                if x == "score":
                    score = (t[i + 1], int(t[i + 2]))
        if line.startswith("bestmove"):
            best = line.split()[1]
            break
    send("quit")
    p.wait(timeout=10)
    return score, best


print("=" * 92)
print("THE ORACLE'S STABILITY, MEASURED ON THIS BOX")
print("=" * 92)

# ---- A: Stockfish's DEFAULT threading (it defaults Threads to the core count) -------------
print("\nA. DEFAULT Threads (unset -- Stockfish picks the core count), depth 18, FOUR runs")
runs = [search(KIWIPETE, 18) for _ in range(4)]
for i, (sc, bm) in enumerate(runs, 1):
    print(f"     run {i}: {str(sc):18s} bestmove={bm}")
scores = [sc[1] for sc, _ in runs if sc]
moves = {bm for _, bm in runs}
if scores:
    print(f"     spread {max(scores) - min(scores)} cp   distinct scores {len(set(scores))}   "
          f"distinct bestmoves {len(moves)}: {sorted(moves)}")

# ---- B: Threads=1 + pinned Hash ------------------------------------------------------------
print("\nB. Threads=1, Hash pinned, depth 18, TWO runs")
runs = [search(KIWIPETE, 18, threads=1, hash_mb=64) for _ in range(2)]
for i, (sc, bm) in enumerate(runs, 1):
    print(f"     run {i}: {str(sc):18s} bestmove={bm}")
print(f"     identical: {runs[0] == runs[1]}")

# ---- C: the depth-dependence, at Threads=1 -------------------------------------------------
print("\nC. Threads=1, the SAME position across depths -- is the answer monotone in depth?")
prev = None
mono = True
rows = []
for d in (8, 12, 16, 18, 20):
    sc, bm = search(KIWIPETE, d, threads=1, hash_mb=64)
    rows.append((d, sc, bm))
    flag = ""
    if prev is not None and sc and prev[1] is not None:
        # centipawns from the side to move: more negative = worse for the mover
        if sc[1] > prev[1]:
            mono = False
            flag = "  <- NOT monotone (better than the shallower depth)"
    print(f"     d{d:<3} {str(sc):18s} bestmove={bm}{flag}")
    prev = sc
print(f"     monotone in depth: {mono}")
if rows:
    moves = {bm for _, _, bm in rows}
    print(f"     distinct bestmoves across depths: {sorted(moves)}")

print("\n" + "=" * 92)
print("A reproducible oracle is not the same as a FIXED one: Threads=1 makes runs agree;")
print("it does not make different DEPTHS agree. Both fields must be frozen, not just depth.")
print("=" * 92)
