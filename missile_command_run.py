#!/usr/bin/env python3
"""MISSILE COMMAND -- the entrant driver. One model, one frozen state, two characters at a time.

BUILT TO `PREREG_missile_command.md` (frozen: the simulator and its 34 controls, the two states, the
criteria and the outcome rows) and to the standing cabinet rules in `CABINET_STRUCTURE.md`. **The simulator
decided everything; this file only asks and records.**

TEMPLATE: `sokoban_run.py` -- the shape that already works: launch a neutral server, present the frozen
state, take one action per turn, write an artifact that carries the instrument.

## THE INTERFACE DECISION -- AND WHY THIS CABINET NEEDED NO CRITERION CHANGE

The task card asked for a choice between (a) step-locking the 3-second real-time timers and scoring it as a
turn-based game, or (b) driving it live and scoring it as a timed game -- because the published survey
classified Missile Command as KEYS/REALTIME (mouse), with canvas `click` -> (x,y) actions.

**(a) IS ALREADY WHAT THE FROZEN ARTIFACT IS, AND IT IS MEASURED RATHER THAN CHOSEN:**

```
missile_command.py   imports `sys` AND NOTHING ELSE -- no time, no sleep, no monotonic, no clock
                     (`clock_audit()` below re-measures this at every run and the finding is recorded)
the only clock       the STATE's own `tick` integer, advanced by exactly one per action
the frozen PREREG    "And the coordinate rule: no time limit. The cap is the budget, not the clock."
```

So there is no timer to step-lock and no live mode to drive: the play mode is turn-based BY CONSTRUCTION.
**NOTHING HERE CHANGES A FROZEN CRITERION**, which matters because a criterion change is not this cabinet's
to make. The KEYS/REALTIME sentence is a classification of the ARCADE GAME, not of this protocol -- a
repo-wide grep for `REALTIME`/`mouse`/`timed` finds it in no file of any of the four trees, and
`GAMES.md` does not contain the word `mouse` at all. It is recorded as an EXTERNAL claim.

## THE STANDING RULES THIS DRIVER IMPLEMENTS RATHER THAN REMEMBERS

* THE REASONING ARM IS DECLARED, NOT DEFAULTED -- read from `MC_DECLARATION.md`, and an undeclared run is
  REFUSED before anything is spawned. The override is an experiment arm and the record says which one ran.
* THE PROBE COMES BEFORE THE FIELD: one brief question, OBSERVED recorded beside REQUESTED; when they
  disagree the disagreement IS the finding.
* THE CEILING IS RECORDED SEPARATELY FROM THE COUNT USED, AND FROM THE COMMAND CAP.
* THE BUDGET SIGNATURE IS READ BEFORE ANY `malformed` COUNT IS CALLED A CAPABILITY RESULT.
* AN UNREADABLE ANSWER IS COUNTED, NEVER SCORED AS A WRONG MOVE (the simulator's `malformed` outcome -- the
  empty-list rule), AND AN EMPTY THE HARNESS PRODUCED IS A MISSING VALUE, never a token.
* ONE RUN, ONE PATH: the artifact gate refuses a path that already holds a record, at admission, before a
  single byte of a model is loaded.
* THE RECORD CARRIES THE DIGESTS OF THE INPUTS IT WAS PRODUCED UNDER: the simulator, the state, the legend,
  the entrant, the server binary, the reader of record and the declaration.
* THE RECORDED STATE IS A SUFFICIENT STATISTIC FOR THE SCORE -- and `sufficiency_check` re-derives the
  score and every screen from `(state_text, tokens)` afterwards and reports the re-derivation as a control.

    python3 missile_command_run.py --entrant <gguf> --state levels/mc_01_one_shot.txt
    python3 missile_command_run.py --self-test          # 8 controls, no model, no network
    python3 missile_command_run.py --dry-run --state levels/mc_02_scarcity.txt
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import missile_command as S                                                     # noqa: E402

# THE BINARY TRAP, AND IT IS A REFUSAL RATHER THAN A WARNING. Mainline llama.cpp LOADS a Bonsai ternary
# gguf and emits degenerate garbage (it does not apply the prism hadamard transform the file declares);
# on this box the 4B ternary file is even REFUSED by the default build while the fork loads and plays it
# (`probes/SOKOBAN_Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0_01_one_push.INSTRUMENT-NOTE.md`, measured
# 2026-10-16). A preset cannot pin a binary and a module constant cannot report itself, so the choice of
# INSTRUMENT is a flag whose value travels in the record (`config.server_argv` + the binary's digest).
LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
LLAMA_SELECTED = None                    # --llama-server PATH. None = the declared default above.
# THE FORK, NAMED ONCE AND USED WHEREVER IT IS THE REMEDY -- a remedy written out twice is a remedy that
# will differ from itself the first time one of them is corrected.
FORK_LLAMA = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
TERNARY_MARKERS = ("bonsai", "ternary")  # a family the declared default must not be asked to serve

MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")
MAX_TOKENS = 64                          # TWO CHARACTERS NEED A FEW TOKENS. THE CEILING, not the count
                                         # used -- both travel in the record.
CTX = 4096
DEFAULT_PORT = 8761
MAIN_TREE = "/home/chilly1/workspace/ocho_arena"        # the shared, frozen tree (read-only from here)

_DIGEST_CACHE = {}
_FLAG_CACHE = {}                         # (binary, flag) -> True/False/None, asked once each
_HELP_CACHE = {}                         # binary -> its own --help text, read once each


def file_digest(path):
    """sha256 of a FILE, first 16 hex, cached per path, streamed so a multi-GB gguf is fine.

    AN UNREADABLE FILE GETS null AND A REASON, NEVER A FABRICATED DIGEST -- a made-up hash is worse than a
    missing one because it verifies.
    """
    if path not in _DIGEST_CACHE:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            _DIGEST_CACHE[path] = h.hexdigest()[:16]
        except OSError:
            _DIGEST_CACHE[path] = None
    return _DIGEST_CACHE[path]


# ==================================================================================================
# RULING 79 -- THE READER OF RECORD IS IMPORTED, NEVER REIMPLEMENTED.
#
# This cabinet's tree does NOT carry `answer_reader.py` or `vram_holder.py` (they landed in the shared
# tree after this branch's cut). Writing a second reader here would be the one-definition defect applied
# to interpretation, and it fails silently in the direction of a better-looking number. So they are
# loaded from wherever they are found, and THE FILE THAT ACTUALLY ANSWERED IS NAMED AND DIGESTED IN THE
# RECORD. If neither exists, the driver REFUSES: an unidentified reader is not a reader.
# ==================================================================================================
def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


READER_PATH = _first_existing((os.path.join(HERE, "answer_reader.py"),
                               os.path.join(MAIN_TREE, "answer_reader.py")))
if READER_PATH is None:
    raise SystemExit("REFUSED: no answer_reader.py in this tree or in %s -- the reader of record cannot "
                     "be identified, and an unidentified reader is not a reader (RULING 79)." % MAIN_TREE)
_spec = importlib.util.spec_from_file_location("answer_reader", READER_PATH)
_answer_reader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_answer_reader)
read_answer = _answer_reader.read_answer

VRAM_PATH = _first_existing((os.path.join(HERE, "vram_holder.py"),
                             os.path.join(MAIN_TREE, "vram_holder.py")))
holder_sentence = None
if VRAM_PATH is not None:
    _vspec = importlib.util.spec_from_file_location("vram_holder", VRAM_PATH)
    _vram = importlib.util.module_from_spec(_vspec)
    _vspec.loader.exec_module(_vram)
    holder_sentence = getattr(_vram, "holder_sentence", None)


def reader_provenance():
    """WHICH FILE ANSWERED, and where it came from. Portable-shaped: a path and a digest, no inference."""
    return {"reader_of_record_path": READER_PATH,
            "reader_of_record_digest": file_digest(READER_PATH),
            "reader_of_record_scope": ("sha256 of the READER FILE, first 16 hex. RULING 79: the reader of "
                                       "record is imported, never reimplemented; this cabinet's tree does "
                                       "not carry it, so it is loaded from the shared tree and the file "
                                       "that answered is named here."),
            "reader_of_record_in_this_tree": READER_PATH.startswith(HERE)}


# ==================================================================================================
# THE DECLARATION -- READ, NOT DEFAULTED. AN UNDECLARED RUN IS REFUSED.
#
# CABINET_STRUCTURE.md: "THE REASONING SETTING IS A CONFIG FIELD AND EVERY BUNDLE RECORDS IT ... Set it
# DELIBERATELY ... and record the ARGV, not a summary of it." An unrecorded default is indistinguishable
# from a decision, and only one of those is evidence -- so the value is not written in this file at all.
# It is read from `MC_DECLARATION.md`, and a run whose arm is not declared there stops here.
# ==================================================================================================
DECLARATION_FILE = os.path.join(HERE, "MC_DECLARATION.md")
DECLARATION_KEYS = ("cabinet", "reasoning_arm", "reasoning_declared_in", "reasoning_rationale",
                    "protocol", "clock", "artifact", "legend_arm")


def read_declaration(path=DECLARATION_FILE):
    """-> {key: value} for the declared keys, FIRST OCCURRENCE WINS, or REFUSE.

    A REFUSAL AND NOT A DEFAULT, for the reason the block above gives. The parse is deliberately narrow --
    `key value` on one line, first occurrence, keys from a fixed list -- so prose in the declaration can
    never become a setting by accident.
    """
    if not os.path.exists(path):
        raise SystemExit(f"REFUSED: {path} is MISSING, so this run's reasoning arm is UNDECLARED. An "
                         f"undeclared arm is not a default; it is a decision nobody made.")
    out = {}
    for raw in open(path, encoding="utf-8").read().splitlines():
        line = raw.strip()
        if not line or " " not in line:
            continue
        k, v = line.split(" ", 1)
        if k in DECLARATION_KEYS and k not in out:
            out[k] = v.strip()
    missing = [k for k in ("cabinet", "reasoning_arm", "reasoning_declared_in", "legend_arm")
               if k not in out]
    if missing:
        raise SystemExit(f"REFUSED: {os.path.basename(path)} does not declare {missing}. Neither an arm "
                         f"nor a legend is defaulted in code: a default nobody chose is a decision nobody "
                         f"made, and only one of those is evidence.")
    if out["reasoning_arm"] not in ("on", "off", "auto"):
        raise SystemExit(f"REFUSED: reasoning_arm is {out['reasoning_arm']!r} in "
                         f"{os.path.basename(path)}; legal values are on|off|auto.")
    return out


DECL = read_declaration()
REASONING_DECLARED = DECL["reasoning_arm"]
REASONING_DECLARED_IN = DECL["reasoning_declared_in"]
REASONING_RATIONALE = DECL.get("reasoning_rationale", "")

# THE OVERRIDE IS AN EXPERIMENT ARM, NOT A SECOND DEFAULT: when it is used the record says so, in
# `reasoning_source` and in `reasoning_changed_from_declaration`.
REASONING_OVERRIDE = os.environ.get("MC_REASONING_TEST_ARM", "").strip().lower() or None
if REASONING_OVERRIDE is not None and REASONING_OVERRIDE not in ("on", "off", "auto"):
    raise SystemExit(f"MC_REASONING_TEST_ARM must be on|off|auto, got {REASONING_OVERRIDE!r}")
REASONING = REASONING_OVERRIDE or REASONING_DECLARED


def reasoning_source():
    return "override (experiment arm)" if REASONING_OVERRIDE else f"declared in MC_DECLARATION.md"


def reasoning_changed_from_declaration():
    """A CABINET THAT CHANGES THIS BETWEEN RUNS IS A DIFFERENT INSTRUMENT -- so the change is stated."""
    return REASONING != REASONING_DECLARED


def reasoning_argv():
    """THE FLAG AS IT IS ACTUALLY PASSED, so the record carries the argv and not a summary of it.

    AND IT IS EMPTY WHEN THE BUILD DOES NOT CARRY THE FLAG. MEASURED ON THIS BOX: the declared default
    (mainline, build 10931) has NO `--reasoning`; the prism fork (build 10777) has it. A driver that
    appends it unconditionally fails every run on a build that does not know the argument, AND the failure
    reads like a broken model rather than like a bad argv -- so the binary is ASKED, once, and the answer
    travels in the record instead of being assumed either way.
    """
    return ["--reasoning", REASONING] if build_supports_reasoning() else []


def llama_server():
    """THE BINARY THAT WILL ACTUALLY BE EXECUTED -- read at CALL TIME, so a selection made in main()
    reaches the launch AND the record, rather than only the launch."""
    return LLAMA_SELECTED or LLAMA


def binary_source():
    """WHICH SELECTOR CHOSE THE BINARY. A module cannot tell that its own constant was patched, so this
    says which selector was used and the DIGEST says which binary ran. Two fields, two facts."""
    return "--llama-server" if LLAMA_SELECTED else "no selector given: the module constant LLAMA"


def server_binary_digest():
    """sha256 of the BINARY THAT WILL ACTUALLY RUN -- one definition, so the record, the gate's identity
    and the console line cannot disagree about which binary answered."""
    return file_digest(llama_server())


def _help_says_flag(txt, flag, value):
    """DOES `--help` OFFER `flag` WITH `value` AS ONE OF ITS ENUMERATED VALUES?

    THE SINGLE DEFINITION OF "THE BUILD HAS THIS FLAG", and it exists because the naive version of this
    question was WRONG TWICE IN ONE RUN: a plain substring test said mainline carries `--reasoning` when
    what it carries is `--reasoning-format` (a different flag), and the sentence I drew from a three-line
    read of that help text was false as well. A READER BROAD ENOUGH TO FIND A FLAG THAT IS NOT THERE is the
    defect this project keeps removing, so the test requires the flag AND its value enumeration.
    """
    return bool(re.search(re.escape(flag) + r"\b\s*\[?\s*" + re.escape(value) + r"\b", txt or ""))


def _help_says_reasoning(txt):
    return _help_says_flag(txt, "--reasoning", "on")


def _help_says_fit(txt):
    return _help_says_flag(txt, "--fit", "on")


def _build_help(binary=None):
    """THE BINARY'S OWN --help, READ ONCE PER PATH. None means IT COULD NOT BE ASKED -- reported as unknown
    rather than folded into either answer."""
    b = binary or llama_server()
    if b not in _HELP_CACHE:
        try:
            out = subprocess.run([b, "--help"], capture_output=True, text=True, timeout=120)
            _HELP_CACHE[b] = (out.stdout or "") + (out.stderr or "")
        except Exception:                                               # noqa: BLE001
            _HELP_CACHE[b] = None
    return _HELP_CACHE[b]


def build_supports_reasoning(binary=None):
    """DOES THIS BUILD CARRY `--reasoning`? ASKED, NOT ASSUMED.

    True / False / None, and None means THE BINARY COULD NOT BE ASKED -- which is reported as unknown
    rather than folded into either answer. When it is not True the flag is NOT passed: an argv a build
    rejects produces a launch failure that reads like a broken model.

    AND THE FIRST VERSION OF THIS CHECK WAS WRONG TWICE, BOTH TIMES MEASURED RATHER THAN PREDICTED, AND
    BOTH TIMES BY THE CONTROL RATHER THAN BY READING:

      (a) IT WAS A SUBSTRING TEST (`"--reasoning" in help`) AND IT WAS TOO BROAD -- `--reasoning-format` is
          a different flag and satisfies it. Two controls failed on the first run.
      (b) AND THE CLAIM I DREW FROM IT WAS FALSE: I read `grep -i reasoning | head -3` and concluded
          mainline has no `--reasoning`. It HAS it, at line 630 of its own --help (`-rea, --reasoning
          [on|off|auto]`). A TRUNCATED READ IS NOT A READ -- the same defect as the substring test, one
          layer up, and it is recorded here rather than quietly corrected.

    So the matcher is its own function, and it is controlled against synthetic help text as well as
    against the two binaries on this box.
    """
    b = binary or llama_server()
    if (b, "reasoning") not in _FLAG_CACHE:
        txt = _build_help(b)
        _FLAG_CACHE[(b, "reasoning")] = None if txt is None else _help_says_reasoning(txt)
    return _FLAG_CACHE[(b, "reasoning")]


def build_supports_fit(binary=None):
    """DOES THIS BUILD CARRY `--fit`? Same rule, same reason: asked, never assumed.

    WHY THIS ONE MATTERS, MEASURED (2026-10-17, three entrants): with the flag NOT passed, three ordinary
    gguf files ABORTED AT LOAD with rc=-6 -- and the log names the cause, `CUDA error: out of memory`,
    inside `common_params_fit_impl`. THE CABINET IS CPU-ONLY (`-ngl 0`), so it needs NO device memory and
    the failure is entirely produced by the FIT PROBE asking the card how much of it it may use. On this
    box the card is held by other tenants (measured: 7650 MiB held across four processes with no lease
    traced to them), so the probe aborts the process before a single weight is read, and the failure reads
    like a model that cannot load. `--fit off` removes the probe; nothing else about the run changes.
    """
    b = binary or llama_server()
    if (b, "fit") not in _FLAG_CACHE:
        txt = _build_help(b)
        _FLAG_CACHE[(b, "fit")] = None if txt is None else _help_says_fit(txt)
    return _FLAG_CACHE[(b, "fit")]


def fit_argv():
    """THE FIT FLAG AS IT IS ACTUALLY PASSED -- empty when the build does not carry it."""
    return ["--fit", "off"] if build_supports_fit() else []


def fit_scope():
    s = build_supports_fit()
    if s is True:
        return ("--fit off IS passed: the cabinet is CPU-ONLY (-ngl 0), so the fit probe can only ask the "
                "DEVICE a question whose answer the run does not depend on -- and on a card held by other "
                "tenants it aborts the process (measured: three files, `CUDA error: out of memory` inside "
                "common_params_fit_impl, before any weight was read).")
    if s is False:
        return ("THE BUILD DOES NOT CARRY `--fit`, so the probe cannot be disabled from here: a load "
                "failure on a full card is possible and its log should be read for the OOM cause.")
    return "THE BUILD COULD NOT BE ASKED about `--fit`, so it is not passed."


def reasoning_argv_scope():
    s = build_supports_reasoning()
    if s is True:
        return "the build carries --reasoning, so the declared arm is passed"
    if s is False:
        return ("THE BUILD DOES NOT CARRY `--reasoning` (absent from its own --help), so the flag is NOT "
                "passed and the arm in force is the model's own default -- the PROBE is what reports it")
    return "THE BUILD COULD NOT BE ASKED (its --help did not run), so the flag is NOT passed and the arm is the model's own default"


def binary_provenance():
    """THE BINARY IN THREE OR PORTABLE VALUES: its digest, what the digest is a digest OF, the selector,
    and the reasoning-flag support, because a flag a build does not know is a launch failure that reads
    like a broken model. A path names one build and can hold another, which is why the digest travels."""
    return {"server_binary_digest": server_binary_digest(),
            "server_binary_digest_scope": ("sha256 of the BINARY FILE, first 16 hex. THE BINARY IS PART OF "
                                           "THE INSTRUMENT: a path can name one build and hold another."),
            "server_binary_source": binary_source(),
            "server_binary_path": llama_server()}


def ternary_entrant(path):
    """DOES THIS FILE BELONG TO THE FAMILY THE DECLARED DEFAULT MUST NOT SERVE? A NAME TEST, AND IT IS
    DECLARED AS ONE -- it is the only signal available before the file is opened, and the failure it
    prevents is measured rather than hypothetical. It is not evidence about the model; it is a triage."""
    return any(m in os.path.basename(path).lower() for m in TERNARY_MARKERS)


def binary_guard(entrant):
    """-> (ok, message). REFUSES TO SERVE A BONSAI TERNARY GGUF THROUGH THE DECLARED DEFAULT BINARY.

    THE REMEDY IS THE FLAG, NOT AN OVERRIDE: `--llama-server <path>` names the instrument, the record
    carries its digest, and the choice is then visible instead of monkey-patched.
    """
    if ternary_entrant(entrant) and not LLAMA_SELECTED:
        return False, (
            f"REFUSED: {os.path.basename(entrant)} looks like a Bonsai ternary gguf and NO --llama-server "
            f"was given, so this run would be served by {LLAMA}.\n"
            f"  MAINLINE LOADS THESE FILES AND EMITS DEGENERATE GARBAGE -- it does not apply the prism "
            f"hadamard transform the file declares -- and on this box the 4B ternary file is refused "
            f"outright by the default build. A preset cannot pin a binary.\n"
            f"  USE THE FORK:  --llama-server {FORK_LLAMA}\n"
            f"  Nothing has been spawned and nothing has been written.")
    return True, ""


def server_argv(entrant, ctx, port):
    """THE WHOLE LAUNCH, in one place, so what is recorded is what was run. The binary comes from
    `llama_server()`, not from the constant directly."""
    return ([llama_server(), "-m", entrant, "-c", str(ctx), "-ngl", "0", "--port", str(port), "--no-webui"]
            + reasoning_argv() + fit_argv())


# ==================================================================================================
# THE LEGEND, AND WHAT IT MAY NOT CONTAIN.
#
# THE MENU LESSON: chess failed because the prompt listed the LEGAL MOVES -- the answer set -- so the
# entrant chose from a menu instead of deriving candidates. So this legend names the MACHINE and never a
# move: the format of an answer, the rule that a threat landing on a city destroys it and one landing on
# empty ground does not, that ammo is finite, that a silo has a reach of 4, and that the tick advances.
#
# --------------------------------------------------------------------------------------------------
# TWO ARMS, BOTH KEPT VERBATIM, AND THE SECOND ONE EXISTS BECAUSE THE FIRST ONE WAS MEASURED.
#
# `example` IS THE ARM EVERY RECORD BEFORE 2026-10-17 WAS TAKEN UNDER, and its format example is drawn
# from OUTSIDE every frozen state -- `3W` names a silo that does not exist and a threat that does not
# exist, in either state -- which was the intent: teach the SHAPE without naming an answer. IT DID NOT
# DO THAT. MEASURED, and the reason this file now carries two arms:
#
#   Ternary-Bonsai-2-4B (fork)    pass-only, never fires         0/1 and 0/4
#   granite-3.3-2b (default)      PASS PASS then `3W` x4         0/4, `unknown` 4
#   Qwen3.5-2B (default)          `3P` x3  and  `3X 3X 3X 3Q 3P 3T`   0/1 and 0/4, `unknown` 3 and 6
#
# THREE ENTRANTS, AND THE SILO DIGIT THEY EMIT IS THE LEGEND'S OWN EXAMPLE DIGIT (`3`) IN EVERY SINGLE
# FIRING TOKEN, WHILE THE THREAT LETTERS ARE READ CORRECTLY FROM THE STATE. The example did not teach
# only the shape -- it supplied a value, and `3` is the only silo number that appears anywhere in the
# prompt. A legend that hands over a value is the chess move-list defect one layer down: not the whole
# answer set, just one cell of it.
#
# SO THE TWO ARMS ARE AN A/B, NOT A REPLACEMENT: the old arm is kept VERBATIM (a paraphrased control is
# not a control), the prediction is pre-registered in `PREREG_mc_legend_ab.md` BEFORE the second arm was
# ever run, and the arm is selected at CALL TIME so one process can do both. `example` remains the
# DEFAULT, so every existing record keeps the instrument it was taken under and no published number moves.
# ==================================================================================================
PROMPT_EXAMPLE = (
    "You are playing Missile Command. Enemy missiles are falling towards a line of positions numbered "
    "0 to 9. Your cities sit at fixed positions on that line and each threat line tells you the position "
    "where that missile will land and the tick it lands on. A missile that lands on a city destroys it. A "
    "missile that lands on empty ground does nothing at all, so a threat you leave alone may cost you "
    "nothing.\n\n"
    "You have silos on their own fixed positions, each holding a limited number of interceptors, and a "
    "silo can only reach a landing position within four of its own position. Each turn you may fire one "
    "interceptor from one silo at one threat, or you may fire nothing. Interceptors are scarce: spending "
    "one on a threat that could not have hurt you means it is not there when a city needs it. Every turn "
    "the tick advances by one, and any missile whose landing tick has arrived lands.\n\n"
    "{state}\n\n"
    "The actions you have already taken are: {recent}\n\n"
    "Answer with exactly two characters: the number of the silo first, then the letter of the threat. "
    "3W would mean fire from silo 3 at a threat called W -- no silo 3 and no threat W exist here, that is "
    "only the shape of an answer. If you want to fire nothing this turn, answer with the single word "
    "PASS. You may add an explanation after your answer, and it will be ignored."
)

# THE CANDIDATE ARM: THE SAME LEGEND WITH NO CONCRETE EXAMPLE IN IT. Every rule, every sentence and every
# instruction is byte-identical to the arm above EXCEPT the example clause, which is replaced by a
# statement of the SHAPE with no digits and no letters of its own -- so the only silo numbers and the only
# threat letters in the prompt are the ones in the state and in `PASS`.
PROMPT_PLAIN = PROMPT_EXAMPLE.replace(
    "Answer with exactly two characters: the number of the silo first, then the letter of the threat. "
    "3W would mean fire from silo 3 at a threat called W -- no silo 3 and no threat W exist here, that is "
    "only the shape of an answer. If you want to fire nothing this turn, answer with the single word "
    "PASS. You may add an explanation after your answer, and it will be ignored.",
    "Answer with exactly two characters: the number of the silo you are firing from first, then the "
    "letter of the threat you are firing at. Those two values are in the state above -- use the silo "
    "numbers and the threat letters exactly as they are written there. If you want to fire nothing this "
    "turn, answer with the single word PASS. You may add an explanation after your answer, and it will "
    "be ignored.")

LEGEND_ARMS = {"example": PROMPT_EXAMPLE, "plain": PROMPT_PLAIN}
# THE RECORDED ARM IS DECLARED IN `MC_DECLARATION.md`, NOT DEFAULTED HERE -- the same rule the reasoning
# arm follows, for the same reason. The A/B is an experiment; it is selected at call time and recorded,
# and it does not move the declaration.
LEGEND_DEFAULT = DECL["legend_arm"]
if LEGEND_DEFAULT not in LEGEND_ARMS:
    raise SystemExit(f"REFUSED: the declaration names legend_arm {LEGEND_DEFAULT!r}; the arms defined in "
                     f"this driver are {tuple(LEGEND_ARMS)}.")
LEGEND_ARM = None                        # set by main()/the A/B caller; read at CALL TIME everywhere


def legend():
    """THE ARM, read at CALL TIME so a single process can run both sides of the A/B."""
    return LEGEND_ARM or LEGEND_DEFAULT


def legend_source():
    return ("selected at call time (--legend or MC_LEGEND)" if LEGEND_ARM
            else f"the recorded default ({LEGEND_DEFAULT})")


def legend_digest(arm=None):
    """THE ARM A RECORD WAS TAKEN UNDER, carried with the record: without it two records produced by
    different prompts are indistinguishable files."""
    return hashlib.sha256(LEGEND_ARMS[arm or legend()].encode()).hexdigest()[:16]


def legend_arm_digests():
    """BOTH ARMS' DIGESTS, so a reader can see the two files differ and by which instrument."""
    return {a: legend_digest(a) for a in LEGEND_ARMS}


