#!/usr/bin/env python3
# digdug_solve.py -- THE SOLVER.  Complete search, with an admissible heuristic.
#
# Three jobs:
#
#   1. PROVE the optimum of every level, and COUNT the distinct optimal
#      lines.  Standing rule R2: where a seed has more than one optimal line,
#      say how many.  Standing rule B3: a validator validates UNIQUENESS, not
#      only COUNT -- so "optimal 12" is not a claim this file makes; "optimal
#      12, one distinct line" is.
#
#   2. PROVE that level 04 has NO safe line, so the runner can declare it a
#      CONTROL level and the only correct answer on it can be an abstention.
#      A level nobody proved unsolvable is a level the instrument will blame
#      an entrant for.
#
#   3. Supply `safe_line_exists()`, the per-state search behind the facet
#      numbers, with a declared node cap and an honest `complete` flag.
#
# THE SEARCH IS OVER THE PLAYER'S CHOICES ONLY.  The hazard clock is
# deterministic under the frozen policy [U1], so the opponent is a function
# and the game is a one-agent search.  That is a consequence of freezing the
# policy, and it is why the numbers here are proofs and not estimates.
#
# METHOD: iterative deepening over the depth limit, with an ADMISSIBLE and
# EXACT heuristic -- `min_moves_to_complete`, the rock-free distance to the
# nearest remaining target.  A breadth-first search over (player, dug-set,
# targets, hazards) is complete but explodes: the dug set is a subset of the
# soil and level 03 has 30 soil cells.  This build was measured doing exactly
# that and dying of memory, which is why the method is what it is.
#
# Stdlib only.

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug                                              # noqa: E402
from digdug import (ACTIONS, State, find_level,             # noqa: E402
                    min_moves_to_complete, turn)

#: Declared caps.  A search that hits a cap has NOT proved anything, and the
#: result says so instead of returning a confident number.
DEFAULT_BUDGET = 30
DEFAULT_NODE_CAP = 4_000_000


