#!/usr/bin/env python3
"""SNAKE HARNESS -- THE CONTROLS. Every check here is shown the failure it exists to prevent.

A check that has never failed is indistinguishable from a check that cannot fail, and this repo has paid
for that lesson more than once. So each positive below is paired with the negative that must fire:

  positive                                    negative control
  ------------------------------------------  ----------------------------------------------------
  the solver's cycle covers the 25x25 torus    an ILLEGAL cycle step is rejected (assertion is exercised)
  a real bundle's score is reconstructed       a TAMPERED score block is refused
  from its own trace                           a TAMPERED trace row is refused
  a real bundle REPLAYS digest-for-digest      a TAMPERED move list fails the replay
  the score reader counts an eat and a reset   a trace whose rng counter is ODD is refused
  inside ONE tick                              a trace whose apple moved with no respawn is refused

    python3 test_snake_harness.py [bundle.json]
"""
import copy
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import snake_page as P            # noqa: E402
import snake_run as R             # noqa: E402
import snake_score as SC          # noqa: E402
import snake_solver as S          # noqa: E402

FAILS = []


def ctl(name, ok, detail=""):
    print("  %-4s %s%s" % ("ok" if ok else "FAIL", name, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)
    return ok


def row(before, after, tick=0):
    return {"tick": tick, "before": before, "after": after, "requested": "R"}


def st(rng, length, max_cells, apple, head=(0, 0), cells=None):
    return {"tick": 0, "head": list(head), "dir": [16, 0], "cells": cells or [], "length": length,
            "maxCells": max_cells, "apple": list(apple), "rng_calls": rng, "count": 0, "grid": 16,
            "canvas": [400, 400]}


def test_the_one_tick_case_that_needs_the_random_counter():
    """THE CASE snake_score.py EXISTS FOR: the head eats the apple, the respawn lands on the snake's own
    body, and the collision resets the board -- all inside ONE tick. `maxCells` goes 6 -> 7 -> 4 -> 5 and
    the population of cells is emptied, so the length/maxCells readings cannot count the eat; the page's
    random counter can, because every respawn is two Math.random calls."""
    trace = [row(st(10, 4, 6, (100, 100)), st(14, 0, 5, (200, 200)))]
    live = SC.score_trace(trace)
    ctl("one tick carrying an eat AND a reset is counted as 1 eaten, 1 death",
        live["eaten"] == 1 and live["deaths"] == 1,
        "eaten=%s deaths=%s checks=%s" % (live["eaten"], live["deaths"], json.dumps(live["checks"])))
    ctl("the maxCells reading is not used on a reset tick (it would say 6 -> 5, a lie)",
        live["checks"]["maxCells_reading_used"] == 0 and live["checks"]["rng_reading_used"] == 1)

    # NEGATIVE CONTROL: an odd random delta is not a half-respawn. The reader must refuse, not round.
    bad = [row(st(10, 4, 6, (100, 100)), st(13, 0, 5, (200, 200)))]
    live2 = SC.score_trace(bad)
    ctl("an ODD rng delta is refused rather than rounded", live2["problems"] != [],
        "problems=%s" % live2["problems"])

    # NEGATIVE CONTROL: an apple that moves with no respawn is impossible.
    bad2 = [row(st(10, 4, 6, (100, 100)), st(10, 4, 6, (200, 200)))]
    live3 = SC.score_trace(bad2)
    ctl("an apple that moved with no respawn is refused", live3["disagreements"] != [],
        "disagreements=%s" % live3["disagreements"])

    # NEGATIVE CONTROL: two readings of one event that disagree must be reported, not averaged.
    bad3 = [row(st(10, 4, 6, (100, 100)), st(12, 5, 6, (200, 200)))]   # 1 respawn, maxCells unchanged
    live4 = SC.score_trace(bad3)
    ctl("two readings of one tick that disagree are reported", live4["disagreements"] != [],
        "disagreements=%s" % live4["disagreements"])


def test_verify_positive_and_tamper(bundle_path):
    b = json.load(open(bundle_path))
    ok, reasons, live = SC.verify(b)
    ctl("a real bundle's score IS reconstructed from its own trace", ok, "; ".join(reasons[:2]))

    t = copy.deepcopy(b)
    t["score"]["eaten"] = t["score"]["eaten"] + 3
    ok2, why2, _ = SC.verify(t)
    ctl("NEGATIVE CONTROL: a flattered score block is refused", not ok2,
        (why2 or ["nothing"])[0])

    t2 = copy.deepcopy(b)
    if t2["trace"]:
        t2["trace"][0]["after"]["rng_calls"] += 2          # an event the trace says never happened
        ok3, why3, _ = SC.verify(t2)
        ctl("NEGATIVE CONTROL: a tampered trace row is refused", not ok3, (why3 or ["nothing"])[0])

    t3 = copy.deepcopy(b)
    t3["trace"] = []
    ok4, why4, _ = SC.verify(t3)
    ctl("NEGATIVE CONTROL: a bundle whose trace is gone does not verify", not ok4)


def test_replay_positive_and_tamper(bundle_path):
    """THE REPLAY IS THE SUFFICIENCY TEST AT ITS STRONGEST: the run is re-entered from (seed, moves) in
    the REAL page, and the state chain must come back digest for digest."""
    if not P.find_chrome():
        ctl("replay (SKIPPED: no chrome binary on this box)", False, "this is a SKIP, not a pass")
        return
    ok = R.replay_bundle(bundle_path)
    ctl("a real bundle REPLAYS digest-for-digest", ok)

    b = json.load(open(bundle_path))
    tampered = os.path.join(HERE, "probes", "_tamper_control.json")
    b2 = copy.deepcopy(b)
    i, why = _a_tamper_that_must_change_the_run(b2)
    if i is None:
        ctl("NEGATIVE CONTROL: a tampered move list fails the replay", False, why)
    else:
        with open(tampered, "w") as f:
            json.dump(b2, f)
        ok2 = R.replay_bundle(tampered)
        ctl("NEGATIVE CONTROL: a tampered move list fails the replay", not ok2,
            "edit: tick %d, %s -> %s (%s)" % (i, b["moves"][i], b2["moves"][i], why))
        os.remove(tampered)


def _a_tamper_that_must_change_the_run(b2):
    """-> (index, why) for ONE edited move that the GAME CANNOT ignore.

    THE FIRST VERSION OF THIS CONTROL FAILED, AND THE FAILURE IS A MEASUREMENT OF THE SUBJECT. It swapped a
    move for its opposite, three quarters of the way into the run -- and the tampered replay reproduced the
    recorded chain EXACTLY. That is not a hole in the replay: `snake.html`'s own keydown handler ignores a
    reversal along the axis the snake is already on (`snake.dx === 0` / `snake.dy === 0`), so an opposite
    request is a NO-OP, and a no-op leaves the run identical. A reverse-swap is not a tamper in this game.

    So the edit is a PERPENDICULAR turn, chosen from the direction the trace says the snake was actually
    moving at that tick: a perpendicular request always satisfies the handler's guard, so it always
    applies, and it always sends the snake somewhere the recorded run did not go.
    """
    for i in range(len(b2["moves"]) - 1, max(1, len(b2["moves"]) // 2) - 1, -1):
        move = b2["moves"][i]
        if move is None:
            continue
        dirv = b2["trace"][i]["before"]["dir"]
        if dirv[0] != 0:
            options = ["U", "D"]
        elif dirv[1] != 0:
            options = ["L", "R"]
        else:
            continue
        new = options[0] if move != options[0] else options[1]
        if new != move:
            b2["moves"][i] = new
            return i, "perpendicular to the direction the trace says the snake was moving"
    return None, "no tick in this trace admits a perpendicular edit"


def test_the_prompt_varies(bundle_paths):
    """THE CONTROL THAT KEEPS A CONSTANT ANSWER FROM BEING A HARNESS ARTIFACT.

    The recorded model run answered the same letter on every turn of every episode. That is a statement
    about the entrant ONLY IF the question changed. The first version of this control asserted that every
    turn's prompt was distinct -- and it FAILED on all six model bundles at 29 distinct out of 120, which
    is CORRECT behaviour and a measurement of the board rather than a defect: a snake walking straight
    across a wrapping board 25 cells wide returns to its own state every 25 ticks (same head, same body
    shape, same apple), so `ceil(120/25) + 4 = 29` distinct questions is exactly what 120 straight-line
    turns contain. Both readings are asserted, separately and with the reason stated:

      (1) THE QUESTION IS NOT CONSTANT -- every turn inside the first board-width is a distinct prompt;
      (2) THE ANSWER WAS CONSTANT ACROSS DISTINCT QUESTIONS -- for a model bundle, the set of answers has
          one member while the set of questions has many. THAT is the finding, and this is its evidence.
    """
    for p in bundle_paths:
        if not os.path.exists(p):
            continue
        b = json.load(open(p))
        lc = b["instrument"]["subject"]["live_constants"]
        w = lc["canvas"][0] // lc["grid"]
        prompts, answers = [], set()
        for r in b["trace"]:
            st = dict(r["before"])
            st["grid"], st["canvas"], st["count"] = lc["grid"], lc["canvas"], 0
            prompts.append(R.prompt_for(st, 0))
            if "turn" in r:
                answers.add(r["requested"])
        window = prompts[:min(w, len(prompts))]
        ctl("the question is not constant in %s (%d distinct in the first %d turns, %d in %d)"
            % (os.path.basename(p), len(set(window)), len(window), len(set(prompts)), len(prompts)),
            len(set(window)) == len(window))
        if answers:
            ctl("...and the answer is constant across those distinct questions in %s (%s)"
                % (os.path.basename(p), sorted(x for x in answers if x)),
                len(answers) == 1)


def main():
    bundle = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "probes", "SNAKE_baseline-cycle-shortcut_s1.json")
    model_bundles = sorted(glob.glob(os.path.join(HERE, "probes", "SNAKE_Ternary*s*.json")))
    print("=" * 100)
    print("SNAKE HARNESS -- THE CONTROLS   (bundle: %s)" % os.path.relpath(bundle, HERE))
    print("=" * 100)
    print("  solver:")
    ctl("the torus cycle is complete, legal and closed on every size tried", S.selftest())
    print("  score reader:")
    test_the_one_tick_case_that_needs_the_random_counter()
    print("  reconstruction from the bundle:")
    if os.path.exists(bundle):
        test_verify_positive_and_tamper(bundle)
        print("  re-entering the recorded run:")
        test_replay_positive_and_tamper(bundle)
    else:
        ctl("bundle present (%s)" % bundle, False, "run a baseline first")
    print("  the question the entrant is asked:")
    test_the_prompt_varies([bundle] + model_bundles)
    print("=" * 100)
    print("  %d control(s) FAILED" % len(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
