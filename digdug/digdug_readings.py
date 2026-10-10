#!/usr/bin/env python3
# digdug_readings.py -- THE SHADOW TABLE.  Every rejected reading of the
# paragraph, MEASURED on the same five levels, beside the frozen one.
#
# WHY THIS FILE EXISTS INSTEAD OF A PARAGRAPH IN A DOCUMENT.
#
# Tier 3's content is the open questions, and the reflex here would be to argue
# them: "we chose tunnels_only because the prose says 'through the tunnels'".
# An argument settles nothing.  So each rejected reading is instantiated as a
# real Policy and run against the real item set, and what comes out is a
# difference in NUMBERS.  Where a clause changes nothing measurable on these
# levels the table SAYS SO ("inert here"), because a clause that only ever cost
# you nothing is a clause you did not test, and a table that reports a difference
# for every row is a table that is measuring something else.
#
# THE KEY MEASUREMENT IS NOT "does the optimum change".  It is:
#
#     play the FROZEN optimal plan, under the rejected rule, and report how it
#     ended.
#
# Same letters.  Same level.  Different ending.  That is the whole claim "these
# clauses are the game" in one column, and it needs no entrant to prove it.
#
# This module is part of the instrument: `digdug_run.py` will not pass its own
# check without it, so the shadow table cannot be quietly dropped from a release.
#
# Stdlib only.

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug                                                    # noqa: E402
from digdug import (FROZEN, MOVE_LETTERS, Policy, State, feed,   # noqa: E402
                    terminal_reason)
import digdug_solve                                              # noqa: E402

BUDGET = 10


def beeline_stream(level, budget=BUDGET):
    """The letters a hazard-blind greedy player actually produces, frozen once
    under the CONTRACT's reading.

    The second stream of the table.  The optimum is a statement about the rules;
    a plan somebody would really play is a statement about PLAYERS, and a shadow
    reading that no optimal line notices can still be the reading that kills a
    real run.  Recomputed per level, never stored in a level file.
    """
    st = State(level, FROZEN)
    out = []
    while not st.ended and st.consumed < budget:
        nxt = _greedy_letter(st)
        if nxt is None:
            break
        out.append(nxt)
        feed(st, nxt, budget=budget)
    return "".join(out)


def _greedy_letter(st):
    """The FIRST letter of the shortest hazard-blind path to the nearest pearl.

    Re-derived every ply, which is what makes this stream the greedy entrant and
    not the static one: it re-plans, it simply never plans AROUND anything.
    """
    from collections import deque
    if not st.targets:
        return None
    goal = min(st.targets)
    seen = {st.player}
    q = deque([(st.player, None)])
    while q:
        cur, first = q.popleft()
        for a in MOVE_LETTERS:
            dr, dc = digdug.DELTAS[a]
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in seen or not st.traversable(nxt):
                continue
            if nxt == goal:
                return first or a
            seen.add(nxt)
            q.append((nxt, first or a))
    return None


