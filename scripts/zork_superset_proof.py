#!/usr/bin/env python3
"""zork_superset_proof.py -- RE-RUN THE PROOF BEHIND PREREG AMENDMENT Z1 (2026-10-26).

WHAT IT PROVES. That the 175-control simulator is a SUPERSET of the 114-control one the prereg froze at
`4e0eb43`: that every one of the frozen 114 control names still exists and still prints, that nothing was
removed, and -- one level deeper than a name count -- that every `ck(name, got, want)` CALL SITE in the
frozen file is present in the current one with the same name template and the same compared expressions.

WHY A COUNT IS NOT ENOUGH: 175 - 114 = 61 cannot distinguish "grew by 61" from "grew by 71 and lost 10".
A number is not a membership test. This prints the names, both ways, and the difference.

WHY A NAME IS NOT ENOUGH EITHER: a control can keep its name and have what it compares weakened. The
call-site pass compares the assertion source text, with looped and f-string names matched as templates,
and reports any frozen site whose multiplicity changed (a control that survives but fires fewer times).

WHAT IT DOES NOT PROVE, and says so in its own output: that the thing a kept control measures did not
change underneath it. `parse_command`'s contract DID change in `6c426e5`. The 175/175 run is evidence
that the kept controls still bite; it is not proof that they bite the same object.

    python3 scripts/zork_superset_proof.py              # default: 4e0eb43 -> HEAD
    python3 scripts/zork_superset_proof.py OLDREV NEWREV

Read-only: it does `git show` into a temp dir, symlinks the repo's own `levels/` in, and runs each
revision's `--self-test`. It writes nothing into the repo and touches no model, port or GPU.
"""
import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = sys.argv[1] if len(sys.argv) > 1 else "4e0eb43"
NEW = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
LINE = re.compile(r"^  (PASS|FAIL)  (.*)$")


def git(*args):
    return subprocess.run(("git",) + args, cwd=HERE, capture_output=True, text=True)


def source_at(rev):
    r = git("show", f"{rev}:zork.py")
    if r.returncode:
        sys.exit(f"REFUSED: {rev}:zork.py is not in this repository: {r.stderr.strip()}")
    return r.stdout


def self_test_names(rev, tmp):
    """Run THAT revision's zork.py --self-test against this repo's levels and return its printed names."""
    d = os.path.join(tmp, rev.replace("/", "_"))
    os.makedirs(d, exist_ok=True)
    src = source_at(rev)
    with open(os.path.join(d, "zork.py"), "w", encoding="utf-8") as fh:
        fh.write(src)
    link = os.path.join(d, "levels")
    if not os.path.exists(link):
        os.symlink(os.path.join(HERE, "levels"), link)
    r = subprocess.run([sys.executable, "zork.py", "--self-test"], cwd=d,
                       capture_output=True, text=True)
    names, fails = [], []
    for raw in r.stdout.splitlines():
        m = LINE.match(raw)
        if m:
            (names if m.group(1) == "PASS" else fails).append(m.group(2).strip())
    footer = [ln.strip() for ln in r.stdout.splitlines() if "ALL CONTROLS PASS" in ln or "FAILED" in ln]
    return names, fails, r.returncode, footer[-1] if footer else "?", hashlib.sha256(
        src.encode()).hexdigest()


def call_sites(src):
    """(name-template, got-source, want-source) for every ck(...) call site -- f-strings as templates."""
    sites = Counter()
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ck"):
            continue
        if not node.args:
            continue
        a0 = node.args[0]
        name = a0.value if (isinstance(a0, ast.Constant) and isinstance(a0.value, str)) \
            else "<dynamic>" + ast.unparse(a0)
        got = ast.unparse(node.args[1]) if len(node.args) > 1 else "<none>"
        want = ast.unparse(node.args[2]) if len(node.args) > 2 else "<none>"
        sites[(name, got, want)] += 1
    return sites


