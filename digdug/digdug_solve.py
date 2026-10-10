#!/usr/bin/env python3
# digdug_solve.py -- EXHAUSTIVE search for the DIG DUG cabinet, and the reason
# this cabinet is allowed to say "provably lost" out loud.
#
# WHY THIS FILE IS NOT OPTIONAL HERE.  The Sokoban dossier refused to write its
# third level: "to claim a level has no solution you must be able to prove it,
# and the project hasn't built one".  DIG DUG NEEDS a lost level, because R1
# makes abstention a SCOREABLE answer and because FACET 1 is about a state the
# board cannot announce.  So no optimum in this cabinet is asserted from a level
# file: every one is produced here, and every one is produced BEFORE any entrant
# runs.
#
# THE STATE KEY, AND WHY IT IS ENOUGH
#
#     (player, frozenset(tunnels), frozenset(targets_left), hazards)
#
# There is no clock in it, and three facts make that sound rather than lucky:
#   * step() is deterministic and the hazard tie-break is frozen (reading
#     order), so a plan replays the same way on any machine, with no seed;
#   * the tunnel set is MONOTONE -- a ply adds a cell or changes nothing, and
#     nothing in the contract removes one ("dug ground never returns to soil");
#   * the objective is `all_targets` and collecting SHRINKS `targets`, so
#     progress lives inside the key.  Under `objective=survive_n` or
#     `target_persistence=persists_as_marker` the key is unsound and `refuse()`
#     raises instead of producing a number that looks like a proof.
#
# PROOF GRADES, NAMED IN EVERY ROW.  The reachable space of an OPEN level is a
# subset of 2^(soil cells) and is not exhaustible on this box, so claiming
# "exhaustive" for one would be a confident, brief, unfalsifiable lie.  Hence:
#
#   exhaustive   the frontier EMPTYED BY ITSELF: every reachable state was
#                expanded and no state was dropped.  Only then is a claim of
#                LOSS licensed, because loss is a statement about every plan of
#                every length.  04 is built CLOSED (a cavern ringed by rock, so
#                the only cell that can ever be dug is the pearl's own) exactly
#                so that it can earn the grade.
#   bounded:K    the search stopped at K plies or at the state cap.  A WIN found
#                inside K is still a PROVEN OPTIMUM -- "no shorter win exists"
#                is not a guess when every shorter plan was played out -- but a
#                failure inside K is only `no_win_within_K`, and this file
#                refuses to print the word "lost" for such a row.
#
# A state from which the search was cut off is `uncertain`, and `uncertain` is
# reported as null.  It is never folded into False.  That distinction -- unknown
# is not no -- is the whole difference between a solver and a rumour.
#
# Stdlib only.

import argparse
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug                                                    # noqa: E402
from digdug import (FROZEN, ACTIONS, MOVE_LETTERS, State,       # noqa: E402
                    resolve_turn, min_hazard_distance)

#: The search alphabet: every legal answer, WAIT included.  [D-STOP] puts WAIT in
#: the alphabet, so leaving it out would let this file call a level lost when it
#: is merely unwinnable-without-standing-still.
SEARCH_ACTIONS = tuple(ACTIONS)


def search_actions(policy):
    """The action set a search may expand under `policy`.

    DERIVED from the reading, never lifted from the global alphabet.  A proof of
    optimality that searched an action the game forbids is a proof about a
    different game, and `wait_legal = False` [D-STOP] makes `.` exactly that --
    `step()` raises on it, which is the right behaviour for a runner and a wrong
    one for a search that did not ask.
    """
    return tuple(a for a in ACTIONS if policy.wait_legal or a != ".")

#: cap on expanded states, so a big level reports NOT PROVEN instead of eating
#: the 3 GB box.  Hitting the cap is a FAILURE of the horizon check, not a
#: verdict -- see `horizon_ok`.
MAX_STATES = 45000

#: how deep the graph is chased, in plies.  Must be >= the runner's attempt
#: budget for the per-ply diagnostic to be EXACT rather than true-so-far, and
#: control [HZ] asserts the inequality instead of assuming it.
HORIZON = 12


class NotProven(Exception):
    """The search hit its cap.  An honest refusal, never a verdict."""


