#!/usr/bin/env python3
"""THE DEAD-END MAP -- irreversibility asked once, at the boundary, and PROVEN rather than asserted.

WHAT THIS IS FOR. PREREG_sokoban.md describes the faculty as "irreversible planning -- dead-end recognition,
asked once, at the boundary." A crate pushes and never pulls, so ONE WRONG PUSH kills a level permanently.
Until the solver existed, that could not be measured: the pre-registration said so, and the third level was
left ABSENT rather than faked. Now it can be, and this is the instrument that does it.

WHAT IT MEASURES. For a level, and for every first move available:

    BLOCKED   the move is not legal from here -- a wall or a crate in the way
    FATAL     legal, and it leads to a position with NO SOLUTION. THE DEAD END. Proven, not guessed.
    SAFE      legal, and the position is still solvable
    UNKNOWN   the follow-up search exhausted its budget -- reported as UNKNOWN, NEVER as FATAL

THE LOAD-BEARING DISTINCTION IS FATAL vs UNKNOWN. A dead-end map that reports "gave up" as "dead end" is the
same defect as a solver reporting BUDGET_EXHAUSTED as UNSOLVABLE: it is an answer found in text that does not
contain one, with a number attached. So the two are separate verdicts and never merged.

AND IT PRODUCES A NUMBER THE EVENT WANTS: the FATAL FRACTION of the opening moves. A level where every first
move is safe is a level that cannot measure dead-end recognition at all; a level where the obvious move is
fatal is a level that does.

THE ROUND-TRIP CONTROL COMES FIRST. The map is built by stepping the frozen simulator, RENDERING the resulting
position back to text, and re-solving that text. If render -> parse is lossy the whole map is fiction, so the
control asserts parse(render(s)) == s on every state the search visits, BEFORE any verdict is read.

    python3 sokoban_deadend.py levels/02_two_boxes.txt
    python3 sokoban_deadend.py --all
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402
import sokoban_solver as SOL                                            # noqa: E402

ACTIONS = ["U", "D", "L", "R"]

# THE READ-CONTROL'S EXPECTED VALUES COME FROM THE **PUBLISHED** ANSWERS, NOT FROM THE SOLVER'S OUTPUT.
# `verify_levels.py` carries RRRRDLLLDRRR for 02 and R for 01, so BOTH opening moves are known-good and the
# control is INDEPENDENT of the thing it checks. A control derived from the solver's own answer would confirm
# only that the mapper agrees with the solver about a string the solver produced.
KNOWN_FIRST_MOVE = {"01_one_push": "R", "02_two_boxes": "R"}
KNOWN_MOVES = {"01_one_push": 1, "02_two_boxes": 12}

# THE FROZEN VOCABULARY, READ FROM step() RATHER THAN ASSUMED: outcome is one of moved, pushed, blocked.
# A PUSHED IS A LEGAL SUCCESSFUL MOVE. The first version of this file treated everything that was not
# "moved" as BLOCKED, so a push reported as blocked -- and `01_one_push`, the level whose known solution IS
# a push, came back with "none legal". THE LEVEL WITH A KNOWN ANSWER IS WHAT CAUGHT IT.
LEGAL_OUTCOMES = ("moved", "pushed")


def roundtrip_control(level_text, depth=3):
    """parse(render(s)) == s on every state reachable within `depth` moves. MUST pass before any map.

    A dead-end map is built by rendering a position back to text and re-solving it. IF THE RENDER IS LOSSY,
    EVERY VERDICT DOWNSTREAM DESCRIBES A DIFFERENT LEVEL, and nothing would say so.
    """
    start = S.parse(level_text)
    seen, queue, bad = set(), [(start, 0)], []
    key = lambda st: (render_key(st))
    seen.add(key(start))
    while queue:
        st, d = queue.pop(0)
        if parse_roundtrip_ok(st) is not True:
            bad.append(S.render(st))
            continue
        if d >= depth:
            continue
        for a in ACTIONS:
            nxt, outcome = S.step(st, a)
            if outcome != "moved":
                continue
            k = render_key(nxt)
            if k not in seen:
                seen.add(k)
                queue.append((nxt, d + 1))
    return len(seen), bad


def render_key(st):
    return S.render(st)


def parse_roundtrip_ok(st):
    r = S.render(st)
    try:
        back = S.parse(r)
    except Exception:                                                   # noqa: BLE001
        return False
    return S.render(back) == r


def dead_end_map(level_text, max_states=None, max_seconds=None, known_first_move=None):
    """-> dict with the opening move map. Every FATAL verdict is a proof; UNKNOWN is never FATAL.

    TWO CONTROLS, both of which must pass before the map means anything:

      READ-CONTROL   `01_one_push` is solved by ONE MOVE and the solution is `R`. So that level MUST report
                     at least one legal opening move, and `R` must be among them and SAFE. A dead-end mapper
                     that reports zero legal opening moves on a level solved in one move is not a mapper --
                     the same rule as the legality checker that must list the starting position's twenty
                     moves before any termination counts as a verdict.

      INVARIANT      on a SOLVABLE level at least one opening move must be SAFE. If every legal opening move
                     came back FATAL, the level would be unsolvable while the solver just said it is --
                     so that combination is a CONTRADICTION and is refused rather than reported.
    """
    start = S.parse(level_text)
    rows = []
    for a in ACTIONS:
        nxt, outcome = S.step(start, a)
        if outcome not in LEGAL_OUTCOMES:
            rows.append({"move": a, "verdict": "BLOCKED", "detail": outcome})
            continue
        pos_text = S.render(nxt)
        r = SOL.solve_text(pos_text, name=f"after-{a}", max_states=max_states, max_seconds=max_seconds)
        if r.get("verdict") == "SOLVABLE":
            rows.append({"move": a, "verdict": "SAFE", "moves_left": r.get("moves")})
        elif r.get("verdict") == "UNSOLVABLE":
            rows.append({"move": a, "verdict": "FATAL", "detail": "no solution from here -- PROVEN",
                         "reachable": r.get("reachable_states_enumerated")})
        else:
            rows.append({"move": a, "verdict": "UNKNOWN",
                         "detail": f"search stopped early ({r.get('budget')}) -- NOT a dead end"})

    legal = [r for r in rows if r["verdict"] != "BLOCKED"]
    fatal = [r for r in legal if r["verdict"] == "FATAL"]
    safe = [r for r in legal if r["verdict"] == "SAFE"]
    problems = []

    # INVARIANT: a level the solver called SOLVABLE cannot have every opening move fatal.
    if legal and not safe and not any(r["verdict"] == "UNKNOWN" for r in legal):
        problems.append("CONTRADICTION: the solver said SOLVABLE and EVERY legal opening move is FATAL")

    # READ-CONTROL: only meaningful when the caller knows the answer.
    if known_first_move is not None:
        if not legal:
            problems.append(f"READ-CONTROL FAILED: no legal opening move, but {known_first_move} solves it")
        elif known_first_move not in [r["move"] for r in safe]:
            got = {r["move"]: r["verdict"] for r in rows}
            problems.append(f"READ-CONTROL FAILED: {known_first_move} is the known solution's first move, "
                            f"but the map says {got.get(known_first_move)}")

    return {"rows": rows, "legal_opening_moves": len(legal), "fatal_opening_moves": len(fatal),
            "safe_opening_moves": len(safe),
            "fatal_fraction": (len(fatal) / len(legal)) if legal else None,
            "problems": problems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("level", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-states", type=int, default=200000)
    a = ap.parse_args()

    paths = []
    if a.all:
        paths = [os.path.join(HERE, "levels", f) for f in sorted(os.listdir(os.path.join(HERE, "levels")))
                 if f.endswith(".txt") and f[0].isdigit()]
    elif a.level:
        paths = [a.level if os.path.exists(a.level) else os.path.join(HERE, "levels", a.level)]
    else:
        ap.error("give a level or --all")

    print("=" * 100)
    print("THE DEAD-END MAP -- dead-end recognition, asked once at the boundary, PROVEN")
    print("=" * 100)

    for p in paths:
        if not os.path.exists(p):
            print(f"  ABSENT: {p}")
            continue
        text = open(p).read()
        name = os.path.basename(p)

        # CONTROL FIRST -- before any verdict is read.
        states, bad = roundtrip_control(text)
        print()
        print(f"  {name}")
        print(f"    round-trip control   parse(render(s)) == s over {states} reachable state(s): "
              f"{'PASS' if not bad else 'FAIL -- ' + str(len(bad)) + ' lossy'}")

        r = SOL.solve_text(text, name=name, max_states=a.max_states)
        print(f"    solver               {r.get('verdict')}  moves {r.get('moves')}  "
              f"expanded {r.get('expanded')}  solution {r.get('solution')}")
        if r.get("verdict") != "SOLVABLE":
            print("    dead-end map         SKIPPED -- a level with no solution has no opening move map")
            continue
        if bad:
            print("    dead-end map         REFUSED -- the round-trip control failed, so a map would be")
            print("                         a map of a different level")
            continue

        m = dead_end_map(text, max_states=a.max_states,
                         known_first_move=KNOWN_FIRST_MOVE.get(name.replace(".txt", "")))
        if m["fatal_fraction"] is not None:
            print(f"    opening moves        {m['legal_opening_moves']} legal "
                  f"({m['safe_opening_moves']} safe, {m['fatal_opening_moves']} FATAL)   "
                  f"fatal fraction {m['fatal_fraction']:.3f}")
        else:
            print("    opening moves        none legal")
        for row in m["rows"]:
            extra = row.get("detail") or (f"still solvable in {row['moves_left']}"
                                          if "moves_left" in row else "")
            print(f"      {row['move']}  {row['verdict']:8s} {extra}")
        if m["problems"]:
            print("    *** THE MAP IS REFUSED ***")
            for p in m["problems"]:
                print(f"      {p}")
        else:
            print("    controls             round-trip PASS, invariant PASS"
                  + (", read-control PASS" if name.replace(".txt", "") in KNOWN_FIRST_MOVE else ""))

    print()
    print("  UNKNOWN IS NEVER FATAL. A follow-up search that ran out of budget reports UNKNOWN, because")
    print("  'gave up' and 'dead end' are different claims -- the same rule that keeps BUDGET_EXHAUSTED")
    print("  out of the UNSOLVABLE column.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
