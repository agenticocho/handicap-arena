#!/usr/bin/env python3
"""SOKOBAN -- event 2 of THE ORDER. The simulator, and NOTHING ELSE.

WHY THIS GAME, IN ONE LINE PER CONSTRAINT IT SATISFIES BY CONSTRUCTION RATHER THAN BY HOPE:

  1. NO LEGAL-MOVE GENERATION. The action space is FOUR SYMBOLS -- U D L R. The model SELECTS; it does not
     generate. This is what killed chess: the entrant had to derive a legal move from a position and
     nothing on this box could.
  2. NO EXTERNAL ORACLE. The simulator decides solved or unsolved and the score is the move counter. Chess
     carried the third reorder case -- an oracle binary absent from the box. Sokoban drops that class of
     prerequisite entirely, and with it the largest item in a port to another machine.
  3. SHORT ANSWERS. A one-letter answer cannot be deliberated into the token cap. The second failure mode
     measured on chess was deliberation without commitment -- 2314 and 2048 tokens, both cap-hit, no move.
  4. FORMAT A, THE ORDER'S OWN REASON: IRREVERSIBLE PLANNING -- dead-end recognition, asked once, at the
     boundary. Boxes push and never pull, so one wrong push kills a level permanently.

WHAT IS DELIBERATELY ABSENT: no solver, no optimiser, no renderer, no time limit. Dead-end detection is a
LATER measurement and needs a solver that does not exist yet; blocking version one on it would be the
third-reorder defect committed on purpose. THE CAP IS THE BUDGET, NOT THE CLOCK.

LEVELS ARE ASCII, so a level is a text blob that travels in a message and diffs in git:

    #  wall        .  target       $  box         @  player
    *  box on a target            +  player on a target        (space) floor

THE ONE RULE THAT MATTERS FOR MEASUREMENT: AN ILLEGAL PUSH IS A NO-OP, AND IT IS RECORDED ANYWAY.
In Sokoban a move into a wall, or a push into a wall or another box, simply does not happen -- so the
board is unchanged and a naive move counter would count a model that bumped a wall forever as having
played a long game. Both quantities are therefore recorded and they are different claims:

    moves      SUCCESSFUL actions -- the score, and the number that is comparable across entrants
    attempted  every token the model emitted, legal or not
    blocked    attempts that could not be made; a wall-bumper's signature

    python3 sokoban.py --level levels/01_first_push.txt --moves ULLDDR
    python3 sokoban.py --self-test
"""
import argparse
import json
import os
import sys

WALL, TARGET, BOX, PLAYER, FLOOR = "#", ".", "$", "@", " "
BOX_ON, PLAYER_ON = "*", "+"
ACTIONS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


# AN EXPLICIT GIVE-UP IS NOT NOISE. `RESIGN` IS NOT AN ACTION LETTER, so it used to be counted as
# `unrecognised` alongside typos -- but a model that says it is beaten when it IS beaten, and one that says
# it when it is NOT, are the dead-end faculty this cabinet exists to measure. THE GIVE-UP IS THE SIGNAL.
#
# AND IT IS MATCHED EXACTLY, because this is the very word that caused the truncation defect: `RESIGN` was
# once read as `R` (Right) and EXECUTED. A prefix or substring match here would reintroduce exactly that.
# Whitelist, whole-token, nothing inferred.
GIVE_UP_TOKENS = {"RESIGN", "RESIGNS", "RESIGNED", "GIVEUP", "SURRENDER", "IQUIT", "QUIT", "FORFEIT"}


def _is_give_up(tok):
    """Exact whole-token match after removing spaces and case. NOT a prefix, NOT a substring."""
    t = "".join((tok or "").split()).upper()
    return t in GIVE_UP_TOKENS


