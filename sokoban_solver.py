#!/usr/bin/env python3
"""THE THIRD LEVEL'S SOLVER -- one new file, THREE verdicts, and no fourth.

WHY THIS FILE EXISTS
    `SOKOBAN_VERDICT_1.md` closes on the gap that blocks the third level:

        "The third level is ABSENT and is reported as absent: a level nobody can solve needs a solver to
         PROVE it, and one that merely LOOKS lost is a trap for the reader rather than a control."

    This file is the prover. Every run ends in exactly one of three verdicts:

        SOLVABLE          a move string that the FROZEN simulator replays to `solved`, plus its move count
        UNSOLVABLE        a COMPLETE enumeration of the reachable state space, with no solved state in it
        BUDGET_EXHAUSTED  the NAMED budget ran out with work left to do

    AN UNDECIDED RESULT IS NEVER REPORTED AS UNSOLVABLE. BUDGET_EXHAUSTED is a different word, a
    different field, and a different exit path, and the budget is printed WITH the verdict so a reader
    never has to infer which of the two they are looking at. The worst failure available here is a
    reader finding an answer in text that does not contain one, with a number attached.

WHAT IT DOES NOT DO
    No population runs, no entrant anywhere near it, no timing of anything but its own search. It READS
    levels and it does not write them. It never modifies a frozen file: it IMPORTS `sokoban.py` and uses
    its `step()` as the transition rule and its `play()` as the verifier -- so a solution reported here
    is a solution the frozen simulator agrees with, not a second opinion, and the digest of the file it
    used is printed beside the verdict.

THE TWO DIRECTIONS, BOTH ASSERTED
    A solver that never says UNSOLVABLE is broken; one that always says it is dead. The control suite
    asserts BOTH: the frozen levels must come back SOLVABLE with EXACTLY the move counts the project already
    has, and a
    level built here -- a crate whose only legal moves end in a non-target corner -- must come back
    UNSOLVABLE, with the enumeration cross-checked by a second, independently written enumerator.

    python3 sokoban_solver.py                     # the full control suite (exit 0 = all controls pass)
    python3 sokoban_solver.py --read-control      # ONLY the frozen read-control; the counts are in
                                                  # READ_CONTROL and are not restated here
    python3 sokoban_solver.py --level levels/02_two_boxes.txt
    python3 sokoban_solver.py --level X.txt --max-states 50          # -> BUDGET_EXHAUSTED, named
    python3 sokoban_solver.py --level X.txt --json
"""
import argparse
import hashlib
import json
import os
import sys
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                       # noqa: E402  FROZEN. read-only.

SOLVABLE, UNSOLVABLE, BUDGET_EXHAUSTED = "SOLVABLE", "UNSOLVABLE", "BUDGET_EXHAUSTED"
ACTIONS = "UDLR"                                    # the frozen action space, in the frozen order

# --------------------------------------------------------------------------------- what we are read against
# THE READ-CONTROL, declared HERE and not inferred from a run: the answers the project already has.
# A solver that cannot reproduce these cannot be trusted on the answers it does not have.
#
# AND THE THREE ENTRIES ARE NOT EQUALLY STRONG, SO THE DIFFERENCE IS WRITTEN DOWN RATHER THAN BLURRED:
#
#   01, 02   the solutions were PUBLISHED BEFORE THIS SOLVER EXISTED (verify_levels.py carried R and
#            RRRRDLLLDRRR). Fully independent of the thing being checked.
#   03       the solution was FOUND BY THIS SOLVER, and then confirmed by the FROZEN SIMULATOR replaying
#            RULDLU -> solved, 6 moves. THE ENFORCER IS INDEPENDENT; THE DISCOVERY IS NOT. So this entry
#            tests that the solver still returns what it found and that an independent enforcer agrees the
#            count is ACHIEVABLE -- it does NOT independently establish optimality.
#
# Keeping both kinds, and labelling which is which, is the point: a control whose provenance is not stated
# gets read as the strongest kind.
READ_CONTROL = [("01_one_push", 1), ("02_two_boxes", 12), ("03_the_corner_waiting", 6)]