def refuse(policy):
    """Say NO rather than compute a plausible wrong proof.  Header explains."""
    if policy.objective != "all_targets":
        raise NotProven("the state key carries no clock, so it cannot prove "
                        "anything about objective=%r" % policy.objective)
    if policy.target_persistence != "removed":
        raise NotProven("under target_persistence=%r the objective advances "
                        "without `targets` shrinking, which the key cannot see"
                        % policy.target_persistence)
    return True


# ---------------------------------------------------------------------------
# THE GRAPH
# ---------------------------------------------------------------------------

def graph(level, policy=FROZEN, depth=HORIZON, max_states=MAX_STATES,
          cache=None):
    """Every state reachable within `depth` plies, and every edge among them.

    -> {"dist","children","wins","winset","n_states","start","exhaustive",
        "truncated_at_depth","expanded_to"}

    EVERY state that enters the graph is expanded, which is what makes
    `exhaustive` mean something: it says the set is closed under the rules, not
    merely "the queue happened to empty".  `depth` and `max_states` can only
    stop a NEW state from being admitted, and either one sets `truncated`.

    A winning state is a LEAF: [D-END] ends the run on the winning ply, so no
    plan continues past it and "wins, then keeps playing" is not an object.
    """
    refuse(policy)
    start_state = State(level, policy)
    start = start_state.snapshot()
    dist = {start: 0}
    children = {start: []}
    wins = []
    winset = set()
    q = deque()
    truncated = None
    n = 1
    if start_state.objective_met():
        wins.append(start)
        winset.add(start)
    else:
        q.append(start)
    while q:
        cur = q.popleft()
        d = dist[cur]
        kids = []
        for act in search_actions(policy):
            probe = State.restore(level, cur, policy)
            res = resolve_turn(probe, act)
            if res["killed"] and not res["solved"]:
                continue                 # death is absorbing; no plan wins
            nxt = probe.snapshot()
            if res["solved"]:
                kids.append((act, nxt))
                if nxt not in winset:
                    winset.add(nxt)
                    wins.append(nxt)
                    if nxt not in dist:
                        dist[nxt] = d + 1
                        n += 1
                continue
            if nxt in dist:
                kids.append((act, nxt))
                continue
            if depth is not None and d + 1 > depth:
                truncated = d + 1 if truncated is None else truncated
                continue
            if n >= max_states:
                truncated = d + 1 if truncated is None else truncated
                continue
            dist[nxt] = d + 1
            children[nxt] = []
            q.append(nxt)
            n += 1
            kids.append((act, nxt))
        children[cur] = kids
    g = {"dist": dist, "children": children, "wins": wins, "winset": winset,
         "n_states": n, "start": start, "exhaustive": truncated is None,
         "truncated_at_depth": truncated,
         "expanded_to": max([d for s, d in dist.items()
                             if s not in winset] or [0])}
    if cache is not None:
        cache[(level.name, level.sha256, policy.name, depth, max_states)] = g
    return g


def backward_wins(g):
    """min plies to a win, for every state in the graph.  absent = no win seen."""
    parents = {}
    for s, kids in g["children"].items():
        for a, t in kids:
            parents.setdefault(t, []).append(s)
    dw = {w: 0 for w in set(g["wins"])}
    q = deque(dw)
    while q:
        cur = q.popleft()
        for p in parents.get(cur, ()):
            if p not in dw:
                dw[p] = dw[cur] + 1
                q.append(p)
    return dw, parents


def certain_no(g, dw, parents):
    """States the search can POSITIVELY call "no win from here".

    In a CLOSED graph (exhaustive) that is every state with no distance.  In a
    TRUNCATED one it is no state at all, because "the search did not find a win"
    is a statement about the search.  Collapsing those two is exactly how a
    solver starts reporting `false` where it means `unknown` -- so the caller
    gets null, and the bundle says so.
    """
    if not g["exhaustive"]:
        return set()
    return {s for s in g["dist"] if s not in dw}


