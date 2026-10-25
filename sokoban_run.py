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
# THE ONE READER OF RECORD -- IMPORTED, NEVER REIMPLEMENTED (RULING 79).
from answer_reader import read_answer                                   # noqa: E402
# RULING 82 -- the failure names the HOLDER, not the model.
from vram_holder import holder_sentence                                 # noqa: E402

LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")

# ==================================================================================================
# THE BINARY IS PART OF THE INSTRUMENT, SO IT IS SELECTABLE -- AND IT TRAVELS WITH THE NUMBER.
#
# WHAT THIS FIXES, MEASURED RATHER THAN ARGUED (card t_33042da0, five arms, two files, one box):
#
#   Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0    mainline b10931 = THE DECLARED DEFAULT   rc=1, model REFUSED
#                                         mainline b11540                           rc=1, model REFUSED
#                                         prism fork b10777                         loads, SOLVES level 01 in 1 move
#   Ternary-Bonsai-2-2B-Q2_0              mainline b10931 = THE DECLARED DEFAULT   LOADS, and answers
#                                         each turn with 64 tokens of multilingual token salad -- three
#                                         turns, zero moves, `not_an_action` 3 -- FILED AS THE MODEL'S
#                                         NUMBER, because nothing in the run said which binary answered.
#                                         prism fork b10777                         rc=-6 (ggml_abort)
#
# So `python3 sokoban_run.py --entrant <bonsai>` measured MAINLINE and filed it under the model's name, and
# the ONLY way to run the fork was to set the module constant in memory at the call site -- an override
# performed outside the artifact is an override the artifact cannot report. A driver that can only be
# pointed at another instrument by monkey-patching it cannot host that family.
#
# THE DEFAULT IS THE CONSTANT ABOVE, UNCHANGED, so every existing record keeps the instrument it was taken
# under and no published number moves. And the flag takes a PATH, deliberately: choosing between a fork and
# mainline is a choice of INSTRUMENT, not a setting of the model.
#
# AND A PATH IS NOT AN IDENTITY -- the rule the ENTRANT gets further down this file, applied one layer down
# the instrument. MEASURED ON THIS BOX: `~/.hermes/runtimes/llamacpp/b10931/cuda/llama-server` reports
# `build 10964, commit b29c606e2`; a record carrying only that path names 10931 and describes 10964. So the
# record carries the binary's FILE DIGEST and the selector that chose it: portable-shaped values, and NO
# new path is published (`server_argv` already carries the path, and is already classified LOCAL in
# `make_conformance_package.py`).
# ==================================================================================================
LLAMA_SELECTED = None                    # --llama-server PATH. None = the declared default above.
# THE COMPUTE PATH, AS A PARAMETER RATHER THAN A CONSTANT. `-ngl 0` is this driver's REGISTERED launch
# and stays the DEFAULT, so every existing record keeps the instrument it was taken under. The suite
# that owns the card (kanban t_234b2387) runs its rows on the GPU, and a launch flag is a COMPUTE-PATH
# field -- the same class of variable as the binary above -- not part of the prompt or the scorer. It
# travels in the argv the server is actually started with, so a row states the path it ran on and no
# flag can imply what a process did.
NGL_DECLARED = 0
NGL = NGL_DECLARED                       # --ngl INT. Set in main(); read by server_argv().
_BINARY_DIGEST_CACHE = {}


def llama_server():
    """THE BINARY THAT WILL ACTUALLY BE EXECUTED -- read at CALL TIME, so a selection made in main()
    reaches the launch AND the record, rather than only the launch."""
    return LLAMA_SELECTED or LLAMA


def binary_digest(path=None):
    """sha256 of the BINARY FILE, first 16 hex. Cached per path, streamed, so a large binary is fine.

    AN UNREADABLE BINARY GETS null AND A REASON, NEVER A FABRICATED DIGEST -- the same rule, and the same
    reason, as `model_digest` above: a made-up hash is worse than a missing one because it verifies.
    """
    p = path or llama_server()
    if p not in _BINARY_DIGEST_CACHE:
        h = hashlib.sha256()
        try:
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            _BINARY_DIGEST_CACHE[p] = h.hexdigest()[:16]
        except OSError:
            _BINARY_DIGEST_CACHE[p] = None
    return _BINARY_DIGEST_CACHE[p]


