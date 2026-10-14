#!/usr/bin/env python3
"""Write the ratified SUPERSESSION records for the historical game-name violations.

Ratified by Tiel with two conditions, and both are load-bearing rather than stylistic.

1. THE RECORD MAY NOT BE EXCULPATORY. The first draft would have said of each bundle, "per
   GAME_CONTRACT.md it is not a game claim". THAT IS FALSE BY THE CONTRACT'S OWN STANDARD: a game name
   with no state behind it IS the violation, and on an INSTRUMENT it is precisely the referee in a
   costume. An annotation denying it lets the record off for something the record owns. So:

     A NOTE BESIDE AN ARTIFACT MAY ADD INFORMATION. IT MAY NOT CHANGE THE ARTIFACT'S STANDING.
     SUPERSEDED IS NOT THE SAME AS COMPLIANT -- and a record that upgrades an artifact's status is a
     rewrite wearing a footnote.

2. THE CHECK MUST STILL BE ABLE TO FAIL. Teaching the check to SKIP these rounds would make a count of 0
   mean "none new" OR "none ever", with no way to distinguish. Instead the check counts NEW and HISTORICAL
   separately and gates the exit code on NEW, which must be 0.

AND IT IS NOT A MIGRATION: nothing moved. The bundle is unchanged; the annotation is new. So the record is
named for what it does -- supersession -- and it records its own authorship, because a record added after
the fact must say so: written AFTER the run, when, and from which commit.

Records live in `results/supersessions/`, a SUBDIRECTORY, so they can never be counted as bundles by a
sweep of `results/*.json`. That is the `EXERCISE_` collision caught before creating it.

Run: annotate_superseded.py --commit <sha> [--dry-run]
"""
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # root scripts: already sys.path[0]; scripts/*: required
import cabinet_root as _root


def scope(pattern="*.json"):
    """[(kind, base, [paths])] over the DECLARED domain, entry by entry. No pattern is widened,
    no directory joins by existing."""
    rows = []
    for kind, base in _root.domain():
        rows.append((kind, base, sorted(glob.glob(os.path.join(base, pattern)))))
    return rows


def print_scope(rows, pattern):
    # THE SCOPE IS PRINTED WITH THE COUNT IT CONTRIBUTED: a count without its scope is not a count.
    for kind, base, hits in rows:
        print(f"  scope  {kind:16} {len(hits):4} {pattern}  {base}")

# THE WRITE SCOPE, RESOLVED ONCE (AC5): ONE PATH, OR A REFUSAL -- results_dir() refuses with a
# SystemExit and the refusal PROPAGATES, because a caught refusal is a fallback with better manners.
# A run with no declared root exits non-zero, prints the remedy, and writes NOTHING.
OUT = os.path.join(_root.results_dir(), "supersessions")

STATUS = "SUPERSEDED -- NOT COMPLIANT"

VIOLATION = (
    "The round records in this bundle name a game and carry no state for it. That IS the violation "
    "GAME_CONTRACT.md names: a game name with no state behind it is a label with nothing behind it, and "
    "on an INSTRUMENT it is the referee in a costume. This bundle was written before the fix, when the "
    "task files declared `metaphor` and arena.py copied that field into every round record."
)

EFFECT = (
    "NONE. This violation REMAINS COUNTED, as HISTORICAL. The record does not excuse it, downgrade it or "
    "upgrade the artifact -- it only stops a reader from mistaking history for the present."
)


def stem_of(bundle_filename):
    """`X_cardv4_...json` -> `X_cardv4_...`, so the record is `X_cardv4_....json` and not `....json.json`.

    A FILENAME IS NOT A STEM. The first version appended `.json` to the full filename, which produces a
    name asserting that the bundle's extension is part of its identifier -- and the checker used the same
    wrong rule, so it agreed with the generator and would have kept agreeing while both were wrong. The
    two are now forced to share this function's rule, in the same repo, one import apart.
    """
    return bundle_filename[:-len(".json")] if bundle_filename.endswith(".json") else bundle_filename


def bundles_with_game_names():
    """The bundles the check reports as claiming a game with no state."""
    sys.path.insert(0, HERE)
    import test_game_states as tgs  # noqa: E402
    names = []
    _rows = scope("*.json")
    print_scope(_rows, "*.json")
    for p in [p for _k, _b, hits in _rows for p in hits]:
        for f in tgs.check_bundle(p):
            if "claims game" in f:
                names.append(os.path.basename(p))
                break
    return names


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    commit = ""
    if "--commit" in args:
        commit = args[args.index("--commit") + 1]
    if not commit:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
                                capture_output=True, text=True).stdout.strip()
    names = bundles_with_game_names()
    print(f"  {len(names)} bundle(s) claim a game with no state")
    if dry:
        print("  --dry-run: nothing written")
        return 0

    os.makedirs(OUT, exist_ok=True)
    written = 0
    for name in names:
        # THE STEM, NOT THE FILENAME. The first version appended `.json` to the bundle's FULL filename,
        # producing `X.json.json` -- a name that says the bundle's extension is part of its identifier.
        # That is the stand-in family again: a filename treated as a stem. The record is named for the
        # bundle it annotates, so the stem is the identifier.
        rec = {
            "record": "supersession",
            "written_after_the_run": True,
            "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "written_from_commit": commit,
            "subject": name,
            "status": STATUS,
            "violation": VIOLATION,
            "effect_on_standing": EFFECT,
            "superseding_change": commit,
        }
        with open(os.path.join(OUT, stem_of(name) + ".json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
            fh.write("\n")
        written += 1
    print(f"  wrote {written} SUPERSESSION record(s) to results/supersessions/")
    print(f"  status on every one: {STATUS}")
    print("  and every one records that it was written AFTER the run, when, and from which commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
