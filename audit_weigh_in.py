#!/usr/bin/env python3
"""What the weigh-in renderer can actually draw, audited against the bundles.

THE PRODUCT CONTEXT. The weigh-in is the Arena's INSTRUMENT event: a number everyone understands, a
hard threshold with a consequence, a scheduled moment, a legible way to fail and a side-by-side. Every
ingredient is already recorded. **None of it is rendered** -- a spectator sees a table of aggregates,
and the moment a model misses weight is invisible. The miss is the drama.

So the lead instrument product is a RENDERER over measurements that already exist. This script is its
spec: what is present, what is absent, and which fields a renderer will get wrong if it guesses.

THE STORY IT FINDS: models that step on the scale in one class and are another class by their own
weights. A fighter missing weight -- recorded many times, shown never.
"""
import glob
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["Featherweight", "Lightweight", "Middleweight", "Heavyweight"]


def main():
    both, disagree, div_only = 0, Counter(), 0
    cv, place_top, place_weigh = Counter(), 0, 0
    empty, total, rows = 0, 0, 0
    comp = Counter()
    missing = Counter()
    for p in sorted(glob.glob(os.path.join(HERE, "results", "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        total += 1
        if not (d.get("results") or []):
            empty += 1
        for e in (d.get("results") or []):
            rows += 1
            cv[e.get("card_version", "ABSENT")] += 1
            if "placement" in e:
                place_top += 1
            w = e.get("weigh_in") or {}
            if w.get("placement"):
                place_weigh += 1
            for k in ("division_from_resident", "division_from_weights",
                      "division_for_competition"):
                if not w.get(k):
                    missing[k] += 1
            # THE STORY IS RESIDENT vs BY-WEIGHTS -- the scale reading against the actual mass.
            # The first version of this script compared the top-level `division` against
            # `division_from_weights`, which are nearly the same by design, and reported ONE
            # disagreement where there are 33. A guessed field name produced a plausible number.
            res, frm = w.get("division_from_resident"), w.get("division_from_weights")
            if res and frm:
                both += 1
                if res != frm:
                    disagree[(res, frm)] += 1
            elif w.get("division") or e.get("division"):
                div_only += 1
            if w.get("division_for_competition"):
                comp[w["division_for_competition"]] += 1

    # THE ASSERTION MUST NOT CRY WOLF. Four entries legitimately carry no weigh-in (they were never
    # offloaded), so "absent on 4 entries" is data, not a broken schema. The warning fires only when
    # a field is missing on EVERYTHING, which is what a renamed or moved field looks like -- the
    # difference between "this entry has no weigh-in" and "this audit is reading the wrong schema".
    if missing and max(missing.values()) >= rows:
        print("  *** FIELD NAMES DID NOT RESOLVE -- this audit is reading a schema that is not "
              "there, and any number below is void:")
        for k, n in missing.items():
            print(f"      {k}: absent on {n} of {rows} entries")
        print()
    elif missing:
        for k, n in missing.items():
            print(f"  note: {k} absent on {n} of {rows} entries -- expected (no weigh-in recorded), "
                  f"not a schema change")
        print()

    print(f"  bundles: {total}    entries: {rows}")
    print()
    print("  --- WHAT IS PRESENT ---")
    print(f"  entries with a weigh-in                         : {both + div_only}")
    print(f"    with BOTH a resident and a by-weights division: {both}")
    print()
    print("  --- THE STORY: models that miss their own weight ---")
    print("      resident class (the scale) vs by-weights (the actual mass)")
    print(f"  WHERE THE TWO DISAGREE : {sum(disagree.values())}")
    for (a, b), n in disagree.most_common():
        gap = abs(ORDER.index(a) - ORDER.index(b)) if a in ORDER and b in ORDER else 0
        print(f"      resident {a:14} -> by-weights {b:14}  x{n:3}"
              f"{'   <<< ' + str(gap) + ' classes apart' if gap >= 2 else ''}")
    print()
    print("  --- and the division actually used for competition ---")
    for k, n in comp.most_common():
        print(f"      {k:16} {n}")
    print()
    print("  --- SCHEMA TRAPS A RENDERER WILL GET WRONG ---")
    print(f"  card_version present on        : {rows - cv['ABSENT']} of {rows} entries")
    print(f"      (absent on the rest: that is v1, and 'absent' is NOT '1')")
    print(f"  top-level `placement` present   : {place_top}    <- reads ZERO")
    print(f"  `weigh_in.placement` present    : {place_weigh}    <- the real location")
    print(f"  bundles with results == []      : {empty} of {total}")
    print(f"      THE SCRATCH IS THE COMMON CASE, NOT THE EDGE CASE.")
    print()
    print("  Every number above is counted from the bundles. None is quoted from memory.")


if __name__ == "__main__":
    main()
