#!/usr/bin/env python3
"""Measured list: every destination named `results` that a script in this tree still binds.

COUNTED BY DESTINATION, IN ANY FORM. The two `os.path.join` patterns this file used to carry could
not see an ABSOLUTE literal into the record (depth_test.py:27) or `os.path.join(os.path.dirname(
__file__), "results")` (darts/darts.py:706,715) -- a writer is bound by its DESTINATION, not by its
syntax. So the DETECTION is now the one scripts/audit_results_binder_forms.py already implements
(loaded BY PATH, so there is one detector and not two that drift), and every row it finds is
CLASSIFIED by where the path points:

  record_binder             <worktree>/results, or an absolute literal into the legacy record or one
                            of its declared duplicate copies.                      TARGET 0
  named_write_destination   a named directory's own results/ (darts/results).     TARGET 0
  log_coordinate            a LIVE log-path construction, DECLARED in the manifest as
                            deferred:log-coordinate:t_c442023d + landed_by 8f51ae8 -- a coordinate,
                            not a binder, so it is reported and is NOT residue.

The manifest (RESULTS_BINDERS_MANIFEST.json) carries one row per file with its status; a binder with
no declared status is reported UNDECLARED and is a failure, not a number. RESIDUE ZERO IS A NUMBER
THE TOOL EXITS ON: the exit code is non-zero while residue > 0.

usage:   python3 scripts/list_results_binders.py [tree] [--manifest PATH]
exit:    0 when residue is 0
         1 while residue > 0   (residue = record_binders + named_write_destinations)
         2 if the tree names a binder the manifest does not declare, or the manifest cannot be read
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
import cabinet_root as _root                                          # noqa: E402

DEFAULT_MANIFEST = os.path.join(REPO, "RESULTS_BINDERS_MANIFEST.json")

# THE TWO FORMS THE COUNTER USED TO KNOW -- still a RECORD binder, and still detected. Kept here so
# that the counter's own history is readable next to the classifier that replaced it.
LEGACY_FORMS = re.compile(r'(?m)^\s*[A-Z_]*RESULTS\s*=\s*os\.path\.join\('
                          r'|os\.path\.join\((HERE|ARENA|os\.path\.dirname\(os\.path\.abspath\(__file__\)\)), "results"')
# a quoted literal path with `results` as a whole component (NOT `results/supersessions`, whose last
# component is something else, and NOT `"results/"` quoted as a bare name)
ABS_LITERAL = re.compile(r'"([^"]*?)/(results)(?:/[^"]*)?"')
# the file's OWN directory + results, i.e. <dirname(thisfile)>/results
PARENT_JOIN = re.compile(r'os\.path\.join\(\s*os\.path\.dirname\(\s*__file__\s*\)\s*,\s*"results"\s*\)')
# the destinations that ARE the record: declared in cabinet_root, never typed here
RECORD_DESTS = [os.path.realpath(p) for p in
                (_root.LEGACY_RECORD, *_root.DUPLICATE_RECORD_TREES)]

CLASSES = ("record_binder", "named_write_destination", "log_coordinate")


def classify(rel, text, root):
    """-> (class, destination) for a detected line, or (None, None) if it binds no destination.

    BY DESTINATION, IN ANY FORM: the syntax decides nothing, the path does.
    """
    if LEGACY_FORMS.search(text):
        return "record_binder", os.path.join(root, "results")
    if PARENT_JOIN.search(text):
        own = os.path.dirname(rel)
        dest = os.path.join(root, own, "results") if own else os.path.join(root, "results")
        return ("record_binder" if not own else "named_write_destination"), dest
    m = ABS_LITERAL.search(text)
    if m:
        dest = os.path.realpath(m.group(1) + "/" + m.group(2))
        if dest in RECORD_DESTS or dest == os.path.realpath(os.path.join(root, "results")):
            return "record_binder", dest
        return "named_write_destination", dest
    return None, None


def load_audit():
    """The ONE detector, loaded by path -- the idiom the gate already uses."""
    spec = importlib.util.spec_from_file_location(
        "audit_results_binder_forms", os.path.join(HERE, "audit_results_binder_forms.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["audit_results_binder_forms"] = m
    spec.loader.exec_module(m)
    return m


def find_binders(root, audit=None):
    """-> [{"file", "class", "lines", "destination"}] -- one row per (file, class). THE DETECTION is
    the audit's; the CLASS is by destination; grouping is here so the guard can re-use both."""
    audit = audit or load_audit()
    rows, by = [], {}
    for r in audit.find_rows(root):
        cls, dest = classify(r["file"], r["text"], root)
        if cls is None:
            continue
        key = (r["file"], cls)
        by.setdefault(key, {"file": r["file"], "class": cls, "lines": [],
                            "destination": dest})
        by[key]["lines"].append(r["line"])
    for (f, cls) in sorted(by):
        by[(f, cls)]["lines"].sort()
        rows.append(by[(f, cls)])
    return rows


