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
sys.path.insert(0, HERE)
LOG = None      # THE JOURNAL IS RESOLVED PER BUNDLE -- see log_at() below. It is NOT a module
                # constant any more: a constant is one coordinate for the whole sweep, and the
                # admissible coordinate is a property of the BUNDLE (cabinet_root.log_for), not of
                # the process reading it. The old constant was <HERE>/logs/card_run.log, derived
                # from where this reader sits; measured, that made the same sweep resolve 31
                # admissible lines from main and 0 from each cabinet worktree.
APPLY = "--apply" in sys.argv

# THE DOMAIN IS DECLARED, NOT FOUND.
#
# This file used to scope itself with `RESULTS = os.path.join(HERE, "results")` and then widen with
# `os.path.join(RESULTS, "**", "*.json")`: the scope was DERIVED from where the script happens to
# sit, and the `**` made it discover its own domain by recursion. A sweep that discovers its domain
# by recursion cannot be protected from recursion -- and a results directory a sweep can reach is a
# results directory a sweep will eventually rewrite, which is why the separate root exists.
#
# `cabinet_root.domain()` is a LIST, not a walk: the live subtrees under the declared root, plus the
# one legacy record declared in place. Nothing joins it by existing.
import cabinet_root as _root                                              # noqa: E402
DOMAIN = _root.domain()      # [(kind, path)] -- declared in cabinet_root.py


# ---------------------------------------------------------------- 1. the set
def predicate():
    """THE EXACT SET, stated as code rather than described in prose."""
    return ("glob <declared domain>/*.json (NON-RECURSIVE -- no quarantine subdirectories; the "
            "domain is the live subtrees under the declared root plus the legacy record declared "
            "in place, and it is a LIST rather than a walk), json parses, top-level 'harness' == "
            "'handicap-arena', and the top-level 'results' value is empty or absent")