# AND THE MESSAGES ARE BUILT FROM THE TABLE, NEVER RETYPED.
#
# They read "the two answers" and "PASSES: 1 and 12" while the table held two entries. Adding a third made
# a TRUE sentence FALSE WITHOUT ANYTHING EDITING IT -- the caption drifted from the record it captions,
# which is the defect this project has spent the week removing. A hand-typed count beside a growing table
# is a second copy of the truth, so these are derived at print time instead.
_COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


def _rc_count_word():
    n = len(READ_CONTROL)
    return _COUNT_WORDS.get(n, str(n))


def _rc_moves_str():
    ms = [m for _, m in READ_CONTROL]
    if len(ms) == 1:
        return str(ms[0])
    return ", ".join(str(m) for m in ms[:-1]) + f" and {ms[-1]}"

# The digests the freeze record names. If any of these does not match, the artifact this solver read is
# not the artifact the numbers came from -- and that is reported, not rounded off.
FROZEN_DIGESTS = {
    "sokoban.py": "7134c3e8fc59fe027f3691ffa56ab4acb5eb735018a17683f3183ce538f90235",
    "levels/01_one_push.txt": "db6ca59655f0d7d1f1ce48e36e0b0c90a3bca5158b96a31a7a4fe37006a6a313",
    "levels/02_two_boxes.txt": "7549657f1768607cefab6d892b1756b1cabf23f51144a7679d76f331b38a57d7",
    "levels/03_the_corner_waiting.txt": "77d18407a001da292b2f1dcf8054ed40ddc2038563f23b96861a362c78cf23d6",
}

# The frozen solution `verify_levels.py` carries for 02, used as a CROSS-CHECK on the read-control: 12
# moves must come out of the frozen enforcer for the frozen string too, not only out of this solver.
FROZEN_SOLUTION_02 = "RRRRDLLLDRRR"


# ----------------------------------------------------------------------------------------- the transition
def _state(walls, targets, rows, cols, player, boxes):
    """The state dict the frozen `step()` expects. Built here so the search and the verifier share ONE
    transition rule: whatever `step()` does about walls, boxes and pushes, this search inherits."""
    return {"walls": walls, "targets": targets, "boxes": set(boxes), "player": player,
            "rows": rows, "cols": cols}


def _corner_dead(cell, walls, targets, rows, cols):
    """A box in a corner that is NOT a target can never move again -- SO THE STATE IS LOST.

    WHY THE RULE IS SOUND: a push needs the player standing on the square OPPOSITE the direction the box
    travels. In a corner, two perpendicular push directions would require the player to stand in a wall.
    The two remaining directions push the box into a wall. Nothing pulls. So the box is immobile forever,
    and every state reachable from this one is unsolvable.

    It is used ONLY to skip work. It never decides a verdict on its own -- the corner-at-start case
    below is the exception and it is labelled as such, and the control suite cross-checks every
    UNSOLVABLE verdict against the pruning-free enumeration.
    """
    if cell in targets:
        return False
    r, c = cell

    def wall(p):
        rr, cc = p
        return rr < 0 or cc < 0 or rr >= rows or cc >= cols or p in walls

    return (wall((r - 1, c)) or wall((r + 1, c))) and (wall((r, c - 1)) or wall((r, c + 1)))


