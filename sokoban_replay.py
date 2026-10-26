#!/usr/bin/env python3
"""SOKOBAN REPLAY VERIFIER -- a SEPARATE process that executes a plan against the level, and can refuse.

WHY THIS FILE EXISTS
    `sokoban_run.py` scores a cell with `solved = S.play(level, tokens)["solved"]`. The process that PLAYED the
    plan is the process that ASSERTED the score, and nothing re-executed it. A rate computed from rows like
    that measures the driver's optimism, not a solver: the one failure this cabinet cannot detect is a row that
    says `solved: true` over a plan nobody can replay.

    This file is the second opinion, and it is deliberately not a function inside the driver. It is a separate
    executable with its own exit code, so "the row carries the replay's verdict" means a fact another process
    produced:

        VERIFIED              0   the plan replays to a solved board at its LAST ply, and the frozen
                                  simulator's per-ply boards agree with this file's, ply for ply
        REFUSED               3   well-formed input, and the plan does NOT verify -- with a NAMED reason
        USAGE / NOT A LEVEL   2   a level that is not a level has no solvability, and refusing is not a
                                  fourth verdict (the rule `sokoban_solver.py` already carries)
        CROSS-CHECK DISAGREES 5   this file's replay and the frozen simulator reached DIFFERENT boards

WHAT MAKES IT A SECOND OPINION RATHER THAN A SECOND COPY
    1. IT READS THE LEVEL FROM DISK. Never from the row under test. `--row` takes a level NAME and this file
       opens `levels/<name>.txt` itself, so a row that describes a board differently from the file is caught
       by construction rather than by inspection.
    2. ITS OWN PARSER AND ITS OWN TRANSITION RULE, written from the level spec, sharing no state with
       `sokoban.py`. The frozen simulator is imported for ONE purpose -- the cross-check -- and its agreement
       is recorded, not assumed. Two independent implementations that agree are a stronger statement than one
       implementation that is trusted.
    3. THE CROSS-CHECK IS COMPARED PLY BY PLY, not only at the end. Two engines can reach the same final board
       by different routes on a level with two interchangeable crates; comparing every intermediate board
       catches a divergence that the endpoint hides.
    4. THE CROSS-CHECK CAN FIRE. `SOKOBAN_REPLAY_FAULT=independent-step` breaks this file's own transition on
       purpose; the verdict then says `fault_injected` and the exit code is 5. The control suite uses it to
       prove the cross-check is a mechanism and not decoration. It is an env var so that it cannot be reached
       by a command-line typo, and it travels in the verdict so a faulted run can never be read as a clean one.

WHAT A PLAN IS
    The emitted TOKEN STREAM, blocked attempts kept. Measured on the corpus before this file was written:
    three rows solved level 01 with `['R']`, one with `['D','R']` and one with `['U','U','R']` -- the blocked
    attempts are part of the plan, and a verifier that trims them would agree with three rows and be wrong
    about two. A token that is not an action is recorded as `not_an_action` and changes nothing, exactly as
    the frozen simulator treats it. A give-up token is TERMINAL and can never appear in a verified plan.

    python3 sokoban_replay.py --level levels/01_one_push.txt --plan R
    python3 sokoban_replay.py --row probes/SOKOBAN_Ornith-1.5-9B-Q4_K_M_01_one_push.json --json
    python3 sokoban_replay.py --level levels/03_the_corner_waiting.txt --plan RULDLU --json
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                          # noqa: E402  FROZEN. read-only.

VERIFIED, REFUSED, NOT_A_LEVEL, CROSS_CHECK = "VERIFIED", "REFUSED", "NOT_A_LEVEL", "CROSS_CHECK_DISAGREES"
RC = {VERIFIED: 0, NOT_A_LEVEL: 2, REFUSED: 3, CROSS_CHECK: 5}

WALL, TARGET, BOX, PLAYER, FLOOR, BOX_ON, PLAYER_ON = "#", ".", "$", "@", " ", "*", "+"
DELTA = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

# DECLARED HERE, INDEPENDENTLY OF `sokoban.py`, AND THAT IS THE POINT: if the two whitelists ever disagree, the
# per-ply cross-check reports it as a divergence instead of one silently governing the other.
GIVE_UP_TOKENS = frozenset({"RESIGN", "RESIGNS", "RESIGNED", "GIVEUP", "SURRENDER", "IQUIT", "QUIT",
                            "FORFEIT"})

FAULT = os.environ.get("SOKOBAN_REPLAY_FAULT", "").strip()
FAULTS = {"independent-step": "this file's own transition is broken on purpose: a push moves the crate and "
                              "leaves the player where they were"}


class NotALevel(ValueError):
    """A level that is not a level. It has no solvability, so no verdict -- see `sokoban_solver.py`."""


# ------------------------------------------------------------------------------------------- this file's own board
class Board:
    """This file's own parse of a level. Deliberately a different shape from `sokoban.py`'s dict: walls and
    targets are frozensets of (r,c), the player is a tuple, and the board does NOT carry the boxes -- the state
    does, so the search and the replay can copy a state without copying the level."""

    __slots__ = ("rows", "cols", "walls", "targets", "enclosed")

    def __init__(self, rows, cols, walls, targets, enclosed):
        self.rows, self.cols = rows, cols
        self.walls, self.targets, self.enclosed = walls, targets, enclosed


def parse_level(text):
    """-> (Board, state). State is `(player, frozenset_of_boxes)`. Raises `NotALevel` on anything malformed,
    with the reason: a board silently parsed is a board whose measurements are about something else."""
    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    if not lines:
        raise NotALevel("empty level")
    cols = max(len(ln) for ln in lines)
    walls, targets, boxes, player = set(), set(), set(), None
    for r, ln in enumerate(lines):
        for c, ch in enumerate(ln.ljust(cols)):
            p = (r, c)
            if ch == WALL:
                walls.add(p)
            elif ch == TARGET:
                targets.add(p)
            elif ch == BOX:
                boxes.add(p)
            elif ch == PLAYER:
                if player is not None:
                    raise NotALevel(f"more than one player: {(r, c)} and {player}")
                player = p
            elif ch == BOX_ON:
                boxes.add(p)
                targets.add(p)
            elif ch == PLAYER_ON:
                if player is not None:
                    raise NotALevel(f"more than one player: {(r, c)} and {player}")
                player = p
                targets.add(p)
            elif ch != FLOOR:
                raise NotALevel(f"unknown level character {ch!r} at {(r, c)}")
    rows = len(lines)
    if player is None:
        raise NotALevel("no player (@)")
    if not boxes:
        raise NotALevel("no boxes ($)")
    if not targets:
        raise NotALevel("no targets (.)")
    if len(boxes) != len(targets):
        raise NotALevel(f"{len(boxes)} boxes against {len(targets)} targets -- unbalanced")
    enclosed = (all((0, c) in walls and (rows - 1, c) in walls for c in range(cols))
                and all((r, 0) in walls and (r, cols - 1) in walls for r in range(rows)))
    return Board(rows, cols, frozenset(walls), frozenset(targets), enclosed), (player, frozenset(boxes))


def render(board, state):
    """The board as text, so a verdict can be read and so the cross-check compares like with like."""
    player, boxes = state
    out = []
    for r in range(board.rows):
        row = []
        for c in range(board.cols):
            p = (r, c)
            if p in board.walls:
                row.append(WALL)
            elif p == player:
                row.append(PLAYER_ON if p in board.targets else PLAYER)
            elif p in boxes:
                row.append(BOX_ON if p in board.targets else BOX)
            elif p in board.targets:
                row.append(TARGET)
            else:
                row.append(FLOOR)
        out.append("".join(row))
    return "\n".join(out)


def solved(board, state):
    return state[1] == board.targets


def _faulty(state, nxt, outcome):
    """The DECLARED fault: a push leaves the player behind. Only reachable through `SOKOBAN_REPLAY_FAULT`."""
    if FAULT == "independent-step" and outcome == "pushed":
        return (state[0], nxt[1])
    return nxt


def step(board, state, action):
    """-> (state, outcome). outcome in {moved, pushed, blocked}. This file's own rule, from the spec: a move
    into a wall, off the board, into a crate that cannot be pushed; nothing pulls."""
    if action not in DELTA:
        return state, "blocked"
    dr, dc = DELTA[action]
    pr, pc = state[0]
    ahead = (pr + dr, pc + dc)
    if not (0 <= ahead[0] < board.rows and 0 <= ahead[1] < board.cols) or ahead in board.walls:
        return state, "blocked"
    boxes = state[1]
    if ahead not in boxes:
        return (ahead, boxes), "moved"
    beyond = (ahead[0] + dr, ahead[1] + dc)
    if not (0 <= beyond[0] < board.rows and 0 <= beyond[1] < board.cols):
        return state, "blocked"
    if beyond in board.walls or beyond in boxes:
        return state, "blocked"
    nb = frozenset((boxes - {ahead}) | {beyond})
    return _faulty(state, (ahead, nb), "pushed"), "pushed"


def classify(token):
    """-> ("action", LETTER) | ("give_up", None) | ("not_an_action", None). Exact whole-token matching: a
    six-letter word must not become a legal action by accident."""
    t = "".join((token or "").split()).upper()
    if t in GIVE_UP_TOKENS:
        return "give_up", None
    if len(t) == 1 and t in DELTA:
        return "action", t
    return "not_an_action", None


def replay(board, state0, tokens):
    """Execute the whole plan, recording one row per ply. Does NOT stop at a solve: `solves_at_ply` is the
    first solved ply, and a plan that solves early and keeps going is reported as trailing, not accepted."""
    state, rows = state0, []
    moves = blocked = pushes = not_an_action = 0
    solves_at = None
    for i, tok in enumerate(tokens):
        kind, act = classify(tok)
        if kind == "give_up":
            rows.append({"ply": i, "token": tok, "outcome": "give_up", "board": render(board, state)})
            break
        if kind == "not_an_action":
            not_an_action += 1
            rows.append({"ply": i, "token": tok, "outcome": "not_an_action", "board": render(board, state)})
            continue
        nxt, outcome = step(board, state, act)
        if outcome == "blocked":
            blocked += 1
        else:
            moves += 1
            if outcome == "pushed":
                pushes += 1
        state = nxt
        rows.append({"ply": i, "token": tok, "action": act, "outcome": outcome, "board": render(board, state)})
        if solves_at is None and solved(board, state):
            solves_at = i
    return {"tokens": list(tokens), "trace": rows, "state": state, "moves": moves, "blocked": blocked,
            "pushes": pushes, "not_an_action": not_an_action, "solves_at_ply": solves_at,
            "solved_at_end": solved(board, state), "final_board": render(board, state),
            "ended": rows[-1]["outcome"] if rows else None}


def cross_check(text, tokens, mine):
    """Executed, not assumed: the frozen simulator runs the SAME token stream and every one of its per-ply
    boards must equal this file's. -> a record, and `agrees` is the fact the exit code turns on."""
    frozen = S.play(text, list(tokens), stop_when_solved=False)
    theirs = [row.get("board") for row in frozen.get("trace", [])]
    ours = [row.get("board") for row in mine["trace"]]
    n = min(len(theirs), len(ours))
    first = next((i for i in range(n) if theirs[i] != ours[i]), None)
    agrees = (first is None) and (len(theirs) == len(ours)) and (frozen["final_board"] == mine["final_board"])
    return {"by": "sokoban.play(..., stop_when_solved=False) -- the FROZEN simulator",
            "plies_compared": n, "ply_count_frozen": len(theirs), "ply_count_independent": len(ours),
            "agrees": agrees, "first_divergent_ply": first,
            "frozen_final_board": frozen["final_board"],
            "simulator_sha256": sha256_file(os.path.join(HERE, "sokoban.py"))}


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ------------------------------------------------------------------------------------------------ the verdict
def verify_text(text, tokens, level_name="<text>", level_path=None, claimed_solved=None):
    """-> a verdict dict. EXACTLY ONE of VERIFIED / REFUSED / NOT_A_LEVEL / CROSS_CHECK, plus the reason.

    `claimed_solved` is what a ROW says. It never decides the verdict -- it is compared with it, and the
    comparison is a separate, named field, because a row's claim and a replay's result are different claims.
    """
    verdict = {"level": level_name, "verifier": {"file": "sokoban_replay.py",
                                                 "sha256": sha256_file(os.path.abspath(__file__)),
                                                 "bytes": os.path.getsize(os.path.abspath(__file__))},
               "plan_tokens": list(tokens), "plan_actions": "".join(
                   (classify(t)[1] or "") for t in tokens),
               "level_sha256": sha256_file(level_path) if level_path else None,
               "fault_injected": FAULT or None,
               "row_claim_solved": claimed_solved,
               "refusal_reason": None, "refusal_detail": None}
    if FAULT and FAULT not in FAULTS:
        verdict.update(verdict=REFUSED, exit_code=RC[REFUSED], refusal_reason="unknown_fault_injection",
                       refusal_detail=f"SOKOBAN_REPLAY_FAULT={FAULT!r} is not a declared fault "
                                      f"({sorted(FAULTS)}); refusing rather than running unknown code paths")
        return verdict
    try:
        board, state0 = parse_level(text)
    except NotALevel as e:
        verdict.update(verdict=NOT_A_LEVEL, exit_code=RC[NOT_A_LEVEL], refusal_reason="not_a_level",
                       refusal_detail=str(e))
        return verdict

    mine = replay(board, state0, tokens)
    verdict.update(moves=mine["moves"], blocked=mine["blocked"], pushes=mine["pushes"],
                   not_an_action=mine["not_an_action"], solves_at_ply=mine["solves_at_ply"],
                   plan_len=len(tokens), final_board=mine["final_board"],
                   solved_at_end=mine["solved_at_end"],
                   boxes_on_targets=len(mine["state"][1] & board.targets),
                   targets=len(board.targets), ended=mine["ended"])
    xc = cross_check(text, tokens, mine)
    verdict["cross_check"] = xc

    if not xc["agrees"]:
        verdict.update(verdict=CROSS_CHECK, exit_code=RC[CROSS_CHECK],
                       refusal_reason="cross_check_disagrees",
                       refusal_detail=(f"this file and the frozen simulator reached different boards at ply "
                                       f"{xc['first_divergent_ply']}"
                                       + (f" (fault injected: {FAULTS[FAULT]})" if FAULT else "")))
    elif not mine["solved_at_end"]:
        verdict.update(verdict=REFUSED, exit_code=RC[REFUSED], refusal_reason="not_solved",
                       refusal_detail=(f"plan does not solve the level: {len(mine['state'][1] & board.targets)}"
                                       f" of {len(board.targets)} boxes on targets after {len(tokens)} plies"
                                       + (f"; solved at ply {mine['solves_at_ply']} but the plan continues"
                                          if mine["solves_at_ply"] is not None else "")))
    elif any(row["outcome"] == "give_up" for row in mine["trace"]):
        verdict.update(verdict=REFUSED, exit_code=RC[REFUSED], refusal_reason="plan_contains_a_give_up",
                       refusal_detail="the plan resigns: a resignation is TERMINAL and can never be part of "
                                      "a plan that solves")
    elif mine["solves_at_ply"] != len(tokens) - 1:
        verdict.update(verdict=REFUSED, exit_code=RC[REFUSED], refusal_reason="solved_before_the_plan_ended",
                       refusal_detail=(f"solved at ply {mine['solves_at_ply']} of {len(tokens)} -- the plan "
                                       f"carries {len(tokens) - 1 - mine['solves_at_ply']} trailing plies, so "
                                       f"it is a plan plus noise and not a plan"))
    elif any(row["outcome"] == "give_up" for row in mine["trace"]):
        verdict.update(verdict=REFUSED, exit_code=RC[REFUSED], refusal_reason="plan_contains_a_give_up")
    else:
        verdict.update(verdict=VERIFIED, exit_code=RC[VERIFIED])

    if claimed_solved is not None:
        verdict["claim_matches_verdict"] = (bool(claimed_solved) == (verdict["verdict"] == VERIFIED))
        # A ROW THAT CLAIMS A SOLVE ITS PLAN DOES NOT SUPPORT IS ITS OWN REFUSAL, and it is named that way --
        # but only when the refusal is the generic one. A cross-check divergence or a resignation in the plan is
        # a more specific finding and must not be relabelled into the row's optimism.
        if claimed_solved and verdict["verdict"] == REFUSED and verdict["refusal_reason"] == "not_solved":
            verdict["refusal_reason"] = "row_claims_solved_but_plan_does_not"
    return verdict


