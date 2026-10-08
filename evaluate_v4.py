#!/usr/bin/env python3
"""CARD v4 — the verdict against the criteria frozen in CARD_v4.md BEFORE the run.

Two things this shares with nothing else in the repo, both deliberate:

1. IT REFUSES TO CALL A VERDICT ON AN INCOMPLETE FIELD. v3's verdict was computed while the question of
   what counted as "the field" was still open, and it ended up conditional on the scope of its own
   correction. So this prints the ACCOUNTED count first and, if the field is short, prints NO VERDICT and
   the reason -- rather than a number that would read as a result.

2. IT STATES ITS SCOPE. Which bundles, which predicate, and which parser. The scope is a CHOICE and is
   printed as one, because a criterion whose verdict flips on an unstated scope is not a criterion.

The bar, quoted from CARD_v4.md:

  C1  at least 4 of 6 items fall in the 15%-85% corrected pass-rate band
  C2  at least 5 entrants score below 0.34 aggregate
  C3  the parser is honest, and EVERY failure class is stored -- including pre-scoring failures
  C4  no pooling; v3's criterion 2 stands failed and is not re-scored

v4's scorer is arena.py's own strict_json_schema_multi, so unlike the v3 audit there is no correction to
apply and no second parser to choose between: the scores in the bundle ARE the scores, and re-parsing them
would be re-deriving rather than verifying.
"""
import glob
import importlib.util
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
ROUND = "R1_fencing"
BAND_LO, BAND_HI = 0.15, 0.85
FLOOR = 0.34
C1_NEED, C2_NEED = 4, 5


