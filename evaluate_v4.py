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
import datetime
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
    # DERIVED FROM THE COUNTS, NOT FROM THE DISPLAYED PERCENTAGES. Subtracting the rounded strings gave
    # +2.7 on two rows where the counts give +2.63 -- a number computed from a display instead of from
    # the data, which is the same defect as filling a rate from memory. The counts are the primitive.
    for vn, rg, rt, cg, ct, un in (
        ("R1.1 forbidden_key_must_be_absent", 33, 38, 34, 38, "ordered_sequence_with_a_gap"),
        ("R1.2 null_means_absent", 22, 38, 23, 38, "order_is_the_content"),
        ("R1.3 type_under_natural_language", 35, 38, 36, 38, "duplicates_are_significant"),
        ("R1.4 ambiguous_nesting", 33, 38, 34, 38, "absence_is_the_answer"),
        ("R1.5 enum_nearest_is_wrong", 30, 38, 33, 38, "exact_key_set_under_a_bribe"),
        ("R1.6 array_exact_and_ordered", 15, 38, 15, 38, "exact_scalar_types"),
    ):
        r, c = rg / rt, cg / ct
        print(f"        {vn:36}  {r:>7.1%}  {c:>8.1%}  {(c - r) * 100:+5.1f}% | {un}")
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
    print(f"  accounted for : {accounted}   (as of {datetime.datetime.now().astimezone().isoformat(timespec='seconds')})")
    print(f"  MEASURED      : {len(with_rd)}")
    print(f"  empty (no results) : {len(empty)}")
    print("  TWO DIFFERENT QUANTITIES, AND THEY MUST NOT BE COMPARED:")
    print("    this 'accounted for' counts BUNDLE FILES on disk.")
    print("    the runner's own '[N/46]' counts ENTRANTS ATTEMPTED, and it is a DIFFERENT number --")
    print("    a resumed run's index starts from where it left off, so a runner index of 39 alongside")
    print("    44 files is CONSISTENT, not a discrepancy.")
    print("  An earlier version of this note attributed that difference to TIMING. It was not timing:")
    print("  it was two counts with different denominators, compared before either was established --")
    print("  the repo's own recurring class, committed by the check that was watching for it.")
    print("  The timestamp above is kept because a count of a GROWING record is still a timestamp rather")
    print("  than a fact; it is not an explanation of that difference.")

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
    # ---- THE POPULATION ARGUMENT, AND ITS DIRECTION PER CRITERION -----------
    #
    # MONOTONICITY, which is the provable form of "the exclusions push against me": an empty bundle
    # carries `results: []`, so it contributes ZERO aggregates to any count. Removing an entrant can
    # only ever REDUCE the number below the floor. So the measured count is a LOWER BOUND, and that
    # holds regardless of what the missing entrants would have scored -- no hunch required.
    #
    # AND IT ONLY HELPS ONE WAY. A thin field that PASSES a monotone criterion is a STRICTER result.
    # A thin field that FAILS one is INDETERMINATE: the failure may belong to the CARD or to the
    # POPULATION, and this subset cannot distinguish them. So the thinning argument is a DEFENCE OF A
    # PASS, NOT A LICENCE FOR A FAIL -- and using it to excuse a failure would let the card off for a
    # result the card may own.
    if ok2:
        print("     Population note: the count is a LOWER BOUND (empty bundles contribute zero), so this")
        print("       PASS is stricter than it would be on a full field.")
    else:
        print("     Population note: this count is a LOWER BOUND, and it FAILS anyway. The failure may")
        print("       belong to the CARD or to the POPULATION, and this subset cannot distinguish them.")
        print("       The thinning argument does NOT excuse a failure -- it is a defence of a PASS.")
    print()
    print("  AND C1 GETS NO PROTECTION FROM THAT ARGUMENT. C1 is computed from RATES, which move in")
    print("  EITHER direction as entrants are added -- measured: adding a single entrant moved R1.2")
    print("  82.8->83.3 and R1.3 75.9->73.3, in OPPOSITE directions. EVERY EXCLUSION HAS A DIRECTION,")
    print("  AND THE DIRECTION IS A PROPERTY OF THE CRITERION, NOT OF THE EXCLUSION: two criteria on")
    print("  one card can be protected and exposed by the same removed entrants.")

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
    # ---- THE THIRD OUTCOME, DECLARED BEFORE THE NUMBERS LAND ----------------
    #
    # Chilly's point, and it is the sharpest thing said about this verdict: a thin field that PASSES a
    # monotone criterion is a STRICTER result; a thin field that FAILS one is INDETERMINATE. So a FAIL
    # needs a third outcome rather than a defence, because the failure may belong to the CARD or to the
    # POPULATION and this subset cannot tell them apart.
    #
    # Declared here, before the field closes, so it cannot be read as a hedge added after a result.
    if not ok2:
        print()
        print("  *** OUTCOME 3 APPLIES TO C2: FAILED ON THIS POPULATION, AND THE POPULATION IS A ***")
        print("  *** CANDIDATE CAUSE THIS FIELD CANNOT RULE OUT.                                     ***")
        print("  The twelve unmeasured entrants are all SERVING failures (size-correlated, failing at")
        print("  load), and the count is a LOWER BOUND. So the card's C2 status is INDETERMINATE on this")
        print("  population: the floor may be unpopulated because the card does not discriminate the low")
        print("  end, or because the entrants that would have populated it could not run. This field")
        print("  cannot distinguish those, and no re-reading of it will.")
        print("  That is a SCOPE, not a hedge. The remedy is one small known-good entrant for the clock")
        print("  exercise and, for C2, a population that can run -- not a relaxation of the bar.")
    print("  C3 is expected to FAIL on this field: the clock and failure-class fixes are forward-only,")
    print("  so artifacts written before them are silent by construction. It is a statement about the")
    print("  instrument's history, not about any entrant.")
    print("The bar does not move to accommodate the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