def binary_source():
    """WHICH SELECTOR CHOSE THE BINARY -- and the wording is exact, because only one of the two answers is
    knowable from in here.

    MEASURED, and this is why the field is worded this way: the pre-image way of running the fork was to
    set `LLAMA` in memory at the call site, and a module cannot tell that its own constant was patched --
    so any field claiming `is_the_declared_default` would have answered TRUE for a fork run, which is a
    false statement made out of a true measurement. The DIGEST says which binary ran; this says which
    selector was used. Two fields, two different facts, and neither is an inference.
    """
    return "--llama-server" if LLAMA_SELECTED else "no selector given: the module constant LLAMA"


def binary_provenance():
    """WHICH BINARY, IN THREE VALUES: the digest, what the digest is a digest OF, and which selector chose
    it. All three are portable-shaped, and no path is added -- `server_argv` already carries the path and is
    already classified LOCAL in `make_conformance_package.py`.

    CARRIED BY THE CELL RECORD AND BY BOTH LOAD-FAILURE RECORDS. The failure path is the one where the
    binary is decisive -- the 4B file above is REFUSED by the default binary and runs on the fork -- and a
    failure record that cannot say which binary refused it is exactly the record this change exists for, on
    its worst day. One definition, so the two records cannot drift apart.
    """
    return {"server_binary_digest": binary_digest(),
            "server_binary_digest_scope": ("sha256 of the BINARY FILE, first 16 hex. THE BINARY IS PART OF "
                                           "THE INSTRUMENT, so it is identified by a digest and not by a "
                                           "path alone: a path can name one build and hold another."),
            "server_binary_source": binary_source()}


# ==================================================================================================
# THE ARTIFACT PATH IS OWNED BY ONE RUN (card t_8dc430a7, S1).
#
# FINDING 020's rule -- "a run must OWN its artifact path: one run, one file ... launching a second run
# against a live path is not a retry, it is an OVERWRITE" -- on the axis the last fix did not cover.
# MEASURED on the pre-image driver: two runs on one (entrant, level), fork then mainline, wrote ONE
# artifact path and ONE log path; the first run's record is gone, and its log was overwritten with it.
# NO FIELD COULD CLOSE THAT: the record that would carry the field is the record that gets overwritten.
# So the fix is a REFUSAL, and it is taken AT ADMISSION, before Popen -- a refusal that costs a whole
# model load is not a refusal (a refusal must consume nothing), and the run that never starts overwrites
# neither the artifact nor the log.
#
# IT REFUSES ON ANY EXISTING RECORD, NOT ONLY ON A DIFFERING server_binary_digest. Three measured
# reasons, and the wider form is a Chair decision rather than the card's one-liner:
#   (a) a record written before f1c0c5d carries NO DIGEST TO COMPARE -- measured at this commit: both
#       committed Bonsai artifacts carry no server_binary_digest, and one of them is the very record the
#       last card's acceptance run destroyed;
#   (b) the artifact NAME never carried the legend or the reasoning arm -- only the LOG name did
#       (FINDING 024 §1) -- so a same-binary run on the other arm of the A/B would still delete arm A;
#   (c) the same instrument twice is not the same record: measured on the 2B Bonsai, two runs of one
#       driver on one binary emitted 0 and 64 tokens.
# THE NAME IS NOT MOVED: probes/SOKOBAN_<entrant>_<level>.json is a PUBLISHED convention (cited in
# GAMES.md and in the conformance package's census), so every existing citation still resolves to the
# same path and the fix is a refusal rather than a rename.
# ==================================================================================================
ARTIFACT_OVERRIDE = None                 # the reason given on this command line, or None. Read by main().
IDENTITY_IN_RECORD = ("server_binary_digest", "legend_digest", "reasoning")


