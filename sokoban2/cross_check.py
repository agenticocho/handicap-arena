#!/usr/bin/env python3
# cross_check.py -- BEHAVIOURAL diff: the frozen sokoban.py vs sokoban2.py.
#
# Run BOTH implementations on IDENTICAL streams and compare the numbers.  This
# uses only the public signature recorded in sokoban/MANIFEST.txt and
# PROPOSED-FIX-line348.diff -- `play(text, toks)` returning
# {solved, moves, attempted, blocked, unrecognised, final_board, ...}.
# Nothing here reads the other implementation's source.
#
# The point is not "who is right".  It is to find the streams on which two
# honest readings of the same frozen contract produce DIFFERENT numbers -- because
# those are the places the contract does not speak, and they are invisible from
# inside either implementation.

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(REPO, "sokoban2")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "sokoban"))

import sokoban as frozen                                   # noqa: E402
import sokoban2 as mine                                    # noqa: E402

LEVELS = {
    "01": open(os.path.join(REPO, "sokoban", "levels",
                            "01_one_push.txt")).read(),
    "02": open(os.path.join(REPO, "sokoban", "levels",
                            "02_two_boxes.txt")).read(),
    "03": open(os.path.join(HERE, "levels",
                            "03_the_corner_waiting.txt")).read(),
}

#: Streams chosen to probe the places the contract does not speak.
STREAMS = [
    ("empty", []),
    ("one right", ["R"]),
    ("optimal 01", ["R"]),
    ("optimal 02", list("DDRRRRULLURR")),
    ("optimal 03", list("RRULLL")),
    ("lower case", ["r"]),
    ("padded", ["  R  "]),
    ("wall bump x5", ["U"] * 5),
    ("WASD", ["W", "A", "S", "D"]),
    ("two letters", ["UR"]),
    ("RESIGN", ["RESIGN"]),
    ("resign lower", ["resign"]),
    ("give up", ["GIVE UP"]),
    ("give up punct", ["GIVE UP."]),
    ("natural abstention", ["I give up, there is no way to finish this."]),
    ("prose", ["I think you should push the crate right"]),
    ("json", ['{"move": "R"}']),
    ("fenced", ["```R```"]),
    ("after solve", ["R", "R", "R"]),
    ("after resign", ["RESIGN", "R"]),
    ("blank", [""]),
    ("multi-line", ["R\nR"]),
    ("digit", ["1"]),
    ("corner death 03", ["U", "R", "L", "D", "U", "R"]),
    ("mixed", ["U", "W", "R", "RESIGN", "x", "", "RD"]),
]

FIELDS = ("solved", "moves", "attempted", "blocked")


def run_frozen(text, toks):
    r = frozen.play(text, list(toks))
    return {k: r.get(k) for k in FIELDS}


def run_mine(text, toks):
    lvl = mine.parse_level(text, "x")
    r = mine.play(lvl, list(toks))
    return {k: r.get(k) for k in FIELDS}


def main():
    agree = 0
    disagree = []
    print("CROSS-CHECK -- frozen sokoban.py vs sokoban2.py, identical streams")
    print("  fields compared: %s" % ", ".join(FIELDS))
    print()
    for name, toks in STREAMS:
        for tag, text in sorted(LEVELS.items()):
            try:
                a = run_frozen(text, toks)
            except Exception as exc:                       # noqa: BLE001
                a = {"EXCEPTION": "%s: %s" % (type(exc).__name__, exc)}
            try:
                b = run_mine(text, toks)
            except Exception as exc:                       # noqa: BLE001
                b = {"EXCEPTION": "%s: %s" % (type(exc).__name__, exc)}
            if a == b:
                agree += 1
            else:
                disagree.append((tag, name, a, b))
    print("  streams x levels compared : %d" % (len(STREAMS) * len(LEVELS)))
    print("  agree                     : %d" % agree)
    print("  DISAGREE                  : %d" % len(disagree))
    print()
    for tag, name, a, b in disagree:
        print("  -- level %s / %r" % (tag, name))
        print("     frozen : %s" % json.dumps(a, sort_keys=True))
        print("     mine   : %s" % json.dumps(b, sort_keys=True))
    print()
    return 0 if not disagree else 1


if __name__ == "__main__":
    sys.exit(main())
