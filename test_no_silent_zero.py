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
    silent_bundles = []
    total_bundles = 0
    for p in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        total_bundles += 1
        # BUNDLE-LEVEL SILENCE, the level above the item. A bundle whose results list is empty never
        # reached a scoring path, so the item-level fix cannot apply to it and the RUNNER must write the
        # class. Chilly measured four of the first 33 v4 bundles shipping `results: []` with the reason
        # present in the LOG and absent from the ARTIFACT -- a label with nothing behind it, and a
        # consumer counting files reads it as a completed entrant.
        if not (d.get("results") or []):
            if not any(k in d for k in ("failure", "empty_reason", "failure_class")):
                silent_bundles.append((os.path.basename(p), d.get("version")))
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

    print(f"scanned {total_items} item records in {total_bundles} bundles, {RESULTS}")
    print()
    rc = 0
    if silent_bundles:
        print(f"FAIL -- {len(silent_bundles)} bundle(s) with an EMPTY results list and NO failure record.")
        print("  The reason exists (run_card.py computes it) and went to stdout and the log. Neither is")
        print("  the artifact. A bundle that never reached scoring has no scoring path to write the")
        print("  class, so the RUNNER writes it -- pre-scoring failures are C3's job too.")
        for f, v in silent_bundles[:12]:
            print(f"    version={v}  {f}")
        rc = 1
    else:
        print("PASS -- no bundle ships an empty results list without saying why.")
    print()
    if not silent:
        print("PASS -- every 0.0 item carries a reason or a raw. No silent zero.")
        return rc
    print(f"FAIL -- {len(silent)} item(s) scored 0.0 with NO reason and NO raw.")
    print("  A zero that cannot be explained cannot be argued with, and this is the pair of fields")
    print("  that make it explainable. Pre-fix bundles are expected to appear here.")
    print()
    for f, cv, rid, iid, tr in silent:
        print(f"  card_version={cv}  {rid:14} {iid:34} truncated={tr}")
        print(f"      {f}")
    print()
    print("This check is RED BY DESIGN on the pre-fix field. It is the conformance test for C3 of")
    print("CARD_v4.md and it must be green before a field is treated as auditable.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
