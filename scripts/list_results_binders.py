#!/usr/bin/env python3
"""Measured list: which scripts still bind a <worktree>/results DIRECTORY.

Run from the repo root of a worktree. Writes the list to the scratch dir for the record.
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PAT = re.compile(r'(?m)^\s*[A-Z_]*RESULTS\s*=\s*os\.path\.join\('
                 r'|os\.path\.join\((HERE|ARENA|os\.path\.dirname\(os\.path\.abspath\(__file__\)\)), "results"')
FIXED = {"cabinet_root.py", "run_card.py", "test_game_states.py",
         "reconcile_and_backfill.py", "test_bind_control.py", "test_declared_root.py"}

rows = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in (".git", "results", "logs", "__pycache__", ".worktrees")]
    for f in sorted(files):
        if not f.endswith(".py"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, ROOT)
        if rel in FIXED:
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        hits = [i + 1 for i, ln in enumerate(txt.splitlines()) if PAT.search(ln)]
        if hits:
            rows.append((rel, hits))

print(f"{len(rows)} files still bind a <worktree>/results directory "
      f"(outside the {len(FIXED)} this change fixes):")
for p, h in rows:
    print(f"  {p:46} lines {h}")
out = "/home/chilly1/.hermes/profiles/ocho/cache/scratch/remaining_results_binders.txt"
with open(out, "w", encoding="utf-8") as fh:
    fh.write(f"measured in {os.path.abspath(ROOT)} on the working tree\n")
    for p, h in rows:
        fh.write(f"{p}\t{h}\n")
print(f"\nwritten to {out}")
