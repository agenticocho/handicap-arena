#!/usr/bin/env python3
"""PROBE -- THE FIELD CHECKER'S DRIVER-DIGEST CHECK: CAN IT TELL A CORRECT FIELD FROM A MUTATED RECORD?

MODEL-FREE BY CONSTRUCTION. No model file is read: ARENA_MODELS points at a path that does not exist, so the
entrant-identity check fails on all eleven measured records identically in EVERY run and that check is not
what this instrument reads. No lease, no server, no runner, no record and no artifact of the cabinet is
touched -- the shadow cabinets below are built in a temp directory OUTSIDE the tree.

WHAT IT MEASURES. Three shadow cabinets, each a copy of this cabinet's checker + probes + the three
documents it reads, differing ONLY in one record's `driver_digest`:

    M0  the field as published            22 records carry 4018f0262498eb3e
    M1  one record carries a digest that belongs to NO committed driver      deadbeefdeadbeef
    M2  one record carries a DIFFERENT committed driver than its 21 siblings  b726188380ce681c

C3-C5 are the discriminator, and they are written with the POST-FIX expectation, so they FAIL before the edit:
the pre-edit checker reports ONE driver failure in all three shadows, quoting the SET of digests and never the
coordinate, so a legitimate field is indistinguishable from two different mutations. After the edit it must
report the reading INCONCLUSIVE on M0, and NAME THE COORDINATE on M1 and M2.

C1 is the premise re-derived with this instrument's OWN git read (not the checker's -- an independent read of
the same fact), and C2 is the fact that makes the pre-move records unusable for this question at all.

    scripts/run_guarded.sh mc-driver-probe-pre <cabinet> /usr/bin/python3 scripts/probe_mc_driver_digest.py

Exit 0 = every check holds; 3 = at least one does not. Nothing here is a criterion, a verdict or a re-score.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CAB = os.path.dirname(HERE)
ARCHIVE = os.path.join(CAB, "probes", "MC_FIELD_EXAMPLE_ARM_ARCHIVE_20261017.json")
DRIVER = "missile_command_run.py"
RECORD_TO_MUTATE = "probes/MC_Qwen3-1.7B-Q8_0_mc_01_one_shot.json"
GARBAGE = "deadbeefdeadbeef"          # belongs to no committed driver, and never will
OLDER = "b726188380ce681c"            # a REAL committed driver -- the pre-move one
FIELD = "4018f0262498eb3e"            # what the 22 published records carry
LIVE = "3bd43eed4c6e41f3"             # missile_command_run.py on disk today

fails, checks = [], []


def ck(name, got, want):
    ok = got == want
    checks.append((name, ok, got, want))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"          got  {got!r}\n          want {want!r}")
        fails.append(name)
    return ok


def d16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def committed_driver_digests(repo):
    """THIS INSTRUMENT'S OWN READ OF THE DRIVER'S HISTORY -- independent of the checker's, on purpose: if both
    asked one function, a mistake in that function would be invisible to both."""
    shas = subprocess.run(["git", "-C", repo, "log", "--all", "--format=%H", "--", DRIVER],
                          capture_output=True, text=True, check=True).stdout.split()
    out = set()
    for sha in shas:
        blob = subprocess.run(["git", "-C", repo, "show", f"{sha}:{DRIVER}"],
                              capture_output=True, check=True).stdout
        out.add(hashlib.sha256(blob).hexdigest()[:16])
    return out


def shadow(mutate=None):
    """A cabinet copy that differs from this one in NOTHING but, when asked, one record's driver_digest."""
    root = tempfile.mkdtemp(prefix="mc-driver-shadow-")
    sh = os.path.join(root, "cab")
    os.makedirs(os.path.join(sh, "scripts"))
    os.makedirs(os.path.join(sh, "probes"))
    for name in (DRIVER, "missile_command.py", "MC_DECLARATION.md", "PREREG_mc_field_plain.md"):
        os.symlink(os.path.join(CAB, name), os.path.join(sh, name))
    shutil.copy2(os.path.join(HERE, "check_mc_field_plain.py"), os.path.join(sh, "scripts"))
    for name in sorted(os.listdir(os.path.join(CAB, "probes"))):
        if name.startswith("MC_") and name.endswith(".json"):
            shutil.copy2(os.path.join(CAB, "probes", name), os.path.join(sh, "probes", name))
    if mutate:
        digest, value = mutate
        p = os.path.join(sh, digest)
        d = json.load(open(p))
        d["driver_digest"] = value
        json.dump(d, open(p, "w"), indent=1)
    return root, sh


