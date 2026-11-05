#!/usr/bin/env python3
"""THE WINNABILITY FLOOR -- can a real player win this board at all, and how much better than a schedule can it play?

WHY THIS EXISTS (Jarvis, 2026-11-05, relaying Mike)
    The cabinet has a CEILING gate and no FLOOR gate. The ceiling asks "can a trivial policy clear this?"
    (p*), and it catches one failure. It cannot catch the other two: a board no model can play, and a
    board nobody can win. Those two are INDISTINGUISHABLE in a results table -- a model scoring 0 on an
    unwinnable board looks exactly like a model scoring 0 on an unwinnable-for-it board. That is the
    arena's version of "unmeasured reads as zero", and it is the failure Mike is pointing at.

THREE FACTS THIS FILE KEEPS APART, BECAUSE THEY PRINT THE SAME NUMBER
    WINNABLE     a reference solver reached the board's terminal state; the count below is its cost
    UNWINNABLE   the reference solver's search space was EXHAUSTED without a win -- a proof, not a timeout
    UNDETERMINED the budget bit, or no reference solver exists for this event. NOT a low score, and never a
                 zero. Chess is this state today: no engine is declared, so its floor is UNMEASURED and it
                 must stay visible on the board rather than being closed as a pass.
    A fourth state belongs to the ceiling, not the floor: CEILING_UNREACHABLE -- no play of any kind reaches
    the event's declared full clear (measured: missile `mc_02` would be this if a city sat outside every
    silo's range). That is a broken board, not a hard one, and it is not the same as UNWINNABLE.

AND THE PAIR IS THE POINT: HEADROOM, NOT CLEARABILITY
    p* alone says "a fixed schedule clears it" and reads as "the board is worthless". That inference is
    only valid if the schedule is ALSO the best available play. So this file reports both costs in the
    SAME UNIT -- commands consumed -- and their difference:

        schedule_cost   the p* witness repeated until the board clears
        floor           the reference solver's OPTIMAL cost (BFS for Sokoban and Zork: complete, so the
                        count is the minimum and an exhausted frontier is a proof)
        headroom        schedule_cost - floor

    headroom 0    COLLAPSED  the optimal play IS the schedule. The board ranks emission only; nothing about
                             it asks a player to read it. (Measured: Sokoban 01 and 03, Zork 01, both
                             Missile boards -- five of the seven win-typed boards.)
    headroom 1-2  NARROW     a schedule is available and nearly optimal. (Measured: Zork 02, 1 command.)
    headroom >=3  SEPARATED  a schedule clears it, but a player who reads the board beats it. (Measured:
                             Sokoban 02, 16 commands -- a finding that a ceiling-only reading gets wrong.)
    no schedule   NO-SCHEDULE nothing periodic clears it; only the floor is measured. (Measured: Snake,
                             which is score-typed and has no cleared state at all.)

    THE CEILING ALONE CANNOT TELL A COLLAPSED BOARD FROM A SEPARATED ONE. Both are "cleared by a fixed
    schedule". Only the pair can, which is why the floor is not a second opinion on the ceiling.

THE EVENT'S TYPE DECIDES WHAT A FLOOR IS
    win-typed    Sokoban (solved), Zork (escaped), Missile (every city survives): the floor is a cost to a
                 terminal state, and the reference solver is complete search.
    score-typed  Snake: there is NO cleared state -- the snake wraps the torus and never wins. Its floor is
                 a reference POLICY's score at the same tick cap through the same page, and it is labelled
                 as a score. Pooling a score floor with a win floor is the scaffold-pooling defect again.

EVERY SOLVE IS REPLAYED IN THE EVENT'S OWN FROZEN SIMULATOR
    A solver's opinion about its own solution is not evidence. Each row re-enters the winning stream into
    `sokoban.play` / `missile_command.play` / `zork.play` / the snake page and records that simulator's
    verdict beside the number. If the replay disagrees, the function raises instead of reporting.

CONTROLS (`--self-test`), and a control that cannot fail is not one
    `sokoban/01_one_push`      known WINNABLE in 1 (the retired board, retained as a fixture)
    `sokoban synthetic`        known UNWINNABLE -- a box in a corner with no target: proof, not budget
    `sokoban budget`           the same solvable board with max_states=2: MUST be UNDETERMINED. This is the
                               one assertion that keeps a bounded search from reporting itself as a proof.
    `zork control world`       known WINNABLE in 2 (`take key ; north`) -- the degenerate gate's own fixture
    `zork synthetic`           gate item placed nowhere: UNWINNABLE by exhaustion
    `missile synthetic`        a city outside every silo's range: CEILING_UNREACHABLE, not UNWINNABLE
    `chess`                    UNDETERMINED with a stated reason, and asserted NOT to equal UNWINNABLE

RUN
    python3 winnability_floor.py --self-test
    python3 winnability_floor.py                      # the whole cabinet, human-readable
    python3 winnability_floor.py --json --write probes/FLOOR_TABLE_2026-11-05.json
"""
import argparse
import hashlib
import json
import os
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import degenerate_gate as G