def cell_labels(entrant, level_path):
    return (os.path.basename(entrant).replace(".gguf", ""),
            os.path.basename(level_path).replace(".txt", ""))


def artifact_path(entrant, level_path):
    """THE ONE DEFINITION OF THE ARTIFACT'S COORDINATE -- used by the gate and by the writer both, so the
    path the gate refuses on and the path the run writes cannot be two different paths."""
    label, lname = cell_labels(entrant, level_path)
    return os.path.join(HERE, "probes", f"SOKOBAN_{label}_{lname}.json")


def run_identity():
    """WHAT THIS RUN IS, in the three values the RECORD can carry and the NAME cannot: the instrument,
    and the two arms whose names were put into the LOG filename and never into the artifact's."""
    return {"server_binary_digest": binary_digest(), "legend_digest": legend_digest(),
            "reasoning": REASONING}


def carried_identity(d):
    """-> THE SAME THREE VALUES AS AN EXISTING RECORD CARRIES THEM, or None for one it does not carry.

    None IS NOT A MATCH AND IS NOT TREATED AS ONE: PRECEDENCE.md -- when the disagreement is a MISSING
    record, the winner is nothing -- so a run cannot show it is the same instrument as a record that
    names no instrument. The three live at different levels by construction (the load-failure records
    carry them at their top level, the cell record inside `config`), so the reader takes either.
    """
    cfg = d.get("config") if isinstance(d.get("config"), dict) else {}
    return {k: (d[k] if k in d else cfg.get(k)) for k in IDENTITY_IN_RECORD}


def artifact_gate(out, reason, old_bytes=None):
    """-> (ok, message, replaced). REFUSES to write over a record this run did not take.

    THE MESSAGE IS THE GATE'S OTHER HALF: it names the path, what the record on disk says about itself,
    what THIS run would write, and which of the two the reader is looking at -- because the person who
    hits this at 2am is the person who needs to read it, and the remedy is one token whose text lands in
    the record (a gate with an override that is not written down is a gate nobody can audit).
    """
    if not os.path.exists(out):
        return True, "", None
    if old_bytes is None:
        old_bytes = open(out, "rb").read()
    try:
        old = json.loads(old_bytes.decode())
    except (OSError, ValueError):
        old = None
    rel = os.path.relpath(out, HERE)
    mtime = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(out)))
    if reason is not None:
        return True, "", {
            "path": rel,
            "sha256": hashlib.sha256(old_bytes).hexdigest(),
            "bytes": len(old_bytes),
            "mtime": mtime,
            "it_named": carried_identity(old) if isinstance(old, dict) else "UNREADABLE AS JSON",
            "reason_given": reason,
            "reading": ("THIS RUN REPLACED THE RECORD AT THIS PATH. The replaced record is NOT "
                        "recoverable from this file: what survives is that it existed, the digest of the "
                        "bytes it was, and what it said about its own instrument. The reason above is "
                        "the operator's, verbatim, and is checked against nothing.")}
    this = run_identity()
    if not isinstance(old, dict):
        theirs = {k: "UNREADABLE" for k in IDENTITY_IN_RECORD}
        verdict = "THE RECORD ON DISK COULD NOT BE READ AS JSON, so it cannot be shown to be this run's."
    else:
        theirs = carried_identity(old)
        diff = [k for k in IDENTITY_IN_RECORD if theirs[k] != this[k]]
        verdict = ("THE TWO ARE THE SAME INSTRUMENT AND THE SAME ARMS -- nothing in these three values "
                   "differs -- AND THE REPLACEMENT IS STILL REFUSED, because the same instrument twice "
                   "is not the same record." if not diff else
                   "AND THESE DO NOT MATCH: " + "; ".join(
                       f"{k} (record {theirs[k]!r} -> this run {this[k]!r})" for k in diff))
    pairs_old = "  ".join(f"{k}={theirs[k]!r}" for k in IDENTITY_IN_RECORD)
    pairs_new = "  ".join(f"{k}={this[k]!r}" for k in IDENTITY_IN_RECORD)
    return False, (
        f"REFUSED: {rel} ALREADY HOLDS A RECORD, AND A RUN DOES NOT REPLACE A RECORD IT DID NOT TAKE "
        f"(FINDING 020).{os.linesep}"
        f"  record on disk        {rel}  ({len(old_bytes)} B, mtime {mtime}){os.linesep}"
        f"  it says about itself  {pairs_old}{os.linesep}"
        f"  this run would write  {pairs_new}{os.linesep}"
        f"  {verdict}{os.linesep}"
        f"  A MISSING VALUE IS NOT A MATCH: a record that names no instrument cannot be shown to be this "
        f"run's instrument (PRECEDENCE.md: when the disagreement is a missing record, the winner is "
        f"nothing).{os.linesep}"
        f"  THE REMEDY IS NOT TO IGNORE THIS EXIT CODE, AND IT IS NOT A BARE FORCE. If the replacement "
        f"is intended, say why, and the reason is written into the record that does the replacing:{os.linesep}"
        f"      --overwrite-artifact \"<why this record should be replaced>\"{os.linesep}"
        f"  NOTHING HAS BEEN WRITTEN, NO SERVER HAS BEEN STARTED AND NOTHING HAS BEEN CONSUMED."), None