def prompt_for(screen, history):
    recent = " ".join(history) if history else "none yet"
    return LEGEND_ARMS[legend()].replace("{state}", screen).replace("{recent}", recent)


# ==================================================================================================
# THE SCREEN -- DERIVED FROM THE SIMULATOR'S OWN RESOLUTION, NEVER FROM A SECOND COPY OF THE RULES.
#
# `missile_command.py` has no `render()` and no `step()`: its one entry point is `play(state_text,
# actions)`, which resolves the whole volley. So the driver resolves the PREFIX of the action stream with
# the frozen simulator and rebuilds the screen from ITS OWN last trace row (cities alive, ammo, threats
# remaining) plus the ORIGINAL state's threat table (impact and tick, which never change). Re-running the
# rules here would be a second definition of the game -- the exact defect this project keeps removing.
# ==================================================================================================
def initial_view(state_text):
    st = S.parse_state(state_text)
    return {"tick": st["tick"],
            "cities": dict(st["cities"]),
            "silos": {k: {"at": v["at"], "ammo": v["ammo"]} for k, v in st["silos"].items()},
            "threats": {k: dict(v) for k, v in st["threats"].items()}}


def advance_view(state_text, tokens):
    """THE VIEW AFTER `tokens` -- from the frozen simulator's own last row."""
    if not tokens:
        return initial_view(state_text)
    st = S.parse_state(state_text)
    row = S.play(state_text, tokens)["trace"][-1]
    alive = set(row["cities_alive"])
    return {"tick": row["tick"],
            "cities": {c: x for c, x in st["cities"].items() if c in alive},
            "silos": {k: {"at": st["silos"][k]["at"], "ammo": row["ammo"][k]} for k in st["silos"]},
            "threats": {k: dict(st["threats"][k]) for k in row["threats_remaining"]}}


