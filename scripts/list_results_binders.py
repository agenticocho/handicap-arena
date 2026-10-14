#!/usr/bin/env python3
"""Measured list: which scripts still bind a <worktree>/results DIRECTORY.

THE FIXED SET IS GONE. This file used to carry a hardcoded `FIXED = {...}` of the six files the
declaration is allowed to mention; that is now a DECLARED MANIFEST (RESULTS_BINDERS_MANIFEST.json),
read here. An exclusion can HIDE a binder; a declaration cannot -- every binder in the tree is
either in the manifest with a status or reported as UNDECLARED.

RESIDUE ZERO IS A NUMBER THE TOOL EXITS ON, not a number a reader eyeballs: the exit code is
non-zero while N > 0.

usage:   python3 scripts/list_results_binders.py [tree] [--manifest PATH]
         (default tree `.`, default manifest <repo>/RESULTS_BINDERS_MANIFEST.json)
exit:    0 when nothing in the tree still binds <worktree>/results
         1 while N > 0        (the residue)
         2 if the tree names a binder the manifest does not declare
"""
import argparse
import hashlib
import json
import os
import re
import sys

# THE DETECTION IS A FUNCTION, NOT A SCRIPT BODY, so the guard that checks the manifest can RE-USE
# it (test_declared_root.py section 8 loads find_binders from here) instead of copying the pattern
# -- a copy drifts from the thing it copied.
PAT = re.compile(r'(?m)^\s*[A-Z_]*RESULTS\s*=\s*os\.path\.join\('
                 r'|os\.path\.join\((HERE|ARENA|os\.path\.dirname\(os\.path\.abspath\(__file__\)\)), "results"')
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MANIFEST = os.path.join(os.path.dirname(HERE), "RESULTS_BINDERS_MANIFEST.json")
SKIP_FILES = {"scripts/list_results_binders.py", "scripts/audit_results_binder_forms.py"}


def find_binders(root):
    """-> [(rel, [lines])] for every .py under `root` that still binds a <worktree>/results dir.

    The tree walk and the pattern, in one place. `root` is a path, so the same call measures any
    worktree -- which is how one copy of this instrument serves all four trees.
    """
    rows = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "results", "logs", "__pycache__", ".worktrees")]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, root)
            if rel in SKIP_FILES:
                continue
            txt = open(p, encoding="utf-8", errors="replace").read()
            hits = [i + 1 for i, ln in enumerate(txt.splitlines()) if PAT.search(ln)]
            if hits:
                rows.append((rel, hits))
    return rows


def load_manifest(path):
    """-> (manifest, sha256 of the BYTES read). The number's instrument travels with the number."""
    raw = open(path, "rb").read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="which scripts still bind <worktree>/results")
    ap.add_argument("tree", nargs="?", default=".")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    a = ap.parse_args()
    root = os.path.abspath(a.tree)
    try:
        man, msha = load_manifest(a.manifest)
    except OSError as e:
        print(f"STATE: BLOCKED. The manifest cannot be read: {e}")
        print(f"  the counter no longer carries an exclusion list of its own -- without the "
              f"declaration there is nothing to measure against.")
        return 2
    entries = {e["script"]: e for e in man.get("entries", [])}
    fixed = {f["rel"] for f in man.get("fixed_mechanism_files", [])}
    rows, undeclared = [], []
    for rel, hits in find_binders(root):
        if rel in fixed:
            continue
        e = entries.get(rel)
        if e is None:
            undeclared.append(rel)
            cls = "UNDECLARED"
        else:
            cls = " + ".join(ed["status"] for ed in e["edges"])
        rows.append((rel, hits, cls))
    print(f"{len(rows)} results-record binders still bind <worktree>/results in {root}")
    for rel, h, cls in rows:
        print(f"  {rel:46} lines {h}  [{cls}]")
    print(f"manifest {os.path.abspath(a.manifest)} sha256 {msha}")
    if undeclared:
        print(f"UNDECLARED: {len(undeclared)} binder(s) the manifest does not carry: {undeclared}")
        print("STATE: BLOCKED. A binder that is not declared is a binder nobody has decided about.")
        return 2
    return 1 if rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