# ---------------------------------------------------------------------------------------------- the search
def solve_text(text, name="<text>", max_states=None, max_seconds=None, deadlock="corner"):
    """Level text -> a result dict carrying EXACTLY ONE of the three verdicts.

    THE ENGINE IS A BREADTH-FIRST SEARCH OVER PLAYER MOVES, so the move count it reports IS the minimum:
    BFS expands the state space in order of move count, and the first solved state it reaches is reached
    at the smallest depth. The optimality claim is therefore structural, and it is additionally
    re-derived from scratch by a second enumerator in the control suite, which does not share this code.

    THE BUDGET IS CHECKED ONLY WHEN WORK REMAINS. An exhausted frontier is a proof and is never reported
    as a budget; a budget that bites is never reported as a proof. That single line is the whole
    difference between the two failure modes this file exists to keep apart.

    A MALFORMED LEVEL GETS NO VERDICT AT ALL: `S.parse` raises, the exception travels, and the caller
    refuses. Refusal is not a fourth verdict -- it is the absence of one.
    """
    t0 = time.perf_counter()
    st0 = S.parse(text)                                     # raises ValueError: not a level, not a verdict
    walls, targets, rows, cols = st0["walls"], st0["targets"], st0["rows"], st0["cols"]
    start = (st0["player"], frozenset(st0["boxes"]))
    expanded, pruned = 0, 0
    expanded_by_depth = {}
    max_depth = 0

    def base(verdict):
        return {"level": name, "verdict": verdict, "moves": None, "pushes": None, "solution": None,
                "proof": None, "budget": None, "verification": None,
                "cost": {"states_expanded": expanded, "states_pruned_by_corner_rule": pruned,
                         "states_reachable_enumerated": expanded + pruned,
                         "expanded_by_depth": dict(sorted(expanded_by_depth.items())),
                         "max_depth_reached": max_depth, "seconds": time.perf_counter() - t0}}

    def solvable(moves, solution, frontier_size, depth):
        """A SOLVABLE verdict is only ever returned with the FROZEN SIMULATOR's agreement attached. The
        solution replays through `S.play`, which is the enforcer the score comes from -- if it did not,
        this function raises rather than reporting a solve nobody can reproduce."""
        replay = S.play(text, list(solution))
        if not (replay["solved"] and replay["moves"] == moves):
            raise AssertionError(f"INTERNAL: solution {solution!r} replays to solved={replay['solved']} "
                                 f"moves={replay['moves']}, not {moves}")
        pushes = sum(1 for t in replay["trace"] if t["outcome"] == "pushed")
        r = base(SOLVABLE)
        r.update(moves=moves, pushes=pushes, solution=solution)
        r["verification"] = {"by": "sokoban.play() -- the FROZEN simulator, the same counter the score uses",
                             "solved": replay["solved"], "moves": replay["moves"],
                             "blocked": replay["blocked"], "pushes": pushes,
                             "simulator_sha256": _sha256(os.path.join(HERE, "sokoban.py"))}
        return r

    if S.solved(st0):                                       # already solved: zero moves, and that is SOLVABLE
        return solvable(0, "", 0, 0)

    if deadlock == "corner":
        dead = sorted(b for b in st0["boxes"] if _corner_dead(b, walls, targets, rows, cols))
        if dead:
            # LABELLED, because it is the ONE place a rule decides instead of the enumeration. It is a
            # sound rule and it consumes no budget: there is no reachable state to enumerate, since the
            # start state is already dead.
            pruned = 1
            r = base(UNSOLVABLE)
            r["proof"] = {"kind": "sound_rule_at_the_start",
                          "rule": "corner_rule: a box in a non-target corner can never move again",
                          "box_cells": [list(b) for b in dead],
                          "reachable_states_enumerated": 0,
                          "cross_check": "the control suite exhausts this same level WITHOUT any rule "
                                         "and reports the same verdict"}
            return r

    depth = {start: 0}
    parent: dict = {start: None}
    frontier = deque([start])

    while frontier:
        # ---- the budget, checked ONLY while work remains. Past this line there is either a solution or
        # ---- a proof; before it there is neither, and the verdict says so by name.
        if max_states is not None and expanded >= max_states:
            r = base(BUDGET_EXHAUSTED)
            r["budget"] = {"kind": "max_states", "limit": max_states, "used": expanded,
                           "states_still_queued": len(frontier),
                           "note": "NOT a proof of unsolvability -- the search stopped early"}
            return r
        if max_seconds is not None and (time.perf_counter() - t0) > max_seconds:
            r = base(BUDGET_EXHAUSTED)
            r["budget"] = {"kind": "max_seconds", "limit": max_seconds,
                           "used": round(time.perf_counter() - t0, 6),
                           "states_expanded": expanded, "states_still_queued": len(frontier),
                           "note": "NOT a proof of unsolvability -- the search stopped early"}
            return r

        key = frontier.popleft()
        d = depth[key]
        max_depth = max(max_depth, d)
        st = _state(walls, targets, rows, cols, key[0], key[1])
        expanded += 1
        expanded_by_depth[d] = expanded_by_depth.get(d, 0) + 1

        for a in ACTIONS:
            nst, outcome = S.step(st, a)                    # THE FROZEN RULE. never reimplemented here.
            if outcome == "blocked":
                continue
            nk = (nst["player"], frozenset(nst["boxes"]))
            if nk in depth:
                continue
            if deadlock == "corner" and any(_corner_dead(b, walls, targets, rows, cols)
                                            for b in nk[1]):
                pruned += 1
                continue
            depth[nk] = d + 1
            parent[nk] = (key, a)
            if S.solved(nst):
                return solvable(d + 1, _reconstruct(parent, nk), len(frontier), d + 1)
            frontier.append(nk)

    # ---- the frontier emptied: EVERY reachable state was seen. That is the proof, and it is the only
    # ---- thing in this file allowed to write the word UNSOLVABLE about an enumeration.
    r = base(UNSOLVABLE)
    r["proof"] = {"kind": "complete_enumeration",
                  "engine": "breadth-first search over player moves",
                  "transition_rule": "sokoban.py step() -- the frozen simulator",
                  "simulator_sha256": _sha256(os.path.join(HERE, "sokoban.py")),
                  "reachable_states_enumerated": expanded + pruned,
                  "states_expanded": expanded,
                  "states_pruned_by_corner_rule": pruned,
                  "solved_states_found": 0,
                  "deadlock_rule": deadlock,
                  "soundness": "every reachable state was expanded, or was cut by the corner rule; the "
                               "corner rule only ever cuts states from which no solved state is "
                               "reachable, so no solution can hide behind it"}
    return r