def run_checker(sh, root):
    env = dict(os.environ,
               MC_DRIVER_HISTORY_REPO=CAB,                      # the history lives in the repo, not the shadow
               ARENA_MODELS=os.path.join(root, "no-such-models"))  # no model read; the entrant check is inert
    p = subprocess.run([sys.executable, os.path.join(sh, "scripts", "check_mc_field_plain.py")],
                       cwd=sh, env=env, capture_output=True, text=True)
    out = p.stdout + p.stderr
    lines = out.splitlines()
    driver_fails = []
    for i, line in enumerate(lines):
        if line.startswith("  FAIL") and "driver" in line.lower():
            detail = lines[i + 1].strip() if i + 1 < len(lines) else ""
            driver_fails.append((line.strip(), detail))
    summary = [l for l in lines if "CHECKS FAILED" in l or "ALL CHECKS PASS" in l]
    m = re.search(r"(\d+)/(\d+)", summary[-1]) if summary else None
    got, total = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    return {"rc": p.returncode, "driver_fails": driver_fails, "got": got, "total": total,
            "out": out, "reading_inconclusive": "INCONCLUSIVE FROM THE RECORD'S SIDE" in out}


def main():
    print("=" * 100)
    print("PROBE -- THE CHECKER'S DRIVER-DIGEST CHECK, AGAINST THREE SHADOW CABINETS (card t_d68e29ba)")
    print("=" * 100)
    hist = committed_driver_digests(CAB)
    live = d16(os.path.join(CAB, DRIVER))
    art = json.load(open(ARCHIVE))
    archived_without = sum(1 for c in art["cells"] if "driver_digest" not in json.loads(c["text"]))
    print(f"\n  driver versions committed to git: {sorted(hist)}   ({len(hist)} versions)")
    print(f"  driver on disk: {live}   the 22 records carry: {FIELD}   the pre-move archive carries no "
          f"driver_digest in {archived_without}/{len(art['cells'])} cells")

    print("\n[1] THE PREMISE, RE-DERIVED WITH THIS INSTRUMENT'S OWN GIT READ")
    ck("the driver's history holds the three versions this card names, and the file on disk is the third",
       ({OLDER, FIELD, LIVE} <= hist, live), (True, LIVE))
    ck("...and NO pre-move record names a driver at all -- the archive cannot answer the question this card "
       "is about, which is why the history is the only tree-local source",
       archived_without, len(art["cells"]))

    print("\n[2] THREE SHADOW CABINETS, ONE RECORD DIFFERENT")
    runs = {}
    for tag, mutate in (("M0 [the field as published]", None),
                        ("M1 [one record: no committed driver]", (RECORD_TO_MUTATE, GARBAGE)),
                        ("M2 [one record: a DIFFERENT committed driver]", (RECORD_TO_MUTATE, OLDER))):
        root, sh = shadow(mutate)
        try:
            runs[tag] = run_checker(sh, root)
        finally:
            shutil.rmtree(root, ignore_errors=True)
        r = runs[tag]
        print(f"\n  {tag}   rc {r['rc']}   {r['got']}/{r['total']}   driver failures {len(r['driver_fails'])}")
        for head, detail in r["driver_fails"]:
            print(f"      {head}\n          {detail}")

    print("\n[3] THE DISCRIMINATOR -- CAN THE CHECK TELL A CORRECT FIELD FROM A MUTATION?")
    m0, m1, m2 = (runs[t] for t in ("M0 [the field as published]",
                                    "M1 [one record: no committed driver]",
                                    "M2 [one record: a DIFFERENT committed driver]"))
    ck("C3  M0, the field as published: NO driver check fails, and the reading says INCONCLUSIVE from the "
       "record's side (a legitimate field is not a failure)",
       (len(m0["driver_fails"]), m0["reading_inconclusive"]), (0, True))
    ck("C4  M1, a digest belonging to no committed driver: TWO driver checks fail and BOTH name the "
       "coordinate and the value",
       [(RECORD_TO_MUTATE in h, GARBAGE in (h + " " + d)) for h, d in m1["driver_fails"]],
       [(True, True), (True, True)])
    ck("C5  M2, a record that disagrees with its 21 siblings: ONE driver check fails and it names the "
       "coordinate",
       [(RECORD_TO_MUTATE in h, OLDER in (h + " " + d)) for h, d in m2["driver_fails"]],
       [(True, True)])
    ck("C6  the totals, stated honestly: 115 checks in all three runs, and the driver failure count is the "
       "ONLY thing that differs -- 2/4/3 failures overall, the two known findings plus 0/2/1 driver failures",
       [(r["total"], r["got"], len(r["driver_fails"])) for r in (m0, m1, m2)],
       [(115, 113, 0), (115, 111, 2), (115, 112, 1)])

    print("\n[4] NOTHING OF THE CABINET'S WAS TOUCHED")
    porcelain = subprocess.run(["git", "-C", CAB, "status", "--porcelain", "probes/", "results/"],
                               capture_output=True, text=True).stdout.strip()
    ck("C7  git status --porcelain probes/ results/ is empty after all three runs (the shadows live in a temp "
       "directory, outside the tree)", porcelain, "")

    print("\n" + "=" * 100)
    print(f"{'ALL CHECKS PASS' if not fails else str(len(fails)) + ' CHECKS FAILED'}   --  "
          f"{len(checks) - len(fails)}/{len(checks)}")
    print("=" * 100)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
