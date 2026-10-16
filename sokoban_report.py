#!/usr/bin/env python3
"""SOKOBAN -- THE REPORT, DERIVED FROM THE ARTIFACT.

WHY THIS EXISTS RATHER THAN A SUMMARY PRINTED AT THE END OF THE RUN.

The first run printed a summary line that DISAGREED WITH ITS OWN RECORD:
    printed   not_an_action  2      <- a COUNT OF CELLS WITH A NONZERO COUNTER
    true                80      <- the SUM OF THE COUNTER
    printed   solved         1      <- supported by NO ROW in the artifact
    true                     0

Two defects in one line: A COUNT OF ENTRIES IS NOT THE SUM OF VALUES, and a number nobody can trace back to
a row. So the run no longer prints a verdict. THE REPORT IS COMPUTED FROM THE RECORD, HERE, AT READ TIME.

    A SUMMARY ACCUMULATED DURING A RUN IS A SECOND COPY OF THE TRUTH, AND TODAY HAS BEEN ABOUT WHAT SECOND
    COPIES DO. This one is derived, or it is not printed.

    python3 sokoban_report.py [probes/SOKOBAN_FIRST_RUN.json]
    python3 sokoban_report.py --self-test

WHICH SHAPES IT READS, NAMED RATHER THAN GUESSED, AND PRINTED ON THE `source ... SHAPE ...` LINE:

    run        a run's own file: a dict carrying "cells"          (the shape this report always read)
    list       a bare list of cell records                        (the shape the freeze's probes use)
    cell       ONE cell record -- one load failure handed over directly
    container  a dict whose every non-underscore value is a cell record, e.g. {"pre": ..., "new": ...},
               read in KEY ORDER (this is how a before/after pair of records is compared)

ANYTHING ELSE IS REFUSED WITH A SENTENCE, rc 1. The pre-image reader iterated whatever dict it was given and
called `.get` on its KEYS, so a bare cell record produced `AttributeError: 'str' object has no attribute
'get'` -- A TRACEBACK IS NOT A READING, and an input the report cannot read is a thing to say out loud.
"""
import json
import os
import sys

COUNTERS = ["moves", "attempted", "blocked", "not_an_action", "give_up"]

# ==================================================================================================
# A NON-LOADING CELL IS BUCKETED BY THE FIELD THE WRITER WROTE, AND THE RULE THAT PRODUCED THE BUCKET
# IS PRINTED WITH IT.
#
# THE DEFECT, MEASURED RATHER THAN ASSUMED (card t_7d2eb103). This block bucketed a load failure by
#
#     k = (r.get("why") or "unknown").split(" -- ")[0][:44]
#
# -- A SPLIT OF PROSE. A bucket is a claim about WHICH CONDITION a cell fell into, and the driver now
# writes that condition as a FIELD. In the case where the server's own log names a cause, the prose also
# contains " -- " INSIDE the sentence ("server exited rc=1." / "THE BINARY REFUSED THE FILE -- log line
# 10, quoted verbatim: ..."), so the split stopped landing on a sentence boundary and the label moved to a
# fragment of a DIFFERENT sentence. MEASURED on that record: the pre-image label is "server exited rc=1.
# \nTHE BINARY REFUSED THE F".
#
# SO THE FIELD IS READ, AND THE PROSE SPLIT IS KEPT AS THE FALLBACK for records written before the driver
# carried a class -- one word away rather than in place of it. WHICH RULE FIRED IS PRINTED BESIDE EVERY
# BUCKET, because a report that silently changes buckets between record generations is two reports wearing
# one name, and a reader who pooled them would be pooling a decided class with a split of prose.
#
# AND A BUCKET IS KEYED BY (RULE, LABEL), NOT BY LABEL ALONE: two generations cannot be merged into one
# line even if their labels happened to read the same.
#
# THE CLASS IS NOT ENUMERATED HERE, DELIBERATELY. A list of the writer's values living in the reader would
# be a SECOND DEFINITION of a set the writer owns -- the same defect shape as a census that lists fields
# the record does not carry. The field is printed VERBATIM, so a fourth class added tomorrow is REPORTED
# rather than folded into "unknown".
#
# THE 44-CHARACTER CUT STAYS ON THE PROSE AND IS NOT APPLIED TO THE CLASS: the cut is the fallback's own
# display compromise over prose of unknown length, and a class is a label with an authored meaning -- a
# truncated one is a reader's defect in a new place.
# ==================================================================================================
FALLBACK_CUT = 44
RULE_FIELD = "field"
RULE_PROSE = "prose"
RULE_LEGEND = {
    RULE_FIELD: "load_failure_class -- the condition the driver decided and wrote down",
    RULE_PROSE: f'why.split(" -- ")[0][:{FALLBACK_CUT}] -- the fallback for records written before the '
                f'class existed',
}

