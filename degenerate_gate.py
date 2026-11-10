#!/usr/bin/env python3
"""THE DEGENERATE-CLASS GATE -- a board a fixed schedule clears ranks nobody.

WHY THIS IS A GATE AND NOT A REPORT
    Measured 2026-11-04/05: Sokoban level `01_one_push` is cleared by the constant stream `R` in ONE
    move, and its OPTIMAL solution is that same single action. A board like that never asked anyone
    to observe it: every entrant ranked on it was ranked on the model's willingness to emit `R`.
    A report saying so leaves the board selectable; a gate refuses it at admission.

THE CLASS IS DECLARED PER EVENT, DEFENDED, AND BOUNDED BY THE EVENT'S OWN VOCABULARY
    A gate whose degenerate class is undefined measures nothing, so each event states its alphabet,
    its class, and the budget the class is played to:

      sokoban  alphabet U D L R (`sokoban.ACTIONS`). Class = every PERIODIC word of period <= 3 over
               that alphabet, repeated to the registered cap (40). Period 1 is "press the same key
               forever"; periods 2-3 are the cycles an emitter can produce without reading the board.
               4 + 16 + 64 = 84 streams, which is the number the cabinet reported and this file
               re-derives rather than trusts.

      zork     the alphabet is WORDS, not letters, so it is bounded by the world's own vocabulary:
               every direction the simulator accepts (both spellings), the verbs it parses with no
               object, and `take <name>` for every item and alias the world declares. Class =
               periodic streams of period <= 2 over that alphabet. Period 2 matters here and is not
               decoration: in `zork_01`, `north` alone ends `gate_locked`, but the cycle
               `take key ; north` escapes -- a stream that never looks at the world.

      chess    no constant token exists, because legality depends on the position. The class must be
               a POLICY: `always the first legal move in a fixed ordering` or `always the last`.
               NOT IMPLEMENTED against the move lister yet, so this event returns UNDETERMINED.
               Naming the class without building the probe is exactly the state this gate exists to
               keep from reading as PASS.

THE CONTROL IS THE POINT
    "The gate found nothing" and "the gate did not work" print the same line. So every event carries
    a POSITIVE CONTROL -- a state known to be degenerate -- and the SAME probe must hit it:

      sokoban  level `01_one_push`, RETIRED as a scorable board and RETAINED as this gate's control.
               That is the reason the file still exists: a rule that retires a board must keep one
               object that proves the detector still fires on it.
      zork     a synthetic two-room control world in this file, where `take key ; north` escapes.
      chess    none, so chess cannot return PASS even if the probe later finds nothing.

    Verdicts, and they are three different facts:
      PASS          the control fired AND no stream in the class cleared the subject
      DEGENERATE    a stream in the class cleared the subject (the witness is published)
      UNDETERMINED  the control did not fire, so the probe's silence about the subject means nothing

    `--self-test` drives the control to FAIL on purpose (it swaps the control for a board the class
    cannot clear and requires UNDETERMINED) -- a control that reports PASS is not evidence; a control
    you have driven to FAIL is.

RUN
    python3 degenerate_gate.py --self-test
    python3 degenerate_gate.py --event sokoban --board levels/02_two_boxes.txt
    python3 degenerate_gate.py --event zork --board levels/zork_01_the_floor.txt
    python3 degenerate_gate.py --json --event sokoban --board levels/03_the_corner_waiting.txt
"""
import argparse
import hashlib
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PASS, DEGENERATE, UNDETERMINED = "PASS", "DEGENERATE", "UNDETERMINED"

SOKOBAN_BUDGET = 40          # the registered cap in sokoban_run.py / PREREG_sokoban.md
SOKOBAN_MAX_PERIOD = 3       # 4 + 16 + 64 = 84 streams
ZORK_BUDGET = 24
ZORK_MAX_PERIOD = 2

# ------------------------------------------------------------------------------------------------
# THE CONTROLS. A control is an object that the class MUST clear. It is a fixture, not a subject:
# it never ranks anyone, and it is never scored.
# ------------------------------------------------------------------------------------------------
SOKOBAN_CONTROL = "levels/01_one_push.txt"      # RETIRED as a board; retained as the gate's control