# ==================================================================================================
# WHICH CONDITION IS THIS FAILURE REPORTING? (card t_8dc430a7, S2)
#
# RULING 82's holder sentence is appended to EVERY load failure, so a file the binary cannot PARSE is
# reported as a card-tenancy condition. MEASURED: a CPU-only run of the 4B Bonsai printed "AND THE CARD
# IS HELD BY: pid 2418 (134 MiB) ... Tenants total 7146 MiB" while the cause was two lines further down
# the log the record did not quote:
#     E gguf_init_from_reader: tensor 'token_embd.weight' has invalid ggml type 142. should be in [0, 43)
# THE SENTENCE IS NOT WRONG, IT IS UNCONDITIONAL, AND TWO CONDITIONS PRINTED ONE SENTENCE.
#
# RULING 82 IS NOT WEAKENED AND ITS CARRIER IS UNTOUCHED -- vram_holder.py is NOT edited here: the
# sentence is kept verbatim for the case the ruling was ratified for, a log that names no cause of its
# own. What this adds is the OTHER case, decided by a READING of the server's own log, with the matched
# line QUOTED WITH ITS LINE NUMBER so a reader can overrule the class from the carrier.
#
# THE SIGNATURE LIST IS A SNAPSHOT OF ONE BUILD'S WORDING, WHICH IS WHY THE LINE TRAVELS WITH THE CLASS.
# Measured on this box: `invalid ggml type 142` (the 4B and the 27B Bonsai files), `invalid magic
# characters` (a file that is not a gguf), `done_getting_tensors: wrong number of tensors` (a file whose
# tensors do not match its own header). A check written against ONE of those would have called the other
# two "no cause named" -- so the class is never asserted alone.
# ==================================================================================================
FILE_REFUSAL_SIGNATURES = ("gguf_init_from_reader", "llama_model_loader", "invalid ggml type",
                           "invalid magic characters", "failed to read tensor info",
                           "done_getting_tensors", "unknown model architecture")


