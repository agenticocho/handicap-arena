#!/usr/bin/env python3
"""FORMAT.md section 10, AS A CHECK -- measured at the event vs current state.

WHY THIS EXISTS. `FORMAT.md` now rules that every field of a record is either MEASURED AT THE EVENT
(immutable once committed) or CURRENT STATE (recomputable, named `current_*`, and never stored inside
a committed row). A ruling that lives only in a document is a declaration; a ruling that FAILS A ROW
IS A FORMAT. This is the failing part.

    python3 check_provenance_classes.py --self-test     # the controls, both directions
    python3 check_provenance_classes.py                 # the committed rows
    python3 check_provenance_classes.py <row.json> ...  # named rows

THE THREE DEFECTS THIS CATCHES

  1. AN UNCLASSIFIED FIELD. A row carries a field the table does not name. The rule then has a hole
     exactly where a future author was inventive -- which is where it will be.
  2. A `current_*` FIELD INSIDE A COMMITTED ROW. Current state depends on bytes outside the row, so
     writing it in changes the row's digest -- the annotation destroys the record it annotates. The
     name is the tell, and this reads the name.
  3. A `C` CLASS UNDER A BARE NAME. A reader who sees `simulator_digest` is entitled to rely on it
     being the instrument at measurement. A bare name that is defined as recomputable is a lie the
     format itself tells.

THE HONEST LIMIT, STATED. Checks 1 and 2 are mechanical and complete over the fields present. Check 3
is a consistency check between the table and itself: THIS SCRIPT CANNOT TELL whether the value of a
bare field was in fact recomputed at read time -- it reads names and table rows, not intentions. What
it can do is make the recomputation impossible to do while keeping a bare name, which is the part that
was silent before.
"""
import glob
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FORMAT = os.path.join(HERE, "FORMAT.md")
ROW_GLOB = os.path.join(HERE, "probes", "ZORK_*.json")
LEDGER = os.path.join(HERE, "provenance", "measurement_times.json")

CLASSES = {"M1", "M2", "C"}
ROW_RE = re.compile(r"^\|\s*`([A-Za-z0-9_]+)`\s*\|\s*`(M1|M2|C)`\s*\|")
CURRENT_PREFIX = "current_"


def load_table(path=FORMAT):
    """{field: class} from the section-10 table. Raises if the table is not there or is empty."""
    declared, dupes = {}, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = ROW_RE.match(line.strip())
            if not m:
                continue
            name, cls = m.group(1), m.group(2)
            if name in declared:
                dupes.append(name)
            declared[name] = cls
    if not declared:
        raise RuntimeError("no classification table found in %s" % path)
    if dupes:
        raise RuntimeError("field classified twice in %s: %s" % (path, sorted(set(dupes))))
    return declared


def is_sidecar(path):
    """A sidecar ANNOTATES a row and is not one. `current_*` is legal there and illegal in a row --
    which is the whole distinction, so the two must not be checked by the same branch."""
    return os.path.basename(path).endswith(".provenance.json")


def check_one(path, declared):
    """[(severity, message)] for one record. severity in {"FAIL", "NOTE"}."""
    out = []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        return [("FAIL", "%s: unparseable (%s)" % (os.path.basename(path), exc))]
    if not isinstance(d, dict):
        return [("FAIL", "%s: not a JSON object" % os.path.basename(path))]
    base = os.path.basename(path)
    if is_sidecar(path):
        return out                      # a sidecar is where current state belongs; not a row
    for key in d:
        if key.startswith(CURRENT_PREFIX):
            out.append(("FAIL", "%s: carries `%s` -- current state must not be written into a "
                                "committed row (FORMAT.md 10, naming rule 3)" % (base, key)))
        elif key not in declared:
            out.append(("FAIL", "%s: field `%s` is not classified in FORMAT.md 10" % (base, key)))
    return out


def check_table(declared):
    """The table against itself: a C class under a bare name is a lie in the format."""
    out = []
    for name, cls in sorted(declared.items()):
        if cls == "C" and not name.startswith(CURRENT_PREFIX):
            out.append(("FAIL", "FORMAT.md 10: `%s` is class C under a BARE name -- current state "
                                "must be named `%s<thing>`" % (name, CURRENT_PREFIX)))
        if name.startswith(CURRENT_PREFIX) and cls != "C":
            out.append(("FAIL", "FORMAT.md 10: `%s` is named as current state but classified %s"
                        % (name, cls)))
    return out


def run(paths, declared, quiet=False):
    findings = list(check_table(declared))
    for p in paths:
        findings += check_one(p, declared)
    present = set()
    for p in paths:
        try:
            present.update(json.load(open(p, encoding="utf-8")).keys())
        except Exception:
            pass
    # The ledger beside the rows carries classified keys of its own. Counting them here keeps the
    # "declared but carried by nothing" note honest instead of turning 19 rows of the table into noise.
    try:
        led = json.load(open(LEDGER, encoding="utf-8"))
        present.update(led.keys())
        for entry in led.get("rows", []):
            if isinstance(entry, dict):
                present.update(entry.keys())
    except Exception:
        pass
    fails = [m for s, m in findings if s == "FAIL"]
    notes = ["declared in FORMAT.md 10 but carried by no row: `%s`" % n
             for n in sorted(set(declared) - present)]
    if not quiet:
        print("  scope  %d row(s), %d declared field(s)" % (len(paths), len(declared)))
        for p in paths:
            print("         %s" % os.path.relpath(p, HERE))
        for m in fails:
            print("  FAIL  " + m)
        for n in notes:
            print("  note  " + n)
        print("  %s  %d field(s) checked across %d row(s): %d failure(s)"
              % ("OK  " if not fails else "RED ", len(present), len(paths), len(fails)))
    return fails, notes, present


