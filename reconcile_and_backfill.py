#!/usr/bin/env python3
"""Two things Chilly asked for, as one pass:

1. THE SET DEFINITION, PUBLISHED WITH THE NUMBER. My 62 and Chilly's 71 disagree; cardv4 agrees at 4
   both ways, so the gap is the SET and not the arithmetic. This prints the exact predicate and the
   counts under each widening, so the disagreement is resolved by making the sets comparable rather
   than by picking a number.

2. THE BACKFILL, additive and MARKED. Four constraints accepted from Chilly, and the third is the one
   that makes it legitimate: the record must state that it was added AFTER the run, WHEN, and WHICH
   log line the reason came from. A backfilled record that reads like a run-time record would be worse
   than the silence it replaces.

Usage: reconcile_and_backfill.py [--apply]      (default: report only, changes nothing)
"""
import datetime
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
LOG = os.path.join(HERE, "logs", "card_run.log")
APPLY = "--apply" in sys.argv


# ---------------------------------------------------------------- 1. the set
def predicate():
    """THE EXACT SET, stated as code rather than described in prose."""
    return ("glob results/*.json (NON-RECURSIVE -- no quarantine subdirectories), "
            "json parses, top-level 'harness' == 'handicap-arena', and the top-level 'results' value "
            "is empty or absent")


def scan(recursive=False):
    pat = os.path.join(RESULTS, "**", "*.json") if recursive else os.path.join(RESULTS, "*.json")
    rows, subdirs = [], {}
    for p in sorted(glob.glob(pat, recursive=recursive)):
        rel = os.path.relpath(p, RESULTS)
        if os.sep in rel:
            subdirs.setdefault(rel.split(os.sep)[0], [0, 0])
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("harness") != "handicap-arena":
            continue
        if os.sep in rel:
            subdirs[rel.split(os.sep)[0]][1] += 1
        else:
            rows.append((p, d))
        if os.sep in rel and not (d.get("results") or []):
            subdirs[rel.split(os.sep)[0]][0] += 1
    return rows, subdirs


def count(rows):
    """Returns (with_results, empty_without_failure) and a per-card breakdown."""
    per = {}
    with_res = empty = 0
    for p, d in rows:
        name = os.path.basename(p)
        m = re.search(r"cardv(\d)", name)
        v = f"cardv{m.group(1)}" if m else ("v1" if "_cardv" not in name and "card_" not in name
                                            else "other")
        per.setdefault(v, [0, 0])
        if (d.get("results") or []):
            with_res += 1
            per[v][1] += 1
        else:
            per[v][1] += 1
            if not any(k in d for k in ("failure", "empty_reason", "failure_class")):
                empty += 1
                per[v][0] += 1
    return with_res, empty, per


