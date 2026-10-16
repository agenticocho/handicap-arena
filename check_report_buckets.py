#!/usr/bin/env python3
"""AN ENFORCER FOR THE REPORT'S BUCKET RULE -- THE WRITER STILL WRITES THE KEY, THE READER STILL READS IT.

WHY THIS EXISTS. `sokoban_report.py` buckets a non-loading cell by the field the driver writes
(`load_failure_class`) and FALLS BACK to splitting the prose in `why` for records that predate the field --
that is what card t_7d2eb103 landed, and it prints which of the two rules produced each bucket. **THE
FALLBACK IS WHAT MAKES A RENAME SILENT.** Nothing outside `sokoban_report.py` reads `sokoban_run.py`'s
load-failure path, so if that key were renamed or dropped: every bucket takes the PROSE rule, every reason
line reads `[prose] ...`, and the report EXITS 0 -- one plausible report over a class the driver decided and
no longer publishes. The reader's own `--self-test` cannot see it: it exercises the pure `failure_bucket`
function over records built inside the test file and never reads the writer's field NAME.

IT FAILS WHEN:

  A  THE WRITER NO LONGER PUTS THE KEY INTO ITS LOAD-FAILURE RECORD. Checked by EXECUTING the writer's own
     `load_failure()` and reading the key set it returns -- not by grepping the writer for a copy of a list
     kept here. A copy of the writer's key list in this file would be the census defect one level out.
  B  THE FUNCTION'S RETURN REACHES NO RECORD. The writer's source must SPLAT `**load_failure(...)` into the
     failure record it returns; a key on a value nobody stores is a key the report cannot read.
  C  THE READER NO LONGER READS THAT KEY. The reader's source must get it out of the record.
  D  THE READER, DRIVEN OVER ONE FIXTURE OF EACH GENERATION, PRINTS SOMETHING ELSE THAN PREDICTED -- the
     bucket label, the `[field]` / `[prose]` tag and the tally line, for a record carrying a class, a
     pre-class record whose prose contains the fallback's split token, and a container of both.

AND IT HAS A CONTROL OF ITS OWN, RUN IN EVERY RUN: a copy of the writer with the key RENAMED and a copy of the
reader with the same literal renamed are written into this check's scratch and the SAME evaluation is run
against each -- BOTH MUST FIRE. A checker that has only ever been run on a clean tree has not been tested.

AND IT SAYS WHAT IT IS NOT: not a check on the counters, the rates, the levels or the models, and not a second
reader of the record -- it parses the report's OUTPUT, never the record. **The writer's class VALUES are not
listed here: the KEY is the contract, the values are the writer's, and the class this check's own fixture
carries is READ OUT OF THE WRITER at run time.** A check holding a second copy of the writer's values would go
stale exactly where the census defect does.

    python3 check_report_buckets.py
    python3 check_report_buckets.py --writer <a copy> [--reader <a copy>] [--no-control]

FIXTURES ARE WRITTEN INTO THIS CHECK'S OWN SCRATCH (`tempfile.mkdtemp`) AND REMOVED ON EXIT -- NEVER INTO
`probes/`, and never into any directory a sweep reads. Writing a fixture into the domain every sweep reads is
how a check changes what it measures.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WRITER = "sokoban_run.py"
READER = "sokoban_report.py"

# THE CONTRACT -- ONE KEY, NAMED ONCE. This is not a copy of the writer's VALUES: the writer owns its class
# strings, this file owns none of them, and the class its fixture carries is the one the writer RETURNS.
CONTRACT_KEY = "load_failure_class"
# THE TWO TAGS THE READER PRINTS BESIDE EVERY BUCKET -- the rule's own display vocabulary, read off the
# report's output by this check. NOT the values of the writer's classes.
RULE_FIELD = "field"
RULE_PROSE = "prose"

# A PATH THAT CANNOT EXIST, so the writer's own load-failure path is driven with no server and no model: the
# branch it takes is the unreadable-cause branch, and the RECORD is what this check reads.
NO_SUCH_PROBE = "/nonexistent/CHECK_REPORT_BUCKETS_no_such_file_probe"

# THE PRE-CLASS FIXTURE and the label the fallback must yield. The label is WRITTEN DOWN rather than
# recomputed here -- recomputing the split would make this file a second reader of the record.
PROSE = "PRE: the check's own prose fixture -- and the split token is inside it"
PROSE_LABEL = "PRE: the check's own prose fixture"

# THE REPORT'S OWN TWO FORMS, parsed out of its output:
#     did not load    3   [prose] server exited rc=1
#     [field]  0 of 3   from   load_failure_class -- the condition the driver decided and wrote down
BUCKET = re.compile(r"^\s+did not load\s+(\d+)\s+\[([a-z]+)\]\s?(.*)$")
TALLY = re.compile(r"^\s+\[([a-z]+)\]\s+(\d+) of (\d+)\s+from\s")
SHAPE = re.compile(r"^\s+source\s+\S+\s+SHAPE\s+(.*)$")


def writer_failure_record(path):
    """-> (keys, class_value, error): the record THE WRITER ITSELF returns on its load-failure path.

    READ, NOT COPIED. The writer's own module is executed and its own `load_failure()` is called, so the key
    set asserted against is the key set the writer produces -- if it is renamed, this changes and the check
    fires. The module is loaded BY PATH, which is how `verify_scope.py` loads `arena.py` and how
    `test_declared_root.py` loads the results-binder counter: one definition, not two that drift.
    """
    p = os.path.abspath(path)
    sys.path.insert(0, os.path.dirname(p))
    sys.path.insert(0, HERE)          # the writer's siblings live with THIS file's tree, wherever it is run
    try:
        spec = importlib.util.spec_from_file_location("_check_report_buckets_writer", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_check_report_buckets_writer"] = mod
        spec.loader.exec_module(mod)
    except Exception as e:                                                # noqa: BLE001
        return None, None, f"{os.path.basename(p)} COULD NOT BE EXECUTED: {type(e).__name__}: {e}"
    fn = getattr(mod, "load_failure", None)
    if fn is None:
        return None, None, (f"{os.path.basename(p)} carries no load_failure() -- the load-failure path whose "
                            f"record this check reads")
    try:
        rec = fn(NO_SUCH_PROBE, "the checks own status line")
    except Exception as e:                                                # noqa: BLE001
        return None, None, f"load_failure() raised {type(e).__name__}: {e}"
    if not isinstance(rec, dict):
        return None, None, f"load_failure() returned {type(rec).__name__}, not the record dict"
    return sorted(rec.keys()), rec.get(CONTRACT_KEY), None


def check_writer(path):
    """-> (problems, notes). The writer's own return, and the splat that puts it into a record."""
    problems, notes = [], []
    keys, value, err = writer_failure_record(path)
    if err:
        return [f"WRITER NOT READ -- {err}"], notes
    notes.append(f"writer  {os.path.basename(path)}: load_failure() returns the key(s) {keys}")
    if CONTRACT_KEY not in keys:
        problems.append(
            f"THE WRITER NO LONGER PUTS `{CONTRACT_KEY}` INTO ITS LOAD-FAILURE RECORD -- load_failure() "
            f"returns {keys}. Every bucket would take the PROSE rule, every reason line would read "
            f"`[prose] ...`, and THE REPORT WOULD STILL EXIT 0. This is the rename the check exists for.")
    elif not isinstance(value, str) or not value.strip():
        problems.append(
            f"THE WRITER RETURNS `{CONTRACT_KEY}` WITH NO USABLE VALUE ({value!r}) -- the reader treats a "
            f"blank class as ABSENT, so a blank class empties the field rule as quietly as a rename does.")
    else:
        notes.append(f"writer  the value it returns is {value!r}  "
                     f"(READ OUT OF THE WRITER, not copied into this file)")
    src = open(path, encoding="utf-8").read()
    splat = [i for i, ln in enumerate(src.splitlines(), 1) if re.search(r"\*\*\s*load_failure\s*\(", ln)]
    if not splat:
        problems.append(
            f"`{os.path.basename(path)}` NEVER SPLATS load_failure() INTO A RECORD -- the function's return "
            f"reaches no record, so the field is written nowhere and the reader has nothing to read.")
    else:
        notes.append(f"writer  line(s) {splat}: the failure record is built with **load_failure(...), so the "
                     f"return reaches the record")
    return problems, notes


