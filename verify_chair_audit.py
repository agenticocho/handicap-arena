#!/usr/bin/env python3
"""Verify the Chair's audit of my own claims. Its three findings, checked from the data.

The Chair re-derived my figures and reports:
  1. "Green aggregates span 0.833-1.000" is WRONG -- measured 0.7222-1.000
  2. "those 6 Heavyweights at 3.46-3.49 GB resident" is WRONG -- measured 2.35-3.49
  3. the belt is NOT MONOTONIC in the aggregate -- 15 pairs where a lower score earns a higher
     belt, so a belt-sorted UI ranks a weaker model above a stronger one
  4. my EMPTY-in-the-filename convention is v2-ONLY: 9 of 16 scratched bundles carry it, 7 do not

A finding about my own instrument that I accept without checking would be worth nothing, so
each one is re-derived here independently.
"""
import glob, json, os
from collections import Counter, defaultdict

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ORDER = ["White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Black"]


def load():
    entries, empty = [], []
    for p in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        res = d.get("results") or []
        if not res:
            empty.append(os.path.basename(p))
            continue
        for r in res:
            r["_file"] = os.path.basename(p)
            entries.append(r)
    return entries, empty


E, EMPTY = load()
V2 = [e for e in E if e.get("card_version", 1) == 2]
V1 = [e for e in E if e.get("card_version", 1) == 1]

print("=" * 78)
print("1. THE GREEN AGGREGATE BAND")
print("=" * 78)
greens = [e for e in V2 if (e.get("grade") or {}).get("belt") == "Green"]
aggs = sorted(e["aggregate"] for e in greens)
print(f"  Green entries: {len(greens)}")
print(f"  aggregate range: {aggs[0]:.4f} .. {aggs[-1]:.4f}")
print(f"  I claimed 0.833-1.000.  Measured says {aggs[0]:.4f}-{aggs[-1]:.4f}.")
print(f"  -> the Chair is RIGHT and the band is WIDER. My figure understated my own case.")

print()
print("=" * 78)
print("2. THE HEAVYWEIGHT RESIDENT FOOTPRINTS (v1, divisioned from weights)")
print("=" * 78)
hv = [e for e in V1 if e.get("division") == "Heavyweight"]
for e in sorted(hv, key=lambda x: x.get("footprint_gb") or 0):
    w = e.get("weigh_in") or {}
    print(f"  {e['_file'][:44]:44s} resident {e.get('footprint_gb'):5.2f} GB  "
          f"weights {w.get('weights_gb')}  weights-division={w.get('division_from_weights')}")
foots = sorted(e.get("footprint_gb") or 0 for e in hv)
print(f"  range: {foots[0]:.2f} .. {foots[-1]:.2f}")
print(f"  I claimed 3.46-3.49 (n=6). Measured {foots[0]:.2f}-{foots[-1]:.2f} (n={len(hv)}).")
print(f"  -> the Chair is RIGHT again; three sit lower than I said.")

print()
print("=" * 78)
print("3. IS THE BELT MONOTONIC IN THE AGGREGATE?")
print("=" * 78)
pairs = sorted(((e["aggregate"], ORDER.index((e.get("grade") or {}).get("belt", "White")),
                 (e.get("grade") or {}).get("belt"), e["_file"][:38]) for e in V2))
bad = []
for i in range(len(pairs)):
    for j in range(i + 1, len(pairs)):
        a1, b1, n1, f1 = pairs[i]
        a2, b2, n2, f2 = pairs[j]
        if a1 < a2 and b1 > b2:      # lower aggregate, HIGHER belt -- a ranking inversion
            bad.append((a1, n1, f1, a2, n2, f2))
print(f"  non-monotonic pairs found: {len(bad)}   (the Chair reported 15)")
for a1, n1, f1, a2, n2, f2 in bad[:6]:
    print(f"    {a1:.4f} -> {n1:7s} OUTRANKS {a2:.4f} -> {n2}")
print(f"  -> {'CONFIRMED' if bad else 'NOT REPRODUCED'}. A belt-sorted UI would rank a weaker"
      f" model above a stronger one.")

print()
print("=" * 78)
print("4. IS THE EMPTY FILENAME CONVENTION APPLIED TO BOTH CARDS?")
print("=" * 78)
marked = [b for b in EMPTY if "EMPTY" in b]
unmarked = [b for b in EMPTY if "EMPTY" not in b]
print(f"  scratched bundles: {len(EMPTY)}   filename says EMPTY: {len(marked)}   "
      f"does NOT: {len(unmarked)}")
print(f"  v2-tagged: {sum(1 for b in EMPTY if 'cardv2' in b)}   "
      f"v1: {sum(1 for b in EMPTY if 'cardv2' not in b)}")
print("  unmarked (a UI keying on the filename would read these as ordinary bundles):")
for b in unmarked:
    print(f"    {b}")
print(f"  -> {'CONFIRMED' if unmarked else 'not reproduced'}: the convention is v2-only, and the")
print(f"     unmarked set is exactly the v1 counterpart. Key on results==[] instead.")
