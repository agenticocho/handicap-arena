#!/usr/bin/env python3
"""SOKOBAN -- the entrant driver. One model, one level, one letter at a time.

BUILT TO PREREG_sokoban.md. The simulator decided everything; this only asks and records.

THE MENU LESSON, APPLIED BY DISTINCTION RATHER THAN BY HABIT. Chess failed because the prompt listed the
LEGAL MOVES -- the answer set -- so the entrant chose from a menu instead of deriving candidates. Here the
prompt names the four CONTROLS: U D L R. That is the INTERFACE, the way a controller has four buttons:

    NAMING THE FOUR CONTROLS IS THE INTERFACE.        LISTING THE TWENTY LEGAL MOVES WAS THE ANSWER.
    A control scheme is part of the machine.          A move list is the work.

No move is named, no direction is suggested, and the illegal push is rejected by the simulator rather than
warned about in the prompt -- so the entrant learns about walls the way a player does.

AND `RESIGN` IS OFFERED, because the give-up is a SIGNAL and not noise: a model that says it is beaten when
it IS beaten, and one that says it when it is not, are the faculty this cabinet measures. Premature
collapse is provable without a solver wherever the level's solution is verified.

    python3 sokoban_run.py --entrant <gguf> --level levels/01_one_push.txt --cap 40
    python3 sokoban_run.py --self-test
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sokoban as S                                                     # noqa: E402

LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")

# THE ENTRANT IS THE THING BEING MEASURED, AND A NAME IS NOT AN IDENTITY.
#
# The record digested the INSTRUMENT (simulator_digest, legend_digest) and named the ENTRANT by a filename with
# its extension stripped -- so two people holding the same weights under different filenames were
# indistinguishable, and two different QUANTIZATIONS under one name were equally indistinguishable. Q4_K_M and
# IQ2_XXS would have looked identical. THAT IS BACKWARDS: the entrant is the subject of the measurement.
#
# The name STAYS, beside the digest, as a LABEL -- a label is for reading, an identity is for checking.
_DIGEST_CACHE = {}


def model_digest(path):
    """sha256 of the model FILE, first 16 hex, cached per path. Streamed, so a multi-GB GGUF is fine."""
    if path not in _DIGEST_CACHE:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            _DIGEST_CACHE[path] = h.hexdigest()[:16]
        except OSError:
            # AN UNREADABLE MODEL GETS null AND A REASON, NEVER A FABRICATED DIGEST. A made-up hash is worse
            # than a missing one because it verifies.
            _DIGEST_CACHE[path] = None
    return _DIGEST_CACHE[path]


def cap_cut_statement(hit, answer_present):
    """WHAT THE CAP CUT -- because `finish_reason=length` IS A STATEMENT ABOUT THE HARNESS, NOT THE MODEL.

    The ceiling sweep measured this directly: the same task at 1200, 2048 and 4096 tokens returned
    `finish_reason=length` at EVERY size AND THE ANSWER WAS CORRECT AT EVERY SIZE. So `length` on its own says
    nothing about whether a model answered -- it says WE STOPPED IT. A verdict carrying it must therefore say
    WHAT was cut, or it invites the reader to infer a failure that may not exist.
    """
    if not hit:
        return "nothing -- the model stopped on its own"
    if not answer_present:
        return ("THE ANSWER -- deliberation consumed the ceiling before any answer was reached. "
                "THIS IS THE ONE CASE WHERE `length` MEANS THE MODEL DID NOT ANSWER.")
    return ("SURPLUS AFTER AN ANSWER -- the answer is present and readable; the cap cut what followed it. "
            "NOT a failed turn.")

MAX_TOKENS = 64                     # ONE LETTER NEEDS A FEW TOKENS, and a cap that cannot be deliberated
                                    # into is the constraint this game was chosen for.
                                    # THE CEILING, not the count used -- both travel in the record.

# ==================================================================================================
# THE REASONING SETTING IS DECLARED, PER CABINET, WITH A REASON -- AND AN UNDECLARED RUN IS REFUSED.
#
# THE CHAIR'S REFINEMENT, AND IT CORRECTS A GENERALISATION I HAD ALREADY CODED: "off" is NOT the right value
# in general. It is the right value FOR THIS CABINET, because of what this cabinet asks for.
#
#   thinking OFF   held a short-answer format perfectly (two turns, four rules carried across, zero padding)
#   thinking ON    appears to IMPROVE the same model's ARITHMETIC
#
# So the rule is narrower and it is an INSTRUMENT CHOICE:
#
#   ONE LETTER or ONE WORD answers        -> off. Deliberation occupies the answer slot and the ceiling eats
#                                            it. Measured: 2314 tokens, no move.
#   MULTI-STEP ARITHMETIC, exact sums     -> on, probably. That is where it helps. (DARTS, not this cabinet.)
#
# AND IT MUST BE DECLARED, NOT DEFAULTED: AN UNRECORDED DEFAULT IS INDISTINGUISHABLE FROM A DECISION, AND
# ONLY ONE OF THOSE IS EVIDENCE. My first version of this block DID exactly that -- it read an env var and
# fell back to "off". That fallback was a decision nobody made, wearing a default's clothes.
#
# THE FIRST VERSION OF *THIS* BLOCK WAS THEREFORE THE SAME DEFECT AS THE ONE IT WAS WRITTEN TO FIX.
# ==================================================================================================
REASONING_DECLARED = "off"
REASONING_DECLARED_IN = "PREREG_sokoban.md"
REASONING_RATIONALE = (
    "Sokoban's answer is ONE LETTER. A thinking model puts deliberation where the answer belongs and the "
    "ceiling eats it -- measured on the same weights: 2314 tokens and no commitment. This cabinet is the "
    "one-letter case, so the setting is off. MISSILE COMMAND is the same case (one integer). DARTS is the "
    "opposite (exact checkout arithmetic), and a harness that proves the SHAPE should be able to prove it at "
    "either setting -- so it takes this as a PARAMETER rather than a constant."
)

# THE OVERRIDE IS FOR EXPERIMENTS, NOT FOR DEFAULTS. It is the instrument-check path's argument, so the
# harness can prove the shape at either setting -- and when it is used, THE RECORD SAYS SO.
REASONING_OVERRIDE = os.environ.get("SOKOBAN_REASONING_TEST_ARM", "").strip().lower() or None
if REASONING_OVERRIDE is not None and REASONING_OVERRIDE not in ("on", "off", "auto"):
    raise SystemExit(f"SOKOBAN_REASONING_TEST_ARM must be on|off|auto, got {REASONING_OVERRIDE!r}")
REASONING = REASONING_OVERRIDE or REASONING_DECLARED


def reasoning_source():
    return "override (experiment arm)" if REASONING_OVERRIDE else f"declared in {REASONING_DECLARED_IN}"


def reasoning_changed_from_declaration():
    """A CABINET THAT CHANGES THIS BETWEEN RUNS IS A DIFFERENT INSTRUMENT -- like a depth series or a
    Context/Hash pair. The record states the change rather than hiding it inside a flag."""
    return REASONING != REASONING_DECLARED


def reasoning_argv():
    """THE FLAG AS IT IS ACTUALLY PASSED, so the record carries the argv and not a summary of it."""
    return ["--reasoning", REASONING]


def server_argv(entrant, ctx, port):
    """THE WHOLE LAUNCH, in one place, so what is recorded is what was run."""
    return ([LLAMA, "-m", entrant, "-c", str(ctx), "-ngl", "0", "--port", str(port), "--no-webui"]
            + reasoning_argv())


# ==================================================================================================
# THE CONTROLLED A/B. Both legends are kept because the PREDICTION CANNOT BE TESTED WITHOUT BOTH.
#
# The re-run gave granite-3.3-2b a clean result (`U`, 40 blocked, not_an_action 0) and gave LFM2-350M
# UNCHANGED (40 not_an_action). So granite IMPROVED -- and improving is not the same as having been
# disadvantaged, because THERE WAS NO granite RUN UNDER THE OLD LEGEND. A result with no control is an
# observation, not a difference.
#
# SO THE OLD LEGEND IS REINTRODUCED DELIBERATELY, as a CONTROL. Reintroducing a known defect is legitimate
# exactly here and nowhere else: the defect is MEASURED, its size is KNOWN, and the only question left is
# whether THIS entrant was affected by it. That is a control's job.
#
# AND IT IS VERBATIM. A paraphrased control is not a control -- if the old prompt were tidied while being
# restored, the A/B would measure the tidying.
#
# Selection is by SOKOBAN_LEGEND=old|new, read at CALL TIME so one process can do both.
# ==================================================================================================
PROMPT_OLD = (
    "You are playing Sokoban. One crate per target; a crate can be PUSHED but never pulled, so a "
    "wrong push can end the level permanently.\n\n"
    "Board:\n"
    "# wall   . target   $ crate   @ you   * crate on target   + you on target\n\n"
    "{board}\n\n"
    "Moves so far: {recent}\n\n"
    "FIRST LINE: your next move as ONE letter and nothing else.\n"
    "  U = up    D = down    L = left    R = right\n"
    "If you judge the level unwinnable from here, the first line is exactly: RESIGN\n"
    "AFTER the first line you may explain your reasoning if you wish."
)

PROMPT_NEW = (
    "You are playing Sokoban. The goal is to push every crate onto a target. A crate can be pushed "
    "but never pulled, so one wrong push can end the level permanently.\n\n"
    "The board below uses these symbols. A hash mark is a wall. A dot is a target. A dollar sign is "
    "a crate. An at sign is you. A star is a crate that is already sitting on a target, and a plus "
    "is you standing on a target.\n\n"
    "{board}\n\n"
    "The moves you have already made are: {recent}\n\n"
    "Answer with a single letter. Use U to move up, D to move down, L to move left, or R to move "
    "right. If you judge the level unwinnable from here, answer with the single word RESIGN. You may "
    "add an explanation after your answer, and it will be ignored."
)

LEGEND_DIGESTS = {}


def legend():
    """Read at CALL TIME, so a single process can run both arms of the A/B."""
    return os.environ.get("SOKOBAN_LEGEND", "new").strip().lower()


def prompt_for(board, history):
    """THE SCREEN, not the answers -- and NOT A FORM in the `new` arm.

    INSTRUMENT CHANGE, PRE-REGISTERED BEFORE THE RE-RUN. The first version's legend was a line of
    key-value PAIRS:

        "# wall   . target   $ crate   @ you   * crate on target   + you on target"
        "FIRST LINE: your next move as ONE letter and nothing else."
        "  U = up    D = down    L = left    R = right"

    and the measured consequence was that an entrant FILLED IT IN. It emitted
        {"wall": "", "first_line": "U = up", "second_line": "D = down", ...}
    -- it keyed on `wall`, `crate` and `FIRST LINE` and treated the prompt as a SCHEMA. Forty commands,
    zero moves, every turn capped.

    A MODEL THAT TRANSCRIBES THE LEGEND AS A SCHEMA IS NOT FAILING TO PLAY SOKOBAN. IT IS PLAYING A GAME
    CALLED FILL IN THE FORM, AND PLAYING IT CORRECTLY. So the symbols are described in PROSE SENTENCES
    rather than pairs, and every pseudo-field LABEL is gone -- `FIRST LINE:` and `U = up` are exactly the
    tokens the model echoed as keys.

    THE PREDICTION, RECORDED IN ADVANCE: a legend that does not look like a schema should move
    `not_an_action` DOWN. IF IT DOES NOT MOVE, THE SCHEMA-FILLING EXPLANATION IS WRONG and the echo has
    another cause -- and the A/B is what distinguishes a repaired instrument from a luckier sample.
    """
    recent = "".join(history[-12:]) if history else "none yet"
    tpl = PROMPT_OLD if legend() == "old" else PROMPT_NEW
    return tpl.replace("{board}", board).replace("{recent}", recent)


def legend_digest():
    """THE ARM A RECORD WAS TAKEN UNDER, carried with the record.

    Without this a reader cannot tell the two arms apart in the artifacts, and a comparison between
    them would be a comparison between two files whose difference is invisible.
    """
    import hashlib
    tpl = PROMPT_OLD if legend() == "old" else PROMPT_NEW
    return hashlib.sha256(tpl.encode()).hexdigest()[:16]


def ask(base, board, history, timeout_s=300):
    body = json.dumps({"messages": [{"role": "user", "content": prompt_for(board, history)}],
                       "max_tokens": MAX_TOKENS, "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
        dt = time.time() - t0
        msg = ((j.get("choices") or [{}])[0].get("message") or {})
        txt = (msg.get("content") or "").strip()
        source = "content"
        if not txt and (msg.get("reasoning_content") or "").strip():
            # THE SECOND FIELD, AND THIS IS A TRAP I NEARLY WALKED INTO.
            #
            # A reasoning model leaves `content` empty and puts its deliberation in `reasoning_content`.
            # Falling back to it is right WHEN THE DELIBERATION CONTAINS THE ANSWER. IT IS WRONG WHEN THE
            # TURN WAS CUT OFF AT THE CEILING, because then the first token of the deliberation is NOT an
            # answer -- it is the beginning of a sentence that never finished. THE ORNITH CASE EXACTLY:
            # 2314 tokens of deliberation, no move. Reading that fallback as a token would score a
            # TRUNCATION ARTIFACT as a legal action.
            #
            # So the fallback is kept -- it is the only way a thinking model's answer is ever read -- but it
            # TRAVELS WITH ITS PROVENANCE, and a capped fallback is reported as a MISSING VALUE rather than
            # mined for a token.
            txt = (msg.get("reasoning_content") or "").strip()
            source = "reasoning_content"
        nt = (j.get("usage") or {}).get("completion_tokens", 0)
        hit = (j.get("choices") or [{}])[0].get("finish_reason") == "length"
        # THE HARNESS MADE THIS EMPTY: capped, with only deliberation behind it. NOT an answer.
        if source == "reasoning_content" and hit:
            return "", dt, nt, True, "capped-deliberation-missing-value"
        return txt, dt, nt, hit, source
    except Exception as e:                                              # noqa: BLE001
        return "", time.time() - t0, 0, False, f"error:{type(e).__name__}"


def first_token(text):
    """THE ANSWER IS AT THE HEAD -- the first line, and one token from it. Nothing is mined from prose."""
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line.split()[0] if line.split() else ""
    return ""


def probe_reasoning(base, timeout_s=180):
    """ASK THE MODEL ONCE, BRIEFLY, BEFORE THE FIELD -- two seconds, and it would have caught this a week ago.

    A model with thinking OFF answers a one-token question in one or two tokens. A model with thinking ON
    answers it in hundreds. That is the whole test.

    AND IT RECORDS WHAT HAPPENED, NOT WHAT WAS ASKED FOR. The flag says which setting was requested; the
    probe says which one the model is actually running under. WHEN THOSE TWO DISAGREE, THE DISAGREEMENT IS
    THE FINDING -- a config field nobody measured is the same class as a legend nobody read.
    """
    q = "What is 2 + 2? Reply with just the number and nothing else."
    body = json.dumps({"messages": [{"role": "user", "content": q}], "max_tokens": MAX_TOKENS,
                       "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
    except Exception as e:                                              # noqa: BLE001
        return {"question": q, "error": f"{type(e).__name__}: {e}", "observed": None}
    ch = (j.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    txt = (msg.get("content") or "").strip()
    think = (msg.get("reasoning_content") or "").strip()
    ctok = (j.get("usage") or {}).get("completion_tokens", 0)
    # WHAT THE PROBE ACTUALLY MEASURES, NAMED PRECISELY, BECAUSE IT CANNOT SEE WHY.
    #
    # The threshold is on ANSWER LENGTH. From that it INFERS a reasoning mode -- and that inference can be
    # wrong. MEASURED: LFM2-350M-Extract answers the one-token question in 33 tokens whose content is
    # `{"answer": "2 + 2", "answer": "2 + 2", ...}` -- AN EXTRACTION MODEL ECHOING THE QUESTION AS JSON,
    # not deliberating. The old field called that `observed: "on"`, which is a FALSE STATEMENT ABOUT THE
    # MODEL made out of a TRUE MEASUREMENT of its output.
    #
    # So length and inference are now TWO FIELDS. The measurement is stated; the inference is labelled as an
    # inference; and a reader can see which one the disagreement is about.
    shape = "short" if ctok <= 8 else "long"
    observed = "off" if ctok <= 8 else "on"
    return {"question": q, "answer": txt[:60], "answer_from_reasoning_field": bool(think and not txt),
            "completion_tokens": ctok, "finish_reason": ch.get("finish_reason"),
            # THE MEASUREMENT: what came out.
            "observed_answer_shape": shape,
            "shape_threshold_tokens": 8,
            # THE INFERENCE: what that is taken to mean. SEPARATE, because it is a second step.
            "observed": observed,
            "observed_is_an_inference": True,
            "inference_caveat": ("a LONG answer is not necessarily deliberation -- a model that echoes the "
                                 "question in a schema produces a long answer too, and this probe cannot "
                                 "tell them apart"),
            "requested": REASONING,
            "disagrees_with_config": (REASONING != "auto" and observed != REASONING)}


def budget_signature(turns, cap):
    """DID IT HIT THE CAP, OR COULD IT NOT ANSWER? Different findings, and one has been published as the other.

    A `not_an_action` count is NOT a capability result until this has been read. `2314 tokens and no
    commitment` is the signature of a model with no stop condition, not of a model that cannot do the task.
    """
    n = len(turns) or 1
    hit = sum(1 for t in turns if t.get("budget_hit"))
    return {"turns": len(turns), "turns_that_hit_the_ceiling": hit, "ceiling": cap,
            "fraction_capped": round(hit / n, 3),
            "all_turns_capped": hit == len(turns) and len(turns) > 0,
            "reading": ("BUDGET-CONFOUNDED -- every answer was cut off at the ceiling, so this is NOT a "
                        "capability result until it is re-run with room"
                        if hit == len(turns) and turns else
                        "some turns hit the ceiling -- see the per-turn rows"
                        if hit else "no turn hit the ceiling -- the answers are the model's own endings")}


def dead_end_verdict(level_text, tokens, max_states=200000):
    """DID THIS ENTRANT WALK INTO A DEAD END? Recorded BESIDE THE COUNTERS, because they cannot say.

    THE GAP THIS CLOSES: `moves 4` reads as four successful actions whether they were progress or four walks
    around a level that cannot be finished. The counters are TRUE and they are not the whole truth, and a
    reader who only has them cannot tell the difference.

    AND IT IS A PROOF ABOUT *THIS ENTRANT'S* MOVE, not a general remark about the level: the position after
    its first action is handed to the solver, which either finds a solution or COMPLETELY ENUMERATES the
    reachable space and finds none. An empty search is not a dead end -- BUDGET_EXHAUSTED is reported as
    UNKNOWN, never as a fatal verdict.
    """
    if not tokens:
        return {"checked": False, "why": "no tokens produced"}
    first = (tokens[0] or "").strip().upper()
    if len(first) != 1 or first not in ACTIONS_UDLR:
        return {"checked": False, "first_action": tokens[0], "why": "the first token was not an action letter"}
    import sokoban_solver as SOL
    st = S.parse(level_text)
    nxt, outcome = S.step(st, first)
    if outcome not in ("moved", "pushed"):
        return {"checked": False, "first_action": first, "why": f"the first action was {outcome}"}
    r = SOL.solve_text(S.render(nxt), name="after-first-action", max_states=max_states)
    v = r.get("verdict")
    # THE PROOF LIVES IN `r["proof"]`, NOT AT THE TOP LEVEL -- and reading the wrong one made this function
    # claim A METHOD IT HAD NOT USED. The first version said "complete enumeration" for every UNSOLVABLE,
    # including a case the solver proved with the corner rule at the start. THE METHOD IS PART OF THE CLAIM:
    # "1 reachable state by a sound rule" and "70 states by full enumeration" are different proofs with
    # different strengths, and a field that reports the strength must read where the strength is written.
    proof = r.get("proof") or {}
    cost = r.get("cost") or {}
    kind = proof.get("kind") or "?"
    enumerated = proof.get("reachable_states_enumerated", cost.get("states_reachable_enumerated"))
    if v == "UNSOLVABLE":
        return {"checked": True, "first_action": first, "no_solution_from_here": True,
                "proof_kind": kind,
                "proof_rule": proof.get("rule"),
                "reachable_states_enumerated": enumerated,
                "states_expanded": cost.get("states_expanded"),
                # THE READING NAMES THE METHOD THE SOLVER ACTUALLY USED, AND CLAIMS ONLY WHAT WAS RUN.
                "reading": (f"DEAD END ON THE FIRST ACTION -- proved by {kind}"
                            + ("; no solution exists from here"
                               if kind == "complete_enumeration" else
                               "; a sound, skip-only rule fired at the start, so the position is dead on a "
                               "rule rather than on this search's exhaustion")
                            + ". Every later counter is movement inside a position that cannot be finished.")}
    if v == "SOLVABLE":
        return {"checked": True, "first_action": first, "no_solution_from_here": False,
                "still_solvable_in": r.get("moves"),
                "reading": "still winnable after the first action"}
    return {"checked": True, "first_action": first, "no_solution_from_here": None,
            "unknown": True, "budget": r.get("budget"),
            "reading": ("UNKNOWN -- the follow-up search stopped early, so this is NOT a dead end. "
                        "'Gave up' and 'dead end' are different claims.")}


ACTIONS_UDLR = ("U", "D", "L", "R")


def run(entrant, level_path, cap, port):
    level = open(level_path).read()
    label = os.path.basename(entrant).replace(".gguf", "")
    lname = os.path.basename(level_path).replace(".txt", "")
    st = S.parse(level)

    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    # THE ARM IS IN THE FILENAME -- BOTH ARMS. It carried `legend()` and NOT the reasoning setting, so an
    # A/B over `--reasoning` would have had arm A's raw log OVERWRITTEN BY ARM B's, and the only evidence of
    # what each arm actually sent would have been gone. THAT IS FINDING 018 AND 020 A THIRD TIME, caught
    # this time before the run rather than after -- and caught because the filename was READ rather than
    # assumed, the same way the read-control caption and the batch's scope sentence were caught.
    log = os.path.join(HERE, "logs",
                       f"SOKOBAN_{label}_{lname}_{legend()}_rea-{REASONING}.log")
    srv = subprocess.Popen(server_argv(entrant, 4096, port),
                           stdout=open(log, "w"), stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        t0 = time.time()
        up = False
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                return {"entrant": label, "entrant_digest": model_digest(entrant),
                        "level": lname, "loaded": False,
                        "why": f"server exited rc={srv.returncode}"}
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                up = True
                break
            except Exception:                                           # noqa: BLE001
                time.sleep(3)
        if not up:
            return {"entrant": label, "entrant_digest": model_digest(entrant),
                    "level": lname, "loaded": False,
                    "why": "never answered /health in 600 s"}
        load_s = time.time() - t0

        # THE PROBE RUNS BEFORE A SINGLE GAME TURN. Ask once, briefly: what setting is this model ACTUALLY
        # on? Recorded as OBSERVED beside REQUESTED, because a config field nobody measured is the same
        # class as a legend nobody read.
        probe = probe_reasoning(base)

        tokens, turns = [], []
        cur, history = S.render(st), []
        missing_values = 0
        for i in range(cap):
            text, secs, nt, hit, source = ask(base, cur, history)
            tok = first_token(text)
            tokens.append(tok)
            is_missing = (source == "capped-deliberation-missing-value")
            if is_missing:
                missing_values += 1
            # EACH TURN SAYS WHAT THE CAP CUT, because `finish_reason=length` describes the harness and not the
            # model. Measured: the same task returned `length` at 1200, 2048 AND 4096 tokens and was CORRECT at
            # every size -- so a bare `length` invites a reader to infer a failure that may not be there.
            capped = hit
            turns.append({"ply": i, "raw": text[:400], "token": tok, "secs": round(secs, 1),
                          "gen_tokens": nt, "budget_hit": hit,
                          "cap_cut": cap_cut_statement(capped, bool(tok)),
                          "answer_field": source,
                          # A MISSING VALUE IS NOT AN ANSWER. The harness produced this emptiness, so it is
                          # recorded as missing rather than scored -- never an illegal move, never a zero.
                          "missing_value": is_missing,
                          "board": cur})
            history.append(tok)
            if not tok:
                # AN EMPTY ANSWER ENDS THE RUN, AND THE REASON IS NAMED RATHER THAN IMPLIED.
                #
                # `commands_exhausted` WOULD BE A FALSE STATEMENT -- this run used ONE command, not its
                # allocation. And that difference is not cosmetic: it changes the DENOMINATOR, and a rate
                # over `attempted` can be improved by quitting early. So the cell says WHICH termination it
                # was, and the reader is not left to infer forty turns from a one-turn cell.
                break
            # STEP THE SIMULATOR, so the next screen is the truth rather than the model's belief about it
            nxt, _outcome = S.step(st, tok.strip().upper()) if (
                len(tok.strip()) == 1 and tok.strip().upper() in S.ACTIONS) else (st, "noop")
            st = nxt
            cur = S.render(st)
            if S.solved(st):
                break

        r = S.play(level, tokens)
        # THE TERMINATION IS NAMED BY THE PATH THAT PRODUCED IT, and a harness-produced empty gets its own
        # name because "it could not answer" and "we cut it off" are different findings.
        if not r["solved"] and missing_values and missing_values == len(turns):
            r["ended"] = "budget_confounded"
            r["ended_why"] = ("every command was an empty answer the HARNESS produced: the model "
                              "deliberated into the ceiling and never reached an answer. NOT a capability "
                              "result until it is re-run with room or at a setting that stops deliberating.")
        r.update({"entrant": label, "entrant_digest": model_digest(entrant),
                  "entrant_digest_scope": "sha256 of the model FILE, first 16 hex. THE ENTRANT IS THE THING "
                                          "BEING MEASURED, so it is identified by a digest and not by a name; "
                                          "`entrant` beside it is a LABEL, for reading, not for checking.",
                  "level": lname, "loaded": True, "load_s": round(load_s, 1),
                  "turns": turns, "cap": cap, "final_screen": cur,
                  "legend": legend(), "legend_digest": legend_digest(),
                  # THE CONFIG BLOCK, with the reasoning setting on the same footing as ctx and temperature.
                  # THE CEILING IS RECORDED SEPARATELY FROM THE COUNT USED: `max_tokens_ceiling` is what the
                  # model was allowed, `cap` is how many turns it was allowed -- two different ceilings that
                  # were previously one word, "cap".
                  "config": {"reasoning": REASONING,
                             "reasoning_source": reasoning_source(),
                             "reasoning_declared": REASONING_DECLARED,
                             "reasoning_declared_in": REASONING_DECLARED_IN,
                             "reasoning_rationale": REASONING_RATIONALE,
                             "reasoning_changed_from_declaration": reasoning_changed_from_declaration(),
                             "reasoning_argv": reasoning_argv(),
                             "reasoning_supported_by_build": True,
                             "max_tokens_ceiling": MAX_TOKENS,
                             "command_cap": cap,
                             "ctx": 4096, "n_gpu_layers": 0, "temperature": 0.0,
                             "legend": legend(), "legend_digest": legend_digest(),
                             "server_argv": server_argv(entrant, 4096, port)},
                  # WHAT HAPPENED, not what was asked for.
                  "reasoning_probe": probe,
                  # THE FORMAT FIELDS (A7), AND A NAMING RELATIONSHIP NAMED RATHER THAN LEFT TO BE GUESSED:
                  #
                  #   `not_an_action`  is the GRAMMAR's per-turn outcome (SOKOBAN_READ_GRAMMAR §2)
                  #   `unreadable`     is the FORMAT field (A6/A7), and it is the AGGREGATE of the above
                  #
                  # THEY ARE THE SAME STATE AT TWO LEVELS, NOT TWO STATES. Two names for one state is how a
                  # format field and its reader drift apart -- so the relationship is written down here, and
                  # both travel, because the grammar's name is frozen and the format field is required.
                  "kind": "model",
                  "unreadable": r.get("not_an_action", 0),
                  "unreadable_is_the_aggregate_of": "not_an_action (grammar §2), per turn",
                  # AND INSIDE `unreadable` THERE IS A SUBSET THE HARNESS PRODUCED. Both are non-answers and
                  # both are INSIDE the denominator (A6) -- but "the model answered badly" and "we cut it
                  # off" are different findings and one has already been published as the other.
                  "missing_values": missing_values,
                  "missing_values_are_a_subset_of": "unreadable -- the harness produced these, the model "
                                                    "produced the rest",
                  # A7: OUTSIDE the denominator and reported separately. This cell PLAYED, so it is 0; the
                  # run-level count of cells that never started lives in the run block.
                  "never_started": 0,
                  "budget_signature": budget_signature(turns, MAX_TOKENS),
                  # THE COUNTERS CANNOT SAY WHETHER `moves 4` WAS PROGRESS. This can, and it travels on the
                  # same line as them because a reader who has only the counters cannot tell the difference.
                  "dead_end": dead_end_verdict(level, tokens)})
        return r
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                               # noqa: BLE001
            srv.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant")
    ap.add_argument("--level")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--port", type=int, default=8751)
    a = ap.parse_args()
    if not a.entrant or not a.level:
        ap.error("--entrant and --level are required")
    p = a.entrant if os.path.exists(a.entrant) else os.path.join(MODELS, a.entrant)
    if not os.path.exists(p):
        print(f"  ENTRANT ABSENT: {a.entrant}"); return 2
    r = run(p, a.level, a.cap, a.port)
    print(f"  entrant   {r['entrant']}")
    print(f"  level     {r['level']}")
    if not r.get("loaded"):
        print(f"  DID NOT LOAD -- {r['why']}"); return 3
    print(f"  ended     {r['ended']}    solved={r['solved']}    moves={r['moves']}")
    print(f"  counts    blocked={r['blocked']}  not_an_action={r['not_an_action']}  "
          f"give_up={r['give_up']}  gave_up_at={r['gave_up_at']}")
    print(f"  tokens    {[t['token'] for t in r['turns']]}")
    out = os.path.join(HERE, "probes", f"SOKOBAN_{r['entrant']}_{r['level']}.json")
    os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)
    json.dump(r, open(out, "w"), indent=1)
    print(f"  artifact  {os.path.relpath(out, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
