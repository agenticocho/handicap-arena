#!/usr/bin/env python3
"""THE FOUR FRONT-END CLAUSES AS CHECKS -- each with a NEGATIVE CONTROL.

Each clause is one of four INVERSIONS that has already happened once, and the numbers in
FRONTEND_CONTRACT_ACCEPTANCE.md are what make them clauses rather than taste. The checks
are mechanical and read only the record; no local paths are written out (public repo).

WHY THE CONTROLS ARE THE POINT. A check that cannot fail is INVISIBLE: it passes forever,
nobody investigates a pass, and the pass gets quoted as evidence. So every check here has
a control that MUST fail it, and `--selftest` reports 4/4 only if all four controls were
caught. Miss a control and the script fails -- the same rule as the record itself.

C1  sort on the aggregate; the belt is a LABEL, never a sort key.
      measured: 0.7222 / 0.7778 / 0.8333 each mapped to TWO belts, so a belt sort ranks a
      weaker model above a stronger one.
C2  a scratch is NO MEASUREMENT, never a zero; keyed off `results == []`, never the filename.
      measured: the EMPTY marker covered 9 of 16 for a period; the 7 unmarked were exactly
      the v1 counterparts, which a filename-keyed view renders as zeros.
C3  `card_version` is a HARD PARTITION and is NOT the release version; absent is not 1.
      measured: 42 graded rows on v1, 33 on v2, different suites.
C4  truncation is OUT OF ROOM, not a wrong answer; no latency without its `placement`.
      measured: 22 v1 trials stopped on the token cap; autofit and ngl99 are different
      measurements.

Usage:
    python3 check_frontend_clauses.py                     # check results/
    python3 check_frontend_clauses.py --view view.json    # also check a view declaration
    python3 check_frontend_clauses.py --selftest          # 4/4 controls MUST be caught
"""
import argparse
import glob
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
BELT_ORDER = ["White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Black"]


def belt_rank(b):
    return BELT_ORDER.index(b) if b in BELT_ORDER else None


def exact(rounds):
    """The aggregate as a RATIONAL over the counts -- never the stored float. `round(x,4)`
    does not even recover the order: two entries are both exactly 10/18."""
    w = sum(Fraction(str(r.get("wins") or 0)) for r in rounds)
    t = sum(Fraction(str(r.get("trials") or 0)) for r in rounds)
    return (w / t) if t else None


def rows_from(record):
    out = []
    for e in record.get("results") or []:
        rounds = list((e.get("rounds") or {}).values())
        out.append({"name": os.path.basename(str(e.get("gguf") or e.get("sha256") or "?")),
                    "card_version": e.get("card_version"),
                    "belt": (e.get("grade") or {}).get("belt"),
                    "exact": exact(rounds), "rounds": rounds, "entrant": e})
    return out


def c1(rows, view=None):
    """The belt is a label ON the aggregate: it never orders anything."""
    f = []
    for a in rows:
        for b in rows:
            if a is b or a["exact"] is None or b["exact"] is None:
                continue
            if a["card_version"] != b["card_version"]:
                continue
            ra, rb = belt_rank(a["belt"]), belt_rank(b["belt"])
            if ra is None or rb is None:
                continue
            if a["exact"] > b["exact"] and ra < rb:
                f.append("C1 inversion: %s (agg %s, belt %s) is ranked BELOW %s (agg %s, belt %s)"
                         % (a["name"], a["exact"], a["belt"], b["name"], b["exact"], b["belt"]))
    if view is not None:
        s = str(view.get("sort", "")).lower().replace("entrant.", "")
        if s in ("belt", "grade.belt", "cord", "division", "grade"):
            f.append("C1 the view declares a non-aggregate sort key: sort=%r" % view.get("sort"))
    return f


def c2(bundles):
    """Where the filename marker and the record disagree, the RECORD is the data."""
    f = []
    for path, d in bundles:
        scratched = (d.get("results") == [])
        marker = "_EMPTY_" in os.path.basename(path).upper()
        if scratched != marker:
            f.append("C2 %s: a FILENAME-keyed reader says scratched=%s; the record says %s "
                     "(results == %s) -- the label is a rename applied afterwards"
                     % (os.path.basename(path), marker, scratched, d.get("results")))
    return f


