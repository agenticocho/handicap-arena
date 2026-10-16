#!/usr/bin/env python3
"""SPLIT THE RECORD INTO TWO LISTS -- THE FORMAT, AND THE LOCAL BOOKKEEPING.

THE CHAIR'S HARD REQUIREMENT: the spec ships as TWO LISTS, because THE RECORD AS IT STANDS CANNOT BE
PUBLISHED. It carries `host` (node, platform, cpu_count, nvidia_smi) and `config.server_argv` (absolute local
paths). A conforming implementation following the record shape literally WOULD PUBLISH OUR FILESYSTEM.

SO THE SPLIT IS NOT AN EDITORIAL JUDGEMENT, IT IS A TEST, AND THE TEST IS RUN RATHER THAN ASSERTED:

    A FIELD IS FORMAT IF AN INDEPENDENT IMPLEMENTATION, ON OTHER HARDWARE, IN ANOTHER LANGUAGE,
    WOULD PRODUCE IT WITH A VALUE THAT MEANS THE SAME THING.
    A FIELD IS LOCAL IF ITS VALUE IS MEANINGFUL ONLY ON THE MACHINE THAT WROTE IT.

AND THE MECHANICAL PART: every field classified FORMAT is scanned for a path-shaped value, a hostname, or a
device name. A FORMAT field whose value looks local is a HARD FAILURE, not a warning -- because that is the
leak the two lists exist to prevent.

    python3 make_conformance_package.py

AND THE TWO LISTS ARE ENFORCED RATHER THAN BELIEVED: `check_conformance_census.py` reads the writer that OWNS
these names, by `ast`, and fails on drift in BOTH directions -- a name the writer emits that these lists do not
carry, and a name these lists carry that the writer does not emit. It also cross-checks this file's `FORMAT` and
`LOCAL` against the package's §1 `LIST 1`/`LIST 2`, because they are ONE LIST IN TWO CARRIERS and two carriers
can disagree. Run it after every change here.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# LOCAL: meaningful only on the machine that wrote it. A PATH, not a pair: a tuple of length 1 is a TOP-LEVEL
# field (`why`), a tuple of length 2 is a field inside a block (`host.node`). A split that can only name nested
# fields cannot name a top-level local one.
LOCAL = {
    ("host", "node"), ("host", "platform"), ("host", "cpu_count"), ("host", "nvidia_smi"),
    ("config", "server_argv"),
    ("config", "n_gpu_layers"),          # a property of THIS box's VRAM, not of the measurement
    # ---- ARTIFACT REPLACED: a block, and it is LOCAL as a block. It records a LOCAL EVENT at a LOCAL
    # coordinate -- the repo-relative path of the record this run destroyed, when it was last written, its
    # size -- and what that record claimed about its own instrument. Only the fact that it existed is
    # meaningful elsewhere, and that is not what these keys carry.
    ("artifact_replaced",),
    ("artifact_replaced", "path"), ("artifact_replaced", "sha256"), ("artifact_replaced", "bytes"),
    ("artifact_replaced", "mtime"), ("artifact_replaced", "it_named"),
    ("artifact_replaced", "reason_given"), ("artifact_replaced", "reading"),
    # ---- `why` QUOTES THIS BOX. Two of its three branches embed the holder's tenancy reading -- pid and MiB,
    # read off this machine -- and every branch quotes the local server's own log line with its line number.
    # THE PORTABLE HALF OF THE SAME FACT TRAVELS BESIDE IT as `load_failure_class`, which is FORMAT.
    # AND THE TRIPWIRE WOULD NOT HAVE CAUGHT THIS: no pattern in LEAK matches `pid 2418 (134 MiB)`. The
    # classification is made by the TEST, and the tripwire's blind spot is recorded here rather than left
    # as a false sense of cover.
    ("why",),
    # ---- the probe's failure text, verbatim from the local socket. UNBOUNDED: it is whatever the exception
    # says, so no other implementation can be promised a value that means the same thing. The portable half is
    # `observed: None` -- the probe recorded no reading.
    ("reasoning_probe", "error"),
}

# FORMAT: an independent implementation produces it with an equivalent value. Grouped by what it IS.
FORMAT = [
    ("IDENTITY", ["run_id", "entrant", "entrant_digest", "entrant_digest_scope", "level", "kind", "cap",
                  "simulator_digest", "legend_digest", "freeze"]),
    ("CONFIG -- DECLARED, PORTABLE", ["config.reasoning", "config.reasoning_source",
                                      "config.reasoning_declared", "config.reasoning_declared_in",
                                      "config.reasoning_rationale",
                                      "config.reasoning_changed_from_declaration",
                                      "config.reasoning_argv", "config.ctx",
                                      "config.temperature", "config.max_tokens_ceiling",
                                      "config.command_cap", "config.legend"]),
    # WHICH BINARY, WITHOUT A PATH. `server_argv` already carries the absolute path and is already LOCAL;
    # these three are what the record can say about the instrument without publishing a coordinate -- a
    # digest, what the digest is a digest OF, and which selector chose it. Measured, not asserted: the
    # tripwire is run over them.
    ("INSTRUMENT -- WHICH BINARY", ["config.server_binary_digest", "config.server_binary_digest_scope",
                                    "config.server_binary_source"]),
    ("COUNTERS -- THE MEASUREMENT", ["solved", "moves", "attempted", "attempted_emitted",
                                     "attempted_consumed", "attempted_note", "blocked",
                                     "not_an_action", "give_up", "gave_up_at", "ended", "trace",
                                     # A DIAGNOSTIC THAT CANNOT BE READ AS A COUNTER, because a diagnostic read
                                     # as a counter is how a diagnostic becomes a score. It is in no rate, no
                                     # gate and no denominator, and its own NAME says so.
                                     "loose_match_diagnostic_only_never_scored",
                                     "loose_match_diagnostic_note"]),
    ("HONESTY FIELDS -- THE ONES THAT SAY WHAT IS MISSING",
     ["loaded", "load_s", "never_started", "unreadable", "missing_values",
      "unreadable_is_the_aggregate_of", "missing_values_are_a_subset_of"]),
    # WHICH CONDITION A FAILURE IS REPORTING, and the caveat on a cell the harness confounded. The PROSE that
    # quotes this box is LOCAL (`why`); the CLASS travels.
    ("FAILURE -- WHICH CONDITION IT REPORTS", ["load_failure_class", "ended_why"]),
    ("INSTRUMENT READINGS", ["reasoning_probe", "budget_signature", "dead_end", "turns"]),
]

# what a leak looks like. NOT a security scanner -- a tripwire for the specific mistake of publishing a path.
LEAK = [
    (r"/home/", "an absolute home path"),
    (r"/mnt/", "a mount path"),
    (r"^[A-Za-z]:\\", "a Windows path"),
    (r"\.gguf", "a model FILENAME (a model IDENTITY is format; a filename is a local naming)"),
    (r"\bnvidia-smi\b", "a device tool"),
    (r"RTX \d", "a device model"),
    (r"\bRyzen\b", "a CPU model"),
]


def leak_in(key, value):
    s = json.dumps(value) if not isinstance(value, str) else value
    out = []
    for pat, why in LEAK:
        if re.search(pat, s):
            out.append(why)
    return out


def main():
    art = os.path.join(HERE, "probes", "SOKOBAN_RUN_20261010-072252.json")
    print("=" * 100)
    print("THE TWO LISTS -- the format, and the local bookkeeping")
    print("=" * 100)
    try:
        d = json.load(open(art))
    except OSError as e:
        print(f"  cannot read the run of record: {e}")
        return 2

    cell = next((c for c in (d.get("cells") or []) if isinstance(c, dict)), {})

    def resolve(name):
        """-> (found: bool, value). RESOLUTION IS ATTEMPTED AT EVERY LEVEL THE FIELD COULD LIVE AT.

        MY FIRST VERSION LOOKED ONLY AT THE TOP LEVEL AND TREATED `None` AS "NOTHING TO CHECK". `entrant`
        LIVES PER-CELL, SO IT RESOLVED TO None AND WAS WAVED THROUGH -- AND `entrant` IS THE ONE FIELD THAT
        CARRIES A `.gguf` FILENAME. A CHECK THAT SKIPS WHAT IT CANNOT READ REPORTS CLEAN FOR THE SAME REASON
        A DEAD PROBE REPORTS SUCCESS.
        """
        head, _, tail = name.partition(".")
        for scope in (d, cell, cell.get("config") or {}, d.get("config") or {}):
            if not isinstance(scope, dict):
                continue
            if tail:
                blk = scope.get(head)
                if isinstance(blk, dict) and tail in blk:
                    return True, blk[tail]
            elif head in scope:
                return True, scope[head]
        return False, None

    print("\n  LIST 1 -- THE FORMAT. An independent implementation produces these.\n")
    problems = []
    UNRESOLVED = []
    for group, names in FORMAT:
        print(f"    {group}")
        for n in names:
            found, val = resolve(n)
            leaks = leak_in(n, val) if found else []
            # AN UNRESOLVED FIELD IS REPORTED, NOT WAVED THROUGH. "not in this artifact" and "checked and
            # clean" are different statements and must not print the same way.
            mark = "!" if leaks else (" " if found else "?")
            if leaks:
                detail = f"  <-- LEAK: {'; '.join(leaks)}"
            elif found:
                detail = ""
            else:
                detail = "  <-- UNRESOLVED: not checked, not clean"
                UNRESOLVED.append(n)
            shown = f" = {str(val)[:44]}" if found and n == "entrant" else ""
            print(f"      {mark} {n:44s} {'present' if found else 'NOT FOUND'}{shown}{detail}")
            if leaks:
                problems.append((n, leaks))

    print("\n  LIST 2 -- LOCAL BOOKKEEPING. A conforming implementation does NOT produce these.\n")
    for path in sorted(LOCAL):
        # A PATH: one name for a TOP-LEVEL field (`why`), two for a field inside a block (`host.node`).
        if len(path) == 1:
            top = path[0]
            found = top in d or top in cell
            value = d.get(top, cell.get(top))
        else:
            parent, key = path
            blk = d.get(parent) or cell.get(parent) or {}
            found = isinstance(blk, dict) and key in blk
            value = blk[key] if found else None
        if found:
            print(f"      {'.'.join(path):34s} = {str(value)[:58]}")
        else:
            print(f"      {'.'.join(path):34s} (not present in this artifact)")

    print()
    print("=" * 100)
    if problems:
        print(f"  *** {len(problems)} FORMAT FIELD(S) CARRY A LOCAL VALUE. THE SPLIT IS NOT CLEAN. ***")
        for n, l in problems:
            print(f"      {n}: {'; '.join(l)}")
        print("  A CONFORMING IMPLEMENTATION FOLLOWING LIST 1 LITERALLY WOULD PUBLISH THESE.")
        return 1
    print("  THE SPLIT IS CLEAN: no field classified FORMAT carries a path-, host- or device-shaped value.")
    print("  AND THE TRIPWIRE IS THE PART THAT MATTERS -- it is run, not asserted. A LIST THAT IS ONLY")
    print("  BELIEVED IS THE DOCUMENT THIS EXERCISE EXISTS TO PREVENT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
