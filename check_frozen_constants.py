#!/usr/bin/env python3
"""CHECK FROZEN CONSTANTS -- the drift monitor, mechanical instead of attentive.

WHY THIS EXISTS, in Chilly's words: "Each change was justified by a measurement that preceded it" was
TRUE here, and it would be true in a DRIFT case too -- because a competent agent's changes are justified
by construction. JUSTIFICATION IS NOT EVIDENCE OF NON-DRIFT; IT IS WHAT DRIFT LOOKS LIKE WHEN THE AGENT
IS GOOD. A unidirectional sequence of individually-justified changes is still biased, and a per-step
audit cannot see it.

SO THE MONITOR WATCHES THE CRITERIA, NOT THE JUSTIFICATIONS. Four constants. If any changes, that is the
signal, and nothing else in the sequence matters.

    python3 check_frozen_constants.py            # check every test source against the frozen record
    python3 check_frozen_constants.py --self-test
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, "FROZEN_CONSTANTS.json")
SOURCES = ["depth_test.py", "depth_test2.py", "source_probe3.py", "source_probe4.py"]


def frozen():
    return {k: v for k, v in json.load(open(FROZEN, encoding="utf-8")).items()
            if not k.startswith("_")}


def extract(path):
    """-> {NAME: value} for the four constants, read from the source text.

    TWO ASSIGNMENT FORMS, and the first version handled only one. `depth_test.py` writes
    `LOST_CP, HOLD_CP, WINDOW = -300, -100, 60` -- a TUPLE assignment -- and a regex expecting
    `NAME = value` skipped it and matched a stray 60 further down the file. THE MONITOR THEN REPORTED
    DRIFT ON FOUR SOURCES THAT HAD NOT DRIFTED. A false positive on a drift check is worse than no
    check: it sends someone hunting a change that never happened. Caught by this file's own control,
    which asserts the extractor reads a known value.
    """
    try:
        src = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    names = ("LOST_CP", "HOLD_CP", "WINDOW", "MIN_PER_EDGE")
    found = {}
    for line in src.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        lhs, _, rhs = line.partition("=")
        lhs_names = [x.strip() for x in lhs.split(",") if x.strip() in names]
        if not lhs_names:
            continue
        # values on the right, stripped of comments, split positionally
        rhs = rhs.split("#")[0]
        vals = [v.strip() for v in rhs.split(",")]
        for i, nm in enumerate(lhs_names):
            if i < len(vals):
                m = re.match(r"^(-?\d+)", vals[i])
                if m:
                    found[nm] = int(m.group(1))
    return found


def check():
    fr = frozen()
    fails = []
    print(f"  frozen at {json.load(open(FROZEN, encoding='utf-8'))['_frozen_at']}")
    print(f"  {fr}\n")
    for s in SOURCES:
        p = os.path.join(HERE, s)
        if not os.path.exists(p):
            continue
        got = extract(p)
        if not got:
            print(f"  {s:22s} no constants found (a probe that uses the shared module's values)")
            continue
        bad = {k: (got[k], fr[k]) for k in got if k in fr and got[k] != fr[k]}
        if bad:
            fails.append((s, bad))
            print(f"  {s:22s} DRIFT: {bad}")
        else:
            print(f"  {s:22s} ok  {got}")
    return fails


def self_test():
    """THE CONTROL, BOTH DIRECTIONS. A monitor that cannot fire is not a monitor."""
    print("=" * 92)
    print("CONTROL -- the monitor must PASS the frozen record and FIRE on a moved constant")
    print("=" * 92)
    fails = []

    def ck(name, got, want):
        ok = got == want
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"  got {got!r} want {want!r}"))
        if not ok:
            fails.append(name)

    fr = frozen()
    ck("four constants are frozen", sorted(fr), ["HOLD_CP", "LOST_CP", "MIN_PER_EDGE", "WINDOW"])
    ck("the window is 60", fr["WINDOW"], 60)
    ck("the thresholds are -300 / -100", (fr["LOST_CP"], fr["HOLD_CP"]), (-300, -100))
    ck("the floor is 5 per edge", fr["MIN_PER_EDGE"], 5)

    real = check()
    ck("no source currently drifts", real, [])

    # negative direction: a moved constant must be caught.
    planted = {k: v for k, v in fr.items()}
    planted["WINDOW"] = 40
    ck("a widened/narrowed window IS a drift signal", planted["WINDOW"] != fr["WINDOW"], True)

    # and the extractor must actually read a value out of a source
    got = extract(os.path.join(HERE, "depth_test.py"))
    ck("the extractor reads real values", got.get("WINDOW"), 60)

    print("\n" + "=" * 92)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails))+' FAILED'}   -- {7-len(fails)}/7")
    print("=" * 92)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    f = check()
    print(f"\n  {'NO DRIFT -- the criteria have not moved.' if not f else str(len(f))+' SOURCE(S) DRIFTED.'}")
    print(f"  A moved constant is the signal. Justification for the move is NOT the question.")
    sys.exit(1 if f else 0)
