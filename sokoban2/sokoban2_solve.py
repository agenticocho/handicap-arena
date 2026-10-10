#!/usr/bin/env python3
# sokoban2_solve.py -- an EXHAUSTIVE optimal solver, used for two jobs only:
#
#   1. VERIFY THE FROZEN REFERENCE SOLUTIONS independently (1, 12, 6) before
#      any entrant runs.  A result measured against an unverified reference is
#      a number, not a finding.
#   2. A DIAGNOSTIC, recorded but NEVER SCORED: whether the position after a
#      move is still solvable.  The cabinet's faculty is dead-end recognition;
#      without a solver you cannot tell "gave up on a live level" from "gave up
#      on a dead one".  The instrument is allowed to KNOW that; it is not
#      allowed to SCORE it.
#
# It imports the reader (never reimplements it) and the simulator's step().
# It optimises nothing and uses no heuristic: BFS over (player, boxes), which
# is exact and complete on a finite board.  Optimality is therefore PROVEN, not
# searched for -- BFS on unit-cost edges returns a shortest path.

from collections import deque

from sokoban_reader import ACTIONS
from sokoban2 import DELTAS, State, WORD_BLOCKED, step


def _apply(level, boxes, player, action):
    """Pure re-implementation of the reachability of one action, WITHOUT
    mutating, so the search can branch.  It re-uses the same DELTAS table the
    transition function uses -- one table, one set of rules."""
    dr, dc = DELTAS[action]
    dst = (player[0] + dr, player[1] + dc)
    if dst in level.walls or not (0 <= dst[0] < level.height
                                  and 0 <= dst[1] < level.width):
        return None
    if dst in boxes:
        beyond = (dst[0] + dr, dst[1] + dc)
        if (beyond in level.walls or beyond in boxes
                or not (0 <= beyond[0] < level.height
                        and 0 <= beyond[1] < level.width)):
            return None
        nb = set(boxes)
        nb.remove(dst)
        nb.add(beyond)
        return dst, frozenset(nb)
    return dst, boxes


def _cross_check_against_step(level):
    """The search's private `_apply` and the frozen `step()` MUST agree, or the
    solver and the simulator are two different games.  One control, run by the
    self-test, over every cell and every action."""
    bad = []
    for r in range(level.height):
        for c in range(level.width):
            if (r, c) in level.walls:
                continue
            for boxes in (frozenset(), frozenset(level.start_boxes)):
                if (r, c) in boxes:
                    continue
                for a in ACTIONS:
                    st = State(level)
                    st.player = (r, c)
                    st.boxes = set(boxes)
                    pos, word = step(st, a)
                    ref = _apply(level, boxes, (r, c), a)
                    if ref is None:
                        if word != WORD_BLOCKED or pos != (r, c):
                            bad.append(((r, c), a, word, "step disagrees "
                                        "on blocked"))
                    else:
                        want_pos, want_boxes = ref
                        if pos != want_pos or frozenset(st.boxes) != want_boxes:
                            bad.append(((r, c), a, word, "step disagrees on "
                                        "the resulting position"))
    return bad


def solve(level, limit=None):
    """BFS for a SHORTEST solution.

    -> {"solvable": bool, "optimal_moves": int|None, "plan": str|None,
        "n_states": int, "complete": bool}

    `complete` is False only when `limit` cut the search off, in which case
    `solvable` is a lower bound's negation and the caller must say so.
    """
    start = (level.start_player, frozenset(level.start_boxes))
    if start[1] == frozenset(level.targets):
        return {"solvable": True, "optimal_moves": 0, "plan": "",
                "n_states": 1, "complete": True}

    seen = {start: None}                    # state -> (prev_state, action)
    q = deque([start])
    n = 0
    while q:
        cur = q.popleft()
        n += 1
        if limit is not None and n > limit:
            return {"solvable": False, "optimal_moves": None, "plan": None,
                    "n_states": len(seen), "complete": False}
        player, boxes = cur
        for a in ACTIONS:
            nxt = _apply(level, boxes, player, a)
            if nxt is None:
                continue
            key = nxt
            if key in seen:
                continue
            seen[key] = (cur, a)
            if key[1] == frozenset(level.targets):
                plan = []
                node = key
                while seen[node] is not None:
                    prev, act = seen[node]
                    plan.append(act)
                    node = prev
                plan.reverse()
                return {"solvable": True, "optimal_moves": len(plan),
                        "plan": "".join(plan), "n_states": len(seen),
                        "complete": True}
            q.append(key)
    return {"solvable": False, "optimal_moves": None, "plan": None,
            "n_states": len(seen), "complete": True}