# --------------------------------------------------------------------------------------------------- the row
def plan_from_row(row):
    """-> (tokens, source_note). THE PLAN IS READ, NOT PRE-COMPUTED: a row written after this file exists
    carries `plan.tokens`; a historical row does not, and its plan is the emitted turn stream itself -- which
    is why the five solved rows can be certified WITHOUT rewriting a byte of them."""
    blk = row.get("plan")
    if isinstance(blk, dict) and isinstance(blk.get("tokens"), list):
        return [str(t) for t in blk["tokens"]], "plan.tokens (written by this instrument)"
    turns = row.get("turns")
    if isinstance(turns, list) and turns:
        toks = [str(t.get("token")) if t.get("token") is not None else "" for t in turns]
        return toks, "turns[].token (a historical row: its plan is the emitted stream)"
    toks = row.get("tokens")
    if isinstance(toks, list):
        return [str(t) for t in toks], "tokens"
    return None, None


def level_path_for(row, root):
    """THE LEVEL IS A ROOTED NAME, and it is opened at `levels/`, never at a path the row supplies. A row that
    says it played `01_one_push` is verified against `levels/01_one_push.txt` or against nothing."""
    name = row.get("level")
    if not isinstance(name, str) or not name:
        return None
    name = os.path.basename(name)
    if name.endswith(".txt"):
        name = name[:-4]
    return os.path.join(root, "levels", name + ".txt")


