#!/usr/bin/env python3
"""EVERY LEVEL CARRIES A SOLUTION THAT THE SIMULATOR HAS VERIFIED, AND ITS PROVEN DEAD END IF IT HAS ONE.

A LEVEL WHOSE SOLVABILITY NOBODY CHECKED IS NOT A LEVEL -- it is a grid that might be impossible, and an
entrant failing on it would be recorded as a fact about the entrant. The chess reader produced exactly
that error in the other direction; this is the same discipline applied before the first move.

AND A LEVEL'S PURPOSE TRAVELS WITH IT. `03_the_corner_waiting` exists to measure DEAD-END RECOGNITION, and
that claim is only worth anything if the dead end is real. So the fatal opening move is recorded HERE and
asserted to be a LEGAL MOVE THAT CHANGES THE POSITION -- a typo in the proof would otherwise survive as a
proof. The full proof (no solution reachable from the resulting position, by complete enumeration) lives in
`sokoban_deadend.py`, which is where it can be re-derived rather than quoted.

    python3 verify_levels.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sokoban as S                                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# name, solution, why, fatal opening moves (proven FATAL by sokoban_deadend.py; () if none)
LEVELS = [
    ("01_one_push", "R",
     "ONE PUSH. The floor of the scale: a model that cannot do this cannot play the game at all. "
     "ALSO THE COLLAPSE CONTROL -- it is easy ON PURPOSE, its easiness IS the oracle, so resigning on it "
     "is provably premature without needing a solver.",
     ()),
    ("02_two_boxes", "RRRRDLLLDRRR",
     "TWO BOXES AND A WALK. Requires routing the player around a solved crate, so a model that only ever "
     "pushes in one direction cannot finish it. FATAL FRACTION 0.000: every opening move is survivable, so "
     "this level CANNOT measure dead-end recognition.",
     ()),
    ("03_the_corner_waiting", "RULDLU",
     "ONE BOX, ONE TARGET, SIX MOVES, AND ONE OPENING MOVE THAT ENDS IT. The crate starts one square below a "
     "corner formed by the wall above it and the wall to its right; pushing it UP is legal, takes one move, "
     "and drops it in that corner OFF-TARGET -- and nothing pulls, so the level is dead from there. Pushing "
     "it LEFT then UP wins. FATAL FRACTION 0.250: the first level in the set that can measure the faculty "
     "the event exists for.",
     ("U",)),
]

# TWO DISTINCT MINIMAL SOLUTIONS FOR 02, both replaying to solved/12. The published one and the one the
# solver found independently. Kept because a solver tuned to the published string would have returned the
# published string, and this is the evidence that it did not.
ALT_SOLUTIONS = {"02_two_boxes": "DDRRRRULLURR"}


def main():
    fails = []
    print("=" * 96)
    print("LEVEL VERIFICATION -- every level is solvable by a solution the simulator confirms")
    print("=" * 96)
    for name, sol, why, fatal in LEVELS:
        p = os.path.join(HERE, "levels", f"{name}.txt")
        if not os.path.exists(p):
            print(f"  {name:24s} MISSING")
            fails.append(name)
            continue
        text = open(p).read()
        try:
            st0 = S.parse(text)
        except ValueError as e:
            print(f"  {name:24s} MALFORMED: {e}")
            fails.append(name)
            continue
        r = S.play(text, list(sol))
        ok = r["solved"]
        print(f"  {'PASS' if ok else 'FAIL'}  {name:24s} solved={r['solved']}  "
              f"moves={r['moves']}  solution={sol}")
        if not ok:
            fails.append(name)
            print(f"        final board:\n{chr(10).join('          ' + l for l in r['final_board'].splitlines())}")
            continue
        print(f"        {why}")

        # THE FATAL MOVES ARE ASSERTED TO BE REAL MOVES. A dead-end "proof" anchored to a move that is not
        # legal, or that does not change the position, would be a proof of nothing.
        for m in fatal:
            nxt, outcome = S.step(st0, m)
            moved = outcome in ("moved", "pushed") and S.render(nxt) != S.render(st0)
            tag = "PASS" if moved else "FAIL"
            print(f"        {tag}  fatal opening move {m}: legal and it MOVES the position "
                  f"(outcome {outcome})")
            if not moved:
                fails.append(f"{name}:{m}")

        if name in ALT_SOLUTIONS:
            alt = ALT_SOLUTIONS[name]
            ra = S.play(text, list(alt))
            ok2 = ra["solved"] and ra["moves"] == r["moves"]
            print(f"        {'PASS' if ok2 else 'FAIL'}  a SECOND minimal solution also verifies: "
                  f"{alt} -> solved={ra['solved']} moves={ra['moves']} (same length as the published one)")
            if not ok2:
                fails.append(f"{name}:alt")

    print()
    print("  the full dead-end proof (complete enumeration from the position after the fatal move) is in")
    print("  sokoban_deadend.py -- re-derived there rather than quoted here.")
    print()
    print("=" * 96)
    print(f"{'ALL LEVELS VERIFIED' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{len(LEVELS) - len([f for f in fails if f in [l[0] for l in LEVELS]])}/{len(LEVELS)} levels, "
          f"{len(fails)} problem(s)")
    print("=" * 96)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