def parse(level_text):
    """ASCII -> state. Raises on a level that is not a level, because a malformed board silently parsed is
    a board whose measurements are about something else."""
    walls, targets, boxes = set(), set(), set()
    player = None
    rows = [r for r in level_text.splitlines() if r.strip() != ""]
    if not rows:
        raise ValueError("empty level")
    width = max(len(r) for r in rows)
    for r, line in enumerate(rows):
        for c, ch in enumerate(line.ljust(width)):
            if ch == WALL:
                walls.add((r, c))
            elif ch == TARGET:
                targets.add((r, c))
            elif ch == BOX:
                boxes.add((r, c))
            elif ch == PLAYER:
                # B3 -- MORE THAN ONE PLAYER IS AN ERROR, NOT A BOARD. The old code overwrote `player` on every
                # `@`/`+`, so a two-player level PARSED SILENTLY and the last one won -- a hole in the control
                # "a malformed level is an error, not a board". VERIFIED before fixing: a level with two players
                # parsed without error and reported player=(1,3).
                if player is not None:
                    raise ValueError(f"level has more than one player (@) -- one at row {r} col {c}, another "
                                     f"already at {player}. A level is one player.")
                player = (r, c)
            elif ch == BOX_ON:
                boxes.add((r, c))
                targets.add((r, c))
            elif ch == PLAYER_ON:
                if player is not None:
                    raise ValueError(f"level has more than one player (@/+) -- one at row {r} col {c}, another "
                                     f"already at {player}. A level is one player.")
                player = (r, c)
                targets.add((r, c))
            elif ch != " ":
                raise ValueError(f"unknown level character {ch!r} at row {r} col {c}")
    if player is None:
        raise ValueError("level has no player (@)")
    if not boxes:
        raise ValueError("level has no boxes ($)")
    if not targets:
        raise ValueError("level has no targets (.)")
    if len(boxes) != len(targets):
        raise ValueError(f"{len(boxes)} boxes against {len(targets)} targets -- an unbalanced level "
                         f"cannot be solved and would be measured as an entrant failure")
    # B2's MEASURED PROPERTY: IS THIS BOARD ENCLOSED? A level with a non-wall cell on any edge CAN be walked off,
    # so whether it can is a declared property of the LEVEL rather than an accident discovered mid-run. With
    # out-of-bounds now blocked, an unenclosed level is no longer a hole in the simulation -- but it remains a
    # property worth recording, because it is the difference between a level that contains its player and one
    # that merely refuses to let them leave.
    enclosed = (all((0, c) in walls and (len(rows) - 1, c) in walls for c in range(width))
                and all((r, 0) in walls and (r, width - 1) in walls for r in range(len(rows))))
    return {"walls": walls, "targets": targets, "boxes": set(boxes), "player": player,
            "rows": len(rows), "cols": width, "enclosed": enclosed}


def render(st):
    out = []
    for r in range(st["rows"]):
        row = []
        for c in range(st["cols"]):
            p = (r, c)
            if p in st["walls"]:
                row.append(WALL)
            elif p == st["player"]:
                row.append(PLAYER_ON if p in st["targets"] else PLAYER)
            elif p in st["boxes"]:
                row.append(BOX_ON if p in st["targets"] else BOX)
            elif p in st["targets"]:
                row.append(TARGET)
            else:
                row.append(FLOOR)
        out.append("".join(row))
    return "\n".join(out)


def solved(st):
    return st["boxes"] == st["targets"]


def step(st, action):
    """-> (new_state, outcome). outcome is one of: moved, pushed, blocked.

    AN ILLEGAL PUSH IS A NO-OP AND IS REPORTED AS ONE. It is not an error, it is not a termination, and it
    is not the entrant's disqualification -- it is a fact about the attempt, and the measurement keeps it.
    """
    if action not in ACTIONS:
        return st, "blocked"
    dr, dc = ACTIONS[action]
    pr, pc = st["player"]
    ahead = (pr + dr, pc + dc)
    # B2 -- OUT OF BOUNDS IS BLOCKED. Ruled on the report from an independent implementation and VERIFIED here
    # before fixing: on an unenclosed level the player reached row 3 of a 3-row board, `render` stopped drawing
    # them, and the game continued on a board that no longer contained the player -- reachable in three moves, and
    # every later screen a position the entrant cannot act from.
    #
    # I HAD ALREADY ROUTED AROUND THIS WITHOUT NAMING IT: the independent BFS oracle in recovery_semantic.py
    # carries its own bounds check, because this function did not have one. A bug you work around in your own
    # code is a bug you have already decided is real.
    if not (0 <= ahead[0] < st["rows"] and 0 <= ahead[1] < st["cols"]):
        return st, "blocked"
    if ahead in st["walls"]:
        return st, "blocked"
    if ahead in st["boxes"]:
        beyond = (ahead[0] + dr, ahead[1] + dc)
        # A BOX CANNOT BE PUSHED INTO A WALL OR INTO ANOTHER BOX. That is the entire irreversibility rule:
        # nothing pulls, so a crate against a wall is against it for the rest of the level.
        # AND IT CANNOT BE PUSHED OFF THE BOARD EITHER -- the same hole as the player's, one step further out,
        # and worse: a crate beyond the edge is a crate no render shows and no target can ever reach.
        if not (0 <= beyond[0] < st["rows"] and 0 <= beyond[1] < st["cols"]):
            return st, "blocked"
        if beyond in st["walls"] or beyond in st["boxes"]:
            return st, "blocked"
        nb = set(st["boxes"])
        nb.discard(ahead)
        nb.add(beyond)
        nxt = dict(st, boxes=nb, player=ahead)
        return nxt, "pushed"
    return dict(st, player=ahead), "moved"


