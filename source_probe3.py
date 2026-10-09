#!/usr/bin/env python3
"""TEST 3's SOURCE, AND THE REACH PROBE THAT MUST PRECEDE ITS PRE-REGISTRATION.

FINDING 014: "both edges are reachable by construction" was asserted twice and was false twice. So the
reach is now MEASURED here, and the pre-registration cites these numbers instead of a claim.

    GENERATOR A -- balanced legal-move walks. Sits near zero, so it DRIFTS THROUGH the -100 window.
    GENERATOR B -- the material handicap ladder, walked further. Sits far from zero, so it drifts
                   through the -300 window.

Test 1 reached only -100 with A. Test 2 reached only -300 with B. Neither reaches both; pooled, they do.

    python3 source_probe3.py            # measure the reach per edge, print the numbers
"""
import random
import sys

sys.path.insert(0, "/home/chilly1/workspace/ocho_arena")
import depth_test2 as t2                                    # noqa: E402  (uci/eval/fen helpers)

WINDOW = 60
LOST_CP, HOLD_CP = -300, -100


def generator_a(n_walks=4, per_walk=16):
    """Balanced legal-move walks from the start, sampling along the way."""
    rnd = random.Random(31415)
    cands = []
    for w in range(n_walks):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        for step in range(per_walk):
            # depth_test2 has no legal_moves helper; `go perft 1` enumerates them, and it terminates on
            # `Nodes searched:` rather than `bestmove` -- the terminator bug that hung the first harness.
            out = t2.uci([f"position fen {fen}", "go perft 1"], until="Nodes searched")
            mvs = []
            for ln in out:
                head = ln.split(":")[0].strip() if ":" in ln else ""
                if len(head) in (4, 5) and head[0] in "abcdefgh" and head[2] in "abcdefgh":
                    mvs.append(head)
            if not mvs:
                break
            mv = rnd.choice(mvs)
            d = t2.uci([f"position fen {fen} moves {mv}", "d"], until="Fen:")
            nxt = next((x.split("Fen:", 1)[1].strip() for x in d if x.startswith("Fen:")), None)
            if not nxt:
                break
            fen = nxt
            if step >= 4:
                cands.append(("A", f"walk{w}", step, fen))
    return cands


def generator_b(move_counts=(7, 9, 11, 13, 15, 17, 19, 21)):
    """Material handicap ladder, walked further -- the -300 region measured in FINDING 014."""
    out = []
    for label, squares in t2.LADDER:
        base = t2.fen_without(squares)
        cur = base
        for n in range(0, max(move_counts) + 1):
            if n:
                cur = t2.engine_moves(cur, 1)
                if not cur:
                    break
            if n in move_counts:
                out.append(("B", label, n, cur))
    return out


def main():
    print("=" * 96)
    print("TEST 3 SOURCE -- REACH PROBE. Measured, not asserted.")
    print("=" * 96)
    cands = generator_a() + generator_b()
    print(f"\n  candidates generated: {len(cands)}   "
          f"(A balanced {sum(1 for c in cands if c[0]=='A')}, "
          f"B material {sum(1 for c in cands if c[0]=='B')})")

    rows = []
    for i, (gen, label, n, fen) in enumerate(cands, 1):
        ev = t2.eval_at(fen, 18)
        if ev is None:
            continue
        rows.append((gen, label, n, fen, ev, t2.side_of(ev)))

    near_lost = [r for r in rows if abs(r[4] - LOST_CP) <= WINDOW]
    near_hold = [r for r in rows if abs(r[4] - HOLD_CP) <= WINDOW]
    from collections import Counter
    print(f"  evaluated: {len(rows)}")
    print(f"  side distribution: {dict(Counter(r[5] for r in rows))}")
    print(f"\n  AT-RISK near -300  [{LOST_CP-WINDOW}, {LOST_CP+WINDOW}] : {len(near_lost)}")
    for r in near_lost[:8]:
        print(f"      {r[0]} {r[1]:18s} mv{r[2]:<3} d18 {r[4]:6d}")
    print(f"  AT-RISK near -100  [{HOLD_CP-WINDOW}, {HOLD_CP+WINDOW}] : {len(near_hold)}")
    for r in near_hold[:8]:
        print(f"      {r[0]} {r[1]:18s} mv{r[2]:<3} d18 {r[4]:6d}")

    ok = len(near_lost) >= 5 and len(near_hold) >= 5
    print(f"\n  REACH: {'BOTH EDGES >= 5 -- ADMISSIBLE' if ok else 'STILL SHORT -- REFINE BEFORE TEST 3'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
