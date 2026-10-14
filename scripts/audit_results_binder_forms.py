#!/usr/bin/env python3
"""INDEPENDENT FORM AUDIT of scripts/list_results_binders.py -- AND THE ONE DETECTOR.

WHY THIS EXISTS. `list_results_binders.py` used to match TWO syntactic forms:

    ^\\s*[A-Z_]*RESULTS\\s*=\\s*os\\.path\\.join\\(
    os\\.path\\.join\\((HERE|ARENA|os\\.path\\.dirname\\(os\\.path\\.abspath\\(__file__\\)\\)), "results"

Its COUNT was exact for its PATTERN, and its pattern was narrower than its own headline. This walks
every .py file and reports every line that can build a path whose last component is the literal
directory name "results", in ANY form -- os.path.join with any first argument, an absolute literal,
an f-string, a / division -- then splits them into:

  A. lines the counter DOES match                 (sanity: same files?)
  B. lines that name a `results` directory the counter does NOT match   <- the blind spots
  C. files that appear in B and are not in the counter's list
  D. of those, the ones that are NOT PROSE -- a real path, in a form the counter misses

A line whose only mention of "results" is a DICT KEY (d.get("results"), d["results"], a
"results": [...] literal) is NOT a path and is filtered out. Comment lines are skipped.

AND SINCE t_fdf55800 THIS FILE IS THE ONE DETECTOR: `find_rows(root)` is importable, and
list_results_binders.py loads it BY PATH and classifies each row BY ITS DESTINATION -- so the
counter and the audit cannot drift, and a binder in a form neither of the old two patterns knew
(depth_test.py's absolute literal, darts/darts.py's `dirname(__file__)`) is measured rather than
missed. The classes live in list_results_binders.classify().

Usage: python3 scripts/audit_results_binder_forms.py [tree-root]
"""
import hashlib
import json
import os
import re
import sys

SKIP_DIRS = {".git", "results", "logs", "__pycache__", ".worktrees"}
SKIP_FILES = {"scripts/list_results_binders.py", "scripts/audit_results_binder_forms.py"}

# does this line build a path with "results" as a component?
PATHISH = re.compile(r'"[^"]*/results|results/[^"]*"|"results"|/ *"results"')
# ...or is it only a dict key / variable?
KEYISH = re.compile(r'\.get\(\s*"results"|\[\s*"results"\s*\]|"results"\s*:|\bresults\b\s*=\s*\[|'
                    r'sum\(results\)|len\(results\)|for \w+ in results\b|results\.append')

# verbatim from list_results_binders.py's PATTERN (the two forms the counter used to know)
COUNTER_PAT = re.compile(r'(?m)^\s*[A-Z_]*RESULTS\s*=\s*os\.path\.join\('
                         r'|os\.path\.join\((HERE|ARENA|os\.path\.dirname\(os\.path\.abspath\(__file__\)\)), "results"')


def find_rows(root):
    """-> [{"file", "line", "text", "counter_match"}] over `root`: every non-comment line that can
    build a `results` path. THE DETECTION, in one place, so the counter and this audit cannot
    disagree about what a binder is."""
    rows = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, root)
            if rel in SKIP_FILES:
                continue
            for i, ln in enumerate(open(p, encoding="utf-8", errors="replace").read().splitlines(), 1):
                s = ln.strip()
                if s.startswith("#") or not PATHISH.search(ln) or KEYISH.search(ln):
                    continue
                rows.append({"file": rel, "line": i, "text": s[:150],
                             "counter_match": bool(COUNTER_PAT.search(ln))})
    return rows


def counter_fixed():
    """-> the manifest's fixed_mechanism_files, read from the ONE declaration (never typed here)."""
    man_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "RESULTS_BINDERS_MANIFEST.json")
    raw = open(man_path, "rb").read()
    return {f["rel"] for f in json.loads(raw.decode("utf-8")).get("fixed_mechanism_files", [])}, \
        man_path, hashlib.sha256(raw).hexdigest()


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    rows = find_rows(root)
    counter_files = sorted({r["file"] for r in rows if r["counter_match"]})
    bind_files = sorted({r["file"] for r in rows})
    try:
        fixed, man_path, man_sha = counter_fixed()
    except OSError as e:                                          # noqa: BLE001
        raise SystemExit(f"STATE: BLOCKED. The manifest cannot be read: {e}")

    print(f"TREE {root}")
    print(f"  counter-matched .py files      : {len(counter_files)}")
    print(f"  files naming a results DIR     : {len(bind_files)}")
    print(f"  manifest                       : {man_path} sha256 {man_sha}")
    print()
    print("  B. BINDING LINES THE COUNTER DOES NOT MATCH:")
    for r in rows:
        if not r["counter_match"]:
            print(f"     {r['file']}:{r['line']}: {r['text']}")
    print()
    extra = sorted(f for f in set(bind_files) - set(counter_files) if f not in fixed)
    print("  C. FILES IN B BUT NOT IN THE COUNTER'S LIST (excluding the six it excludes by name):")
    for f in extra:
        print(f"     {f}")
    if not extra:
        print("     (none)")
    print()
    print("  D. OF THOSE, THE ONES THAT ARE *NOT* PROSE -- a real path, in a form the counter misses:")
    for r in rows:
        if r["file"] in extra and r["counter_match"] is False:
            print(f"     {r['file']}:{r['line']}: {r['text']}")
    print()
    print("  THE CLASSIFICATION IS NOT HERE. list_results_binders.classify() decides by DESTINATION")
    print("  (a worktree's own results/ -> record_binder; another named directory's -> "
          "named_write_destination), and this file's job is the DETECTION.")


if __name__ == "__main__":
    main()
