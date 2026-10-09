#!/usr/bin/env python3
"""CARD v5's verdict, computed FROM THE ARTIFACTS. Read-only: it writes nothing.

"The artifact should say it" -- so this reads the bundles and prints the gate and the item criteria
itself, rather than restating a number someone sent in a message.

AND THE YIELD NUMERATOR IS THE CORRECTED ONE. A resumed run's `done` counts only what THIS invocation
measured; entrants skipped as already-measured are MEASUREMENTS, and leaving them out made the gate
unsatisfiable by construction. Here every measured bundle on disk counts, which is what the criterion
always meant.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_card as rc

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = "v5"
BAND = (0.15, 0.85)          # C1: an item must DISCRIMINATE -- neither saturated nor dead
FLOOR = 0.34                 # C2: the bottom of the range must be populated
C1_NEED = 4                  # of 6 items in band
C2_NEED = 5                  # entrants below the floor

# ---- the population, by the card's own rule -------------------------------------------------
rc.CARD = CARD
ents = rc.entrants()
planned, excluded, measured, missing = 0, [], [], []
for size, path, base in ents:
    stem = base.replace(".gguf", "")
    if rc.permanently_failed(base):
        excluded.append(base)
        continue
    planned += 1
    bp = rc.bundle_path(stem)
    if rc.bundle_has_measurement(bp):
        measured.append((base, bp))
    else:
        missing.append(base)

print("=" * 96)
print(f"CARD {CARD} -- VERDICT FROM THE ARTIFACTS")
print("=" * 96)
print(f"\nDENOMINATORS (card rule, not a filename count)")
print(f"  applicants (library - EXCLUDE_PAT)  {len(ents)}")
print(f"  planned    (minus permanent fails)  {planned}")
print(f"  excluded   (by RECORD)              {len(excluded)}")
print(f"  measured   (bundle carries results) {len(measured)}")
if missing:
    print(f"  NOT measured                        {len(missing)}: {missing[:5]}")

g = rc.gate_ratios(planned=planned, attempted=planned, measured=len(measured))
print(f"\nGATE  (a fraction of the field that ran -- CARD_v5.md)")
print(f"  COVERAGE attempted/planned   {planned}/{planned} = {g['coverage']:.3f}  (>= 0.95)  "
      f"{'OK' if g['coverage_ok'] else 'UNMET'}")
print(f"  YIELD    measured/attempted  {len(measured)}/{planned} = {g['yield']:.3f}  (>= 0.85)  "
      f"{'OK' if g['yield_ok'] else 'UNMET'}")
print(f"  GATE {'MET' if g['gate_met'] else 'UNMET'}")
if not g["gate_met"]:
    print("\nOUTCOME 1 -- NO VERDICT: THE FIELD DID NOT COMPLETE.")
    print("  Calling nothing a pass or a fail, per the card.")
    raise SystemExit(0)

# ---- C1: per-item discrimination ------------------------------------------------------------
per_item = {}
agg = []
for base, bp in measured:
    try:
        d = json.load(open(bp, encoding="utf-8"))
    except Exception:
        continue
    for r in (d.get("results") or []):
        if r.get("aggregate") is not None:
            agg.append(r["aggregate"])
        for rk, rv in (r.get("rounds") or {}).items():
            for item_id, it in (rv.get("items") or {}).items():
                per_item.setdefault(item_id, []).append(it.get("score"))

print(f"\nC1  PER-ITEM DISCRIMINATION -- band {int(BAND[0]*100)}-{int(BAND[1]*100)}%, need >= {C1_NEED} of 6")
in_band = 0
for item_id in sorted(per_item):
    scores = [s for s in per_item[item_id] if s is not None]
    rate = sum(scores) / len(scores) if scores else 0.0
    ok = BAND[0] <= rate <= BAND[1]
    in_band += ok
    why = "IN BAND" if ok else ("saturated" if rate > BAND[1] else "dead (floor)")
    print(f"    {item_id:44s} {rate:.3f}  {len(scores):3d} scores  {why}")
print(f"    -> {in_band} of 6 in band -- C1 {'PASS' if in_band >= C1_NEED else 'FAIL'}")

# ---- C2: is the floor populated? ------------------------------------------------------------
below = [a for a in agg if a < FLOOR]
print(f"\nC2  THE FLOOR IS POPULATED -- entrants below {FLOOR}, need >= {C2_NEED}")
print(f"    {len(below)} of {len(agg)} entrants below {FLOOR} -- C2 {'PASS' if len(below) >= C2_NEED else 'FAIL'}")

# ---- the verdict ----------------------------------------------------------------------------
print("\n" + "=" * 96)
if in_band >= C1_NEED and len(below) >= C2_NEED:
    print("VERDICT: PASS on both criteria.")
else:
    print(f"VERDICT: FAIL on the item criteria -- "
          f"C1 {in_band}/6 (need {C1_NEED}), C2 {len(below)}/{len(agg)} (need {C2_NEED}).")
    print("  THE FIELD IS COMPLETE AND THE INSTRUMENT RAN. This is a FAIL on the items, not a scope:")
    print("  every criterion is a DISCRIMINATION criterion, and the ceiling means the suite is too easy")
    print("  for this population rather than that the scoring is wrong.")
print("=" * 96)
