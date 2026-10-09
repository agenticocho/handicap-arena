#!/usr/bin/env python3
"""TEST 3's SOURCE -- denser sampling, with an EARLY STOP once both edges are populated.

WHAT THE TWO PREVIOUS PROBES TAUGHT, and this file is built on both:

  probe 1 (test 1's walk)        reached -100, never -300
  probe 2 (material, mv 0..21)    3 near -300, 2 near -100 -- BOTH EDGES, but short of 5 each
  AND a correction: probe 2 proves MATERIAL ALONE DOES REACH -100, at mv19 (-119) and mv21 (-81).
  FINDING 014 said it could not, on a walk that stopped at mv15. The window is reachable; the walk
  was too short.

SO THE DEFICIENCY IS DENSITY, NOT KIND. The windows are 120 cp wide and the evaluation moves in tens of
centipawns per move, so the walk PASSES THROUGH a window over a few plies. Sampling sparsely misses it;
sampling EVERY ply catches every crossing. This samples every ply and stops as soon as both edges hold
ENOUGH, so the cost is proportional to what is needed rather than to a fixed grid.
"""
import sys
import time

sys.path.insert(0, "/home/chilly1/workspace/ocho_arena")
import depth_test2 as t2                                    # noqa: E402

WINDOW = 60
LOST_CP, HOLD_CP = -300, -100
NEED_EACH = 6                 # target per edge; the card's floor is 5
MAX_PLIES = 70
BUDGET_SECS = 1500            # stop and report what was reached rather than run away


def walk_rung(label, squares, cap):
    """Every ply along one material rung, evaluated. Yields positions."""
    cur = t2.fen_without(squares)
    out = []
    for n in range(0, cap + 1):
        if n:
            cur = t2.engine_moves(cur, 1)
            if not cur:
                break
        out.append((label, n, cur))
    return out


def main():
    t0 = time.time()
    print("=" * 96)
    print("TEST 3 SOURCE -- DENSE REACH PROBE, early stop on both edges")
    print("=" * 96)
    print(f"\n  target: >= {NEED_EACH} at-risk per edge   budget {BUDGET_SECS}s\n")

    near_lost, near_hold, all_rows = [], [], []
    rungs = [(lbl, sq) for lbl, sq in t2.LADDER]          # all eight rungs, every ply

    stop = False
    for label, squares in rungs:
        if stop:
            break
        # walk_rung yields (label, ply, fen) -- THREE values. Unpacking two raised
        # "too many values to unpack" and the probe died on its first rung before evaluating anything,
        # while its output file held only the header. A header and no error is NOT evidence of running.
        for _lbl, n, fen in walk_rung(label, squares, MAX_PLIES):
            if time.time() - t0 > BUDGET_SECS:
                print("  BUDGET REACHED")
                stop = True
                break
            ev = t2.eval_at(fen, 18)
            if ev is None:
                continue
            row = (label, n, ev, t2.side_of(ev), fen)
            all_rows.append(row)
            if abs(ev - LOST_CP) <= WINDOW:
                near_lost.append(row)
                print(f"    -300 hit  {label:18s} mv{n:<3} d18 {ev:6d}")
            elif abs(ev - HOLD_CP) <= WINDOW:
                near_hold.append(row)
                print(f"    -100 hit  {label:18s} mv{n:<3} d18 {ev:6d}")
            if len(near_lost) >= NEED_EACH and len(near_hold) >= NEED_EACH and n >= 20:
                print(f"\n  BOTH EDGES POPULATED at {label} mv{n}")
                stop = True
                break
        print(f"  ...{label} done  ({len(all_rows)} evaluated, "
              f"{len(near_lost)} near -300, {len(near_hold)} near -100)")

    print(f"\n  evaluated: {len(all_rows)}   elapsed {time.time()-t0:.0f}s")
    print(f"  AT-RISK near -300 : {len(near_lost)}")
    for r in near_lost:
        print(f"      {r[0]:18s} mv{r[1]:<3} d18 {r[2]:6d}")
    print(f"  AT-RISK near -100 : {len(near_hold)}")
    for r in near_hold:
        print(f"      {r[0]:18s} mv{r[1]:<3} d18 {r[2]:6d}")
    ok = len(near_lost) >= 5 and len(near_hold) >= 5
    print(f"\n  REACH: {'BOTH EDGES >= 5 -- ADMISSIBLE, write the pre-registration' if ok else 'STILL SHORT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