def c3(rows):
    """A hard partition, and an absence is a fact rather than a value."""
    f = []
    seen = {}
    for r in rows:
        v = r["card_version"]
        if v is None:
            f.append("C3 %s: card_version ABSENT -- that is not 1; render it as inferred or refuse"
                     % r["name"])
        else:
            seen.setdefault(v, 0)
            seen[v] += 1
    return f


def c4(rows):
    """Truncation is out of room; a latency is not comparable without its placement."""
    f = []
    for r in rows:
        e = r["entrant"]
        if e.get("mean_latency") is not None and not (e.get("weigh_in") or {}).get("placement"):
            f.append("C4 %s: a latency figure with no `placement` beside it" % r["name"])
        for i, rd in enumerate(r["rounds"]):
            tr = bool(rd.get("truncated"))
            fr = rd.get("finish_reasons") or {}
            capped = any(k != "stop" for k in fr)
            if tr and not capped:
                f.append("C4 %s round %d: truncated=true but finish_reasons=%r shows no cap"
                         % (r["name"], i, fr))
            if capped and not tr:
                f.append("C4 %s round %d: finish_reasons=%r hit a cap but truncated is not set"
                         % (r["name"], i, fr))
    return f


# --- the controls: each MUST fail its check ---------------------------------------------

def controls():
    caught = {}
    # C1: an inversion -- the higher aggregate carrying the LOWER belt.
    caught["C1"] = bool(c1([
        {"name": "A", "card_version": 2, "belt": "Orange", "exact": Fraction(9, 10),
         "rounds": [], "entrant": {}},
        {"name": "B", "card_version": 2, "belt": "Green", "exact": Fraction(8, 10),
         "rounds": [], "entrant": {}}]))
    # C1b: a view that sorts on a belt.
    caught["C1-view"] = bool(c1([], view={"sort": "belt"}))
    # C2: a scratched bundle whose filename carries no marker.
    caught["C2"] = bool(c2([("/x/BTL-4_IQ2_autofit_neutral.json", {"results": []})]))
    # C3: an entrant whose card_version is absent.
    caught["C3"] = bool(c3([{"name": "X", "card_version": None, "belt": "White",
                             "exact": None, "rounds": [], "entrant": {}}]))
    # C4: a truncated round showing no cap, and a latency with no placement.
    caught["C4"] = bool(c4([{"name": "Y", "card_version": 2, "belt": "White", "exact": None,
                             "entrant": {"mean_latency": 6.5},
                             "rounds": [{"truncated": True, "finish_reasons": {"stop": 3}}]}]))
    return caught


def main(argv=None):
    ap = argparse.ArgumentParser(description="the four front-end clauses, as checks")
    ap.add_argument("--results", default=RESULTS)
    ap.add_argument("--view", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        got = controls()
        for k in sorted(got):
            print("  %-8s %s" % (k, "CAUGHT" if got[k] else "*** MISSED -- a check that cannot fail ***"))
        bad = [k for k, v in got.items() if not v]
        print("  controls caught %d/%d" % (len(got) - len(bad), len(got)))
        return 1 if bad else 0

    bundles, rows = [], []
    for p in sorted(glob.glob(os.path.join(a.results, "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:                                               # noqa: BLE001
            print("  UNREADABLE %s" % os.path.basename(p))
            continue
        if d.get("harness") != "handicap-arena":
            continue
        bundles.append((p, d))
        rows += rows_from(d)
    view = None
    if a.view:
        try:
            view = json.load(open(a.view, encoding="utf-8"))
        except Exception:                                               # noqa: BLE001
            print("  view is unreadable: %s" % a.view)
            return 2

    fails = c1(rows, view) + c2(bundles) + c3(rows) + c4(rows)
    print("C1/C2/C3/C4 over %d bundles, %d entrant rows" % (len(bundles), len(rows)))
    for m in fails:
        print("  FAIL  %s" % m)
    print("  %s -- %d failure(s)" % ("PASS" if not fails else "FAILED", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
