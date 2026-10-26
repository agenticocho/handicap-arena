#!/usr/bin/env python3
"""THE ENFORCER FOR THE REPLAY RULE -- and the mutation test that proves the enforcer can fire.

WHAT IT ENFORCES
    Every row that claims a solve must carry a plan that `sokoban_replay.py` -- a SEPARATE process -- replays to
    a solved board. The claim and the replay are two different claims, and this file is where they are compared:

        row says solved: true   ->  the verifier must return VERIFIED (rc 0)
        row says solved: false  ->  the verifier must NOT return VERIFIED, or the row is worse than it says

    It exits 1 on any disagreement. It never edits a row: the historical corpus is certified by RE-EXECUTION and
    the files stay byte-identical, because a rewritten row would destroy the evidence that the claim was ever
    made.

WHY THE MUTATIONS ARE THE POINT
    A check that has only ever passed is indistinguishable from a check that cannot fail. The three mutations
    the card names are run here as CONTROLS, each asserting a NON-ZERO exit from the separate process:

        M1  a plan STEP mutated            -> rc 3 REFUSED
        M2  a BOX POSITION mutated         -> rc 3 REFUSED   (the level is read from disk, never from the row)
        M3  a CLAIMED SOLVE changed        -> rc 3 from the verifier AND rc 1 from this enforcer

    ...and the positive direction is asserted too (a verifier that always refuses is as useless as one that
    always accepts): a known-good plan on each of the three frozen levels must VERIFY. The known-good plans are
    declared here WITH PROVENANCE, because the three are not equally strong:

        01  `R`              trivial: the level is one push
        02  `RRRRDLLLDRRR`   FROZEN in `verify_levels.py` before any solver in this tree existed
        03  `RULDLU`         found by `sokoban_solver.py`; its 6-move optimality is proven there by complete
                             enumeration, and by an independent second enumerator

    python3 check_sokoban_replay.py                  # controls + the whole corpus sweep
    python3 check_sokoban_replay.py --corpus probes/controls --json
rc 0  every claim matches its replay and every control fired / did not fire as declared
rc 1  a claim disagrees with its replay, or a control did not fire
rc 2  the checker could not run (a missing file is a MISS, never a pass)
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFIER = os.path.join(HERE, "sokoban_replay.py")

# DECLARED HERE, WITH PROVENANCE. `sokoban_solver.py`'s READ_CONTROL is NOT imported: a control that imports the
# thing it checks is a restatement. These three are checked against the level files by the verifier itself.
KNOWN_GOOD = [
    ("01_one_push", "R", 1, "trivial: the level is one push"),
    ("02_two_boxes", "RRRRDLLLDRRR", 12, "FROZEN in verify_levels.py before any solver here existed"),
    ("03_the_corner_waiting", "RULDLU", 6, "found by sokoban_solver.py; optimality proven there by enumeration"),
]

# M2 mutates a level by moving ONE box one cell, and the harness then CLASSIFIES every mutation instead of
# asserting that all of them are caught. That distinction was measured, not assumed: the first fixture this file
# carried moved level 02's lower box from (3,3) to (3,4) and the 12-move plan STILL SOLVED IT -- the box needed
# two pushes and the plan's third push is now blocked, so it lands on the target anyway. A mutation the plan
# survives is not a control; it is a survivor, and it is REPORTED rather than swapped for one that fires.
BOX_MUTATION_PLANS = [
    ("01_one_push", "R"),
    ("02_two_boxes", "RRRRDLLLDRRR"),
    ("03_the_corner_waiting", "RULDLU"),
]

# WHETHER A LEVEL ADMITS A BOX MUTATION THAT BREAKS ITS PLAN IS A PROPERTY OF THE LEVEL, NOT OF THE VERIFIER, and
# it is declared here so that a mutation that stops firing is noticed while a mutation that CANNOT fire is not
# demanded. Level 01 is three cells wide: the box's only free neighbour is the target itself, so moving the box
# one cell either puts it ON the target (the level is solved before the plan starts, and `R` keeps it solved) or
# is impossible. That is measured, below, not asserted.
M2_EXPECT_REFUSAL = {"01_one_push": False, "02_two_boxes": True, "03_the_corner_waiting": True}
M2_WHY_NO_REFUSAL = {
    "01_one_push": "the box has exactly one free neighbour and it is the target: a one-cell box move cannot "
                   "make `R` fail, it can only make the level already solved",
}


def box_mutations(text):
    """Every one-cell move of every box, as a level that is STILL A LEVEL.

    THE TARGET UNDER A BOX IS PART OF THE LEVEL: a box written onto a `.` must be `*`, not `$`. My first writer
    wrote `$` and produced a level with no targets -- refused as NOT_A_LEVEL, which would have been a control
    that fired for the wrong reason and a mutation that measured the parser instead of the plan.
    -> list of (src, dst, mutated_text)
    """
    lines = [list(ln) for ln in text.splitlines()]
    out = []
    for r, row in enumerate(lines):
        for c, ch in enumerate(row):
            if ch not in ("$", "*"):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                r1, c1 = r + dr, c + dc
                if not (0 <= r1 < len(lines) and 0 <= c1 < len(lines[r1])):
                    continue
                if lines[r1][c1] not in (" ", "."):
                    continue
                grid = [list(x) for x in lines]
                grid[r1][c1] = "*" if lines[r1][c1] == "." else "$"
                grid[r][c] = "." if ch == "*" else " "
                out.append(((r, c), (r1, c1), "\n".join("".join(x) for x in grid) + "\n"))
    return out



def run_verifier(args, env_extra=None, root=HERE):
    """ALWAYS A SUBPROCESS. A verdict this checker computed in-process would be the same process asserting its
    own agreement, which is the defect the whole card is about."""
    env = dict(os.environ)
    env.pop("SOKOBAN_REPLAY_FAULT", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, VERIFIER] + args + ["--root", root],
                       capture_output=True, text=True, env=env, timeout=300)
    doc = None
    if "--json" in args:
        try:
            doc = json.loads(p.stdout)
        except ValueError:
            doc = None
    return p.returncode, doc, (p.stdout + p.stderr)


def verifier_sha():
    import hashlib
    with open(VERIFIER, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ----------------------------------------------------------------------------------------------- the controls
class Controls:
    def __init__(self):
        self.rows = []

    def ck(self, name, got, want, detail=""):
        ok = got == want
        self.rows.append({"control": name, "got": got, "want": want, "pass": ok, "detail": detail})
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
        if detail:
            print(f"          {detail}")
        return ok


def controls(c: Controls, root, scan_dirs):
    tmp = tempfile.mkdtemp(prefix="sokoban-replay-", dir=os.environ.get("TMPDIR") or None)
    try:
        # ---- C0 POSITIVE DIRECTION: one known-good plan on each level
        print("\n[C0] THE POSITIVE DIRECTION -- a plan that DOES solve must VERIFY, on all three levels")
        for level, plan, moves, why in KNOWN_GOOD:
            rc, doc, out = run_verifier(["--level", os.path.join(root, "levels", level + ".txt"),
                                         "--plan", plan, "--json"], root=root)
            c.ck(f"{level}: {plan} ({len(plan)} moves) VERIFIES", (rc, doc and doc.get("moves"),
                                                                  doc and doc.get("verdict")),
                 (0, moves, "VERIFIED"), why)

        # ---- C1 M1: a plan STEP mutated
        print("\n[C1] M1 -- A PLAN STEP MUTATED MUST BE REFUSED (non-zero exit)")
        for level, plan, moves, _why in KNOWN_GOOD:
            mutated = plan[:-1] + ("U" if plan[-1] != "U" else "D")
            rc, doc, out = run_verifier(["--level", os.path.join(root, "levels", level + ".txt"),
                                         "--plan", mutated, "--json"], root=root)
            c.ck(f"{level}: last step {plan[-1]!r}->{mutated[-1]!r} is REFUSED", (rc, doc and doc.get("verdict")),
                 (3, "REFUSED"), f"reason {doc and doc.get('refusal_reason')}")

        # ---- C2 M2: a BOX POSITION mutated -- the level is read from disk, not from the row
        print("\n[C2] M2 -- A BOX POSITION MUTATED: same plan, level re-read from disk. EVERY mutation is")
        print("     classified, and a mutation the plan SURVIVES is reported as a survivor, not asserted away.")
        for level, plan in BOX_MUTATION_PLANS:
            text = open(os.path.join(root, "levels", level + ".txt")).read()
            clean_rc, clean, _ = run_verifier(["--level", os.path.join(root, "levels", level + ".txt"),
                                               "--plan", plan, "--json"], root=root)
            refused, survivors, weird = [], [], []
            for src, dst, mutated in box_mutations(text):
                path = os.path.join(tmp, f"mut_{level}_{src[0]}{src[1]}_{dst[0]}{dst[1]}.txt")
                with open(path, "w") as fh:
                    fh.write(mutated)
                rc, doc, _ = run_verifier(["--level", path, "--plan", plan, "--json"], root=root)
                tag = (src, dst, rc, (doc or {}).get("verdict"), (doc or {}).get("refusal_reason"))
                if rc == 3 and tag[4] == "not_solved":
                    refused.append(tag)
                elif rc == 0:
                    survivors.append(tag)
                else:
                    weird.append(tag)
                os.unlink(path)
            c.ck(f"{level}: clean plan VERIFIES, and "
                 f"{'a mutated level is refused by the REPLAY' if M2_EXPECT_REFUSAL[level] else 'no mutated level can be refused -- declared in advance'}",
                 (clean_rc, bool(refused), len(weird)),
                 (0, M2_EXPECT_REFUSAL[level], 0),
                 f"{len(refused)} refused by replay, {len(survivors)} SURVIVED the mutation, "
                 f"{len(weird)} refused for another reason"
                 + (f" -- {M2_WHY_NO_REFUSAL[level]}" if not M2_EXPECT_REFUSAL[level] else ""))
            for src, dst, rc, verdict, reason in refused:
                print(f"        box {src}->{dst}: rc {rc} {verdict} ({reason})")
            for src, dst, rc, verdict, reason in survivors:
                print(f"        box {src}->{dst}: rc 0 {verdict} -- THE PLAN STILL SOLVES THIS LEVEL, so this "
                      f"mutation is a SURVIVOR and not a control")
            for src, dst, rc, verdict, reason in weird:
                print(f"        box {src}->{dst}: rc {rc} {verdict} ({reason}) -- NOT a refusal of the plan")

        # ---- C3 M3: a CLAIMED SOLVE changed, in BOTH directions
        print("\n[C3] M3 -- A CLAIMED SOLVE CHANGED MUST BE CAUGHT, in both directions")
        solved_rows = [p for p in rows_with_claim(scan_dirs, True)]
        unsolved_rows = [p for p in rows_with_claim(scan_dirs, False)]
        if solved_rows and unsolved_rows:
            good = solved_rows[0]
            row = json.load(open(good))
            # (i) a row that solves, relabelled `solved: false` -- the understatement
            under = os.path.join(tmp, "understated.json")
            json.dump(dict(row, solved=False), open(under, "w"))
            rc, doc, out = run_verifier(["--row", under, "--json"], root=root)
            c.ck("a VERIFIED plan relabelled solved=false is caught (claim_matches_verdict false)",
                 (rc, doc and doc.get("verdict"), doc and doc.get("claim_matches_verdict")), (0, "VERIFIED", False),
                 f"from {os.path.basename(good)}")
            # (ii) a row that does NOT solve, relabelled `solved: true` -- THE FALSE SUCCESS
            bad = unsolved_rows[0]
            brow = json.load(open(bad))
            over = os.path.join(tmp, "overstated.json")
            json.dump(dict(brow, solved=True), open(over, "w"))
            rc, doc, out = run_verifier(["--row", over, "--json"], root=root)
            c.ck("an UNSOLVED plan relabelled solved=true is REFUSED, and the reason names the claim",
                 (rc, doc and doc.get("verdict"), doc and doc.get("refusal_reason")),
                 (3, "REFUSED", "row_claims_solved_but_plan_does_not"),
                 f"from {os.path.basename(bad)}")
            # ...and the ENFORCER, not just the verifier, must exit non-zero over a corpus holding it
            corpus = os.path.join(tmp, "corpus")
            os.makedirs(corpus, exist_ok=True)
            shutil.copy(over, os.path.join(corpus, os.path.basename(over)))
            rc2, _ = sweep(corpus, root, quiet=True)
            c.ck("THE ENFORCER exits non-zero over a corpus holding a false success", rc2, 1)
            # ...and rc 0 over the same corpus with the claim restored, so rc 1 is caused by the mutation
            shutil.copy(bad, os.path.join(corpus, os.path.basename(over)))
            rc3, _ = sweep(corpus, root, quiet=True)
            c.ck("...and exits 0 over the identical corpus with the claim restored", rc3, 0)
        else:
            c.ck("corpus has at least one solved and one unsolved row to mutate", False, True)

        # ---- C4 the cross-check can fire
        print("\n[C4] THE CROSS-CHECK CAN FIRE -- a declared fault in this file's own transition must be caught")
        rc, doc, out = run_verifier(["--level", os.path.join(root, "levels", "01_one_push.txt"),
                                     "--plan", "R", "--json"],
                                    env_extra={"SOKOBAN_REPLAY_FAULT": "independent-step"}, root=root)
        c.ck("fault-injected replay is CROSS_CHECK_DISAGREES (rc 5), and says it was faulted",
             (rc, doc and doc.get("verdict"), bool(doc and doc.get("fault_injected"))), (5, "CROSS_CHECK_DISAGREES", True),
             "the two engines are compared PLY BY PLY; this is the control that proves it")
        rc, doc, _ = run_verifier(["--level", os.path.join(root, "levels", "01_one_push.txt"),
                                   "--plan", "R", "--json"], root=root)
        c.ck("...and the same plan with no fault injected is VERIFIED (the hook is the only difference)",
             (rc, doc and doc.get("fault_injected")), (0, None))

        # ---- C5 a plan with trailing plies, and a plan with no solve at all
        print("\n[C5] A PLAN PLUS NOISE IS NOT A PLAN; a level that is not a level has no verdict")
        rc, doc, _ = run_verifier(["--level", os.path.join(root, "levels", "01_one_push.txt"),
                                   "--plan", "RR", "--json"], root=root)
        c.ck("`RR` on level 01 is REFUSED as solved_before_the_plan_ended",
             (rc, doc and doc.get("refusal_reason")), (3, "solved_before_the_plan_ended"))
        # A RESIGNATION IS A TOKEN STREAM, NOT A LETTER STRING -- so this control goes through a ROW. `--plan`
        # splits into characters by design; feeding it `RESIGN` would test the trailing rule instead, which is
        # exactly the kind of control that passes for the wrong reason.
        resign = os.path.join(tmp, "resign.json")
        json.dump({"entrant": "control", "level": "01_one_push", "solved": True,
                   "turns": [{"token": "RESIGN"}]}, open(resign, "w"))
        rc, doc, _ = run_verifier(["--row", resign, "--json"], root=root)
        c.ck("a row whose whole plan is `RESIGN` and which claims solved is REFUSED",
             (rc, doc and doc.get("refusal_reason")), (3, "row_claims_solved_but_plan_does_not"),
             f"replay ended {doc and doc.get('ended')!r}, solves_at_ply {doc and doc.get('solves_at_ply')}")
        resign2 = os.path.join(tmp, "resign_after.json")
        json.dump({"entrant": "control", "level": "01_one_push", "solved": True,
                   "turns": [{"token": "R"}, {"token": "RESIGN"}]}, open(resign2, "w"))
        rc, doc, _ = run_verifier(["--row", resign2, "--json"], root=root)
        c.ck("a plan that SOLVES and then resigns is REFUSED, and the reason names the resignation",
             (rc, doc and doc.get("refusal_reason")), (3, "plan_contains_a_give_up"))
        bad_level = os.path.join(tmp, "not_a_level.txt")
        open(bad_level, "w").write("#####\n#@..#\n#####\n")
        rc, doc, _ = run_verifier(["--level", bad_level, "--plan", "R", "--json"], root=root)
        c.ck("a level with no box is NOT_A_LEVEL (rc 2), not a refusal and not a verdict",
             (rc, doc and doc.get("verdict")), (2, "NOT_A_LEVEL"))

        # ---- C6 THE DRIVER'S OWN FUNCTION, not a copy of it. `solve_certificate()` is what `run()` calls on
        # every loaded cell; this exercises it against a real historical row WITHOUT a model, and then reads the
        # row it produces back through the verifier's `--row` path -- so "the row carries a verdict" is checked
        # as a round trip rather than asserted.
        print("\n[C6] THE DRIVER'S solve_certificate() -- the production function, on a real historical row")
        sys.path.insert(0, root)
        import sokoban as S                                                  # noqa: E402
        import sokoban_run as RUN                                            # noqa: E402
        solved_row = next(iter(rows_with_claim([os.path.join(root, "probes")], True)), None)
        if solved_row:
            row = json.load(open(solved_row))
            toks = [t.get("token") for t in row["turns"]]
            lvl = os.path.join(root, "levels", row["level"] + ".txt")
            base = S.play(open(lvl).read(), toks)
            cert = RUN.solve_certificate(base, lvl, toks)
            c.ck("a real solved row's certificate: solved, VERIFIED, and the plan is the row's own stream",
                 (cert["solved"], cert["replay"]["verdict"], cert["plan"]["tokens"], cert["solved_simulator_claim"],
                  cert["solved_downgraded_by_replay"]),
                 (True, "VERIFIED", toks, True, None),
                 f"from {os.path.basename(solved_row)}")
            prov = RUN.provenance_block()
            with open(os.path.join(root, "sokoban_run.py"), "rb") as fh:
                driver_sha = hashlib.sha256(fh.read()).hexdigest()
            c.ck("...and the provenance names the COMPUTE PATH and the DRIVER REVISION",
                 (prov["compute_path"], prov["driver_sha256"] == driver_sha,
                  prov["replay_verifier_sha256"] == verifier_sha(), bool(prov["driver_git_commit"])),
                 ("cpu", True, True, True),
                 f"driver {prov['driver_sha256'][:16]} at {prov['driver_git_commit_short']}, "
                 f"verifier {prov['replay_verifier_sha256'][:16]}")
            # THE ROUND TRIP: the blocks the driver writes are the blocks the enforcer can read.
            written = os.path.join(tmp, "row_as_written.json")
            json.dump(dict(row, **{k: cert[k] for k in ("plan", "replay")},
                           solved=cert["solved"], provenance=prov), open(written, "w"))
            rc2, doc, _ = run_verifier(["--row", written, "--json"], root=root)
            c.ck("...and the row AS WRITTEN round-trips through `--row` to the same verdict",
                 (rc2, doc and doc.get("verdict"), doc and doc.get("plan_source")), (0, "VERIFIED",
                                                                                    "plan.tokens (written by this "
                                                                                    "instrument)"))
            # THE FAIL-CLOSED GUARD: a simulator claim the replay refuses may not survive into the score.
            fake = dict(base, solved=True)
            cert2 = RUN.solve_certificate(fake, lvl, ["L"])
            c.ck("a simulator claim the replay REFUSES is downgraded, and `ended` may not still say solved",
                 (cert2["solved"], cert2["solved_simulator_claim"], cert2["ended"],
                  cert2["solved_downgraded_by_replay"]),
                 (False, True, "solved_unverified", "row_claims_solved_but_plan_does_not"))
        else:
            c.ck("corpus has a solved row to certify", False, True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------------------------------- the sweep
def rows_with_claim(dirs, solved):
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".json"):
                continue
            p = os.path.join(d, name)
            try:
                doc = json.load(open(p))
            except (OSError, ValueError):
                continue
            if isinstance(doc, dict) and doc.get("solved") is solved and (doc.get("turns") or doc.get("plan") or doc.get("tokens")):
                yield p


def sweep(corpus, root, quiet=False):
    """Every row in `corpus` that carries a plan is replayed by the SEPARATE verifier and compared with its own
    claim. -> (rc, table). rc 1 if any claim disagrees, or if any row claiming a solve has no plan at all."""
    table = []
    for name in sorted(os.listdir(corpus)):
        if not name.endswith(".json"):
            continue
        p = os.path.join(corpus, name)
        try:
            doc = json.load(open(p))
        except (OSError, ValueError):
            table.append({"row": name, "skipped": "unreadable"})
            continue
        if not isinstance(doc, dict) or "solved" not in doc:
            table.append({"row": name, "skipped": "not a cell record"})
            continue
        claimed = bool(doc.get("solved"))
        # A ROW WITH NO PLAN AT ALL IS A VIOLATION ONLY IF IT CLAIMS A SOLVE -- that is the rule the card states,
        # and it is checked here rather than inferred from the verifier's exit code, because "nothing to replay"
        # and "a replay that failed" are different findings and must not print the same way.
        has_plan = bool(doc.get("turns") or doc.get("plan") or doc.get("tokens"))
        if not has_plan:
            table.append({"row": name, "entrant": doc.get("entrant"), "level": doc.get("level"),
                          "claim_solved": doc.get("solved"), "verdict": "NO PLAN", "rc": None,
                          "claim_matches_verdict": not claimed,
                          "refusal_reason": "no_plan_to_replay" if claimed else None,
                          "reason": ("a row that claims a solve and carries no plan cannot support the claim"
                                     if claimed else "nothing claimed, nothing to replay")})
            continue
        rc, v, out = run_verifier(["--row", p, "--json"], root=root)
        row = {"row": name, "entrant": doc.get("entrant"), "level": doc.get("level"),
               "claim_solved": doc.get("solved"), "verdict": (v or {}).get("verdict"), "rc": rc,
               "claim_matches_verdict": (v or {}).get("claim_matches_verdict"),
               "plan": (v or {}).get("plan_actions"), "moves": (v or {}).get("moves"),
               "blocked": (v or {}).get("blocked"), "solves_at_ply": (v or {}).get("solves_at_ply"),
               "refusal_reason": (v or {}).get("refusal_reason"),
               "reason": (v or {}).get("refusal_detail"),
               "plan_source": (v or {}).get("plan_source")}
        if v is None:
            row["verdict"] = "NO VERDICT -- the verifier did not return JSON"
            row["reason"] = out[-400:]
        else:
            claimed = bool(doc.get("solved"))
            verified = row["verdict"] == "VERIFIED"
            row["claim_matches_verdict"] = (claimed == verified)
        table.append(row)
    bad = [r for r in table if not r.get("skipped") and not r.get("claim_matches_verdict")]
    if not quiet:
        print(f"\n  {'row':78s} {'claim':6s} {'verdict':22s} {'rc':3s} plan")
        for r in table:
            if r.get("skipped"):
                continue
            print(f"  {r['row'][:78]:78s} {str(r['claim_solved']):6s} {str(r['verdict']):22s} "
                  f"{r['rc']:<3d} {r['plan']!r} moves={r['moves']} blocked={r['blocked']}")
            if r.get("reason"):
                print(f"      {r['refusal_reason']}: {r['reason']}")
    return (1 if bad else 0), table


def main():
    ap = argparse.ArgumentParser(description="Enforce that every claimed solve carries a plan a SEPARATE "
                                             "process replays; mutation-test the enforcer.")
    ap.add_argument("--corpus", nargs="*", default=None,
                    help="directories of cell records to sweep (default: probes/ and probes/controls/)")
    ap.add_argument("--root", default=HERE)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--controls-only", action="store_true")
    a = ap.parse_args()
    corpus = a.corpus or [os.path.join(a.root, "probes"), os.path.join(a.root, "probes", "controls")]

    if not os.path.exists(VERIFIER):
        print(f"  MISSING: {VERIFIER} -- a checker without its verifier is not a check")
        return 2

    print("=" * 104)
    print("SOKOBAN REPLAY CONTROLS -- the verdicts below come from a SEPARATE PROCESS")
    print("=" * 104)
    print(f"  verifier   sokoban_replay.py  sha256 {verifier_sha()[:16]}")
    c = Controls()
    controls(c, a.root, corpus)

    tables = {}
    if not a.controls_only:
        print("\n[D0] THE CORPUS -- every row that carries a plan, replayed and compared with its own claim")
        for d in corpus:
            if not os.path.isdir(d):
                print(f"  (no such corpus directory: {d})")
                continue
            print(f"\n  --- {os.path.relpath(d, a.root)}/")
            rc_d, table = sweep(d, a.root)
            tables[d] = table
            n = sum(1 for r in table if not r.get("skipped"))
            solved = sum(1 for r in table if r.get("claim_solved") is True)
            bad = [r for r in table if not r.get("skipped") and not r.get("claim_matches_verdict")]
            print(f"  {n} cell record(s); {solved} claim solved; {len(bad)} disagree(s)")
            c.ck(f"{os.path.relpath(d, a.root)}/: every claim matches its replay", len(bad), 0)

    print()
    print("=" * 104)
    n = sum(1 for r in c.rows if r["pass"])
    print(f"{'ALL CONTROLS PASS' if n == len(c.rows) else str(len(c.rows) - n) + ' CONTROL(S) FAILED'}"
          f"   --  {n}/{len(c.rows)}")
    print("=" * 104)
    if a.json:
        print(json.dumps({"controls": c.rows, "corpus": tables, "verifier_sha256": verifier_sha()}, indent=1,
                         sort_keys=True))
    return 0 if n == len(c.rows) else 1


if __name__ == "__main__":
    sys.exit(main())