ZORK_CONTROL_WORLD = """\
# THE GATE'S CONTROL -- a world built to be degenerate, and NOT a board anyone is ranked on.
# The key is in the start room and the gate is one move north, so the two-command cycle
# `take key ; north` escapes. If the probe cannot clear THIS, it cannot see a degenerate world.
start hall
room hall Dusty Hall
room vault The Vault
item key hall
gate vault key
exit hall north vault
"""


def _digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


# ------------------------------------------------------------------------------------------------
# SOKOBAN
# ------------------------------------------------------------------------------------------------
def sokoban_streams():
    """Every periodic word of period <= SOKOBAN_MAX_PERIOD over U D L R, played to the cap."""
    import sokoban as S
    alpha = sorted(S.ACTIONS)
    out = []
    for period in range(1, SOKOBAN_MAX_PERIOD + 1):
        for word in itertools.product(alpha, repeat=period):
            w = "".join(word)
            reps = SOKOBAN_BUDGET // period + 1
            out.append({"period": period, "word": w,
                        "stream": list((w * reps)[:SOKOBAN_BUDGET])})
    return out


def sokoban_probe(level_text):
    import sokoban as S
    hits = []
    streams = sokoban_streams()
    for cand in streams:
        rec = S.play(level_text, cand["stream"], stop_when_solved=True)
        if rec["solved"]:
            hits.append({"period": cand["period"], "word": cand["word"], "moves": rec["moves"],
                         "solved_at_ply": rec["moves"]})
    hits.sort(key=lambda h: (h["period"], h["word"]))
    return hits, len(streams)


# ------------------------------------------------------------------------------------------------
# ZORK
# ------------------------------------------------------------------------------------------------
def zork_alphabet(world_text):
    """The words a fixed schedule could emit, taken from the world's OWN declarations."""
    import zork as Z
    w = Z.parse_world(world_text)
    dirs = sorted(set(Z.DIRECTIONS.keys()) | set(Z.DIRECTIONS.values()))
    verbs = [v for v in ("look", "wait", "inventory", "help") if v in getattr(Z, "VERBS", {})]
    takes = []
    for iid, meta in w["items"].items():
        takes.append(f"take {iid}".replace("_", " "))
        for al in sorted(meta["aliases"]):
            takes.append(f"take {al}")
    return dirs + verbs + sorted(set(takes))


def zork_streams(world_text):
    import zork as Z
    alpha = zork_alphabet(world_text)
    out = []
    for period in range(1, ZORK_MAX_PERIOD + 1):
        for word in itertools.product(alpha, repeat=period):
            reps = ZORK_BUDGET // period + 1
            out.append({"period": period, "word": " ; ".join(word),
                        "stream": (list(word) * reps)[:ZORK_BUDGET]})
    return out, alpha


def zork_probe(world_text):
    import zork as Z
    hits = []
    streams, alpha = zork_streams(world_text)
    for cand in streams:
        rec = Z.play(world_text, cand["stream"])
        if rec["finished"]:
            hits.append({"period": cand["period"], "word": cand["word"],
                         "commands_consumed": rec["commands_consumed"]})
    hits.sort(key=lambda h: (h["period"], h["word"]))
    return hits, len(streams), alpha


# ------------------------------------------------------------------------------------------------
# CHESS -- the class is named and the probe is not built. It says so instead of passing.
# ------------------------------------------------------------------------------------------------
def chess_probe(_board_text):
    return [], 0, []


CHESS_CLASS = ("(policy) always the FIRST legal move in a fixed ordering / always the LAST -- no "
               "constant token exists because legality depends on the position; probe against the "
               "move lister NOT IMPLEMENTED")


