#!/usr/bin/env python3
"""INDEPENDENT FORM AUDIT of scripts/list_results_binders.py.

WHY THIS EXISTS. `list_results_binders.py` matches TWO syntactic forms:

    ^\\s*[A-Z_]*RESULTS\\s*=\\s*os\\.path\\.join\\(
    os\\.path\\.join\\((HERE|ARENA|os\\.path\\.dirname\\(os\\.path\\.abspath\\(__file__\\)\\)), \"results\"

Its COUNT is exact for its PATTERN, and its pattern is narrower than its own headline
("scripts that bind a <worktree>/results directory"). This walks every .py file and reports
every line that can produce a path whose last component is the literal directory name
"results", in ANY form -- os.path.join with any first argument, an absolute literal, a
f-string, a / division -- then splits them into:

  A. lines the counter DOES match                 (sanity: same files?)
  B. lines that name a `results` directory the counter does NOT match   <- the blind spots
  C. files that appear in B and are not in the counter's list

A line whose only mention of "results" is a DICT KEY (d.get("results"), d["results"], a
"results": [...] literal) is NOT a path and is filtered out. Comment lines are skipped.
This script and list_results_binders.py are skipped about themselves: a counter's own
pattern text is not a binding.

Usage: python3 scripts/audit_results_binder_forms.py [tree-root]
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SKIP_DIRS = {".git", "results", "logs", "__pycache__", ".worktrees"}
SKIP_FILES = {"scripts/list_results_binders.py", "scripts/audit_results_binder_forms.py"}
# THE COUNTER'S EXCLUSION LIST IS NOW A DECLARED MANIFEST, AND THIS READER READS THE SAME
# DECLARATION rather than keeping a second copy of it: two readers of one declaration, or two
# lists that drift. The six paths below are no longer typed here -- they are read from
# RESULTS_BINDERS_MANIFEST.json's fixed_mechanism_files. Column C means "the counter does not list
# this AND the manifest does not exclude it".
MANIFEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "RESULTS_BINDERS_MANIFEST.json")
try:
    _RAW = open(MANIFEST, "rb").read()
    _MAN = json.loads(_RAW.decode("utf-8"))
except OSError as _e:                                            # noqa: BLE001
    raise SystemExit(f"STATE: BLOCKED. The manifest cannot be read: {_e}")
MANIFEST_SHA = hashlib.sha256(_RAW).hexdigest()
COUNTER_FIXED = {f["rel"] for f in _MAN.get("fixed_mechanism_files", [])}

# verbatim from list_results_binders.py
COUNTER_PAT = re.compile(r'(?m)^\s*[A-Z_]*RESULTS\s*=\s*os\.path\.join\('
                         r'|os\.path\.join\((HERE|ARENA|os\.path\.dirname\(os\.path\.abspath\(__file__\)\)), "results"')

# does this line build a path with "results" as a component?
PATHISH = re.compile(r'"[^"]*/results|results/[^"]*"|"results"|/ *"results"')
# ...or is it only a dict key / variable?
KEYISH = re.compile(r'\.get\(\s*"results"|\[\s*"results"\s*\]|"results"\s*:|\bresults\b\s*=\s*\[|'
                    r'sum\(results\)|len\(results\)|for \w+ in results\b|results\.append')

rows = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in sorted(files):
        if not f.endswith(".py"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, ROOT)
        if rel in SKIP_FILES:
            continue
        for i, ln in enumerate(open(p, encoding="utf-8", errors="replace").read().splitlines(), 1):
            s = ln.strip()
            if s.startswith("#") or not PATHISH.search(ln) or KEYISH.search(ln):
                continue
            rows.append({"file": rel, "line": i, "text": s[:150],
                         "counter_match": bool(COUNTER_PAT.search(ln))})

counter_files = sorted({r["file"] for r in rows if r["counter_match"]})
bind_files = sorted({r["file"] for r in rows})

print(f"TREE {ROOT}")
print(f"  counter-matched .py files      : {len(counter_files)}")
print(f"  files naming a results DIR     : {len(bind_files)}")
print(f"  manifest                       : {MANIFEST} sha256 {MANIFEST_SHA}")
print()
print("  B. BINDING LINES THE COUNTER DOES NOT MATCH:")
for r in rows:
    if not r["counter_match"]:
        print(f"     {r['file']}:{r['line']}: {r['text']}")
print()
extra = sorted(f for f in set(bind_files) - set(counter_files) if f not in COUNTER_FIXED)
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
