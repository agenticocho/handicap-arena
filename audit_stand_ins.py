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
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")



def main():
    rows = []
    _rows = scope("*cardv4*.json")
    print_scope(_rows, "*cardv4*.json")
    for p in [p for _k, _b, hits in _rows for p in hits]:
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

        if wins is None or trials is None or not trials or agg is None:
            notderivable += 1
            continue
        from_round = wins / trials
        # THE TEST WAS WRONG. `agg == from_round` conflates "the stored value was rounded" with
        # "rounding changed nothing" -- and I reported the second as the first.
        #
        # Chilly ran its own predicate and got 29 aggregates, EVERY ONE rounded to four decimals:
        # 1.0 x10, 0.6667 x8, 0.5 x3, 0.8333 x2, 0.3333 x2, 0.8889, 0.7222, 0.6111, 0.0. Zero exact.
        # My script said "14 exact" because for a perfect score 6/6 = 1.0, and `1.0 == 1.0` is True --
        # so a rounded value counted as unrounded whenever the rounding happened to be a no-op.
        #
        # That split reads as TWO STORAGE PATHS, which is what I claimed. There is ONE path -- round to
        # 4dp -- and it loses precision on 15 of 29 and not on 14. The numbers were right and the
        # sentence was wrong, in the audit written by the person who had just been corrected for
        # exactly that. A comparison against a rendering is not a statement about the rendering.
        _dp = len(str(agg).split(".")[-1]) if "." in str(agg) else 0
        _lossy = (round(from_round, 4) != from_round)
        if agg != round(agg, 4):
            notderivable += 1          # stored at full precision -- path (b)
        elif _lossy:
            rounded += 1               # rounded AND the rounding lost precision
            if worst is None:
                worst = (f, agg, from_round)
        else:
            exact += 1                 # rounded, but the rounding was a no-op at 4dp
        if _dp > 4:
            mismatch += 1

    print(f"  every aggregate is stored ROUNDED to 4dp  : {exact + rounded} of {exact + rounded + notderivable}")
    print(f"    ...and the rounding LOST precision       : {rounded}   <-- the stand-in")
    print(f"    ...and the rounding was a NO-OP at 4dp   : {exact}   (ratios exactly representable)")
    print(f"  stored at full precision (no rounding)    : {notderivable}")
    print(f"  aggregate more than 4dp (path b evidence) : {mismatch}")
    if worst:
        print(f"\n  example: stored {worst[1]!r}  vs derived {worst[2]!r}")
    print()
    print("  PREDICATE, so this can be reproduced or refuted: glob results/*cardv4*.json, json parses,")
    print("  harness == 'handicap-arena', non-empty results; per ENTRY row take `aggregate` and the")
    print("  ROUND row's `wins`/`trials`; a value is ROUNDED iff `agg == round(agg, 4)`, and LOSSY iff")
    print("  `round(wins/trials, 4) != wins/trials`.")
    print()
    print("  AND THE CORRECTION THAT PRODUCED THIS: Chilly ran its own predicate and got 29 aggregates,")
    print("  every one rounded to four decimals -- 1.0 x10, 0.6667 x8, 0.5 x3, 0.8333 x2, 0.3333 x2,")
    print("  0.8889, 0.7222, 0.6111, 0.0 -- zero exact. My first test was `agg == wins/trials`, which is")
    print("  True for a perfect score because 6/6 = 1.0, so it counted a ROUNDED value as UNROUNDED")
    print("  whenever the rounding happened to be a no-op. The split read as two storage paths. THERE IS")
    print("  ONE PATH, and 14 of 29 are unaffected by it. The numbers were right and the sentence was")
    print("  wrong -- a comparison against a rendering is not a statement about the rendering, which is")
    print("  the fifth member of the family, committed inside the audit that found it.")
    print()
    print("  Remedy unchanged: COMPARE THE PRIMITIVE. `wins`/`trials` are the record; `aggregate` is a")
    print("  display, and 15 of 29 display values differ from the ratio they stand for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
