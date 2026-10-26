#!/usr/bin/env python3
"""THE BASE RATE, RE-DERIVED IN-CABINET -- and the period-6 claim tested rather than carried.

WHY THIS FILE EXISTS
    The rung's scoring has to SUBTRACT a base rate, and the base rate on this cabinet was measured by a PEER'S
    script (`fixed_reply_base_rate.py`, `5ad37be8…`), not by anything in this cabinet:

        streams_tried 87 380 · clear 01: 77 540 · 02: 198 · 03: 76 · all three: 0
        best plan RULDLU (period 6) · strict 1/3 · generous 2/3

    A number a cabinet cannot re-derive is a number it can only repeat. This file re-derives it from the frozen
    simulator and this cabinet's own verifier (`sokoban_replay.py`), and it ASSERTS the parts the next reader
    will lean on. A number that does not reproduce is printed as a disagreement, not rounded off.

WHAT IS ENUMERATED, STATED PRECISELY BECAUSE THE SENTENCE IS THE MEASUREMENT
    A PLAN HERE IS A PERIODIC STREAM. A word `w` of length `p` (the PERIOD) is repeated until the cap, and the
    plan is that repetition. The universe is every word of length 1..8 over the frozen action order `U D L R`:

        Σ_{L=1..8} 4^L = 87 380

    TWO COUNTINGS, BOTH PRINTED, BECAUSE THE PEER'S TWO NUMBERS ARE TWO READINGS OF ONE THING:

        GENEROUS   the level is solved at ANY ply of the repeated plan
        STRICT     the FIRST solve falls exactly at a PERIOD BOUNDARY (ply+1 is a multiple of the period)

    `RULDLU` on level 03 solves at ply 6 -- the boundary -- so it is STRICT there; on level 01 it solves at ply 1,
    inside the first period, so it is GENEROUS there and not strict. `strict 1/3 · generous 2/3` is exactly that
    reading, and it is the reading this file tests.

WHAT IT WILL NOT DO
    It does not import, run, read or reproduce the peer's script. It reads the three frozen levels and nothing
    else. It writes nothing. The solver's `READ_CONTROL` is NOT consulted: the counts it asserts are derived from
    the level files here, and the known-good plans are cross-checked against `sokoban_replay.py` so that a
    base rate is never computed with a different transition rule than the one that certifies a solve.

    python3 sokoban_base_rate.py                 # caps 40 and 64, the cabinet's own cap first
    python3 sokoban_base_rate.py --caps 40 64 200
    python3 sokoban_base_rate.py --json
"""
import argparse
import hashlib
import itertools
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                          # noqa: E402  FROZEN. read-only.
import sokoban_replay as R                                                   # noqa: E402  the verifier's own rule

LEVELS = ("01_one_push", "02_two_boxes", "03_the_corner_waiting")
ACTIONS = "UDLR"                                     # the frozen action order
MAX_PERIOD = 8
UNIVERSE = sum(4 ** p for p in range(1, MAX_PERIOD + 1))          # 87 380

# THE ASSERTIONS. Each is a claim a reader of the rung will lean on, so each is checked and each can fail.
EXPECT_UNIVERSE = 87380
EXPECT_01_GENEROUS = 77540        # = Σ_{L=1..8} (4^L − 3^L): level 01 is one push, so a word clears it iff it
                                  #   contains an R -- every other first move from its start is blocked
EXPECT_ALL_THREE = 0
PERIOD6_WORD = "RULDLU"
# THE CAP THE ASSERTIONS ARE TAKEN AT: the cabinet's own `--cap 40` (sokoban_run.py's default). Named here so
# that `--caps 12 24` can still be run for a cap-sensitivity reading without moving what is being asserted.
ASSERT_CAP = 40


def level_digest(name):
    p = os.path.join(HERE, "levels", name + ".txt")
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def first_solve(board, state0, plan):
    """-> the 0-based ply of the FIRST solved board, or None. The whole plan is not run once solved: a crate can
    be pushed OFF a target, so a later `solved` would not be the solve this measurement is about."""
    st = state0
    for i, tok in enumerate(plan):
        st, _outcome = R.step(board, st, tok)
        if R.solved(board, st):
            return i
    return None


def cycle_plan(word, cap):
    reps = (cap + len(word) - 1) // len(word)
    return (word * reps)[:cap]