def count_shortest_plans(g, D):
    """How many DISTINCT optimal lines a level has.  [R2] demands the number.

    "the optimum" is a fact; "the plan" is not, and a cabinet that pretends
    otherwise starts ranking models against one route out of many.  Counted by
    DFS over action strings whose FIRST win is exactly at depth D -- which is
    the same thing as an optimal plan, because [D-END] ends the run on the
    winning ply and a deterministic board makes a path and a string one object.
    """
    memo = {}
    winset = g["winset"]

    def rec(state, r):
        """# of action strings of length EXACTLY r whose first win lands at r."""
        if r <= 0:
            return 0
        key = (state, r)
        if key in memo:
            return memo[key]
        total = 0
        for a, t in g["children"].get(state, ()):
            if t in winset:
                if r == 1:
                    total += 1
                continue            # a win earlier than r is not an optimal plan
            total += rec(t, r - 1)
        memo[key] = total
        return total

    return rec(g["start"], D)


def one_plan(g, D):
    """One representative shortest winning line, as a string."""
    wins_at_D = [w for w in g["wins"] if g["dist"][w] == D]
    if not wins_at_D:
        return None
    goals = set(wins_at_D)
    q = deque([(g["start"], "")])
    while q:
        s, path = q.popleft()
        for a, t in g["children"].get(s, ()):
            np = path + a
            if t in goals and len(np) == D:
                return np
            if len(np) < D:
                q.append((t, np))
    return None


# ---------------------------------------------------------------------------
# THE VERIFICATION THE RUNNER FREEZES ON
# ---------------------------------------------------------------------------

def verify_level(level, claim=None, policy=FROZEN, depth=HORIZON,
                 budget=None):
    """Prove the optimum (or the loss).  -> a row a reader can audit."""
    g = graph(level, policy, depth)
    dw, parents = backward_wins(g)
    no = certain_no(g, dw, parents)
    winnable = bool(g["wins"])
    D = (min(g["dist"][w] for w in g["wins"]) if winnable else None)
    n_plans = (count_shortest_plans(g, D) if winnable else 0)
    # The per-ply diagnostic asks "can this run still be won inside its own
    # remaining turns".  That is EXACT only while the graph reaches past the
    # budget, so the relationship is checked, not assumed.
    horizon_ok = (g["truncated_at_depth"] is None
                  or budget is None
                  or g["truncated_at_depth"] > budget)
    row = {
        "level": level.name,
        "sha256": level.sha256,
        "reading": policy.name,
        "winnable": winnable,
        "proven_optimal": D,
        "distinct_shortest_plans": n_plans,
        "has_multiple_optima": (n_plans or 0) > 1,
        "shortest_plan": one_plan(g, D) if D else None,
        "n_states_explored": g["n_states"],
        "proof_grade": ("exhaustive" if g["exhaustive"]
                        else "bounded:%s" % (g["expanded_to"] + 1)),
        "unexpanded_states": 0 if g["exhaustive"] else "see truncated_at_depth",
        "exhaustive": g["exhaustive"],
        "expanded_to_depth": g["expanded_to"],
        "truncated_at_depth": g["truncated_at_depth"],
        "horizon_ok": horizon_ok,
        "n_certain_no_states": len(no),
        "loss_claim": ("PROVEN LOST -- every reachable state expanded, none is "
                       "a win, so no plan of any length finishes this level"
                       if (not winnable and g["exhaustive"]) else
                       "no win within %d plies -- NOT a proof of loss, and this "
                       "row does not claim one" % (g["expanded_to"] + 1)
                       if not winnable else "win at ply %d" % D),
        "enclosed": level.enclosed,
        "n_targets": level.n_targets,
        "n_hazards": level.n_hazards,
        "playable_cells": level.playable,
    }
    if claim is not None:
        row["claimed_optimal"] = claim.get("optimal_moves")
        row["claimed_plans"] = claim.get("distinct_shortest_plans")
        row["claimed_winnable"] = claim.get("winnable")
        row["agree"] = (row["proven_optimal"] == claim.get("optimal_moves")
                        and row["distinct_shortest_plans"]
                        == claim.get("distinct_shortest_plans")
                        and row["winnable"] == claim.get("winnable"))
    return row


def verify_levels(levels, policy=FROZEN, claims=None, depth=HORIZON,
                  budget=None):
    rows, ok = [], True
    for name in levels:
        try:
            r = verify_level(levels[name], (claims or {}).get(name), policy,
                             depth, budget)
        except NotProven as exc:
            rows.append({"level": name, "agree": False, "error": str(exc)})
            ok = False
            continue
        rows.append(r)
        if (claims or {}).get(name) is not None:
            ok = ok and r["agree"]
        ok = ok and r["horizon_ok"]
    return ok, rows


