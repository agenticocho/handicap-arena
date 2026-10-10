#!/usr/bin/env python3
"""RULING 79, MECHANISED -- exactly ONE reader of record, and every scorer imports it.

    "the reader of record lives in the instrument of record, and every side-script imports it -- never
     reimplements it. Two readers for one record is the one-definition defect applied to interpretation,
     and it fails silently in the direction of a better-looking number."

The ruling is worth exactly what its control is worth, so this is the control. It FAILS on:

  A  A SECOND READER. Any module other than answer_reader.py that reads an answer out of a response by
     choosing between `content` and `reasoning_content`.
  B  A SCORER THAT DOES NOT IMPORT THE READER. A file that extracts an answer to SCORE it must import
     answer_reader; measuring a trace's LENGTH is a different act and is allowed.

AND IT HAS A CONTROL OF ITS OWN: it is run against a synthetic offender and MUST fire. A checker that has only
ever been run on a clean tree has not been tested.

    python3 check_one_reader.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
READER = "answer_reader.py"

# A SECOND READER: choosing between the two fields in one expression.
SECOND_READER = re.compile(r'\(\s*[\w\.\[\]\'"]*get\(\s*["\']content["\']\)\s*or\s*""\s*\)'
                           r'.*\bor\b.*reasoning_content'
                           r'|reasoning_content["\']\s*\)\s*or\s*""\s*\)\s*or\s*')
# READING the field at all is fine; SCORING it is not. So the offence is a fallback that BUILDS the text.
FALLBACK = re.compile(r'=\s*\(.*get\(["\']content["\']\).*\)\s*(?:\.strip\(\))?\s*or\s*'
                      r'\(.*get\(["\']reasoning_content["\']\)')
# AND THE SECOND SHAPE, WHICH MY FIRST CHECKER MISSED: assigning the trace to a variable WITHOUT wrapping it in
# len(). Measuring a trace's length is a different act from reading it as an answer.
ASSIGNS_TRACE = re.compile(r'=\s*\(?[^\n]*get\(["\']reasoning_content["\']\)[^\n]*$')

# SECOND READERS THAT ARE DECLARED, WITH A REASON -- NOT AN EXEMPTION FROM THE RULING, BUT THE RECORD OF A
# DECISION, so the next one cannot appear without one. These two belong to the CHESS cabinet, which is STOOD
# DOWN with its numbers already published: changing its read NOW would change the semantics of a frozen
# instrument AFTER the fact. That is a decision for the Chair, not for me, so they are FLAGGED rather than
# silently fixed.
DECLARED_SECOND_READERS = {
    "arena.py": "the CHESS run harness -- frozen, stood down, numbers published. FLAGGED to the Chair.",
    "chess_game.py": "the CHESS game loop -- same instrument, same status. FLAGGED to the Chair.",
}

# measuring the trace's length is not scoring it, and the checker CARRIES the offender as its own control --
# a checker that flags itself for containing the pattern it tests for is a false positive, not a finding.
ALLOWED_TO_MENTION = {"answer_reader.py", "sokoban_probe.py", "cost_probe.py", "check_one_reader.py"}


def scan_text(name, text):
    """-> list of complaints. Pure, so the control can call it on a synthetic offender."""
    out = []
    if name == READER or name in ALLOWED_TO_MENTION:
        return out
    declared = name in DECLARED_SECOND_READERS
    if FALLBACK.search(text):
        out.append(f"{name}: BUILDS an answer by choosing between content and reasoning_content -- "
                   f"A SECOND READER OF RECORD"
                   f"{'  [DECLARED: ' + DECLARED_SECOND_READERS[name] + ']' if declared else ''}")
    else:
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#") or "len(" in s or '"""' in s or s.startswith("message["):
                continue
            if ASSIGNS_TRACE.search(s):
                out.append(f"{name}: READS the deliberation into a variable -- A SECOND READER OF RECORD"
                           f"{'  [DECLARED: ' + DECLARED_SECOND_READERS[name] + ']' if declared else ''}"
                           f"   line: {s[:70]}")
                break
    return out


def main():
    print("=" * 100)
    print("RULING 79 -- is there exactly one reader of record?")
    print("=" * 100)
    problems, flags = [], []
    files = sorted(f for f in os.listdir(HERE) if f.endswith(".py"))
    for f in files:
        try:
            text = open(os.path.join(HERE, f)).read()
        except OSError:
            continue
        for c in scan_text(f, text):
            (flags if "[DECLARED:" in c else problems).append(c)

    # every file whose JOB is to score an answer must import the reader
    for f in files:
        try:
            text = open(os.path.join(HERE, f)).read()
        except OSError:
            continue
        if f in ALLOWED_TO_MENTION or f.startswith("test_") or f.startswith("check_"):
            continue
        if "L.score(" in text or re.search(r"^def score\(", text, re.M):
            if "answer_reader" not in text:
                problems.append(f"{f}: SCORES an answer but does NOT import answer_reader -- "
                                f"IT HAS ITS OWN READER, which is the defect the ruling names")

    # ---- THE CONTROL. The checker must FIRE on a known offender.
    offender = 'txt = (m.get("content") or "").strip() or (m.get("reasoning_content") or "").strip()'
    control_fired = bool(scan_text("__control__.py", offender))
    print(f"\n  CONTROL -- does this checker fire on the pattern that caused the retraction? "
          f"{'YES' if control_fired else 'NO'}")
    if not control_fired:
        problems.append("THE CHECKER DOES NOT FIRE ON THE KNOWN OFFENDER -- so a clean result means nothing")
    # and the second shape, which the FIRST version of this checker missed
    control2 = bool(scan_text("__control2__.py", 'reasoning = m.get("reasoning_content") or ""'))
    print(f"  CONTROL -- does it fire on the shape that IT ITSELF missed first time? "
          f"{'YES' if control2 else 'NO'}")
    if not control2:
        problems.append("THE CHECKER MISSES THE SECOND SHAPE -- the one sokoban_run.py actually had")

    print(f"\n  files scanned      {len(files)}")
    print()
    if flags:
        print("  DECLARED SECOND READERS -- flagged, not silently exempt:")
        for fl in flags:
            print(f"    {fl}")
        print()
    if problems:
        print("  *** RULING 79 VIOLATED ***")
        for p in problems:
            print(f"    {p}")
        print()
        print("  A SECOND READER FAILS SILENTLY IN THE DIRECTION OF A BETTER-LOOKING NUMBER. That is not a")
        print("  style objection -- it is the mechanism by which a 1/5 was published as a 5/5.")
        return 1
    print("  ONE READER OF RECORD, AND EVERY SCORER IMPORTS IT. Ruling 79 holds -- with the declared chess")
    print("  hold-outs flagged above for the Chair rather than fixed behind her back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