def play(level_text, tokens, stop_when_solved=True):
    """A level plus a move stream -> the measurement. THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE:

        solved + moves          the number, and the reason this game was chosen
        trace[] per ply         level, action, outcome, board -- so a later reader can REPLAY it
        blocked                 attempts that could not be made

    `tokens` is the model's output split into actions. Anything that is not U D L R is counted as
    `unrecognised` and changes nothing -- it is a fact about the output, not about the board.
    """
    st = parse(level_text)
    # B1 -- `tokens` IS MATERIALISED SO THE EMITTED LENGTH IS KNOWABLE. The ruled fix needs both quantities, and
    # one of them is the length of the stream the entrant produced; enumerate() over a generator cannot report it.
    tokens = list(tokens)
    trace, moves, blocked, not_an_action, give_up = [], 0, 0, 0, 0
    gave_up_at: int | None = None
    for i, tok in enumerate(tokens):
        # AN EXPLICIT GIVE-UP IS A SIGNAL AND IT IS TERMINAL. It ends the run where it happens, because a
        # resignation the simulator ignores is not a resignation -- and because the point is to record the
        # DECISION, not to watch the model keep bumping walls afterwards.
        if _is_give_up(tok):
            give_up += 1
            gave_up_at = i
            trace.append({"ply": i, "token": tok, "action": None, "outcome": "give_up",
                          "board": render(st)})
            break
        # THE ANSWER IS EXACTLY ONE LETTER, SO ANYTHING ELSE IS NOT AN ACTION -- NEVER TRUNCATED.
        # The first version took token[:1], which read "RESIGN" as `R` (right) and executed it. A SIX-LETTER
        # WORD BECAME A LEGAL ACTION BY ACCIDENT, which is the same class as every false verdict this
        # project has filed: a reader broad enough to find an answer in text that does not contain one.
        act = (tok or "").strip().upper()
        if len(act) != 1 or act not in ACTIONS:
            not_an_action += 1
            trace.append({"ply": i, "token": tok, "action": None, "outcome": "not_an_action",
                          "board": render(st)})
            continue
        nxt, outcome = step(st, act)
        if outcome == "blocked":
            blocked += 1
        else:
            moves += 1
        st = nxt
        trace.append({"ply": i, "token": tok, "action": act, "outcome": outcome, "board": render(st)})
        if stop_when_solved and solved(st):
            break
    # B1 -- `attempted` MEANT TWO THINGS AND NOW NAMES NEITHER. The frozen harness truncates the stream at the end
    # of the run and counted the CONSUMED tokens; the other implementation consumes the stream and counts the
    # REMAINDER separately. 13 of 75 probes disagreed and every one was here -- ON THE DENOMINATOR for the
    # not_an_action and blocked rates, so two conforming implementations computed different rates from one run.
    #
    # BOTH ARE NAMED, AND THE RATE IS solved / attempted_emitted -- because that is the quantity a SHORTER RUN
    # CANNOT FLATTER. It is the same defect this cabinet closed tonight one level up, where a rate over
    # `attempted` could be improved by quitting early.
    return {"solved": solved(st), "moves": moves,
            "attempted_emitted": len(tokens), "attempted_consumed": len(trace),
            # DEPRECATED AND KEPT ONLY SO THE EXISTING BATCH AND REPORT PATHS DO NOT BREAK IN THE SAME COMMIT THAT
            # REPLACES THEM: `attempted` still equals attempted_consumed. My ruling retires the name; it does not
            # require retiring it mid-flight. A READER OF AN OLD RECORD SHOULD READ `attempted` AS CONSUMED, which
            # is what it always was.
            "attempted": len(trace), "attempted_note": "DEPRECATED -- equals attempted_consumed; future runs use "
                                                       "the named pair",
            "blocked": blocked, "not_an_action": not_an_action, "give_up": give_up,
            "gave_up_at": gave_up_at,
            # ENDED says BY WHAT PATH, written by the path that produced it and never inferred later --
            # the same rule the chess termination follows.
            "ended": ("gave_up" if give_up else ("solved" if solved(st) else "commands_exhausted")),
            "final_board": render(st), "trace": trace}