#: (label, kwargs, what the reading claims, what to look for)
SHADOWS = (
    ("FROZEN", {}, "the contract's reading", "the baseline"),
    ("shadow:clock2", {"hazard_clock": "every_2_player_turns"},
     "a hazard moves on every second turn",
     "does the world's clock belong to the player's success or the player's "
     "turns -- and does any optimum here depend on the difference"),
    ("shadow:clock-never", {"hazard_clock": "never"},
     "hazards never move at all",
     "the degenerate reading: DIG DUG becomes Sokoban-with-digging. If an item "
     "still distinguishes entrants under it, the item was not measuring the "
     "hazard"),
    ("shadow:hazard-in-soil", {"hazard_terrain": "soil_too"},
     "a hazard can come through undisturbed earth",
     "does 'not sealed behind rock' mean 'has a path' -- two winnable items are "
     "proven lost under this reading"),
    ("shadow:resolve-simultaneous", {"resolve_order": "simultaneous"},
     "hazards move at the same time as the player, not after",
     "the adjacency swap: can a run that survives under one ordering die under "
     "the other"),
    ("shadow:end-on-solve-last", {"end_on_solve_first": False},
     "hazard resolution happens even on the winning ply",
     "does [D-END] decide the FLOOR of the scale"),
    ("shadow:end-on-solve-last-lenient",
     {"end_on_solve_first": False, "death_beats_solve": False},
     "same, but a player who finishes is never killed",
     "the rejected reading has an INTERNAL split the prose never hints at; if "
     "these two rows agree, the split was not worth marking -- they do not"),
    ("shadow:step-onto-hazard-kills", {"player_into_hazard": "killed"},
     "walking into a hazard kills you",
     "the living wall loses its teeth: does any item's optimum change, and does "
     "'blocked' still appear in the record"),
    ("shadow:step-onto-hazard-passes", {"player_into_hazard": "pass_through"},
     "you can walk through it",
     "the hazard stops being terrain at all"),
    ("shadow:no-wait", {"wait_legal": False},
     "the player may not stand still",
     "whether `.` is an action or a refusal, and which entrant notices"),
    ("shadow:targets-persist", {"target_persistence": "persists_as_marker"},
     "a collected pearl leaves a marker that must be re-entered",
     "the reading in which 'solved' is a route through a set of cells rather "
     "than a set of cells becoming empty -- and the one that makes the solver's "
     "state key wrong"),
    ("shadow:wrap", {"wrap": True},
     "the frame wraps",
     "the paragraph says 'a 2D grid' and nothing about edges; under `bounds="
     "blocked` and a rock frame this row is INERT, and the table has to say so"),
    ("shadow:bounds-raise", {"bounds": "raises"},
     "a letter aimed out of the board is an error, not a blocked turn",
     "where the boundary check lives: [B2] says in the transition function, and "
     "this row is what the alternative would report instead"),
    ("shadow:tiebreak-reversed", {"hazard_tiebreak": "reverse_reading_order"},
     "the last hazard in reading order takes a contested cell",
     "the clause that buys determinism; measured to be INERT on this item set, "
     "which is exactly why it is a decision and not a finding"),
    ("shadow:hazards-overlap", {"hazard_blocks_hazard": False},
     "two hazards may stand on one cell",
     "whether [B3]'s uniqueness rule is about the input or about the world"),
    ("shadow:objective-survive", {"objective": "survive_n"},
     "solved means surviving N turns",
     "the reading of 'solved' the paragraph does not exclude -- and the one the "
     "solver REFUSES, because its state key is no longer complete"),
)


def one_reading(name, level, policy, budget=BUDGET):
    """The frozen optimal plan, replayed under `policy`, and what it proves."""
    out = {"level": name, "policy": policy.name}
    try:
        row = digdug_solve.verify_level(level, policy=policy, budget=budget)
    except digdug_solve.NotProven as exc:
        out["error"] = "NOT PROVEN -- the solver refuses: %s" % (exc,)
        out["refused"] = True
        return out
    out["winnable"] = row["winnable"]
    out["optimal_moves"] = row["proven_optimal"]
    out["distinct_shortest_plans"] = row["distinct_shortest_plans"]
    out["proof_grade"] = row["proof_grade"]
    out["n_states"] = row["n_states_explored"]
    out["refused"] = False
    # the frozen optimum, played out under the shadow rule
    base = digdug_solve.verify_level(level, policy=FROZEN, budget=budget)
    plan = base["shortest_plan"]
    if plan:
        st = State(level, policy)
        for raw in plan:
            feed(st, raw, budget=budget)
            if st.ended:
                break
        out["frozen_plan_replayed_under_shadow"] = plan
        out["terminal_under_shadow"] = terminal_reason(st, budget)
        out["alive_at_end"] = not st.killed_at
        out["solved_under_shadow"] = st.solved
        out["hazard_turns_taken"] = st.hazard_turns
        out["frozen_optimum_still_optimal"] = (
            row["winnable"] and row["proven_optimal"] == len(plan)
            and st.solved)
    else:
        out["frozen_plan_replayed_under_shadow"] = None
        out["terminal_under_shadow"] = "NO_PLAN_UNDER_THE_FROZEN_READING"
        out["frozen_optimum_still_optimal"] = False
        out["alive_at_end"] = None
        out["solved_under_shadow"] = False
    # the greedy stream, replayed under the shadow reading
    stream = _STREAM_CACHE.get((name, budget))
    if stream is None:
        stream = beeline_stream(level, budget)
        _STREAM_CACHE[(name, budget)] = stream
    out["beeline_stream_under_frozen"] = stream
    if stream:
        gst = State(level, policy)
        for raw in stream:
            feed(gst, raw, budget=budget)
            if gst.ended:
                break
        out["beeline_terminal_under_shadow"] = terminal_reason(gst, budget)
        out["beeline_died_here"] = bool(gst.killed_at)
    else:
        out["beeline_terminal_under_shadow"] = "NO_GREEDY_LETTERS"
        out["beeline_died_here"] = False
    # and the shadow's own best line, if it differs
    if row["winnable"] and row["shortest_plan"] != plan:
        out["shadow_plan"] = row["shortest_plan"]
        out["shadow_optimum"] = row["proven_optimal"]
    return out


