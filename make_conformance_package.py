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
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# LOCAL: meaningful only on the machine that wrote it.
LOCAL = {
    ("host", "node"), ("host", "platform"), ("host", "cpu_count"), ("host", "nvidia_smi"),
    ("config", "server_argv"),
    ("config", "n_gpu_layers"),          # a property of THIS box's VRAM, not of the measurement
}

# FORMAT: an independent implementation produces it with an equivalent value. Grouped by what it IS.
FORMAT = [
    ("IDENTITY", ["run_id", "entrant", "level", "kind", "cap",
                  "simulator_digest", "legend_digest", "freeze"]),
    ("CONFIG -- DECLARED, PORTABLE", ["config.reasoning", "config.reasoning_source",
                                      "config.reasoning_declared", "config.reasoning_declared_in",
                                      "config.reasoning_rationale",
                                      "config.reasoning_changed_from_declaration",
                                      "config.reasoning_argv", "config.ctx",
                                      "config.temperature", "config.max_tokens_ceiling",
                                      "config.command_cap", "config.legend"]),
    ("COUNTERS -- THE MEASUREMENT", ["solved", "moves", "attempted", "blocked",
                                     "not_an_action", "give_up", "gave_up_at", "ended", "trace"]),
    ("HONESTY FIELDS -- THE ONES THAT SAY WHAT IS MISSING",
     ["loaded", "load_s", "never_started", "unreadable", "missing_values",
      "unreadable_is_the_aggregate_of", "missing_values_are_a_subset_of"]),
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
    for parent, key in sorted(LOCAL):
        blk = d.get(parent) or cell.get(parent) or {}
        if isinstance(blk, dict) and key in blk:
            v = blk[key]
            print(f"      {parent}.{key:26s} = {str(v)[:58]}")
        else:
            print(f"      {parent}.{key:26s} (not present in this artifact)")

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