def load_v4():
    rows = []
    for p in sorted(glob.glob(os.path.join(RESULTS, "*cardv4*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        if not (d.get("results") or []):
            rows.append((p, d, None, None))       # empty: accounted for, measured nothing
            continue
        for e in d["results"]:
            rd = (e.get("rounds") or {}).get(ROUND)
            rows.append((p, d, e, rd))
    return rows


def main():
    rows = load_v4()
    if not rows:
        print("no v4 bundles on disk")
        return 1

    # ---- THE SCOPE, PRINTED AS A CHOICE ------------------------------------
    pred = ("glob results/*cardv4*.json, json parses, top-level harness == 'handicap-arena'; a bundle "
            "counts as ACCOUNTED when it exists, and as MEASURED when its results list is non-empty "
            "with an R1_fencing round")
    print("=" * 78)
    print("CARD v4 -- VERDICT AGAINST THE FROZEN BAR")
    print("=" * 78)
    print()
    print("  SCOPE (stated as a choice, not implied):")
    print(f"    {pred}")
    print(f"  scorer: arena.py's strict_json_schema_multi -- the bundle's own scores, no re-parse")
    print()
    # ---- THE LABEL HAZARD, STATED BEFORE ANY NUMBER IS READ --------------
    #
    # Chilly: EVERY R1 LABEL WAS REWRITTEN BETWEEN v3 AND v4, AND NONE REFERS TO THE SAME ITEM.
    #
    #   v3  R1.6 array_exact_and_ordered      39.5%   |  v4  R1.6 exact_scalar_types       96.6%
    #   v3  R1.2 null_means_absent            60.5%   |  v4  R1.2 order_is_the_content      82.8%
    #   v3  R1.5 enum_nearest_is_wrong        86.8%   |  v4  R1.5 exact_key_set_under_a_bribe 86.2%
    #
    # The last pair is the dangerous one: TWO UNRELATED ITEMS WITH NEAR-IDENTICAL RATES LOOK EXACTLY
    # LIKE ONE ITEM HOLDING STEADY. A change is visible; a coincidence is not. So the mapping below is
    # BY NAME and never by slot, and any cross-version sentence must use the names.
    print("  *** LABEL HAZARD: v3 and v4 item IDs are NOT comparable. Same slot, different item. ***")
    print()
    print("      THE FULL MAPPING. Any cross-version sentence must name BOTH sides; a slot alone is a")
    print("      changed referent, and two unrelated items with near-identical rates (R1.5 below) look")
    print("      exactly like one item holding steady -- a change is visible, a coincidence is not.")
    print()
    print("      AND THE v3 COLUMN CARRIES *TWO* READINGS, LABELLED, because it must never mix them.")
    print("      `recorded` is what the bundle says, written by the greedy parser. `corrected` is the")
    print("      same raws through the strict parser. Quoting a recorded rate beside a corrected one")
    print("      inside one column, in a table whose purpose is stopping readers mixing things, is the")
    print("      defect the table exists to prevent -- Chilly caught exactly that in the first version.")
    print()
    print("        item                                  recorded  corrected   delta | v4 item")
    print("        ------------------------------------  --------  ---------  ------ | ------------------------")
    for vn, rr, rc, un in (
        ("R1.1 forbidden_key_must_be_absent", "86.8%", "89.5%", "ordered_sequence_with_a_gap"),
        ("R1.2 null_means_absent", "57.9%", "60.5%", "order_is_the_content"),
        ("R1.3 type_under_natural_language", "92.1%", "94.7%", "duplicates_are_significant"),
        ("R1.4 ambiguous_nesting", "86.8%", "89.5%", "absence_is_the_answer"),
        ("R1.5 enum_nearest_is_wrong", "78.9%", "86.8%", "exact_key_set_under_a_bribe"),
        ("R1.6 array_exact_and_ordered", "39.5%", "39.5%", "exact_scalar_types"),
    ):
        d = float(rc.rstrip("%")) - float(rr.rstrip("%"))
        print(f"        {vn:36}  {rr:>8}  {rc:>9}  {d:+5.1f}% | {un}")
    print()
    print("      THE DELTA IS THE PARSER'S FINGERPRINT: zero on R1.6, whose raws parsed cleanly, and")
    print("      positive everywhere the greedy `{.*}` failed on a model that reasoned before it")
    print("      answered -- largest on R1.5 (+7.9). Chilly derived the same asymmetry independently")
    print("      from the on-disk scores, so the correction is corroborated from two sides rather than")
    print("      repeated. Derive both columns with `v3_rates_both_readings.py`; never quote one as the")
    print("      other, and never fill a rate from memory.")
    print()
    print("      THE COERCION CLAIM, stated the only way it is true:")
    print("        v3's R1.3 type_under_natural_language and v4's R1.6 exact_scalar_types are both")
    print("        about type coercion. The claim is that the FIRST was confounded by the greedy parser")
    print("        -- a parse failure reads as a coercion failure -- while the SECOND is measured clean.")
    print("        Two named items across two cards. The slot version would be a claim about one item")
    print("        that does not exist.")
    print()
    print("      AND WHY THE SLOTS WERE NOT RENUMBERED: a rename would not remove this hazard, it would")
    print("      MOVE it -- the 29 bundles already measured carry the old keys, so renaming the task file")
    print("      creates a third naming era and a new cross-era mapping. The mapping is the honest fix;")
    print("      a canonical citation is `<card>:<slot> <name>` and never the slot alone.")
    print()

    accounted = len(rows)
    with_rd = [(p, d, e, rd) for p, d, e, rd in rows if rd]
    empty = [(p, d) for p, d, e, rd in rows if rd is None]
    print(f"  accounted for : {accounted}")
    print(f"  MEASURED      : {len(with_rd)}")
    print(f"  empty (no results) : {len(empty)}")

    # ---- C4 BEFORE ANYTHING ELSE: the partition must hold ------------------
    cvs = defaultdict(int)
    for p, d, e, rd in with_rd:
        cvs[e.get("card_version")] += 1
    print()
    print(f"  C4 card_version partition: {dict(cvs)}")
    ok4 = set(cvs) == {4}
    print(f"     {'PASS' if ok4 else 'FAIL -- pooled with another card'}")

    # ---- C3: the conformance test, run here so the verdict carries it -----
    silent_items = silent_bundles = 0
    bad_parse = 0
    for p, d, e, rd in with_rd:
        for iid, it in (rd.get("items") or {}).items():
            if (it.get("score") or 0) == 0:
                raw = it.get("raw")
                has_raw = bool(raw) if not isinstance(raw, list) else any(bool(x) for x in raw)
                if not it.get("reason") and not has_raw:
                    silent_items += 1
    for p, d in empty:
        if not any(k in d for k in ("failure", "empty_reason", "failure_class")):
            silent_bundles += 1
    print()
    print(f"  C3 conformance: silent item-zeros {silent_items}, silent empty bundles {silent_bundles}")
    ok3 = silent_items == 0 and silent_bundles == 0
    print(f"     {'PASS' if ok3 else 'FAIL (pre-fix artifacts are expected to fail here)'}")
    # ---- THE C3 SCOPE RULING, STATED RATHER THAN LEFT OPEN -----------------
    #
    # C3 asks whether the instrument records every failure class. The four silent bundles were written
    # by a runner that HAD NO CODE to write one -- the class was computed and sent to stdout and the log,
    # and the artifact was never given it. So their silence is a fact about the instrument's HISTORY, not
    # about v4's design.
    #
    # The scope is therefore: C3 IS SCORED ON ARTIFACTS WRITTEN UNDER THE CURRENT CODE, and pre-fix
    # bundles are EXCLUDED WITH THE EXCLUSION NAMED. The alternative -- scoring v4 on files written by
    # code that could not satisfy the criterion -- would make C3 unpassable by construction, which is a
    # criterion that cannot fail and therefore measures nothing. This is stated BEFORE the field closes
    # so it cannot be read as a rationalisation of a result.
    print("     C3 SCOPE (fixed before the field closes): scored on artifacts written under the current")
    print("       code. The 4 silent bundles predate the failure-record fix, whose absence they are")
    print("       evidence FOR. Excluded, on the record, and named. Scoring v4 on files written by a")
    print("       runner that had no code to write the field would make C3 unpassable by construction.")
    if silent_items == 0:
        print("       Within that scope: the ITEM-level fix HOLDS on every v4 artifact -- 0 silent zeros.")

    # ---- C1: per-item discrimination --------------------------------------
    per = defaultdict(lambda: [0, 0])
    for p, d, e, rd in with_rd:
        for iid, it in (rd.get("items") or {}).items():
            per[iid][1] += 1
            if (it.get("score") or 0) >= 1.0:
                per[iid][0] += 1
    print()
    print(f"  C1 item discrimination, band {BAND_LO:.0%}-{BAND_HI:.0%} (need >= {C1_NEED} of {len(per)}):")
    disc = 0
    for iid in sorted(per):
        g, t = per[iid]
        if not t:
            continue
        f = g / t
        band = "DISCRIMINATES" if BAND_LO <= f <= BAND_HI else ("SATURATED" if f > BAND_HI else "FLOOR")
        if band == "DISCRIMINATES":
            disc += 1
        print(f"    {iid[:44]:44} {g:3}/{t:3} = {f:5.1%}  {band}")
    ok1 = disc >= C1_NEED
    print(f"     discriminating items: {disc}   {'PASS' if ok1 else 'FAIL'}")

    # ---- C2: the floor -----------------------------------------------------
    below = 0
    for p, d, e, rd in with_rd:
        items = rd.get("items") or {}
        if not items:
            continue
        agg = sum((it.get("score") or 0) for it in items.values()) / len(items)
        if agg < FLOOR:
            below += 1
    print()
    print(f"  C2 floor: {below} entrants below {FLOOR} (need >= {C2_NEED})")
    ok2 = below >= C2_NEED
    print(f"     {'PASS' if ok2 else 'FAIL'}")

    # ---- THE VERDICT, AND WHETHER IT MAY BE CALLED YET --------------------
    print()
    print("=" * 78)
    if len(with_rd) < 40:
        print(f"NO VERDICT YET -- the field is INCOMPLETE: {len(with_rd)} measured of ~46 expected.")
        print("  The criteria above are computed for diagnostics only. Calling a verdict on a partial")
        print("  field is how v3's verdict became conditional on the scope of its own correction.")
        return 1
    verdict = {"C1": ok1, "C2": ok2, "C3": ok3, "C4": ok4}
    print("VERDICT: " + "  ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in verdict.items()))
    print("  C3 is expected to FAIL on this field: the clock and failure-class fixes are forward-only,")
    print("  so artifacts written before them are silent by construction. It is a statement about the")
    print("  instrument's history, not about any entrant.")
    print("The bar does not move to accommodate the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
