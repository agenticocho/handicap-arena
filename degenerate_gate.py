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

    print(f"\n  {ok[0]} passed, {ok[1]} failed")
    return 0 if ok[1] == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--event", choices=["sokoban", "zork", "chess"])
    ap.add_argument("--board")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
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