def _fields(r):
    return tuple((r.get("winnable"), r.get("optimal_moves"),
                  r.get("distinct_shortest_plans"), r.get("proof_grade"),
                  r.get("terminal_under_shadow"),
                  r.get("beeline_terminal_under_shadow")))


def measure(budget=BUDGET, as_json=False, out_path=None):
    levels = digdug.load_level_set()
    table = []
    baseline = None
    for label, kw, claim, look in SHADOWS:
        try:
            pol = Policy(name=label, **kw)
        except (ValueError, digdug_solve.NotProven) as exc:
            table.append({"label": label, "claim": claim, "error": repr(exc),
                          "levels": [], "inert_here": False,
                          "changes_anything": None})
            continue
        rows = [one_reading(n, levels[n], pol, budget) for n in
                digdug.LEVEL_FILES]
        entry = {"label": label, "claim": claim, "look_for": look,
                 "levels": rows}
        if baseline is None:
            entry["baseline"] = True
            baseline = rows
            entry["changes_anything"] = None
            entry["inert_here"] = None
        else:
            diffs = []
            for r, br in zip(rows, baseline):
                if r.get("refused") or br.get("refused"):
                    diffs.append(r["level"])
                    continue
                if _fields(r) != _fields(br):
                    diffs.append(r["level"])
            entry["levels_that_separate"] = diffs
            entry["changes_anything"] = bool(diffs)
            entry["inert_here"] = not diffs
            entry["baseline"] = False
        table.append(entry)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as fh:
            json.dump({"artifact": "DIG DUG shadow readings",
                       "budget": budget,
                       "frozen": "digdug/CONTRACT_digdug_v1.md",
                       "the_number_that_matters": (
                           "terminal_under_shadow: the contract's own optimum, "
                           "replayed under the rejected rule"),
                       "table": table}, fh, indent=2, default=str)
            fh.write("\n")
    if as_json:
        print(json.dumps(table, indent=2, default=str))
        return 0
    _print(table)
    print_probes()
    return 0


_STREAM_CACHE = {}
_FROZEN_CACHE = {}


# ---------------------------------------------------------------------------
# THE PROBES -- for a clause the item set cannot separate, say WHY in public
# ---------------------------------------------------------------------------
#
# `INERT HERE` is an uncomfortable line in a table: it can mean "the clause does
# not matter" or "nothing we built could tell".  These four boards exist to
# separate the two.  Each is aimed at ONE clause, each is played with a fixed
# letter stream (never a solver, so a probe cannot smuggle in a solution), and
# each is run under the frozen reading AND under the reading named beside it.
#
# P1 is the interesting one, and it is not interesting in the way probes usually
# are: under the FROZEN contract there is no legal way for the player to step into
# a hazard's cell and live, because the cell the player must occupy first is a
# tunnel and any hazard adjacent to a tunnel has a route and resolves onto it.
# [D-BLOCK] is therefore not "untested" -- it is UNREACHABLE, and the reading
# that was rejected cannot be distinguished from the reading that was chosen by
# any level at all.  It becomes measurable only under a SECOND rejected clause
# (`hazard_clock=every_2_player_turns`, which skips a resolution): the clauses are
# not independent, which is a finding about the paragraph's silences, not about
# these boards.

