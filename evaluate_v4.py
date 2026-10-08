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
    # MONOTONICITY. The provable half: an empty bundle carries `results: []`, so it contributes ZERO
    # aggregates to any count, and the measured count is therefore a LOWER BOUND. That holds regardless
    # of what the missing entrants would have scored -- no hunch required.
    #
    # AND THE PROVABLE HALF IS ALL OF IT. A LOWER BOUND IS A STATEMENT ABOUT A NUMBER, NOT ABOUT A
    # VERDICT. Chilly's correction, and it is decisive: whether thinning makes this criterion HARDER
    # depends on WHAT THE MISSING ENTRANTS WOULD HAVE SCORED -- and a missing entrant, by definition, has
    # no score. If they would have scored BELOW the floor they would have HELPED C2. So "thin makes it
    # harder" needs the unstated premise "the missing would have scored high", which is never measured
    # and is NOT implied by monotonicity. DIRECTION NEEDS THE MISSING VALUES, NOT THE MISSING COUNT.
    #
    # The earlier version of this block said the thinning argument "is a defence of a PASS, not a licence
    # for a FAIL" -- WHICH ASSERTS A DIRECTION THE FIELD CANNOT ESTABLISH. It was a true argument pointing
    # the wrong way, and a direction that runs AGAINST the speaker is exactly where the check stops.
    # Dropped. The bound is stated; no direction is claimed.
    print()
    print("  POPULATION BOUND (no direction claimed): empty bundles contribute zero, so the measured")
    print("  count is a LOWER BOUND on the number of low-scoring entrants this field could have had.")
    print("  A LOWER BOUND IS A STATEMENT ABOUT A NUMBER, NOT ABOUT A VERDICT: whether the omissions")
    print("  made C2 harder or easier depends on what the missing entrants WOULD have scored, and a")
    print("  missing entrant has no score. 'Thin makes it harder' needs the premise 'the missing would")
    print("  have scored high' -- never measured, and NOT implied by monotonicity. Direction needs the")
    print("  missing VALUES, not the missing COUNT.")
    print("  AND THE OMISSIONS ARE NOT ONE CAUSE: of the 8 entrants that emptied in every copy, six are")
    print("  27B (5.95-7.21 GB) and TWO ARE SMALL (Kev-4B 3.03 GB, laya_english_f16 0.85 GB) -- while a")
    print("  0.219 GB entrant measured cleanly. At least two causes. The thinned field is NOT the")
    print("  measurement this project was built to make, and no claim may rest on it being one.")
    print()
    print("  AND C1 GETS NO PROTECTION FROM THAT ARGUMENT. C1 is computed from RATES, which move in")
    print("  EITHER direction as entrants are added -- measured: adding a single entrant moved R1.2")
    print("  82.8->83.3 and R1.3 75.9->73.3, in OPPOSITE directions. EVERY EXCLUSION HAS A DIRECTION,")
    print("  AND THE DIRECTION IS A PROPERTY OF THE CRITERION, NOT OF THE EXCLUSION: two criteria on")
    print("  one card can be protected and exposed by the same removed entrants.")

    # ---- WHAT EACH ARGUMENT PROTECTS (Chilly's rule, applied to this evaluator) --------------
    #
    # Printed HERE, before the verdict gate, because the first version of this block sat after the
    # `len(with_rd) < 40` early return -- so at 31 measured it would never have printed at all. The
    # argument table belongs BESIDE the arguments, not after the verdict: it is most useful exactly when
    # the verdict is still refused.
    print_protects()

    # ---- THE VERDICT, AND WHETHER IT MAY BE CALLED YET --------------------
    print()
    print("=" * 78)
    if len(with_rd) < 40:
        # STILL RUNNING vs CLOSED AND SHORT are different states, and the first version of this gate
        # printed "NO VERDICT YET" for both. After the field closed, that sentence was STALE: it invites
        # a reader to wait for a number that is not coming. So the gate now asks whether any entrant can
        # still add: an entrant whose EVERY attempt produced an empty bundle has failed permanently.
        per_entrant = {}
        for p in sorted(glob.glob(os.path.join(RESULTS, "*cardv4*.json"))):
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            if d.get("harness") != "handicap-arena":
                continue
            stem = os.path.basename(p).split("_cardv4")[0]
            per_entrant.setdefault(stem, []).append(bool(d.get("results") or []))
        never = [k for k, v in per_entrant.items() if not any(v)]
        can_add = len(never) == 0
        print(f"NO VERDICT -- {'the field can still add entrants' if can_add else 'THE FIELD IS CLOSED AND SHORT'}: "
              f"{len(with_rd)} measured of ~46 expected.")
        print("  THIS IS A COMPLETENESS GATE, NOT A SCORE THRESHOLD. It answers 'did enough entrants")
        print("  produce a measurement', not 'did the card pass'.")
        print("  TWO DENOMINATORS, and both are right: the bundle FILES on disk and the UNIQUE entrants")
        print("  attempted are different quantities -- 8 entrants carry a second bundle from a re-run.")
        print("  Same shape as 38-versus-44 earlier today: two correct numbers, unstated denominators.")
        print("  REACHABILITY DEPENDS ON A FIELD RULE, NOT ON ARITHMETIC -- the rule is named here,")
        print("  before the verdict is attempted: an empty bundle is a MISSING VALUE, not a score of zero;")
        print("  a serving failure is not a result about the entrant, so re-running is a RE-MEASUREMENT")
        print("  rather than a second chance; an entrant counts as MEASURED if ANY attempt measured;")
        print("  every failure stays reported as a failure; no entrant is dropped from the denominator.")
        if not can_add:
            print()
            print("  *** UNSCOREABLE ON THIS FIELD. ***")
            print(f"  Every entrant that has not measured has failed EVERY attempt: {len(never)} entrants,")
            print("  each with an empty bundle in EVERY copy. Re-measurement was attempted and returned")
            print("  nothing new, so the gate of 40 is UNMET. A further run COULD in principle meet it --")
            print("  that is a policy question, not arithmetic -- but every one of these entrants has now")
            print("  failed every attempt made: original run, re-run, and re-attempt, THREE TIMES EACH.")
            print("  Nothing in this field's own behaviour suggests a fourth would differ, and this")
            print("  instrument cannot say why the first three did not.")
            print("  AND SIZE IS NOT THE EXPLANATION: of those entrants, SIX are 27B (5.95-7.21 GB) and")
            print("  TWO ARE SMALL -- Kev-4B-Q4_K_M 3.03 GB and laya_english_f16 0.85 GB -- while a")
            print("  0.219 GB entrant measured cleanly. At least two causes, and the field cannot say")
            print("  which. THE CARD IS NOT EXCUSED -- THE POPULATION COULD NOT BE MADE COMPLETE. Those")
            print("  are different sentences, and only the second one is supported by this instrument.")
        print("  Calling a verdict on a partial field is how v3's verdict became conditional on the scope")
        print("  of its own correction.")
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