# ---------------------------------------------------------------------------
# PER-PLY FACET DIAGNOSTICS.  One graph per level; every question a lookup.
# ---------------------------------------------------------------------------

class Diagnostics(object):
    """The two facets, read off one graph.

    A 10-entrant field asks ~300 of these questions.  Rebuilding the graph for
    each one is not a design, it is a timeout -- and a timeout inside a
    diagnostic is how a cabinet ends up reporting `unknown` as `false`.
    """

    def __init__(self, level, policy=FROZEN, depth=HORIZON, budget=None):
        self.level = level
        self.policy = policy
        self.depth = depth
        self.budget = budget or depth
        self.g = graph(level, policy, depth)
        self.dw, self.parents = backward_wins(self.g)
        self._no = certain_no(self.g, self.dw, self.parents)
        self._tunnel_only = {}

    # -- FACET 1 ------------------------------------------------------------
    def completable(self, snap, ply):
        """Can THIS run still be won inside its own remaining turns?

        Three-valued on purpose: True, False, and None for "the graph was cut
        off before it could tell you".  With budget <= horizon the answer is
        exact for every state a legal run can reach, and control [HZ] is what
        keeps that sentence true.
        """
        d = self.dw.get(snap)
        if d is not None:
            return d <= max(0, self.budget - ply)
        if snap in self._no:
            return False
        return None

    def dist_to_win(self, snap):
        d = self.dw.get(snap)
        return None if d is None else d

    def tunnel_only(self, snap):
        """Can the level still be finished WITHOUT digging another cell?

        -> (plies, exact).  `plies` is None when the fixed-tunnel sub-search was
        exhausted with no win, which is the answer "no: every remaining plan
        has to open more ground".  `exact` is False when the sub-search hit its
        own cap, and then `plies = None` means UNKNOWN, not NO.  Collapsing
        those two is how a diagnostic starts lying.

        Mobility is the wrong measure for FACET 1 -- control [M1] proves the
        player's traversable set never shrinks -- so the question is whether
        every remaining plan must dig, which under [D-T0] means laying another
        road for the hazard, permanently, with nothing that gives it back.
        """
        if snap in self._tunnel_only:
            return self._tunnel_only[snap]
        st = State.restore(self.level, snap, self.policy)
        if st.objective_met():
            self._tunnel_only[snap] = (0, True)
            return 0, True
        seen = {snap}
        best = {snap: 0}
        q = deque([snap])
        out = None
        truncated = False
        while q and out is None:
            cur = q.popleft()
            d = best[cur]
            cs = State.restore(self.level, cur, self.policy)
            for act in search_actions(self.policy):
                if act not in MOVE_LETTERS and act != ".":
                    continue
                if act != ".":
                    dr, dc = digdug.DELTAS[act]
                    dst = digdug.neighbour(cs, cs.player, (dr, dc))
                    if not self.policy.wrap and dst not in cs.tunnels:
                        continue          # this search may not dig
                probe = State.restore(self.level, cur, self.policy)
                res = resolve_turn(probe, act)
                if res["killed"]:
                    continue
                if res["solved"]:
                    out = d + 1
                    break
                nxt = probe.snapshot()
                if nxt not in seen:
                    if len(seen) > 6000:
                        truncated = True
                        q.clear()
                        break
                    seen.add(nxt)
                    best[nxt] = d + 1
                    q.append(nxt)
        self._tunnel_only[snap] = (out, not truncated)
        return self._tunnel_only[snap]

    def committed(self, snap, ply):
        """Still winnable, and every remaining plan has to dig.  FACET 1.

        On this level set the naive form of this is degenerate -- pearls start in
        soil, so there is never a tunnel-only completion until the last one is
        in.  It is kept because the *shape* is the right shape, and it is
        reported beside the measure that is not degenerate (`slack`), so a reader
        can see the difference instead of being handed the flattering one.
        """
        c = self.completable(snap, ply)
        if c is None:
            return None
        if not c:
            return False
        t, exact = self.tunnel_only(snap)
        if not exact:
            return None
        return t is None and bool(
            State.restore(self.level, snap, self.policy).targets)

    # -- FACET 2 ------------------------------------------------------------
    def armed(self, snap):
        """Does some hazard have a route to the player from this state?"""
        return min_hazard_distance(
            State.restore(self.level, snap, self.policy)) is not None

    def min_distance(self, snap):
        return min_hazard_distance(State.restore(self.level, snap,
                                                 self.policy))

    def safe_alternatives(self, snap, ply):
        """Actions that neither die, nor arm a hazard, nor forfeit the win.

        The answer to "could it have dug somewhere else" -- worth printing only
        because somebody actually searched for it.  A non-empty list at the ply
        that armed a hazard is the finding "it dug its own grave out of a free
        choice"; an empty one is the opposite finding, "the level forced it", and
        the two must not be reported with the same word.
        """
        st = State.restore(self.level, snap, self.policy)
        was_armed = min_hazard_distance(st) is not None
        out = []
        for act in search_actions(self.policy):
            probe = State.restore(self.level, snap, self.policy)
            res = resolve_turn(probe, act)
            if res["solved"]:
                out.append(act)            # winning now is safe under any rule
                continue
            if res["killed"]:
                continue
            armed_now = min_hazard_distance(probe) is not None
            if self.completable(probe.snapshot(), ply + 1) and \
                    (not armed_now or was_armed):
                out.append(act)
        return sorted(out)

    # -- the arithmetic of spending ground ----------------------------------
    def task(self, snap):
        """plies this run still needs to finish the objective, or None."""
        return self.dist_to_win(snap)

    def threat(self, snap):
        """plies until a hazard can stand on you; None = it has no route."""
        return self.min_distance(snap)

    @staticmethod
    def balance(task_before, task_after, threat_before, threat_after):
        """What one ply DID, as four numbers.

        progress     task_before - task_after    what the ply bought, in turns
        threat_gain  threat_before - threat_after
                                               what the ply handed over, in the
                                               hazard's steps (None on either
                                               side means NO ROUTE, which is not
                                               a number and is never converted
                                               into one)
        balance      progress - threat_gain
        slack        threat_after - task_after: the turns this run can still
                                               afford to waste.  < 0 means the
                                               objective was still there and the
                                               ground was not.

        A ply with a negative balance spent more ground than it bought, and a run
        that ends with slack below zero is the failure this cabinet is named for.
        Both terms come from the same exhaustive graph, so the number is not an
        opinion about how the plan felt.
        """
        unknown = (task_before is None or task_after is None)
        progress = None if unknown else (task_before - task_after)
        # Neither side has a road is not "unknown": it is ZERO.  A hazard that
        # could not reach you before and still cannot has gained nothing, and
        # calling that None would hide every negative-balance ply in a run where
        # nobody has dug near a hazard yet -- which is most of them.  Only the
        # TRANSITION (a road opened or closed) is unmeasurable in steps, and that
        # one is reported as `hazard_route_changed`.
        both_none = (threat_before is None and threat_after is None)
        one_none = ((threat_before is None) != (threat_after is None))
        gain = 0 if both_none else (None if one_none
                                    else threat_before - threat_after)
        bal = None if (progress is None or gain is None) else progress - gain
        slack = (None if (threat_after is None or task_after is None)
                 else threat_after - task_after)
        return {"progress": progress, "threat_gain": gain, "balance": bal,
                "slack": slack,
                "hazard_route": threat_after is not None,
                "hazard_route_changed": bool(one_none)}

    def row(self, snap, ply, prev_armed=None, prev_task=None, prev_threat=None):
        st = State.restore(self.level, snap, self.policy)
        armed = min_hazard_distance(st) is not None
        start_mobility = len(State.restore(self.level, self.g["start"],
                                           self.policy).reachable_cells())
        mob = len(st.reachable_cells())
        task = self.dist_to_win(snap)
        threat = min_hazard_distance(st)
        bal = self.balance(prev_task, task, prev_threat, threat)
        row = {
            "ply": ply,
            "alive": not any(h["pos"] == st.player for h in st.hazards),
            "objective_met": st.objective_met(),
            "F1_mobility": mob,
            "F1_mobility_equals_start_mobility": mob == start_mobility,
            "F1_dug_cells": len(st.tunnels),
            "F1_targets_left": len(st.targets),
            "F1_completable_within_budget": self.completable(snap, ply),
            "F1_dist_to_win": task,
            "F1_tunnel_only_completion": self.tunnel_only(snap)[0],
            "F1_tunnel_only_search_exact": self.tunnel_only(snap)[1],
            "F1_committed_to_dug_ground": self.committed(snap, ply),
            "F1_moves_available": digdug.moves_available(st),
            "F2_armed": armed,
            "F2_arming_ply": (ply if (armed and not prev_armed) else None),
            "F2_min_hazard_distance": threat,
            "proof_grade": ("exhaustive" if self.g["exhaustive"]
                            else "bounded:%d" % (self.g["expanded_to"] + 1)),
        }
        row.update(bal)
        return row


