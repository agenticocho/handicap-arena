#!/usr/bin/env python3
"""SNAKE -- THE SCORE, RECONSTRUCTED FROM THE RECORDED TRACE. One definition, imported by everything.

GAME_CONTRACT.md: *the recorded state must be a sufficient statistic for the score -- the scored outcome
can be recomputed from the recorded state alone.* This module is what makes that true rather than
claimed, and it is the ONLY place the score is computed: the driver, the verifier and the test all call
it, so a number and its reconstruction cannot drift apart.

WHAT THE TRACE HAS TO CARRY, and why each field is load-bearing:

  rng_calls  the game's own count of `Math.random` calls (the wrapper counts them at the one call site the
             page has -- `getRandomInt`). The page consumes a random pair on exactly two events: an apple
             being EATEN, and a RESET after a self-collision. Nothing else in the file calls it.
  length     `snake.cells.length` after the tick. A reset sets `snake.cells = []` and nothing else in the
             file can empty that array, so `length == 0` after a tick IS the reset -- an exact signal.
  maxCells   the snake's length cap: +1 per apple eaten, back to 4 on a reset. A SECOND, INDEPENDENT
             reading of the same event count, which is why both are recorded and compared below.
  apple      the apple's cell o the tick. Independent again: the apple moves only when it is eaten or
             when the board resets.
  head/dir/  the rest of the live state, carried because a bundle that cannot be replayed is a claim
  cells      about a run nobody can re-enter.

THE ARITHMETIC, and the one case that needs the random counter rather than the length: if the head eats the
apple and the respawn lands ON the snake's own body, the page ticks `maxCells` twice inside one tick
(the `forEach` continues over the old array). So `maxCells` alone under-counts in exactly that case, while
the random counter counts both respawns. THE TWO READINGS ARE COMPARED EVERY TICK and any disagreement is
returned, not swallowed.
"""


def _respawns(before, after):
    """random pairs the page consumed during this tick -> number of apple respawns. Each respawn is two
    `Math.random` calls (x and y). An ODD delta is not a score of 2.5, it is a broken trace."""
    d = after["rng_calls"] - before["rng_calls"]
    if d < 0:
        return None, "rng_calls went BACKWARDS (%d -> %d)" % (before["rng_calls"], after["rng_calls"])
    if d % 2:
        return None, "rng_calls advanced by an ODD number (%d): a respawn takes two calls" % d
    return d // 2, None


def score_trace(trace):
    """THE SCORE, FROM THE RECORDED ROWS ALONE. -> dict(eaten, best_life, deaths, ticks, checks,
    disagreements, per_tick)

    eaten      apples eaten across the episode (survives resets -- the page resets rather than ending)
    best_life  the longest the snake ever got, in apples (max of `maxCells - 4`): the arcade reading,
               and the one reading that is exact even across a reset
    deaths     self-collisions the page performed
    """
    eaten = 0
    deaths = 0
    best_life = 0
    per_tick = []
    disagreements = []
    notes = []
    problems = []
    checks = {"ticks": 0, "ticks_with_respawn": 0, "maxCells_reading_used": 0,
              "rng_reading_used": 0, "both_readings_compared": 0}
    for row in trace:
        before, after = row["before"], row["after"]
        checks["ticks"] += 1
        respawns, err = _respawns(before, after)
        if err:
            problems.append("tick %s: %s" % (row.get("tick"), err))
            per_tick.append({"tick": row.get("tick"), "eaten": 0, "deaths": 0, "why": "unreadable trace"})
            continue
        # THE RESET IS AN EXACT STATE SIGNAL: only the self-collision branch empties `snake.cells`.
        reset = (after["length"] == 0)
        # reading 1 -- the page's own maxCells, which a reset hides
        by_max = (after["maxCells"] - before["maxCells"]) if not reset else None
        # reading 2 -- the respawns the page performed, minus the one a reset also performs
        by_rng = respawns - (1 if reset else 0)
        if by_rng < 0:
            problems.append("tick %s: a reset with no respawn -- the page always respawns on reset"
                            % row.get("tick"))
            by_rng = 0
        if by_max is not None:
            checks["both_readings_compared"] += 1
            checks["maxCells_reading_used"] += 1
            if by_max != by_rng:
                disagreements.append({"tick": row.get("tick"), "maxCells_reading": by_max,
                                      "rng_reading": by_rng, "reset": reset})
        else:
            checks["rng_reading_used"] += 1
        if respawns:
            checks["ticks_with_respawn"] += 1
        # a third reading: the apple cannot MOVE without a respawn. (The converse is not a defect -- a
        # respawn may land on the cell it already occupied, 1 in 625 -- so that case is a NOTE, because a
        # check that fires on a legal outcome is a check that will be ignored on the day it matters.)
        apple_moved = tuple(after["apple"]) != tuple(before["apple"])
        if apple_moved and respawns == 0:
            disagreements.append({"tick": row.get("tick"), "apple_moved": True, "respawns": 0,
                                  "why": "the apple moved in a tick with no respawn"})
        elif (not apple_moved) and respawns > 0:
            notes.append({"tick": row.get("tick"),
                          "why": "a respawn landed on the cell the apple already held: legal, and it "
                                 "makes the apple reading blind this tick"})
        eaten += by_rng
        deaths += 1 if reset else 0
        best_life = max(best_life, after["maxCells"] - 4)
        per_tick.append({"tick": row.get("tick"), "eaten": by_rng, "deaths": 1 if reset else 0,
                         "length_after": after["length"], "maxCells_after": after["maxCells"],
                         "apple_after": after["apple"], "reset": reset})
    return {"eaten": eaten, "best_life": best_life, "deaths": deaths, "ticks": len(trace),
            "checks": checks, "disagreements": disagreements, "notes": notes, "problems": problems,
            "per_tick": per_tick}


def verify(bundle):
    """-> (ok, [reasons]). Recomputes the score from `bundle['trace']` and compares it with the score the
    bundle records. THE POINT IS THE COMPARISON: a bundle whose stated score does not follow from its own
    trace is a number carried with no carrier, which is the defect the game contract exists to refuse."""
    rec = (bundle.get("score") or {})
    live = score_trace(bundle.get("trace") or [])
    reasons = list(live["problems"])
    for k in ("eaten", "best_life", "deaths", "ticks"):
        if rec.get(k) != live[k]:
            reasons.append("recorded score.%s = %r, but the trace alone gives %r" % (k, rec.get(k), live[k]))
    if live["disagreements"]:
        reasons.append("%d tick(s) where two independent readings of the same event disagree: %s"
                       % (len(live["disagreements"]), live["disagreements"][:3]))
    return (not reasons), reasons, live


if __name__ == "__main__":
    import json
    import sys
    b = json.load(open(sys.argv[1]))
    ok, reasons, live = verify(b)
    print(json.dumps({k: live[k] for k in ("eaten", "best_life", "deaths", "ticks", "checks")}, indent=1))
    for r in reasons:
        print("  FAIL %s" % r)
    print("  RECONSTRUCTION %s" % ("OK -- the recorded trace alone reproduces the recorded score"
                                   if ok else "REFUSED"))
    sys.exit(0 if ok else 1)