PROBES = (
    ("P1 the letter that aims at a living wall [D-BLOCK]",
     "#####\n#@~o#\n#####\n",
     [("frozen:blocked", {}),
      ("frozen:kills", {"player_into_hazard": "killed"}),
      ("frozen:passes", {"player_into_hazard": "pass_through"}),
      ("clock2:blocked", {"hazard_clock": "every_2_player_turns"}),
      ("clock2:kills", {"hazard_clock": "every_2_player_turns",
                        "player_into_hazard": "killed"}),
      ("clock2:passes", {"hazard_clock": "every_2_player_turns",
                        "player_into_hazard": "pass_through"})],
     "R",
     "does the letter block, kill, or pass?  Under the FROZEN clock all three "
     "end in the same place -- you cannot stand next to a hazard that has a road "
     "and live to take another turn -- so the clause is not untested by "
     "negligence, it is UNREACHABLE, and it becomes measurable only under a "
     "second rejected clause.  The three rows still differ in the RECORD, which "
     "is why this cabinet counts words and not only endings."),
    ("P2 standing still with a road open [D-STOP]",
     "#####\n#@~o#\n#####\n",
     [("frozen", {}), ("clock-never", {"hazard_clock": "never"}),
      ("no-wait", {"wait_legal": False})],
     ".",
     "does WAIT consume a turn and advance the world's clock?  One letter, `.`: "
     "the frozen reading dies with `waited` counted, which is the whole clause.  "
     "`never` survives (there is no clock to advance) and `wait_legal=False` "
     "raises inside step(), which is the reading the RUNNER must refuse rather "
     "than swallow."),
    ("P3 the edge, on a board with no frame [D-WRAP][D-BOUNDS]",
     ".....\no..@.\n.....\n..~..\n.....\n",
     [("frozen", {}), ("wrap", {"wrap": True}),
      ("bounds-raise", {"bounds": "raises"})],
     "RRR",
     "the pearl is one cell LEFT of the start and the frame is absent, so the "
     "only way to reach it is off the right edge.  Frozen: blocked forever, "
     "never solved.  Wrap: it wraps into the pearl and the level is WON.  "
     "`bounds=raises`: an exception out of the transition function, which is "
     "what a harness that did not check the boundary in step() would be doing "
     "instead of scoring.  A no-op on every framed level and a different GAME on "
     "an open one -- `enclosed` is measured per level precisely so a reader can "
     "see which kind they are looking at."),
    ("P4 two hazards, one cell [D-TIEBREAK][D-HAZCOLL]",
     "#######\n#.~~o.#\n#..@..#\n#######\n",
     [("frozen", {}), ("overlap", {"hazard_blocks_hazard": False}),
      ("reversed-directions", {"hazard_tiebreak": "reverse_reading_order"})],
     "UU",
     "which hazard takes the contested cell, and may two stand on it?  INERT on "
     "every probe and level this cabinet has, because the player has to survive "
     "beside two hazards for the collision to be observable at all.  So the "
     "tie-break is a decision that buys determinism for nothing -- which is the "
     "best outcome for a clause and the worst outcome for a finding, and the "
     "table keeps them apart."),
)


def _play_probe(board, kwargs, stream, budget=BUDGET):
    pol = Policy(**kwargs)
    if pol.bounds == "raises" and pol.wrap:
        pol.bounds = "blocked"      # wrap makes an out-of-bounds letter 'raises'
                                     # impossible to reach; the reading is
                                     # self-contradictory and says so here
    lv = digdug.parse_level(board, "probe")
    st = State(lv, pol)
    words = []
    for raw in stream:
        ply = feed(st, raw, budget=budget)
        words.append(ply.get("word") or ply.get("outcome"))
        if st.ended:
            break
    return {"policy": pol.name, "terminal": terminal_reason(st, budget),
            "blocked": st.blocked, "waited": st.waited, "moves": st.moves,
            "solved": st.solved, "alive": not bool(st.killed_at),
            "player": st.player, "hazards": [h["pos"] for h in st.hazards],
            "words": words, "tunnels": len(st.tunnels)}