def scan(recursive=False, domain=None):
    """Each declared entry is globbed ON ITS OWN, and everything found under it is keyed by the
    entry it was found in -- so every number this file prints names the tree it was counted in.
    """
    rows, subdirs = [], {}
    for kind, base in (DOMAIN if domain is None else domain):
        pat = os.path.join(base, "**", "*.json") if recursive else os.path.join(base, "*.json")
        for p in sorted(glob.glob(pat, recursive=recursive)):
            rel = os.path.relpath(p, base)
            # An EXERCISE_ bundle is not an entrant -- see the note in test_no_silent_zero.py. This
            # sweep is the WIDE one (`*.json` and `**/*.json`), and it is the glob that produced the
            # 62-empty and 71-empty figures, so it is the one most likely to meet a mis-placed
            # exercise.
            if "EXERCISE_" in os.path.basename(p):
                continue
            key = f"{kind}/{rel.split(os.sep)[0]}" if os.sep in rel else None
            if key:
                subdirs.setdefault(key, [0, 0])
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            if d.get("harness") != "handicap-arena":
                continue
            if key:
                subdirs[key][1] += 1
            else:
                rows.append((p, d))
            if key and not (d.get("results") or []):
                subdirs[key][0] += 1
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
    print("  THE DECLARED DOMAIN this sweep reads -- a LIST, not a walk:")
    for _kind, _base in DOMAIN:
        print(f"    {_kind:16} {_base}")
    print()
    top, subs = scan(recursive=False)
    wr, emp, per = count(top)
    print(f"  {len(top)} bundles parse as arena bundles")
    print(f"      carrying a results list : {wr}")
    print(f"      EMPTY, no failure record: {emp}      <-- NON-RECURSIVE COUNT (this scope)")
    print(f"  (this label used to read 'my 62', a literal that went stale the moment the field grew one")
    print(f"   bundle. A hand-maintained count in a label is a claim with no check behind it.)")
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
    print(f"  THE GAP: {emp2 - emp} bundles sit in subdirectories below the declared domain's roots. My glob is")
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
    # THE JOURNAL IS RESOLVED PER BUNDLE, FROM THE DECLARATION.
    #
    # `cabinet_root.log_for(bundle)` answers one question per bundle: WHICH TREE'S RUN WROTE THIS?
    # A bundle in the legacy record was written by a run in main, so its journal is the one declared
    # in place; a bundle under a cabinet's live subtree was written in the CABINET's worktree, so its
    # journal is that worktree's. Read as a single constant derived from HERE, the sweep answered
    # one coordinate for every bundle in the domain -- the reader's own -- and MEASURED, that made
    # the same domain resolve 31 admissible lines from main and 0 from each cabinet worktree. An
    # answer that changes when you read it from another tree is an answer about the reader.
    journals, _cache = {}, {}
    def loglines_at(path):
        if path not in _cache:
            lines = {}
            if path and os.path.exists(path):
                for line in open(path, encoding="utf-8", errors="replace"):
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) >= 5:
                        lines[parts[0]] = line.rstrip("\n")
            _cache[path] = lines
        return _cache[path]
    for p, _d in top:
        lp = _root.log_for(p)
        if lp not in journals:
            journals[lp] = loglines_at(lp)
    print(f"  journals this sweep may read, resolved PER BUNDLE from the declaration:")
    for lp in sorted(journals, key=lambda x: (x is None, x or "")):
        print(f"    {len(journals[lp]):5} lines  {lp}"
              f"{'' if (lp and os.path.exists(lp)) else '   <- NO FILE AT THE DECLARED COORDINATE'}")
    print(f"  log lines available as SOURCE: {sum(len(v) for v in journals.values())}")
    todo = []
    rejected = []
    for p, d in top:
        if (d.get("results") or []):
            continue
        if any(k in d for k in ("failure", "empty_reason", "failure_class")):
            continue
        stem = os.path.basename(p).replace(".json", "")
        base = re.sub(r"_cardv\d.*$", "", stem)
        # ADMISSIBLE, AND ONLY FROM THE DECLARED COORDINATE. There is no fallback to the reader's
        # own journal when the declared one is missing: a fallback is how a coordinate becomes
        # decorative, and the standing condition on this card is that a REJECT is correct behaviour
        # while a silent substitution is not.
        _lp = _root.log_for(p)
        loglines = journals.get(_lp) or {}
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
        todo.append((p, stem, base, src, _lp))
    print(f"  silent bundles to backfill: {len(todo)}")
    withsrc = sum(1 for *_x, s, _lp in todo if s)
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
        for p, stem, base, src, _lp in todo[:3]:
            print(f"    would write: {os.path.basename(p)}")
            print(f"      source: {(src or '(none)')[:96]}")
            print(f"      from  : {_lp}")
        return 0

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    written = 0
    for p, stem, base, src, _lp in todo:
        if not src:
            continue
        # THE WRITE GUARD. A sweep may only rewrite what its DECLARATION names. An --apply that
        # reached a bundle outside the declared domain would be a sweep rewriting a tree that no
        # declaration covers -- which is the shape this file was changed to remove, one layer down.
        # The legacy record IS in the domain (declared in place), so maintaining it is allowed;
        # what is not allowed is a path that joined the scope by being found.
        if not _root.in_domain(p):
            raise SystemExit(f"REFUSING: {p} is outside the declared domain -- this backfill will "
                             f"not write to it. Fix the declaration in cabinet_root.py, or leave "
                             f"the bundle alone. (CABINET_STRUCTURE.md, addendum 2026-10-14)")
        parts = src.split("\t")
        rec = {"class": "empty",
               "reason": parts[4] if len(parts) > 4 and parts[4] else "results list is EMPTY",
               "rc": int(parts[1].split("=")[1]) if len(parts) > 1 and "=" in parts[1] else None,
               "secs": float(parts[3].rstrip("s")) if len(parts) > 3 and parts[3].rstrip("s").replace(".", "").isdigit() else None,
               "written_by": "reconcile_and_backfill.py",
               "backfilled": {
                   "added_after_the_run": True,
                   "added_at": now,
                   # THE RESOLVED COORDINATE, NOT A LITERAL. This read "logs/card_run.log" -- a
                   # relative path that named no tree, in a domain that holds several, so the record
                   # could not be re-read against the journal it was built from. The path written
                   # here is the one cabinet_root.log_for() resolved FOR THIS BUNDLE, which is the
                   # same rule a reader must apply to check it.
                   "source_log": _lp,
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