def _self_test():
    declared = load_table()
    base_rows = sorted(glob.glob(ROW_GLOB))
    print("[0] THE TABLE PARSES, AND THE SCOPE IS PRINTED WITH ITS COUNT")
    print("  PASS  %d fields classified in FORMAT.md 10" % len(declared))
    print("  PASS  %d committed rows in scope" % len(base_rows))
    if not base_rows:
        print("  FAIL  no rows found at %s -- a check with an empty scope proves nothing" % ROW_GLOB)
        return 1

    print("\n[1] THE COMMITTED ROWS: every field classified, no current state inside a row")
    fails, notes, present = run(base_rows, declared)
    print("  PASS  %d distinct fields present, all classified" % len(present) if not fails
          else "  FAIL  see above")
    if notes:
        print("  note  %d declared field(s) carried by no row" % len(notes))

    scratch = tempfile.mkdtemp(prefix="prov_classes_")
    try:
        src = base_rows[0]
        good = json.load(open(src, encoding="utf-8"))

        # MUTANT 1: a field nobody classified.
        m1 = os.path.join(scratch, "m1_undeclared.json")
        d = dict(good); d["a_field_invented_after_the_rule"] = 1
        json.dump(d, open(m1, "w", encoding="utf-8"))
        f1, _, _ = run([m1], declared, quiet=True)
        caught1 = any("is not classified" in m for m in f1)
        print("\n[2] A FIELD NOBODY CLASSIFIED IS CAUGHT")
        print("  %s  an undeclared field fails the check" % ("PASS" if caught1 else "FAIL"))
        print("  %s  ...and the failure NAMES the field"
              % ("PASS" if any("a_field_invented_after_the_rule" in m for m in f1) else "FAIL"))

        # MUTANT 2: current state written into a committed row.
        m2 = os.path.join(scratch, "m2_current_in_row.json")
        d = dict(good); d["current_simulator_digest"] = "b9701007d6e186d5"
        json.dump(d, open(m2, "w", encoding="utf-8"))
        f2, _, _ = run([m2], declared, quiet=True)
        caught2 = any("current state must not be written into a committed row" in m for m in f2)
        print("\n[3] CURRENT STATE INSIDE A COMMITTED ROW IS CAUGHT")
        print("  %s  `current_simulator_digest` in a row fails the check"
              % ("PASS" if caught2 else "FAIL"))

        # MUTANT 3: the table declares a BARE name as current state.
        bad_fmt = os.path.join(scratch, "FORMAT.md")
        body = open(FORMAT, encoding="utf-8").read() + "\n| `simulator_digest_recomputed` | `C` | mutation |\n"
        open(bad_fmt, "w", encoding="utf-8").write(body)
        try:
            bad_declared = load_table(bad_fmt)
            f3 = [m for s, m in check_table(bad_declared) if s == "FAIL"]
        except Exception as exc:
            f3 = [str(exc)]
        caught3 = any("BARE name" in m for m in f3)
        print("\n[4] A BARE NAME DEFINED AS CURRENT STATE IS CAUGHT")
        print("  %s  a `C` class under a bare name fails the table check"
              % ("PASS" if caught3 else "FAIL"))

        # THE POSITIVE DIRECTION: the same bytes are legal in a sidecar and illegal in a row.
        m4_side = os.path.join(scratch, "m4.provenance.json")
        m4_row = os.path.join(scratch, "m4_row.json")
        payload = {"current_simulator_digest": "b9701007d6e186d5",
                   "reading": "sidecar, not a row"}
        for p in (m4_side, m4_row):
            json.dump(payload, open(p, "w", encoding="utf-8"))
        f_side, _, _ = run([m4_side], declared, quiet=True)
        f_row, _, _ = run([m4_row], declared, quiet=True)
        caught4a = not f_side
        caught4b = any("current state must not be written into a committed row" in m for m in f_row)
        print("\n[5] THE RULE IS ABOUT THE ROW, NOT A BAN ON THE NAME")
        print("  %s  the SAME bytes in a `.provenance.json` sidecar are accepted"
              % ("PASS" if caught4a else "FAIL"))
        print("  %s  ...and in a row are refused"
              % ("PASS" if caught4b else "FAIL"))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    checks = [
        ("table parses with a non-empty scope", bool(declared and base_rows)),
        ("committed rows classify cleanly", not fails),
        ("an undeclared field fails", caught1),
        ("the failure names the field",
         any("a_field_invented_after_the_rule" in m for m in f1) if caught1 else False),
        ("current state in a row fails", caught2),
        ("a bare name declared C fails", caught3),
        ("a sidecar carrying current state is accepted", caught4a),
        ("a row carrying current state is refused", caught4b),
    ]
    nfail = sum(1 for _n, ok in checks if not ok)
    print("\n" + "=" * 100)
    print("%d FAILED   --   %d/%d" % (nfail, len(checks) - nfail, len(checks)))
    print("=" * 100)
    return 1 if nfail else 0


def main(argv):
    if "--self-test" in argv:
        return _self_test()
    paths = [a for a in argv[1:] if not a.startswith("-")]
    if not paths:
        paths = sorted(glob.glob(ROW_GLOB))
    declared = load_table()
    fails, notes, present = run(paths, declared)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