def _reconstruct(parent, goal):
    seq, k = [], goal
    while parent[k] is not None:
        pk, a = parent[k]
        seq.append(a)
        k = pk
    seq.reverse()
    return "".join(seq)


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ----------------------------------------------------------- the SECOND enumerator, for cross-checking
def independent_enumerate(text, cap=60):
    """A second enumerator, written separately from `solve_text`, sharing nothing with it but the frozen
    `step()`. It keys states by the RENDERED BOARD, where the solver keys them by (player, boxes) -- so a
    keying mistake in one does not reproduce in the other. No pruning, no budget, no early exit on a
    solved board except to record its depth.

    -> {"first_solve_depth": int|None, "exhausted": bool, "states": int}
    `exhausted` True with no depth IS an independent confirmation of unsolvability; a cap reached
    without exhaustion is reported as neither.
    """
    st0 = S.parse(text)
    layer = [st0]
    seen = {S.render(st0)}
    states = 0
    for d in range(cap + 1):
        if any(S.solved(st) for st in layer):
            return {"first_solve_depth": d, "exhausted": False, "states": states}
        if not layer:
            return {"first_solve_depth": None, "exhausted": True, "states": states}
        nxt = []
        for st in layer:
            states += 1
            for a in ACTIONS:
                nst, outcome = S.step(st, a)
                if outcome == "blocked":
                    continue
                k = S.render(nst)
                if k in seen:
                    continue
                seen.add(k)
                nxt.append(nst)
        layer = nxt
    return {"first_solve_depth": None, "exhausted": False, "states": states}


# ---------------------------------------------------------------- the levels BUILT HERE, as controls
# U1 -- A CRATE IN A CORNER WITH NO TARGET. The start state is already dead: the crate is immobile on
# move one and the target is elsewhere. The weakest of the two unsolvable controls, and included because
# it is the one the brief names -- "a crate pushed into a corner with no target is the obvious one".
U1_CORNER_AT_START = """#####
#@$##
#.  #
#####"""

# U2 -- A CRATE THAT CAN ONLY EVER SLIDE ALONG ONE ROW. It sits under the top wall, so it can never be
# pushed down (that needs the player standing in the wall above it); the row's left end is a non-target
# corner, so one branch dies outright; the target is two rows below, so NO branch can reach it. The level
# STARTS ALIVE -- this is the irreversibility control, not a dead start -- and it is small enough that
# the pruning-free enumeration finishes, which is what makes the budget boundary testable on it.
U2_ONE_ROW_ONLY = """#######
# @$  #
#     #
#  .  #
#######"""