def log_file_refusal(log_path):
    """-> (kind, line, lineno), kind in {"file_refusal", "no_cause", "log_unreadable"}.

    A MISS IS REPORTED AS ITS OWN KIND: an unreadable log is not "the log says nothing", the same way an
    unreadable cause is never reported as an absent one.
    """
    try:
        lines = open(log_path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return "log_unreadable", None, None
    for i, ln in enumerate(lines, 1):
        if any(sig in ln for sig in FILE_REFUSAL_SIGNATURES):
            return "file_refusal", ln.strip(), i
    return "no_cause", None, None


def load_failure(log_path, status):
    """-> {"why": ..., "load_failure_class": ...} for a load that did not finish.

    ONE DEFINITION, SO THE TWO FAILURE RETURNS CANNOT DRIFT APART IN WORDING OR IN CLASS. The status is
    the first line, exactly as it read before this change; what follows says WHICH CONDITION is being
    reported, which is what one sentence for two conditions could not say.
    """
    kind, line, lineno = log_file_refusal(log_path)
    if kind == "file_refusal":
        return {"load_failure_class": "the binary refused the FILE (the log names the cause)",
                "why": (f"{status}.{os.linesep}"
                        f"THE BINARY REFUSED THE FILE -- log line {lineno}, quoted verbatim: "
                        f"{line}{os.linesep}"
                        f"  AND THE HOLDER SENTENCE IS NOT REPORTED HERE: RULING 82's sentence is "
                        f"appended when the log names no cause of its own, and this log names one. An "
                        f"unconditional tenancy report for a file the binary cannot read points the "
                        f"reader at the wrong subsystem.")}
    if kind == "log_unreadable":
        return {"load_failure_class": "unknown -- the server's log could not be read",
                "why": (f"{status}.{os.linesep}"
                        f"  THE SERVER'S LOG COULD NOT BE READ ({os.path.basename(log_path)}), so WHICH "
                        f"CONDITION THIS IS CANNOT BE DECIDED FROM HERE -- an unreadable cause is "
                        f"reported as unreadable, never as absent.{os.linesep}{holder_sentence()}")}
    return {"load_failure_class": "no cause named by the log: the card at failure is what is reported",
            "why": (f"{status}.{os.linesep}{holder_sentence()}{os.linesep}"
                    f"  AND THE LOG NAMES NO CAUSE OF ITS OWN: it was scanned for a reader's refusal of "
                    f"the file and carries none, which is the condition RULING 82 was ratified for.")}

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
    """THE WHOLE LAUNCH, in one place, so what is recorded is what was run.

    THE BINARY COMES FROM `llama_server()`, NOT FROM THE CONSTANT DIRECTLY: with `--llama-server` given,
    the launch and `config.server_argv` both take the selection, so the record cannot show the default and
    name the fork.
    """
    return ([llama_server(), "-m", entrant, "-c", str(ctx), "-ngl", str(NGL), "--port", str(port), "--no-webui"]
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
        # THE READER OF RECORD IS IMPORTED, NOT REIMPLEMENTED -- RULING 79, AND THIS FILE WAS THE LAST
        # HOLD-OUT. It had its own read built from `if not txt and reasoning_content...`, which agreed with the
        # shared one TODAY and would have been free to disagree tomorrow. THE INSTRUMENT THAT WRITES THE RECORD
        # AND THE INSTRUMENTS THAT SCORE IT MUST READ IT THE SAME WAY, OR THE RECORD HAS TWO MEANINGS.
        #
        # AND THE ONE BEHAVIOUR THIS CHANGES, STATED RATHER THAN SLIPPED IN: an UNCAPPED trace is now a MISSING
        # VALUE instead of a fallback. The old read handed the deliberation back as if it were an answer; a
        # trace is deliberation, and nothing is scored from it. STRICTER, and on the side of not scoring
        # something that is not an answer.
        ans = read_answer(j)
        return (ans["text"], dt, ans["completion_tokens"],
                ans["finish_reason"] == "length", ans["field"])
    except Exception as e:                                              # noqa: BLE001
        ans = read_answer({}, exception=e)
        return "", time.time() - t0, 0, False, ans["field"]


# THE COMMENT THAT WAS HERE IS NOW THE REASON THE READER EXISTS, and it is preserved because it is the whole
# argument: "A reasoning model leaves `content` empty and puts its deliberation in `reasoning_content`.
# Falling back to it is right WHEN THE DELIBERATION CONTAINS THE ANSWER. IT IS WRONG WHEN THE TURN WAS CUT OFF
# AT THE CEILING, because then the first token of the deliberation is NOT an answer -- it is the beginning of a
# sentence that never finished. THE ORNITH CASE EXACTLY: 2314 tokens of deliberation, no move. Reading that
# fallback as a token would score a TRUNCATION ARTIFACT as a legal action."
#
# THAT ARGUMENT WAS RIGHT, AND I THEN VIOLATED IT IN A SIDE-SCRIPT BY SCORING A TRACE AS AN ANSWER -- which is
# why the rule now lives in ONE IMPORTED MODULE instead of in this file's good intentions.


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
    # THE PROBE READS THE SAME READER, SO "content or reasoning_content" HAS ONE DEFINITION IN THIS TREE.
    # It does not SCORE the answer -- it only reports which field the text arrived in -- but a second
    # definition of that question is the same class of defect as a second reader of record.
    _ans = read_answer(j)
    txt = _ans["text"]
    think = _ans.get("trace_head") or ""
    ctok = _ans["completion_tokens"]
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
    # THE LABELS COME FROM ONE DEFINITION, because the artifact's coordinate is derived from them too and
    # the gate must refuse on the SAME path the writer writes.
    label, lname = cell_labels(entrant, level_path)
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
                        # WHICH CONDITION THIS IS -- RULING 82's sentence is KEPT for the case it was
                        # ratified for, and the file-refusal case quotes the binary's own line instead of
                        # pointing the reader at the card. MEASURED: a CPU-only run of a file the binary
                        # cannot parse printed the tenant list while the cause was in the log it did not
                        # quote. Both branches come from ONE definition (load_failure), so the two
                        # failure returns cannot drift apart, and the class travels in the record.
                        **load_failure(log, f"server exited rc={srv.returncode}"),
                        # WHICH BINARY REFUSED IT -- the failure path is where this matters most (the
                        # same file is REFUSED by the default and runs on the fork), so the failure record
                        # carries the binary's identity too, from the one definition.
                        **binary_provenance()}
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                up = True
                break
            except Exception:                                           # noqa: BLE001
                time.sleep(3)
        if not up:
            return {"entrant": label, "entrant_digest": model_digest(entrant),
                    "level": lname, "loaded": False,
                    # SAME DEFINITION AS THE EXIT BRANCH, so the two can only differ by the status they
                    # are handed. A /health timeout is the case where the log usually names nothing, so
                    # this is where RULING 82's sentence normally appears.
                    **load_failure(log, "never answered /health in 600 s"),
                    **binary_provenance()}
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
                             "server_argv": server_argv(entrant, 4096, port),
                             # WHICH BINARY: the digest, whether it is the declared default, and which
                             # selector chose it (see binary_provenance()). Portable-shaped -- no new path.
                             **binary_provenance()},
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


