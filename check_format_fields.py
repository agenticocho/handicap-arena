#!/usr/bin/env python3
"""A7 + A1/A2/A4/A9 AS FORMAT FIELDS -- AND CHECKED, NOT MERELY DECLARED.

WHY THIS EXISTS. The Chair ruled nine format items. A ruling that lives only in a document is a
declaration; A RULING THAT FAILS A BUNDLE IS A FORMAT. `check_field_semantics.py` already checks what a
field NAME claims about its contents. THIS checks that the fields a ruling REQUIRES ARE PRESENT AT ALL --
a different defect: a bundle can be perfectly named and completely silent about the thing that matters.

    python3 check_format_fields.py --self-test      # the controls, both directions
    python3 check_format_fields.py <bundle.json>    # one bundle
    python3 check_format_fields.py --all            # every bundle under results/

THE RULINGS ENCODED, EACH WITH ITS REASON:

  A1  `kind` declares "model" | "code". A CODE ENTRANT IS A DIFFERENT INSTRUMENT and is NEVER pooled with
      models. The pooling error at the entrant level -- the same rule that keeps Formats A and B apart.
  A1  AN INVENTED VALUE IS NEVER SUBSTITUTED. A missing quantity is `null` PLUS A WRITTEN REASON, never a
      zero -- a fabricated number is worse than a missing one BECAUSE IT COMPUTES.
  A2  `server` may be ABSENT. Absent is honest; a reduced config is a SECOND SHAPE, and a second shape is
      what this project spends its weeks finding.
  A4  a DETERMINISTIC oracle gets ONE trial, AND THE RECORD SAYS SO. If `deterministic` is true then
      `trials` must be 1 and a reason must be written; three identical trials of a fixed algorithm are
      three copies of one measurement, and calling that `n=3` is a false sample size.
  A7  `never_started` and `unreadable` are FORMAT fields, not private ones -- two privates do not compare.
      AND THEY SIT ON OPPOSITE SIDES OF THE DENOMINATOR: `unreadable` is INSIDE as a non-pass;
      `never_started` is OUTSIDE and reported separately. A population that fails to form an answer must
      not IMPROVE a rate by leaving.
  A9  a freeze record carries the VERIFIER's identity, not only the oracle's. A self-test proves the
      instrument agrees with ITSELF, which is not the same as agreeing with anything else.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# THE COUNTERS THAT MUST SIT ON EITHER SIDE OF A DENOMINATOR, and which side they sit on.
DENOMINATOR_SIDES = {
    "unreadable": "INSIDE -- answered badly, counted as a non-pass",
    "never_started": "OUTSIDE -- did not play at all, reported separately",
}

# A RESOURCE MEASUREMENT: a number that is a fact about the MACHINE or the MODEL, where a zero means "not
# taken" rather than "measured nothing". THIS IS THE ONLY CLASS WHERE A ZERO IS A FABRICATION -- see the
# scoping note in check_bundle, because a zero in a COUNT is a true statement and must NOT be flagged.
RESOURCE_MEASUREMENTS = ("footprint_gb", "weights_gb", "gpu_free_gb_at_weigh_in")

# WHICH PROBLEMS A HISTORICAL BUNDLE *CANNOT* HELP -- the field is ABSENT, not wrong.
#
# THE DISTINCTION IS THE WHOLE MECHANISM: a bundle taken before a field existed CANNOT carry it, so its
# absence is a fact about the CALENDAR. A bundle that carries the field and gets it WRONG is a different
# claim entirely and is NEVER grandfathered. Being conservative here is deliberate -- a false "problem"
# spends the checker's credibility, but a false "grandfathered" spends the record's.
GRANDFATHERED_MARKERS = re.compile(
    r"(A1: no `kind`"
    r"|A7: `unreadable` is not a format field"
    r"|A7: `never_started` is not a format field)")

# AND A BUNDLE THAT DECLARES ITSELF NEW-FORMAT IS NEVER GRANDFATHERED.
#
# THE FLAW THIS CLOSES, found by asking the question rather than by a control: the marker keys on THE FIELD
# BEING ABSENT, so a NEW bundle that forgot one would have been grandfathered too. A RULE THAT COVERS
# EVERYTHING COVERS NOTHING -- and the grandfather rule is for the HISTORY, not for the next run.
#
# The bundle already carries the evidence of which side it is on: `run_id` and `kind` are new-format fields
# and no historical bundle has either. Presence of any one of them means THIS BUNDLE MUST COMPLY IN FULL.
NEW_FORMAT_MARKERS = ("run_id", "kind", "freeze")


def is_new_format(d):
    """Does this bundle declare itself written under the ruling? If so it must carry every field, and the
    grandfather rule cannot excuse it."""
    return any(k in d for k in NEW_FORMAT_MARKERS)


def _find(d, names, path="<bundle>"):
    """Walk the whole bundle for quantity keys, reporting the PATH so a nested one is located, not guessed.

    THE PATH IS THE POINT: my first version read one nested block and a top-level zero escaped it. A report
    that names where the value lives is the difference between a finding and a hint.
    """
    out = []
    if isinstance(d, dict):
        for k, v in d.items():
            if k in names:
                out.append((f"{path}.{k}", k, v))
            out.extend(_find(v, names, f"{path}.{k}"))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.extend(_find(v, names, f"{path}[{i}]"))
    return out


def check_bundle(d, where="<bundle>"):
    """-> list of problems. An empty list is the only passing result.

    EVERY CHECK HERE IS A RULING. None of them is a style preference, and each one is asserted in
    --self-test in BOTH directions: a bundle that violates it must fail, and a faithful bundle must pass.
    """
    p = []

    # ---- A1: the entrant's KIND is declared, and a code entrant is not a model.
    kind = d.get("kind")
    if kind is None:
        p.append("A1: no `kind` -- the entrant does not say whether it is a MODEL or CODE, so a solver "
                 "result and a model result are indistinguishable in this record")
    elif kind not in ("model", "code"):
        p.append(f"A1: `kind` is {kind!r}; must be 'model' or 'code'")

    # ---- A1: an invented value is never substituted.
    #
    # SCOPED DELIBERATELY, because a bare zero is LEGITIMATE in a count: `never_started: 0`, `moves: 0` and
    # `unreadable: 0` are all true statements. The rule is about a MEASUREMENT OF A RESOURCE that could not
    # be taken -- there, a zero is a FABRICATION rather than a fact, because "no nvidia-smi" and "the model
    # occupied nothing" are different claims and `0.00` makes the second out of the first.
    #
    # AND IT SCANS THE WHOLE BUNDLE, NOT ONE NESTED BLOCK. My first version walked `weigh_in` only, and the
    # control immediately produced a bundle with the zero at the TOP LEVEL that escaped it. A check that
    # reads one place when the value can live in two is the defect this project keeps finding.
    found = _find(d, RESOURCE_MEASUREMENTS)
    for path, k, v in found:
        if v == 0 or v == 0.0:
            reason_here = (isinstance(d.get("weigh_in"), dict)
                           and d["weigh_in"].get(f"{k}_null_reason")) or d.get(f"{k}_null_reason")
            p.append(f"A1: `{path}` is a ZERO. A resource measurement that could not be taken must be null "
                     f"plus a written reason, never 0 -- A FABRICATED NUMBER COMPUTES"
                     + ("" if reason_here else ", and no reason is written beside it"))

    # ---- A7: the two counters exist, and they are on opposite sides of the denominator.
    for f in DENOMINATOR_SIDES:
        if f not in d:
            p.append(f"A7: `{f}` is not a format field in this bundle -- two privates do not compare "
                     f"({DENOMINATOR_SIDES[f]})")

    # ---- A4: one trial for a deterministic oracle, and SAID.
    if d.get("deterministic") is True:
        t = d.get("trials")
        if t != 1:
            p.append(f"A4: `deterministic` is true and `trials` is {t!r}; a deterministic oracle gets ONE "
                     f"trial and the record must say 1 -- three identical trials is a false sample size")
        if not (d.get("why_one_trial") or d.get("trials_reason")):
            p.append("A4: `trials` is 1 but NO REASON IS WRITTEN. The number must be said, not just "
                     "produced -- otherwise a reader cannot tell a deliberate 1 from a runner that stopped")
        if d.get("trials_are_identical") is not None and d.get("trials_are_identical") is False:
            p.append("A4: `deterministic` is true and `trials_are_identical` is false -- that is a "
                     "CONTRADICTION, and one of the two fields is wrong")

    # ---- A9: the freeze record names the VERIFIER, not only the oracle.
    #
    # ONE NAME, AND IT IS THE PRODUCER'S. This check asked for `verifier_identity` while the record wrote
    # `verifier` -- A NAME MISMATCH BETWEEN A CHECK AND THE THING IT CHECKS, which is the defect this
    # project keeps finding in cards, gates and slot namespaces. AND THE CONTROL DID NOT CATCH IT, because
    # the control was built with the check's vocabulary and so agreed with the check. ONLY THE REAL RECORD
    # EXPOSED IT. A control that shares the checker's words cannot detect a disagreement about words.
    fr = d.get("freeze") or d.get("freeze_record")
    if isinstance(fr, dict):
        if not fr.get("verifier"):
            p.append("A9: the freeze record names no VERIFIER (`freeze.verifier`). A self-test proves the "
                     "instrument agrees with ITSELF, which is not the same as agreeing with anything else")

    # ---- A2: a server block, IF PRESENT, must not be a REDUCED one.
    srv = d.get("server")
    if isinstance(srv, dict) and srv:
        named = {"flags", "ctx", "n_gpu_layers"}
        if not (named & set(srv)):
            p.append("A2: a `server` block exists but carries none of the named shape -- a reduced config "
                     "is a SECOND SHAPE; if the server was not used, OMIT the block, because absent is "
                     "honest and a half-block is not")
    return p


def main():
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()

    strict = "--strict" in argv
    targets = []
    if "--all" in argv:
        targets = sorted(glob.glob(os.path.join(RESULTS, "*.json")))
    elif [a for a in argv if not a.startswith("--")]:
        targets = [[a for a in argv if not a.startswith("--")][0]]
    else:
        print("  give a bundle, or --all, or --self-test")
        return 2

    clean, grandfather, broken = [], [], []
    for t in targets:
        if not os.path.exists(t):
            broken.append((t, ["ABSENT"]))
            continue
        try:
            d = json.load(open(t))
        except Exception as e:                                          # noqa: BLE001
            broken.append((t, [f"UNREADABLE: {type(e).__name__}"]))
            continue
        probs = check_bundle(d, t)
        if not probs:
            clean.append(t)
        elif all(GRANDFATHERED_MARKERS.match(x) for x in probs) and not is_new_format(d):
            # A CRITERION CHANGE AFTER THE NUMBER IS A FILE, NOT A CRITERION. A bundle taken before these
            # fields existed CANNOT carry them, and failing it would be scoring a historical run against a
            # rule written afterwards -- the defect this project refuses everywhere else.
            #
            # AND ONLY IF THE BUNDLE DOES NOT DECLARE ITSELF NEW-FORMAT. A bundle carrying `run_id` or
            # `kind` is written UNDER the ruling and must carry all of it; excusing it would be the
            # grandfather rule eating the rule.
            grandfather.append(t)
        else:
            broken.append((t, probs))

    print("=" * 100)
    print("FORMAT FIELDS -- A7 + A1/A2/A4/A9")
    print("=" * 100)
    print(f"  {len(targets)} bundle(s)")
    print(f"    PASS             {len(clean)}   carry every field the rulings require")
    print(f"    GRANDFATHERED    {len(grandfather)}   PREDATE the fields -- recorded, NOT re-scored")
    print(f"    PROBLEMS         {len(broken)}   carry some fields and not others, which is the real failure")
    print()
    print("  A CRITERION CHANGE AFTER THE NUMBER IS A FILE, NOT A CRITERION. The grandfathered set is named")
    print("  rather than failed, because a bundle taken before a field existed cannot carry it -- and")
    print("  failing it would be scoring a historical run against a rule written afterwards.")
    print()
    if grandfather and len(grandfather) == len(targets):
        print("  AND THE HONEST READING OF A CLEAN SWEEP OF THE GRANDFATHERED SET: EVERY BUNDLE IN IT IS")
        print("  MISSING THE SAME THREE FIELDS, so NOTHING in it can be compared on them. The fields are")
        print("  new; the history cannot be back-filled; and any cross-run comparison on `kind`,")
        print("  `unreadable` or `never_started` is impossible across the boundary.")
        print()
    for t, probs in broken[:12]:
        print(f"  {os.path.basename(t)}  ({len(probs)} problem(s))")
        for x in probs[:4]:
            print(f"      {x}")
    if len(broken) > 12:
        print(f"  ... and {len(broken) - 12} more")
    print()
    if strict and grandfather:
        print(f"  --strict: {len(grandfather)} grandfathered bundle(s) ALSO fail, because a NEW run must carry "
              f"the fields -- the grandfather rule covers the history, not the next run.")
        return 1
    if broken:
        print(f"  {len(broken)} bundle(s) with real problems")
        return 1
    return 0


def self_test():
    """A CHECK THAT ONLY EVER FIRES IS BROKEN; ONE THAT NEVER FIRES IS DEAD. Both directions, each ruling."""
    ok, bad, n = [], [], 0

    def ck(name, got_clean, want_clean):
        nonlocal n
        n += 1
        (ok if got_clean == want_clean else bad).append(name)
        print(f"  {'PASS' if got_clean == want_clean else 'FAIL'}  {name}")

    FAITHFUL = dict(kind="model", never_started=3, unreadable=40, deterministic=True, trials=1,
                    why_one_trial="the oracle is a fixed algorithm; repeats cannot differ",
                    weigh_in={"footprint_gb": None, "footprint_gb_null_reason": "no nvidia-smi here"},
                    freeze={"verifier": "verify_levels.py, 3/3"},
                    server={"flags": ["--reasoning", "off"]})

    print("=" * 100)
    print("[1] A FAITHFUL BUNDLE MUST PASS -- a check that fails everything is dead, not strict")
    print("=" * 100)
    ck("a faithful bundle is CLEAN", check_bundle(FAITHFUL) == [], True)

    print()
    print("=" * 100)
    print("[2] EVERY RULING MUST BE ABLE TO FIRE")
    print("=" * 100)
    for label, mut, want in [
        ("A1 no `kind`", {k: v for k, v in FAITHFUL.items() if k != "kind"}, True),
        ("A1 `kind` is not model|code", dict(FAITHFUL, kind="robot"), True),
        ("A1 a ZERO where a measurement was missing", dict(FAITHFUL, footprint_gb=0.0), True),
        ("A7 `never_started` absent", {k: v for k, v in FAITHFUL.items() if k != "never_started"}, True),
        ("A7 `unreadable` absent", {k: v for k, v in FAITHFUL.items() if k != "unreadable"}, True),
        ("A4 deterministic with 3 trials", dict(FAITHFUL, trials=3), True),
        ("A4 trials 1 with NO reason", {k: v for k, v in FAITHFUL.items() if k != "why_one_trial"}, True),
        ("A4 deterministic but trials_are_identical false", dict(FAITHFUL, trials_are_identical=False), True),
        ("A9 a freeze record with no verifier", dict(FAITHFUL, freeze={"oracle": "sf_19"}), True),
        # THE CONTROL THAT WOULD HAVE CAUGHT THE REAL MISMATCH: the verifier is named, but under a name the
        # CHECK does not read. A control built with the checker's own vocabulary agrees with the checker by
        # construction and can never expose a disagreement about vocabulary -- THE REAL RECORD FOUND IT.
        ("A9 the verifier named under a DIFFERENT KEY -> FIRES",
         dict(FAITHFUL, freeze={"verifier_identity": "verify_levels.py"}), True),
        ("A9 and the PRODUCER's name is the one that passes",
         dict(FAITHFUL, freeze={"verifier": "verify_levels.py"}), False),
        ("A2 a server block carrying none of the shape", dict(FAITHFUL, server={"something": 1}), True),
    ]:
        ck(f"{label} -> FIRES", check_bundle(mut) != [], want)

    print()
    print("=" * 100)
    print("[3] AND THE HONEST ABSENCES MUST NOT FIRE -- a2 says absent is honest")
    print("=" * 100)
    ck("no `server` block at all -> CLEAN", check_bundle({k: v for k, v in FAITHFUL.items()
                                                          if k != "server"}) == [], True)
    ck("a null with a written reason -> CLEAN",
       check_bundle(dict(FAITHFUL, footprint_gb=None)) == [], True)
    ck("a NON-deterministic bundle may run 3 trials -> CLEAN",
       check_bundle({k: v for k, v in FAITHFUL.items()
                     if k not in ("deterministic", "why_one_trial")} | {"trials": 3}) == [], True)

    print()
    print("=" * 100)
    print("[4] AND THE GRANDFATHER RULE MUST NOT EAT THE RULE")
    print("=" * 100)
    absence = ["A1: no `kind` -- the entrant does not say whether it is a MODEL or CODE"]

    def grandfathered(d, probs):
        return bool(probs) and all(GRANDFATHERED_MARKERS.match(x) for x in probs) and not is_new_format(d)

    ck("a HISTORICAL bundle (no run_id, no kind) IS grandfathered", grandfathered({}, absence), True)
    ck("a NEW-FORMAT bundle (has run_id) is NOT grandfathered -- it must comply",
       grandfathered({"run_id": "20261010-0001"}, absence), False)
    ck("a bundle carrying `kind` is NEW-FORMAT", is_new_format({"kind": "model"}), True)
    ck("a bundle carrying `freeze` is NEW-FORMAT", is_new_format({"freeze": {}}), True)
    ck("a bundle carrying none of them is HISTORICAL", is_new_format({"results": []}), False)
    ck("and a NON-absence problem is never grandfathered, new or old",
       grandfathered({"results": []}, ["A4: `deterministic` is true and `trials` is 3"]), False)

    print()
    print("=" * 100)
    print(f"  {'ALL CONTROLS PASS' if not bad else str(len(bad)) + ' FAILED'}   --   {len(ok)}/{n}")
    for b in bad:
        print(f"    FAILED: {b}")
    print("=" * 100)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
