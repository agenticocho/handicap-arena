#!/usr/bin/env python3
"""THE COORDINATE ARM AND THE ENTRANT SCOPE SENTENCE, MEASURED WITHOUT A MODEL.

Built for card `t_8edaaf2d` under `PREREG_mc_entrant_identity.md`, which was committed BEFORE the two
edits this probe exists to check. **It loads no model, takes no lease, writes no record, and touches
nothing at a published coordinate** -- it reads the 22 coordinate files, the driver's source, and the
decision in `main`, and it reports what the runner would do with them.

WHAT IT ASKS, and it asks the runner's own question with the runner's own functions:

  1  THE PLACEMENT RULE. `missile_command_population.py`'s branch for the arm of record decides, for each
     published coordinate, whether a re-run ADOPTS the record already there or records `never_started`:

         mine   = missile_command_run.run_identity()            (under the arm the runner PLACES)
         theirs = missile_command_run.carried_identity(record)  (as the record on disk carries it)
         adoptable  <=>  no member of IDENTITY_IN_RECORD differs

     It is asked TWICE -- once under the arm the RUNNER actually takes (`COORD_ARM`, the value under test)
     and once under the OTHER arm -- and the two answers are the controls: the arms must DISAGREE on every
     cell (they differ by a member of the identity triple, so agreement means this probe cannot see the
     arm), and the disagreement must be carried by `legend_digest` ALONE (any other member appearing in a
     diff is a live reading that moved, and shows as itself rather than being absorbed into the arm).

     The differing keys are REPORTED PER CELL, not collapsed to a count: `server_binary_digest` is a live
     reading of a binary, and the box this runs on flips ~1 bit per 0.3-1.5 GB of data in motion, so a
     corrupt reading must show up as itself and not be mistaken for the arm.

  2  THE TRANSCRIPTION. `entrant_digest_scope` is a string literal inside `run()`, so it is read OUT OF THE
     SOURCE BY AST rather than by importing. It is compared, whitespace-normalised, with the text fixed in
     `DECISION_entrant_identity.md` section 3(a) -- a transcription is checkable, and the only thing this
     comparison forgives is line wrapping and the code block's own two-space indent.

  3  WHAT SECTION 3(a) SAYS DOES NOT MOVE: the field's name and its computation. Every `entrant_digest`
     entry in the driver must still be `file_digest(entrant)`, `entrant_digest_scope` must occur exactly
     once, and the sentence the decision calls measured false must be gone.

USAGE (under the guard, never a bare python3):

    scripts/run_guarded.sh mc-entrant-id-probe "$PWD" /usr/bin/python3 scripts/probe_coord_arm_adoption.py

EXIT 0 the probe ran and every one of its checks passed · 3 the scope sentence is not the decision's ·
     4 a control or a check failed (the arms agree, a member other than the arm moved, the runner's arm is
     not the declaration's, or the field's computation moved) · 5 an input it has to read is missing.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # the cabinet tree
sys.path.insert(0, HERE)

import missile_command_run as R                                            # noqa: E402
import missile_command_population as P                                     # noqa: E402

DRIVER = os.path.join(HERE, "missile_command_run.py")
DECISION_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                "ocho_arena", "DECISION_entrant_identity.md")


def d16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


# ------------------------------------------------------------------ 1. the placement rule, both arms
def coordinates():
    """-> [(coordinate path, entrant label)] for the PER-CELL records, by the field's own rule.

    The run artifacts in probes/ (MC_POPULATION_*, MC_LEGEND_AB, MC_FIELD_*_ARCHIVE) are not cells: a cell
    is `MC_<entrant>_<level>.json` for one of this cabinet's two states. DERIVED, never typed.
    """
    levels = tuple(os.path.basename(lv).replace(".txt", "") for lv in P.LEVELS)
    out = []
    for path in sorted(__import__("glob").glob(os.path.join(HERE, "probes", "MC_*.json"))):
        stem = os.path.basename(path)[len("MC_"):-len(".json")]
        for lv in levels:
            if stem.endswith("_" + lv):
                out.append((path, stem[:-len(lv) - 1]))
                break
    return out


def driver_strings():
    """-> (scope literal, [every entry whose key is `entrant_digest`]) read from the source, not imported."""
    src = open(DRIVER, encoding="utf-8").read()
    scopes, digests = [], []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            if k.value == "entrant_digest_scope":
                scopes.append(v)
            elif k.value == "entrant_digest":
                digests.append((v, ast.unparse(v) if hasattr(ast, "unparse") else "?"))
    return scopes, digests, src


def decision_text(path):
    """-> the body of the fenced block in `DECISION_entrant_identity.md` 3(a) that starts `entrant_digest`."""
    src = open(path, encoding="utf-8").read()
    for block in re.findall(r"```\n(.*?)```", src, re.S):
        lines = block.rstrip().splitlines()
        if lines and lines[0].strip() == "entrant_digest":
            return "\n".join(lines[1:])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", default=DECISION_DEFAULT)
    a = ap.parse_args()

    print("=" * 100)
    print("THE COORDINATE ARM AND THE ENTRANT SCOPE SENTENCE -- MEASURED WITHOUT A MODEL")
    print("=" * 100)
    print(f"  cabinet tree      {HERE}")
    print(f"  driver            {os.path.relpath(DRIVER, HERE)}  digest {d16(DRIVER)}")
    print(f"  declaration       {os.path.relpath(R.DECLARATION_FILE, HERE)}  digest "
          f"{d16(R.DECLARATION_FILE)}   legend_arm {R.DECL['legend_arm']!r}")
    print(f"  the runner takes  COORD_ARM = {P.COORD_ARM!r}      (the value under test)")

    cells = coordinates()
    if not cells:
        print("  REFUSED: no per-cell coordinate found -- nothing to measure.")
        return 5

    # ONE reading of a binary per binary, shared by both arms, so the two arms differ by the legend and
    # nothing else -- and the read is REPORTED, because on this box a live reading is a reading.
    digests = {}
    for _, label in cells:
        served = R.FORK_LLAMA if R.ternary_entrant(os.path.join(R.MODELS, label + ".gguf")) else R.LLAMA
        digests.setdefault(served, R.file_digest(served))
    print(f"  binaries read     { {os.path.basename(k): v for k, v in digests.items()} }")

    # ---- BOTH ARMS. The value under test is the runner's; the other arm is the counterfactual, and the
    # CONTROL is not "the other arm refuses" (it adopts, when the declaration names it -- that is the point
    # of this card). The control is that the two arms DISAGREE, and that the disagreement is carried by
    # `legend_digest` and by nothing else: any other member appearing in a diff is a live reading that moved
    # (this box flips bits in data in motion) and must be seen as itself.
    arms = sorted(set(P.ARMS))
    if P.COORD_ARM not in arms:
        print(f"  REFUSED: COORD_ARM {P.COORD_ARM!r} is not one of the runner's arms {arms}.")
        return 4
    other = next(arm for arm in arms if arm != P.COORD_ARM)

    rc = 0
    results = {}
    for label, arm in (("UNDER TEST (the runner's own arm)", P.COORD_ARM),
                       ("COUNTERFACTUAL (the other arm)", other)):
        rows = []
        R.LEGEND_ARM = arm
        for path, cell in cells:
            served = R.FORK_LLAMA if R.ternary_entrant(os.path.join(R.MODELS, cell + ".gguf")) else R.LLAMA
            saved, R.server_binary_digest = R.server_binary_digest, (lambda p=served: digests[p])
            try:
                rec = json.load(open(path))
                mine, theirs = R.run_identity(), R.carried_identity(rec)
            finally:
                R.server_binary_digest = saved
            diff = [k for k in R.IDENTITY_IN_RECORD if theirs.get(k) != mine[k]]
            rows.append({"cell": os.path.basename(path), "adoptable": not diff, "diff": diff})
        results[arm] = rows
        ok = sum(1 for r in rows if r["adoptable"])
        print(f"\n  {label}: arm {arm!r} (legend_digest {R.legend_digest(arm)})")
        print(f"    ADOPTED {ok}/{len(rows)}   never_started {len(rows) - ok}/{len(rows)}")
        keys = sorted({k for r in rows for k in r["diff"]})
        print(f"    differing identity keys across the cells: {keys if keys else 'NONE'}")
        for r in rows:
            if not r["adoptable"]:
                print(f"      never_started  {r['cell']:70s} diff {r['diff']}")

    # CONTROL 1 -- no identity member other than the arm's own digest may move between a record and a run.
    stray = [(r["cell"], arm, r["diff"]) for arm in arms for r in results[arm]
             if set(r["diff"]) - {"legend_digest"}]
    print(f"\n  CONTROL 1  no identity member but `legend_digest` moves: "
          f"{'PASS' if not stray else 'FAIL'}")
    if stray:
        print(f"    a reading moved somewhere other than the arm -- this is NOT a disagreement about the arm: "
              f"{stray[:4]}")
        rc = 4

    # CONTROL 2 -- the two arms must reach OPPOSITE verdicts on every cell, because they differ by a member
    # of the identity triple. Same verdict under both arms means the probe cannot see the arm at all.
    same = [results[P.COORD_ARM][i]["cell"] for i in range(len(cells))
            if results[P.COORD_ARM][i]["adoptable"] == results[other][i]["adoptable"]]
    print(f"  CONTROL 2  the two arms DISAGREE on every cell: {'PASS' if not same else 'FAIL'}"
          f"   (agree on {len(same)}/{len(cells)}: {same[:4]})")
    if same:
        print("    both arms refuse, or both adopt: the arm is not the variable in this probe.")
        rc = 4

    # CHECK 3 -- E1's own claim, stated as a check rather than left to be eyeballed in the dry-run.
    agrees = P.COORD_ARM == R.LEGEND_DEFAULT
    print(f"  CHECK 3    the runner's coordinate arm IS the arm the declaration names "
          f"({'PASS' if agrees else 'FAIL'}): {P.COORD_ARM!r} against legend_arm {R.LEGEND_DEFAULT!r}")
    if not agrees:
        print("    THE COORDINATE ARM IS A SECOND COPY OF A DECISION THE DECLARATION OWNS -- this is the "
              "defect card t_8edaaf2d exists to remove.")
        rc = 4

    # ---- the transcription
    scopes, digest_entries, src = driver_strings()
    dec_path = os.path.abspath(a.decision)
    if not os.path.exists(dec_path):
        print(f"  REFUSED: the decision is not readable at {dec_path} -- the text has no source to be "
              f"checked against, and an unchecked transcription is not a transcription.")
        return 5
    fixed = decision_text(dec_path)
    if fixed is None:
        print(f"  REFUSED: no fenced block starting `entrant_digest` in {dec_path} -- section 3(a) is not "
              f"where this probe was told it would be.")
        return 5

    print(f"\n  3(a) THE TRANSCRIPTION   (decision {os.path.relpath(dec_path, HERE)}  digest "
          f"{d16(dec_path)})")
    if len(scopes) != 1:
        print(f"    FAIL  `entrant_digest_scope` occurs {len(scopes)} time(s) in the driver; expected 1.")
        rc = 4
        scope_text = ""
    else:
        try:
            scope_text = ast.literal_eval(scopes[0])
        except ValueError:
            print("    FAIL  `entrant_digest_scope` is not a literal this probe can read.")
            return 4
        same = squash(scope_text) == squash(fixed)
        print(f"    {'PASS' if same else 'FAIL'}  the driver's sentence IS the sentence 3(a) fixed "
              f"({'word for word' if same else 'THE TEXT DIFFERS'})")
        if not same:
            a_, b_ = squash(scope_text), squash(fixed)
            i = next((n for n in range(min(len(a_), len(b_))) if a_[n] != b_[n]), min(len(a_), len(b_)))
            print(f"          driver [{a_[i:i + 120]!r}]")
            print(f"          fixed  [{b_[i:i + 120]!r}]")
            rc = 3
        dead = "THE ENTRANT IS THE SUBJECT OF THE MEASUREMENT"
        print(f"    {'PASS' if dead not in scope_text else 'FAIL'}  the sentence the decision measured FALSE "
              f"is not carried: {dead!r}")

    print(f"\n  3(d) WHAT THE FIELD KEEPS -- its name and its computation")
    keep = [(ast.unparse(v) if hasattr(ast, "unparse") else "?") for v, _ in digest_entries]
    print(f"    `entrant_digest` entries in the driver: {len(keep)} {keep}")
    if [k for k in keep if k != "file_digest(entrant)"]:
        print(f"    FAIL  an `entrant_digest` entry is no longer file_digest(entrant) -- the VALUE moved, and "
              f"3(a) says it does not.")
        rc = 4
    else:
        print(f"    PASS  every one still computes file_digest(entrant) -- the field's value is untouched")

    print("\n" + "=" * 100)
    test_arm = results[P.COORD_ARM]
    print(f"  THE VALUE UNDER TEST  COORD_ARM = {P.COORD_ARM!r}  ->  adopts "
          f"{sum(1 for r in test_arm if r['adoptable'])}/{len(test_arm)} of the published coordinates")
    print(f"  VERDICT {'PASS' if rc == 0 else f'FAIL (rc {rc})'}")
    print("=" * 100)
    return rc


if __name__ == "__main__":
    sys.exit(main())