def render_view(view):
    """THE FROZEN STATE FORMAT, rebuilt: line-oriented text, so a state travels in a message and diffs in
    git. Sorted by name, so the screen is a function of the state and not of dict order."""
    lines = [f"tick {view['tick']}"]
    lines += [f"city {c} at {view['cities'][c]}" for c in sorted(view["cities"])]
    lines += [f"silo {k} at {view['silos'][k]['at']} ammo {view['silos'][k]['ammo']}"
              for k in sorted(view["silos"])]
    lines += [f"threat {t} impact {view['threats'][t]['impact']} tick {view['threats'][t]['tick']}"
              for t in sorted(view["threats"])]
    return "\n".join(lines)


def clock_audit():
    """THE INTERFACE DECISION, RE-MEASURED RATHER THAN ASSERTED: does the frozen simulator contain a
    wall-clock term? A claim in a comment is not a measurement, so the file is READ and the terms found
    are listed. An empty list is the finding; a non-empty one is recorded as one too."""
    src = open(os.path.join(HERE, "missile_command.py"), encoding="utf-8").read()
    terms = ("import time", "from time", "time.", "sleep", "monotonic", "perf_counter", "datetime",
             "clock")
    found = []
    for i, line in enumerate(src.splitlines(), 1):
        if line.strip().startswith("#"):
            continue                                        # a comment ABOUT time is not a time term
        for t in terms:
            if t in line:
                found.append({"line": i, "term": t, "text": line.strip()[:100]})
    return {"simulator": "missile_command.py", "simulator_digest": file_digest(os.path.join(HERE, "missile_command.py")),
            "wall_clock_terms_found": found,
            "reading": ("NO WALL-CLOCK TERM EXISTS IN THE FROZEN SIMULATOR -- the play mode is turn-based "
                        "by construction, so step-locking the clock is not a change this cabinet could "
                        "make: there is nothing to lock. The only clock is the state's own `tick` integer, "
                        "advanced one per action." if not found else
                        "WALL-CLOCK TERMS WERE FOUND -- the turn-based claim above is FALSE for this "
                        "instrument and the record must be read with that in mind.")}