def measure(cap):
    """-> per level, the counts, and the argmax under the peer's own ranking. Pure function of the levels."""
    boards = {}
    for name in LEVELS:
        board, state0 = R.parse_level(open(os.path.join(HERE, "levels", name + ".txt")).read())
        boards[name] = (board, state0)
    generous = {n: 0 for n in LEVELS}
    strict = {n: 0 for n in LEVELS}
    all_three = 0
    best = {"strict": -1, "generous": -1, "period": None, "word": None}
    shortest = {}                                    # level -> (period, word) of the first solve by period
    for p in range(1, MAX_PERIOD + 1):
        for tup in itertools.product(ACTIONS, repeat=p):
            word = "".join(tup)
            plan = cycle_plan(word, cap)
            solved_at = {}
            for name in LEVELS:
                board, state0 = boards[name]
                ply = first_solve(board, state0, plan)
                solved_at[name] = ply
                if ply is not None:
                    generous[name] += 1
                    if (ply + 1) % p == 0:
                        strict[name] += 1
                    if name not in shortest:
                        shortest[name] = (p, word)
            if all(v is not None for v in solved_at.values()):
                all_three += 1
            st_n = sum(1 for n in LEVELS if solved_at[n] is not None and (solved_at[n] + 1) % p == 0)
            gen_n = sum(1 for n in LEVELS if solved_at[n] is not None)
            key = (st_n, gen_n, -p)
            if key > (best["strict"], best["generous"], -(best["period"] or 999)):
                best = {"strict": st_n, "generous": gen_n, "period": p, "word": word}
    # the shortest period attaining the maximum COVERAGE, which is a different objective from the peer's ranking
    cover = {n: (generous[n], shortest.get(n)) for n in LEVELS}
    return {"cap": cap, "universe": UNIVERSE, "generous": generous, "strict": strict,
            "all_three_generous": all_three, "best_by_peer_ranking": best,
            "shortest_period_per_level": {n: (list(v) if v else None) for n, v in shortest.items()},
            "coverage": cover}


def cycle_report(name, word, cap):
    """The named word measured one level at a time, with the ply it solves at -- so a claim about 'RULDLU' is
    about numbers rather than about a string."""
    board, state0 = R.parse_level(open(os.path.join(HERE, "levels", name + ".txt")).read())
    plan = cycle_plan(word, cap)
    ply = first_solve(board, state0, plan)
    return {"level": name, "word": word, "period": len(word), "solves_at_ply": ply,
            "solved_at_period_boundary": (ply is not None and (ply + 1) % len(word) == 0)}


def shortest_for_coverage(cap, want=2):
    """The SHORTEST period whose plan solves at least `want` levels -- the question the card asks second:
    'if RULDLU is not optimal, print the best you find and its period'."""
    boards = {}
    for name in LEVELS:
        boards[name] = R.parse_level(open(os.path.join(HERE, "levels", name + ".txt")).read())
    for p in range(1, MAX_PERIOD + 1):
        hits = []
        for tup in itertools.product(ACTIONS, repeat=p):
            word = "".join(tup)
            plan = cycle_plan(word, cap)
            got = [n for n in LEVELS if first_solve(boards[n][0], boards[n][1], plan) is not None]
            if len(got) >= want:
                hits.append((word, got))
        if hits:
            return {"period": p, "count": len(hits), "examples": hits[:8]}
    return None


