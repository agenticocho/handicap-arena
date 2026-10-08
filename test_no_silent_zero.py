#!/usr/bin/env python3
"""NO SILENT ZERO -- a bundle item that scores 0.0 must say WHY, and must carry what the model said.

THE DEFECT THIS EXISTS FOR. `arena.py`'s trial loop caught a serving exception and `continue`d. That
discarded the raw slot and left `why` at its initial "", so:
  * the item recorded score 0.0
  * the guard below was `if npass == 0 and why:` -- "" is falsy, so NO reason key was written
  * the bundle-writing path read `reason = r.get("why") or r.get("reason")` -> None
  * `raw = []`
`Cloudflare_clef-Q4_K_M :: R1.5` in the v3 field is exactly that triple: score 0.0, reason None, raw
absent. A machine failure recorded as a capability result, with nothing left to examine. FINDING 007's
hole, one level down.

THIS CHECK IS EXPECTED TO FAIL ON THE BUNDLES THAT EXIST TODAY. That is the point: a test that cannot
fail on the defect it was written for is decoration. It goes green only for fields written after the
fix, which is the honest scope of a fix.

Usage: test_no_silent_zero.py [results_dir]
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results")


def main():
    silent = []
    total_items = 0
    for p in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        for e in (d.get("results") or []):
            cv = e.get("card_version")
            for rid, rd in (e.get("rounds") or {}).items():
                for iid, it in (rd.get("items") or {}).items():
                    total_items += 1
                    score = it.get("score")
                    if score != 0:
                        continue
                    reason = it.get("reason")
                    raw = it.get("raw")
                    has_raw = bool(raw) if not isinstance(raw, list) else any(
                        bool(x) for x in raw)
                    if not reason and not has_raw:
                        silent.append((os.path.basename(p), cv, rid, iid, it.get("truncated")))

    print(f"scanned {total_items} item records in {RESULTS}")
    print()
    if not silent:
        print("PASS -- every 0.0 carries a reason or a raw. No silent zero.")
        return 0
    print(f"FAIL -- {len(silent)} item(s) scored 0.0 with NO reason and NO raw.")
    print("  A zero that cannot be explained cannot be argued with, and this is the pair of fields")
    print("  that make it explainable. Pre-fix bundles are expected to appear here.")
    print()
    for f, cv, rid, iid, tr in silent:
        print(f"  card_version={cv}  {rid:14} {iid:34} truncated={tr}")
        print(f"      {f}")
    print()
    print("This check is RED BY DESIGN on the current field. It is the conformance test for C3 of")
    print("CARD_v4.md and it must be green before a v4 field is treated as auditable.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