def probe_clauses():
    out = []
    for label, board, readings, stream, question in PROBES:
        rows = []
        err = None
        for name, kw in readings:
            try:
                r = _play_probe(board, dict(kw, name=name), stream)
            except Exception as exc:                                # noqa: BLE001
                r = {"policy": name, "error": "%s: %s"
                     % (type(exc).__name__, exc)}
            rows.append(r)
        sig = [json.dumps({k: v for k, v in r.items()
                           if k in ("terminal", "solved", "player", "hazards",
                                    "words", "error")}, default=str,
                          sort_keys=True) for r in rows]
        out.append({"probe": label, "board": board, "stream": stream,
                    "question": question, "rows": rows,
                    "separates": len(set(sig)) > 1})
    return out


def print_probes():
    print()
    print("THE PROBES -- aimed at the clauses the item set cannot separate")
    for e in probe_clauses():
        print()
        print("== %s" % e["probe"])
        print("   question: %s" % e["question"])
        print("   board %r  stream %r" % (e["board"], e["stream"]))
        for r in e["rows"]:
            if "error" in r:
                print("   %-10s ERROR %s" % (r["policy"], r["error"]))
            else:
                print("   %-10s %-24s solved=%-5s player=%s hazards=%s words=%s"
                      % (r["policy"], r["terminal"], r["solved"], r["player"],
                         r["hazards"], r["words"]))
        print("   -> %s" % ("SEPARATES" if e["separates"] else
                            "INERT even here -- the readings produce the same "
                            "world from these letters, and the table says so "
                            "rather than implying it tested something"))
    return 0


def _print(table):
    print()
    print("THE SHADOW TABLE -- every rejected reading, measured on the frozen "
          "item set")
    print("   'frozen plan' below is the OPTIMUM UNDER THE CONTRACT, replayed "
          "under the shadow rule.\n   Same letters, same level, different "
          "ending -- that column is the claim 'these clauses\n   are the game', "
          "and it needs no entrant.")
    base = table[0]["levels"]
    for row in table:
        print()
        print("== %s" % row["label"])
        print("   claims: %s" % row["claim"])
        if row.get("look_for"):
            print("   looks for: %s" % row["look_for"])
        if row.get("error"):
            print("   ERROR: %s" % row["error"])
            continue
        if row.get("baseline"):
            print("   BASELINE -- every other row is diffed against these "
                  "numbers.  The greedy column on this row is the baseline "
                  "ending of a hazard-blind run.")
        elif row.get("inert_here"):
            print("   INERT HERE -- no item in this set separates this reading "
                  "from the frozen one.  Said out loud, because an untested "
                  "clause is not a decided clause, and a table that found a "
                  "difference in every row would be measuring something else.")
        elif row.get("levels_that_separate"):
            print("   SEPARATES on: %s" % ", ".join(row["levels_that_separate"]))
        for r, b in zip(row["levels"], base):
            if r.get("refused"):
                print("   %-32s REFUSED BY THE SOLVER: %s"
                      % (r["level"], r["error"]))
                continue
            same = (r.get("optimal_moves") == b.get("optimal_moves"))
            print("   %-32s opt %-4s plans %-2s %-11s %-12s  optimum -> "
                  "%-20s   greedy %s -> %s"
                  % (r["level"], r.get("optimal_moves"),
                     r.get("distinct_shortest_plans"), r.get("proof_grade"),
                     "(= frozen)" if same else "(!= frozen %s)"
                     % b.get("optimal_moves"),
                     r.get("terminal_under_shadow"),
                     r.get("beeline_stream_under_frozen") or "-",
                     r.get("beeline_terminal_under_shadow")))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="digdug_run.py readings")
    ap.add_argument("--depth", type=int, default=digdug_solve.HORIZON)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results",
                                                   "shadow_readings.json"))
    args = ap.parse_args(argv)
    return measure(budget=min(args.depth, BUDGET), as_json=args.json,
                   out_path=args.out if not args.json else None)


if __name__ == "__main__":
    sys.exit(main())