# S1 -- A SOLVABLE LEVEL WHOSE ANSWER IS IN NO FILE IN THIS REPO. The two frozen levels have published
# answers, so a solver tuned to them would pass the read-control and be worthless. This one has no answer
# anywhere: it is solved here, replayed through the frozen enforcer, and its optimum re-derived by the
# second enumerator.
S1_BUILT_SOLVABLE = """#########
#@      #
#  $    #
#   .   #
#       #
#  $    #
#   .   #
#########"""

CONTROL_LEVELS = [("U1_corner_at_start", U1_CORNER_AT_START), ("U2_one_row_only", U2_ONE_ROW_ONLY),
                  ("S1_built_solvable", S1_BUILT_SOLVABLE)]


# ---------------------------------------------------------------------------------------- the control suite
def _self_test():
    fails, total = [], [0]

    def ck(name, got, want):
        total[0] += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 100)
    print("SOKOBAN SOLVER CONTROLS -- the read-control first, then both directions, then the budget")
    print("=" * 100)

    level_path = lambda n: os.path.join(HERE, "levels", f"{n}.txt")   # noqa: E731

    # ---- [1] THE READ-CONTROL. First, because it is the first thing the reader will check.
    print(f"\n[1] THE READ-CONTROL -- the {_rc_count_word()} answers we already have, reproduced EXACTLY")
    read_results = {}
    for lname, want_moves in READ_CONTROL:
        text = open(level_path(lname)).read()
        r = solve_text(text, name=lname)
        read_results[lname] = r
        ck(f"{lname}: verdict", r["verdict"], SOLVABLE)
        ck(f"{lname}: moves are EXACTLY {want_moves}", r["moves"], want_moves)
        ck(f"{lname}: the reported solution replays through the frozen simulator to solved",
           S.play(text, list(r["solution"]))["solved"], True)
        ck(f"{lname}: ...and the simulator's move count equals the solver's",
           S.play(text, list(r["solution"]))["moves"], want_moves)
        print(f"        {lname}: solution {r['solution']}  moves {r['moves']}  "
              f"expanded {r['cost']['states_expanded']}  {r['cost']['seconds']:.4f}s")
    # the frozen string in verify_levels.py, through the frozen enforcer, as a second opinion on 12
    frozen02 = S.play(open(level_path("02_two_boxes")).read(), list(FROZEN_SOLUTION_02))
    ck("the FROZEN solution string in verify_levels.py is also 12 moves (independent of this solver)",
       (frozen02["solved"], frozen02["moves"]), (True, 12))

    # ---- [2] OPTIMALITY, re-derived from scratch by the second enumerator
    print("\n[2] 'EXACTLY 1 AND 12' IS THE MINIMUM, not merely what this solver happened to find")
    for lname, want_moves in READ_CONTROL:
        ind = independent_enumerate(open(level_path(lname)).read())
        ck(f"{lname}: independent first-solve depth == {want_moves}", ind["first_solve_depth"], want_moves)
        ck(f"{lname}: ...and the space was not exhausted below it (a solved state was genuinely found)",
           ind["exhausted"], False)
        print(f"        {lname}: independent enumeration, first solved state at depth "
              f"{ind['first_solve_depth']}, {ind['states']} states walked")

    # ---- [3] BOTH DIRECTIONS
    print("\n[3] BOTH DIRECTIONS -- one it solves, one BUILT here that it cannot")
    print("    (a solver that never says UNSOLVABLE is broken; one that always says it is dead)")
    built = {}
    for lname, ltext in CONTROL_LEVELS[:2]:
        r = solve_text(ltext, name=lname)
        built[lname] = r
        ind = independent_enumerate(ltext)
        ck(f"{lname}: verdict UNSOLVABLE", r["verdict"], UNSOLVABLE)
        ck(f"{lname}: the SECOND enumerator, written separately, agrees -- 0 solved states, space exhausted",
           (ind["first_solve_depth"], ind["exhausted"]), (None, True))
        ck(f"{lname}: the verdict is a proof and says which kind",
           r["proof"]["kind"] in ("complete_enumeration", "sound_rule_at_the_start"), True)
        ck(f"{lname}: UNSOLVABLE was NOT reached by running out of budget",
           r["budget"], None)
        ck(f"{lname}: ...and the proof records zero solved states found",
           r["proof"].get("solved_states_found", 0), 0)
        print(f"        {lname}: proof kind {r['proof']['kind']}; "
              f"expanded {r['cost']['states_expanded']} pruned "
              f"{r['cost']['states_pruned_by_corner_rule']}  {r['cost']['seconds']:.4f}s")
    # U2 must be UNSOLVABLE BY PURE ENUMERATION, with no rule helping: the strong form of the claim
    proof_u2 = solve_text(U2_ONE_ROW_ONLY, name="U2_one_row_only", deadlock="none")
    ck("U2 with the corner rule OFF is still UNSOLVABLE, by complete enumeration alone",
       proof_u2["verdict"], UNSOLVABLE)
    ck("U2: ...and the enumeration is non-trivial (more than one reachable state was expanded)",
       proof_u2["proof"]["reachable_states_enumerated"] > 1, True)
    ck("U2: ...and it is a complete_enumeration proof, not a rule fired at the start",
       proof_u2["proof"]["kind"], "complete_enumeration")
    # the SOLVABLE direction on a level whose answer is in NO file here (anti-overfitting control)
    s1 = solve_text(S1_BUILT_SOLVABLE, name="S1_built_solvable")
    ind_s1 = independent_enumerate(S1_BUILT_SOLVABLE)
    ck("S1 (a level built here, answer published nowhere) is SOLVABLE", s1["verdict"], SOLVABLE)
    ck("S1: the second enumerator finds the SAME first-solve depth", ind_s1["first_solve_depth"], s1["moves"])
    ck("S1: the solution replays through the frozen simulator", s1["verification"]["solved"], True)
    print(f"        S1_built_solvable: moves {s1['moves']} pushes {s1['pushes']} "
          f"solution {s1['solution']}  expanded {s1['cost']['states_expanded']}  "
          f"{s1['cost']['seconds']:.4f}s")
    verdicts = [r["verdict"] for r in built.values()] + [s1["verdict"]] + \
               [r["verdict"] for r in read_results.values()]
    ck("both directions are asserted: at least one SOLVABLE in the suite",
       verdicts.count(SOLVABLE) >= 1, True)
    ck("both directions are asserted: at least one UNSOLVABLE in the suite",
       verdicts.count(UNSOLVABLE) >= 1, True)

    # ---- [4] THE THIRD VERDICT, and the one confusion this file exists to prevent
    print("\n[4] BUDGET_EXHAUSTED IS ITS OWN VERDICT, and is NEVER reported as UNSOLVABLE")
    k = solve_text(U2_ONE_ROW_ONLY, name="U2", deadlock="none")["cost"]["states_expanded"]
    boundary = solve_text(U2_ONE_ROW_ONLY, name="U2", max_states=k, deadlock="none")
    short = solve_text(U2_ONE_ROW_ONLY, name="U2", max_states=k - 1, deadlock="none")
    ck(f"U2 with max_states == the {k} states it needs: UNSOLVABLE (exhaustion IS the proof)",
       boundary["verdict"], UNSOLVABLE)
    ck(f"U2 with max_states == {k - 1}, one state short: BUDGET_EXHAUSTED",
       short["verdict"], BUDGET_EXHAUSTED)
    ck("...and that short run does NOT say UNSOLVABLE", short["verdict"] == UNSOLVABLE, False)
    ck("...and it names the budget that bit", short["budget"]["kind"], "max_states")
    ck("...and it says how many states were still queued when it stopped",
       short["budget"]["states_still_queued"] > 0, True)
    ck("...and its proof field is EMPTY -- a budget is not a proof", short["proof"], None)
    ck("...and it carries no move count and no solution", (short["moves"], short["solution"]), (None, None))
    print(f"        boundary: max_states={k} -> SOLVABLE/UNSOLVABLE side; "
          f"max_states={k - 1} -> {short['verdict']} ({short['budget']})")
    clock = solve_text(U2_ONE_ROW_ONLY, name="U2", max_seconds=0.0, deadlock="none")
    ck("a CLOCK budget fires and is named too (max_seconds=0)",
       (clock["verdict"], clock["budget"]["kind"]), (BUDGET_EXHAUSTED, "max_seconds"))
    starved = solve_text(open(level_path("02_two_boxes")).read(), name="02_two_boxes", max_states=3)
    ck("a SOLVABLE level under a tight budget reports BUDGET_EXHAUSTED, not SOLVABLE",
       starved["verdict"], BUDGET_EXHAUSTED)
    ck("...and that run does NOT claim a solution", starved["solution"], None)

    # ---- [5] THE CORNER RULE IS SOUND, asserted rather than assumed
    print("\n[5] THE CORNER RULE ONLY SKIPS WORK -- it never changes a verdict")
    for lname, ltext in CONTROL_LEVELS[:2] + [("S1", S1_BUILT_SOLVABLE)]:
        on = solve_text(ltext, name=lname, deadlock="corner")
        off = solve_text(ltext, name=lname, deadlock="none")
        ck(f"{lname}: pruning ON and OFF agree on the verdict",
           (on["verdict"], off["verdict"]), (off["verdict"], off["verdict"]))
        ck(f"{lname}: ...and agree on the move count",
           on["moves"], off["moves"])
        if off["cost"]["states_expanded"]:
            ck(f"{lname}: ...and the rule costs no verdict, only work",
               on["cost"]["states_expanded"] <= off["cost"]["states_expanded"], True)
    u2_on = solve_text(U2_ONE_ROW_ONLY, name="U2", deadlock="corner")
    ck("U2 with the rule ON: the rule demonstrably fires (states cut by it)",
       u2_on["cost"]["states_pruned_by_corner_rule"] > 0, True)
    ck("U2 with the rule ON: still UNSOLVABLE, and no solved state was found",
       (u2_on["verdict"], u2_on["proof"]["solved_states_found"]), (UNSOLVABLE, 0))

    # ---- [6] THE ENFORCER: the file cited is the file read
    print("\n[6] THE ENFORCER IS THE FROZEN ONE, and it is unchanged")
    for rel, want in FROZEN_DIGESTS.items():
        got = _sha256(os.path.join(HERE, rel))
        ck(f"{rel}: sha256 matches the freeze record", got[:len(want)] if got != want else got, want)
    ck("sokoban.py's own self-test passes (its self-test IS its contract, per the freeze record)",
       S._self_test(), 0)

    # ---- [7] A MALFORMED LEVEL IS REFUSED, and gets no verdict at all
    print("\n[7] A MALFORMED LEVEL GETS NO VERDICT -- refusing is not a fourth verdict")
    for bad, why in (("#####\n#@$$.#\n#####", "two boxes one target"),
                     ("#####\n#@$#\n#####", "no target"),
                     ("#####\n#@X.#\n#####", "unknown character"),
                     ("#####\n#@..#\n#####", "no box")):
        try:
            solve_text(bad, name="malformed")
            ck(f"refuses a level with {why}", "returned a verdict", "ValueError / no verdict")
        except ValueError:
            ck(f"refuses a level with {why} (raises, so no verdict exists to misread)", "ValueError",
               "ValueError")

    print()
    print("=" * 100)
    n = total[0] - len(fails)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  {n}/{total[0]}")
    print("=" * 100)
    return 1 if fails else 0


