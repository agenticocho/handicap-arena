#!/usr/bin/env python3
"""DOES ANY ROW CLAIM AN INSTRUMENT THAT DID NOT MEASURE IT?

The defect R2 of the 2026-10-26 ruling exists to prevent: a row that NAMES one instrument while
CARRYING a measurement taken with another. This checks that directly, without trusting either the
row's prose or the card that reported it.

HOW THE TWO GENERATIONS ARE TOLD APART, measured from the zork.py blobs rather than assumed:

    git show fa2011f:zork.py | grep -c attribution   -> 0     (4e0eb43:zork.py is byte-identical)
    git show 6c426e5:zork.py | grep -c attribution   -> 33

`attribution`, `attribution_of`, `attribution_reasons` and `progress_field_source` are emitted only by
the 2026-10-26 instrument, so a row CARRYING them cannot have been produced by the older one. The
digests themselves are recomputed from git blobs here, never typed in.

    python3 check_row_generation.py --self-test
    python3 check_row_generation.py
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MARKERS = ("attribution", "attribution_of", "attribution_reasons", "progress_field_source")


def sh(*args):
    return subprocess.run(args, cwd=HERE, capture_output=True, check=True).stdout


def known_instruments():
    """{first16 sha256: (commit, bytes)} over every distinct zork.py that ever existed in this repo."""
    out = {}
    for h in sh("git", "log", "--format=%H", "--", "zork.py").decode().split():
        blob = sh("git", "show", "%s:zork.py" % h)
        d = hashlib.sha256(blob).hexdigest()[:16]
        out.setdefault(d, (h[:7], len(blob)))
    return out


def rows():
    found = []
    for d in ("probes", "suite2", "suite3"):
        for p in glob.glob(os.path.join(HERE, d, "**", "ZORK_*.json"), recursive=True):
            if not p.endswith(".provenance.json"):
                found.append(p)
    return sorted(set(found))


def generation(d):
    return "2026-10-26" if any(m in d for m in MARKERS) else "2026-10-25"


def check(paths, instruments):
    findings, table = [], []
    for p in paths:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as exc:
            findings.append("%s: unparseable (%s)" % (os.path.basename(p), exc))
            continue
        claim, gen = d.get("simulator_digest"), generation(d)
        base = os.path.relpath(p, HERE)
        if claim is None:
            findings.append("%s: carries no simulator_digest" % base)
            table.append(("FAIL", "-", gen, base))
            continue
        if claim not in instruments:
            findings.append("%s: claims `%s`, which is not a zork.py this repo ever held" % (base, claim))
            table.append(("FAIL", claim, gen, base))
        # THE PAIRING: the 2026-10-26 instrument is the only one that emits the marker fields.
        want = "2026-10-26" if claim != "ff35ec83b340fbf0" else "2026-10-25"
        ok = gen == want
        table.append(("PASS" if ok else "FAIL", claim, gen, base))
        if not ok:
            findings.append("%s: NAMES %s but CARRIES the %s measurement -- the instrument did not "
                            "measure this row" % (base, claim, gen))
    return findings, table


def show(found, table, instruments):
    print("  instruments this repo has held for zork.py: %s"
          % ", ".join("%s(%s B from %s)" % (k, v[1], v[0]) for k, v in sorted(instruments.items())))
    print("  rows in scope: %d\n" % len(table))
    print("  %-5s %-18s %-12s %s" % ("", "claims", "carries", "row"))
    for status, claim, gen, base in table:
        print("  %-5s %-18s %-12s %s" % (status, claim, gen, base))
    print()
    for f in found:
        print("  FAIL  " + f)
    print("  %s  %d row(s): %d claiming an instrument that did not measure them"
          % ("OK  " if not found else "RED", len(table), len(found)))


def _self_test():
    instruments = known_instruments()
    live = rows()
    print("[0] SCOPE AND THE INSTRUMENTS, RECOMPUTED FROM GIT (never typed in)")
    if len(instruments) < 2:
        print("  FAIL  fewer than two zork.py revisions in history -- the pairing test would be vacuous")
        return 1
    print("  PASS  %d distinct instrument(s) recomputed from blobs" % len(instruments))
    if not live:
        print("  FAIL  no rows in scope")
        return 1
    print("  PASS  %d row(s) in scope" % len(live))

    print("\n[1] EVERY COMMITTED ROW: the digest it names is the instrument that produced it")
    found, table = check(live, instruments)
    show(found, table, instruments)

    old = "ff35ec83b340fbf0"
    new = [k for k in instruments if k != old][0]
    scratch = tempfile.mkdtemp(prefix="row_gen_")
    try:
        good = json.load(open(live[0], encoding="utf-8"))
        cases = [
            ("new content, OLD digest  (the R2 defect)", dict(good, simulator_digest=old), False),
            ("new content, NEW digest  (honest)", dict(good, simulator_digest=new), True),
            ("new content, digest of a file this repo never held",
             dict(good, simulator_digest="0123456789abcdef"), False),
        ]
        results = []
        print("\n[2] THE CONTROL FIRES IN BOTH DIRECTIONS")
        for i, (label, payload, should_pass) in enumerate(cases):
            p = os.path.join(scratch, "case%d.json" % i)
            json.dump(payload, open(p, "w", encoding="utf-8"))
            f, _t = check([p], instruments)
            passed = not f
            ok = passed == should_pass
            results.append(ok)
            print("  %s  %-52s -> %s" % ("PASS" if ok else "FAIL", label,
                                         "accepted" if passed else "refused"))
            if not should_pass and f:
                print("        %s" % f[0])
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    checks = [not found, all(results)]
    nfail = sum(1 for c in checks if not c)
    print("\n" + "=" * 100)
    print("%d FAILED   --   %d/%d" % (nfail, len(checks) - nfail, len(checks)))
    print("=" * 100)
    return 1 if nfail else 0


def main(argv):
    instruments = known_instruments()
    if "--self-test" in argv:
        return _self_test()
    paths = [a for a in argv[1:] if not a.startswith("-")] or rows()
    found, table = check(paths, instruments)
    show(found, table, instruments)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
