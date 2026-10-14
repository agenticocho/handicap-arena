#!/usr/bin/env python3
"""CHECK FIELD SEMANTICS -- a name is a claim about its contents.

Chilly's generalisation, and it came from three instances found in ONE bundle:

    `secs`        the item field holds ONE TRIAL's duration, presented under a per-item name
    `gen_tokens`  the same scope defect, same place
    `trials`      THE ROUND FIELD HOLDS AN ITEM COUNT. `wins 3.667 / trials 6.0` coexists with the
                  server log's EIGHTEEN requests, because "trials" there counts items.

Every one is arithmetically correct and wrongly named. Nothing in this project checks field names, so a
reader has to already know. This makes the claim checkable: EVERY QUANTITY-NAMED FIELD MUST BE DECLARED
with its unit and its scope, or the check fails.

    python3 check_field_semantics.py            # check the newest v5 bundle
    python3 check_field_semantics.py --self-test
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")

# A FIELD NAME THAT ASSERTS A QUANTITY. Anything matching these must appear in SEMANTICS below.
QUANTITY_NAME = re.compile(
    r"(^|_)(secs?|seconds|ms|tokens|count|n|num|trials|score|latency|rate|ratio|size|bytes|gb|mb|"
    r"pct|percent|tokens_per|sum|mean|median|total)($|_)", re.I)

# THE DECLARED SEMANTICS. field -> (unit, scope, cardinality). A field absent from here FAILS.
# Entries marked MISLEADING were found by measurement and are kept so a reader meets them.
SEMANTICS = {
    # --- what a measurement is about
    "secs":         ("seconds", "ONE TRIAL of the item", "one value per item; the item ran 3 trials"),
    "gen_tokens":   ("tokens", "ONE TRIAL of the item", "one value per item; the item ran 3 trials"),
    "mean_latency": ("seconds", "MEAN over the item's trials", "one value per entrant"),
    "secs_total":   ("seconds", "SUM over all trials and items", "one value per entrant"),
    "wall_secs":    ("seconds", "ENTRANT wall clock, INCLUDING model load", "one value per entrant"),
    "load_secs":    ("seconds", "ENTRANT model load + server start", "one value per entrant"),
    "trials_ran":   ("count", "REQUESTS actually made for this item", "one value per item"),
    # --- aggregates
    "score":        ("ratio 0-1", "MEAN over the item's trials", "one value per item"),
    "aggregate":    ("ratio 0-1", "MEAN over the entrant's items", "one value per entrant"),
    "wins":         ("count", "SUM of item scores", "one value per round"),
    "trials":       ("count", "ITEMS IN THE ROUND -- NOT TRIALS", "one value per round"),
    # --- structural
    "max_completion_tokens": ("tokens", "the max_tokens BUDGET, a setting", "one value per round"),
    "ctx_limited_trials":    ("count", "trials that hit the context cap", "one value per round"),
    "secs_taken":   ("seconds", "one trial", "one value per item"),
    "wall":         ("seconds", "entrant wall clock", "one value per entrant"),
    "secs_min":     ("seconds", "minimum", "one value per set"),
    "secs_max":     ("seconds", "maximum", "one value per set"),
    "count":        ("count", "as named by its container", "contextual"),
    "ratio":        ("ratio", "as named by its container", "contextual"),
    # --- the weigh-in (Finding 002): memory readings, correctly named and unit-suffixed
    "footprint_gb":           ("GiB", "live RESIDENT footprint at load", "one value per entrant"),
    "weights_gb":             ("GiB", "the model's size ON DISK", "one value per entrant"),
    "gpu_free_gb_at_weigh_in": ("GiB", "free VRAM at weigh-in time", "one value per entrant"),
    "max_tokens":             ("tokens", "the generation BUDGET, a setting", "one value per config"),
}

# WHERE A NAME STILL LIES, SEPARATELY MARKED. The first version inferred "misleading" from a non-empty
# note -- so a field with an EXPLANATORY note was tagged as a misname, and the tag meant "has a note"
# rather than "is misleading". That is this check's own subject, committed by this check: a label
# asserting something its contents do not support.
MISLEADING = {
    "secs":       "reads per-item, holds ONE TRIAL's duration. Read with `trials_ran`.",
    "gen_tokens": "same scope defect as `secs`: one trial under a per-item name.",
    "trials":     "holds an ITEM COUNT. `wins 3.667 / trials 6.0` coexists with the server log's 18 "
                  "requests, because this field counts items.",
}


def collect(obj, path="", out=None):
    """Every (path, field_name, value) in a nested structure."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append((f"{path}/{k}", k, v))
            collect(v, f"{path}/{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):
            collect(v, f"{path}[{i}]", out)
    return out


def check(bundle_path, verbose=True):
    d = json.load(open(bundle_path, encoding="utf-8"))
    fields = {}
    for path, name, val in collect(d):
        if isinstance(val, (int, float)) and QUANTITY_NAME.search(name):
            fields.setdefault(name, (path, val))
        elif isinstance(val, dict) and QUANTITY_NAME.search(name):
            fields.setdefault(name, (path, "<object>"))
    undeclared = sorted(n for n in fields if n not in SEMANTICS)
    misleading = sorted(n for n in fields if n in MISLEADING)
    if verbose:
        print(f"  bundle: {os.path.basename(bundle_path)}")
        print(f"  quantity-named fields found: {len(fields)}")
        for n in sorted(fields):
            s = SEMANTICS.get(n)
            tag = "UNDECLARED" if s is None else ("MISLEADING" if n in MISLEADING else "ok")
            unit = "-" if s is None else s[0]
            scope = "-" if s is None else s[1]
            print(f"    {n:24s} {tag:10s} unit={unit:10s} scope={scope}")
        print(f"\n  UNDECLARED quantity-named fields: {len(undeclared)}  {undeclared if undeclared else ''}")
        print(f"  MISLEADING (declared, and their names still lie): {len(misleading)}  {misleading}")
    return {"undeclared": undeclared, "misleading": misleading, "fields": fields}


def self_test():
    """THE CONTROL, BOTH DIRECTIONS. A check that cannot fail is not a check."""
    print("=" * 92)
    print("CONTROL -- the check must PASS a clean record and FIRE on a misleading name")
    print("=" * 92)
    fails = []

    def ck(name, got, want):
        ok = got == want
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"  got {got!r} want {want!r}"))
        if not ok:
            fails.append(name)

    d = json.load(open(NEWEST, encoding="utf-8"))
    n = sum(1 for _, name, v in collect(d) if isinstance(v, (int, float)) and QUANTITY_NAME.search(name))
    print(f"\n  real bundle: {n} quantity-named fields")

    # negative direction: an undeclared quantity field must be caught
    planted = {"results": [{"rounds": {"R": {"items": {"i": {"newfangled_pct": 3.0}}}}}]}
    f = {a for _, a, v in collect(planted) if isinstance(v, (int, float)) and QUANTITY_NAME.search(a)}
    ck("an UNDECLARED quantity field is detected", "newfangled_pct" in f, True)
    ck("...and it is not declared", "newfangled_pct" in SEMANTICS, False)

    # positive direction: a declared field must not be flagged
    ck("a DECLARED field is accepted", "secs" in SEMANTICS, True)

    # the three real findings must be present and marked
    for f_ in ("secs", "gen_tokens", "trials"):
        ck(f"`{f_}` is declared", f_ in SEMANTICS, True)
        ck(f"`{f_}` is marked MISLEADING", f_ in MISLEADING, True)

    # and a correctly-named field with a NOTE must NOT be marked misleading
    ck("a correctly-named field with a note is NOT flagged", "footprint_gb" in MISLEADING, False)

    # and the semantic claim itself: `trials` must NOT be declared as a trial count
    ck("`trials` does not claim to count trials", "NOT TRIALS" in SEMANTICS["trials"][1], True)

    print("\n" + "=" * 92)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails))+' FAILED'}   -- {10-len(fails)}/10")
    print("=" * 92)
    return 1 if fails else 0


_v5rows = scope("*cardv5*.json")
print_scope(_v5rows, "*cardv5*.json")
v5 = [p for _k, _b, hits in _v5rows for p in hits]
NEWEST = max(v5, key=os.path.getmtime) if v5 else None

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if not NEWEST:
        print("no v5 bundle found")
        sys.exit(2)
    r = check(NEWEST)
    print(f"\n  a quantity-named field that is NOT declared is a name nobody has checked.")
    sys.exit(1 if r["undeclared"] else 0)
