#!/usr/bin/env python3
"""THE FIFTH MEMBER OF THE FAMILY -- audit the v4 bundle for stand-ins.

Chilly's family, from its ruling:

    a greedy regex's extraction   ->  the model's actual output
    _EMPTY_ in a filename         ->  the reason the bundle was empty
    a slot name surviving v3->v4  ->  the item the slot used to mean
    a displayed percentage        ->  the measured rate

Every one is a COMPACT, WELL-FORMED STAND-IN, trusted after the thing it stands for had changed or been
approximated, and every one looked correct at the point of use.

This is that rule applied FORWARD, to my own artifact, rather than waiting for instance five to be found
by someone else. The question per field: does this field store a DERIVED or APPROXIMATED form of
something whose PRIMITIVE is also in the record?

The known candidate is `aggregate`. It was stored ROUNDED in some bundles earlier in this project
(`0.8889` beside a raw `0.8888666666666666`), which is exactly a rendering kept where the value should be.
So: is the aggregate derivable from primitives that are also present, and is it stored rounded?
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(RESULTS, "*cardv4*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        if not (d.get("results") or []):
            continue
        for e in d["results"]:
            rd = (e.get("rounds") or {}).get("R1_fencing") or {}
            if rd:
                rows.append((os.path.basename(p), e, rd))
    if not rows:
        print("no measured v4 bundles yet")
        return 0

    print(f"auditing {len(rows)} measured v4 entries for stand-ins whose primitive is also present\n")

    exact = rounded = mismatch = notderivable = 0
    worst = None
    for f, e, rd in rows:
        # the primitives
        wins = rd.get("wins")
        trials = rd.get("trials")
        items = rd.get("items") or {}
        from_items = sum((it.get("score") or 0) for it in items.values()) / len(items) if items else None
        agg = e.get("aggregate")

        if wins is None or trials is None or not trials:
            notderivable += 1
            continue
        from_round = wins / trials
        if agg is None:
            notderivable += 1
            continue
        # is it the exact ratio, or a rounded rendering?
        if agg == from_round:
            exact += 1
        elif from_round and abs(agg - from_round) < 5e-5:
            rounded += 1
            if worst is None:
                worst = (f, agg, from_round)
        else:
            mismatch += 1
            if worst is None:
                worst = (f, agg, from_round)
        # and does the round agree with the items it holds?
        if from_items is not None and abs(from_round - from_items) > 1e-9 and mismatch == 0:
            mismatch += 1

    print(f"  aggregate == wins/trials EXACTLY          : {exact}")
    print(f"  aggregate is a ROUNDED wins/trials        : {rounded}   <-- the stand-in")
    print(f"  aggregate does NOT match its primitives   : {mismatch}")
    print(f"  not derivable from this record            : {notderivable}")
    if worst:
        print(f"\n  example: stored {worst[1]!r}  vs derived {worst[2]!r}")
    print()
    if rounded == 0 and mismatch == 0:
        print("  VERDICT: no stand-in found in this field. The aggregate IS the ratio, and `wins` and")
        print("  `trials` are both present -- so the primitive is in the record and the rendering is not")
        print("  being trusted in its place. v4 does not have the fifth member.")
    else:
        print("  VERDICT: the aggregate is a RENDERING stored where the value should be. `wins` and")
        print("  `trials` are both in the record, so the exact value is DERIVABLE and the stored form")
        print("  loses precision -- 0.9444333 != 0.9444 breaks stable sorts and equality tests.")
        print("  Remedy: derive on read, never compare the stored form. Or store the primitive only.")
    print()
    print("  WHY THIS AUDIT EXISTS AT ALL: the family rule was found by accumulating instances. Applying")
    print("  it forward is the difference between having a rule and having a check. The footer states")
    print("  nothing about the outcome -- an earlier version of this file ended by saying the answer")
    print("  'happens to be clean' BEFORE the branch that decides it, which is the same two-numbers-in-")
    print("  one-output defect the audit is looking for, committed by the audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
