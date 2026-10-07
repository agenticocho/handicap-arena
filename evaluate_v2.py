#!/usr/bin/env python3
"""Evaluate the v2 field against the criterion frozen in CARD_v2.md BEFORE the run.

A criterion chosen after seeing the results is not a criterion. These four were written down in
advance, including the one that can embarrass the work: if criterion 4 fails while 1-3 pass, the
honest reading is that the hardening worked by DIFFICULTY rather than by DISCRIMINATION, and that
gets reported as such rather than buried.
"""
import glob, json, os, sys
from collections import Counter

RESULTS = "/home/chilly1/workspace/ocho_arena/results"
TRAPS = {"R2_chess::R2.4_no_tool_correct": "no tool fits the request",
         "R3_pitstop::R3.6_already_correct": "the code is already correct"}
ORDER = ["White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Black"]


def load(card_version=2):
    out, empty = [], []
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
            if r.get("card_version", 1) == card_version:
                r["_file"] = os.path.basename(p)
                out.append(r)
    return out, empty


def trap_failures(entries):
    """A trap is only a trap if models fail it. Read the per-item scores."""
    fails = {k: [] for k in TRAPS}
    passed = {k: 0 for k in TRAPS}
    for e in entries:
        flat = {}
        for rid, rd in (e.get("rounds") or {}).items():
            for item, v in (rd.get("items") or {}).items():
                flat[f"{rid}::{item}"] = v
        for k in TRAPS:
            v = flat.get(k)
            if v is None:
                continue
            if (v.get("score") or 0) >= 0.999:
                passed[k] += 1
            else:
                fails[k].append(e["_file"].replace("_cardv2_autofit_neutral_ctx8192_mt3000.json", ""))
    return fails, passed


def main():
    entries, empty = load(2)
    print(f"=== v2 field ===")
    print(f"  graded entries : {len(entries)}")
    print(f"  empty/scratched: {len(empty)}")
    if not entries:
        print("  nothing to evaluate")
        return

    belts = Counter((e.get("grade") or {}).get("belt", "?") for e in entries)
    print(f"  belts          : " + "  ".join(f"{b} {belts.get(b,0)}" for b in ORDER if belts.get(b)))
    aggs = [round(e.get("aggregate") or 0, 3) for e in entries]
    dist = Counter(aggs)

    print("\n=== aggregate distribution ===")
    for v, n in sorted(dist.items(), reverse=True):
        print(f"  {v:5.3f}  {n:3d}  " + "#" * n)

    n = len(entries)
    green = belts.get("Green", 0)
    top_val, top_n = dist.most_common(1)[0]
    low = sum(1 for a in aggs if a < 0.34)

    print("\n=== CRITERION (frozen in CARD_v2.md before the run) ===")
    c1 = (green / n) < 0.25
    print(f"  1. saturation: Green {green}/{n} = {green/n:.1%}  "
          f"(v1 was 52%)  -> needs <25%   {'PASS' if c1 else 'FAIL'}")
    c2a = len(dist) >= 6
    c2b = (top_n / n) <= 0.40
    print(f"  2. gradient  : {len(dist)} distinct aggregate values (v1 had 4) -> needs >=6   "
          f"{'PASS' if c2a else 'FAIL'}")
    print(f"     no value >40%: top is {top_val} at {top_n}/{n} = {top_n/n:.1%}          "
          f"{'PASS' if c2b else 'FAIL'}")
    c3 = low >= 4
    print(f"  3. zero-side : {low} models below 0.34 -> needs >=4             "
          f"{'PASS' if c3 else 'FAIL'}")

    fails, passed = trap_failures(entries)
    detail = {}
    c4 = True
    for k, label in TRAPS.items():
        f = len(fails[k])
        detail[k] = {"failed": f, "passed": passed[k]}
        print(f"  4. trap      : {label:34s} failed by {f:2d}, passed by {passed[k]:2d}  "
              f"-> needs >=3 fails  {'PASS' if f >= 3 else 'FAIL'}")
        c4 = c4 and f >= 3

    print("\n=== VERDICT ===")
    print(f"  criterion 1 {c1}   2 {c2a and c2b}   3 {c3}   4 {c4}")
    if c1 and c2a and c2b and c3 and c4:
        print("  ALL FOUR PASS — the card discriminates, and it does so by near-miss rather than")
        print("  by uniform difficulty: the traps catch models that would otherwise sweep.")
    elif c1 and c2a and c2b and c3 and not c4:
        print("  HARDENING BY DIFFICULTY, NOT DISCRIMINATION. Criteria 1-3 pass but the trap items")
        print("  are not biting, which means the card got harder without getting more informative.")
        print("  This is the outcome CARD_v2.md committed to reporting rather than burying.")
    else:
        print("  Not all criteria met. Report as-is; the criteria were frozen in advance and do")
        print("  not move to accommodate the result.")

    print("\n=== the trap failures, named ===")
    for k, names in fails.items():
        print(f"  {k}  ({TRAPS[k]})")
        for nm in names[:12]:
            print(f"      {nm}")


if __name__ == "__main__":
    main()