# ------------------------------------------------------------------------------------------------------ main
def _print(v, as_json):
    if as_json:
        print(json.dumps(v, indent=1, sort_keys=True))
        return
    print(f"  level        {v.get('level')}")
    print(f"  verdict      {v['verdict']}   (exit {v['exit_code']})")
    print(f"  plan         {v.get('plan_actions')!r}  tokens {v.get('plan_tokens')!r}")
    if v.get("refusal_reason"):
        print(f"  refused by   {v['refusal_reason']}")
        print(f"               {v.get('refusal_detail')}")
    print(f"  replay       moves {v.get('moves')}  pushes {v.get('pushes')}  blocked {v.get('blocked')}  "
          f"solves_at_ply {v.get('solves_at_ply')} of {v.get('plan_len')}")
    print(f"  board        {v.get('boxes_on_targets')}/{v.get('targets')} on target")
    if v.get("cross_check"):
        xc = v["cross_check"]
        print(f"  cross-check  {v['cross_check']['plies_compared']} plies compared against the frozen "
              f"simulator: {'AGREE' if xc['agrees'] else 'DISAGREE at ply ' + str(xc['first_divergent_ply'])}")
    if v.get("row_claim_solved") is not None:
        print(f"  row claims   solved={v['row_claim_solved']}   claim matches replay: "
              f"{v.get('claim_matches_verdict')}")
    if v.get("fault_injected"):
        print(f"  FAULT        {v['fault_injected']} -- {FAULTS.get(v['fault_injected'])}")
    print(v.get("final_board", ""))