# ==================================================================================================
# THE REFUSAL: A TERNARY ENTRANT UNDER A BINARY THAT CANNOT READ IT IS NOT A RUN, IT IS A MISFILING.
#
# The flag above makes the RIGHT instrument possible. This makes the WRONG one impossible -- because
# possible-and-documented was not enough: on 2026-10-17 a sweep took the default binary anyway and
# produced nine records, five of them failure records and one of them naming mainline outright. Its card
# said so in prose. A warning in a card body is not a gate.
#
# THE TEST IS THE FILE'S OWN DECLARATION, NOT ITS NAME -- "a name is not an identity", applied one layer
# down from the entrant rule. These ggufs declare `prism.hadamard.*` in their header; a non-ternary model
# declares none of it (measured: 4B 11 occurrences, 2B 10, Ministral-3-3B 0). A rename cannot smuggle one
# past this, and a false positive is not reachable from a file that does not carry the metadata.
#
# AND THE REFUSAL NAMES WHAT IT WOULD HAVE MEASURED. The consequence is not "it fails": on the 2B the
# default binary LOADED the file and answered with 64 tokens of multilingual token salad -- three turns,
# zero moves, not_an_action 3 -- FILED AS THE MODEL'S NUMBER. A message that said "incompatible" would
# hide exactly the thing that makes this worth refusing.
# ==================================================================================================
def refuse_a_ternary_entrant_under_a_blind_binary(entrant_path):
    """-> None when the pair is runnable, or a refusal message when it is not.

    Fail-SAFE BY CONSTRUCTION: an unreadable file raises no objection here -- a genuine load failure
    reports itself later, with its own class -- so this gate can never be the reason a runnable pair is
    blocked. It can only refuse a pair whose model declares prism metadata and whose binary does not.
    """
    try:
        with open(entrant_path, "rb") as f:
            head = f.read(1 << 20)
    except OSError:
        return None
    if b"prism.hadamard" not in head:
        return None
    binary = llama_server()
    if "prism" in binary.lower():
        return None
    return (
        f"  REFUSED: {os.path.basename(entrant_path)} DECLARES prism.hadamard -- a ternary file that\n"
        f"  needs the prism fork.\n"
        f"    selected binary : {binary}\n"
        f"    selected by     : {binary_source()}\n"
        f"    WHAT IT WOULD MEASURE: the default binary either refuses the file, or loads it and answers\n"
        f"    with tokens that are not moves -- measured on the 2B as three turns, zero moves, 64 tokens\n"
        f"    of multilingual token salad, FILED AS THE MODEL'S NUMBER.\n"
        f"    RUN IT PROPERLY:\n"
        f"      --llama-server /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server\n"
        f"    This is a gate, not a limitation: pass the fork and the same command runs."
    )


