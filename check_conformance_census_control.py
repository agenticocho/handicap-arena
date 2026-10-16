#!/usr/bin/env python3
"""THE CONTROL FOR `check_conformance_census.py` -- A CHECK THAT CANNOT FAIL IS A RESOLUTION, NOT A MECHANISM.

That sentence is the finding the enforcer exists to answer, so the enforcer is held to it. Four arms, all on
COPIES in a scratch directory -- nothing in the repo is touched, and the arms are run against the same check the
repo runs:

  A  a name INJECTED into the package's §2 CELL RECORD block   -> rc 1, and the name printed under DIRECTION 2
  B  `final_board` RENAMED in `sokoban.py`'s `play()` literal   -> rc 1, the new name under DIRECTION 1 and
                                                                  `final_board` under DIRECTION 2
  C  BOTH COPIES UNMUTATED                                      -> rc 0
  D  the DEAD-END CELL header REMOVED from the package          -> rc 2, and the miss printed

**C IS THE CONTROL'S OWN CONTROL, AND IT IS THE ONE THAT MATTERS.** Without it, a check that fails on everything
would look exactly like a check that catches everything; with it, the failure in A and B is shown to be caused by
the mutation rather than by the copy, the temp directory, or the phase of the moon.

    python3 check_conformance_census_control.py

rc 0  every arm behaved as pre-registered (the check is a mechanism)
rc 1  an arm did not behave as pre-registered (the check is a resolution)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "check_conformance_census.py")
INJECTED = "conformance_probe_injected_20261016"
RENAMED = "loose_match_diagnostic_only_never_scored_by_control"
CARRIED = ("sokoban.py", "sokoban_run.py", "sokoban_batch.py",
           "make_conformance_package.py", "SOKOBAN_CONFORMANCE_PACKAGE.md")


def stage(dst):
    """A COPY of every file the check reads. A copy, so an arm cannot damage the tree it is checking."""
    os.makedirs(dst, exist_ok=True)
    for f in CARRIED:
        shutil.copy2(os.path.join(HERE, f), os.path.join(dst, f))
    return dst


def run(root):
    p = subprocess.run([sys.executable, CHECK, "--root", root], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def swap(path, old, new):
    """-> True if the text was there EXACTLY ONCE. A mutation that landed zero times, or twice, is a control
    that proves nothing, and reporting it as a pass is how a control becomes decoration."""
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        return False, n
    open(path, "w", encoding="utf-8").write(text.replace(old, new))
    return True, n


def main():
    arms = []
    with tempfile.TemporaryDirectory(prefix="census_control_") as tmp:
        # ---------------- C FIRST: THE UNMUTATED COPIES MUST PASS.
        clean = stage(os.path.join(tmp, "clean"))
        rc_c, out_c = run(clean)
        arms.append(("C  unmutated copies pass", rc_c == 0,
                     f"rc={rc_c} (expected 0)"))

        # ---------------- A: a name injected into the package.
        a = stage(os.path.join(tmp, "injected"))
        ok, n = swap(os.path.join(a, "SOKOBAN_CONFORMANCE_PACKAGE.md"),
                     "never_started  config  reasoning_probe",
                     f"never_started  {INJECTED}  config  reasoning_probe")
        rc_a, out_a = run(a)
        after_d2 = out_a.split("DIRECTION 2")[-1] if "DIRECTION 2" in out_a else ""
        named_a = INJECTED in after_d2
        arms.append(("A  an injected package name fails, and is NAMED", ok and rc_a == 1 and named_a,
                     f"mutation applied={ok} (matches={n}), rc={rc_a} (expected 1), "
                     f"named under DIRECTION 2={named_a}"))

        # ---------------- B: a name removed from the writer.
        # THE KEY IS DELIBERATELY NOT ONE THIS CHECK IDENTIFIES A LITERAL BY. The first cut of this arm renamed
        # `final_board`, which IS such a key -- so the site vanished and the check correctly reported a MISS
        # (rc 2) while the arm expected DRIFT (rc 1). The arm was wrong, not the check, and the MISS case is
        # arm E, kept separately so the two failures cannot be confused for one another again.
        b = stage(os.path.join(tmp, "renamed"))
        ok, n = swap(os.path.join(b, "sokoban.py"),
                     '"loose_match_diagnostic_only_never_scored": loose_match_diagnostic_only,',
                     f'"{RENAMED}": loose_match_diagnostic_only,')
        rc_b, out_b = run(b)
        after_d1 = out_b.split("DIRECTION 1")[-1].split("DIRECTION 2")[0] if "DIRECTION 1" in out_b else ""
        after_d2b = out_b.split("DIRECTION 2")[-1] if "DIRECTION 2" in out_b else ""
        arms.append(("B  a renamed writer key fails, both directions",
                     ok and rc_b == 1 and RENAMED in after_d1
                     and "loose_match_diagnostic_only_never_scored" in after_d2b,
                     f"mutation applied={ok} (matches={n}), rc={rc_b} (expected 1), new name under "
                     f"DIRECTION 1={RENAMED in after_d1}, old name under "
                     f"DIRECTION 2={'loose_match_diagnostic_only_never_scored' in after_d2b}"))

        # ---------------- D: a declared block that cannot be read is a MISS, not a pass.
        d = stage(os.path.join(tmp, "noheader"))
        ok, n = swap(os.path.join(d, "SOKOBAN_CONFORMANCE_PACKAGE.md"),
                     "**DEAD-END CELL — `sokoban_run.py`, `dead_end_verdict()`**",
                     "DEAD-END CELL (header deleted by the control)")
        rc_d, out_d = run(d)
        arms.append(("D  a missing census header is a MISS (rc 2)", ok and rc_d == 2 and "DEAD-END CELL" in out_d,
                     f"mutation applied={ok} (matches={n}), rc={rc_d} (expected 2)"))

        # ---------------- E: a literal this check FINDS only by its keys, with one of those keys renamed.
        e = stage(os.path.join(tmp, "nofingerprint"))
        ok, n = swap(os.path.join(e, "sokoban.py"),
                     '"final_board": render(st), "trace": trace}',
                     '"final_board_by_control": render(st), "trace": trace}')
        rc_e, out_e = run(e)
        arms.append(("E  a literal the check cannot find is a MISS (rc 2)", ok and rc_e == 2
                     and "CELL COUNTERS" in out_e,
                     f"mutation applied={ok} (matches={n}), rc={rc_e} (expected 2: the site is gone, and a "
                     f"reader that cannot find a literal must not report fewer names as a pass)"))

    print("=" * 100)
    print("THE CONTROL -- DOES THE CENSUS CHECK FAIL WHERE IT MUST, AND PASS WHERE IT MUST?")
    print("=" * 100)
    bad = 0
    for what, good, detail in arms:
        print(f"  {'OK  ' if good else 'FAIL'}  {what}")
        print(f"        {detail}")
        bad += 0 if good else 1
    print()
    print("=" * 100)
    if bad:
        print(f"  *** {bad} ARM(S) DID NOT BEHAVE AS PRE-REGISTERED. THE CHECK IS A RESOLUTION UNTIL THEY DO. ***")
        return 1
    print("  ALL FIVE ARMS AS PRE-REGISTERED: the check fails on an injected package name and on a renamed")
    print("  writer key, passes on the unmutated copies, and reports a missing declared block (and a literal it")
    print("  can no longer find) as a MISS. The failure is therefore CAUSED BY THE MUTATION and not by the")
    print("  copy, the directory, or the run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