def load_manifest(path):
    raw = open(path, "rb").read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="every `results` destination a script still binds")
    ap.add_argument("tree", nargs="?", default=".")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    a = ap.parse_args()
    root = os.path.abspath(a.tree)
    try:
        audit = load_audit()
        man, msha = load_manifest(a.manifest)
    except OSError as e:
        print(f"STATE: BLOCKED. An instrument cannot be read: {e}")
        print("  the counter carries no exclusion list of its own -- without the declaration there "
              "is nothing to measure against.")
        return 2
    entries = {e["script"]: e for e in man.get("entries", [])}
    fixed = {f["rel"] for f in man.get("fixed_mechanism_files", [])}
    live = [r for r in find_binders(root, audit) if r["file"] not in fixed]

    # THE LOG COORDINATES ARE DECLARED, NOT DETECTED: they were re-pointed at
    # cabinet_root.log_dir()/log_path() by t_c442023d, so there is no live construction left to
    # find -- what remains is the DECLARATION, and it is reported so it cannot go quiet.
    logrows = [{"file": s, "class": "log_coordinate", "lines": [], "destination": "<declared>"}
               for s, e in sorted(entries.items())
               for ed in e["edges"] if ed.get("kind") == "log-coordinate"]

    rows = live + logrows
    per = {c: [r for r in rows if r["class"] == c] for c in CLASSES}
    undeclared = sorted(r["file"] for r in live if r["file"] not in entries)
    print(f"{len(per['record_binder'])} record_binders + {len(per['named_write_destination'])} "
          f"named_write_destinations + {len(per['log_coordinate'])} log_coordinates in {root}")
    for cls in CLASSES:
        for r in per[cls]:
            e = entries.get(r["file"])
            status = "UNDECLARED" if e is None else " + ".join(
                ed["status"] for ed in e["edges"] if ed.get("kind") != "log-coordinate"
                or cls == "log_coordinate")
            print(f"  {cls:24} {r['file']:44} lines {r['lines']}  [{status}]")
    residue = len(per["record_binder"]) + len(per["named_write_destination"])
    print(f"residue {residue} = record {len(per['record_binder'])} + named "
          f"{len(per['named_write_destination'])}  (targets 0 / 0; the {len(per['log_coordinate'])} "
          f"log_coordinates are DECLARED and are not residue)")
    print(f"manifest {os.path.abspath(a.manifest)} sha256 {msha}")
    if undeclared:
        print(f"UNDECLARED: {len(undeclared)} binder(s) the manifest does not carry: {undeclared}")
        print("STATE: BLOCKED. A binder that is not declared is a binder nobody has decided about.")
        return 2
    if residue:
        print(f"STATE: RESIDUE. {residue} binder(s) still bind a results destination -- exit non-zero "
              f"until that number is 0.")
        return 1
    print("STATE: RESIDUE ZERO. Nothing in this tree binds a results destination any more.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