def check_reader_reads(path):
    """-> (problems, notes). The reader's source must read the key the writer writes."""
    problems, notes = [], []
    src = open(path, encoding="utf-8").read()
    hits = [i for i, ln in enumerate(src.splitlines(), 1)
            if re.search(r"\.get\(\s*[\"']" + re.escape(CONTRACT_KEY) + r"[\"']\s*\)", ln)]
    if not hits:
        problems.append(
            f"`{os.path.basename(path)}` NO LONGER READS `{CONTRACT_KEY}` OUT OF THE RECORD -- it would "
            f"bucket every non-loading cell by the prose fallback and print a report over a class it cannot "
            f"see.")
    else:
        notes.append(f"reader  line(s) {hits}: the reader gets `{CONTRACT_KEY}` out of the record")
    return problems, notes


def reader_rows(stdout):
    """-> (buckets, tally, shape) out of the report's OWN OUTPUT. The record itself is never read here."""
    buckets, tally, shape = [], {}, None
    for ln in stdout.splitlines():
        m = SHAPE.match(ln)
        if m:
            shape = m.group(1).strip()
            continue
        m = BUCKET.match(ln)
        if m:
            buckets.append((int(m.group(1)), m.group(2), m.group(3)))
            continue
        m = TALLY.match(ln)
        if m:
            tally[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return buckets, tally, shape


def run_reader(reader_path, fixture_path, scratch):
    return subprocess.run(["python3", os.path.abspath(reader_path), fixture_path],
                          capture_output=True, text=True, cwd=scratch, timeout=300)


def drive_reader(reader_path, class_value, scratch):
    """-> (problems, notes). ONE FIXTURE OF EACH GENERATION, built here and written into THIS check's scratch.

    Each fixture is a whole cell record, so no wrapper and no artifact is needed and the check runs anywhere.
    """
    problems, notes = [], []
    with_class = {"entrant": "enforcer_class", "level": "L_class", "loaded": False,
                  "load_failure_class": class_value, "why": PROSE}
    pre_class = {"entrant": "enforcer_preclass", "level": "L_pre", "loaded": False, "why": PROSE}
    fixtures = {
        "class.json": with_class,
        "preclass.json": pre_class,
        "container.json": {"new": with_class, "pre": pre_class},
    }
    expected = {
        "class.json": ([(1, RULE_FIELD, class_value)], {RULE_FIELD: (1, 1), RULE_PROSE: (0, 1)}, "cell"),
        "preclass.json": ([(1, RULE_PROSE, PROSE_LABEL)], {RULE_PROSE: (1, 1), RULE_FIELD: (0, 1)}, "cell"),
        "container.json": ([(1, RULE_FIELD, class_value), (1, RULE_PROSE, PROSE_LABEL)],
                           {RULE_FIELD: (1, 2), RULE_PROSE: (1, 2)}, "container"),
    }
    for name in ("class.json", "preclass.json", "container.json"):
        path = os.path.join(scratch, name)
        json.dump(fixtures[name], open(path, "w"), indent=1)
        want_buckets, want_tally, want_shape = expected[name]
        r = run_reader(reader_path, path, scratch)
        notes.append(f"fixture {name}")
        if r.returncode != 0:
            problems.append(f"THE READER FAILED ON THE `{name}` FIXTURE -- rc {r.returncode}: "
                            f"{(r.stderr.strip().splitlines() or [''])[-1][:200]}")
            continue
        buckets, tally, shape = reader_rows(r.stdout)
        for n, rule, label in buckets:
            notes.append(f"          bucket  {n}   [{rule}] {label}")
        for rule in (RULE_FIELD, RULE_PROSE):
            if rule in tally:
                notes.append(f"          tally   [{rule}]  {tally[rule][0]} of {tally[rule][1]}")
        notes.append(f"          SHAPE   {shape}")
        if not (shape or "").startswith(want_shape):
            problems.append(f"THE `{name}` FIXTURE WAS READ AS SHAPE {shape!r}, NOT a {want_shape} -- the "
                            f"drive did not happen on the shape the check means to drive")
        if sorted(buckets) != sorted(want_buckets):
            problems.append(f"THE `{name}` FIXTURE BUCKETED DIFFERENTLY THAN PREDICTED --\n"
                            f"          wanted  {want_buckets}\n"
                            f"          got     {buckets}")
        for rule, want in want_tally.items():
            if tally.get(rule) != want:
                got = tally.get(rule)
                got_s = f"{got[0]} of {got[1]}" if got else "NO TALLY LINE AT ALL"
                problems.append(f"THE TALLY ON THE `{name}` FIXTURE IS NOT `[{rule}] {want[0]} of {want[1]}` "
                                f"-- got `[{rule}] {got_s}`")
    return problems, notes


def evaluate(writer_path, reader_path, scratch):
    """-> (problems, notes) for one pair of files. PURE with respect to the tree: it writes only to scratch."""
    problems, notes = [], []
    pw, nw = check_writer(writer_path)
    problems += pw
    notes += nw
    pr, nr = check_reader_reads(reader_path)
    problems += pr
    notes += nr
    keys, value, err = writer_failure_record(writer_path)
    class_value = value if isinstance(value, str) and value.strip() else None
    if class_value is None:
        # the writer supplied no class, so the FIELD fixture cannot be built from it. A synthetic value keeps
        # the reader's side driven, and the writer's own complaint above is the finding.
        class_value = "a class the writer did NOT supply (the check's own placeholder)"
        notes.append("NOTE    the writer supplied no usable class, so the field fixture carries a "
                     "placeholder -- the writer's complaint above is the finding")
    pd, nd = drive_reader(reader_path, class_value, scratch)
    problems += pd
    notes += nd
    return problems, notes


def write_mutated(src, dst, old, new):
    """-> how many literals were renamed. A COPY, written outside the tree -- never the tree's own file."""
    text = open(src, encoding="utf-8").read()
    n = text.count(old)
    open(dst, "w", encoding="utf-8").write(text.replace(old, new))
    return n


def control(writer_path, reader_path, scratch):
    """-> problems. THE CHECK MUST FIRE ON A RENAMED KEY -- on both sides of the contract.

    Both mutations are copies in this run's own scratch. A checker that has only ever been run on a clean tree
    has not been tested.
    """
    print("  " + "-" * 96)
    print("  CONTROL -- this check must FIRE on a RENAMED KEY. Until it has, a clean run proves nothing.")
    print()
    out = []
    renamed = '"%s_RENAMED_BY_THE_CONTROL"' % CONTRACT_KEY
    for side, src in (("reader", reader_path), ("writer", writer_path)):
        if side == "reader":
            mut = os.path.join(scratch, "CONTROL_reader_literal_renamed.py")
            hits = write_mutated(src, mut, '"%s"' % CONTRACT_KEY, renamed)
            rp, _ = evaluate(writer_path, mut, scratch)
        else:
            mut = os.path.join(scratch, "CONTROL_writer_key_renamed.py")
            hits = write_mutated(src, mut, '"%s"' % CONTRACT_KEY, renamed)
            rp, _ = evaluate(mut, reader_path, scratch)
        fired = bool(rp)
        print(f"    {side} copy  {os.path.basename(mut)}   ({hits} literal(s) renamed)   "
              f"-> complaints {len(rp)}   {'FIRED' if fired else 'DID NOT FIRE'}")
        for p in rp[:2]:
            for i, line in enumerate(str(p).splitlines()):
                print(f"         {'| ' if i else '  '}{line}")
        print()
        if not fired:
            out.append(f"THE CHECK DOES NOT FIRE ON A RENAMED {side.upper()} LITERAL -- so a clean result "
                       f"means nothing")
    return out


def main():
    ap = argparse.ArgumentParser(description="Does the writer still write the key the report's bucket rule "
                                             "reads, and does the reader still read it?")
    ap.add_argument("--writer", default=os.path.join(HERE, WRITER),
                    help=f"the writer to read (default: this tree's {WRITER})")
    ap.add_argument("--reader", default=os.path.join(HERE, READER),
                    help=f"the reader to drive (default: this tree's {READER})")
    ap.add_argument("--no-control", action="store_true",
                    help="skip the renamed-copy control (for a quick read; a run without it is NOT a check)")
    a = ap.parse_args()

    scratch = tempfile.mkdtemp(prefix="check_report_buckets.")
    print("=" * 100)
    print("THE REPORT'S BUCKET RULE -- DOES THE WRITER STILL WRITE THE KEY THE READER READS?")
    print("=" * 100)
    print(f"  writer  {a.writer}")
    print(f"  reader  {a.reader}")
    print(f"  scratch {scratch}")
    print("          (this check's own fixtures, written and removed by it -- NEVER into probes/, and never")
    print("           into any directory a sweep reads)")
    print()
    try:
        problems, notes = evaluate(a.writer, a.reader, scratch)
        for n in notes:
            print("  " + n)
        print()
        if problems:
            print("  *** THE REPORT'S BUCKET RULE IS NOT ENFORCED BY THE TREE AS IT STANDS ***")
            for p in problems:
                print(f"    {p}")
        else:
            print("  THE WRITER WRITES THE KEY, THE RECORD CARRIES IT, THE READER READS IT, AND THE READER")
            print("  PRINTS THE FIELD WHERE THE FIELD IS PRESENT AND THE NAMED FALLBACK WHERE IT IS NOT.")
        print()
        if not a.no_control:
            problems += control(a.writer, a.reader, scratch)
        print("  WHAT THIS IS NOT: not a check on the counters, the rates, the levels or the models, and not")
        print("  a second reader of the record -- it parses the report's OUTPUT, never the record. It carries")
        print("  no copy of the writer's class VALUES: the KEY is the contract, the values are the writer's,")
        print("  and the class its own fixture carries is read out of the writer at run time.")
        print()
        return 1 if problems else 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
