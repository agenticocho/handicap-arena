#!/usr/bin/env python3
"""THE MEASUREMENT INSTANT, AS A CHECK -- `provenance/measurement_times.json` against the rows.

WHY THIS EXISTS. On 2026-10-26 the Local Chair read eight committed rows as having `mtime`
2026-10-25 and concluded that a later commit had rewritten their `simulator_digest`. The rows were
in fact written 2026-10-26 14:05-14:06; the 2026-10-25 timestamp was `artifact_replaced.mtime` --
the mtime of the record each row REPLACED, carried inside a block. A row that does not say WHEN it
was measured is a row whose reader has to guess, and the guess available to a reader is the
predecessor's time. That guess was wrong once and cost a withdrawn ruling.

So: `measured_at_utc` is recorded for every row, BESIDE the row (FORMAT.md 10, naming rule 3: writing
a field into a committed row changes the digest of the record it annotates). This checks the ledger:

    python3 check_measurement_times.py --self-test    # six controls, five of them mutants
    python3 check_measurement_times.py                # the committed ledger

WHAT IT CAN AND CANNOT DO. It cannot prove the filesystem reading was true -- nothing in the repo
can, the reading is not in git. It CAN prove the ledger still describes THESE bytes (the entry is
keyed by the row's sha256), that the row's own time is never the predecessor's time, and that the
superseded artefact each entry names is present on disk and hashes to the digest the row recorded.
That last one turns "recoverable" from a claim into a measurement.
"""
import glob
import hashlib
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_provenance_classes import load_table            # one parser for the section-10 table

LEDGER = os.path.join(HERE, "provenance", "measurement_times.json")
ROW_GLOB = os.path.join(HERE, "probes", "ZORK_*.json")
CURRENT_PREFIX = "current_"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def instant(text):
    """A timezone-aware datetime, or raise. A reading with no zone is not a reading of an instant."""
    d = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("no timezone on %r -- an instant with no zone is a local guess" % text)
    return d


def check(ledger, rows, declared):
    """[(severity, message)] for one ledger against one set of rows (rel path -> abs path)."""
    out = []
    if not isinstance(ledger, dict) or not isinstance(ledger.get("rows"), list):
        return [("FAIL", "ledger is not an object with a `rows` list")]

    entries = ledger["rows"]
    by_row = {}
    for i, e in enumerate(entries):
        if not isinstance(e, dict) or "row" not in e:
            out.append(("FAIL", "entry %d has no `row`" % i))
            continue
        if e["row"] in by_row:
            out.append(("FAIL", "`%s` has two entries" % e["row"]))
        by_row[e["row"]] = e

    live = {os.path.relpath(p, HERE): p for p in rows}
    for rel in sorted(set(live) - set(by_row)):
        out.append(("FAIL", "%s: no entry in the ledger -- a row whose measurement time is not "
                            "recorded is a row the next reader will date from its predecessor" % rel))
    for rel in sorted(set(by_row) - set(live)):
        out.append(("FAIL", "%s: ledger entry names a row that is not there" % rel))

    for rel, e in sorted(by_row.items()):
        if rel not in live:
            continue
        try:
            row = json.load(open(live[rel], encoding="utf-8"))
        except Exception as exc:
            out.append(("FAIL", "%s: unparseable (%s)" % (rel, exc)))
            continue
        # [A] KEYED BY THE BYTES IT ANNOTATES.
        digest, size = sha256(live[rel]), os.path.getsize(live[rel])
        if e.get("row_sha256") != digest:
            out.append(("FAIL", "%s: ledger says sha256 %s, the file is %s -- the annotation has "
                                "drifted off its subject" % (rel, str(e.get("row_sha256"))[:12],
                                                             digest[:12])))
        if e.get("row_bytes") != size:
            out.append(("FAIL", "%s: ledger says %s B, the file is %d B"
                        % (rel, e.get("row_bytes"), size)))
        # [B] THE INSTANT IS AN INSTANT, AND IT IS NOT THE PREDECESSOR'S.
        try:
            measured = instant(e["measured_at_utc"])
            predecessor = instant(e["predecessor_mtime_utc"])
        except Exception as exc:
            out.append(("FAIL", "%s: %s" % (rel, exc)))
            continue
        if e["measured_at_utc"] == e["predecessor_mtime_utc"]:
            out.append(("FAIL", "%s: measured_at_utc == predecessor_mtime_utc -- the confusion the "
                                "ledger exists to end" % rel))
        if not measured > predecessor:
            out.append(("FAIL", "%s: the row claims to have been written at %s, BEFORE the record it "
                                "replaced (%s)" % (rel, e["measured_at_utc"],
                                                   e["predecessor_mtime_utc"])))
        # [C] THE ROW'S OWN `artifact_replaced` IS THE PREDECESSOR THE LEDGER NAMES.
        rec = (row.get("artifact_replaced") or {})
        if e.get("predecessor_sha256") != rec.get("sha256"):
            out.append(("FAIL", "%s: ledger predecessor %s is not the row's artifact_replaced %s"
                        % (rel, str(e.get("predecessor_sha256"))[:12], str(rec.get("sha256"))[:12])))
        if e.get("predecessor_mtime_utc") != rec.get("mtime"):
            out.append(("FAIL", "%s: ledger predecessor time %s is not the row's "
                                "artifact_replaced.mtime %s"
                        % (rel, e.get("predecessor_mtime_utc"), rec.get("mtime"))))
        # [D] THE PRESERVATION CAME FIRST, AND THE SUPERSEDED BYTES ARE STILL RECOVERABLE.
        try:
            preserved_at = instant(e["preserved_at_utc"])
            if not measured > preserved_at:
                out.append(("FAIL", "%s: the record was preserved at %s, AFTER this row was written "
                                    "at %s -- then it is not the record this row replaced"
                            % (rel, e["preserved_at_utc"], e["measured_at_utc"])))
        except Exception as exc:
            out.append(("FAIL", "%s: preserved_at_utc: %s" % (rel, exc)))
        copy = os.path.join(HERE, e.get("preserved_copy") or "")
        if not os.path.exists(copy):
            out.append(("FAIL", "%s: preserved copy `%s` is not on disk -- the superseded artefact is "
                                "not recoverable at this path" % (rel, e.get("preserved_copy"))))
        elif sha256(copy) != e.get("predecessor_sha256"):
            out.append(("FAIL", "%s: preserved copy hashes to %s, not the recorded predecessor %s"
                        % (rel, sha256(copy)[:12], str(e.get("predecessor_sha256"))[:12])))
        # [E] EVERY KEY CLASSIFIED, AND NOTHING HERE CLAIMS TO BE CURRENT STATE.
        for key in list(e) + list(ledger):
            if key.startswith(CURRENT_PREFIX):
                out.append(("FAIL", "%s: ledger key `%s` -- current state is recomputable and cannot "
                                    "be evidence about when this row was measured" % (rel, key)))
            elif key not in declared:
                out.append(("FAIL", "%s: ledger key `%s` is not classified in FORMAT.md 10"
                            % (rel, key)))
    return out


