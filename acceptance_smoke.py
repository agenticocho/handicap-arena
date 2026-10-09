#!/usr/bin/env python3
"""ACCEPTANCE-RATE SMOKE TEST -- the four-ply rule applied to money instead of to a loop body.

FINDING 015 says the unblock is a REJECTION SAMPLER over many walks, and that its cost is roughly ONE
FULL WALK PER ACCEPTED POSITION. That is a DERIVATION, not a measurement. This measures it on TEN walks
before anyone budgets on a hundred -- and the measured rate is what gets pre-registered, so the budget is
auditable rather than plausible.

AN INDEPENDENT WALK IS THE SAMPLING UNIT, not a ply. FINDING 015: six hits along one walk are one
observation wearing six indices. So this counts WALKS THAT LAND IN A WINDOW, never plies -- and each walk
draws a fresh rung, a fresh ply length and a fresh seed, so no two accepted positions share a derivation.

    python3 acceptance_smoke.py [n_walks]
"""
import random
import sys
import time

sys.path.insert(0, "/home/chilly1/workspace/ocho_arena")
import depth_test2 as t2                                    # noqa: E402

WINDOW = 60
LOST_CP, HOLD_CP = -300, -100
N_WALKS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
PLY_MIN, PLY_MAX = 8, 60


def one_walk(seed):
    """-> (d18 eval or None, rung, plies). A FRESH derivation every call."""
    rnd = random.Random(seed)
    label, squares = rnd.choice(t2.LADDER)
    target = rnd.randint(PLY_MIN, PLY_MAX)
    cur = t2.fen_without(squares)
    for _ in range(target):
        out = t2.uci([f"position fen {cur}", "go depth 6"], until="bestmove")
        best = next((l.split()[1] for l in out if l.startswith("bestmove")), None)
        if not best or best == "(none)":
            return None, label, target
        d = t2.uci([f"position fen {cur} moves {best}", "d"], until="Fen:")
        nxt = next((x.split("Fen:", 1)[1].strip() for x in d if x.startswith("Fen:")), None)
        if not nxt:
            return None, label, target
        cur = nxt
    return t2.eval_at(cur, 18), label, target


def main():
    t0 = time.time()
    print("=" * 92)
    print(f"ACCEPTANCE-RATE SMOKE TEST -- {N_WALKS} INDEPENDENT WALKS")
    print("=" * 92)
    print(f"\n  windows:  near -100 [-160,-40]     near -300 [-360,-240]\n")
    acc_lost, acc_hold, rows = 0, 0, []
    for i in range(N_WALKS):
        ev, label, plies = one_walk(1000 + i)
        if ev is None:
            print(f"    walk {i+1:2d}  no evaluation")
            continue
        in_lost = abs(ev - LOST_CP) <= WINDOW
        in_hold = abs(ev - HOLD_CP) <= WINDOW
        acc_lost += in_lost
        acc_hold += in_hold
        tag = ("NEAR -300" if in_lost else "") + (" NEAR -100" if in_hold else "")
        rows.append((ev, label, plies, bool(tag)))
        print(f"    walk {i+1:2d}  {label:18s} {plies:2d} plies  d18 {ev:6d}  {t2.side_of(ev):9s} {tag}")
    print(f"\n  WALKS: {len(rows)}   ACCEPTED near -300: {acc_lost}   near -100: {acc_hold}")
    if rows:
        print(f"  ACCEPTANCE RATE per walk:  -300 {acc_lost/len(rows):.2f}   -100 {acc_hold/len(rows):.2f}")
        need = 5
        for name, acc in (("-300", acc_lost), ("-100", acc_hold)):
            if acc:
                print(f"  TO REACH {need} near {name}: ~{need/(acc/len(rows)):.0f} walks (measured rate)")
            else:
                print(f"  TO REACH {need} near {name}: rate 0/{len(rows)} -- UNBOUNDED on this evidence")
    print(f"\n  elapsed {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