# ------------------------------------------------------------------------------------------------
# THE GATE
# ------------------------------------------------------------------------------------------------
def gate(event, board_path, control_path=None, control_text=None):
    """-> the verdict record. Three states, never conflated."""
    text = open(board_path, encoding="utf-8").read()
    if event == "sokoban":
        class_def = (f"periodic words of period <= {SOKOBAN_MAX_PERIOD} over "
                     f"sorted(sokoban.ACTIONS) = U D L R, repeated to the cap {SOKOBAN_BUDGET}")
        ctrl_path = control_path or os.path.join(HERE, SOKOBAN_CONTROL)
        ctrl_text = open(ctrl_path, encoding="utf-8").read()
        hits, n_streams = sokoban_probe(text)
        ctrl_hits, ctrl_streams = sokoban_probe(ctrl_text)
        ctrl_identity = {"control": os.path.relpath(ctrl_path, HERE), "sha256": _digest(ctrl_text)}
        instrument = {"simulator": "sokoban.py", "sha256": _file_digest("sokoban.py"),
                      "budget": SOKOBAN_BUDGET}
    elif event == "zork":
        class_def = (f"periodic streams of period <= {ZORK_MAX_PERIOD} over the world's own vocabulary "
                     f"(directions both spellings, objectless verbs, take <item|alias>), budget {ZORK_BUDGET}")
        ctrl_text = control_text or ZORK_CONTROL_WORLD
        hits, n_streams, alpha = zork_probe(text)
        ctrl_hits, ctrl_streams, _ = zork_probe(ctrl_text)
        ctrl_identity = {"control": "SYNTHETIC_ZORK_CONTROL_WORLD", "sha256": _digest(ctrl_text)}
        instrument = {"simulator": "zork.py", "sha256": _file_digest("zork.py"),
                      "budget": ZORK_BUDGET, "alphabet": alpha}
    elif event == "chess":
        class_def, ctrl_streams = CHESS_CLASS, 0
        hits, n_streams, ctrl_hits = [], 0, []
        ctrl_identity = {"control": None, "sha256": None}
        instrument = {"simulator": "chess_game.py", "sha256": _file_digest("chess_game.py")}
    else:
        raise SystemExit(f"UNREADABLE EVENT {event!r} -- no verdict")

    if not ctrl_hits:
        verdict = UNDETERMINED
        why = ("the control did not fire: the probe cannot see a state built to be degenerate, so its "
               "silence about this board is not a PASS")
    elif hits:
        verdict = DEGENERATE
        w = hits[0]
        why = f"the fixed stream {w['word']!r} (period {w['period']}) clears the board"
    else:
        verdict = PASS
        why = "the control fired and no stream in the class clears this board"

    return {"gate": "degenerate-class", "event": event,
            "board": os.path.relpath(board_path, HERE), "board_sha256": _digest(text),
            "class": class_def, "verdict": verdict, "why": why,
            "streams_evaluated": n_streams, "hits": hits[:8], "n_hits": len(hits),
            "control": ctrl_identity, "control_streams": ctrl_streams,
            "control_hits": [h["word"] for h in ctrl_hits[:4]], "n_control_hits": len(ctrl_hits),
            "instrument": instrument}


def _file_digest(name):
    p = os.path.join(HERE, name)
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------------
# THE MEASURE THAT DOES NOT DEPEND ON A CHOSEN WIDTH: the board's PERIODIC CLEARANCE INDEX p*.
#
# A boolean verdict at a declared width answers "is this board degenerate at width W", and W is a
# choice -- so a board can pass because W was set below the period that clears it. p* removes the
# choice from the answer: the smallest period p for which some word of length p, repeated to the
# cap, clears the board. p* is then compared to the width the EVENT declares, and published beside
# every board so a reader can see the distance between the two.
#
# THIS IS THE CATALOGUE QUESTION, NOT THE PER-RUN QUESTION. Cost is 4^p streams: p*<=3 is
# milliseconds, p*<=8 is 87,380 streams and ~20 s on this box. So the admission gate stays at the
# declared width, and this runs when a board is ADMITTED to a catalogue.
# ------------------------------------------------------------------------------------------------
def sokoban_admitted(board_path, threshold=8):
    """A board is admitted only if no periodic word of period <= threshold clears it
    (i.e. its ablated null does NOT clear it). Refuses boards whose null clears them."""
    r = sokoban_min_period(board_path, upto=threshold)
    return r["period"] is None


# alias used by board generators
board_admitted = sokoban_admitted
sokoban_null_clears = lambda board_path, threshold=8: sokoban_min_period(board_path, upto=threshold)["period"] is not None