# ---------------------------------------------------------------------------
# STRUCTURAL CLAIMS, CHECKED OVER EVERY EDGE OF THE GRAPH
# ---------------------------------------------------------------------------

def check_monotonicity(level, policy=FROZEN, depth=HORIZON):
    """Does the player's own digging ever REMOVE a cell it could enter?

    -> (edges_checked, n_shrinks, n_cells_opened)

    The brief's gloss says the tunnel you dug is ground you cannot re-use.  This
    counts, over every edge of the level's game graph, whether the ground gets
    smaller.  Zero is the answer, and zero is the finding: the sentence is false
    of the mechanics the paragraph supplies, so FACET 1 has to be re-derived from
    what the rules really destroy.  See SECTION_4F.md item 1.
    """
    g = graph(level, policy, depth)
    shrunk = opened = n = 0
    for s, kids in g["children"].items():
        st = State.restore(level, s, policy)
        before = len(st.reachable_cells())
        for a, t in kids:
            n += 1
            tt = State.restore(level, t, policy)
            if len(tt.reachable_cells()) < before:
                shrunk += 1
            if len(tt.tunnels) > len(st.tunnels):
                opened += 1
    return n, shrunk, opened


def check_armedness_monotone(level, policy=FROZEN, depth=HORIZON):
    """Can the player ever CLOSE a hazard's route again, and can it be entombed?

    -> (edges_checked, n_routes_closed, n_entombed_states)

    The third number is the one this cabinet's NAME depends on: alive, objective
    short, and no legal move, with every cell of the map still enterable.  Under
    the frozen reading a route never closes and entombment is unreachable -- a
    wall that is alive walks toward you -- and `digdug_readings.py` shows which
    single clause makes it reachable.  Those are theorems about MY reading, not
    about the paragraph, and they are only worth printing because a search
    counted them.
    """
    g = graph(level, policy, depth)
    closed = n = 0
    for s, kids in g["children"].items():
        st = State.restore(level, s, policy)
        was = min_hazard_distance(st) is not None
        for a, t in kids:
            n += 1
            tt = State.restore(level, t, policy)
            if was and min_hazard_distance(tt) is None:
                closed += 1
    entombed = 0
    for s in g["dist"]:
        st = State.restore(level, s, policy)
        if not st.objective_met() and not digdug.moves_available(st):
            entombed += 1
    return n, closed, entombed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="digdug_solve.py",
                                 description="exhaustive DIG DUG solver")
    ap.add_argument("--level", help="path to a level file")
    ap.add_argument("--all", action="store_true", help="verify the frozen set")
    ap.add_argument("--depth", type=int, default=HORIZON)
    args = ap.parse_args(argv)

    if args.level:
        lv = digdug.load_level(args.level)
        r = verify_level(lv, depth=args.depth)
        for k in sorted(r):
            print("  %-24s %s" % (k, r[k]))
        return 0 if r["winnable"] else 1

    levels = digdug.load_level_set()
    ok, rows = verify_levels(levels, depth=args.depth)
    for r in rows:
        if "error" in r:
            print("  %-30s NOT PROVEN -- %s" % (r["level"], r["error"]))
            continue
        print("  %-30s optimal %-3s  %2s plan(s)  %6d states  %-11s plan %s"
              % (r["level"], r["proven_optimal"], r["distinct_shortest_plans"],
                 r["n_states_explored"], r["proof_grade"], r["shortest_plan"]))
    print()
    print("LEVEL VERIFICATION %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