def print_protects():
    """WHAT EACH ARGUMENT PROTECTS (Chilly's rule, applied to this evaluator).

    On any argument that supports a conclusion, PRINT THE OUTCOME IT PROTECTS. If it protects only one,
    say which. "This pushes against me" is a defence ONLY when it is true of the outcome that actually
    obtained -- otherwise it is a conclusion-shaped argument, and that is the more dangerous form
    BECAUSE IT IS CHECKABLE.

    Why the direction check is the one that gets skipped: verifying an argument is satisfying, and it
    feels like diligence. Asking which outcome it protects requires asking whose interest it serves, and
    verification never asks that. The argument-level twin of the flattering measurement -- it survives
    for the same reason, because nobody investigates good news.

    Applied to THIS FILE'S arguments rather than described, because an argument protecting one outcome
    is exactly the kind that reads as rigour.
    """
    print()
    print("=" * 78)
    print("WHAT EACH ARGUMENT PROTECTS -- ONE OUTCOME, BOTH OUTCOMES, OR NEITHER")
    # THE CAPTION IS PART OF THE TAXONOMY, and it is the copy nobody re-reads. This line said
    # "ONE OUTCOME OR BOTH" for a table that already had a NO DIRECTION row -- the fix for the missing
    # slot had introduced the same missing slot, ten lines from the body it contradicted. Chilly's rule:
    # a taxonomy is stated at least twice, in the labels and in the caption, and the fix is not complete
    # until the sentence describing the categories has changed too. THE TELL: a value the prose cannot
    # name means one of the two is wrong -- AND THE PROSE IS THE ONE THAT WILL BE BELIEVED.
    argues = [
        ("C2's count is a LOWER BOUND (empty bundles contribute zero)",
         set(),
         "protects NEITHER -- a bound is a statement about a NUMBER, not about a verdict. Whether the "
         "omissions helped or hurt depends on what the missing entrants would have scored, and a "
         "missing entrant has no score"),
        ("C1 gets no protection from the thinning argument (rates move either way)",
         {"PASS", "FAIL"},
         "genuine -- and it is why C1 is not excused by it"),
        ("OUTCOME 3: the failure may belong to the POPULATION",
         {"FAIL"},
         "declared BEFORE the numbers landed, which is what makes it a scope and not a hedge"),
        ("C3 is expected to FAIL on this field (the fixes are forward-only)",
         {"FAIL"},
         "about the INSTRUMENT's history, not a defence of any entrant"),
    ]
    for arg, protects, note in argues:
        if not protects:
            tag = "NO DIRECTION"
        elif len(protects) == 1:
            tag = "ONE OUTCOME "
        else:
            tag = "BOTH        "
        shown = "/".join(sorted(protects)) if protects else "neither"
        print(f"  [{tag}] {arg}")
        print(f"      protects {shown} -- {note}")
    print()
    print("  AN ARGUMENT THAT PROTECTS ONLY ONE OUTCOME IS THE ONE TO CHECK HARDEST, because it is the one")
    print("  that reads as rigour. Every entry tagged ONE OUTCOME above is either DECLARED BEFORE THE")
    print("  RESULT or a statement ABOUT THE INSTRUMENT rather than the entrants -- and those are the only")
    print("  two forms that survive this check. An argument offered after a result, about the entrants, is")
    print("  a conclusion-shaped argument no matter how true it is.")


if __name__ == "__main__":
    raise SystemExit(main())
