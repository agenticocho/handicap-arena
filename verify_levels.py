#!/usr/bin/env python3
"""EVERY LEVEL CARRIES A SOLUTION THAT THE SIMULATOR HAS VERIFIED.

A LEVEL WHOSE SOLVABILITY NOBODY CHECKED IS NOT A LEVEL -- it is a grid that might be impossible, and an
entrant failing on it would be recorded as a fact about the entrant. The chess reader produced exactly
that error in the other direction; this is the same discipline applied before the first move.

    python3 verify_levels.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sokoban as S                                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# name, solution, what the level is FOR
LEVELS = [
    ("01_one_push", "R",
     "ONE PUSH. The floor of the scale: a model that cannot do this cannot play the game at all."),
    ("02_two_boxes", "RRRRDLLLDRRR",
     "TWO BOXES AND A WALK. Requires routing the player around a solved crate, so a model that only ever "
     "pushes in one direction cannot finish it."),
]


def main():
    fails = []
    print("=" * 96)
    print("LEVEL VERIFICATION -- every level is solvable by a solution the simulator confirms")
    print("=" * 96)
    for name, sol, why in LEVELS:
        p = os.path.join(HERE, "levels", f"{name}.txt")
        if not os.path.exists(p):
            print(f"  {name:16s} MISSING")
            fails.append(name)
            continue
        text = open(p).read()
        try:
            S.parse(text)
        except ValueError as e:
            print(f"  {name:16s} MALFORMED: {e}")
            fails.append(name)
            continue
        r = S.play(text, list(sol))
        ok = r["solved"]
        print(f"  {'PASS' if ok else 'FAIL'}  {name:16s} solved={r['solved']}  "
              f"moves={r['moves']}  solution={sol}")
        if not ok:
            fails.append(name)
            print(f"        final board:\n{chr(10).join('          ' + l for l in r['final_board'].splitlines())}")
        else:
            print(f"        {why}")
    print()
    print("=" * 96)
    print(f"{'ALL LEVELS VERIFIED' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{len(LEVELS) - len(fails)}/{len(LEVELS)}")
    print("=" * 96)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