def main():
    ap = argparse.ArgumentParser(description="Re-derive SOKOBAN's periodic-plan base rate in-cabinet.")
    ap.add_argument("--caps", type=int, nargs="+", default=[40, 64])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    t0 = time.perf_counter()
    out = {"universe_formula": f"sum(4**p for p in 1..{MAX_PERIOD})", "levels": LEVELS,
           "level_sha256": {n: level_digest(n) for n in LEVELS}, "runs": []}
    for cap in a.caps:
        out["runs"].append(measure(cap))
    out["period6"] = {n: cycle_report(n, PERIOD6_WORD, ASSERT_CAP) for n in LEVELS}
    out["shortest_two_of_three"] = shortest_for_coverage(ASSERT_CAP, 2)
    out["shortest_three_of_three"] = shortest_for_coverage(ASSERT_CAP, 3)
    out["assert_cap"] = ASSERT_CAP
    out["seconds"] = round(time.perf_counter() - t0, 1)

    # ---- the assertions, each printed with its evidence. THEY ARE TAKEN AT ONE NAMED CAP, not at whichever cap
    # was passed first: a cap too tight for a level to be solvable would otherwise fail an assertion that is
    # about the PERIODIC PLANS and not about the budget. (Measured: at cap 12 no word clears level 02 at all.)
    checks = []

    def ck(name, got, want):
        checks.append({"name": name, "got": got, "want": want, "pass": got == want})

    first = next((r for r in out["runs"] if r["cap"] == ASSERT_CAP), out["runs"][-1])
    ck("the universe is Σ 4^L for L=1..8", first["universe"], EXPECT_UNIVERSE)
    ck("level 01: GENEROUS count equals Σ(4^L − 3^L) -- clears iff the word contains an R",
       first["generous"]["01_one_push"], EXPECT_01_GENEROUS)
    ck("no word clears all three levels (GENEROUS)", first["all_three_generous"], EXPECT_ALL_THREE)
    p6 = out["period6"]
    ck("RULDLU clears level 01 (at ply 1, INSIDE its first period)", p6["01_one_push"]["solves_at_ply"], 0)
    ck("RULDLU clears level 03 (at ply 6, exactly ON the period boundary)", p6["03_the_corner_waiting"]["solves_at_ply"], 5)
    ck("RULDLU does NOT clear level 02", p6["02_two_boxes"]["solves_at_ply"], None)
    ck("so RULDLU is STRICT on 03 and GENEROUS on 01 -- the peer's 1/3 and 2/3",
       (p6["03_the_corner_waiting"]["solved_at_period_boundary"], p6["01_one_push"]["solved_at_period_boundary"]),
       (True, False))
    ck("the minimum period that clears level 01 is 1 (`R` repeated)",
       first["shortest_period_per_level"]["01_one_push"][0], 1)
    ck("the minimum period that clears level 03 is 6 -- the same 6 the solver proves is optimal",
       first["shortest_period_per_level"]["03_the_corner_waiting"][0], 6)

    if a.json:
        out["checks"] = checks
        print(json.dumps(out, indent=1, sort_keys=True))
        return 0 if all(c["pass"] for c in checks) else 1

    print("=" * 104)
    print("SOKOBAN BASE RATE -- every periodic plan over U D L R, period 1..%d, re-derived here" % MAX_PERIOD)
    print("=" * 104)
    print(f"  universe          {UNIVERSE} words  (Σ 4^L, L=1..{MAX_PERIOD})")
    for name in LEVELS:
        print(f"  level             {name}  sha256 {level_digest(name)[:16]}")
    for run in out["runs"]:
        g, s = run["generous"], run["strict"]
        print()
        print(f"  ---- CAP {run['cap']} (plan = word repeated to {run['cap']} plies)")
        for name in LEVELS:
            sp = run["shortest_period_per_level"].get(name)
            shown = (f"{sp[0]} ({sp[1]})" if sp
                     else f"NONE -- no word of period <= {MAX_PERIOD} clears it at this cap")
            print(f"    {name:26s} GENEROUS {g[name]:6d}   STRICT {s[name]:6d}   shortest period {shown}")
        print(f"    {'all three (GENEROUS)':26s} {run['all_three_generous']:6d}")
        b = run["best_by_peer_ranking"]
        print(f"    best by the peer's ranking (strict, generous, then shortest period):")
        print(f"      {b['word']}  period {b['period']}  strict {b['strict']}/3  generous {b['generous']}/3")

    print()
    print(f"  ---- CAP SENSITIVITY (a reading, not an assertion; the assertions are taken at cap {ASSERT_CAP})")
    print(f"    {'cap':>6s} {'01':>8s} {'02':>6s} {'03':>5s} {'all three':>10s}")
    for run in out["runs"]:
        g = run["generous"]
        print(f"    {run['cap']:6d} {g['01_one_push']:8d} {g['02_two_boxes']:6d} {g['03_the_corner_waiting']:5d} "
              f"{run['all_three_generous']:10d}")

    print()
    print("  ---- THE PERIOD-6 CLAIM, MEASURED LINE BY LINE")
    for name in LEVELS:
        r = out["period6"][name]
        where = ("ply " + str(r["solves_at_ply"] + 1)) if r["solves_at_ply"] is not None else "never"
        print(f"    RULDLU on {name:26s} solves at {where:8s}"
              f"  {'ON the period boundary' if r['solved_at_period_boundary'] else 'inside a period / never'}")
    print()
    s2 = out["shortest_two_of_three"]
    s3 = out["shortest_three_of_three"]
    print(f"  ---- OPTIMALITY. The shortest period clearing TWO of three: "
          f"{('period ' + str(s2['period']) + ', ' + str(s2['count']) + ' word(s)') if s2 else 'none'}")
    if s2:
        for w, got in s2["examples"]:
            print(f"       {w:10s} clears {got}")
    print(f"       the shortest period clearing THREE of three: "
          f"{('period ' + str(s3['period']) + ', ' + str(s3['count']) + ' word(s)') if s3 else 'NONE -- '
          'no periodic plan of period <= ' + str(MAX_PERIOD) + ' clears all three'}")
    if s2 and s2["period"] < len(PERIOD6_WORD):
        print(f"       ** RULDLU (period 6) is NOT the shortest plan attaining the same coverage: "
              f"{s2['examples'][0][0]!r} reaches it at period {s2['period']}. **")

    print()
    print("=" * 104)
    for c in checks:
        print(f"  {'PASS' if c['pass'] else 'FAIL'}  {c['name']}")
        if not c["pass"]:
            print(f"          got  {c['got']!r}\n          want {c['want']!r}")
    n = sum(1 for c in checks if c["pass"])
    print(f"{'ALL ASSERTIONS HOLD' if n == len(checks) else str(len(checks) - n) + ' ASSERTION(S) FAILED'}"
          f"   --  {n}/{len(checks)}   in {out['seconds']}s")
    print("=" * 104)
    return 0 if n == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
