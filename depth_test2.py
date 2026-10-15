#!/usr/bin/env python3
"""TEST 2 -- THE DEPTH SENSITIVITY TEST, per PREREG_depth_sensitivity.md (49ef665).

THE SOURCE, AND WHY IT IS BUILT THIS WAY
    Test 1's legal-move walk reached NO LOST position (30 positions, none below -198) -- structurally,
    because random legal play has neither side pursuing an advantage, so material imbalance never
    accumulates. The property that made the walk unbiased made it useless for the region in question.

    THIS SOURCE INSTEAD SEEDS AN IMBALANCE AND THEN PLAYS ENGINE MOVES. A deterministic HANDICAP LADDER
    (a pawn, two pawns, a knight, a knight plus a pawn, a bishop, a rook) sets how large the imbalance is,
    and a deterministic number of ENGINE-DIRECTED moves makes the position realistic rather than a bare
    material difference. Varying the two sweeps the evaluation across BOTH thresholds, and the sign is
    read from the side to move, so both edges are reachable BY CONSTRUCTION.

    NO POSITION IS CHOSEN OR REJECTED BY EYE. The ladder and the move count are a rule; the ORACLE labels.

WHAT IT REPORTS
    shifts d12->d18 (median and range), the crossing rate among at-risk positions, and -- first -- THE
    COMPOSITION CHECK, because a crossing rate over a one-sided sample is a property of the sample.
    Below 5 per edge the verdict is ONE-EDGED or INADMISSIBLE and NO sensitivity is reported.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cabinet_root as _root                                          # noqa: E402

BIN = "/home/chilly1/chess_oracle/stockfish/stockfish-linux-x86-64-universal"
D_REF, D_ALT = 18, 12
THREADS, HASH = 1, 64
LOST_CP, HOLD_CP, WINDOW = -300, -100, 60
MIN_PER_EDGE = 5
WALK_DEPTH = 6

# NO DESTINATION IS BOUND HERE, AND FOR THIS FILE THAT IS ALSO A REQUIREMENT ON ITS IMPORTERS. The
# line that used to sit here was a module-level ABSOLUTE LITERAL naming main's legacy record -- the
# same literal, at the same line, in all four trees -- and main() opens it for writing twice. THIS
# FILE IS ALSO A LIBRARY: source_probe3.py:19, source_probe4.py:21 and acceptance_smoke.py:20 import
# it for its uci/eval/fen helpers. A resolution at module level would make those three refuse over a
# write they never make, so the destination is resolved at the CALL -- see depth_dir().

# deterministic handicap ladder: removal from BLACK's side of the start position, plus engine moves.
# Each entry is (label, [squares removed from the black side]).
LADDER = [
    ("pawn",             ["b7"]),
    ("two-pawns",        ["b7", "g7"]),
    ("knight",           ["b8"]),
    ("two-knights",      ["b8", "g8"]),
    ("knight-plus-pawn", ["b8", "g7"]),
    ("bishop",           ["c8"]),
    ("rook",             ["a8"]),
    ("queen",            ["d8"]),
]
MOVES = [0, 2, 4, 6, 8, 10, 12, 14]      # 8 x 8 = 64 candidates, meeting the >= 60 the card requires.


def uci(cmds, until):
    p = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    lines = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        ln = ln.rstrip("\n")
        lines.append(ln)
        if ln.startswith(until):
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return lines


def fen_without(squares):
    """Start position with the given squares emptied. Kings are never removed, so it stays legal.

    A FEN RANK IS EIGHT WIDE AND ENCODES EMPTIES AS DIGITS. The first version of this deleted the
    character in place, turning `pppppppp` into `ppppppp` -- a seven-character rank, which is not a
    position at all. Ranks are rebuilt from squares and runs of empties are counted.
    """
    board = [["r", "n", "b", "q", "k", "b", "n", "r"],
             ["p"] * 8,
             [None] * 8, [None] * 8, [None] * 8, [None] * 8,
             ["P"] * 8,
             ["R", "N", "B", "Q", "K", "B", "N", "R"]]
    for sq in squares:
        f = ord(sq[0]) - ord("a")
        r = 8 - int(sq[1])
        board[r][f] = None
    ranks = []
    for row in board:
        s, gap = "", 0
        for cell in row:
            if cell is None:
                gap += 1
            else:
                if gap:
                    s += str(gap)
                    gap = 0
                s += cell
        if gap:
            s += str(gap)
        ranks.append(s)
    return "/".join(ranks) + " w KQkq - 0 1"


def engine_moves(fen, n):
    """Play n ENGINE-DIRECTED moves from fen. -> final fen (or None)."""
    cur = fen
    for _ in range(n):
        out = uci([f"position fen {cur}", f"go depth {WALK_DEPTH}"], until="bestmove")
        best = None
        for ln in out:
            if ln.startswith("bestmove"):
                best = ln.split()[1]
        if not best or best == "(none)":
            return None
        d = uci([f"position fen {cur} moves {best}", "d"], until="Fen:")
        nxt = None
        for ln in d:
            if ln.startswith("Fen:"):
                nxt = ln.split("Fen:", 1)[1].strip()
        if not nxt:
            return None
        cur = nxt
    return cur


def eval_at(fen, depth):
    out = uci([f"position fen {fen}", f"go depth {depth}"], until="bestmove")
    sc = None
    for ln in out:
        if ln.startswith("info ") and f" depth {depth} " in ln and " score " in ln:
            t = ln.split()
            for i, x in enumerate(t):
                if x == "score":
                    sc = (t[i + 1], int(t[i + 2]))
    if not sc or sc[0] != "cp":
        return None            # mate scores are not converted into centipawns by invention
    return sc[1]


def side_of(cp):
    if cp is None:
        return None
    if cp <= LOST_CP:
        return "LOST"
    if cp >= HOLD_CP:
        return "HOLDABLE"
    return "GREY"


def depth_dir():
    """-> <declared ROOT>/<this worktree's cabinet>/depth -- THE ONE DESTINATION for this test's output.

    RESOLVED AT THE CALL, NOT AT THE IMPORT. This file is ALSO a library -- source_probe3.py:19,
    source_probe4.py:21 and acceptance_smoke.py:20 import it for its uci/eval/fen helpers -- so a
    resolution at module level would make three importers refuse over a write they never make. The
    three importers ARE the control for that rule: they must still import this module successfully.

    AND IT REFUSES RATHER THAN FALLS BACK. cabinet_root.results_dir() is a Refusal -- a SystemExit
    that names the remedy -- when there is no declared root, or when the declaration resolves inside
    a git working tree or the repository's own git directory. It is NOT caught: a run that cannot
    declare where its result goes must not write one somewhere else.

    WHY A NAMED SUBTREE AND NOT THE FLAT LEVEL -- the naming is the Chair's, not this file's. Both
    published depth artifacts stay DECLARED IN PLACE inside the legacy record, which is ONE tree
    object (0bcaaa0188b35f0bdd17e3ca824a977cac2d94a1) that a removal would change, so a flat-level
    write would put a second file of the same basename under a different domain entry -- a basename
    collision across entries, which the tools that flatten the domain are required to refuse.
    `depth/` is a subtree OF THE DECLARED WRITE SCOPE, not a second root.
    """
    return os.path.join(_root.results_dir(), "depth")


def out_path():
    """-> <declared write scope>/depth/DEPTH_TEST2.json, or a refusal. This creates nothing."""
    return os.path.join(depth_dir(), "DEPTH_TEST2.json")


def main():
    dest = out_path()                    # the destination, resolved where it is written
    print("=" * 96)
    print("TEST 2 -- DEPTH SENSITIVITY. Source: a handicap ladder plus engine-directed moves.")
    print("=" * 96)
    print(f"  destination            {dest}")
    print("                         resolved at the CALL through cabinet_root.results_dir(), which "
          "REFUSES")
    print("                         rather than falling back to a worktree-local path")
    cands = []
    for label, squares in LADDER:
        base = fen_without(squares)
        for n in MOVES:
            f = engine_moves(base, n) if n else base
            if f:
                cands.append({"ladder": label, "moves": n, "fen": f, "side_to_move": f.split()[1]})
    print(f"\n  candidates generated: {len(cands)}  (target >= 60)")

    # ---- reference label at d18, TWICE; disagreement discards ----
    rows = []
    for i, c in enumerate(cands, 1):
        a = eval_at(c["fen"], D_REF)
        b = eval_at(c["fen"], D_REF)
        if a is None or b is None:
            continue
        if a != b:
            print(f"    [{i:2d}] DISCARDED -- d18 disagreed with itself ({a} vs {b})")
            continue
        c["d18"] = a
        c["side18"] = side_of(a)
        rows.append(c)
    print(f"  reproducible at d18: {len(rows)}")
    dist = {}
    for r in rows:
        dist[r["side18"]] = dist.get(r["side18"], 0) + 1
    print(f"  d18 side distribution: {dist}")

    # ---- THE COMPOSITION CHECK FIRST, per the pre-registration ----
    risk = [r for r in rows if abs(r["d18"] - LOST_CP) <= WINDOW or abs(r["d18"] - HOLD_CP) <= WINDOW]
    near_lost = [r for r in risk if abs(r["d18"] - LOST_CP) <= WINDOW]
    near_hold = [r for r in risk if abs(r["d18"] - HOLD_CP) <= WINDOW]
    far = [r for r in rows if r not in risk]
    print(f"\n  ADMISSIBILITY CHECK (before any crossing is read)")
    print(f"    at-risk near -300 : {len(near_lost):3d}   need >= {MIN_PER_EDGE}")
    print(f"    at-risk near -100 : {len(near_hold):3d}   need >= {MIN_PER_EDGE}")
    admissible = len(near_lost) >= MIN_PER_EDGE and len(near_hold) >= MIN_PER_EDGE
    if not admissible:
        which = "INADMISSIBLE" if not risk else "ONE-EDGED"
        print(f"\n  *** {which} -- NOT ADMISSIBLE. ***")
        print(f"  Per the pre-registration: no sensitivity is reported, and NO conclusion about the")
        print(f"  unreached edge follows, in either direction.")
        os.makedirs(depth_dir(), exist_ok=True)
        json.dump({"admissible": False, "which": which, "near_lost": len(near_lost),
                   "near_hold": len(near_hold), "rows": rows}, open(dest, "w"), indent=1)
        print(f"\n  written: {dest}")
        return 0

    print(f"    -> ADMISSIBLE")
    for r in rows:
        r["d12"] = eval_at(r["fen"], D_ALT)
        r["side12"] = side_of(r["d12"])
        r["crossed"] = r["side12"] is not None and r["side18"] != r["side12"]
        r["shift"] = r["d18"] - r["d12"] if r["d12"] is not None else None

    rc_ = sum(1 for r in risk if r["crossed"])
    fc = sum(1 for r in far if r["crossed"])
    shifts = sorted(r["shift"] for r in rows if r["shift"] is not None)
    med = shifts[len(shifts) // 2] if shifts else None
    print(f"\n  CROSSINGS  at-risk {rc_} of {len(risk)}   far {fc} of {len(far)}")
    print(f"  SHIFT d12->d18 over all {len(shifts)}: min {shifts[0]:+d}  median {med:+d}  max {shifts[-1]:+d}")
    print(f"  band width 200 cp  ->  |median shift| / band = {abs(med)/200:.2%}" if med is not None else "")
    print(f"\n  THE SENSITIVITY STATEMENT, which is the deliverable:")
    print(f"    'Moving the depth from 18 to 12 moves a decisive position's evaluation by a median")
    print(f"     of {med:+d} cp (range {shifts[0]:+d} to {shifts[-1]:+d}) and flips the band on "
          f"{rc_}/{len(risk)} = {100*rc_/len(risk):.0f}% of at-risk positions.'")
    os.makedirs(depth_dir(), exist_ok=True)
    json.dump({"admissible": True, "rows": rows, "crossings_at_risk": rc_, "crossings_far": fc,
               "n_at_risk": len(risk), "near_lost": len(near_lost), "near_hold": len(near_hold),
               "shift_min": shifts[0] if shifts else None, "shift_median": med,
               "shift_max": shifts[-1] if shifts else None}, open(dest, "w"), indent=1)
    print(f"\n  written: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
