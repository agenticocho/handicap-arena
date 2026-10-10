#!/usr/bin/env python3
"""EXTRACT THE FIELD NAMES FROM THE CODE -- EXACTLY, BY FINDING THE DICT LITERAL THAT OWNS THEM.

MY FIRST VERSION TOOK A FIXED 4000-CHARACTER WINDOW after a marker, WHICH BLED ACROSS NEIGHBOURING DICTS:
the list it printed for the CONFIG block was actually the CELL record's keys. A FIELD-NAME EXTRACTOR THAT
BLEEDS IS A FALSE-VERIFICATION MACHINE -- it produces a list that looks checked and is wrong, which is the
exact defect this exercise exists to prevent.

So the dict is found with `ast`: parse the file, walk every Dict node, and identify each by a DISTINGUISHING
KEY it must contain. EXACT, AND THE IDENTIFICATION IS CHECKABLE.

    python3 _source_list.py
"""
import ast
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# file -> (label, the dict must contain ALL of these keys, and it is identified by them)
TARGETS = [
    ("sokoban.py", "CELL counters  (play())", ("solved", "gave_up_at", "not_an_action")),
    ("sokoban_run.py", "CELL record    (run())", ("entrant", "final_screen", "dead_end")),
    ("sokoban_run.py", "CONFIG block", ("reasoning_declared", "reasoning_argv", "max_tokens_ceiling")),
    ("sokoban_run.py", "REASONING PROBE", ("disagrees_with_config", "observed_answer_shape")),
    ("sokoban_run.py", "BUDGET SIGNATURE", ("all_turns_capped", "turns_that_hit_the_ceiling")),
    ("sokoban_run.py", "DEAD-END cell", ("no_solution_from_here", "proof_kind")),
    ("sokoban_batch.py", "RUN record     (meta)", ("simulator_digest", "host", "freeze")),
    ("sokoban_deadend.py", "DEAD-END map", ("fatal_opening_moves", "safe_opening_moves")),
]


def find_dict_keys(path, must_have):
    """-> sorted string keys of the ONE dict literal containing all of `must_have`, or None.

    `None` MEANS NOT FOUND AND IS REPORTED AS SUCH. A miss must not silently print an empty list, because
    an empty list reads as "this record has no fields" rather than "the extractor did not find it".
    """
    try:
        tree = ast.parse(open(path).read())
    except (OSError, SyntaxError):
        return None
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        ks = [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        if all(m in ks for m in must_have):
            hits.append(ks)
    if not hits:
        return None
    # if several match, the one with the MOST keys is the fuller record; say how many matched.
    hits.sort(key=len, reverse=True)
    return hits[0], len(hits)


print("=" * 100)
print("FIELD NAMES -- EXACTLY, FROM THE DICT LITERAL THAT OWNS THEM")
print("=" * 100)
for f, label, must in TARGETS:
    got = find_dict_keys(os.path.join(HERE, f), must)
    print(f"\n  {label}   [{f}]")
    if got is None:
        print(f"    *** NOT FOUND -- the extractor looked for keys {must} and found no dict with all of "
              f"them. READ THE FILE. An empty list here would be a LIE. ***")
    else:
        ks, nmatch = got
        print(f"    keys ({len(ks)}){'  [' + str(nmatch) + ' dicts matched; showing the fullest]' if nmatch > 1 else ''}:")
        print(f"      {' '.join(sorted(ks))}")

print()
print("=" * 100)
print("AND EVERY DICT LITERAL IN EACH FILE, SO A MISS IS VISIBLE RATHER THAN ASSUMED")
print("=" * 100)
for f in ("sokoban.py", "sokoban_run.py", "sokoban_batch.py", "sokoban_deadend.py"):
    try:
        tree = ast.parse(open(os.path.join(HERE, f)).read())
    except (OSError, SyntaxError) as e:
        print(f"  {f}: {type(e).__name__}")
        continue
    dicts = [n for n in ast.walk(tree) if isinstance(n, ast.Dict)]
    print(f"  {f:24s} {len(dicts)} dict literal(s) at lines "
          f"{sorted({n.lineno for n in dicts})}")
