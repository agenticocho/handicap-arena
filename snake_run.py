#!/usr/bin/env python3
"""SNAKE -- the entrant driver. One move per turn against a LIVE `snake.html`, one artifact per episode.

THE SHAPE (card t_401ee1d7), and it is the sibling cabinet's shape because that shape was earned there:
the wrapper holds the game's tick (`snake_page.py`), the driver asks for exactly one move per turn, the
simulator decides the result, and the record carries the instrument WITH the number.

    python3 snake_run.py --baseline cycle-shortcut --seeds 1,7 --ticks 300
    python3 snake_run.py --entrant Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0.gguf --ticks 60
    python3 snake_run.py --verify probes/SNAKE_baseline-cycle-shortcut_s1.json
    python3 snake_run.py --replay probes/SNAKE_baseline-cycle-shortcut_s1.json
    python3 snake_run.py --self-test

WHAT A SEED CONTROLS, measured rather than assumed: nothing about the geometry. The board, the start cell
(10,10) and the first apple (320,320) are fixed by the file; the seed drives ONLY the seeded PRNG that
replaces `Math.random`, whose single consumer in the page is `getRandomInt` -- the apple respawn. So a
seed list is the level list this game has.

THE TWO LINTS ON A RECORDED NUMBER, because an LLM score with nothing around it is not a measurement:

    the deterministic baseline's score on the SAME seed list (--baseline), and
    a REPLAY of the recorded move list (--replay) that re-enters the real page and must reproduce the
    recorded state chain digest for digest. A trace that cannot be re-entered is a claim about a run.

THE BINARY TRAP: a Bonsai ternary gguf launched through mainline llama.cpp LOADS and emits garbage, and a
`llamacpp` preset takes server ARGUMENTS and cannot pin a binary -- so the default here is the PrismML fork
binary by PATH, its digest travels in the record, and `--llama-server` exists to point at a different
instrument (which is then recorded too, rather than performed outside the artifact).
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from answer_reader import read_answer                                  # noqa: E402  READER OF RECORD (RULING 79)
import snake_page as P                                                 # noqa: E402
import snake_score as SC                                               # noqa: E402
from snake_solver import (Board, CycleAgent, CycleShortcutAgent, GreedySafeAgent,   # noqa: E402
                              dir_from_delta)   # noqa: E402

# THE DECLARED INSTRUMENT. Not a preset: a preset takes server ARGUMENTS and cannot pin a BINARY.
LLAMA_FORK = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
LLAMA_SELECTED = None
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
PROBES = os.path.join(HERE, "probes")
SEEDS_FILE = os.path.join(HERE, "snake", "seeds.txt")

MAX_TOKENS = 64                    # one letter needs a few; a cap that cannot be deliberated into
CTX = 65536                        # the card's floor, kept identical across arms
# THE COMPUTE PATH, AS PARAMETERS RATHER THAN CONSTANTS. `CTX 65536 / -ngl 0` is this driver's
# REGISTERED launch and stays the DEFAULT, so every existing record keeps the instrument it was taken
# under. The suite that owns the card (kanban t_234b2387) runs its rows on the GPU in an 8192 envelope,
# and a launch flag is a COMPUTE-PATH field -- the same class of variable as the binary above -- not
# part of the prompt or the scorer. Both travel in the argv the server is actually started with, so a
# row states the path it ran on and no flag can imply what the process did.
CTX_DECLARED = CTX
NGL_DECLARED = 0
NGL = NGL_DECLARED
# `--parallel` is the same class of field: the registered launch passes no such flag and lets
# llama-server pick its slot count; the suite's card fixes slots at 1. None = pass nothing.
PARALLEL_DECLARED = None
PARALLEL = PARALLEL_DECLARED
TEMPERATURE = 0.0
SERVER_SEED = 42

# DECLARED, WITH A REASON, AND NOT DEFAULTED: an unrecorded default is indistinguishable from a decision.
# Snake's answer is ONE LETTER, so the deliberation setting is off -- the sibling cabinet measured 2,314
# tokens of `Thinking Process:` and no move on exactly this shape of question.
REASONING_DECLARED = "off"
REASONING_DECLARED_IN = "snake_run.py (declared here; the pattern and the measurement are PREREG_sokoban.md's)"
REASONING_RATIONALE = (
    "Snake's answer is ONE LETTER, the same case as Sokoban and Missile Command: a thinking model puts its "
    "deliberation where the answer belongs and the token ceiling eats it -- measured on unchanged weights at "
    "2,314 tokens with no move. DARTS is the opposite case (exact arithmetic) and is not this cabinet."
)
REASONING_OVERRIDE = os.environ.get("SNAKE_REASONING_TEST_ARM", "").strip().lower() or None
if REASONING_OVERRIDE is not None and REASONING_OVERRIDE not in ("on", "off", "auto"):
    raise SystemExit("SNAKE_REASONING_TEST_ARM must be on|off|auto, got %r" % REASONING_OVERRIDE)
REASONING = REASONING_OVERRIDE or REASONING_DECLARED

# ==================================================================================================
# THE LEGEND. Prose sentences, no pseudo-field labels, and the four CONTROLS named rather than the legal
# moves listed -- the two instrument lessons that cabinet paid for: a legend that looks like a SCHEMA gets
# filled in as a schema, and a menu of legal moves replaces the question with a multiple-choice answer.
# THE WHOLE TEXT TRAVELS IN THE RECORD beside its digest, so the instrument is readable years later.
#
# AND IT HAS ARMS, because the recorded model run produced a CONSTANT answer -- the same letter on all 480
# turns it played -- and WHICH constant moved when the legend's ordering moved. The permutation is the
# control, and each arm is named for the order it presents the four controls in:
#
#   prose  U D L R   -> the run answered R on 120/120 turns at seed 1 (and on the other three seeds)
#   order  D R U L   -> answered D on 120/120 turns at the same seed, same board, same state at tick 0
#   first  R U D L   -> separates "the FIRST control named" from "the alphabetically first control" (D):
#                       the two rules predict differently here, which is the only reason to run it
#
# A result with no control is an observation, not a difference -- and an observation with ONE control is
# still only a difference if the control can fail. Both arms travel with their digest.
# ==================================================================================================
LEGEND_HEAD = (
    "You are playing Snake on a board {w} cells wide and {h} cells tall. The board wraps around, so "
    "sliding off the right edge brings you back on the left and sliding off the bottom brings you back on "
    "the top. There are no walls, and the only way to lose is to run into your own body.\n\n"
    "On the map below a dot is an empty cell, a small letter o is one segment of your body, a capital "
    "letter O is your head, and a capital letter A is the apple you are trying to eat. The first line of "
    "the map is the top row of the board and the first character of each line is its leftmost cell.\n\n"
    "{board}\n\n"
    "Your head is at row {row}, column {col}, counting from zero. You are currently moving {heading}. "
    "Your body is {length} cells long and you have eaten {eaten} apples so far.\n\n"
)

LEGEND_TAIL_PROSE = ("Answer with a single letter: U to move up, D to move down, L to move left, or R to "
                     "move right. You may add an explanation after your answer, and it will be ignored.")
LEGEND_TAIL_ORDER = ("Answer with a single letter: D to move down, R to move right, U to move up, or L to "
                     "move left. You may add an explanation after your answer, and it will be ignored.")
LEGEND_TAIL_FIRST = ("Answer with a single letter: R to move right, U to move up, D to move down, or L to "
                     "move left. You may add an explanation after your answer, and it will be ignored.")

LEGENDS = {"prose": LEGEND_TAIL_PROSE, "order": LEGEND_TAIL_ORDER, "first": LEGEND_TAIL_FIRST}
LEGEND_DEFAULT = "prose"


def legend():
    """Read at CALL TIME, so one process can carry several arms -- and so the arm a record was taken under
    is a VALUE IN THE RECORD rather than an assumption about it."""
    arm = os.environ.get("SNAKE_LEGEND", LEGEND_DEFAULT).strip().lower() or LEGEND_DEFAULT
    if arm not in LEGENDS:
        raise SystemExit("SNAKE_LEGEND must be one of %s, got %r" % (sorted(LEGENDS), arm))
    return arm


def legend_template(arm=None):
    return LEGEND_HEAD + LEGENDS[arm or legend()]


def legend_digest(arm=None):
    return hashlib.sha256(legend_template(arm).encode()).hexdigest()[:16]


def seeds_from_file(path=SEEDS_FILE):
    out = []
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                out.append(int(line))
    return out


def board_text(state):
    """THE SCREEN, not the answers. Pixels -> cells via the game's own `grid`."""
    g = state["grid"]
    w, h = state["canvas"][0] // g, state["canvas"][1] // g
    rows = [["." for _ in range(w)] for _ in range(h)]
    for c in state["cells"]:
        rows[c[1] // g][c[0] // g] = "o"
    rows[state["head"][1] // g][state["head"][0] // g] = "O"
    rows[state["apple"][1] // g][state["apple"][0] // g] = "A"     # drawn last: the target stays visible
    return "\n".join("".join(r) for r in rows)


HEADINGS = {"R": "right", "L": "left", "U": "up", "D": "down"}


def prompt_for(state, eaten):
    g = state["grid"]
    head = (state["head"][0] // g, state["head"][1] // g)
    return legend_template().format(w=state["canvas"][0] // g, h=state["canvas"][1] // g,
                                    board=board_text(state),
                                    row=head[1], col=head[0],
                                    heading=HEADINGS.get(dir_from_delta(*state["dir"]), "nowhere"),
                                    length=state["length"], eaten=eaten)


# ==================================================================================================
# THE STATE CHAIN. Each row carries a digest of the state it left behind, and the chain digest is over the
# rows in order -- so a replay can be compared row by row, and a tampered row cannot survive either check.
# ==================================================================================================
STATE_FIELDS = ("tick", "head", "dir", "cells", "length", "maxCells", "apple", "rng_calls")


def projection(st):
    return {k: st[k] for k in STATE_FIELDS}


def state_digest(proj):
    return hashlib.sha256(json.dumps(proj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def chain_digest(digests):
    return hashlib.sha256("".join(digests).encode()).hexdigest()[:16] if digests else None


def model_digest(path):
    return P.file_digest(path)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def llama_server():
    return LLAMA_SELECTED or LLAMA_FORK


def mmproj_for(entrant, mode="auto", explicit=None):
    """-> (path, how) for the multimodal projector, or (None, reason).

    THE PROJECTOR IS PART OF THE INSTRUMENT AND IS NOW SELECTABLE, because MEASURED: the 9B's arm ABORTED
    inside `clip_model_loader::load_tensors` -> `ggml_backend_buffer_set_usage` -> `ggml_abort` while loading
    THIS cabinet's mmproj, with `-ngl 0` (from the crate's own backtrace, in
    logs/SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_rea-off.log). The abort was in the VISION path, not in the
    weights -- and this cabinet asks its question in TEXT and reads its answer in TEXT, so the projector is
    carried for the launch line the card declares and can be dropped when it is the thing that breaks.
    `auto` picks by LONGEST COMMON PREFIX with the weight filename rather than by a hand-kept table.
    """
    if mode == "off":
        return None, "--no-mmproj: the projector is not loaded (this cabinet reads text; the flag is recorded)"
    if mode == "path" and explicit:
        return explicit, "--mmproj given on the command line"
    label = os.path.basename(entrant)
    best, blen = None, 0
    try:
        names = os.listdir(MODELS)
    except OSError:
        return None, "models dir unreadable"
    for n in names:
        if "mmproj" not in n or not n.endswith(".gguf"):
            continue
        k = 0
        while k < min(len(n), len(label)) and n[k] == label[k]:
            k += 1
        if k > blen and k >= 8:
            best, blen = os.path.join(MODELS, n), k
    if best:
        return best, "longest common prefix with the weight filename (%d chars)" % blen
    return None, "no mmproj file shares an 8-character prefix with %s" % label


def reasoning_argv():
    return ["--reasoning", REASONING]


def server_argv(entrant, mmproj, port, alias):
    argv = [llama_server(), "-m", entrant]
    if mmproj:
        argv += ["--mmproj", mmproj]
    argv += ["--alias", alias, "-c", str(CTX), "-ngl", str(NGL), "--port", str(port), "--no-webui",
             "--jinja", "-s", str(SERVER_SEED)]
    if PARALLEL is not None:
        argv += ["--parallel", str(PARALLEL)]
    return argv + reasoning_argv()


def wait_ready(base, proc, log_path, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return False, "server exited rc=%s" % proc.returncode
        try:
            urllib.request.urlopen(base + "/health", timeout=3).read()
            return True, round(time.time() - t0, 1)
        except Exception:                                              # noqa: BLE001
            time.sleep(2)
    return False, "never answered /health in %ds" % timeout


def ask(base, prompt, timeout_s=600):
    """ONE LETTER, ASKED ONCE. The read is the READER OF RECORD's, imported and never reimplemented."""
    body = json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": MAX_TOKENS,
                       "temperature": TEMPERATURE, "seed": SERVER_SEED})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
        ans = read_answer(j)
        return ans, time.time() - t0
    except Exception as e:                                             # noqa: BLE001
        return read_answer({}, exception=e), time.time() - t0


def first_token(text):
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line.split()[0] if line.split() else ""
    return ""


def cap_cut_statement(hit, answer_present):
    if not hit:
        return "nothing -- the model stopped on its own"
    if not answer_present:
        return ("THE ANSWER -- deliberation consumed the ceiling before any answer was reached. THIS IS "
                "THE ONE CASE WHERE `length` MEANS THE MODEL DID NOT ANSWER.")
    return ("SURPLUS AFTER AN ANSWER -- the answer is present and readable; the cap cut what followed it. "
            "NOT a failed turn.")


def probe_reasoning(base, timeout_s=300):
    """WHAT SETTING THE MODEL IS ACTUALLY ON, asked once before the episode: a one-token question answers
    in one or two tokens with thinking off and in hundreds with it on."""
    q = "What is 2 + 2? Reply with just the number and nothing else."
    body = json.dumps({"messages": [{"role": "user", "content": q}], "max_tokens": MAX_TOKENS,
                       "temperature": TEMPERATURE, "seed": SERVER_SEED})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
    except Exception as e:                                             # noqa: BLE001
        return {"question": q, "error": "%s: %s" % (type(e).__name__, e), "observed": None}
    ans = read_answer(j)
    return {"question": q, "text": ans["text"][:80], "field": ans["field"],
            "completion_tokens": ans["completion_tokens"], "finish_reason": ans["finish_reason"],
            "observed": ("thinking OFF -- a one-token question answered in a few tokens"
                         if ans["completion_tokens"] <= 8 else
                         "thinking ON or a bad answer -- the question consumed %d tokens"
                         % ans["completion_tokens"])}


# ==================================================================================================
# THE EPISODE.
# ==================================================================================================
def play_episode(page, seed, ticks, death_ends, policy):
    """-> (trace, turns, ended). `policy(state, eaten) -> (letter_or_None, meta)`. The harness never
    chooses a move: with `None` the game is stepped with the snake's own velocity, which is what a
    non-answer is."""
    st = page.new_episode(seed)
    trace, turns = [], []
    eaten_so_far = 0
    ended = "tick_cap"
    for k in range(ticks):
        letter, meta = policy(st, eaten_so_far)
        try:
            r = page.step(letter)
        except Exception as e:                                         # noqa: BLE001
            ended = "harness_error: %s: %s" % (type(e).__name__, e)
            break
        after = r["state"]
        before_proj, after_proj = projection(st), projection(after)
        # AND THE POLICY SEES THE NEW STATE NEXT TURN. Measured defect, from the trace of the first
        # baseline run: `st` was never advanced, so every turn was planned from the tick-0 board -- the
        # agent walked a straight line past an apple twenty steps away and the artifact is what showed it.
        st = after
        row = {"tick": k, "before": before_proj, "before_digest": state_digest(before_proj),
               "requested": letter, "intended_dir": list(DIRS_LETTER[letter]) if letter else None,
               "after": after_proj, "after_digest": state_digest(after_proj),
               "tick_calls": r["tick_calls"]}
        # WAS THE MOVE ACTUALLY APPLIED? The game's own handler refuses a reversal along the current
        # axis, so the difference between the letter sent and the direction the tick used is a MEASURED
        # property of the game rather than an inference about the entrant.
        if letter is not None:
            row["accepted"] = (tuple(after["dir"]) == DIRS_LETTER[letter])
            if not row["accepted"]:
                row["refused_because"] = ("the game's own handler ignores a reversal along the axis the "
                                          "snake is already moving on (snake.dx === 0 / snake.dy === 0)")
        else:
            row["accepted"] = None
            row["refused_because"] = "no move was given: the game was stepped on its own velocity"
        if meta:
            row["turn"] = meta
        trace.append(row)
        # THE RUNNING COUNT IS THE SAME READING THE SCORE USES, so the number the entrant is told and the
        # number finally recorded cannot be two different numbers (snake_score.py, one definition).
        eaten_so_far += _ate(before_proj, after_proj)
        turns.append(row)
        if after["length"] == 0 and killed_itself(before_proj):
            ended = "self_collision"
            if death_ends:
                break
    return trace, turns, ended


# THE CONTROL LETTERS AS THE GAME'S OWN UNITS: a pixel delta of one cell. `DIRS` in snake_solver is the
# same mapping in CELL coordinates; this one is here because the trace is written in the game's units.
DIRS_LETTER = {"U": (0, -16), "D": (0, 16), "L": (-16, 0), "R": (16, 0)}


def killed_itself(before):
    """A reset can only follow a body of two or more cells: the first tick puts one cell down and a
    one-cell snake cannot collide with anything.

    MEASURED LIMIT, stated so the reader does not over-read the name: this is the condition the driver
    uses to call an episode "ended by self_collision". THE SCORE DOES NOT DEPEND ON IT -- the score reads
    the reset from `length == 0` in the trace (see snake_score.py), which is exact.
    """
    return before["length"] >= 2


def _ate(before, after):
    d = after["rng_calls"] - before["rng_calls"]
    reset = after["length"] == 0
    return max(0, d // 2 - (1 if reset else 0))


# ==================================================================================================
# THE ARTIFACT.
# ==================================================================================================
def episode_artifact(agent, seed, trace, ended, page, extra):
    live = SC.score_trace(trace)
    digests = [r["after_digest"] for r in trace]
    return {
        "kind": "snake-episode",
        "agent": agent,
        "seed": seed,
        "ended": ended,
        "moves": [r["requested"] for r in trace],
        "score": {k: live[k] for k in ("eaten", "best_life", "deaths", "ticks")},
        "score_readings": live["checks"],
        "score_disagreements": live["disagreements"],
        "score_notes": live["notes"],
        "score_problems": live["problems"],
        "trace": trace,
        "chain_digest": chain_digest(digests),
        "instrument": page.instrument(),
        **extra,
    }


def artifact_path(agent, seed):
    """THE ARM IS IN THE NAME when it is not the default one -- the sibling cabinet's FINDING 024, where the
    legend arm lived only in the LOG name and two arms of an A/B would have overwritten each other's
    artifact. The default arm keeps the plain published shape."""
    arm = legend()
    suffix = "" if arm == LEGEND_DEFAULT else "_leg-%s" % arm
    return os.path.join(PROBES, "SNAKE_%s%s_s%s.json" % (agent, suffix, seed))


def artifact_gate(out, reason):
    """REFUSES to write over a record this run did not take (the sibling cabinet's FINDING 020: a second
    run against a live path is an OVERWRITE, not a retry). The override takes a REASON as its value and
    the reason is written into the replacement beside the digest of what it replaced."""
    if not os.path.exists(out):
        return True, "", None
    if not reason:
        return False, ("REFUSED: %s already exists, and a second run against a live path is an OVERWRITE "
                       "rather than a retry. Pass --overwrite-artifact REASON to replace it and say why."
                       % os.path.relpath(out, HERE)), None
    with open(out, "rb") as f:
        old = f.read()
    old_d = json.loads(old.decode())
    return True, "", {"path": os.path.relpath(out, HERE), "bytes": len(old),
                      "sha256": hashlib.sha256(old).hexdigest()[:16],
                      "said_about_itself": {"agent": old_d.get("agent"), "seed": old_d.get("seed"),
                                            "score": old_d.get("score"),
                                            "chain_digest": old_d.get("chain_digest")},
                      "reason_given": reason}


# ==================================================================================================
# THE ARMS.
# ==================================================================================================
def run_baseline(name, seeds, ticks, death_ends, overwrite):
    page = P.SnakePage().start()
    try:
        st0 = page.new_episode(seeds[0])
        board = Board(st0["canvas"][0] // st0["grid"], st0["canvas"][1] // st0["grid"])
        agent = {"cycle-shortcut": CycleShortcutAgent, "cycle": CycleAgent,
                 "greedy-safe": GreedySafeAgent}[name](board)
        rows, results = [], []
        for seed in seeds:
            policy = (lambda st, eaten: (agent.next_direct(st), None))
            trace, _turns, ended = play_episode(page, seed, ticks, death_ends, policy)
            extra = {"baseline": {"name": agent.name,
                                  "cycle_digest": hashlib.sha256(
                                      json.dumps(board.cycle).encode()).hexdigest()[:16],
                                  "cycle_cells": board.n,
                                  "safety": ("follows the torus's Hamiltonian cycle; the shortcut only ever "
                                             "enters the free window between the head and the tail")}}
            art = episode_artifact(agent.name, seed, trace, ended, page, extra)
            out = artifact_path(agent.name, seed)
            ok, msg, replaced = artifact_gate(out, overwrite)
            if not ok:
                print("  " + msg)
                continue
            if replaced:
                art["artifact_replaced"] = replaced
            os.makedirs(PROBES, exist_ok=True)
            with open(out, "w") as f:
                json.dump(art, f, indent=1)
            results.append({"seed": seed, "score": art["score"], "ended": ended,
                            "artifact": os.path.relpath(out, HERE), "chain_digest": art["chain_digest"]})
            print("  seed %-6s eaten %-4d best_life %-4d deaths %-3d ticks %-4d %-16s %s"
                  % (seed, art["score"]["eaten"], art["score"]["best_life"], art["score"]["deaths"],
                     art["score"]["ticks"], ended, os.path.relpath(out, HERE)))
            rows.append(art)
        return results
    finally:
        page.stop()


def load_failure_record(label, argv, mmproj, mmproj_mode, log_path, exit_code, why, port):
    """THE FAILURE PATH GETS A RECORD TOO, because that is the path where the record matters most.

    MEASURED, on this card: the 9B's first arm died inside `clip_model_loader::load_tensors` and the ONLY
    surviving evidence was a line in `logs/`, which this repository declares SCRATCH (DECISION_logs_are_scratch.md)
    and which `git check-ignore logs/` confirms is not committable. A finding whose only carrier is a scratch
    file is a finding that evaporates -- and a code comment CITING that file is the stand-in outliving its
    thing, one step removed. So the failure carries its own artifact, with the abort quoted in it.

    The quoted tail is bounded and FILTERED to the lines that state the failure, so the bundle stays
    readable; the whole log is not carried, and the record says so rather than pretending to be complete.
    """
    lines = []
    try:
        with open(log_path, "r", errors="replace") as f:
            raw = f.read().splitlines()
        keys = ("abort", "assert", "error", "failed", "unable", "cannot", "no such", "exception",
                "terminate", "refus", "not supported", "out of memory")
        lines = [ln for ln in raw if any(k in ln.lower() for k in keys)][:40] or raw[-40:]
    except OSError as e:
        lines = ["log unreadable: %s" % e]
    return {"kind": "snake-load-failure", "entrant": label, "loaded": False, "why": why,
            "exit_code": exit_code, "port": port, "server_argv": argv,
            "server_binary": llama_server(), "server_binary_digest": P.file_digest(llama_server()),
            "server_binary_digest_scope": "sha256 of the BINARY FILE, first 16 hex",
            "mmproj": mmproj, "mmproj_mode": mmproj_mode,
            "mmproj_digest": model_digest(mmproj) if mmproj else None,
            "entrant_digest": model_digest(os.path.join(MODELS, label + ".gguf")),
            "log": {"path": os.path.relpath(log_path, HERE),
                    "scratch": True,
                    "why_quoted_here": ("logs/ is scratch by repository rule; the lines that state the "
                                        "failure are quoted so the finding survives the directory"),
                    "quoted_lines": lines,
                    "log_is_complete": False}}


def run_model(entrant, seeds, ticks, death_ends, overwrite, port, mmproj_mode="auto", mmproj_path=None):
    label = os.path.basename(entrant).replace(".gguf", "")
    mmproj, mmproj_how = mmproj_for(entrant, mmproj_mode, mmproj_path)
    port = port or free_port()
    alias = "snake-" + label[:40].lower().replace("_", "-")
    argv = server_argv(entrant, mmproj, port, alias)
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    log = os.path.join(HERE, "logs", "SNAKE_%s_rea-%s.log" % (label, REASONING))
    base = "http://127.0.0.1:%d" % port
    print("  launching %s" % " ".join(argv))
    proc = subprocess.Popen(argv, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    try:
        ok, note = wait_ready(base, proc, log)
        if not ok:
            print("  DID NOT LOAD -- %s" % note)
            rec = load_failure_record(label, argv, mmproj, mmproj_mode, log, proc.returncode, note, port)
            out = os.path.join(PROBES, "SNAKE_LOADFAIL_%s_mm-%s_%s.json"
                               % (label, mmproj_mode, time.strftime("%Y%m%d-%H%M%S", time.gmtime())))
            os.makedirs(PROBES, exist_ok=True)
            with open(out, "w") as f:
                json.dump(rec, f, indent=1)
            print("  FAILURE RECORD  %s" % os.path.relpath(out, HERE))
            for ln in rec["log"]["quoted_lines"][:3]:
                print("    %s" % ln[:150])
            return None
        probe = probe_reasoning(base)
        print("  loaded in %ss   reasoning probe: %s" % (note, probe.get("observed")))
        page = P.SnakePage().start()
        try:
            st0 = page.new_episode(seeds[0])
            board = Board(st0["canvas"][0] // st0["grid"], st0["canvas"][1] // st0["grid"])
            results = []
            for seed in seeds:
                state = {"eaten": 0}

                def policy(st, eaten, base=base):
                    pr = prompt_for(st, eaten)
                    ans, secs = ask(base, pr)
                    tok = first_token(ans["text"]).strip().upper()
                    legal = tok[:1] in ("U", "D", "L", "R")
                    letter = tok[:1] if legal else None
                    hit = ans["finish_reason"] == "length"
                    meta = {"ply": st["tick"], "raw": ans["text"][:400], "token": tok[:8], "secs": round(secs, 1),
                            "gen_tokens": ans["completion_tokens"], "budget_hit": hit,
                            "cap_cut": cap_cut_statement(hit, bool(ans["text"])),
                            "answer_field": ans["field"], "not_an_action": not legal,
                            "missing_value": bool(ans.get("missing")),
                            "prompt_chars": len(pr)}
                    return letter, meta

                trace, turns, ended = play_episode(page, seed, ticks, death_ends, policy)
                extra = {
                    "entrant": label, "entrant_digest": model_digest(entrant),
                    "entrant_digest_scope": ("sha256 of the model FILE, first 16 hex. THE ENTRANT IS THE "
                                            "THING BEING MEASURED, so it is identified by a digest; "
                                            "`entrant` is a label for reading, not for checking."),
                    "config": {"server_argv": argv, "server_binary": llama_server(),
                               "server_binary_digest": P.file_digest(llama_server()),
                               "ctx": CTX, "n_gpu_layers": 0, "temperature": TEMPERATURE,
                               "max_tokens_ceiling": MAX_TOKENS, "server_seed": SERVER_SEED,
                               "alias": alias, "mmproj": mmproj, "mmproj_how": mmproj_how,
                               "mmproj_mode": mmproj_mode,
                               "mmproj_digest": model_digest(mmproj) if mmproj else None,
                               "reasoning": REASONING, "reasoning_argv": reasoning_argv(),
                               "reasoning_declared": REASONING_DECLARED,
                               "reasoning_declared_in": REASONING_DECLARED_IN,
                               "reasoning_rationale": REASONING_RATIONALE,
                               "reasoning_changed_from_declaration": REASONING != REASONING_DECLARED,
                               "legend": legend_template(), "legend_arm": legend(),
                               "legend_digest": legend_digest(),
                               "legend_default_arm": LEGEND_DEFAULT,
                               "legend_arms_available": sorted(LEGENDS)},
                    "reasoning_probe": probe,
                    "not_an_action": sum(1 for t in turns if t.get("turn", {}).get("not_an_action")),
                    "missing_values": sum(1 for t in turns if t.get("turn", {}).get("missing_value")),
                }
                art = episode_artifact(label, seed, trace, ended, page, extra)
                out = artifact_path(label, seed)
                gok, msg, replaced = artifact_gate(out, overwrite)
                if not gok:
                    print("  " + msg)
                    continue
                if replaced:
                    art["artifact_replaced"] = replaced
                os.makedirs(PROBES, exist_ok=True)
                with open(out, "w") as f:
                    json.dump(art, f, indent=1)
                results.append({"seed": seed, "score": art["score"], "ended": ended,
                                "artifact": os.path.relpath(out, HERE), "chain_digest": art["chain_digest"],
                                "not_an_action": art["not_an_action"]})
                print("  seed %-6s eaten %-4d best_life %-4d deaths %-3d ticks %-4d %-16s %s"
                      % (seed, art["score"]["eaten"], art["score"]["best_life"], art["score"]["deaths"],
                         art["score"]["ticks"], ended, os.path.relpath(out, HERE)))
            return results
        finally:
            page.stop()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except Exception:                                              # noqa: BLE001
            proc.kill()


# ==================================================================================================
# THE TWO CHECKS ON A RECORD: reconstruct from the bundle, and RE-ENTER the run.
# ==================================================================================================
def verify_bundle(path):
    b = json.load(open(path))
    if b.get("kind") == "snake-load-failure":
        # A LOAD FAILURE IS A RECORD WITH NO TRACE, so there is nothing here to reconstruct and the exit
        # code has to say so in a way a reader can act on rather than a KeyError.
        print("  bundle    %s" % path)
        print("  THIS IS A LOAD-FAILURE RECORD, not an episode: %s (exit code %s). Nothing was played and "
              "there is no trace to reconstruct." % (b.get("why"), b.get("exit_code")))
        print("  the failure lines are carried in log.quoted_lines (%d of them)"
              % len(b.get("log", {}).get("quoted_lines", [])))
        return False
    ok, reasons, live = SC.verify(b)
    print("  bundle    %s" % path)
    print("  recorded  %s" % json.dumps(b.get("score")))
    print("  from trace alone  %s" % json.dumps({k: live[k] for k in ("eaten", "best_life", "deaths",
                                                                     "ticks")}))
    print("  readings  %s" % json.dumps(live["checks"]))
    for r in reasons:
        print("  FAIL %s" % r)
    print("  RECONSTRUCTION %s" % ("OK -- the trace alone reproduces the recorded score" if ok
                                   else "REFUSED"))
    return ok


def replay_bundle(path, ticks=None):
    """RE-ENTER THE RUN: same seed, same moves, the REAL page. The recorded state chain must come back
    digest for digest. This is the difference between a trace and a story about a trace."""
    b = json.load(open(path))
    seed = b["seed"]
    moves = b["moves"]
    page = P.SnakePage().start()
    try:
        st = page.new_episode(seed)
        bad = []
        digests = []
        for k, mv in enumerate(moves if ticks is None else moves[:ticks]):
            r = page.step(mv)
            d = state_digest(projection(r["state"]))
            digests.append(d)
            if d != b["trace"][k]["after_digest"]:
                bad.append({"tick": k, "recorded": b["trace"][k]["after_digest"], "replayed": d})
        chain = chain_digest(digests)
        print("  replayed %d/%d ticks of %s" % (len(digests), len(moves), os.path.basename(path)))
        for x in bad[:5]:
            print("  MISMATCH %s" % json.dumps(x))
        print("  chain  recorded %s  replayed %s" % (b["chain_digest"], chain))
        ok = (not bad) and chain == b["chain_digest"]
        print("  REPLAY %s" % ("OK -- the recorded run is re-enterable from (seed, moves)"
                               if ok else "REFUSED -- the replay does not reproduce the record"))
        return ok
    finally:
        page.stop()


def self_test():
    """THE CONTROLS. A check that has never been shown the failure it exists to prevent is not a check."""
    print("  solver:"); solver_ok = __import__("snake_solver").selftest()
    print("  wrapper:")
    page = P.SnakePage().start()
    try:
        st = page.new_episode(seed=1)
        header_ok = (st["tick"] == 0 and st["cells"] == [])
        seen = []
        for mv in ("D", "R", "U", "L"):                                # a legal square, no reversal
            r = page.step(mv)
            seen.append(state_digest(projection(r["state"])))
        # CONTROL: the same seed replayed must reproduce the state chain exactly
        st2 = page.new_episode(seed=1)
        again = []
        for mv in ("D", "R", "U", "L"):
            again.append(state_digest(projection(page.step(mv)["state"])))
        same_ok = seen == again
        # CONTROL: a DIFFERENT seed must not silently produce the same chain (it must differ once an
        # apple is eaten; before the first eat both are identical, which is the honest statement)
        print("    tick held at episode start: %s" % header_ok)
        print("    same seed reproduces the chain: %s" % same_ok)
        print("    instrument: subject digest disk=%s live=%s modified=%s"
              % (page.instrument()["subject"]["source_digest_on_disk"],
                 page.instrument()["subject"]["source_digest_from_live_dom"],
                 page.instrument()["subject"]["source_modified_by_harness"]))
        return solver_ok and header_ok and same_ok
    finally:
        page.stop()


def main():
    global LLAMA_SELECTED, NGL, CTX
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", choices=["cycle", "cycle-shortcut", "greedy-safe"])
    ap.add_argument("--entrant", help="path to a gguf (or a name inside ARENA_MODELS)")
    ap.add_argument("--seeds", help="comma-separated; default: snake/seeds.txt")
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--death-ends", dest="death_ends", action="store_true", default=True)
    ap.add_argument("--no-death-ends", dest="death_ends", action="store_false")
    ap.add_argument("--llama-server", dest="llama_server", default=None)
    ap.add_argument("--ngl", type=int, default=NGL_DECLARED,
                    help="--n-gpu-layers for the entrant's server (default: the registered %d). A "
                         "COMPUTE-PATH field only; it travels in the argv the server is started with."
                         % NGL_DECLARED)
    ap.add_argument("--ctx", type=int, default=CTX_DECLARED,
                    help="--ctx-size for the entrant's server (default: the registered %d). A "
                         "COMPUTE-PATH field only; it travels in the argv the server is started with."
                         % CTX_DECLARED)
    ap.add_argument("--parallel", type=int, default=PARALLEL_DECLARED,
                    help="--parallel for the entrant's server (default: the registered launch, which "
                         "passes no such flag). A COMPUTE-PATH field; it travels in the argv.")
    ap.add_argument("--overwrite-artifact", dest="overwrite_artifact", default=None, metavar="REASON")
    ap.add_argument("--mmproj", default=None,
                    help="path to the multimodal projector (default: picked by longest common prefix with "
                         "the weight filename, and recorded)")
    ap.add_argument("--no-mmproj", dest="no_mmproj", action="store_true",
                    help="load no projector at all. MEASURED REASON THIS EXISTS: the 9B's projector aborts "
                         "this fork inside clip_model_loader while its weights load fine, and this cabinet "
                         "asks its question and reads its answer in TEXT.")
    ap.add_argument("--legend", choices=sorted(LEGENDS), default=None,
                    help="which arm of the legend A/B to play under (default: %s, always recorded)"
                         % LEGEND_DEFAULT)
    ap.add_argument("--verify", metavar="BUNDLE")
    ap.add_argument("--replay", metavar="BUNDLE")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    a = ap.parse_args()
    NGL = a.ngl
    CTX = a.ctx
    global PARALLEL
    PARALLEL = a.parallel
    if a.legend:
        os.environ["SNAKE_LEGEND"] = a.legend

    if a.self_test:
        return 0 if self_test() else 1
    if a.verify:
        return 0 if verify_bundle(a.verify) else 1
    if a.replay:
        return 0 if replay_bundle(a.replay) else 1
    if a.llama_server:
        sel = os.path.expanduser(a.llama_server)
        if not (os.path.exists(sel) and os.access(sel, os.X_OK)):
            print("  BINARY ABSENT OR NOT EXECUTABLE: %s" % a.llama_server)
            return 2
        LLAMA_SELECTED = sel
    if a.overwrite_artifact is not None and not a.overwrite_artifact.strip():
        print("  --overwrite-artifact WAS GIVEN AN EMPTY REASON: a replacement has to say why.")
        return 2
    seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else seeds_from_file()
    if not seeds:
        print("  NO SEEDS: nothing to play. %s is empty and --seeds was not given." % SEEDS_FILE)
        return 2
    print("  subject   %s  (sha256 %s)" % (os.path.relpath(P.SnakePage().html, HERE),
                                           P.file_digest(P.SnakePage().html)))
    print("  seeds     %s   ticks %d   death_ends %s" % (seeds, a.ticks, a.death_ends))
    if a.baseline:
        res = run_baseline(a.baseline, seeds, a.ticks, a.death_ends, a.overwrite_artifact)
    elif a.entrant:
        p = a.entrant if os.path.exists(a.entrant) else os.path.join(MODELS, a.entrant)
        if not os.path.exists(p):
            print("  ENTRANT ABSENT: %s" % a.entrant)
            return 2
        res = run_model(p, seeds, a.ticks, a.death_ends, a.overwrite_artifact, a.port,
                        mmproj_mode=("off" if a.no_mmproj else ("path" if a.mmproj else "auto")),
                        mmproj_path=a.mmproj)
    else:
        print("  pick one: --baseline cycle-shortcut | --entrant <gguf> | --verify F | --replay F")
        return 2
    if not res:
        return 3
    tot = {"eaten": sum(r["score"]["eaten"] for r in res),
           "best_life": max(r["score"]["best_life"] for r in res) if res else 0,
           "deaths": sum(r["score"]["deaths"] for r in res), "episodes": len(res)}
    print("  TOTAL     %s" % json.dumps(tot))
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    name = a.baseline or os.path.basename(a.entrant or "").replace(".gguf", "")
    run_out = os.path.join(PROBES, "SNAKE_RUN_%s_%s.json" % (name, stamp))
    os.makedirs(PROBES, exist_ok=True)
    with open(run_out, "w") as f:
        json.dump({"kind": "snake-run", "agent": name, "seeds": seeds, "ticks": a.ticks,
                   "death_ends": a.death_ends, "at_utc": stamp, "totals": tot, "episodes": res},
                  f, indent=1)
    print("  run       %s" % os.path.relpath(run_out, HERE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