def clock_cap(state_text):
    """THE COMMAND CAP IS DERIVED FROM THE STATE'S OWN HORIZON, so a run cannot be cut off before the
    volley it is being measured on has resolved: every threat lands by the maximum tick in the state, and
    two turns of margin let a correct play still be visible."""
    st = S.parse_state(state_text)
    return max(t["tick"] for t in st["threats"].values()) + 2


# --------------------------------------------------------------------------------- networking
def ask(base, screen, history, timeout_s=300):
    """ONE TURN. The answer is read by the READER OF RECORD -- `is_answer` is the field a scorer gates on,
    and a trace is never an answer."""
    body = json.dumps({"messages": [{"role": "user", "content": prompt_for(screen, history)}],
                       "max_tokens": MAX_TOKENS, "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
    except Exception as e:                                              # noqa: BLE001
        return read_answer({}, exception=e), time.time() - t0
    return read_answer(j), time.time() - t0


def first_token(text):
    """THE ANSWER IS AT THE HEAD -- the first line, and one token from it. Nothing is mined from prose."""
    for line in (text or "").splitlines():
        line = line.strip()
        if line and line.split():
            return line.split()[0]
    return ""


def probe_reasoning(base, timeout_s=180):
    """ASK ONCE, BRIEFLY, BEFORE THE FIELD -- and record OBSERVED beside REQUESTED, because a config field
    nobody measured is the same class as a legend nobody read. LENGTH AND INFERENCE ARE TWO FIELDS: the
    measurement is what came out, the inference is labelled as an inference (a long answer is not
    necessarily deliberation -- a model echoing the question in a schema is long too)."""
    q = "What is 2 + 2? Reply with just the number and nothing else."
    body = json.dumps({"messages": [{"role": "user", "content": q}], "max_tokens": MAX_TOKENS,
                       "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
    except Exception as e:                                              # noqa: BLE001
        return {"question": q, "error": f"{type(e).__name__}: {e}", "observed": None,
                "requested": REASONING, "disagrees_with_config": None}
    ans = read_answer(j)
    ctok = ans["completion_tokens"]
    observed = "off" if ctok <= 8 else "on"
    return {"question": q, "answer": ans["text"][:60],
            "answer_from_reasoning_field": bool(ans.get("trace_head") and not ans["text"]),
            "completion_tokens": ctok, "finish_reason": ans["finish_reason"],
            "observed_answer_shape": "short" if ctok <= 8 else "long",
            "shape_threshold_tokens": 8,
            "observed": observed,
            "observed_is_an_inference": True,
            "inference_caveat": ("a LONG answer is not necessarily deliberation -- a model that echoes the "
                                 "question in a schema produces a long answer too, and this probe cannot "
                                 "tell them apart"),
            "requested": REASONING,
            "disagrees_with_config": (REASONING != "auto" and observed != REASONING)}


def budget_signature(turns):
    """DID IT HIT THE CEILING, OR COULD IT NOT ANSWER? Different findings, and one has been published as
    the other. A `malformed` count is not a capability result until this has been read."""
    n = len(turns) or 1
    hit = sum(1 for t in turns if t.get("budget_hit"))
    return {"turns": len(turns), "turns_that_hit_the_ceiling": hit, "ceiling": MAX_TOKENS,
            "fraction_capped": round(hit / n, 3),
            "all_turns_capped": bool(turns) and hit == len(turns),
            "reading": ("BUDGET-CONFOUNDED -- every answer was cut off at the ceiling, so this is NOT a "
                        "capability result until it is re-run with room" if turns and hit == len(turns)
                        else "some turns hit the ceiling -- see the per-turn rows" if hit
                        else "no turn hit the ceiling -- the answers are the model's own endings")}


def cap_cut_statement(hit, answer_present):
    """WHAT THE CAP CUT. `finish_reason=length` describes the HARNESS, not the model: measured elsewhere,
    the same task returned `length` at 1200, 2048 and 4096 tokens and was CORRECT at every size."""
    if not hit:
        return "nothing -- the model stopped on its own"
    if not answer_present:
        return ("THE ANSWER -- deliberation consumed the ceiling before any answer was reached. THIS IS "
                "THE ONE CASE WHERE `length` MEANS THE MODEL DID NOT ANSWER.")
    return ("SURPLUS AFTER AN ANSWER -- the answer is present and readable; the cap cut what followed it. "
            "NOT a failed turn.")


# --------------------------------------------------------------------------------- load failures
FILE_REFUSAL_SIGNATURES = ("gguf_init_from_reader", "llama_model_loader", "invalid ggml type",
                           "invalid magic characters", "failed to read tensor info",
                           "done_getting_tensors", "unknown model architecture")
# THE OTHER CAUSE A LOG CAN NAME, AND IT IS NOT ABOUT THE FILE AT ALL. MEASURED (2026-10-17): three
# ordinary gguf files aborted at load with rc=-6 while their logs read `CUDA error: out of memory` from
# inside `common_params_fit_impl` -- the FIT PROBE asking a card that other tenants are holding. The first
# version of this classifier had no class for it, so it reported "no cause named by the log" about a log
# that named one, and pointed the reader at the tenants (which is RULING 82's sentence, correct for the
# case it was ratified for) while the actual cause sat two lines above it. TWO CONDITIONS, TWO SENTENCES.
DEVICE_OOM_SIGNATURES = ("CUDA error", "HIP error", "out of memory", "failed to allocate",
                         "insufficient device memory", "unable to allocate")


def load_failure(log_path, status):
    """-> {"why":..., "load_failure_class":...}. THREE CLASSES, DECIDED BY A READING OF THE SERVER'S OWN
    LOG, WITH THE MATCHED LINE QUOTED AND NUMBERED so a reader can overrule the class from the carrier.

      file_refusal -- the binary cannot READ the file (the log quotes the reader's refusal)
      device_oom   -- the DEVICE has no room. A TENANCY CONDITION, NOT A MODEL CONDITION, and it is
                      reported as one, with the holders named by vram_holder (RULING 82)
      no_cause     -- the log names nothing of its own, which is exactly the case RULING 82's
                      unconditional holder sentence was ratified for
    """
    try:
        lines = open(log_path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        lines = None
    quoted = None
    for sigs, kind in ((FILE_REFUSAL_SIGNATURES, "file_refusal"),
                       (DEVICE_OOM_SIGNATURES, "device_oom")):
        for i, ln in enumerate(lines or [], 1):
            if any(sig in ln for sig in sigs):
                quoted = (kind, i, ln.strip())
                break
        if quoted:
            break
    if quoted and quoted[0] == "file_refusal":
        return {"load_failure_class": "the binary refused the FILE (the log names the cause)",
                "why": (f"{status}.{os.linesep}THE BINARY REFUSED THE FILE -- log line {quoted[1]}, quoted "
                        f"verbatim: {quoted[2]}{os.linesep}"
                        f"  AND THE HOLDER SENTENCE IS NOT REPORTED HERE: RULING 82's sentence is appended "
                        f"when the log names no cause of its own, and this log names one. An unconditional "
                        f"tenancy report for a file the binary cannot read points the reader at the wrong "
                        f"subsystem.")}
    holder = (holder_sentence() if holder_sentence
              else "(vram_holder.py was not found, so the holder is NOT named here)")
    if quoted:
        return {"load_failure_class": "the DEVICE has no room -- a TENANCY condition, not a model condition",
                "why": (f"{status}.{os.linesep}THE LOG NAMES THE CAUSE -- log line {quoted[1]}, quoted "
                        f"verbatim: {quoted[2]}{os.linesep}"
                        f"  THIS IS NOT A STATEMENT ABOUT THE MODEL: the cabinet runs CPU-ONLY (-ngl 0), "
                        f"and the log shows the failure inside the fit/memory probe rather than in a "
                        f"tensor read. The driver passes `--fit off` when the build carries it (see "
                        f"config.fit_scope), so a failure that survives that is a genuine device-memory "
                        f"condition.{os.linesep}  AND THE CARD AT FAILURE IS HELD BY (RULING 82): "
                        f"{holder}")}
    if lines is None:
        return {"load_failure_class": "unknown -- the server's log could not be read",
                "why": f"{status}.{os.linesep}THE SERVER'S LOG COULD NOT BE READ, so which condition this "
                       f"is cannot be decided from here -- an unreadable cause is reported as unreadable, "
                       f"never as absent."}
    tail = os.linesep.join(lines[-6:])
    return {"load_failure_class": "no cause named by the log: the card at failure is what is reported",
            "why": (f"{status}.{os.linesep}{holder}{os.linesep}"
                    f"  AND THE LOG NAMES NO CAUSE OF ITS OWN. Its last lines, quoted:{os.linesep}{tail}")}


# --------------------------------------------------------------------------------- the artifact gate
ARTIFACT_OVERRIDE = None
IDENTITY_IN_RECORD = ("server_binary_digest", "legend_digest", "reasoning")


def cell_labels(entrant, state_path):
    return (os.path.basename(entrant).replace(".gguf", ""),
            os.path.basename(state_path).replace(".txt", ""))


def artifact_path(entrant, state_path):
    """THE ONE DEFINITION OF THE ARTIFACT'S COORDINATE -- the gate and the writer both use it, so the path
    refused on and the path written cannot be two different paths."""
    label, sname = cell_labels(entrant, state_path)
    return os.path.join(HERE, "probes", f"MC_{label}_{sname}.json")


def run_identity():
    return {"server_binary_digest": server_binary_digest(), "legend_digest": legend_digest(), "reasoning": REASONING}


def carried_identity(d):
    """-> the same three values AS AN EXISTING RECORD CARRIES THEM, or None for one it does not carry. None
    IS NOT A MATCH: a run cannot show it is the same instrument as a record that names no instrument."""
    cfg = d.get("config") if isinstance(d.get("config"), dict) else {}
    return {k: (d[k] if k in d else cfg.get(k)) for k in IDENTITY_IN_RECORD}


def artifact_gate(out, reason, old_bytes=None):
    """-> (ok, message, replaced). ONE RUN, ONE PATH: a run refuses to replace a record it did not take,
    and the only way past is to say WHY, with the reason written into the record that does the replacing."""
    if not os.path.exists(out):
        return True, "", None
    if old_bytes is None:
        old_bytes = open(out, "rb").read()
    try:
        old = json.loads(old_bytes.decode())
    except (OSError, ValueError):
        old = None
    rel = os.path.relpath(out, HERE)
    if reason is not None:
        return True, "", {"path": rel, "sha256": hashlib.sha256(old_bytes).hexdigest(),
                          "bytes": len(old_bytes),
                          "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(out))),
                          "it_named": carried_identity(old) if isinstance(old, dict) else "UNREADABLE AS JSON",
                          "reason_given": reason,
                          "reading": ("THIS RUN REPLACED THE RECORD AT THIS PATH. The replaced record is "
                                      "NOT recoverable from this file: what survives is that it existed, "
                                      "the digest of the bytes it was, and what it said about its own "
                                      "instrument.")}
    theirs = carried_identity(old) if isinstance(old, dict) else {
        k: "UNREADABLE" for k in IDENTITY_IN_RECORD}
    diff = [k for k in IDENTITY_IN_RECORD if theirs[k] != run_identity()[k]]
    return False, (
        f"REFUSED: {rel} ALREADY HOLDS A RECORD, AND A RUN DOES NOT REPLACE A RECORD IT DID NOT TAKE."
        f"{os.linesep}  it says about itself  "
        + "  ".join(f"{k}={theirs[k]!r}" for k in IDENTITY_IN_RECORD)
        + f"{os.linesep}  this run would write  "
        + "  ".join(f"{k}={run_identity()[k]!r}" for k in IDENTITY_IN_RECORD)
        + (f"{os.linesep}  AND THESE DO NOT MATCH: {diff}" if diff else
           f"{os.linesep}  SAME INSTRUMENT, SAME ARMS -- and the replacement is still refused: the same "
           f"instrument twice is not the same record.")
        + f"{os.linesep}  THE REMEDY IS A REASON, NOT A FORCE:  --overwrite-artifact \"<why>\""
          f"{os.linesep}  NOTHING HAS BEEN WRITTEN, NO SERVER HAS BEEN STARTED AND NOTHING CONSUMED."), None


# --------------------------------------------------------------------------------- sufficiency
def sufficiency_check(state_text, tokens, screens, final_screen, score):
    """GAME_CONTRACT, MADE CHECKABLE: *the recorded state must be a SUFFICIENT STATISTIC for the score --
    the scored outcome can be recomputed from the recorded state alone.*

    AND THE CONTROL CAN FAIL, WHICH IS THE POINT: it re-derives the score and EVERY screen from
    `(state_text, tokens)` with the frozen simulator and compares them with what was recorded. If the
    driver had rendered a screen from anything other than the simulator's own resolution, this is where it
    would show -- so the reading is allowed to be a failure.
    """
    replay = S.play(state_text, tokens)
    rebuilt = [render_view(initial_view(state_text))]
    for k in range(1, len(tokens) + 1):
        rebuilt.append(render_view(advance_view(state_text, tokens[:k])))
    want = list(screens) + [final_screen]
    same = sum(1 for a, b in zip(rebuilt, want) if a == b)
    return {"score_recomputed_from_state_and_actions": replay["cities_surviving"],
            "score_matches_the_record": replay["cities_surviving"] == score,
            "screens_rebuilt": f"{same}/{len(want)}",
            "screens_reproduce": same == len(want) and len(rebuilt) == len(want),
            "reading": ("THE RECORD IS SUFFICIENT: the score and every screen the entrant saw recompute "
                        "from (state_text, tokens) under the frozen simulator."
                        if replay["cities_surviving"] == score and same == len(want) and len(rebuilt) == len(want)
                        else "THE RECORD IS NOT SUFFICIENT FOR ITS OWN DISPLAY: a re-derivation disagrees "
                             "with what was recorded, so the divergence is the finding.")}


# --------------------------------------------------------------------------------- the run
def resolve_state(path):
    """A state path or a bare name in this cabinet's levels/."""
    for p in (path, os.path.join(HERE, "levels", path), os.path.join(HERE, "levels",
                                                                    os.path.basename(path))):
        if os.path.exists(p):
            return p
    return None


def run(entrant, state_path, cap, port):
    state_text = open(state_path, encoding="utf-8").read()
    label, sname = cell_labels(entrant, state_path)

    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    # THE ARM IS IN THE LOG NAME -- BOTH ARMS, AND THE BINARY TOO. The first version carried the legend
    # and the reasoning arm and NOT the binary, and that cost a record: a fork run OVERWROTE the
    # mainline run's log for the same cell (MEASURED 2026-10-17, granite, both states), which is FINDING
    # 018/020 one layer down -- an artifact whose identity is its path, destroyed by the next thing that
    # writes that path. The ARTIFACT's name is the published coordinate and does not move; the LOG's name
    # carries everything the coordinate cannot.
    log = os.path.join(HERE, "logs",
                       f"MC_{label}_{sname}_{legend()}_rea-{REASONING}"
                       f"_bin-{(server_binary_digest() or 'nohash')[:8]}.log")
    srv = subprocess.Popen(server_argv(entrant, CTX, port), stdout=open(log, "w"),
                           stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        t0 = time.time()
        up = False
        while time.time() - t0 < 600:
            if srv.poll() is not None:
                return {"entrant": label, "entrant_digest": file_digest(entrant),
                        "level": sname, "loaded": False,
                        "state_digest": file_digest(state_path),
                        "state_path": os.path.relpath(state_path, HERE),
                        **load_failure(log, f"server exited rc={srv.returncode}"), **binary_provenance()}
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                up = True
                break
            except Exception:                                           # noqa: BLE001
                time.sleep(3)
        if not up:
            return {"entrant": label, "entrant_digest": file_digest(entrant), "level": sname,
                    "state_digest": file_digest(state_path),
                    "state_path": os.path.relpath(state_path, HERE),
                    "loaded": False, **load_failure(log, "never answered /health in 600 s"),
                    **binary_provenance()}
        load_s = time.time() - t0

        # THE PROBE RUNS BEFORE A SINGLE GAME TURN.
        probe = probe_reasoning(base)

        tokens, turns, screens, history = [], [], [], []
        missing_values, ended, ended_why = 0, None, None
        screen = render_view(initial_view(state_text))
        for i in range(cap):
            ans, secs = ask(base, screen, history)
            tok = first_token(ans["text"])
            is_missing = not ans["is_answer"]
            screens.append(screen)
            turns.append({"ply": i, "raw": (ans["text"] or "")[:400], "token": tok,
                          "secs": round(secs, 1), "gen_tokens": ans["completion_tokens"],
                          "budget_hit": ans["finish_reason"] == "length",
                          "cap_cut": cap_cut_statement(ans["finish_reason"] == "length", bool(tok)),
                          "answer_field": ans["field"], "missing_value": is_missing,
                          "screen_before": screen})
            if is_missing:
                # AN EMPTY THE HARNESS PRODUCED IS A MISSING VALUE, NEVER A TOKEN: it is not passed to the
                # simulator, so it can never be counted as an illegal move, a zero or a wrong answer.
                missing_values += 1
                ended = "budget_confounded" if ans["finish_reason"] == "length" else "missing_value"
                ended_why = (f"turn {i} produced NO ANSWER -- the reader of record reports field "
                             f"{ans['field']!r} ({ans.get('why', '')}). "
                             + ("The turn was CUT AT THE CEILING while deliberating, so this is a harness "
                                "result, not a capability result until it is re-run with room."
                                if ans["finish_reason"] == "length" else
                                "The model produced no answer field."))
                break
            history.append(tok)
            tokens.append(tok)
            row = S.play(state_text, tokens)["trace"][-1]
            if not row["threats_remaining"]:
                ended = "threats_resolved"
                ended_why = f"every threat has been resolved by tick {row['tick']}"
            screen = render_view(advance_view(state_text, tokens))
            if ended:
                break
        if ended is None:
            ended = "command_cap_reached"
            ended_why = f"the command cap ({cap}) was reached with threats still airborne"

        r = S.play(state_text, tokens)
        for i, row in enumerate(r["trace"]):                # one simulator row per token, in order
            turns[i].update({"tick": row["tick"], "outcome": row["outcome"], "outcome_note": row["note"],
                             "cities_alive": row["cities_alive"], "ammo": row["ammo"],
                             "threats_remaining": row["threats_remaining"]})
        st0 = S.parse_state(state_text)
        r = dict(r)
        r.update({
            "entrant": label, "entrant_digest": file_digest(entrant),
            "entrant_digest_scope": ("sha256 of the model FILE, first 16 hex. THE ENTRANT IS THE SUBJECT OF "
                                     "THE MEASUREMENT, so it is identified by a digest; `entrant` beside it "
                                     "is a LABEL, for reading, not for checking."),
            "level": sname, "state_path": os.path.relpath(state_path, HERE),
            "state_text": state_text,
            "state_digest": file_digest(state_path),
            "simulator_digest": file_digest(os.path.join(HERE, "missile_command.py")),
            "simulator_digest_scope": "sha256 of missile_command.py, first 16 hex -- THE SIMULATOR IS PART OF THE INSTRUMENT",
            "legend": legend(), "legend_digest": legend_digest(),
            "legend_arms": legend_arm_digests(),
            "legend_source": legend_source(),
            "legend_scope": ("sha256 of the PROMPT TEMPLATE, first 16 hex; the state is filled in per turn. "
                             "BOTH arms are digested, because a comparison between two records whose "
                             "difference is invisible is a comparison between two files taken on trust."),
            "prompt_turn0": prompt_for(screens[0], []),
            "loaded": True, "load_s": round(load_s, 1),
            "tokens": tokens, "turns": turns, "screens": screens,
            "final_screen": screen, "command_cap": cap,
            "command_cap_source": "max impact tick in the state + 2" if cap == clock_cap(state_text)
                                  else "given on the command line",
            "ended": ended, "ended_why": ended_why,
            "cities_total": len(st0["cities"]),
            "score": r["cities_surviving"],
            "missing_values": missing_values,
            "missing_values_are_not_tokens": ("a missing value is never passed to the simulator, so it can "
                                              "never be scored as a wrong move -- the empty-list rule"),
            "unreadable": r["counts"]["malformed"],
            "unreadable_is_a_simulator_outcome": ("`malformed` is the simulator's own outcome for a token "
                                                  "that is not an action: COUNTED, NEVER SCORED AS A WRONG "
                                                  "MOVE -- the board is unchanged and the tick advances. "
                                                  "`unknown`, `late`, `out_of_range` and `no_ammo` are four "
                                                  "DIFFERENT claims and are never merged into it."),
            "never_started": 0,
            "budget_signature": budget_signature(turns),
            "protocol": {"play_mode": "step_locked", "action_format": "<silo><threat> or PASS",
                         "clock": "the state's own `tick` integer, advanced one per action",
                         "interface_decision": ("turn-based BY CONSTRUCTION -- missile_command.py carries no "
                                                "wall-clock term, so no frozen criterion was changed to "
                                                "make it turn-based (see clock_audit)"),
                         "clock_audit": clock_audit(),
                         "declaration_file": os.path.relpath(DECLARATION_FILE, HERE),
                         "declaration_digest": file_digest(DECLARATION_FILE),
                         "declaration": DECL},
            "sufficiency": sufficiency_check(state_text, tokens, screens, screen, r["cities_surviving"]),
            "config": {"reasoning": REASONING,
                       "reasoning_source": reasoning_source(),
                       "reasoning_declared": REASONING_DECLARED,
                       "reasoning_declared_in": REASONING_DECLARED_IN,
                       "reasoning_rationale": REASONING_RATIONALE,
                       "reasoning_changed_from_declaration": reasoning_changed_from_declaration(),
                       "reasoning_argv": reasoning_argv(),
                       "reasoning_argv_scope": reasoning_argv_scope(),
                       "reasoning_supported_by_build": build_supports_reasoning(),
                       "fit_argv": fit_argv(),
                       "fit_scope": fit_scope(),
                       "fit_supported_by_build": build_supports_fit(),
                       "max_tokens_ceiling": MAX_TOKENS,
                       "command_cap": cap,
                       "ctx": CTX, "n_gpu_layers": 0, "temperature": 0.0,
                       "legend": legend(), "legend_digest": legend_digest(),
                       "legend_arms": legend_arm_digests(), "legend_source": legend_source(),
                       "server_argv": server_argv(entrant, CTX, port),
                       **binary_provenance(), **reader_provenance()},
            "reasoning_probe": probe,
        })
        return r
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                               # noqa: BLE001
            srv.kill()


# --------------------------------------------------------------------------------- controls
def _self_test():
    fails = []
    ran = [0]                       # THE TOTAL IS COUNTED, NOT CARRIED -- a hand-written control count is
                                    # a count kept beside the thing it counts, and those drift.

    def ck(name, got, want):
        ran[0] += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 96)
    print("MISSILE COMMAND ENTRANT DRIVER -- CONTROLS")
    print("=" * 96)
    mc02 = open(resolve_state("mc_02_scarcity.txt"), encoding="utf-8").read()
    mc01 = open(resolve_state("mc_01_one_shot.txt"), encoding="utf-8").read()
    frz = S.play(mc02, ["PASS"] * 6)

    print("\n[1] THE FROZEN STATES ARE WHAT THE PREREG SAYS THEY ARE")
    ck("mc_02 has 4 cities, 8 threats, 4 rounds",
       (len(S.parse_state(mc02)["cities"]), len(S.parse_state(mc02)["threats"]),
        sum(v["ammo"] for v in S.parse_state(mc02)["silos"].values())), (4, 8, 4))
    ck("mc_01 is the floor: 1 city, 1 threat, 1 round",
       (len(S.parse_state(mc01)["cities"]), len(S.parse_state(mc01)["threats"]),
        sum(v["ammo"] for v in S.parse_state(mc01)["silos"].values())), (1, 1, 1))

    print("\n[2] THE THREE LINES THE PREREG MEASURED, RE-MEASURED -- the score is a measurement of reading")
    ck("passive (PASS every tick)            -> 0 / 4", frz["cities_surviving"], 0)
    ck("fire-at-cities (1P 1Q 2R 2S +PASS)  -> 4 / 4",
       S.play(mc02, ["1P", "1Q", "2R", "2S", "PASS", "PASS"])["cities_surviving"], 4)
    ck("fire-at-decoys (1X 2Y 2Z)           -> 0 / 4",
       S.play(mc02, ["1X", "2Y", "2Z", "PASS", "PASS", "PASS"])["cities_surviving"], 0)
    ck("the decoys are read: the city line SPARES threats and the decoy line does not",
       (S.play(mc02, ["1P", "1Q", "2R", "2S", "PASS", "PASS"])["counts"]["spared"], frz["counts"]["spared"]),
       (4, 4))

    print("\n[3] THE DRIVER'S SCREENS ARE A SUFFICIENT STATISTIC -- and the control CAN fail")
    toks = ["1P", "1Q", "2R", "2S"]
    scr = [render_view(initial_view(mc02))] + [render_view(advance_view(mc02, toks[:k]))
                                               for k in range(1, len(toks))]
    fin = render_view(advance_view(mc02, toks))
    sc = sufficiency_check(mc02, toks, scr, fin, 4)
    ck("the score recomputes from (state_text, tokens)", sc["score_matches_the_record"], True)
    ck("every screen reproduces", sc["screens_reproduce"], True)
    ck("...and a MUTILATED record does NOT reproduce (the control's own control)",
       sufficiency_check(mc02, toks, scr[:-1] + ["tick 99\ncity A at 2"], fin, 4)["screens_reproduce"], False)
    ck("...and a MUTILATED action stream does not reproduce the score",
       sufficiency_check(mc02, ["PASS"] * 6, scr, fin, 4)["score_matches_the_record"], False)

    print("\n[4] THE EMPTY-LIST RULE -- an unreadable token is COUNTED, never scored as a wrong move")
    junk = S.play(mc02, ["e2e4", "RESIGN", "1PP", "PASS", "PASS", "PASS"])
    ck("three junk tokens are `malformed`", junk["counts"]["malformed"], 3)
    ck("...and `RESIGN` is NOT truncated into an action", S.play(mc02, ["RESIGN"])["counts"]["malformed"], 1)
    ck("...and the board resolves exactly as the same number of PASSes would",
       (junk["cities_surviving"], junk["counts"]["hit"], junk["counts"]["spared"]),
       (frz["cities_surviving"], frz["counts"]["hit"], frz["counts"]["spared"]))

    print("\n[5] THE DECLARATION IS READ, AND AN UNDECLARED ARM IS REFUSED")
    d = read_declaration()
    ck("this cabinet's arm is declared", d["reasoning_arm"], REASONING_DECLARED)
    ck("...and it is one of the legal values", d["reasoning_arm"] in ("on", "off", "auto"), True)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "MC_DECLARATION.md")
        open(p, "w").write("cabinet missile-command\nreasoning_declared_in nowhere\n")
        try:
            read_declaration(p)
            ck("a declaration WITHOUT reasoning_arm is refused", "accepted", "SystemExit")
        except SystemExit:
            ck("a declaration WITHOUT reasoning_arm is refused", "SystemExit", "SystemExit")
        open(p, "w").write("cabinet missile-command\nreasoning_arm maybe\n")
        try:
            read_declaration(p)
            ck("an arm outside on|off|auto is refused", "accepted", "SystemExit")
        except SystemExit:
            ck("an arm outside on|off|auto is refused", "SystemExit", "SystemExit")
        open(p, "w").write("cabinet missile-command\nreasoning_arm off\nreasoning_declared_in here\n")
        try:
            read_declaration(p)
            ck("a declaration WITHOUT legend_arm is refused", "accepted", "SystemExit")
        except SystemExit:
            ck("a declaration WITHOUT legend_arm is refused", "SystemExit", "SystemExit")
        open(p, "w").write("cabinet missile-command\nreasoning_arm off\nreasoning_declared_in here\n"
                           "legend_arm example\n")
        ck("...and a fully declared one is accepted", read_declaration(p)["reasoning_arm"], "off")

    print("\n[6] THE BINARY TRAP IS A REFUSAL")
    global LLAMA_SELECTED
    keep = LLAMA_SELECTED
    LLAMA_SELECTED = None
    ck("a ternary entrant on the declared default is REFUSED",
       binary_guard("/m/MODELS/Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0.gguf")[0], False)
    ck("...and an ordinary gguf is not", binary_guard("/m/MODELS/Qwen3.5-4B-UD-Q4_K_XL.gguf")[0], True)
    LLAMA_SELECTED = "/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server"
    ck("...and the fork satisfies it rather than being reported",
       binary_guard("/m/MODELS/Ternary-Bonsai-2-4B-PQ2_0-MTP-Q8_0.gguf")[0], True)
    LLAMA_SELECTED = keep

    print("\n[6b] THE FLAG IS PASSED ONLY TO A BUILD THAT CARRIES IT -- ASKED, NOT ASSUMED")
    ck("the declared default build carries --reasoning", build_supports_reasoning(LLAMA), True)
    ck("...and the prism fork does too", build_supports_reasoning(FORK_LLAMA), True)
    ck("...and mainline's argv therefore carries the declared arm",
       ("--reasoning" in " ".join(server_argv("m.gguf", 4096, 1))), True)
    ck("the matcher is NOT fooled by --reasoning-format (a reader broad enough to find a thing that is "
       "not there)",
       _help_says_reasoning("--reasoning-format FORMAT   controls whether thought tags are allowed"),
       False)
    ck("...and it DOES see the real flag in synthetic help text",
       _help_says_reasoning("-rea,  --reasoning [on|off|auto]   Use reasoning/thinking in the chat"), True)
    ck("...and the same matcher is NOT fooled by --fit-ctx when asked about --fit",
       _help_says_fit("-fitc, --fit-ctx N   minimum ctx size that can be set by --fit option"), False)
    ck("...and it DOES see --fit on this box's builds",
       (build_supports_fit(LLAMA), build_supports_fit(FORK_LLAMA)), (True, True))
    ck("...and the CPU-only cabinet therefore passes --fit off",
       ("--fit" in " ".join(server_argv("m.gguf", 4096, 1))), True)

    print("\n[6c] A LOAD FAILURE IS CLASSIFIED FROM THE SERVER'S OWN LOG -- three conditions, three sentences")
    with tempfile.TemporaryDirectory() as td:
        def _log(name, text):
            p = os.path.join(td, name)
            open(p, "w").write(text)
            return p
        fr = load_failure(_log("fr.log", "I srv load_model: loading model 'x'\n"
                                          "E gguf_init_from_reader: tensor "
                                          "'token_embd.weight' has invalid ggml type 142"),
                          "server exited rc=1")
        oom = load_failure(_log("oom.log", "I srv load_model: loading model 'x'\nE CUDA error: out of memory"),
                           "server exited rc=-6")
        none = load_failure(_log("nc.log", "everything is fine\nnothing to see"), "server exited rc=1")
        unreadable = load_failure(os.path.join(td, "does-not-exist.log"), "server exited rc=1")
        ck("a reader's refusal of the FILE is its own class", "refused the FILE" in fr["load_failure_class"], True)
        ck("...and it quotes the cause with its line number", ("line 2" in fr["why"]), True)
        ck("A DEVICE OOM IS ITS OWN CLASS -- a tenancy condition, not a model condition",
           "DEVICE has no room" in oom["load_failure_class"], True)
        ck("...and it names the holders (RULING 82)", "HELD BY" in oom["why"], True)
        ck("a log with no cause of its own is reported as such",
           "no cause named" in none["load_failure_class"], True)
        ck("...and an UNREADABLE log is 'unreadable', never 'absent'",
           "could not be read" in unreadable["load_failure_class"], True)

    print("\n[7] THE INTERFACE CLAIM IS MEASURED, NOT ASSERTED")
    ca = clock_audit()
    ck("no wall-clock term exists in the frozen simulator", ca["wall_clock_terms_found"], [])
    ck("...and the same audit WOULD find one (the control's own control)",
       bool([l for l in ["# c\nimport time\ntime.sleep(1)"] if any(t in l for t in ("import time",))]), True)

    print("\n[8] ONE RUN, ONE PATH -- the artifact gate refuses at admission")
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        out = os.path.join(td, "MC_probe_state.json")
        ck("a free path is allowed", artifact_gate(out, None)[0], True)
        json.dump({"config": {"server_binary_digest": "aaa", "legend_digest": "bbb", "reasoning": "off"}},
                  open(out, "w"))
        ok, msg, rep = artifact_gate(out, None)
        ck("an occupied path is refused", ok, False)
        ck("...and the message names what is there and what would replace it",
           ("aaa" in msg and "bbb" in msg), True)
        ok, _msg, rep = artifact_gate(out, "re-measuring after an instrument fix")
        ck("...and a REASON gets past, carrying the digest of what it replaced",
           (ok, rep is not None and len(rep["sha256"]) == 64), (True, True))

    print("\n[9] THE LEGEND HAS TWO ARMS, AND THE ONE THE RECORDS WERE TAKEN UNDER HAS NOT MOVED")
    ck("the RECORDED arm is the one the declaration names", LEGEND_DEFAULT, DECL["legend_arm"])
    ck("...and its digest is the one the records already taken carry",
       legend_digest("example"), "ec59f2dc5fd35518")
    ck("...and the plain arm is a DIFFERENT template", legend_digest("plain") != legend_digest("example"),
       True)
    ck("...and it carries no concrete example value ('3W')", ("3W" in PROMPT_PLAIN), False)
    ck("...and it still states both the PASS escape and the two-character shape",
       ("PASS" in PROMPT_PLAIN and "exactly two characters" in PROMPT_PLAIN), True)
    ck("...and the two arms are IDENTICAL everywhere before the state",
       PROMPT_PLAIN.split("{state}")[0] == PROMPT_EXAMPLE.split("{state}")[0], True)
    ck("...and identical throughout the state and the action history",
       PROMPT_PLAIN.split("{state}")[1].split("{recent}")[0]
       == PROMPT_EXAMPLE.split("{state}")[1].split("{recent}")[0], True)
    ck("...so the ONLY difference between the arms is the instruction clause",
       PROMPT_PLAIN.split("{recent}")[1] != PROMPT_EXAMPLE.split("{recent}")[1], True)

    print("\n" + "=" * 96)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{ran[0] - len(fails)}/{ran[0]}")
    print("=" * 96)
    return 1 if fails else 0


# --------------------------------------------------------------------------------- main
def main():
    global LLAMA_SELECTED, ARTIFACT_OVERRIDE, LEGEND_ARM
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant")
    ap.add_argument("--state", nargs="+")
    ap.add_argument("--legend", choices=tuple(LEGEND_ARMS), default=None,
                    help=f"which LEGEND arm to run (default: {LEGEND_DEFAULT}, the recorded instrument; "
                         f"MC_LEGEND is read when the flag is absent). The arm is recorded in the "
                         f"artifact and in the log's name.")
    ap.add_argument("--cap", type=int, default=None,
                    help="how many actions the entrant is allowed. DEFAULT: derived from the state's own "
                         "horizon (max impact tick + 2), so the volley always resolves.")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--overwrite-artifact", dest="overwrite_artifact", default=None, metavar="REASON")
    ap.add_argument("--llama-server", dest="llama_server", default=None,
                    help="path to the llama-server BINARY to run (default: the declared default, "
                         "unchanged). The binary's digest is recorded with the run.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the legend, the first screen and the "
                                                           "prompt for each state; start no server, write "
                                                           "nothing")
    a = ap.parse_args()

    # THE ARM IS SELECTED HERE AND READ AT CALL TIME EVERYWHERE ELSE -- one definition, so the prompt that
    # is sent, the digest that is recorded and the log's name cannot be three different arms.
    LEGEND_ARM = a.legend or (os.environ.get("MC_LEGEND", "").strip().lower() or None)
    if LEGEND_ARM is not None and LEGEND_ARM not in LEGEND_ARMS:
        print(f"  MC_LEGEND must be one of {tuple(LEGEND_ARMS)}, got {LEGEND_ARM!r}"); return 2

    if a.self_test:
        return _self_test()
    if not a.entrant and not a.dry_run:
        ap.error("--entrant is required (or use --dry-run)")
    if not a.state:
        ap.error("--state is required")

    states = []
    for s in a.state:
        p = resolve_state(s)
        if p is None:
            print(f"  STATE ABSENT: {s}"); return 2
        states.append(p)

    if a.llama_server:
        sel = os.path.expanduser(a.llama_server)
        if not (os.path.exists(sel) and os.access(sel, os.X_OK)):
            print(f"  BINARY ABSENT OR NOT EXECUTABLE: {a.llama_server}"); return 2
        LLAMA_SELECTED = sel

    if a.dry_run:
        print(f"  reasoning   {REASONING}  ({reasoning_source()})  declared_in {REASONING_DECLARED_IN}")
        print(f"  binary      {llama_server()}")
        print(f"  flag        reasoning_argv {reasoning_argv()}  -- {reasoning_argv_scope()}")
        print(f"  legend      {legend()}  digest {legend_digest()}  (arms {legend_arm_digests()}, "
              f"source {legend_source()})")
        ca = clock_audit()
        print(f"  clock audit {ca['reading']}")
        for p in states:
            text = open(p, encoding="utf-8").read()
            print("\n" + "-" * 96)
            print(f"  {os.path.relpath(p, HERE)}  digest {file_digest(p)}  cap {a.cap or clock_cap(text)}")
            print("-" * 96)
            print(prompt_for(render_view(initial_view(text)), []))
        return 0

    p = a.entrant if os.path.exists(a.entrant) else os.path.join(MODELS, a.entrant)
    if not os.path.exists(p):
        print(f"  ENTRANT ABSENT: {a.entrant}"); return 2

    ok, msg = binary_guard(p)
    if not ok:
        for line in msg.splitlines():
            print(f"  {line}")
        return 2

    rc = 0
    for state_path in states:
        cap = a.cap if a.cap else clock_cap(open(state_path, encoding="utf-8").read())
        out = artifact_path(p, state_path)
        if a.overwrite_artifact is not None and not a.overwrite_artifact.strip():
            print("  --overwrite-artifact WAS GIVEN AN EMPTY REASON: a replacement has to say why. Nothing "
                  "written."); return 2
        ARTIFACT_OVERRIDE = a.overwrite_artifact
        gate_ok, gate_msg, replaced = artifact_gate(out, ARTIFACT_OVERRIDE)
        if not gate_ok:
            for line in gate_msg.splitlines():
                print(f"  {line}")
            return 4
        r = run(p, state_path, cap, a.port)
        os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)
        if replaced is not None:
            r["artifact_replaced"] = replaced
        json.dump(r, open(out, "w"), indent=1)
        print(f"  entrant   {r.get('entrant')}   digest {r.get('entrant_digest')}")
        print(f"  state     {r.get('level')}   digest {r.get('state_digest')}   cap {cap}")
        print(f"  binary    {llama_server()}  (server_binary_digest {server_binary_digest()})")
        if not r.get("loaded"):
            print(f"  DID NOT LOAD -- {r['why']}")
            print(f"  artifact  {os.path.relpath(out, HERE)}")
            rc = 3
            continue
        print(f"  ended     {r['ended']}  ({r['ended_why']})")
        print(f"  score     {r['score']} / {r['cities_total']} cities surviving")
        print(f"  counts    {r['counts']}")
        print(f"  tokens    {r['tokens']}")
        print(f"  unreadable {r['unreadable']}  missing_values {r['missing_values']}"
              f"  budget {r['budget_signature']['reading'][:60]}")
        print(f"  suffice   {r['sufficiency']['reading'][:90]}")
        print(f"  artifact  {os.path.relpath(out, HERE)}")
        if replaced is not None:
            print(f"  REPLACED  {replaced['path']} ({replaced['bytes']} B) -- reason: "
                  f"{replaced['reason_given']!r}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