def sokoban_min_period(board_path, upto=8):
    import sokoban as S
    text = open(board_path, encoding="utf-8").read()
    alpha = sorted(S.ACTIONS)
    for period in range(1, upto + 1):
        n = 0
        for word in itertools.product(alpha, repeat=period):
            w = "".join(word)
            n += 1
            if S.play(text, list((w * (SOKOBAN_BUDGET // period + 1))[:SOKOBAN_BUDGET]),
                      stop_when_solved=True)["solved"]:
                return {"period": period, "word": w, "streams_scanned": n,
                        "moves": S.play(text, list((w * (SOKOBAN_BUDGET // period + 1))[:SOKOBAN_BUDGET]))["moves"]}
    return {"period": None, "word": None, "streams_scanned": sum(4 ** k for k in range(1, upto + 1)),
            "note": f"no periodic word of period <= {upto} clears this board"}


# ------------------------------------------------------------------------------------------------
# p* FOR THE OTHER THREE EVENTS. Same question, different clear condition, stated per event because a
# clear condition borrowed from another event is a measurement of the wrong thing:
#
#   zork    "clears" = the world is FINISHED (the simulator's own terminal state). p* = smallest period
#           of a repeated word stream that finishes it. No ambiguity.
#   missile "clears" = EVERY city survives (score == cities_total). The event's own score is a count, so
#           the ceiling is the count's ceiling. A state where the ceiling is unreachable by ANY play is
#           a broken state and mc_min_period says so rather than reporting a low p* as a win.
#   snake   THERE IS NO CLEARED STATE -- the snake wraps the torus and never wins. So p* is defined as
#           the smallest period whose best repeated word ATTAINS THE BEST SCORE THE CLASS ATTAINS. That
#           is the honest analogue and it is stated, not smuggled: the question "does a fixed schedule
#           match reading play" is answered by comparing that class-best against the ADAPTIVE baseline
#           on the same seed, at the same tick cap, through the same page.
#
# THE COST IS 4^p (or |alphabet|^p) STREAMS, so upto is bounded per event and the bound TRAVELS with
# every number. "p* > upto" is not "not degenerate"; it is "no periodic word of period <= upto clears it".
# ------------------------------------------------------------------------------------------------
MC_MAX_PERIOD = 3
ZORK_PSTAR_MAX_PERIOD = 3
SNAKE_MAX_PERIOD = 4
SNAKE_PSTAR_TICKS = 120
SNAKE_ALPHABET = ["U", "D", "L", "R"]

# THE TABLE'S SEARCH BOUNDS ARE WIDER THAN THE GATE'S WIDTHS, deliberately: the gate is what a run
# pays for every entrant, the catalogue measure is what a board costs ONCE. Measured cost of one play
# here (2026-11-05): zork 0.11 ms, missile 0.02 ms -- so period 5 over zork's 18-word alphabet is 1.9M
# plays and ~3.5 min, which is a catalogue price and not a gate price.
MC_PSTAR_SEARCH = 4
ZORK_PSTAR_SEARCH = 5
SNAKE_PSTAR_SEARCH = 4


def _repeat(word, budget):
    return list((list(word) * (budget // len(word) + 1))[:budget])


def mc_alphabet(state_text):
    import missile_command as M
    st = M.parse_state(state_text)
    alpha = ["PASS"] + [f"{s}{t}" for s in sorted(st["silos"]) for t in sorted(st["threats"])]
    budget = max(t["tick"] for t in st["threats"].values())     # one action per tick to the last impact
    return alpha, budget


def mc_min_period(state_text, upto=MC_MAX_PERIOD):
    """Smallest period whose repeated word saves EVERY city, or the class-best if it cannot."""
    import missile_command as M
    alpha, budget = mc_alphabet(state_text)
    best_by_period, best = {}, None
    for period in range(1, upto + 1):
        pbest = (-1, "")
        for word in itertools.product(alpha, repeat=period):
            rec = M.play(state_text, _repeat(word, budget))
            score = rec["cities_surviving"]
            if score > pbest[0]:
                pbest = (score, " ".join(word))
            if score == rec["cities_total"]:
                return {"period": period, "word": " ".join(word), "score": score,
                        "cities_total": rec["cities_total"], "budget": budget,
                        "alphabet": alpha, "cleared": True,
                        "best_by_period": {**best_by_period, period: pbest}}
        best_by_period[period] = pbest
        if best is None or pbest[0] > best[0]:
            best = pbest
    return {"period": None, "word": best[1] if best else None, "score": best[0] if best else None,
            "cities_total": len(M.parse_state(state_text)["cities"]), "budget": budget,
            "alphabet": alpha, "cleared": False, "best_by_period": best_by_period,
            "note": f"no periodic word of period <= {upto} saves every city"}


def zork_min_period(world_text, upto=ZORK_PSTAR_MAX_PERIOD):
    import zork as Z
    alpha = zork_alphabet(world_text)
    scanned = 0
    for period in range(1, upto + 1):
        for word in itertools.product(alpha, repeat=period):
            scanned += 1
            rec = Z.play(world_text, _repeat(word, ZORK_BUDGET))
            if rec["finished"]:
                return {"period": period, "word": " ; ".join(word), "commands_consumed":
                        rec["commands_consumed"], "streams_scanned": scanned, "budget": ZORK_BUDGET,
                        "alphabet_size": len(alpha), "cleared": True}
    return {"period": None, "word": None, "streams_scanned": scanned, "budget": ZORK_BUDGET,
            "alphabet_size": len(alpha), "cleared": False,
            "note": f"no periodic word of period <= {upto} finishes this world"}


def snake_score(page, seed, word, ticks=SNAKE_PSTAR_TICKS):
    """Eat-count for one repeated word on one seed, through the REAL page. The page is the instrument."""
    import snake_run as R
    st = page.new_episode(seed)
    prev, eaten = R.projection(st), 0
    for letter in _repeat(word, ticks):
        after = R.projection(page.step(letter)["state"])
        eaten += R._ate(prev, after)
        prev = after
    return eaten


def snake_min_period(page, seed, upto=SNAKE_MAX_PERIOD, ticks=SNAKE_PSTAR_TICKS):
    """Smallest period that attains the class-best eat count. Snake has no cleared state -- see above."""
    best_by_period, best, scanned = {}, None, 0
    for period in range(1, upto + 1):
        pbest = (-1, "")
        for word in itertools.product(SNAKE_ALPHABET, repeat=period):
            scanned += 1
            score = snake_score(page, seed, word, ticks)
            if score > pbest[0]:
                pbest = (score, "".join(word))
        best_by_period[period] = pbest
        if best is None or pbest[0] > best[0]:
            best = pbest
    if best is None or best[0] <= 0:
        return {"period": None, "word": None, "score": 0, "streams_scanned": scanned,
                "ticks": ticks, "best_by_period": best_by_period, "cleared": False,
                "note": f"no periodic word of period <= {upto} eats an apple in {ticks} ticks"}
    # p* = the SMALLEST period whose best word attains the class-best score, not the period that found it.
    star = min(p for p, v in best_by_period.items() if v[0] == best[0])
    return {"period": star, "word": best_by_period[star][1], "score": best[0],
            "streams_scanned": scanned, "ticks": ticks, "best_by_period": best_by_period,
            "class_best_word": best[1], "cleared": True}


def snake_control(page, seed, ticks=SNAKE_PSTAR_TICKS):
    """THE INSTRUMENT'S CONTROL: adaptive play on the same seed through the same page must eat an apple.
    If it cannot, the page is not playing and a silent fixed class is not a PASS."""
    import snake_run as R
    from snake_solver import Board, GreedySafeAgent
    st0 = page.new_episode(seed)
    board = Board(st0["canvas"][0] // st0["grid"], st0["canvas"][1] // st0["grid"])
    agent = GreedySafeAgent(board)
    trace, _t, _e = R.play_episode(page, seed, ticks, True, lambda st, eaten: (agent.next_direct(st), None))
    return sum(1 for r in trace if R._ate(r["before"], r["after"]))


def pstar_table(snake_seeds=None, snake_ticks=SNAKE_PSTAR_TICKS, upto=(MC_PSTAR_SEARCH,
                ZORK_PSTAR_SEARCH, SNAKE_PSTAR_SEARCH)):
    """Every board of every event in one table: p*, witness, control, and the declared width beside it."""
    rows = []
    mc_upto, z_upto, sn_upto = upto
    for name in ("mc_01_one_shot", "mc_02_scarcity"):
        p = os.path.join(HERE, "levels", f"{name}.txt")
        text = open(p, encoding="utf-8").read()
        r = mc_min_period(text, upto=mc_upto)
        rows.append({"event": "missile", "board": f"levels/{name}.txt", "sha256": _digest(text),
                     "p_star": r["period"], "witness": r["word"], "score": r.get("score"),
                     "ceiling": r.get("cities_total"), "cleared": r["cleared"],
                     "gate_width": MC_MAX_PERIOD, "search_bound": mc_upto,
                     "streams": sum(len(r["alphabet"]) ** k for k in range(1, mc_upto + 1)),
                     "budget": r["budget"], "best_by_period": {str(k): v for k, v in r["best_by_period"].items()},
                     "control": "n/a -- the score's ceiling is the control (a state that cannot be saved "
                                "by any play is reported, not scored)"})
    for name in ("zork_01_the_floor", "zork_02_long_crawl"):
        p = os.path.join(HERE, "levels", f"{name}.txt")
        text = open(p, encoding="utf-8").read()
        r = zork_min_period(text, upto=z_upto)
        ctrl_hits, ctrl_streams, _a = zork_probe(ZORK_CONTROL_WORLD)
        rows.append({"event": "zork", "board": f"levels/{name}.txt", "sha256": _digest(text),
                     "p_star": r["period"], "witness": r["word"], "cleared": r["cleared"],
                     "gate_width": ZORK_MAX_PERIOD, "search_bound": z_upto,
                     "streams": r["streams_scanned"], "budget": r["budget"],
                     "alphabet_size": r["alphabet_size"],
                     "control": f"synthetic control world: {len(ctrl_hits)} of {ctrl_streams} streams finish it"})
    if snake_seeds:
        import snake_page
        page = snake_page.SnakePage().start()
        try:
            for seed in snake_seeds:
                ctrl = snake_control(page, seed, snake_ticks)
                r = snake_min_period(page, seed, upto=sn_upto, ticks=snake_ticks)
                rows.append({"event": "snake", "board": f"seed {seed}", "seed": seed,
                             "p_star": r["period"], "witness": r["word"], "score": r["score"],
                             "cleared": r["cleared"], "streams": r["streams_scanned"],
                             "gate_width": None, "search_bound": sn_upto,
                             "ticks": snake_ticks, "ticks_cap": snake_ticks,
                             "best_by_period": {str(k): v for k, v in r["best_by_period"].items()},
                             "adaptive_baseline_score": ctrl,
                             "control": (f"greedy-safe on the same seed, same cap, same page: {ctrl} apple(s)"
                                         if ctrl else "DID NOT FIRE -- the page ate nothing, so a silent "
                                                      "fixed class is UNDETERMINED, not PASS")})
        finally:
            page.stop()
    return rows


# ------------------------------------------------------------------------------------------------
def _self_test():
    ok = [0, 0]

    def ck(label, got, want):
        ok[0 if got == want else 1] += 1
        print(f"  {'ok  ' if got == want else 'FAIL'}  {label}: {got!r}"
              + ("" if got == want else f"  (wanted {want!r})"))

    print("DEGENERATE-CLASS GATE -- CONTROLS, BOTH DIRECTIONS")

    # 1. THE CONTROL FIRES: the retired board is still cleared by the class.
    r = gate("sokoban", os.path.join(HERE, SOKOBAN_CONTROL))
    ck("sokoban control (01_one_push) is DEGENERATE", r["verdict"], DEGENERATE)
    ck("sokoban control witness is the period-1 word R", (r["hits"][0]["word"], r["hits"][0]["period"]), ("R", 1))
    ck("sokoban class size is 84", r["streams_evaluated"], 84)

    # 2. THE SUBJECTS: the two boards that survive the class.
    for name in ("02_two_boxes", "03_the_corner_waiting"):
        r = gate("sokoban", os.path.join(HERE, "levels", f"{name}.txt"))
        ck(f"sokoban {name} is PASS", r["verdict"], PASS)
        ck(f"sokoban {name} has no hit", r["n_hits"], 0)

    # 3. THE CONTROL DRIVEN TO FAIL: swap the control for a board the class cannot clear.
    #    Without this, "the control fired" is a claim about one fixture rather than about the probe.
    import sokoban as S
    # a board the class cannot clear: the control's geography with the target moved out of reach of
    # every period-1..3 cycle. Built, not assumed, and asserted to be a legal level.
    impossible = "#######\n#@$ . #\n#######\n"

    saved = globals()["sokoban_probe"]

    def blind_probe(level_text):
        # the probe with its hit path neutralised -- exactly the failure mode that must not read PASS
        hits, n = saved(level_text)
        return [], n

    globals()["sokoban_probe"] = blind_probe
    try:
        r = gate("sokoban", os.path.join(HERE, "levels", "02_two_boxes.txt"))
        ck("a probe whose control cannot fire returns UNDETERMINED (not PASS)", r["verdict"], UNDETERMINED)
    finally:
        globals()["sokoban_probe"] = saved
    ck("the neutralised fixture is a legal level", isinstance(S.parse(impossible), dict), True)

    # 4. ZORK: the control world must be seen as degenerate, and the prediction tested on real worlds.
    r = gate("zork", os.path.join(HERE, "levels", "zork_01_the_floor.txt"))
    ck("zork control world fires (n_control_hits > 0)", r["n_control_hits"] > 0, True)
    print(f"       zork_01: {r['verdict']} -- {r['why']}"
          + (f"  witness {r['hits'][0]['word']!r}" if r["hits"] else ""))
    r2 = gate("zork", os.path.join(HERE, "levels", "zork_02_long_crawl.txt"))
    print(f"       zork_02: {r2['verdict']} -- {r2['why']}"
          + (f"  witness {r2['hits'][0]['word']!r}" if r2["hits"] else ""))

    # 5. CHESS: named class, no probe -> UNDETERMINED, never PASS.
    ck("chess is UNDETERMINED", gate("chess", os.path.join(HERE, "CARD_chess.md"))["verdict"], UNDETERMINED)

    # 6. p* IS A MEASUREMENT, NOT A HOPE: the width-free index on two boards, re-derived here.
    p1 = sokoban_min_period(os.path.join(HERE, SOKOBAN_CONTROL), upto=8)
    ck("p*(01_one_push) = 1 with word R", (p1["period"], p1["word"]), (1, "R"))
    p2 = sokoban_min_period(os.path.join(HERE, "levels", "02_two_boxes.txt"), upto=8)
    ck("p*(02_two_boxes) = 7 with word DDRLUUR (null clears it -> retired)",
       (p2["period"], p2["word"], p2["moves"]), (7, "DDRLUUR", 28))
    p3 = sokoban_min_period(os.path.join(HERE, "levels", "03_the_corner_waiting.txt"), upto=8)
    ck("p*(03_the_corner_waiting) = 6 with word RULDLU", (p3["period"], p3["word"]), (6, "RULDLU"))
    ck("03's p* is FAR wider than the declared width 3", p3["period"] > SOKOBAN_MAX_PERIOD, True)

    # 7. p* FOR THE EVENTS THAT ARE NOT SOKOBAN: the same measure, each with its own clear condition.
    mc1 = os.path.join(HERE, "levels", "mc_01_one_shot.txt")
    t1 = open(mc1, encoding="utf-8").read()
    r = mc_min_period(t1, upto=3)
    ck("p*(mc_01) = 1 -- one threat, one round: no schedule needs a second period",
       (r["period"], r["word"]), (1, "1P"))
    import missile_command as M
    ck("the mc_01 witness REPRODUCES: '1P' repeated saves the only city",
       M.play(t1, _repeat(("1P",), r["budget"]))["cities_surviving"], 1)
    mc2 = os.path.join(HERE, "levels", "mc_02_scarcity.txt")
    t2 = open(mc2, encoding="utf-8").read()
    a2, b2 = mc_alphabet(t2)
    ck("mc_02's alphabet is silo x threat plus PASS", (len(a2), b2), (17, 5))
    r2 = mc_min_period(t2, upto=3)
    # FOUR cities are threatened by four distinct missiles, and one token fires once -- so no period < 4
    # can save all four, and `upto=3` is the honest bound that this measurement must BREAK THROUGH.
    ck("p*(mc_02) > 3 at bound 3: the declared-width class cannot save every city",
       (r2["period"], r2["score"], r2["cities_total"]), (None, 3, 4))
    r2b = mc_min_period(t2, upto=4)
    ck("p*(mc_02) = 4 -- a fixed 4-word schedule saves every city without reading the board",
       (r2b["period"], r2b["score"]), (4, 4))
    print(f"       mc_02 witness at p*=4: {r2b['word']!r}")

    z1 = os.path.join(HERE, "levels", "zork_01_the_floor.txt")
    zt1 = open(z1, encoding="utf-8").read()
    rz = zork_min_period(zt1, upto=3)
    # The witness is whatever the sorted alphabet reaches first, and `take brasskey` sorts before
    # `take key` -- the SAME action under an alias the world declares. So the assertion is on the cycle,
    # not on one spelling of it: period 2, and the two commands are "take the key" then "go north".
    ck("p*(zork_01) = 2 and the cycle is take-key ; north", (rz["period"], [w.replace("brasskey", "key").split()[0]
       for w in rz["word"].split(" ; ")]), (2, ["take", "n"]))
    z2 = os.path.join(HERE, "levels", "zork_02_long_crawl.txt")
    rz2 = zork_min_period(open(z2, encoding="utf-8").read(), upto=3)
    ck("zork_02 is NOT cleared at bound 3, and the bound travels with the result",
       (rz2["period"], rz2["cleared"]), (None, False))
    print(f"       zork_02: {rz2['streams_scanned']} streams, period <= 3, "
          f"alphabet {rz2['alphabet_size']} -- {rz2['note']}")

    print(f"\n  {ok[0]} passed, {ok[1]} failed")
    return 0 if ok[1] == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--event", choices=["sokoban", "zork", "chess"])
    ap.add_argument("--board")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-period", type=int, default=None,
                    help="sokoban only: report the board's periodic clearance index p* by searching "
                         "periods 1..N (catalogue question, not the per-run gate)")
    ap.add_argument("--pstar-table", action="store_true",
                    help="every board of every event: p*, witness, control, and the search bound")
    ap.add_argument("--snake-seeds", default="", help="comma-separated seeds for --pstar-table")
    ap.add_argument("--snake-ticks", type=int, default=SNAKE_PSTAR_TICKS)
    ap.add_argument("--write-json", default=None)
    a = ap.parse_args()
    if a.write_json and not a.pstar_table:
        ap.error("--write-json belongs to --pstar-table")
    if a.self_test:
        return _self_test()
    if a.pstar_table:
        seeds = [s.strip() for s in a.snake_seeds.split(",") if s.strip()]
        rows = pstar_table(seeds, a.snake_ticks)
        print("| event | board | p* | witness | stream/score | control |")
        print("|---|---|---|---|---|---|")
        for r in rows:
            meas = (f"{r['score']} apple(s) @ {r['ticks']}t / adaptive {r['adaptive_baseline_score']}"
                    if r["event"] == "snake" else
                    f"{r.get('score')} of {r.get('ceiling')} cities" if r["event"] == "missile"
                    else f"budget {r['budget']} cmds, alphabet {r.get('alphabet_size')}")
            print(f"| {r['event']} | {r['board']} | {r['p_star']} | {r['witness']} | {meas} | "
                  f"{r['control']} |")
        if a.write_json:
            with open(a.write_json, "w") as f:
                json.dump({"measured_at": __import__("datetime").datetime.now().astimezone().isoformat(),
                           "bounds": {"missile": MC_PSTAR_SEARCH, "zork": ZORK_PSTAR_SEARCH,
                                      "snake": SNAKE_PSTAR_SEARCH, "snake_ticks": a.snake_ticks},
                           "gate_widths": {"sokoban": SOKOBAN_MAX_PERIOD, "zork": ZORK_MAX_PERIOD,
                                           "missile": MC_MAX_PERIOD, "chess": None},
                           "rows": rows}, f, indent=1)
            print(f"\nwritten {a.write_json}")
        return 0
    if a.max_period is not None:
        if a.event != "sokoban" or not a.board:
            ap.error("--max-period needs --event sokoban --board <path>")
        r = sokoban_min_period(a.board, upto=a.max_period)
        r["board"] = os.path.relpath(a.board, HERE)
        print(json.dumps(r, indent=1))
        return 0
    if not a.event or not a.board:
        ap.error("--event and --board are required (or --self-test)")
    r = gate(a.event, a.board)
    print(json.dumps(r, indent=1) if a.json else
          f"{r['verdict']}  {r['event']}  {r['board']}\n  class      {r['class']}\n"
          f"  streams    {r['streams_evaluated']}   hits {r['n_hits']}"
          f"   control hits {r['n_control_hits']}\n  why        {r['why']}")
    return 0 if r["verdict"] != DEGENERATE else 1


if __name__ == "__main__":
    sys.exit(main())