CELL_MARKERS = ("level",)


def is_cell_record(o):
    """A CELL RECORD, as this report reads one: a dict carrying the keys a driver writes per cell.

    DELIBERATELY NARROW. Accepting "any dict" is how a container gets iterated as if it were a list of
    cells -- which is the pre-image reader's own failure. A dict that is not a cell record is refused with
    a sentence naming what was found, and a refusal is a reading.
    """
    return isinstance(o, dict) and all(k in o for k in CELL_MARKERS) and ("loaded" in o or "why" in o)


def failure_bucket(r):
    """-> (label, rule) for a cell that did not load.

    THE FIELD FIRST, THE PROSE ONLY WHEN THERE IS NO FIELD. A blank class, or one that is not a string, is
    treated as ABSENT rather than as a bucket: a label nobody can act on buckets nothing.
    """
    cls = r.get("load_failure_class")
    if isinstance(cls, str) and cls.strip():
        return cls.strip(), RULE_FIELD
    return (r.get("why") or "unknown").split(" -- ")[0][:FALLBACK_CUT], RULE_PROSE


def read_records(d):
    """-> (rows, shape) for the four shapes this report reads, or (None, None) if it reads none."""
    if isinstance(d, list):
        return d, "list"
    if isinstance(d, dict):
        if "cells" in d:
            return d["cells"], "run"
        if is_cell_record(d):
            return [d], "cell -- one record"
        named = [k for k in d if not k.startswith("_")]
        if named and all(is_cell_record(d[k]) for k in named):
            return [d[k] for k in sorted(named)], f"container of {len(named)} named cell record(s)"
    return None, None