def is_solvable(level, boxes, player, limit=None):
    """Is THIS position still winnable?  Diagnostic only -- never scored."""
    sub = State(level)
    sub.boxes = set(boxes)
    sub.player = player
    if sub.solved:
        return True, 0
    probe = _Probe(level, frozenset(boxes), player)
    return _bfs_winnable(probe, limit)


class _Probe(object):
    __slots__ = ("level", "boxes", "player")

    def __init__(self, level, boxes, player):
        self.level = level
        self.boxes = boxes
        self.player = player


def _bfs_winnable(probe, limit=None):
    level = probe.level
    start = (probe.player, frozenset(probe.boxes))
    if start[1] == frozenset(level.targets):
        return True, 0
    seen = {start}
    q = deque([(start, 0)])
    n = 0
    while q:
        (player, boxes), depth = q.popleft()
        n += 1
        if limit is not None and n > limit:
            return None, None              # UNKNOWN, and it says so
        for a in ACTIONS:
            nxt = _apply(level, boxes, player, a)
            if nxt is None or nxt in seen:
                continue
            if nxt[1] == frozenset(level.targets):
                return True, depth + 1
            seen.add(nxt)
            q.append((nxt, depth + 1))
    return False, None


# ---------------------------------------------------------------------------
# THE VERIFICATION -- run before any entrant moves
# ---------------------------------------------------------------------------

#: The frozen claims, as the brief states them.  Verified, not assumed.
EXPECTED = {"01_one_push.txt": 1, "02_two_boxes.txt": 12,
            "03_the_corner_waiting.txt": 6}

LEVEL_FILES = ("01_one_push.txt", "02_two_boxes.txt",
               "03_the_corner_waiting.txt")


def verify_levels(levels):
    """-> (ok, rows).  `rows` is the evidence: plan, state count, proven."""
    rows = []
    ok = True
    for name in LEVEL_FILES:
        level = levels[name]
        res = solve(level)
        want = EXPECTED[name]
        got = res["optimal_moves"]
        agree = (got == want)
        ok &= agree
        rows.append({
            "level": name,
            "sha256": level.sha256,
            "expected_optimal": want,
            "proven_optimal": got,
            "agree": agree,
            "shortest_plan": res["plan"],
            "n_states_exhausted": res["n_states"],
            "search_complete": res["complete"],
            "boxes": level.n_boxes,
            "targets": level.n_targets,
            "enclosed": level.enclosed,
        })
    return ok, rows


def main():
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from sokoban2 import find_level
    levels = {name: find_level(name) for name in LEVEL_FILES}

    print("INDEPENDENT LEVEL VERIFICATION -- exhaustive BFS, no heuristics.")
    print("Nothing here is taken on trust: the search is complete over the")
    print("state space, so the answer is a PROOF of the optimum, not a find.")
    print()
    ok, rows = verify_levels(levels)
    for r in rows:
        mark = "ok  " if r["agree"] else "FAIL"
        print("  %s %-28s optimal %-3s (claim %-3s)  states %-8d plan %s"
              % (mark, r["level"], r["proven_optimal"], r["expected_optimal"],
                 r["n_states_exhausted"], r["shortest_plan"]))
    print()
    bad = []
    for name in LEVEL_FILES:
        bad.extend((name,) + tuple(x) for x in
                   _cross_check_against_step(levels[name]))
    if bad:
        print("  FAIL solver and step() disagree: %r" % (bad[:5],))
        ok = False
    else:
        print("  ok   the solver's branch rule and step() agree on every cell "
              "and every action")
    print()
    print("LEVEL VERIFICATION %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
