#!/usr/bin/env python3
"""SOKOBAN -- THE REPORT, DERIVED FROM THE ARTIFACT.

WHY THIS EXISTS RATHER THAN A SUMMARY PRINTED AT THE END OF THE RUN.

The first run printed a summary line that DISAGREED WITH ITS OWN RECORD:
    printed   not_an_action  2      <- a COUNT OF CELLS WITH A NONZERO COUNTER
    true                80      <- the SUM OF THE COUNTER
    printed   solved         1      <- supported by NO ROW in the artifact
    true                     0

Two defects in one line: A COUNT OF ENTRIES IS NOT THE SUM OF VALUES, and a number nobody can trace back to
a row. So the run no longer prints a verdict. THE REPORT IS COMPUTED FROM THE RECORD, HERE, AT READ TIME.

    A SUMMARY ACCUMULATED DURING A RUN IS A SECOND COPY OF THE TRUTH, AND TODAY HAS BEEN ABOUT WHAT SECOND
    COPIES DO. This one is derived, or it is not printed.

    python3 sokoban_report.py [probes/SOKOBAN_FIRST_RUN.json]
"""
import json
import os
import sys

COUNTERS = ["moves", "attempted", "blocked", "not_an_action", "give_up"]


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "probes", "SOKOBAN_FIRST_RUN.json")
    d = json.load(open(p))
    rows = d["cells"] if isinstance(d, dict) and "cells" in d else d
    if isinstance(d, dict) and d.get("VOID"):
        print("  *** THIS ARTIFACT IS VOID-BANNERED AND IS NOT A RATE ***")
        print()

    loaded = [r for r in rows if r.get("loaded") is True]
    not_loaded = [r for r in rows if r.get("loaded") is not True]
    levels = sorted({r["level"] for r in rows})

    print("=" * 92)
    print("SOKOBAN -- FROM THE RECORD, NOT FROM A SUMMARY")
    print("=" * 92)
    print(f"  cells {len(rows)}   PLAYED {len(loaded)}   DID NOT LOAD {len(not_loaded)}")
    print()

    print("  PER CELL -- the five counters, NEVER MERGED")
    print(f"  {'entrant':32s} {'level':14s} {'ended':19s} " + " ".join(f"{c[:9]:>9s}" for c in COUNTERS))
    for r in rows:
        if r.get("loaded") is not True:
            print(f"  {r['entrant'][:32]:32s} {r['level']:14s} DID NOT LOAD -- {r.get('why')}")
            continue
        vals = " ".join(f"{r.get(c, 0):9d}" for c in COUNTERS)
        print(f"  {r['entrant'][:32]:32s} {r['level']:14s} {r.get('ended', '?'):19s} {vals}")
    print()

    print("  PER LEVEL -- sums over PLAYED cells only, so a non-loading model cannot vote")
    print(f"  {'level':16s} {'played':>6s} {'solved':>6s} {'gaveup':>6s} " +
          " ".join(f"{c[:9]:>9s}" for c in COUNTERS))
    for lv in levels:
        sub = [r for r in loaded if r["level"] == lv]
        vals = " ".join(f"{sum(r.get(c, 0) for r in sub):9d}" for c in COUNTERS)
        print(f"  {lv:16s} {len(sub):6d} {sum(1 for r in sub if r.get('solved') is True):6d} "
              f"{sum(1 for r in sub if r.get('give_up')):6d} {vals}")
    print()

    print("  REASON COUNTS, reported SEPARATELY FROM EVERY TOTAL ABOVE")
    reasons = {}
    for r in not_loaded:
        k = (r.get("why") or "unknown").split(" -- ")[0][:44]
        reasons[k] = reasons.get(k, 0) + 1
    print(f"    played          {len(loaded)}")
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"    did not load    {v}   {k}")
    print("    (A POPULATION THAT NEVER RAN IS NOT EVIDENCE ABOUT THE POPULATION.)")
    print()

    print("  THE SPLIT PER LEVEL, as fractions -- the gate's own shape")
    for lv in levels:
        sub = [r for r in loaded if r["level"] == lv]
        if not sub:
            continue
        att = sum(r.get("attempted", 0) for r in sub) or 1
        print(f"    {lv:16s} blocked {sum(r.get('blocked', 0) for r in sub)/att:.3f}   "
              f"not_an_action {sum(r.get('not_an_action', 0) for r in sub)/att:.3f}   "
              f"give_up {sum(r.get('give_up', 0) for r in sub)/att:.3f}")
    print()
    print(f"  HEAD-READ CHECK -- the first token each played entrant actually produced")
    for r in loaded:
        t = [x.get("token") for x in (r.get("turns") or [])][:3]
        print(f"    {r['entrant'][:32]:32s} {r['level']:14s} {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