def self_test():
    """THE CONTROL. The shipped rule must pass it, and a rule with the preference INVERTED must fail it.

    Pure -- it calls failure_bucket and nothing else -- so it costs nothing, needs no artifact, and can be
    run anywhere. The cases are the two generations plus the three edges that decide between them; the last
    is the one that makes the test able to fail at all rather than a restatement of the code.
    """
    instrument4 = {"load_failure_class": "the binary refused the FILE (the log names the cause)",
                   "why": "server exited rc=1.\nTHE BINARY REFUSED THE FILE -- log line 10, quoted: x",
                   "level": "01_one_push", "loaded": False}
    pre_instrument4 = {"why": "server exited rc=1.\n  AND THE CARD IS HELD BY: pid 1 (1 MiB) ...",
                       "level": "01_one_push", "loaded": False}
    cases = [
        ("field present AND the prose carries \" -- \": THE FIELD WINS", instrument4,
         "the binary refused the FILE (the log names the cause)", RULE_FIELD),
        ("a blank class is not a class", {"load_failure_class": "   ", "why": "a -- b",
                                          "level": "L", "loaded": False}, "a", RULE_PROSE),
        ("a class that is not a string is not a class", {"load_failure_class": 7, "why": "a -- b",
                                                         "level": "L", "loaded": False}, "a", RULE_PROSE),
        ("pre-instrument-4: no field, the fallback, cut at 44", pre_instrument4,
         "server exited rc=1.\n  AND THE CARD IS HELD B", RULE_PROSE),
        ("neither carrier: the pre-image's \"unknown\" is kept", {"level": "L", "loaded": False},
         "unknown", RULE_PROSE),
    ]
    ok = True
    print("=" * 92)
    print("SOKOBAN REPORT -- SELF-TEST OF THE BUCKET RULE")
    print("=" * 92)
    for what, rec, want_label, want_rule in cases:
        got_label, got_rule = failure_bucket(rec)
        good = (got_label == want_label and got_rule == want_rule)
        ok = ok and good
        print(f"  {'OK  ' if good else 'FAIL'}  {what}")
        if not good:
            print(f"        wanted [{want_rule}] {want_label!r}")
            print(f"        got    [{got_rule}] {got_label!r}")
    print(f"\n  {len(cases)} cases, {sum(1 for c in cases if failure_bucket(c[1]) == (c[2], c[3]))} as "
          f"predicted")
    print("  AND A RULE WITH THE PREFERENCE INVERTED MUST FAIL THIS: a control that cannot fail is a"
          "\n  restatement of the code, which is why the inverted copy is run against this file in evidence.")
    return ok


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        return 0 if self_test() else 1
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "probes", "SOKOBAN_FIRST_RUN.json")
    d = json.load(open(p))
    rows, shape = read_records(d)
    if rows is None:
        print(f"  *** {os.path.basename(p)} IS NOT A RUN, A LIST OF CELL RECORDS, ONE CELL RECORD, OR A ***")
        print("  *** CONTAINER OF CELL RECORDS. A REPORT OVER SOMETHING THAT IS NOT A RECORD IS NOT A   ***")
        print("  *** REPORT, SO NOTHING IS REPORTED. Keys found, top level:                            ***")
        keys = sorted(d) if isinstance(d, dict) else []
        print(f"      {keys[:14]}{' ...' if len(keys) > 14 else ''}   (a cell record carries 'level' and " 
              f"'loaded' or 'why')")
        return 1
    if isinstance(d, dict) and d.get("VOID"):
        print("  *** THIS ARTIFACT IS VOID-BANNERED AND IS NOT A RATE ***")
        print()

    loaded = [r for r in rows if r.get("loaded") is True]
    not_loaded = [r for r in rows if r.get("loaded") is not True]
    levels = sorted({r["level"] for r in rows})

    print("=" * 92)
    print("SOKOBAN -- FROM THE RECORD, NOT FROM A SUMMARY")
    print("=" * 92)
    print(f"  source {os.path.basename(p)}   SHAPE {shape}")
    print(f"  cells {len(rows)}   PLAYED {len(loaded)}   DID NOT LOAD {len(not_loaded)}")
    print()

    print("  PER CELL -- the five counters, NEVER MERGED")
    print(f"  {'entrant':32s} {'level':14s} {'ended':19s} " + " ".join(f"{c[:9]:>9s}" for c in COUNTERS))
    for r in rows:
        if r.get("loaded") is not True:
            print(f"  {r['entrant'][:32]:32s} {r['level']:14s} DID NOT LOAD -- {r.get('why')}")
            continue
        vals = " ".join(f"{r.get(c, 0):9d}" for c in COUNTERS)
        print(f"  {r['entrant'][:32]:32s} {r['level']:14s} {r.get('ended', '?'):19s} {vals}")
    print()

    print("  PER LEVEL -- sums over PLAYED cells only, so a non-loading model cannot vote")
    print(f"  {'level':16s} {'played':>6s} {'solved':>6s} {'gaveup':>6s} " +
          " ".join(f"{c[:9]:>9s}" for c in COUNTERS))
    for lv in levels:
        sub = [r for r in loaded if r["level"] == lv]
        vals = " ".join(f"{sum(r.get(c, 0) for r in sub):9d}" for c in COUNTERS)
        print(f"  {lv:16s} {len(sub):6d} {sum(1 for r in sub if r.get('solved') is True):6d} "
              f"{sum(1 for r in sub if r.get('give_up')):6d} {vals}")
    print()

    print("  REASON COUNTS, reported SEPARATELY FROM EVERY TOTAL ABOVE")
    # A BUCKET IS (RULE, LABEL): the rule is part of the key, so two generations of record cannot be
    # pooled into one line even where their labels read the same.
    reasons = {}
    for r in not_loaded:
        label, rule = failure_bucket(r)
        reasons[(rule, label)] = reasons.get((rule, label), 0) + 1
    print(f"    played          {len(loaded)}")
    for (rule, label), v in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    did not load    {v}   [{rule}] {label}")
    tally = {}
    for (rule, _), v in reasons.items():
        tally[rule] = tally.get(rule, 0) + v
    print("  THE RULE EACH BUCKET USED -- a label is only comparable to another label from the SAME rule:")
    for rule in (RULE_FIELD, RULE_PROSE):
        print(f"    [{rule}]  {tally.get(rule, 0)} of {len(not_loaded)}   from   {RULE_LEGEND[rule]}")
    print("    (A POPULATION THAT NEVER RAN IS NOT EVIDENCE ABOUT THE POPULATION.)")
    print()

    print("  THE SPLIT PER LEVEL, as fractions -- the gate's own shape")
    for lv in levels:
        sub = [r for r in loaded if r["level"] == lv]
        if not sub:
            continue
        att = sum(r.get("attempted", 0) for r in sub) or 1
        print(f"    {lv:16s} blocked {sum(r.get('blocked', 0) for r in sub)/att:.3f}   "
              f"not_an_action {sum(r.get('not_an_action', 0) for r in sub)/att:.3f}   "
              f"give_up {sum(r.get('give_up', 0) for r in sub)/att:.3f}")
    print()
    print(f"  HEAD-READ CHECK -- the first token each played entrant actually produced")
    for r in loaded:
        t = [x.get("token") for x in (r.get("turns") or [])][:3]
        print(f"    {r['entrant'][:32]:32s} {r['level']:14s} {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