def report(findings, n_rows):
    fails = [m for _s, m in findings if _s == "FAIL"]
    for m in fails:
        print("  FAIL  " + m)
    print("  %s  %d row(s), %d failure(s)" % ("OK  " if not fails else "RED ", n_rows, len(fails)))
    return fails


def _self_test():
    declared = load_table()
    rows = sorted(glob.glob(ROW_GLOB))
    ledger = json.load(open(LEDGER, encoding="utf-8"))
    print("[0] SCOPE, PRINTED WITH ITS COUNT")
    if not rows:
        print("  FAIL  no rows at %s -- a check with an empty scope proves nothing" % ROW_GLOB)
        return 1
    if len(ledger.get("rows", [])) != len(rows):
        print("  FAIL  %d ledger entries against %d rows" % (len(ledger["rows"]), len(rows)))
        return 1
    print("  PASS  %d row(s), %d ledger entr(ies)" % (len(rows), len(ledger["rows"])))
    print("  PASS  %d fields classified in FORMAT.md 10" % len(declared))

    print("\n[1] THE COMMITTED LEDGER DESCRIBES THE COMMITTED ROWS")
    base = report(check(ledger, rows, declared), len(rows))

    def mutate(label, fn, expect):
        import copy
        d = copy.deepcopy(ledger)
        fn(d)
        f = [m for s, m in check(d, rows, declared) if s == "FAIL"]
        caught = any(expect in m for m in f)
        print("  %s  %-62s -> %s" % ("PASS" if caught else "FAIL", label,
                                     "caught" if caught else "NOT CAUGHT"))
        return caught

    print("\n[2] THE CONTROLS FIRE IN EVERY DIRECTION THAT MATTERS")
    results = [
        mutate("an entry dropped (a row with no recorded time)",
               lambda d: d["rows"].pop(), "no entry in the ledger"),
        mutate("row_bytes nudged (annotation drifted off its subject)",
               lambda d: d["rows"][0].__setitem__("row_bytes", d["rows"][0]["row_bytes"] + 1),
               "the file is"),
        mutate("measured_at and predecessor_mtime SWAPPED (the R2 misreading)",
               lambda d: d["rows"][0].__setitem__(
                   "measured_at_utc", d["rows"][0]["predecessor_mtime_utc"]),
               "BEFORE the record it replaced"),
        mutate("one key nothing classified",
               lambda d: d["rows"][0].__setitem__("when_it_ran", "yesterday"),
               "is not classified"),
        mutate("the preserved copy pointed at nothing",
               lambda d: d["rows"][0].__setitem__("preserved_copy", "suite3/preserved/nope.json"),
               "not on disk"),
        mutate("a `current_*` key smuggled into the ledger",
               lambda d: d.__setitem__("current_simulator_digest", "b9701007d6e186d5"),
               "current state is recomputable"),
    ]
    print("\n" + "=" * 100)
    checks = [not base] + results
    nfail = sum(1 for c in checks if not c)
    print("%d FAILED   --   %d/%d" % (nfail, len(checks) - nfail, len(checks)))
    print("=" * 100)
    return 1 if nfail else 0


def main(argv):
    if "--self-test" in argv:
        return _self_test()
    declared = load_table()
    rows = sorted(glob.glob(ROW_GLOB))
    ledger = json.load(open(LEDGER, encoding="utf-8"))
    print("  ledger  %s  (observed_at_utc %s)" % (os.path.relpath(LEDGER, HERE),
                                                  ledger.get("observed_at_utc")))
    print("  %-16s %-28s %-24s %s" % ("row sha256", "measured_at_utc", "predecessor_mtime_utc",
                                      "row"))
    for e in ledger["rows"]:
        print("  %-16s %-28s %-24s %s" % (str(e.get("row_sha256"))[:16], e.get("measured_at_utc"),
                                          e.get("predecessor_mtime_utc"),
                                          os.path.basename(str(e.get("row")))))
    print()
    fails = report(check(ledger, rows, declared), len(rows))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