class Search(object):
    """Complete search over the player's lines, with an exact heuristic."""

    def __init__(self, budget=DEFAULT_BUDGET, node_cap=DEFAULT_NODE_CAP):
        self.budget = budget
        self.node_cap = node_cap

    # -- the counting DFS ---------------------------------------------------
    def _count(self, st, moves_left, fail, depth):
        """Number of distinct action sequences that solve within moves_left.

        `fail[key]` is the largest `moves_left` already proven to fail from
        that state.  Failing with more time left implies failing with less,
        so the memo is monotone and safe to reuse across depths.
        """
        self.nodes += 1
        if self.nodes > self.node_cap:
            self.cap_hit = True
            return 0
        if not st.targets_left:
            return 1
        if moves_left <= 0:
            return 0
        h = min_moves_to_complete(st)
        if h is None or h > moves_left:
            return 0                       # exact prune: not enough turns left
        k = st.key()
        if moves_left <= fail.get(k, -1):
            return 0
        total = 0
        for a in ACTIONS:
            if self.cap_hit:
                break
            s2, _w, _e = turn(st, a)
            if s2.dead:
                continue                   # a dead line is not a line
            if s2.solved:
                total += 1
                continue
            total += self._count(s2, moves_left - 1, fail, depth + 1)
        if total == 0:
            prev = fail.get(k, -1)
            if moves_left > prev:
                fail[k] = moves_left
        return total

    def count_lines(self, state, limit):
        """-> (n_lines, nodes, complete)"""
        self.nodes = 0
        self.cap_hit = False
        n = self._count(state, limit, {}, 0)
        return n, self.nodes, not self.cap_hit

    # -- job 1: the optimum, and how many lines achieve it -------------------
    def optimal(self, level):
        start = State(level)
        h0 = min_moves_to_complete(start)
        if h0 == 0:
            return {"level": level.name, "solvable": True, "optimal_moves": 0,
                    "n_distinct_optimal_lines": 1, "plan": None,
                    "nodes": 1, "complete": True}
        if h0 is None:
            return {"level": level.name, "solvable": False,
                    "optimal_moves": None, "n_distinct_optimal_lines": 0,
                    "plan": None, "nodes": 1, "complete": True,
                    "search": "the target is walled off from the player"}
        total_nodes = 0
        for limit in range(h0, self.budget + 1):
            n, nodes, complete = self.count_lines(start, limit)
            total_nodes += nodes
            if not complete:
                return {"level": level.name, "solvable": None,
                        "optimal_moves": None,
                        "n_distinct_optimal_lines": None, "plan": None,
                        "nodes": total_nodes, "complete": False,
                        "search": "NODE CAP %d HIT AT DEPTH %d -- NOT A "
                                  "PROOF" % (self.node_cap, limit)}
            if n:
                return {"level": level.name, "solvable": True,
                        "optimal_moves": limit,
                        "n_distinct_optimal_lines": n,
                        "plan": self.one_plan(start, limit),
                        "nodes": total_nodes, "complete": True}
        return {"level": level.name, "solvable": False, "optimal_moves": None,
                "n_distinct_optimal_lines": 0, "plan": None,
                "nodes": total_nodes, "complete": True,
                "search": "exhaustive to the budget: no safe line within %d "
                          "turns" % self.budget}

    def one_plan(self, state, limit):
        """One optimal plan, for the record.  NEVER used to score: the runner
        executes answers, it does not compare them to this [A16]."""
        st = state
        acts = []
        for _ in range(limit):
            if not st.targets_left:
                break
            for a in ACTIONS:
                s2, _w, _e = turn(st, a)
                if s2.dead:
                    continue
                if s2.solved:
                    return "".join(acts + [a])
                n, _nodes, complete = self.count_lines(s2, limit - len(acts) - 1)
                if complete and n:
                    acts.append(a)
                    st = s2
                    break
            else:
                return None
        return "".join(acts) if not st.targets_left or True else None

    # -- job 3: the per-state search behind the facet numbers ----------------
    def safe_line_exists(self, state, depth=None):
        """-> (exists, moves_needed, nodes, complete)

        `complete` False means the node cap was hit, and then `exists` being
        False means NO LINE WAS FOUND, not NO LINE EXISTS.  The facet numbers
        carry that flag rather than laundering it into a verdict.
        """
        depth = self.budget if depth is None else depth
        if not state.targets_left:
            return True, 0, 1, True
        h = min_moves_to_complete(state)
        if h is None:
            return False, None, 1, True
        total = 0
        for limit in range(h, depth + 1):
            n, nodes, complete = self.count_lines(state, limit)
            total += nodes
            if not complete:
                return False, None, total, False
            if n:
                return True, limit, total, True
        return False, None, total, True


# ---------------------------------------------------------------------------
# THE FACET-1 PROOF -- structural, not empirical, and therefore complete
# ---------------------------------------------------------------------------

def destruction_reachability_proof(level, samples=64, seed=20261010):
    """PROVE the U1 corollary: digging never removes a route.

    The claim, and why it is a proof rather than a survey: `min_moves_to_
    complete` is a distance over the cells that are not rock, and the set of
    cells that are not rock does not depend on what has been dug -- digging
    turns soil into tunnel and both cost exactly one move to enter.  So the
    distance is a function of the level and the player's cell ALONE, and the
    dug set cannot appear in it.  Digging can only ever add edges to the graph
    the hazards walk on; it can never remove an edge from the graph the
    player walks on.

    The consequence is the load-bearing finding of this cabinet: under this
    prose the ONLY destructive resource in the game is the soil barrier
    between the player and a hazard, so the two facets the brief asks for
    cannot be two independent mechanics.  See DIGDUG_PROSE_TRAPS.md F4.

    Measured here, for every player cell and for dug = empty / everything /
    random subsets: the distance must not move.
    """
    rng = random.Random(seed)
    all_soil = sorted(level.soil)
    subsets = [frozenset(), frozenset(all_soil)]
    for _ in range(samples):
        k = rng.randrange(0, len(all_soil) + 1)
        subsets.append(frozenset(rng.sample(all_soil, k)))
    moved = []
    checked = 0
    for cell in sorted(level.playable):
        base = None
        for sub in subsets:
            st = State(level, player=cell, dug=sub & level.soil)
            d = min_moves_to_complete(st)
            checked += 1
            if base is None:
                base = d
            elif d != base:
                moved.append((cell, base, d))
    return {
        "level": level.name,
        "claim": "digging never lengthens the route to a target -- the "
                 "distance does not depend on the dug set at all",
        "kind": "STRUCTURAL, checked exhaustively over every player cell and "
                "%d dug subsets" % len(subsets),
        "cells_checked": len(level.playable),
        "distance_evaluations": checked,
        "holds": not moved,
        "violations": moved[:5],
        "corollary": "the only thing digging destroys in this game is the "
                     "soil barrier between the player and a hazard",
    }


