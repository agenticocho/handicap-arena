#!/usr/bin/env python3
"""Mutation control for lightsout_cabinet.py -- a cabinet that cannot fail is a resolution.

Four arms, all on COPIES in scratch.  The cabinet's load_boards() must raise on
each mutated copy (non-zero exit) and pass on the unmutated copy.

  A  board id mutated (idx 1 -> 99)            -> non-zero
  B  `correct` field mutated (A1 -> B2)        -> non-zero   (historically survived)
  C  prose answer cell mutated (A1 -> C3)      -> non-zero   (historically survived)
  D  whole-file substitution (empty json)      -> non-zero
  E  unmutated copies pass                    -> zero  (the control's own control)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CAB = os.path.join(HERE, "lightsout_cabinet.py")
JSON_SRC = os.path.join(HERE, "probes", "lightsout", "3x3_fixture_16_boards_20261022.json")
MD_SRC = os.path.join(HERE, "probes", "lightsout", "3x3_fixture_16_boards_20261022.md")


def stage(dst):
    os.makedirs(dst, exist_ok=True)
    jdst = os.path.join(dst, "fixture.json")
    mdst = os.path.join(dst, "fixture.md")
    shutil.copy2(JSON_SRC, jdst)
    shutil.copy2(MD_SRC, mdst)
    return jdst, mdst


def run(json_path, md_path=None):
    cmd = [sys.executable, CAB, "--json", json_path]
    if md_path:
        cmd += ["--md", md_path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def swap_json(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        return False, n
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
    return True, n


def swap_text(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n < 1:
        return False, n
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
    return True, n


def main():
    arms = []
    with tempfile.TemporaryDirectory(prefix="lightsout_control_") as tmp:
        # E first: unmutated copies must pass
        j, m = stage(os.path.join(tmp, "clean"))
        rc, out = run(j, m)
        arms.append(("E  unmutated copies pass", rc == 0, "rc=%d (expected 0)" % rc))

        # A: board id mutated
        j, m = stage(os.path.join(tmp, "boardid"))
        ok, n = swap_json(j, '"idx": 1,', '"idx": 99,')
        rc, out = run(j, m)
        arms.append(("A  board id mutation refused", ok and rc != 0,
                     "mutation applied=%s (matches=%d), rc=%d (expected !=0)" % (ok, n, rc)))

        # B: correct field mutated A1 -> B2 (historically survived)
        j, m = stage(os.path.join(tmp, "correct"))
        ok, n = swap_json(j, '"correct": "A1"', '"correct": "B2"')
        rc, out = run(j, m)
        arms.append(("B  correct field A1->B2 refused", ok and rc != 0,
                     "mutation applied=%s (matches=%d), rc=%d (expected !=0)" % (ok, n, rc)))

        # C: prose answer cell mutated A1 -> C3 (historically survived)
        j, m = stage(os.path.join(tmp, "prose"))
        # mutate the first prose answer cell "correct string: `A1`" -> "C3"
        ok, n = swap_text(m, "correct string: `A1`", "correct string: `C3`")
        rc, out = run(j, m)
        arms.append(("C  prose answer cell A1->C3 refused", ok and rc != 0,
                     "mutation applied=%s (matches=%d), rc=%d (expected !=0)" % (ok, n, rc)))

        # D: whole-file substitution
        j, m = stage(os.path.join(tmp, "wholefile"))
        with open(j, "w", encoding="utf-8") as fh:
            fh.write("[]")
        rc, out = run(j, m)
        arms.append(("D  whole-file substitution refused", rc != 0,
                     "rc=%d (expected !=0)" % rc))

    print("=" * 100)
    print("LIGHTS OUT CABINET MUTATION CONTROL")
    print("=" * 100)
    bad = 0
    for what, good, detail in arms:
        print("  " + ("OK  " if good else "FAIL") + "  " + what)
        print("        " + detail)
        bad += 0 if good else 1
    print()
    print("=" * 100)
    if bad:
        print("  *** %d ARM(S) DID NOT BEHAVE AS PRE-REGISTERED. ***" % bad)
        return 1
    print("  ALL FIVE ARMS AS PRE-REGISTERED: unmutated passes; board-id, correct-field,")
    print("  prose-cell and whole-file mutations are all refused with non-zero exit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