def main():
    ap = argparse.ArgumentParser(description="Replay a plan against a level in a separate process, and refuse "
                                             "it when it does not solve.")
    ap.add_argument("--level", help="a level FILE (this is the file that will be read)")
    ap.add_argument("--plan", help="the plan: a string of U D L R, e.g. RULDLU")
    ap.add_argument("--plan-tokens", dest="plan_tokens",
                    help="the plan as a JSON list of tokens, boundary-preserving (this is how the DRIVER passes "
                         "a row's turn stream, and it is the only lossless form)")
    ap.add_argument("--claim-solved", dest="claim_solved", choices=("true", "false"),
                    help="what the caller CLAIMS; compared with the replay, never used to decide it")
    ap.add_argument("--row", help="a cell RECORD: its level name, its plan (or its turn stream), and its claim")
    ap.add_argument("--root", default=HERE, help="tree root the levels/ directory is rooted at")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.row:
        try:
            row = json.load(open(a.row))
        except (OSError, ValueError) as e:
            print(f"  UNREADABLE ROW {a.row}: {e}")
            return 2
        if not isinstance(row, dict):
            print(f"  NOT A ROW: {a.row} is a {type(row).__name__}, not a record")
            return 2
        tokens, source = plan_from_row(row)
        if tokens is None:
            print(f"  NO PLAN IN THE ROW: {a.row} carries neither plan.tokens nor turns[].token, so there is "
                  f"nothing to replay -- and a row with no replayable plan cannot support a solve claim")
            return 3
        path = level_path_for(row, a.root)
        if not path or not os.path.exists(path):
            print(f"  LEVEL NOT FOUND: the row names {row.get('level')!r}, which is not a file under "
                  f"{os.path.join(a.root, 'levels')}")
            return 2
        text = open(path).read()
        v = verify_text(text, tokens, level_name=os.path.basename(path)[:-4], level_path=path,
                        claimed_solved=row.get("solved"))
        v["plan_source"] = source
        v["row_path"] = os.path.relpath(a.row, a.root)
        _print(v, a.json)
        return v["exit_code"]

    if not a.level:
        ap.error("--level with --plan or --plan-tokens, or --row, is required")
    if not os.path.exists(a.level):
        print(f"  LEVEL ABSENT: {a.level}")
        return 2
    if a.plan_tokens is not None:
        try:
            tokens = json.loads(a.plan_tokens)
        except ValueError as e:
            print(f"  --plan-tokens is not JSON: {e}")
            return 2
        if not isinstance(tokens, list):
            print(f"  --plan-tokens must be a JSON LIST of tokens, not a {type(tokens).__name__}")
            return 2
        tokens = [str(t) for t in tokens]
    elif a.plan is not None:
        tokens = [c for c in a.plan if not c.isspace()]
    else:
        ap.error("--level with --plan or --plan-tokens, or --row, is required")
    text = open(a.level).read()
    claimed = None if a.claim_solved is None else (a.claim_solved == "true")
    v = verify_text(text, tokens, level_name=os.path.basename(a.level)[:-4]
                    if a.level.endswith(".txt") else os.path.basename(a.level), level_path=a.level,
                    claimed_solved=claimed)
    _print(v, a.json)
    return v["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