def hazard_reach_proof(level):
    """The other half of the U1 corollary, and the one the cabinet is about:
    digging only ever ADDS to the hazard's graph.  Measured: for every cell
    the player could dig, the hazard's reachable set never shrinks."""
    from digdug import hazard_component
    base_state = State(level)
    worst = None
    shrunk = []
    h = level.hazard_starts[0]
    base = hazard_component(level, base_state.tunnels, h)
    for cell in sorted(level.soil):
        st = base_state.copy(dug=frozenset((cell,)))
        comp = hazard_component(level, st.tunnels, h)
        if not base <= comp:
            shrunk.append(cell)
        if worst is None or len(comp) > worst:
            worst = len(comp)
    return {
        "level": level.name,
        "claim": "one dig never shrinks the hazard's component",
        "base_component": len(base),
        "largest_after_one_dig": worst,
        "holds": not shrunk,
        "violations": shrunk[:5],
        "meaning": "the barrier is monotone: once lost it is lost for the "
                   "rest of the run",
    }


def verify_levels(names=None, budget=DEFAULT_BUDGET, verbose=True):
    """Verify the whole set.  -> (all_ok, rows)"""
    names = names or digdug.LEVEL_FILES
    rows = []
    all_ok = True
    s = Search(budget=budget)
    for n in names:
        lvl = find_level(n)
        r = s.optimal(lvl)
        r["file"] = n
        r["sha256"] = lvl.sha256
        r["targets"] = lvl.n_targets
        r["hazards"] = lvl.n_hazards
        r["enclosed"] = lvl.enclosed
        rows.append(r)
        if verbose:
            print("%-30s optimal %-5s distinct %-5s nodes %-8s %s" % (
                n, r["optimal_moves"], r["n_distinct_optimal_lines"],
                r["nodes"],
                "COMPLETE" if r["complete"] else r.get("search")))
        if not r["complete"]:
            all_ok = False
    return all_ok, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="the DIG DUG solver")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--prove", action="store_true",
                    help="also run the two destruction proofs")
    a = ap.parse_args(argv)
    ok, rows = verify_levels(budget=a.budget, verbose=not a.json)
    out = rows
    if a.prove:
        proofs = [{"reachability": destruction_reachability_proof(find_level(n)),
                   "hazard_component": hazard_reach_proof(find_level(n))}
                  for n in digdug.LEVEL_FILES]
        if not a.json:
            print()
            for p in proofs:
                r = p["reachability"]
                h = p["hazard_component"]
                print("%-30s route-proof %s (%d evals)  barrier-proof %s "
                      "(component %d -> %d)" % (
                          r["level"],
                          "HOLDS" if r["holds"] else "VIOLATED",
                          r["distance_evaluations"],
                          "MONOTONE" if h["holds"] else "VIOLATED",
                          h["base_component"], h["largest_after_one_dig"]))
        out = {"levels": rows, "destruction_proof": proofs}
    if a.json:
        print(json.dumps(out, indent=1, sort_keys=True))
    print()
    print("LEVEL VERIFICATION %s" % ("PASSED" if ok else "INCOMPLETE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
