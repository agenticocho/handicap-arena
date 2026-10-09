#!/usr/bin/env python3
"""DECISIVE TEST: is granite's behaviour under the NEW legend reproducible, or was the A/B's solve luck?

TWO POSSIBILITIES, OPPOSITE MEANINGS:
  (a) granite under the new legend ALWAYS varies -> the population run must have seen the OLD prompt, and
      there is a timing/staleness defect to name.
  (b) granite under the new legend SOMETIMES locks on U -> granite is variable at temperature 0 across
      processes, the A/B's n=1 solve is a sample, and the finding must be weakened.

REPEATS, because a single observation cannot tell these apart and one of them is a claim about a mechanism.

    python3 sokoban_repeat.py --reps 3
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban_run as R                                                 # noqa: E402

ENT = "granite-3.3-2b-instruct-critical-thinking.Q5_K_M.gguf"
LEVEL = "levels/01_one_push.txt"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--port", type=int, default=8770)
    a = ap.parse_args()

    ent = os.path.join(R.MODELS, ENT)
    if not os.path.exists(ent):
        print(f"  ENTRANT ABSENT: {ENT}")
        return 2
    print("=" * 96)
    print(f"REPEAT TEST -- {ENT}")
    print(f"  level {LEVEL}   reps {a.reps}   cap {a.cap}   temperature 0.0   same binary, same box")
    print("=" * 96)
    print("  IF EVERY REP VARIES, the population run saw the OLD prompt.")
    print("  IF ANY REP LOCKS ON U, granite is variable and the A/B's n=1 solve was a sample.")
    print()

    rows = []
    port = a.port
    for i in range(a.reps):
        for arm in ("new", "old"):
            os.environ["SOKOBAN_LEGEND"] = arm
            r = R.run(ent, os.path.join(HERE, LEVEL), a.cap, port)
            port += 1
            r["rep"] = i
            rows.append(r)
            toks = [t["token"] for t in (r.get("turns") or [])]
            uniq = sorted(set(toks))
            print(f"  rep {i+1} arm={arm:4s} ended={r.get('ended','?') if r.get('loaded') else 'NO LOAD':18s} "
                  f"moves={r.get('moves',0):3d} blocked={r.get('blocked',0):3d} "
                  f"distinct tokens={uniq}  -> {'VARIED' if len(uniq) > 1 else 'LOCKED'}")

    out = os.path.join(HERE, "probes", "SOKOBAN_REPEAT.json")
    json.dump({"entrant": ENT, "level": LEVEL, "cap": a.cap, "cells": rows}, open(out, "w"), indent=1)
    print()
    print("  DERIVED FROM THE ARTIFACT:")
    d = json.load(open(out))
    for arm in ("new", "old"):
        sub = [c for c in d["cells"] if c.get("legend") == arm and c.get("loaded")]
        varied = sum(1 for c in sub if len({t["token"] for t in (c.get("turns") or [])}) > 1)
        solved = sum(1 for c in sub if c.get("solved") is True)
        print(f"    arm {arm:4s}  n={len(sub)}  varied {varied}/{len(sub)}  solved {solved}/{len(sub)}")
    print()
    nw = [c for c in d["cells"] if c.get("legend") == "new" and c.get("loaded")]
    if nw:
        allvar = all(len({t["token"] for t in (c.get("turns") or [])}) > 1 for c in nw)
        print(f"  VERDICT: new-arm varied in {'EVERY' if allvar else 'NOT EVERY'} rep "
              f"-> {'(a) the population run saw the OLD prompt' if allvar else '(b) granite IS VARIABLE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