# --------------------------------------------------------------------------------------------- reporting
def _report(r):
    print(f"  level        {r['level']}")
    print(f"  verdict      {r['verdict']}")
    if r["verdict"] == SOLVABLE:
        print(f"  moves        {r['moves']}   (player moves -- the counter sokoban.play reports)")
        print(f"  pushes       {r['pushes']}")
        print(f"  solution     {r['solution']}")
        v = r["verification"]
        print(f"  verified     sokoban.play(): solved={v['solved']} moves={v['moves']} "
              f"blocked={v['blocked']}  (simulator sha256 {v['simulator_sha256'][:16]}...)")
    elif r["verdict"] == UNSOLVABLE:
        p = r["proof"]
        print(f"  proof        {p['kind']}")
        if p["kind"] == "complete_enumeration":
            print(f"               every reachable state was seen: "
                  f"{p['reachable_states_enumerated']} enumerated, {p['states_expanded']} expanded, "
                  f"{p['states_pruned_by_corner_rule']} cut by the corner rule, "
                  f"{p['solved_states_found']} solved")
            print(f"               transition rule {p['transition_rule']} "
                  f"(sha256 {p['simulator_sha256'][:16]}...), deadlock rule '{p['deadlock_rule']}'")
        else:
            print(f"               {p['rule']}; box cells {p['box_cells']}")
            print(f"               {p['cross_check']}")
    else:
        b = r["budget"]
        print(f"  budget       {b['kind']} = {b['limit']}   (used {b['used']})")
        print(f"               {b.get('states_still_queued', '?')} states still queued -- "
              f"{b['note']}")
    c = r["cost"]
    print(f"  cost         states_expanded {c['states_expanded']}   "
          f"pruned {c['states_pruned_by_corner_rule']}   "
          f"max_depth {c['max_depth_reached']}   seconds {c['seconds']:.4f}")
    print()