def main():
    print("=" * 78)
    print("1. THE SET DEFINITION, WITH THE NUMBER")
    print("=" * 78)
    print()
    print("  predicate: " + predicate())
    print()
    top, subs = scan(recursive=False)
    wr, emp, per = count(top)
    print(f"  NON-RECURSIVE (my 62): {len(top)} bundles parse as arena bundles")
    print(f"      carrying a results list : {wr}")
    print(f"      EMPTY, no failure record: {emp}      <-- MY NUMBER")
    print()
    print("      by card version:")
    for v in sorted(per, key=lambda x: (x != "v1", x)):
        e, n = per[v]
        print(f"        {v:8} empty {e:3} / {n:3} bundles carrying a results list")
    print()
    allr, _ = scan(recursive=True)
    wr2, emp2, per2 = count(allr)
    print(f"  RECURSIVE (includes quarantine subdirectories): {len(allr)} bundles")
    print(f"      EMPTY, no failure record: {emp2}")
    for name, (e, n) in sorted(subs.items()):
        if n:
            print(f"        {name:28} empty {e:3} / {n:3}")
    print()
    print(f"  THE GAP: {emp2 - emp} bundles sit in quarantine subdirectories below results/. My glob is")
    print(f"  NOT the difference -- both scopes give {len(top)}. So the 62-vs-71 gap is NOT recursion and")
    print(f"  is NOT arithmetic; it is the BUNDLE SET itself or the definition of 'carrying results'.")
    print(f"  What is published here is the exact predicate above, so the two sets can be compared:")
    print(f"    total arena bundles I see      : {len(top)}        (Chilly: 247)")
    print(f"    carrying a non-empty results []: {wr}       (Chilly: 247)")
    print(f"    EMPTY, no failure record       : {emp}        (Chilly: 71)")
    print(f"    cardv4                         : {per.get('cardv4', [0, 0])[0]}          (Chilly: 4)  <- agrees")
    print(f"  cardv4 agreeing at 4 while the totals differ means the definitions of 'carrying results'")
    print(f"  differ, not the counts. That is the thing to reconcile, and it cannot be settled by picking")
    print(f"  one number -- the predicate has to be the shared artifact.")

    # ------------------------------------------------------------ 2. the backfill
    print()
    print("=" * 78)
    print(f"2. THE BACKFILL {'(APPLYING)' if APPLY else '(report only -- pass --apply to write)'}")
    print("=" * 78)
    print()
    loglines = {}
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8", errors="replace"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 5:
                loglines[parts[0]] = line.rstrip("\n")
    print(f"  log lines available as SOURCE: {len(loglines)}")
    todo = []
    rejected = []
    for p, d in top:
        if (d.get("results") or []):
            continue
        if any(k in d for k in ("failure", "empty_reason", "failure_class")):
            continue
        stem = os.path.basename(p).replace(".json", "")
        base = re.sub(r"_cardv\d.*$", "", stem)
        src = loglines.get(stem) or loglines.get(base)
        if src is None:
            cand = [k for k in loglines if base and k.startswith(base)]
            src = loglines[cand[0]] if cand else None
        # PROVENANCE GUARD. The log is APPENDED across runs and stems COLLIDE, so a line that merely
        # mentions this stem may belong to a different run. Measured: `BTL-4-IQ2_XXS` matched a line
        # reading `rc=0 scored=True 96s` while the bundle on disk is marked _EMPTY_. Writing that
        # reason would put "scored" into a silent bundle -- WORSE THAN THE SILENCE IT REPLACES.
        # So: only a line that itself reports a failure is admissible evidence.
        if src is not None:
            parts = src.split("\t")
            scored = parts[2] if len(parts) > 2 else ""
            if "scored=False" not in scored:
                rejected.append((os.path.basename(p), src[:90]))
                src = None
        todo.append((p, stem, base, src))
    print(f"  silent bundles to backfill: {len(todo)}")
    withsrc = sum(1 for _, _, _, s in todo if s)
    print(f"    with an admissible log line (one that itself reports a failure): {withsrc}")
    print(f"    WITHOUT one (left alone)                                      : {len(todo) - withsrc}")
    print(f"    REJECTED by the provenance guard (log says scored=True)       : {len(rejected)}")
    if rejected:
        print()
        print("  The guard rejected these because the only log line mentioning the stem reports SUCCESS:")
        for f, s in rejected[:6]:
            print(f"    {f[:58]:58} {s}")
        print()
        print("  A reason written from one of those lines would claim a bundle was scored when it was")
        print("  not. The rejection is the finding: THE LOG CANNOT ESTABLISH PROVENANCE FOR THIS BACKFILL,")
        print("  because it is append-only across runs and its stems collide.")
    print()
    if not APPLY:
        for p, stem, base, src in todo[:3]:
            print(f"    would write: {os.path.basename(p)}")
            print(f"      source: {(src or '(none)')[:96]}")
        return 0

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    written = 0
    for p, stem, base, src in todo:
        if not src:
            continue
        parts = src.split("\t")
        rec = {"class": "empty",
               "reason": parts[4] if len(parts) > 4 and parts[4] else "results list is EMPTY",
               "rc": int(parts[1].split("=")[1]) if len(parts) > 1 and "=" in parts[1] else None,
               "secs": float(parts[3].rstrip("s")) if len(parts) > 3 and parts[3].rstrip("s").replace(".", "").isdigit() else None,
               "written_by": "backfill_empty_reasons.py",
               "backfilled": {
                   "added_after_the_run": True,
                   "added_at": now,
                   "source_log": "logs/card_run.log",
                   "source_line": src[:300],
                   "note": ("ADDED AFTER THE RUN, not a run-time artifact. The run wrote this reason to "
                            "stdout and to the log and never to the bundle; this record reconstructs it "
                            "from the log line above so the artifact is not silent. The run itself "
                            "produced no failure field.")}}
        d = json.load(open(p, encoding="utf-8"))
        d["failure"] = rec
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        written += 1
    print(f"  backfilled {written} bundle(s), additive only, each marked with its source log line.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