def main():
    tmp = tempfile.mkdtemp(prefix="zork_superset_proof_")
    try:
        old_names, old_fail, old_rc, old_footer, old_sha = self_test_names(OLD, tmp)
        new_names, new_fail, new_rc, new_footer, new_sha = self_test_names(NEW, tmp)

        print("=" * 100)
        print(f"NAME-LEVEL SUPERSET PROOF -- zork.py --self-test, {OLD} vs {NEW}")
        print("=" * 100)
        print(f"{OLD:<12} sha256 {old_sha[:16]}…  {len(old_names)} PASS, {len(old_fail)} FAIL, "
              f"exit {old_rc}   {old_footer}")
        print(f"{NEW:<12} sha256 {new_sha[:16]}…  {len(new_names)} PASS, {len(new_fail)} FAIL, "
              f"exit {new_rc}   {new_footer}")
        if old_fail or new_fail:
            print(f"\nREFUSED: a control FAILED in one of the revisions ({len(old_fail)} old, "
                  f"{len(new_fail)} new). A proof over a red instrument proves nothing. Fix it first.")
            return 1

        A, B = set(old_names), set(new_names)
        removed, added = sorted(A - B), sorted(B - A)
        dup_old = [n for n, k in Counter(old_names).items() if k > 1]
        dup_new = [n for n, k in Counter(new_names).items() if k > 1]
        print(f"\nduplicate names: {len(dup_old)} in {OLD}, {len(dup_new)} in {NEW}")

        print("\n" + "-" * 100)
        print(f"SET A -- THE {len(A)} NAMES IN {OLD}")
        print("-" * 100)
        for i, n in enumerate(sorted(A), 1):
            print(f"{i:>4}  {n}")

        print("\n" + "-" * 100)
        print(f"SET B \\ A -- THE {len(added)} NAMES ADDED (the whole of B is A ∪ this list)")
        print("-" * 100)
        for i, n in enumerate(added, 1):
            print(f"{i:>4}  + {n}")

        print("\n" + "=" * 100)
        print("THE DIFFERENCE")
        print("=" * 100)
        print(f"kept A ∩ B : {len(A & B)}\nadded B \\ A: {len(added)}\nremoved A \\ B: {len(removed)}")
        print()
        if removed:
            print("removed: NOT NONE -- THE FOLLOWING NAMES WENT:")
            for n in removed:
                print(f"  - {n}")
        else:
            print("removed: none")
        print()
        print(f"ARITHMETIC  {len(A & B)} kept + {len(added)} added = {len(A & B) + len(added)}"
              f"  == {len(B)}? {len(A & B) + len(added) == len(B)}")
        print(f"            {len(A & B)} kept + {len(removed)} removed = {len(A & B) + len(removed)}"
              f"  == {len(A)}? {len(A & B) + len(removed) == len(A)}")
        if dup_old or dup_new:
            print("\nREFUSED: duplicate names present; a set difference over repeats is the wrong difference.")
            return 1

        print("\n" + "=" * 100)
        print("ONE LEVEL DEEPER -- THE CALL SITES, BECAUSE A NAME IS NOT AN ASSERTION")
        print("=" * 100)
        F, H = call_sites(source_at(OLD)), call_sites(source_at(NEW))
        missing, extra = F - H, H - F
        print(f"call sites: {sum(F.values())} in {OLD}, {sum(H.values())} in {NEW}")
        print(f"frozen sites absent from {NEW} (name template + compared expressions as a unit): "
              f"{sum(missing.values())}")
        print(f"sites whose multiplicity changed: {sum(1 for s, k in F.items() if H.get(s, 0) != k)}")
        if missing:
            print("\nTHE FOLLOWING FROZEN CALL SITES DID NOT SURVIVE VERBATIM -- READ EVERY ONE:")
            for (name, got, want), k in missing.items():
                print(f"  x{k}  NAME: {name}\n        got : {got}\n        want: {want}")
            return 1
        print("\nremoved: none -- at name level and at call-site level.")
        print(f"\nWHAT THIS DOES NOT PROVE: that the thing a kept control measures did not change underneath it.")
        print(f"The {len(new_names)}/{len(new_names)} run is evidence the kept controls still bite; it is not")
        print(f"proof they bite the same object.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