def main():
    ap = argparse.ArgumentParser(description="The third level's solver: SOLVABLE / UNSOLVABLE / "
                                             "BUDGET_EXHAUSTED, and never a fourth.")
    ap.add_argument("--level", help="a level file to solve")
    ap.add_argument("--controls", action="store_true", help="the full control suite (default)")
    ap.add_argument("--read-control", action="store_true",
                    help=f"ONLY the frozen read-control; its counts live in READ_CONTROL ({_rc_moves_str()})")
    ap.add_argument("--max-states", type=int, default=None, help="budget: states expanded")
    ap.add_argument("--max-seconds", type=float, default=None, help="budget: wall-clock seconds")
    ap.add_argument("--deadlock", choices=("corner", "none"), default="corner",
                    help="the corner rule skips lost states; it never decides a verdict")
    ap.add_argument("--json", action="store_true", help="machine-readable verdict")
    a = ap.parse_args()

    if a.read_control and not a.level:
        print("=" * 100)
        print(f"THE READ-CONTROL -- the {_rc_count_word()} answers the project already has, "
              f"reproduced by the solver")
        print("=" * 100)
        bad = []
        for lname, want in READ_CONTROL:
            r = solve_text(open(level_path_(lname)).read(), name=lname, max_states=a.max_states,
                           max_seconds=a.max_seconds, deadlock=a.deadlock)
            ok = r["verdict"] == SOLVABLE and r["moves"] == want
            print(f"  {'PASS' if ok else 'FAIL'}  {lname}  verdict {r['verdict']}  "
                  f"moves {r['moves']}  want EXACTLY {want}  solution {r['solution']}")
            if not ok:
                bad.append(lname)
        print()
        print("=" * 100)
        print(f"{'READ-CONTROL PASSES: ' + _rc_moves_str() if not bad else 'READ-CONTROL FAILED: ' + ', '.join(bad)}")
        print("=" * 100)
        return 1 if bad else 0

    if a.level:
        text = open(a.level).read()
        name = os.path.basename(a.level)
        try:
            r = solve_text(text, name=name, max_states=a.max_states, max_seconds=a.max_seconds,
                           deadlock=a.deadlock)
        except ValueError as e:
            # NO VERDICT. A malformed level is not a level, and "unsolvable" is the one word that must
            # never be written about a board nobody could parse.
            print(f"  REFUSED      {name}: {e}")
            print("  no verdict   a level that is not a level has no solvability, and refusing is not a "
                  "fourth verdict")
            return 2
        if a.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            _report(r)
        return 0

    return _self_test()


def level_path_(n):
    return os.path.join(HERE, "levels", f"{n}.txt")


if __name__ == "__main__":
    sys.exit(main())