def main():
    global LLAMA_SELECTED, ARTIFACT_OVERRIDE, NGL
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant")
    ap.add_argument("--level")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--port", type=int, default=8751)
    # THE ESCAPE HATCH, AND IT CARRIES A REASON RATHER THAN A FORCE. The gate below refuses to write over
    # a record this run did not take (FINDING 020: a second run on a live path is an OVERWRITE, not a
    # retry). A replacement still has to be possible -- instruments change and cells get re-measured --
    # but a gate with an override that is not written down is a gate nobody can audit, so the token takes
    # the reason as its VALUE and the reason is written into the record that does the replacing.
    ap.add_argument("--overwrite-artifact", dest="overwrite_artifact", default=None, metavar="REASON",
                    help="replace the record already at this cell's artifact path, saying WHY. The reason "
                         "is written into the replacement beside the digest of the record it replaced.")
    # THE BINARY THE RUN IS TAKEN ON. DEFAULT: the declared constant in this file, so every existing
    # record keeps the instrument it was taken under and no published number moves. NEEDED FOR A
    # FORK-ONLY FAMILY: on the Bonsai ternary files the default binary either REFUSES the file or
    # answers with token salad, and the fork is the only instrument that measures the model -- see the
    # block above `LLAMA_SELECTED`. Without this flag the only way in was to set that constant in memory
    # at the call site, which is an override the artifact cannot report.
    ap.add_argument("--llama-server", dest="llama_server", default=None,
                    help="path to the llama-server BINARY to run (default: the declared default, "
                         "unchanged). The binary's digest is recorded with the run.")
    ap.add_argument("--ngl", type=int, default=NGL_DECLARED,
                    help="--n-gpu-layers for the entrant's server (default: the registered %d). A "
                         "COMPUTE-PATH field only: the prompt and the scorer are untouched, and the "
                         "value travels in the argv the server is started with." % NGL_DECLARED)
    a = ap.parse_args()
    NGL = a.ngl
    if not a.entrant or not a.level:
        ap.error("--entrant and --level are required")
    if a.llama_server:
        # A PATH THAT DOES NOT EXIST OR IS NOT EXECUTABLE IS REFUSED HERE RATHER THAN HANDED TO exec --
        # the guard `arena.py` already carries at :152, for the same reason: `--llama-server /typo` would
        # otherwise surface as a launch failure and read like a broken model.
        sel = os.path.expanduser(a.llama_server)
        if not (os.path.exists(sel) and os.access(sel, os.X_OK)):
            print(f"  BINARY ABSENT OR NOT EXECUTABLE: {a.llama_server}"); return 2
        LLAMA_SELECTED = sel
    p = a.entrant if os.path.exists(a.entrant) else os.path.join(MODELS, a.entrant)
    if not os.path.exists(p):
        print(f"  ENTRANT ABSENT: {a.entrant}"); return 2

    # ---- THE BINARY GATE, AT ADMISSION -- BEFORE THE ARTIFACT GATE, BEFORE ANY SERVER IS SPAWNED ----
    # Before the artifact gate because the instrument is the more basic question: a run refused here
    # could not have been a measurement of this model under any file name. Before the spawn because a
    # refusal costing a 1.2 GB model load is a report filed afterwards, not a refusal. Exit 4, distinct
    # from 2 (a bad argument) and from the load-failure codes, so a caller can tell "this pair must not
    # run" from "this pair did not run".
    refusal = refuse_a_ternary_entrant_under_a_blind_binary(p)
    if refusal:
        print(refusal); return 4

    # ---- THE ARTIFACT GATE, AT ADMISSION -- BEFORE ANY SERVER IS SPAWNED -------------------------
    # At admission rather than at the write, for the reason the game-contract gate is at admission: a
    # refusal that costs a whole model load is not a refusal, it is a report filed afterwards. It also
    # makes the LOG axis safe with no change to the log's name -- the run that would overwrite the log
    # never opens it. THE NAME IS NOT MOVED: probes/SOKOBAN_<entrant>_<level>.json is published.
    out = artifact_path(p, a.level)
    if a.overwrite_artifact is not None and not a.overwrite_artifact.strip():
        print("  --overwrite-artifact WAS GIVEN AN EMPTY REASON: a replacement has to say why. Nothing "
              "written."); return 2
    ARTIFACT_OVERRIDE = a.overwrite_artifact
    gate_ok, gate_msg, replaced = artifact_gate(out, ARTIFACT_OVERRIDE)
    if not gate_ok:
        for line in gate_msg.splitlines():
            print(f"  {line}")
        return 4

    r = run(p, a.level, a.cap, a.port)
    print(f"  entrant   {r['entrant']}")
    print(f"  level     {r['level']}")
    # ONLY ON THE SELECTED PATH, so a run on the declared default prints exactly what it printed before
    # this change, byte for byte: the default's own stdout stays its own control.
    if LLAMA_SELECTED:
        print(f"  binary    {LLAMA_SELECTED}  (server_binary_digest {binary_digest()})")
    # THE RECORD, NOT JUST THE CONSOLE -- ruling 82's unverified half, closed.
    #
    # A LOAD FAILURE RETURNED BEFORE THIS POINT, SO THE SENTENCE NAMING THE HOLDER EXISTED ONLY IN STDOUT. That
    # is the whole difference between a finding and a line on a screen: stdout is gone when the terminal closes,
    # and the tenant list is exactly what the tenancy decision needs to survive. THE FAILURE PATH WAS ALSO THE
    # ONE PATH WHERE THE RECORD MATTERED MOST, because a failure nobody can read later is a failure that gets
    # re-diagnosed from scratch.
    os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)
    if replaced is not None:
        # THE REPLACEMENT CARRIES THE FACT THAT IT IS ONE, AND WHAT IT DESTROYED. The replaced record is
        # gone; what survives is that it existed, the digest of its bytes, and what it said about its own
        # instrument -- beside the operator's reason, verbatim.
        r["artifact_replaced"] = replaced
    json.dump(r, open(out, "w"), indent=1)
    print(f"  artifact  {os.path.relpath(out, HERE)}")
    if replaced is not None:
        print(f"  REPLACED  {replaced['path']}  ({replaced['bytes']} B, sha256 "
              f"{replaced['sha256'][:16]}...) -- reason given: {replaced['reason_given']!r}")
    if not r.get("loaded"):
        print(f"  DID NOT LOAD -- {r['why']}")
        return 3
    print(f"  ended     {r['ended']}    solved={r['solved']}    moves={r['moves']}")
    print(f"  counts    blocked={r['blocked']}  not_an_action={r['not_an_action']}  "
          f"give_up={r['give_up']}  gave_up_at={r['gave_up_at']}")
    print(f"  tokens    {[t['token'] for t in r['turns']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