# ---- the three floor verdicts, plus the two states that are not verdicts about a player -----------------
WINNABLE = "WINNABLE"
UNWINNABLE = "UNWINNABLE"
UNDETERMINED = "UNDETERMINED"          # budget bit, or no reference solver: an ABSENCE of measurement
CEILING_UNREACHABLE = "CEILING_UNREACHABLE"   # the event's own full clear is not attainable by any play
SCORES = "SCORES"                       # score-typed event: a reference policy's count, no terminal state

COLLAPSED, NARROW, SEPARATED, NO_SCHEDULE, UNMEASURED = (
    "COLLAPSED", "NARROW", "SEPARATED", "NO-SCHEDULE", "UNMEASURED")

FLOOR_KINDS = {"sokoban": "win", "zork": "win", "missile": "win", "snake": "score", "chess": "win"}

PSTAR_TABLE = os.path.join(HERE, "probes", "PSTAR_TABLE_2026-11-05.json")

SOKOBAN_BUDGET = 40
ZORK_BUDGET = 24


def _digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _approx_periodic(word, upto=None):
    """Is `word` itself the first repetition of a shorter period? A label, never a verdict."""
    for p in range(1, len(word) // 2 + 1):
        if len(word) % p == 0 and word == word[:p] * (len(word) // p):
            return p
    return None


# ------------------------------------------------------------------------------------------------ SOKOBAN
def sokoban_floor(text, name="<text>", max_states=None):
    """Optimal play by breadth-first search -- complete, so the move count is the MINIMUM and an exhausted
    frontier is a PROOF. `solve_text` checks the budget only when work remains (its own docstring), which is
    the line that keeps a bitten budget from being reported as an unsolvable board."""
    import sokoban_solver as SOL
    r = SOL.solve_text(text, name=name, max_states=max_states)
    out = {"event": "sokoban", "board": name, "sha256": _digest(text), "kind": "win",
           "reference": "sokoban_solver.solve_text -- BFS over player moves (complete)"}
    if r["verdict"] == SOL.SOLVABLE:
        out.update(verdict=WINNABLE, commands=r["moves"], solution=r["solution"],
                   pushes=r["pushes"], optimal=True,
                   cost=r["cost"], replay=r["verification"])
        out["solution_period"] = _approx_periodic(r["solution"])
    elif r["verdict"] == SOL.UNSOLVABLE:
        out.update(verdict=UNWINNABLE, commands=None, proof=r.get("proof"),
                   note="frontier exhausted -- every reachable state seen, so this is a proof and not a budget")
    else:                                              # budget bitten: NO verdict about the board
        out.update(verdict=UNDETERMINED, commands=None, budget=r.get("budget"),
                   note="the search budget bit while work remained -- the board is unmeasured, not unsolvable")
    return out


# ------------------------------------------------------------------------------------------------ MISSILE
def missile_floor(text, name="<text>"):
    """Max cities survivable and the MINIMUM actions that attain it, by complete dynamic programming over
    (tick, alive cities, ammo, airborne threats). The winning stream is then replayed through
    `missile_command.play`, which is the counter the score comes from -- the DP's opinion is not the evidence.

    One action per tick, impacts resolve after the action, and an action at or after a threat's impact tick
    is `late`. Those are the simulator's rules, re-implemented here on purpose: a second enumerator that
    agrees with the first is the only way to know the first is right."""
    import missile_command as M
    st = M.parse_state(text)
    cities = dict(st["cities"])
    silos = tuple(sorted(st["silos"]))
    threats = {k: dict(v) for k, v in st["threats"].items()}
    horizon = max(t["tick"] for t in threats.values())

    def resolve(tick, alive, remaining):
        """Impacts at or before `tick`, after the action. Returns (alive, remaining)."""
        alive, remaining = set(alive), set(remaining)
        for tname in sorted(remaining):
            if threats[tname]["tick"] <= tick:
                remaining.discard(tname)
                victim = next((c for c in sorted(alive) if cities[c] == threats[tname]["impact"]), None)
                if victim:
                    alive.discard(victim)
        return frozenset(alive), frozenset(remaining)

    def resolve_all(alive, remaining):
        """The stream ENDS here: every airborne threat resolves. This is what the simulator does after the last
        token, and it is why a board whose decoys land on empty ground is won in FOUR actions while seven
        threats exist -- a solver that insists on resolving every threat before it stops reports a cost that
        no player has to pay."""
        return resolve(float("inf"), alive, remaining)[0]

    @lru_cache(maxsize=None)
    def best(tick, alive, ammo, remaining):
        """-> (cities_alive, (tokens...)) for the best continuation from this tick, one action per tick.

        STOP is always available and costs nothing: the score is read after the remaining threats resolve,
        so stopping early is legal and is often optimal. Without this option the DP returns 6 for a board
        the shipped schedule clears in 4, which is a fact about the search and not about the board."""
        opts = [(len(resolve_all(alive, remaining)), ())]          # stop now: no further actions
        if tick <= horizon:
            cands = [(None, "PASS")]                               # PASS is legal and spends nothing
            for s in silos:
                i = silos.index(s)
                if ammo[i] <= 0:
                    continue
                for tname in sorted(remaining):
                    th = threats[tname]
                    if th["tick"] > tick and abs(st["silos"][s]["at"] - th["impact"]) <= M.RANGE:
                        cands.append(((s, tname, i), f"{s}{tname}"))
            for act, token in cands:
                rem2 = set(remaining)
                ammo2 = list(ammo)
                if act:
                    s, tname, i = act
                    ammo2[i] -= 1
                    rem2.discard(tname)
                al2, rem2 = resolve(tick, alive, frozenset(rem2))
                if not rem2:
                    opts.append((len(al2), (token,)))
                else:
                    sub_c, sub = best(tick + 1, al2, tuple(ammo2), rem2)
                    opts.append((sub_c, (token,) + sub))
        # maximise cities; tie-break on FEWER actions
        return max(opts, key=lambda o: (o[0], -len(o[1])))

    cities_alive, tokens = best(0, frozenset(cities), tuple(st["silos"][s]["ammo"] for s in silos),
                                frozenset(threats))
    rec = M.play(text, list(tokens))
    if rec["cities_surviving"] != cities_alive:
        raise AssertionError(f"INTERNAL: DP claims {cities_alive} cities, the frozen simulator "
                             f"replayed {rec['cities_surviving']} on {tokens!r}")
    total = rec["cities_total"]
    out = {"event": "missile", "board": name, "sha256": _digest(text), "kind": "win",
           "reference": "complete DP over (tick, alive, ammo, airborne) + replay in missile_command.play",
           "commands": len(tokens), "solution": " ".join(tokens), "score": cities_alive,
           "ceiling": total, "optimal": True,
           "replay": {"by": "missile_command.play()", "cities_surviving": rec["cities_surviving"],
                      "cities_total": total, "actions": rec["actions"],
                      "counts": rec["counts"]}}
    if cities_alive == total:
        out["verdict"] = WINNABLE
    else:
        out["verdict"] = CEILING_UNREACHABLE
        out["note"] = (f"no play of any kind saves more than {cities_alive} of {total} cities -- the score's "
                       f"own ceiling is unattainable, which is a broken state and not a hard one")
    return out


# ------------------------------------------------------------------------------------------------ ZORK
def zork_floor(text, name="<text>"):
    """Minimum commands to escape, by breadth-first search over the simulator's OWN states; an exhausted
    frontier proves the world unwinnable. The route is replayed through `zork.play` before it is reported."""
    import zork as Z
    w = Z.parse_world(text)
    start = Z.initial_state(w)

    def key(st):
        return (st["room"], tuple(sorted(st["inventory"])),
                tuple(sorted((k, v or "-") for k, v in st["_placed"].items())))

    cmds = [(d, ("go", d)) for d in sorted(set(Z.DIRECTIONS.values()))]
    for iid, meta in sorted(w["items"].items()):
        cmds.append((f"take {iid}", ("take", iid)))
        for al in sorted(meta["aliases"]):
            cmds.append((f"take {al}", ("take", al)))
    cmds.append(("open", ("open", None)))

    frontier, seen, parent = [(key(start), start, ())], {key(start)}, {}
    expanded = 0
    while frontier:
        nxt = []
        for k, st, route in frontier:
            expanded += 1
            for label, (verb, obj) in cmds:
                st2, outcome, _note = Z.step(w, st, verb, obj)
                if outcome == "escaped":
                    route2 = route + (label,)
                    rec = Z.play(text, list(route2))
                    if not (rec["finished"] and rec["commands_consumed"] == len(route2)):
                        raise AssertionError(f"INTERNAL: route {route2!r} replays to finished="
                                             f"{rec['finished']} commands={rec['commands_consumed']}")
                    return {"event": "zork", "board": name, "sha256": _digest(text), "kind": "win",
                            "reference": "BFS over zork.step states + replay in zork.play (complete)",
                            "verdict": WINNABLE, "commands": len(route2), "solution": " ; ".join(route2),
                            "optimal": True, "states_expanded": expanded,
                            "replay": {"by": "zork.play()", "finished": rec["finished"],
                                       "ending": rec["ending"],
                                       "commands_consumed": rec["commands_consumed"],
                                       "carried_required_item": rec["carried_required_item"]}}
                if outcome == "gate_locked" and st2.get("locked"):
                    continue                                # terminal, and not a win
                k2 = key(st2)
                if k2 in seen:
                    continue
                seen.add(k2)
                nxt.append((k2, st2, route + (label,)))
        frontier = nxt
    return {"event": "zork", "board": name, "sha256": _digest(text), "kind": "win",
            "reference": "BFS over zork.step states (complete)", "verdict": UNWINNABLE, "commands": None,
            "proof": {"kind": "state_space_exhausted", "states_expanded": expanded},
            "note": "every reachable simulator state was expanded without an escape -- a proof, not a budget"}


# ------------------------------------------------------------------------------------------------ SNAKE
def snake_floor(page, seed, ticks=120):
    """A score-typed floor: the best of the two reference POLICIES the cabinet already ships, through the
    real page at the same tick cap. Snake has no cleared state, so this is a count and is labelled one."""
    import snake_run as R
    from snake_solver import Board, GreedySafeAgent, CycleAgent, CycleShortcutAgent

    def run_policy(make):
        st0 = page.new_episode(seed)
        board = Board(st0["canvas"][0] // st0["grid"], st0["canvas"][1] // st0["grid"])
        agent = make(board)
        trace, _t, _e = R.play_episode(page, seed, ticks, True,
                                       lambda st, eaten: (agent.next_direct(st), None))
        return sum(1 for r in trace if R._ate(r["before"], r["after"]))

    scores = {}
    for label, make in (("greedy-safe", GreedySafeAgent), ("hamiltonian-cycle", CycleAgent),
                        ("hamiltonian-shortcut", CycleShortcutAgent)):
        try:
            scores[label] = run_policy(make)
        except Exception as e:                       # a policy that cannot run is not a zero
            scores[label] = None
            scores.setdefault("_errors", {})[label] = f"{type(e).__name__}: {e}"
    good = {k: v for k, v in scores.items() if isinstance(v, int)}
    best_label = max(good, key=lambda k: good[k]) if good else None
    return {"event": "snake", "board": f"seed {seed}", "seed": seed, "kind": "score",
            "reference": "reference policies through the real page (no cleared state exists)",
            "verdict": SCORES if best_label else UNDETERMINED,
            "score": good.get(best_label) if best_label else None,
            "best_policy": best_label, "policy_scores": good, "ticks": ticks,
            "note": "score-typed: a count, not a terminal state. Never pool this with a win floor."}


# ------------------------------------------------------------------------------------------------ CHESS
def chess_floor(name="<board>"):
    """Named and NOT BUILT, which is the honest state and must stay visible. There is no reference solver for
    this event on this box, so its floor is unmeasured; reporting it as a low score or closing it as a pass is
    the defect this function refuses to commit."""
    return {"event": "chess", "board": name, "kind": "win", "verdict": UNDETERMINED, "commands": None,
            "reference": None,
            "note": "no reference solver is declared or built for chess -- the floor is UNMEASURED, and an "
                    "unmeasured floor must not read as 'no model can win it'"}


# ------------------------------------------------------------------------------------------------ HEADROOM
def schedule_cost(event, text, witness, budget=None):
    """The p* witness repeated until the board clears -> the commands it consumed. Same unit as the floor,
    so the subtraction means something. Returns None when no schedule clears (snake has no clear at all)."""
    if not witness:
        return None
    words = [w.strip() for w in witness.split(";")] if event == "zork" else (
        list(witness) if event == "sokoban" else witness.split())
    if event == "sokoban":
        import sokoban as S
        for k in range(1, (budget or SOKOBAN_BUDGET) // len(words) + 2):
            stream = list((words * k)[:budget or SOKOBAN_BUDGET])
            rec = S.play(text, stream, stop_when_solved=True)
            if rec["solved"]:
                return {"commands": rec["moves"], "repetitions": k}
        return None
    if event == "zork":
        import zork as Z
        for k in range(1, (budget or ZORK_BUDGET) // len(words) + 2):
            stream = list((words * k)[:budget or ZORK_BUDGET])
            rec = Z.play(text, stream)
            if rec["finished"]:
                return {"commands": rec["commands_consumed"], "repetitions": k}
        return None
    if event == "missile":
        import missile_command as M
        total = len(M.parse_state(text)["cities"])
        for k in range(1, 8):
            stream = words * k
            rec = M.play(text, stream)
            if rec["cities_surviving"] == total:
                return {"commands": len(stream), "repetitions": k,
                        "score": rec["cities_surviving"]}
        return None
    return None


def grade(floor, sched):
    """The pair -> one word. This is the only place headroom is decided, so the table cannot disagree with
    the prose that quotes it."""
    if floor["verdict"] in (UNDETERMINED, CEILING_UNREACHABLE):
        return UNMEASURED
    if floor["verdict"] == UNWINNABLE:
        return "UNWINNABLE"
    if sched is None:
        return NO_SCHEDULE
    f = floor["commands"]
    if f is None:
        return UNMEASURED
    head = sched["commands"] - f
    return COLLAPSED if head <= 0 else NARROW if head <= 2 else SEPARATED


# ------------------------------------------------------------------------------------------------ THE TABLE
def _sokoban_pstar():
    """Sokoban's p* is re-derived here (84 streams a board, milliseconds) because the published table covers
    the other three events only."""
    rows = []
    for name in ("01_one_push", "02_two_boxes", "03_the_corner_waiting"):
        p = os.path.join(HERE, "levels", f"{name}.txt")
        text = open(p, encoding="utf-8").read()
        r = G.sokoban_min_period(p)
        rows.append({"event": "sokoban", "board": f"levels/{name}.txt", "text": text,
                     "sha256": _digest(text), "p_star": r["period"], "witness": r["word"],
                     "p_star_source": "re-derived in this run (degenerate_gate.sokoban_min_period)"})
    return rows


def _published_pstar():
    """The four rows per event already published, plus their own measured_at so the provenance travels."""
    if not os.path.exists(PSTAR_TABLE):
        return [], None
    doc = json.load(open(PSTAR_TABLE, encoding="utf-8"))
    rows = []
    for r in doc["rows"]:
        p = os.path.join(HERE, r["board"]) if r["event"] != "snake" else None
        rows.append({"event": r["event"], "board": r["board"], "path": p,
                     "seed": r.get("seed"),
                     "text": open(p, encoding="utf-8").read() if p else None,
                     "sha256": r.get("sha256"), "p_star": r["p_star"], "witness": r["witness"],
                     "p_star_score": r.get("score"),
                     "p_star_source": f"{os.path.relpath(PSTAR_TABLE, HERE)} (measured_at "
                                      f"{doc['measured_at']})"})
    return rows, doc["measured_at"]


def table(snake_ticks=120):
    rows, measured_at = _published_pstar()
    rows = _sokoban_pstar() + rows
    page = None
    out = []
    try:
        for r in rows:
            ev = r["event"]
            if ev == "sokoban":
                floor = sokoban_floor(r["text"], r["board"])
            elif ev == "missile":
                floor = missile_floor(r["text"], r["board"])
            elif ev == "zork":
                floor = zork_floor(r["text"], r["board"])
            elif ev == "snake":
                if page is None:
                    import snake_page
                    page = snake_page.SnakePage().start()
                floor = snake_floor(page, r["seed"], snake_ticks)
            else:
                floor = chess_floor(r["board"])
            sched = schedule_cost(ev, r["text"], r["witness"]) if r["text"] else None
            head = (sched["commands"] - floor["commands"]
                    if sched and floor.get("commands") is not None else None)
            out.append({**{k: r[k] for k in ("event", "board", "sha256", "p_star", "witness",
                                             "p_star_source") if k in r},
                        "floor": floor, "schedule": sched, "headroom": head,
                        "verdict_pair": grade(floor, sched)})
    finally:
        if page is not None:
            page.stop()
    # chess has no board in either table: it is stated so its UNMEASURED row is visible, not omitted
    out.append({"event": "chess", "board": "(no board file: probe unbuilt)", "sha256": None,
                "p_star": None, "witness": None, "p_star_source": "n/a",
                "floor": chess_floor(), "schedule": None, "headroom": None,
                "verdict_pair": UNMEASURED})
    return out, measured_at


def _report(rows):
    print(f"{'event':8} {'board':34} {'p*':>3} {'sched':>6} {'floor':>6} {'head':>5}  {'pair':<12} floor")
    print("-" * 118)
    for r in rows:
        f = r["floor"]
        fl = f.get("commands") if f.get("commands") is not None else (f.get("score") and f"={f['score']}")
        sp = r["schedule"]["commands"] if r["schedule"] else "-"
        print(f"{r['event']:8} {os.path.basename(str(r['board'])):34} {str(r['p_star'] or '-'):>3} "
              f"{str(sp):>6} {str(fl if fl is not None else '-'):>6} {str(r['headroom'] if r['headroom'] is not None else '-'):>5}  "
              f"{r['verdict_pair']:<12} {f['verdict']}")
    print()
    for r in rows:
        if r["floor"].get("note"):
            print(f"  {r['event']}/{os.path.basename(str(r['board']))}: {r['floor']['note']}")


# ------------------------------------------------------------------------------------------------ CONTROLS
# CONTROL -- a box in a corner and no target it can reach: provably unsolvable, no budget involved.
# (Sokoban's parser takes no comment lines: a '#' inside the text is a WALL, which is the one trap here.)
SOKOBAN_UNSOLVABLE = """\
#######
#@$####
#.#####
#######
"""

# CONTROL -- one push to the target. Used THREE ways: as a win, as a budget-bitten UNDETERMINED, and as the
# fixture that proves the two are different strings.
SOKOBAN_SOLVABLE = """\
######
#@$.###
######
"""

ZORK_UNWINNABLE = """\
start hall
room hall Dusty Hall
room vault The Vault
exit hall north vault
exit vault south hall
item key vault
gate vault key
"""

MISSILE_SAVABLE = """\
tick 0
city A at 2
silo 1 at 0 ammo 1
threat P impact 2 tick 1
"""

MISSILE_UNREACHABLE = """\
tick 0
city A at 2
city B at 9
silo 1 at 0 ammo 2
threat P impact 2 tick 1
threat Q impact 9 tick 1
"""


def _self_test():
    ok, bad = 0, 0

    def check(label, cond, detail=""):
        nonlocal ok, bad
        if cond:
            ok += 1
            print(f"  ok    {label}")
        else:
            bad += 1
            print(f"  FAIL  {label}  {detail}")

    print("FLOOR GATE -- self-test")
    # 1. a known win, in the retired board that is retained as a fixture
    r = sokoban_floor(open(os.path.join(HERE, "levels", "01_one_push.txt"), encoding="utf-8").read(), "01")
    check("sokoban 01_one_push is WINNABLE in 1 move", r["verdict"] == WINNABLE and r["commands"] == 1, r)
    check("...and its replay through the frozen simulator agrees", r["replay"]["solved"] is True, r["replay"])

    # 2. a proof, not a budget
    r = sokoban_floor(SOKOBAN_UNSOLVABLE, "unsolvable")
    check("sokoban corner-dead box is UNWINNABLE by PROOF",
          r["verdict"] == UNWINNABLE and (r.get("proof") or {}).get("kind") in
          ("complete_enumeration", "sound_rule_at_the_start"), r)

    # 3. THE ASSERTION THAT MATTERS: the SAME board, two budgets. A bitten budget is not an unsolvable board,
    #    and it is not a low score either -- it is the absence of a measurement.
    budget_text = open(os.path.join(HERE, "levels", "02_two_boxes.txt"), encoding="utf-8").read()
    full = sokoban_floor(budget_text, "02")
    check("sokoban 02 with no budget is WINNABLE (12 moves, complete search)",
          full["verdict"] == WINNABLE and full["commands"] == 12, full)
    r = sokoban_floor(budget_text, "02", max_states=5)
    check("the SAME board with max_states=5 is UNDETERMINED, not UNWINNABLE",
          r["verdict"] == UNDETERMINED, r)
    check("...and UNDETERMINED is a different string from UNWINNABLE", UNDETERMINED != UNWINNABLE)

    # 4. zork: the gate's own degenerate fixture, known winnable in 2
    r = zork_floor(G.ZORK_CONTROL_WORLD, "zork-control")
    check("zork control world is WINNABLE in 2 commands",
          r["verdict"] == WINNABLE and r["commands"] == 2 and r["solution"] == "take key ; north", r)

    # 5. zork: gate item placed in a room that does not exist -> exhausted frontier
    r = zork_floor(ZORK_UNWINNABLE, "zork-unwinnable")
    check("zork with the gate item placed nowhere is UNWINNABLE by exhaustion",
          r["verdict"] == UNWINNABLE and r["proof"]["kind"] == "state_space_exhausted", r)

    # 6. missile: the ceiling reached, and the ceiling UNREACHABLE
    r = missile_floor(MISSILE_SAVABLE, "mc-savable")
    check("missile with one reachable city is WINNABLE in 1 action",
          r["verdict"] == WINNABLE and r["commands"] == 1, r)
    r = missile_floor(MISSILE_UNREACHABLE, "mc-unreachable")
    check("missile with a city out of every silo's range is CEILING_UNREACHABLE, not UNWINNABLE",
          r["verdict"] == CEILING_UNREACHABLE and r["score"] == 1 and r["ceiling"] == 2, r)

    # 7. chess: named, unbuilt, and NOT a pass
    r = chess_floor()
    check("chess is UNDETERMINED and says why", r["verdict"] == UNDETERMINED and r["reference"] is None, r)
    check("...and is never reported as UNWINNABLE", r["verdict"] != UNWINNABLE)

    # 8. the schedule cost agrees with the witness it was given, on the two events with a cheap one
    text = open(os.path.join(HERE, "levels", "03_the_corner_waiting.txt"), encoding="utf-8").read()
    sc = schedule_cost("sokoban", text, "RULDLU")
    check("sokoban 03's schedule `RULDLU` costs 6 commands", sc and sc["commands"] == 6, sc)
    text = open(os.path.join(HERE, "levels", "mc_02_scarcity.txt"), encoding="utf-8").read()
    sc = schedule_cost("missile", text, "1P 1Q 2R 2S")
    check("missile mc_02's schedule `1P 1Q 2R 2S` saves every city in 4 actions",
          sc and sc["commands"] == 4 and sc["score"] == 4, sc)

    print(f"\n{ok} passed, {bad} failed")
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="The winnability floor: p* AND a floor, with the headroom between.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", metavar="PATH", help="write the table JSON to PATH")
    ap.add_argument("--ticks", type=int, default=120)
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    rows, measured_at = table(a.ticks)
    if a.write:
        doc = {"measured_at": __import__("datetime").datetime.now().astimezone().isoformat(),
               "pstar_provenance": f"missile/zork/snake p* from probes/PSTAR_TABLE_2026-11-05.json "
                                   f"(measured_at {measured_at}); sokoban p* re-derived in this run",
               "units": "commands consumed to the event's terminal state; snake is a score and is labelled",
               "rows": rows}
        with open(a.write, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print(f"wrote {a.write} ({os.path.getsize(a.write)} bytes, {len(rows)} rows)")
    if a.json:
        print(json.dumps(rows, indent=1, sort_keys=True))
    else:
        _report(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