# -------------------------------------------------------------------------------------- controls
def _self_test():
    fails = []
    total = [0]                                  # a count that cannot go stale when controls are added

    def ck(name, got, want):
        total[0] += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 94)
    print("SOKOBAN SIMULATOR CONTROLS")
    print("=" * 94)

    print("\n[1] parsing and round-tripping")
    lv = "#####\n#@$.#\n#####"
    st = parse(lv)
    ck("render(parse(x)) == x for a simple level", render(st), lv)
    ck("one box, one target", (len(st["boxes"]), len(st["targets"])), (1, 1))
    ck("player found", st["player"], (1, 1))
    ck("box-on-target and player-on-target parse to the same sets",
       parse("#####\n#@*#\n#####")["boxes"], {(1, 2)})
    ck("player-on-target marks the target too", parse("#####\n#+$#\n#####")["targets"], {(1, 1)})

    print("\n[2] A MALFORMED LEVEL IS AN ERROR, NOT A BOARD")
    for bad, why in ((("#####\n#@$#\n#####"), "no target"),
                     (("#####\n#@..#\n#####"), "no box"),
                     (("#####\n#.$$.#\n#####"), "two boxes one target"),
                     (("#####\n#@$X#\n#####"), "unknown character")):
        try:
            parse(bad)
            ck(f"rejects a level with {why}", "parsed anyway", "ValueError")
        except ValueError:
            ck(f"rejects a level with {why}", "ValueError", "ValueError")

    print("\n[3] the movement rules, one at a time")
    st = parse("######\n#@ $.#\n######")
    st2, o = step(st, "R")
    ck("stepping onto floor is `moved`", o, "moved")
    ck("...and the player moves", st2["player"], (1, 2))
    st2, o = step(st, "L")
    ck("walking into a wall is `blocked`", o, "blocked")
    ck("...and the board is UNCHANGED", st2, st)
    st2, o = step(st, "U")
    ck("walking off the top into a wall is `blocked`", o, "blocked")

    print("\n[4] pushing -- including the push that kills the level")
    st = parse("######\n#@ $.#\n######")
    st2, o = step(st, "R")
    st2, o = step(st2, "R")
    ck("pushing a box is `pushed`", o, "pushed")
    ck("...and the box moved with the player",
       (st2["boxes"], st2["player"]), ({(1, 4)}, (1, 3)))
    # a box against a wall, pushed into the wall
    st = parse("######\n#@$#.#\n######")
    st2, o = step(step(st, "R")[0], "R")
    ck("a push into a WALL is `blocked`", o, "blocked")
    ck("...and nothing moved -- no pull, so that crate is against the wall for good", st2, st)
    # box against box
    st = parse("#######\n#@$$..#\n#######")
    st2, o = step(step(st, "R")[0], "R")
    ck("a push into ANOTHER BOX is `blocked`", o, "blocked")

    print("\n[5] solved, and the move counter")
    # a level that genuinely needs three moves: two steps then a push
    lv = "#######\n#@  $.#\n#######"
    r = play(lv, ["R", "R", "R"])
    ck("solved", r["solved"], True)
    ck("move count counts SUCCESSFUL actions", r["moves"], 3)
    ck("a blocked attempt does NOT count as a move", play(lv, ["L", "R", "R", "R"])["moves"], 3)
    ck("...but it IS recorded as blocked", play(lv, ["L", "R", "R", "R"])["blocked"], 1)
    ck("...and as attempted", play(lv, ["L", "R", "R", "R"])["attempted"], 4)
    ck("the trace has one row per ply ATTEMPTED", len(play(lv, ["L", "R", "R", "R"])["trace"]), 4)
    ck("...and every row carries the board", all("board" in t for t in play(lv, ["R"])["trace"]), True)
    ck("and the trace STOPS once solved rather than running the stream out",
       len(play("#####\n#@$.#\n#####", ["R", "R", "R"])["trace"]), 1)

    print("\n[6] the wall-bumper -- why `moves` and `attempted` are different claims")
    r = play(lv, ["U"] * 50)
    ck("50 wall bumps are 0 moves", r["moves"], 0)
    ck("...and 50 attempts", r["attempted"], 50)
    ck("...and 50 blocked", r["blocked"], 50)
    ck("...and the level is UNSOLVED", r["solved"], False)

    print("\n[7] not-an-action and GIVE-UP are DIFFERENT COUNTERS")
    r = play(lv, ["e2e4", "Q", "RESIGN", "R", "R", "R"])
    ck("two junk tokens are `not_an_action`", r["not_an_action"], 2)
    ck("...and RESIGN is a GIVE-UP, not noise", r["give_up"], 1)
    ck("...and a give-up is TERMINAL -- the three real moves after it never run", r["moves"], 0)
    ck("...and `ended` names the path that ended it", r["ended"], "gave_up")
    ck("...and gave_up_at records where", r["gave_up_at"], 2)
    ck("RESIGN is NOT silently read as `R` (right)",
       play("#####\n#@$.#\n#####", ["RESIGN"])["moves"], 0)
    ck("...and the level is not solved by it", play("#####\n#@$.#\n#####", ["RESIGN"])["solved"], False)
    # THE CALIBRATION THE CHESS GATE BRINGS FOR FREE: a give-up on a level with a ONE-MOVE solution is
    # PREMATURE, and that is provable without a solver because the solution is verified.
    r = play("#####\n#@$.#\n#####", ["RESIGN"], stop_when_solved=False)
    ck("a give-up on a solvable level is recorded as a DECISION, with the board it abandoned",
       (r["ended"], r["solved"], r["trace"][-1]["board"].count("@")), ("gave_up", False, 1))
    ck("a give-up does not count as a move", r["moves"], 0)
    ck("...and it is not counted as a blocked attempt either", r["blocked"], 0)
    ck("a give-up is TERMINAL even with commands left", len(r["trace"]), 1)
    # NOT a prefix or substring match -- the truncation defect must not come back through the give-up door
    ck("`RESIGNED` matches (it is on the whitelist)", play(lv, ["RESIGNED"])["give_up"], 1)
    ck("`R` is an ACTION, not a give-up", play("#####\n#@$.#\n#####", ["R"])["give_up"], 0)
    ck("`RESIGNING` is NOT matched -- exact whole-token only", play(lv, ["RESIGNING"])["not_an_action"], 1)
    ck("`XRESIGN` is NOT matched -- no substring", play(lv, ["XRESIGN"])["not_an_action"], 1)

    print("\n[8] irreversibility -- a push that can never be undone")
    st = parse("#####\n#@$ #\n#  .#\n#####")
    s, o = step(st, "R")
    ck("push 1 works", o, "pushed")
    s, o = step(s, "R")
    ck("push 2 into the wall is blocked -- the crate is one square from the wall", o, "blocked")
    ck("the crate is now stuck off-target and NOTHING CAN PULL IT BACK", solved(s), False)

    print("\n" + "=" * 94)
    n = total[0] - len(fails)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  {n}/{total[0]}")
    print("=" * 94)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level")
    ap.add_argument("--moves", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    if not a.level:
        ap.error("--level or --self-test is required")
    text = open(a.level).read()
    toks = [c for c in a.moves.replace(",", " ").split()] if a.moves else \
           [c for c in a.moves.strip()]
    r = play(text, toks)
    print(f"  solved      {r['solved']}")
    print(f"  moves       {r['moves']}   (successful actions -- the score)")
    print(f"  attempted   {r['attempted']}   blocked {r['blocked']}   unrecognised {r['not_an_action']}")
    print()
    print(r["final_board"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
