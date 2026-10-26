#!/usr/bin/env python3
"""ZORK -- the entrant driver. One model, one level, one command per turn.

BUILT TO PREREG_zork.md AND SHAPED ON `sokoban_run.py`, THE ONE ENTRANT DRIVER THIS REPO HAD.

WHAT THIS FILE DOES, AND WHAT IT REFUSES TO DO

    It launches a neutral server, shows the entrant THE SIMULATOR'S OWN RENDERING of the state plus the
    transcript of its own commands, asks for one command, hands that command to the simulator, and writes
    the record. THE SIMULATOR DECIDES EVERYTHING: what a command means, whether it was read at all, what
    the score is and why the crawl ended. This file asks and records -- the same division of labour that
    makes `sokoban_run.py` a driver rather than a scorer.

    IT DOES NOT EVALUATE C1-C4. The criteria, the counters' reading and the verdict belong to Ocho and
    the Chair (CABINET_STRUCTURE.md rule 4: *a cabinet agent never scores its own event*). The cell's
    counters and the simulator's score are reported; the criterion is not, and no field here says
    `passed` or `failed`.

THE INTERFACE IS NAMED AND THE ANSWER IS NOT. The prompt names the COMMAND GRAMMAR the way a controller
names its buttons -- walking, taking, dropping, looking, inventory -- because an entrant that does not know
the controls is measured on guessing them. It names no route, no room it has not seen, and no item: the
world's own rendering of the room is the ONLY description of the world in the prompt, and it is the
simulator's `describe()`, unedited. NAMING THE CONTROLS IS THE INTERFACE; naming the key's room would be
the answer. (The Sokoban driver's menu lesson, applied by distinction rather than by habit.)

AND THE ANSWER IS NOT A MENU HERE EITHER -- WHICH IS THE WHOLE RISK OF THIS EVENT. Sokoban's entrant
picks one of four letters. This one is handed an OPEN TEXT FIELD, which is the chess failure wearing
different clothes. So the driver's reading rule is deliberately the NARROWEST one that can read a command:
THE FIRST NON-EMPTY LINE, VERBATIM, AND NOTHING MINED FROM PROSE. Whether that line IS a command is not
this file's decision -- it is `zork.parse_command`'s, and a line it cannot read is counted `unparsed`,
never scored as a wrong move (PREREG_zork.md: the parser that folds its own failures into the entrant's
score is reporting on itself).

    python3 zork_run.py --entrant <gguf> --level levels/zork_01_the_floor.txt --cap 20
    python3 zork_run.py --self-test
    scripts/run_guarded.sh zork-first-run /home/chilly1/workspace/ocho_arena \
        /usr/bin/python3 zork_run.py --entrant <gguf> --level levels/zork_01_the_floor.txt --cap 20
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zork as Z                                                         # noqa: E402
# THE ONE READER OF RECORD -- IMPORTED, NEVER REIMPLEMENTED (RULING 79).
from answer_reader import read_answer                                    # noqa: E402
# RULING 82 -- the failure names the HOLDER, not the model.
from vram_holder import holder_sentence                                  # noqa: E402

LLAMA = "/home/chilly1/llama.cpp/build/bin/llama-server"
MODELS = os.environ.get("ARENA_MODELS") or os.path.expanduser("~/moltbook_pipeline/models")

# ==================================================================================================
# THE BINARY IS PART OF THE INSTRUMENT, SO IT IS SELECTABLE -- AND IT TRAVELS WITH THE NUMBER.
#
# THE BINARY TRAP, carried here because this cabinet's first run must not walk into it: a Bonsai ternary
# gguf served through MAINLINE llama.cpp either is REFUSED or answers with degenerate garbage, and a
# `llamacpp` preset cannot pin a binary. The fork that loads them is
#     /home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server
# and it is reached through `--llama-server <path>` -- a PATH, deliberately, because choosing between a
# fork and mainline is a choice of INSTRUMENT, not a setting of the model.
#
# AND A PATH IS NOT AN IDENTITY -- the rule the ENTRANT gets further down this file, applied one layer
# down the instrument: `~/.hermes/runtimes/llamacpp/b10931/cuda/llama-server` has been MEASURED ON THIS
# BOX to report `build 10964, commit b29c606e2`, so a record carrying only that path names 10931 and
# describes 10964. The record therefore carries the binary's FILE DIGEST and the selector that chose it,
# and no new path is published (`config.server_argv` already carries the path).
#
# THE DEFAULT IS THE CONSTANT ABOVE, SO A RUN THAT NAMES NO BINARY IS THE DECLARED ONE, AND SAYS SO.
#
# THIS BLOCK IS A SECOND COPY OF `sokoban_run.py`'s, FIELD FOR FIELD AND WORD FOR WORD WHERE THE FIELD IS
# THE CLAIM (`server_binary_digest_scope` must read the same in both records or the two are not
# comparable). It is NOT factored into a shared module because that module would be a new shared file and
# `sokoban_run.py` belongs to another cabinet's card -- both are Ocho's decisions, not this driver's. The
# duplication is named here rather than left for a reader to discover: TWO COPIES THAT MUST AGREE IS A
# DEFECT WITH A DUE DATE.
# ==================================================================================================
LLAMA_SELECTED = None                    # --llama-server PATH. None = the declared default above.
# THE COMPUTE PATH, AS A PARAMETER RATHER THAN A CONSTANT. `-ngl 0` is this driver's REGISTERED launch
# and stays the DEFAULT, so every existing record keeps the instrument it was taken under. The suite
# that owns the card (kanban t_234b2387) runs its rows on the GPU, and a launch flag is a COMPUTE-PATH
# field -- the same class of variable as the binary above -- not part of the prompt or the scorer. It
# travels in the argv the server is actually started with, so a row states the path it ran on.
NGL_DECLARED = 0
NGL = NGL_DECLARED                       # --ngl INT. Set in main(); read by server_argv().
# `--parallel` is the SAME CLASS OF FIELD: the registered launch passes no such flag (llama-server then
# opens its default slot count, reported by /props), and the suite's card fixes slots at 1 so a request
# cannot silently shrink its own context. None means "pass nothing", which is the registered launch.
PARALLEL_DECLARED = None
PARALLEL = PARALLEL_DECLARED
_BINARY_DIGEST_CACHE = {}

# ==================================================================================================
# THE PRESERVED FIXTURE — EIGHT PATHS NAMED LITERALLY, PINNED BY DIGEST, AND NOT GLOBBED.
#
# These are the eight sitting-2 rows of `13b161a`, the bytes the GPU window replaced, preserved under
# `suite3/preserved/` and tracked in git. They are the HISTORICAL DEFECT: `config.n_gpu_layers` 0 beside
# `config.server_argv` `-ngl 99`, the summary naming the constant while the argv named the launch. The
# self-test asserts that contradiction against THESE BYTES, so the evidence for "the writer defect was
# real, and this is what it looked like" is a digest rather than a claim.
#
# WHY LITERAL PATHS AND NOT `glob("suite3/preserved/*/ZORK_*.json")`: a later GPU window adds directories
# there, and a glob is a denominator that can change without a line in the record. Eight names, eight
# digests, eight byte counts, written down once. A missing file or a moved byte is a RED arm.
#
# Local Chair ruling 2026-10-26 (R3-R5), card `t_a828c554`:
#   governance/rulings/2026-10-26-a-control-that-asserts-a-defect-in-the-live-archive-vetoes-the-repair.md
# ==================================================================================================
PRESERVED_FIXTURE = (
    ("suite3/preserved/20261026-140512/ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json",
     "7e57408fe63fd5ad8a16cc9beae80c8b20bf8c712f30dcb89a547d52eaeccc48", 17803),
    ("suite3/preserved/20261026-140521/ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_02_long_crawl.json",
     "df3ef579919866203e0882a22e2b5052c9bd894b8a608fbc844fb29a5e5e645b", 53987),
    ("suite3/preserved/20261026-140527/ZORK_Ornith-1.5-9B-Q4_K_M_zork_01_the_floor.json",
     "24841df4d193ea58cd212240074ad56a5b063cc7937b490e7b5e5bbe5e4ecc10", 14538),
    ("suite3/preserved/20261026-140535/ZORK_Ornith-1.5-9B-Q4_K_M_zork_02_long_crawl.json",
     "60d06b325250d4c9f6fadb5d2a908d49b4427465213e80c802d176c4df412444", 21527),
    ("suite3/preserved/20261026-140549/ZORK_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_zork_01_the_floor.json",
     "3f660454a52843aaf9979b9931c7c0f3bc3db14a61d19ce940e3e61ec0590bda", 40346),
    ("suite3/preserved/20261026-140602/ZORK_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_zork_02_long_crawl.json",
     "4f26f6cf6c8f36bb9ddf235a50fefcc50cea9679efc9fcd356d02fff298a23f4", 49733),
    ("suite3/preserved/20261026-140614/ZORK_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_zork_01_the_floor.json",
     "7b5c27c5cd645746cfed8dacbaf04c8f275962a12847f4022d3dc1564d507e8f", 12960),
    ("suite3/preserved/20261026-140620/ZORK_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_zork_02_long_crawl.json",
     "d466037a2b1a0093f0904c8021d8a9c7f61b30d73f9ae8811ba156a610da0607", 44669),
)


def llama_server():
    """THE BINARY THAT WILL ACTUALLY BE EXECUTED -- read at CALL TIME, so a selection made in main()
    reaches the launch AND the record, rather than only the launch."""
    return LLAMA_SELECTED or LLAMA


def binary_digest(path=None):
    """sha256 of the BINARY FILE, first 16 hex, cached per path and streamed."""
    p = path or llama_server()
    if p not in _BINARY_DIGEST_CACHE:
        h = hashlib.sha256()
        try:
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            _BINARY_DIGEST_CACHE[p] = h.hexdigest()[:16]
        except OSError:
            # AN UNREADABLE BINARY GETS null AND A REASON, NEVER A FABRICATED DIGEST -- a made-up hash
            # is worse than a missing one because it verifies.
            _BINARY_DIGEST_CACHE[p] = None
    return _BINARY_DIGEST_CACHE[p]


def binary_source():
    """WHICH SELECTOR CHOSE THE BINARY. The DIGEST says which binary ran; this says which selector was
    used, and they are two different facts because a module cannot tell that its own constant was
    patched in memory at the call site."""
    return "--llama-server" if LLAMA_SELECTED else "no selector given: the module constant LLAMA"


def binary_provenance():
    """WHICH BINARY, IN THREE VALUES: the digest, what it is a digest OF, and which selector chose it.
    CARRIED ON THE CELL RECORD AND ON BOTH LOAD-FAILURE RECORDS, from this one definition, so the
    success path and the failure path cannot drift apart."""
    return {"server_binary_digest": binary_digest(),
            "server_binary_digest_scope": ("sha256 of the BINARY FILE, first 16 hex. THE BINARY IS PART OF "
                                           "THE INSTRUMENT, so it is identified by a digest and not by a "
                                           "path alone: a path can name one build and hold another."),
            "server_binary_source": binary_source()}


def simulator_digest():
    """THE SIMULATOR IS THE INSTRUMENT THIS EVENT IS MEASURED WITH. A level digest without it describes
    the world and not the machine that scored it -- and this cabinet's simulator is pre-registered, so a
    record that cannot say WHICH simulator produced a number cannot be placed against the criteria."""
    return file_digest(os.path.join(HERE, "zork.py"))


def level_digest(path):
    return file_digest(path)


_DIGEST_CACHE = {}


def file_digest(path):
    """sha256 of a FILE, first 16 hex, cached per path and streamed."""
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


def model_digest(path):
    """sha256 of the model FILE, first 16 hex. THE ENTRANT IS THE THING BEING MEASURED, AND A NAME IS
    NOT AN IDENTITY: two quantizations under one name would otherwise be indistinguishable, and the name
    is a LABEL -- for reading, not for checking."""
    return file_digest(path)


def host_block():
    """WHAT BOX PRODUCED THIS RECORD. Small, and it is the one input the cabinet rule names that neither
    of the other two digests covers."""
    return {"platform": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "cpus": os.cpu_count(),
            "python": platform.python_version()}


# ==================================================================================================
# THE ARTIFACT PATH IS OWNED BY ONE RUN. One run, one path, and the run refuses a path that exists.
#
# FINDING 020's rule on the axis the level and the entrant do not cover: the SAME cell re-run -- the other
# arm of an A/B, a re-measure after an instrument change -- wrote ONE path and the first run's record was
# gone. No field could close that, because the record that would carry the field is the record that gets
# overwritten, so the fix is a REFUSAL, taken AT ADMISSION, before Popen: a refusal that costs a model
# load is not a refusal.
#
# IT REFUSES ON ANY EXISTING RECORD, not only on one with a differing instrument, for the three reasons
# measured on the sibling driver and named there in full: a record written before the digest landed
# carries no digest to compare; the artifact NAME never carried the reasoning arm; and the same instrument
# twice is not the same record (two runs of one binary on one model have emitted 0 and 64 tokens).
#
# `probes/ZORK_<entrant>_<level>.json` is the coordinate, namespaced beside `probes/SOKOBAN_*` so the two
# cabinets' artifacts cannot collide.
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
    return os.path.join(HERE, "probes", f"ZORK_{label}_{lname}.json")


def run_identity():
    """WHAT THIS RUN IS, in the three values the record can carry and the NAME cannot: the instrument that
    answered, the prompt arm, and the reasoning arm."""
    return {"server_binary_digest": binary_digest(), "legend_digest": legend_digest(),
            "reasoning": REASONING}


def carried_identity(d):
    """-> THE SAME THREE VALUES AS AN EXISTING RECORD CARRIES THEM, or None for one it does not carry.
    None IS NOT A MATCH AND IS NOT TREATED AS ONE: a run cannot show it is the same instrument as a
    record that names no instrument."""
    cfg = d.get("config") if isinstance(d.get("config"), dict) else {}
    return {k: (d[k] if k in d else cfg.get(k)) for k in IDENTITY_IN_RECORD}


def artifact_gate(out, reason, old_bytes=None):
    """-> (ok, message, replaced). REFUSES to write over a record this run did not take."""
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
        f"run's instrument.{os.linesep}"
        f"  THE REMEDY IS NOT TO IGNORE THIS EXIT CODE, AND IT IS NOT A BARE FORCE. If the replacement "
        f"is intended, say why, and the reason is written into the record that does the replacing:"
        f"{os.linesep}"
        f"      --overwrite-artifact \"<why this record should be replaced>\"{os.linesep}"
        f"  NOTHING HAS BEEN WRITTEN, NO SERVER HAS BEEN STARTED AND NOTHING HAS BEEN CONSUMED."), None


# ==================================================================================================
# WHICH CONDITION IS THIS FAILURE REPORTING?
#
# RULING 82's holder sentence is appended to EVERY load failure, so a file the binary cannot PARSE is
# reported as a card-tenancy condition. RULING 82 IS NOT WEAKENED AND ITS CARRIER IS UNTOUCHED: the
# sentence is kept, verbatim, for the case the ruling was ratified for -- a log that names no cause of its
# own. What this adds is the OTHER case, decided by a READING of the server's own log, with the matched
# line QUOTED WITH ITS LINE NUMBER so a reader can overrule the class from the carrier.
#
# THE SIGNATURE LIST IS A SNAPSHOT OF ONE BUILD'S WORDING, WHICH IS WHY THE LINE TRAVELS WITH THE CLASS.
# A check written against ONE signature would have called the other two "no cause named".
# ==================================================================================================
FILE_REFUSAL_SIGNATURES = ("gguf_init_from_reader", "llama_model_loader", "invalid ggml type",
                           "invalid magic characters", "failed to read tensor info",
                           "done_getting_tensors", "unknown model architecture")


def log_file_refusal(log_path):
    """-> (kind, line, lineno), kind in {"file_refusal", "no_cause", "log_unreadable"}. A MISS IS
    REPORTED AS ITS OWN KIND: an unreadable log is not "the log says nothing"."""
    try:
        lines = open(log_path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return "log_unreadable", None, None
    for i, ln in enumerate(lines, 1):
        if any(sig in ln for sig in FILE_REFUSAL_SIGNATURES):
            return "file_refusal", ln.strip(), i
    return "no_cause", None, None


def load_failure(log_path, status):
    """-> {"why": ..., "load_failure_class": ...} for a load that did not finish. ONE DEFINITION, so the
    two failure returns cannot drift apart in wording or in class."""
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


# ==================================================================================================
# THE REASONING SETTING IS DECLARED, PER CABINET, WITH A REASON -- AND AN UNDECLARED RUN IS REFUSED.
#
#   ONE LETTER, ONE WORD, or ONE SHORT COMMAND answers -> off. Deliberation occupies the answer slot and
#                                                        the ceiling eats it. Measured on the same
#                                                        weights on the sibling cabinet: 2314 tokens and
#                                                        no commitment.
#   MULTI-STEP ARITHMETIC, exact sums               -> on, probably. That is where it helps. (DARTS.)
#
# This cabinet's answer is a COMMAND OF ONE TO FOUR WORDS -- `take key`, `north` -- which is the same case
# as Sokoban's one letter and gets the same setting FOR THE SAME MEASURED REASON, stated in PREREG_zork.md
# where the criteria are frozen. It is NOT a general default: a default wearing a decision's clothes is
# what the first version of this block was, in the sibling driver, and it was the same defect as the one
# it was written to fix.
#
# AND "REFUSED" IS MECHANISED RATHER THAN INTENDED. `declaration_gate` refuses a run whose arm is not one
# of the three legal values AND a run whose declaration names a document that does not exist: an arm
# declared in a file nobody can find is an undeclared arm with a citation.
# ==================================================================================================
REASONING_DECLARED = "off"
REASONING_DECLARED_IN = "PREREG_zork.md"
REASONING_RATIONALE = (
    "Zork's answer is a COMMAND OF ONE TO FOUR WORDS -- `take key`, `north`, `north; look`. PREREG_zork.md "
    "states it as the reason the counters are kept apart, and the sibling cabinet measured what a thinking "
    "model does with a short-answer slot: 2314 tokens of deliberation and no commitment, because the "
    "deliberation is spent where the answer belongs. This is the short-answer case, so the setting is off. "
    "A LONG-ANSWER format would be the opposite case and would take this as a parameter rather than a "
    "constant -- this cabinet has no long-answer format in it."
)
REASONING_LEGAL = ("on", "off", "auto")
REASONING_OVERRIDE = os.environ.get("ZORK_REASONING_TEST_ARM", "").strip().lower() or None


def declaration_gate(value, declared_in):
    """-> (ok, message). A RUN WITH NO DECLARATION IS REFUSED, and so is one that cites a document that is
    not there. Both directions are controls in --self-test: a gate that has never been shown to refuse has
    not been shown to be a gate."""
    if value not in REASONING_LEGAL:
        return False, (f"REFUSED: the reasoning arm is {value!r}, which is not one of {REASONING_LEGAL}. "
                       f"An arm that is not declared is not a decision -- set the declaration in this "
                       f"file or ZORK_REASONING_TEST_ARM=<on|off|auto> for a deliberate experiment arm.")
    if not declared_in:
        return False, ("REFUSED: the reasoning arm is declared NOWHERE. A value with no document behind it "
                       "is a default wearing a decision's clothes, and only one of those is evidence.")
    path = declared_in if os.path.isabs(declared_in) else os.path.join(HERE, declared_in)
    if not os.path.exists(path):
        return False, (f"REFUSED: the reasoning arm is declared in {declared_in!r}, WHICH DOES NOT EXIST "
                       f"in this tree ({path}). An arm declared in a file nobody can find is an "
                       f"undeclared arm with a citation.")
    return True, ""


_gate_ok, _gate_msg = declaration_gate(REASONING_OVERRIDE or REASONING_DECLARED, REASONING_DECLARED_IN)
if not _gate_ok:
    raise SystemExit(_gate_msg)
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
    the launch and `config.server_argv` both take the selection, so the record cannot show mainline and
    name the fork.

    `-ngl 0` IS DELIBERATE AND IS THE SIBLING DRIVER'S CHOICE, KEPT: the measurement is of the entrant, and
    a cell that runs on the card when the card is free and on the CPU when it is held is two cells wearing
    one name. It also keeps a run possible while another run holds the card.
    """
    argv = [llama_server(), "-m", entrant, "-c", str(ctx), "-ngl", str(NGL), "--port", str(port), "--no-webui"]
    if PARALLEL is not None:
        argv += ["--parallel", str(PARALLEL)]
    return argv + reasoning_argv()


def argv_value(argv, flag):
    """-> the value passed to `flag` in the argv that was ACTUALLY BUILT, or None if the flag is absent.

    THIS EXISTS BECAUSE THE RECORD CONTRADICTED ITSELF, AND IT DID SO ON EVERY GPU ROW. `config` carried
    `"n_gpu_layers": 0` as a LITERAL while `config.server_argv` carried `-ngl 99` -- the summary field
    reporting the constant it was written against, the argv reporting the launch that happened. Eight
    recorded rows said both, and those eight are preserved under `suite3/preserved/` (pinned in
    PRESERVED_FIXTURE below), not at `probes/`:

        suite3/preserved/…/ZORK_*.json   config.n_gpu_layers = 0   config.server_argv   -c 4096 -ngl 99 --parallel 1

    A reader taking the summary would have filed eight CPU rows; a reader taking the argv would have filed
    eight GPU rows, and NEITHER READER WOULD HAVE KNOWN THE OTHER EXISTED. That is the same defect class
    as the counters this cabinet's card is about -- one record, two claims, no way to tell which one is
    the measurement -- and it landed on the one field the suite card names as required: the compute path.

    So the summary is now READ OUT OF THE ARGV rather than written beside it, and `--self-test` asserts the
    two agree instead of trusting that they do.
    """
    try:
        return argv[argv.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def compute_path(argv):
    """THE COMPUTE PATH AS THE LAUNCH STATED IT, read from the argv the server is started with."""
    ngl = argv_value(argv, "-ngl")
    ctx = argv_value(argv, "-c")
    par = argv_value(argv, "--parallel")
    return {"n_gpu_layers": None if ngl is None else int(ngl),
            "ctx": None if ctx is None else int(ctx),
            "parallel": None if par is None else int(par),
            "computed_from": ("config.server_argv -- the summary fields above are READ OUT of the argv "
                              "that was run, not written beside it, because this file once wrote them "
                              "from the module constants and the two disagreed on every GPU row")}


# ==================================================================================================
# THE PROMPT -- THE STATE AND THE CONTROLS, AND NOTHING ELSE.
#
# The legend is a SEPARATE ARM ONLY IF THERE IS AN A/B, and there is none here: one legend, one digest,
# carried so a reader can tell two prompts apart rather than inferring they are the same. What the digest
# covers is THE WHOLE THING THE ENTRANT SEES -- the template, the state rendering and the transcript
# layout -- because a digest of the prose alone would call two different views one view.
#
# AND WHAT THE ENTRANT SEES IS THE SIMULATOR'S OWN `describe()`, UNEDITED. It names the room, its
# description, the exits and what is lying here. It does NOT name the inventory: asking what you carry is
# one of the five commands, so a model that wants to know can ask, and a model that is told has had the
# faculty handed to it. THE TRANSCRIPT IS THE ENTRANT'S OWN SCROLLBACK -- the line it typed and the
# world's reply -- which is what a terminal player sees, and which is the only memory a stateless
# one-message-per-turn harness can offer. Both halves are stated because a reader is entitled to know
# which of the two a retention number is about.
#
# AND IT IS PROSE RATHER THAN A FORM. The sibling's first legend was a line of key-value pairs and an
# entrant TRANSCRIBED IT AS A SCHEMA -- `{"first_line": "U = up", ...}`, forty commands, zero moves. The
# vocabulary is therefore described in sentences, and no pseudo-field label appears in it.
# ==================================================================================================
TRANSCRIPT_LINES = 12

PROMPT = (
    "You are exploring a small world, one command at a time. You can only see the room you are standing in, "
    "and you are told what your last few commands did.\n\n"
    "Here is the room you are in now.\n\n"
    "{state}\n\n"
    "Here is your session so far -- the lines you typed and what the world answered.\n\n"
    "{recent}\n\n"
    "The world understands five kinds of command. You walk by naming a direction: north, south, east or "
    "west, and the single letters n, s, e and w mean the same thing. You take something by naming it after "
    "the word take, and get, grab and pick up mean the same as take. You put something down with drop. You "
    "study the room with look, and you study yourself and what you are carrying with inventory, whose short "
    "form is the single letter i.\n\n"
    "Reply with your next command on one line. Put nothing else on that line; if you want to explain "
    "yourself, the explanation goes on the lines after it. Name things exactly as they are written in the "
    "room, because the world does not guess what an invented word means."
)

# THE LEGEND'S IDENTITY IS OVER THE WHOLE VIEW, NOT OVER THE PROSE: the template, the state rendering and
# the transcript layout. Read at CALL TIME so a change to any of the three moves the digest.


def legend():
    return "state-as-text"


def legend_digest():
    text = (PROMPT + "\n--state-renderer--\n" + _renderer_source()
            + "\n--transcript--\n" + transcript_line("x", "y")
            + "\n--lines--" + str(TRANSCRIPT_LINES))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _renderer_source():
    """THE STATE RENDERING IS PART OF THE INSTRUMENT: `describe()` decides what the entrant is shown, so a
    digest of the prompt that omits it would call two different views one view."""
    import inspect
    return inspect.getsource(Z.describe)


def transcript_line(command, note):
    """ONE EXCHANGE OF THE TRANSCRIPT: the line the entrant typed and the world's reply to it."""
    return f"> {command}\n  {note}"


def prompt_for(state, history):
    """THE SCREEN. The state is the place; the transcript is what has happened so far."""
    recent = "\n".join(history[-TRANSCRIPT_LINES:]) if history else "(nothing yet -- this is your first command)"
    return PROMPT.replace("{state}", state).replace("{recent}", recent)


def ask(base, state, history, timeout_s=300):
    body = json.dumps({"messages": [{"role": "user", "content": prompt_for(state, history)}],
                       "max_tokens": MAX_TOKENS, "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
        dt = time.time() - t0
        # THE READER OF RECORD IS IMPORTED, NOT REIMPLEMENTED -- RULING 79.
        ans = read_answer(j)
        return (ans["text"], dt, ans["completion_tokens"],
                ans["finish_reason"] == "length", ans["field"])
    except Exception as e:                                               # noqa: BLE001
        ans = read_answer({}, exception=e)
        return "", time.time() - t0, 0, False, ans["field"]


def first_line(text):
    """THE ANSWER IS AT THE HEAD: THE FIRST NON-EMPTY LINE, VERBATIM. NOTHING IS MINED FROM PROSE.

    THIS IS THE ONE READING RULE THIS DRIVER OWNS, and it is deliberately the narrowest one that can read
    a command. The sibling driver takes the first TOKEN because its answer is one letter; this cabinet's
    answer is a COMMAND, so the granularity is the line -- `take key` is two words and both of them are the
    answer. What is NOT done here, in either direction: no token is cut off the front of a sentence, and no
    sentence is searched for a command inside it. `I will take the key` is handed to the parser AS TYPED
    and comes back unparsed, which is a counter about the parser and NEVER a wrong move -- the filed defect
    this cabinet's counters exist for. An empty answer returns None: it is a MISSING VALUE the harness read
    off the wire, not a command, and it is never scored.
    """
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return None


def probe_reasoning(base, timeout_s=180):
    """ASK THE MODEL ONCE, BRIEFLY, BEFORE THE FIELD -- and RECORD WHAT HAPPENED, NOT WHAT WAS ASKED FOR.

    The flag says which setting was requested; the probe says which one the model is actually running
    under. WHEN THOSE TWO DISAGREE, THE DISAGREEMENT IS THE FINDING. The answer LENGTH is the measurement
    and the mode is an INFERENCE from it, labelled as one: an extraction-shaped model produces a long
    answer to a one-token question without deliberating.
    """
    q = "What is 2 + 2? Reply with just the number and nothing else."
    body = json.dumps({"messages": [{"role": "user", "content": q}], "max_tokens": MAX_TOKENS,
                       "temperature": 0.0})
    req = urllib.request.Request(base + "/v1/chat/completions", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            j = json.loads(r.read().decode())
    except Exception as e:                                               # noqa: BLE001
        return {"question": q, "error": f"{type(e).__name__}: {e}", "observed": None}
    ch = (j.get("choices") or [{}])[0]
    # THE PROBE READS THE SAME READER, so "content or reasoning_content" has ONE definition in this tree.
    _ans = read_answer(j)
    txt = _ans["text"]
    think = _ans.get("trace_head") or ""
    ctok = _ans["completion_tokens"]
    shape = "short" if ctok <= 8 else "long"
    return {"question": q, "answer": txt[:60], "answer_from_reasoning_field": bool(think and not txt),
            "completion_tokens": ctok, "finish_reason": ch.get("finish_reason"),
            "observed_answer_shape": shape, "shape_threshold_tokens": 8,
            "observed": "off" if ctok <= 8 else "on",
            "observed_is_an_inference": True,
            "inference_caveat": ("a LONG answer is not necessarily deliberation -- a model that echoes the "
                                 "question in a schema produces a long answer too, and this probe cannot "
                                 "tell them apart"),
            "requested": REASONING,
            "disagrees_with_config": (REASONING != "auto" and (("off" if ctok <= 8 else "on") != REASONING))}


MAX_TOKENS = 64          # A COMMAND OF ONE TO FOUR WORDS. The CEILING, not the count used -- both travel.
COMMAND_CAP = 20         # THE BUDGET, NOT THE CLOCK (PREREG: "no time limit; the cap is the budget").
                         # The longest solution in the shipped levels is SIX commands, so twenty is more
                         # than three times a solution and still a number a reader can check against one.


def budget_signature(turns, cap):
    """DID IT HIT THE CEILING, OR COULD IT NOT ANSWER? Different findings, and one has been published as
    the other. `finish_reason=length` IS A STATEMENT ABOUT THE HARNESS, NOT THE MODEL."""
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


# ==================================================================================================
# THE SUFFICIENCY CLAIM, MADE CHECKABLE -- GAME_CONTRACT.md's bar, applied to this cabinet's record.
#
#   "the recorded state must be a SUFFICIENT STATISTIC FOR THE SCORE -- the scored outcome can be
#    recomputed from the recorded state alone, not 'related to' it: the state REPRODUCES it."
#
# So this function takes THE RECORD AND NOTHING ELSE, replays its own trace through the simulator, and
# compares every scored field. IF IT CANNOT REPRODUCE THEM, THE RECORD IS NOT A SUFFICIENT STATISTIC and
# the run says so instead of filing a number.
#
# AND THE LEVEL TRAVELS IN THE RECORD, which is what makes "the record alone" true rather than
# approximately true: a record carrying a level DIGEST and a PATH is a claim that a reader has the file, and
# this project has already paid for the difference between a label and its referent. The level is small --
# a few hundred bytes -- so the honest form costs nothing.
# ==================================================================================================
SCORED_FIELDS = ("finished", "ending", "carried_required_item", "required_item", "start_room",
                 "took_item_at_step", "commands_consumed", "counts", "outcomes", "rooms_visited",
                 "final_room", "final_inventory")
# THE FIELDS THE ADDITIVE AXIS ADDS. Kept OUT of SCORED_FIELDS deliberately: that tuple is the frozen
# claim about the SCORE, and a record written before this axis existed must not be failed for a field it
# was never asked to carry. A record without them reports `axis_measured: false` -- absent, not wrong.
AXIS_FIELDS = ("attribution", "attribution_reasons", "progress")


def sufficiency_check(record):
    """-> (ok, detail). Rebuilds the score FROM THE RECORD ALONE: the command stream is the trace's own
    `command` column, verbatim, handed back to the simulator. A missing field is a MISSING VALUE and is
    reported as a mismatch rather than skipped -- a check that passes by not looking is not a check."""
    for k in ("level_text", "trace", "start_room"):
        if k not in record:
            return False, {"checked": True, "reproduces": False,
                           "why": f"the record carries no {k!r}, so it cannot be replayed from alone"}
    cmds = [row.get("command") for row in record["trace"]]
    if any(c is None for c in cmds):
        return False, {"checked": True, "reproduces": False,
                       "why": "a trace row carries no raw command -- the record is not replayable"}
    try:
        again = Z.play(record["level_text"], cmds)
    except (ValueError, TypeError) as e:
        return False, {"checked": True, "reproduces": False,
                       "why": f"the replay refused the record: {type(e).__name__}: {e}"}
    mismatched = [k for k in SCORED_FIELDS if record.get(k) != again.get(k)]
    # THE ADDITIVE AXIS, WHEN THE RECORD CARRIES ONE. It is NOT folded into SCORED_FIELDS, because that
    # tuple is the frozen claim about the SCORE and a record written before this axis existed must not be
    # failed for a field it was never asked to carry. Absent is reported as absent (`axis_measured: false`),
    # which is a different statement from wrong.
    axis_measured = all(k in record for k in AXIS_FIELDS)
    axis_mismatched = [k for k in AXIS_FIELDS if record.get(k) != again.get(k)] if axis_measured else []
    # THE ROWS THEMSELVES, not only the totals: a trace whose per-step inventory drifted would still sum
    # to the same score, and a reader replaying the crawl needs the rows to be the same rows.
    row_mismatch = [i for i, (a, b) in enumerate(zip(record["trace"], again["trace"]))
                    if {k: a.get(k) for k in ("step", "command", "verb", "object", "outcome", "room",
                                              "inventory")}
                    != {k: b.get(k) for k in ("step", "command", "verb", "object", "outcome", "room",
                                              "inventory")}]
    if len(record["trace"]) != len(again["trace"]):
        row_mismatch.append(f"row count {len(record['trace'])} -> {len(again['trace'])}")
    # AND THE ATTRIBUTION COLUMNS ON THE ROWS, when the record carries them. A total that agrees while
    # the rows it was counted from have drifted is a total about a different run.
    attr_row_mismatch = []
    if axis_measured:
        attr_row_mismatch = [i for i, (a, b) in enumerate(zip(record["trace"], again["trace"]))
                             if (a.get("attribution"), a.get("reason"), a.get("counted_under"))
                             != (b.get("attribution"), b.get("reason"), b.get("counted_under"))]
    # AND THE SIMULATOR'S OWN REPLAY OF THE TRACE -- the second, independent route to the same ending
    # (zork.replay()). If the two routes disagree, the record has two readings and that is a finding.
    #
    # THE REQUIRED ITEM IS PASSED, AND THAT IS A FIX RATHER THAN A TIDY-UP. `replay()` without it recovers
    # `took_item_at_step` as THE FIRST TAKE OF ANY ITEM, while `play()` sets that field to the first take
    # OF THE REQUIRED ITEM. On `zork_02_long_crawl`, which ships a distractor (the torch), the two routes
    # disagree for any entrant that takes the torch first -- and this check then filed
    # `reproduces: false`, "THE RECORD DOES NOT REPRODUCE ITS OWN SCORE", against TWO ROWS THAT WERE FINE:
    #
    #     ZORK_MiMo-...-9B_Q4_K_M_zork_02_long_crawl.json        play said 17, replay said 0 (the torch)
    #     ZORK_Ministral-3-...-_zork_02_long_crawl.json          play said 10, replay said the torch's step
    #
    # THOSE TWO RECORDS ARE NOT REWRITTEN. They are the record of what the instrument said at the time, and
    # what it said was false; the correction belongs in the report, not in a patched file.
    rec = Z.replay(record["trace"], record["start_room"], required_item=record.get("required_item"))
    replay_mismatch = []
    if rec["route"] != record["rooms_visited"]:
        replay_mismatch.append("route")
    if rec["final_inventory"] != record["final_inventory"]:
        replay_mismatch.append("final_inventory")
    if rec["took_item_at_step"] != record["took_item_at_step"]:
        replay_mismatch.append("took_item_at_step")
    if rec["ending"] != (record["ending"] if record["ending"] != "out_of_commands" else None):
        replay_mismatch.append("ending")
    ok = (not mismatched and not row_mismatch and not replay_mismatch and not axis_mismatched
          and not attr_row_mismatch)
    return ok, {"checked": True, "reproduces": bool(ok),
                "replayed_from": "the record alone: trace[].command, verbatim, plus the level text it carries",
                "fields_compared": list(SCORED_FIELDS),
                "fields_mismatched": mismatched,
                "axis_measured": axis_measured,
                "axis_fields_compared": list(AXIS_FIELDS) if axis_measured else [],
                "axis_fields_mismatched": axis_mismatched,
                "attribution_rows_mismatched": attr_row_mismatch,
                "trace_rows_mismatched": row_mismatch,
                "simulator_replay_mismatched": replay_mismatch,
                "replay_basis": rec["took_item_at_step_basis"],
                "reading": ("THE RECORD REPRODUCES ITS OWN SCORE -- the simulator, given nothing but this "
                            "record, returns the same score, the same counters, the same attribution and "
                            "the same rows."
                            if ok else
                            "THE RECORD DOES NOT REPRODUCE ITS OWN SCORE. THIS IS NOT A RESULT: it is an "
                            "instrument failure, and the number above it must not be filed.")}


def run(entrant, level_path, cap, port):
    level_text = open(level_path).read()
    w = Z.parse_world(level_text)
    st = Z.initial_state(w)
    # THE LABELS COME FROM ONE DEFINITION, because the artifact's coordinate is derived from them too.
    label, lname = cell_labels(entrant, level_path)

    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    # THE ARM IS IN THE FILENAME -- the reasoning setting, so an A/B over the arm cannot have one arm's raw
    # log overwritten by the other's. THE LOG IS SCRATCH AND IS NOT THE RECORD (FINDING 020): the record is
    # the file in probes/, and `logs/` is ignored whole by .gitignore.
    log = os.path.join(HERE, "logs", f"ZORK_{label}_{lname}_{legend()}_rea-{REASONING}.log")
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
                        **load_failure(log, f"server exited rc={srv.returncode}"),
                        **binary_provenance()}
            try:
                urllib.request.urlopen(base + "/health", timeout=3).read()
                up = True
                break
            except Exception:                                            # noqa: BLE001
                time.sleep(3)
        if not up:
            return {"entrant": label, "entrant_digest": model_digest(entrant),
                    "level": lname, "loaded": False,
                    **load_failure(log, "never answered /health in 600 s"),
                    **binary_provenance()}
        load_s = time.time() - t0

        # THE PROBE RUNS BEFORE A SINGLE TURN. Ask once, briefly: what setting is this model ACTUALLY on?
        probe = probe_reasoning(base)

        commands, turns, history = [], [], []
        missing_values, never_answered = 0, False
        state = Z.describe(w, st)
        for i in range(cap):
            text, secs, nt, hit, source = ask(base, state, history)
            cmd = first_line(text)
            is_missing = (source == "capped-deliberation-missing-value")
            if is_missing:
                missing_values += 1
            # THE PER-TURN ROW CARRIES THE EXACT PROMPT AND THE EXACT STATE, so "what the entrant saw" is
            # IN the record rather than recovered from a driver at some commit. The `raw` answer is capped
            # for size, and it is the answer only: nothing is scored from it, so a truncation cannot move a
            # number.
            turns.append({"ply": i, "raw": (text or "")[:400], "command": cmd, "secs": round(secs, 1),
                          "gen_tokens": nt, "budget_hit": hit,
                          "cap_cut": cap_cut_statement(hit, bool(cmd)),
                          "answer_field": source, "missing_value": is_missing,
                          "state": state, "prompt": prompt_for(state, history)})
            if cmd is None:
                # AN EMPTY ANSWER ENDS THE RUN, AND THE REASON IS NAMED RATHER THAN IMPLIED: the cell did
                # not use a command, it produced no answer, and `commands_exhausted` would be a false
                # statement about the denominator.
                never_answered = True
                break
            commands.append(cmd)
            # THE SIMULATOR PARSES IT. `unparsed` IS ITS OWN OUTCOME AND MOVES NOTHING.
            verb, obj, why = Z.parse_command(cmd, w)
            if verb is None:
                outcome, note = "unparsed", why
            else:
                st, outcome, note = Z.step(w, st, verb, obj)
            history.append(transcript_line(cmd, note))
            state = Z.describe(w, st)
            if st["ended"]:
                break

        # THE SIMULATOR SCORES THE STREAM -- not the loop above. `play()` re-parses the world and re-reads
        # every command from the start, so the score is a function of the commands and the world, and this
        # driver's live stepping is only what it showed the entrant.
        r = Z.play(level_text, commands)
        if never_answered and not commands:
            r["ended"] = "no_answer"
            r["ended_why"] = ("the first answer was EMPTY -- the harness read a missing value off the wire "
                              "and the model never produced a command. NOT a capability result until it is "
                              "re-run at a setting that stops deliberating or with more room.")
            r["never_started"] = 1
        else:
            r["ended"] = r["ending"]
            # A TERMINATION THAT IS NOT THE GATE AND NOT THE CAP IS NAMED, because an entrant that stopped
            # answering mid-crawl used fewer commands than its budget and the denominator changes.
            if never_answered:
                r["ended_why"] = ("a later answer was EMPTY and ended the run: the commands before it were "
                                  "consumed, and the crawl stopped where the model stopped answering.")
        r.update({
            "kind": "model",
            "entrant": label, "entrant_digest": model_digest(entrant),
            "entrant_digest_scope": ("sha256 of the model FILE, first 16 hex. THE ENTRANT IS THE THING "
                                     "BEING MEASURED, so it is identified by a digest and not by a name; "
                                     "`entrant` beside it is a LABEL, for reading, not for checking."),
            "level": lname, "loaded": True, "load_s": round(load_s, 1),
            # THE LEVEL TRAVELS IN THE RECORD, so the score is recomputable from the record alone.
            "level_text": level_text,
            "level_digest": level_digest(level_path),
            "level_digest_scope": "sha256 of the LEVEL FILE, first 16 hex",
            "simulator": "zork.py", "simulator_digest": simulator_digest(),
            "simulator_digest_scope": ("sha256 of the SIMULATOR FILE, first 16 hex. THE SIMULATOR IS THE "
                                       "INSTRUMENT THIS EVENT IS MEASURED WITH, and it is pre-registered: "
                                       "a record that cannot say which simulator scored it cannot be placed "
                                       "against the frozen criteria."),
            "turns": turns, "cap": cap, "final_state": state,
            "legend": legend(), "legend_digest": legend_digest(),
            "legend_digest_scope": ("sha256, first 16 hex, of EVERYTHING THE ENTRANT SAW as a function of "
                                    "the state: the prompt template, the simulator's describe() source, and "
                                    "the transcript layout"),
            "transcript_lines": TRANSCRIPT_LINES,
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
                       # THE COMPUTE PATH IS READ OUT OF THE ARGV, NOT WRITTEN BESIDE IT. These three
                       # fields used to be the literals `4096` and `0`, and on every GPU row the argv
                       # beside them said `-ngl 99` -- see `argv_value` for the full account.
                       **compute_path(server_argv(entrant, 4096, port)),
                       "temperature": 0.0,
                       "transcript_lines": TRANSCRIPT_LINES,
                       "legend": legend(), "legend_digest": legend_digest(),
                       "server_argv": server_argv(entrant, 4096, port),
                       **binary_provenance()},
            "reasoning_probe": probe,
            "host": host_block(),
            # WHAT HAPPENED, not what was asked for.
            # THE FORMAT FIELDS, AND THE TWO LEVELS OF ONE STATE NAMED RATHER THAN LEFT TO BE GUESSED:
            #   `unparsed`  is the SIMULATOR's counter (the grammar's per-command outcome)
            #   `unreadable` is the FORMAT field, and it is the AGGREGATE of the above
            # THEY ARE THE SAME STATE AT TWO LEVELS, NOT TWO STATES. Both travel, because the counter is
            # frozen by the prereg and the format field is required.
            #
            # THE DRIVER'S READING RULE IS CARRIED BESIDE THE COUNTERS IT AFFECTS, because a reader who
            # does not know how the answer was cut out of the reply cannot read `unparsed` correctly: the
            # answer is the FIRST NON-EMPTY LINE VERBATIM, nothing is mined from prose, and the SIMULATOR's
            # parser then accepts or refuses it. AND THE TWO MEASURED PROPERTIES OF THAT FROZEN PARSER
            # TRAVEL HERE FOR THE SAME REASON: `i` is a declared abbreviation for inventory, so a sentence
            # OPENING WITH `I` is read as an inventory command and lands in `parsed`, where the C3
            # coverage finding cannot see it; and a command with a trailing sentence is refused AS A WHOLE,
            # so it lands in `unparsed`. Both are the frozen instrument's own behaviour (zork.py, 114/114
            # controls, pre-registered), reported rather than patched, and both are asserted in
            # `zork_run.py --self-test`.
            "reading_note": {
                "driver_rule": ("THE FIRST NON-EMPTY LINE, VERBATIM. Nothing is mined from prose; whether "
                                "the line IS a command is the simulator's parser's decision."),
                "measured_frozen_parser_1": ("a first word of `i`/`I` is a DECLARED abbreviation for "
                                             "inventory, so a prose sentence opening with `I` is read as "
                                             "an inventory command and counted `parsed`, NOT `unparsed` -- "
                                             "the parser reads a command out of text that does not contain "
                                             "one, which is the filed RESIGN defect in the other "
                                             "direction"),
                "measured_frozen_parser_2": ("a command with a trailing sentence is refused AS A WHOLE and "
                                             "counted `unparsed` (strict identity, per the prereg's "
                                             "boundary rule): `take the key and walk north` does not "
                                             "resolve"),
                "consequence_for_a_reader": ("`parsed` is NOT a count of progress: it includes commands the "
                                             "world executed and did nothing with (inventory, look). The "
                                             "score is `finished`/`ending`, computed by the simulator; "
                                             "`carried_required_item` is the faculty flag."),
            },
            # ── THE THREE-WAY SEPARATION, CARRIED ON THE RECORD ──────────────────────────────────────
            # THE FROZEN COUNTERS STAY AND ARE NOT REWRITTEN. `unparsed` is pre-registered and this
            # cabinet's card does not license moving it. What arrives beside it is the axis that says
            # WHOSE VOCABULARY FAILED, counted per row:
            #
            #     accepted         the world ACTED on it
            #     rejected         a verb this world knows was read, and the world refused it, with the reason
            #     UNATTRIBUTABLE   not in the game's command language at all
            #
            # AND THE FROZEN COUNTER EACH ROW IS ALSO COUNTED IN TRAVELS WITH THE ROW, so the two axes can
            # be checked against each other on the record itself rather than trusted.
            "attribution": r["attribution"],
            "attribution_reasons": r["attribution_reasons"],
            "attribution_reasons_text": r["attribution_reasons_text"],
            "attribution_scope": r["attribution_of"],
            "attribution_checked_against_counts": r["attribution_checked_against_counts"],
            "attribution_is_the_scoreable_form": True,
            "scoreable": bool(r.get("attribution_checked_against_counts")),
            "scoreable_scope": ("A ROW WITHOUT THE COUNTS IS NOT SCOREABLE. This flag is true only when "
                                "every row was attributed exactly once AND the per-row attribution sums "
                                "back to the frozen counters. Records written before this axis existed "
                                "carry no `attribution` and no `scoreable`, and their absence is the "
                                "statement that they are not scoreable on it -- they are not repaired, "
                                "rewritten or re-scored."),
            # ── PROGRESS AGAINST THE ROOM GRAPH, FROM WORLD STATE ────────────────────────────────────
            "progress": r["progress"],
            "progress_field_source": r["progress_field_source"],
            "progress_prose_only": r["progress_prose_only"],
            "progress_scope": ("EVERY field of `progress` is computed from the parsed world and the "
                               "world's state -- room count, objects moved, score and the BFS distance "
                               "to the gate. NOTHING in it is parsed from the entrant's prose. The one "
                               "prose-derived field in a run is `turns[].command`, which is the INPUT to "
                               "the parser; see `progress_prose_only` for the full list, and "
                               "`progress_field_source` for the declared provenance of every leaf -- a "
                               "control in zork.py fails if a leaf appears without a declared source."),
            "unreadable": r["counts"].get("unparsed", 0),
            "unreadable_is_the_aggregate_of": "unparsed (the simulator's own counter, per command)",
            "unreadable_scope": ("THE FORMAT FIELD, AND IT IS THE FROZEN COUNTER `unparsed` UNDER ANOTHER "
                                 "NAME. IT IS NOT A SINGLE CLAIM: it holds BOTH the commands that were "
                                 "refused (a verb this world knows, an argument it does not) AND the "
                                 "commands that were not in the language at all. A reader who wants to "
                                 "know which should read `attribution.unattributable`; a reader who "
                                 "needs the prereg's number reads this one. The two are reported and "
                                 "both are true; they are not two readings of one thing, they are two "
                                 "questions about one run."),
            "missing_values": missing_values,
            "missing_values_are_a_subset_of": ("a missing value is NOT inside `unreadable` here: `unreadable` "
                                               "counts COMMANDS the parser could not read, and a missing "
                                               "value is not a command at all -- the harness produced it. "
                                               "Both are non-answers and both are reported; they are "
                                               "SEPARATE because one is about the model's phrasing and the "
                                               "other about the ceiling."),
            "never_started": r.get("never_started", 0),
            "never_started_scope": ("OUTSIDE the denominator (A7): a cell whose every answer was empty never "
                                    "started, and a rate taken over `attempted` can be improved by "
                                    "quitting early, so it is counted separately."),
            "budget_signature": budget_signature(turns, MAX_TOKENS),
            # THE CRITERIA ARE NOT THIS DRIVER'S TO READ. Named, so a reader does not look for a verdict
            # field and find its absence ambiguous.
            "criteria_read_by": ("NOT THIS DRIVER -- C1-C4 and the verdict belong to Ocho and the Chair "
                                 "(CABINET_STRUCTURE.md rule 4). The counters above are the cell's; the "
                                 "criterion is not evaluated here, and no field in this record says pass "
                                 "or fail."),
        })
        # THE SUFFICIENCY CONTROL RUNS ON THE REAL RECORD, before it is written: a record that cannot
        # reproduce its own score must say so in the record rather than after the fact.
        ok, detail = sufficiency_check(r)
        r["sufficiency"] = detail
        r["sufficiency_ok"] = ok
        return r
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except Exception:                                                # noqa: BLE001
            srv.kill()


def cap_cut_statement(hit, answer_present):
    """WHAT THE CAP CUT -- because `finish_reason=length` IS A STATEMENT ABOUT THE HARNESS, NOT THE MODEL.
    The sibling measured the same task returning `length` at 1200, 2048 AND 4096 tokens and being CORRECT at
    every size, so a bare `length` invites a reader to infer a failure that may not be there."""
    if not hit:
        return "nothing -- the model stopped on its own"
    if not answer_present:
        return ("THE ANSWER -- deliberation consumed the ceiling before any answer was reached. THIS IS "
                "THE ONE CASE WHERE `length` MEANS THE MODEL DID NOT ANSWER.")
    return ("SURPLUS AFTER AN ANSWER -- the answer is present and readable; the cap cut what followed it. "
            "NOT a failed turn.")


# -------------------------------------------------------------------------------------- controls
def _self_test():
    """THE DRIVER'S OWN CONTROLS. zork.py proves the SIMULATOR can fail; these prove THE DRIVER can,
    in both directions, on the three claims this file makes that no simulator control covers: that an
    undeclared run is refused, that the reading rule does not mine prose, and that the sufficiency check
    FIRES on a record that does not reproduce its own score.

    AND THE CONTROL IS NOT ASSERTED ALONE: a control has a POSITIVE counterpart as well, because a check
    that refuses everything and a check that refuses nothing are one defect wearing two faces.
    """
    fails, total = [], 0

    def ck(name, got, want):
        nonlocal total
        total += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 100)
    print("THE ZORK ENTRANT DRIVER CONTROLS")
    print("=" * 100)

    print("\n[1] AN UNDECLARED RUN IS REFUSED -- and the three legal arms are not")
    for arm in REASONING_LEGAL:
        ck(f"the arm {arm!r} is accepted with its declaration",
           declaration_gate(arm, REASONING_DECLARED_IN)[0], True)
    ck("an EMPTY arm is refused", declaration_gate("", REASONING_DECLARED_IN)[0], False)
    ck("a junk arm is refused", declaration_gate("maybe", REASONING_DECLARED_IN)[0], False)
    ck("None is refused", declaration_gate(None, REASONING_DECLARED_IN)[0], False)
    ck("an arm with NO declaration document is refused", declaration_gate("off", "")[0], False)
    ck("an arm declared in a document that does not exist is refused",
       declaration_gate("off", "NO_SUCH_PREREG.md")[0], False)
    ck("...and the refusal SAYS the file is missing",
       "DOES NOT EXIST" in declaration_gate("off", "NO_SUCH_PREREG.md")[1], True)
    ck("the DECLARED arm is off, for the reason the prereg gives", REASONING_DECLARED, "off")
    ck("this run's arm is the declared one", REASONING, REASONING_DECLARED)
    ck("...and the change flag is clear because nothing was overridden",
       reasoning_changed_from_declaration(), False)
    ck("...and the record carries the argv, not a summary of it", reasoning_argv(), ["--reasoning", "off"])

    print("\n[2] THE READING RULE: the first non-empty line, verbatim -- and NOTHING mined from prose")
    ck("the first line is the command", first_line("take key\nsecond line"), "take key")
    ck("padding is stripped, the words are not cut", first_line("   take key   "), "take key")
    ck("an answer that opens with a blank line is still read",
       first_line("\n\nnorth\nand here is why"), "north")
    ck("AN EMPTY ANSWER IS NOT A COMMAND", first_line(""), None)
    ck("...and neither are blank lines", first_line("  \n \n"), None)
    ck("...and neither is None", first_line(None), None)
    ck("a command is NOT truncated to one token -- `take key` stays two words",
       len(first_line("take key").split()), 2)
    # AND THE OTHER DIRECTION, WHICH IS THE CABINET'S WHOLE RISK: prose is handed over AS TYPED and the
    # SIMULATOR's parser is what reads it. Nothing here finds a command inside a sentence.
    #
    # AND THE TWO MEASURED PROPERTIES OF THE FROZEN PARSER BELOW ARE CONTROLS, NOT COMMENTARY. They were
    # found by THIS control on 2026-10-17, on the first drive of this cabinet, and they are reported to
    # Ocho rather than patched: `zork.py` is FROZEN at the pre-registration commit (PREREG_zork.md:
    # "the simulator ... fixed at this commit"), and a parser change is Ocho's decision, not the driver
    # author's -- editing it here would move the instrument under a criteria set that was frozen against it.
    w = Z.parse_world(open(os.path.join(HERE, "levels", "zork_01_the_floor.txt")).read())
    ck("`I will take the key` is HANDED OVER AS TYPED", first_line("I will take the key"), "I will take the key")
    # MEASURED PROPERTY (1), AND IT IS THE RESIGN DEFECT IN THE OTHER DIRECTION: `i` is a DECLARED
    # abbreviation for inventory, so a sentence that OPENS WITH `I` is read as the inventory command --
    # `parsed`, not `unparsed`. THE PARSER FINDS A COMMAND IN TEXT THAT DOES NOT CONTAIN ONE, and the
    # answer lands in `parsed` where the C3 coverage finding cannot see it. Not patched here; filed.
    ck("...and a sentence opening with `I` IS READ as the declared abbreviation for inventory",
       Z.parse_command(first_line("I will take the key"), w)[:2], ("inventory", None))
    ck("...so it lands in `parsed`, NOT in `unparsed`",
       Z.play(open(os.path.join(HERE, "levels", "zork_01_the_floor.txt")).read(),
              ["I will take the key"])["counts"],
       {"parsed": 1, "unparsed": 0, "recognised-but-impossible": 0})
    # MEASURED PROPERTY (2): a command with a trailing sentence is refused as a WHOLE, and the phrase is
    # quoted back -- strict identity, working as the prereg's boundary rule says. `north pole` resolves
    # because a direction is read from the HEAD and the rest of the line is not part of it.
    ck("...and `take the key and walk north` is REFUSED as a whole, not mined",
       Z.parse_command(first_line("take the key and walk north"), w)[0], None)
    ck("...and the refusal quotes the phrase it could not read",
       Z.parse_command(first_line("take the key and walk north"), w)[2],
       "I do not know 'key and walk north'")
    ck("...while a direction with prose after it resolves from the head",
       Z.parse_command(first_line("north pole"), w)[:2], ("go", "north"))
    ck("...and a readable command parses", Z.parse_command(first_line("take key"), w)[:2], ("take", "key"))
    ck("...and a direction parses", Z.parse_command(first_line("n"), w)[:2], ("go", "north"))

    print("\n[3] SUFFICIENCY, IN BOTH DIRECTIONS -- the record must reproduce its own score, and the")
    print("    check must FIRE when it does not")
    text = open(os.path.join(HERE, "levels", "zork_01_the_floor.txt")).read()
    good = Z.play(text, ["take key", "north"])
    rec = dict(good, level_text=text, level_digest=level_digest(
        os.path.join(HERE, "levels", "zork_01_the_floor.txt")))
    ok, detail = sufficiency_check(rec)
    ck("a record of a real run reproduces its own score", ok, True)
    ck("...and the check says which fields it compared", len(detail["fields_compared"]) > 0, True)
    tampered = json.loads(json.dumps(rec))
    tampered["trace"][0]["command"] = "look"          # the take is gone; the score must change
    ok2, detail2 = sufficiency_check(tampered)
    ck("A TAMPERED RECORD IS CAUGHT -- the check is not a check that passes by construction", ok2, False)
    ck("...and the score it recomputes is the gate_locked ending, not the escape",
       Z.play(text, [r["command"] for r in tampered["trace"]])["ending"], "gate_locked")
    stripped = {k: v for k, v in rec.items() if k != "level_text"}
    ck("...and a record with no level text is reported as unreplayable, not skipped",
       sufficiency_check(stripped)[0], False)
    ck("...and it says WHICH field was missing",
       "level_text" in sufficiency_check(stripped)[1]["why"], True)
    noscore = {k: v for k, v in rec.items() if k != "counts"}
    ck("...and a record missing a SCORED field does not reproduce", sufficiency_check(noscore)[0], False)

    print("\n[4] THE ARTIFACT PATH IS OWNED BY ONE RUN -- refusal and permission, both")
    scratch = tempfile.mkdtemp(prefix="zork_run_selftest_")
    fresh = os.path.join(scratch, "ZORK_x_zork_01_the_floor.json")
    ck("a path that does not exist is written", artifact_gate(fresh, None)[0], True)
    open(fresh, "w").write(json.dumps({"config": {"server_binary_digest": "deadbeef",
                                                  "legend_digest": "cafe", "reasoning": "off"}}))
    ok3, msg3, rep3 = artifact_gate(fresh, None)
    ck("a path that EXISTS is REFUSED", ok3, False)
    ck("...and nothing was replaced", rep3, None)
    ck("...and the message names the path and the remedy", "--overwrite-artifact" in msg3, True)
    ok4, _msg4, rep4 = artifact_gate(fresh, "the instrument changed and the cell was re-measured")
    ck("...and a replacement WITH A REASON is permitted", ok4, True)
    ck("...and it carries what it destroyed, as a digest of the bytes",
       rep4["it_named"]["reasoning"], "off")
    ck("...and the operator's reason is verbatim in the record", rep4["reason_given"],
       "the instrument changed and the cell was re-measured")
    ck("a free path needs no reason at all", artifact_gate(os.path.join(scratch, "nope.json"), None),
       (True, "", None))

    print("\n[5] THE COMPUTE PATH: the summary is READ OUT OF THE ARGV, and the eight recorded rows show why")
    global NGL, PARALLEL
    _ngl_was, _par_was = NGL, PARALLEL
    NGL, PARALLEL = 99, 1
    argv99 = server_argv("M.gguf", 4096, 58701)
    ck("with --ngl 99 the argv says -ngl 99", argv_value(argv99, "-ngl"), "99")
    ck("...and the summary field agrees with it", compute_path(argv99)["n_gpu_layers"], 99)
    ck("...and ctx agrees too", compute_path(argv99)["ctx"], 4096)
    ck("...and --parallel is carried, not dropped", compute_path(argv99)["parallel"], 1)
    NGL, PARALLEL = 0, None
    argv0 = server_argv("M.gguf", 4096, 58701)
    ck("the registered CPU launch reads back as 0 and no --parallel",
       (compute_path(argv0)["n_gpu_layers"], compute_path(argv0)["parallel"]), (0, None))
    ck("a flag that is absent reads as None, not as a plausible zero",
       argv_value(argv0, "--parallel"), None)
    # THE CONTROL IS A PAIR, AND EACH ARM NAMES ITS OWN SUBJECT (ruling 2026-10-26, R3-R5).
    #
    # ONE ARM OVER PRESERVED BYTES. The eight sitting-2 rows are the historical defect -- `n_gpu_layers 0`
    # beside `-ngl 99` -- and they are checked HERE, as a fixture pinned by digest in PRESERVED_FIXTURE,
    # never as "whatever is in probes/". The claim is about committed history, so `git checkout` of an
    # unrelated commit cannot turn it red (R1).
    #
    # ONE ARM OVER THE LIVE ARCHIVE, ASSERTING AGREEMENT. `probes/` is a working directory by design: what
    # sits in it changes when the instrument changes. The invariant that holds over it now -- every row
    # agrees with itself, and nothing is said about the past -- is what goes red the day a writer
    # regresses. That is the arm that would have caught the defect, and the arm the previous two
    # replaced: they asserted the DEFECT was present in the live archive, so a repair to the writer read
    # as a regression and fixing it was vetoed (R2).
    #
    # AND NEITHER SUBJECT MAY BE ABSENT. A missing fixture file or a missing `probes/` is a RED arm, never
    # a skipped one: the old `if _rows:` guard is why the same bytes once printed `62/62` with no
    # `probes/` beside them, the run that saw the least evidence printing the most reassuring line (R4).
    import glob as _glob
    _pres = []
    for _rel, _dig, _n in PRESERVED_FIXTURE:
        try:
            _pres.append((_rel, open(os.path.join(HERE, _rel), "rb").read(), _dig, _n))
        except OSError:
            continue                                  # a missing file is a short count, never a skip
    ck("the eight preserved fixture rows are present and unmodified: pinned sha256, eight literal paths",
       sum(1 for _rel, _raw, _dig, _n in _pres
           if len(_raw) == _n and hashlib.sha256(_raw).hexdigest() == _dig),
       len(PRESERVED_FIXTURE))
    _pairs = []
    for _rel, _raw, _dig, _n in _pres:
        _cfg = json.loads(_raw).get("config", {})
        _pairs.append((_cfg.get("n_gpu_layers"), argv_value(_cfg.get("server_argv", []), "-ngl")))
    ck("THE PRESERVED FIXTURE STILL CONTRADICTS ITSELF: all eight say n_gpu_layers 0 against -ngl 99",
       sum(1 for _s, _l in _pairs if str(_s) == "0" and str(_l) == "99"), len(PRESERVED_FIXTURE))
    ck("...and the contradiction is exactly (0, '99') on all eight preserved rows",
       sorted({(_s, _l) for _s, _l in _pairs}, key=lambda _t: (str(_t[0]), str(_t[1]))),
       [(0, "99")])
    _live = sorted(_glob.glob(os.path.join(HERE, "probes", "ZORK_*.json")))
    ck("the live archive at probes/ZORK_*.json has rows -- an absent archive is RED, not a skipped arm",
       len(_live) > 0, True)
    _disagree = []
    for _p in _live:
        _cfg = json.load(open(_p)).get("config", {})
        _said, _launched = _cfg.get("n_gpu_layers"), argv_value(_cfg.get("server_argv", []), "-ngl")
        if str(_said) != str(_launched):              # a row with no -ngl at all disagrees too
            _disagree.append((os.path.basename(_p), _said, _launched))
    ck("every LIVE row agrees with itself: config.n_gpu_layers == config.server_argv -ngl",
       len(_disagree), 0)
    for _n, _s, _l in _disagree:
        print(f"          disagrees: {_n}  said {_s!r}  launched {_l!r}")
    print(f"        {sum(1 for _s, _l in _pairs if str(_s) == '0' and str(_l) == '99')} preserved rows "
          f"still carry the defect (0 against '99'); {len(_live)} live rows, "
          f"{len(_disagree)} of them disagreeing.")
    NGL, PARALLEL = _ngl_was, _par_was

    print("\n[6] THE AXIS AND THE PROGRESS BLOCK ARE CARRIED, AND SUFFICIENCY CHECKS THEM")
    text = open(os.path.join(HERE, "levels", "zork_02_long_crawl.txt")).read()
    run = Z.play(text, ["north", "take brasskey", "south", "east", "north", "east"])
    rec = dict(run, level_text=text, level_digest=level_digest(
        os.path.join(HERE, "levels", "zork_02_long_crawl.txt")))
    ok, detail = sufficiency_check(rec)
    ck("a record carrying the axis reproduces its own score", ok, True)
    ck("...and the check says the axis was MEASURED, not skipped", detail["axis_measured"], True)
    ck("...comparing all three axis fields", detail["axis_fields_compared"], list(AXIS_FIELDS))
    ck("...and the replay route now names WHICH take it read", "REQUIRED ITEM" in detail["replay_basis"], True)
    bad_axis = json.loads(json.dumps(rec))
    bad_axis["attribution"]["accepted"] += 1
    ck("A TAMPERED ATTRIBUTION TOTAL IS CAUGHT BY SUFFICIENCY", sufficiency_check(bad_axis)[0], False)
    bad_row = json.loads(json.dumps(rec))
    bad_row["trace"][1]["attribution"] = Z.ATTR_UNATTRIBUTABLE
    ck("...and so is a tampered PER-ROW attribution", sufficiency_check(bad_row)[0], False)
    old = {k: v for k, v in rec.items() if k not in AXIS_FIELDS}
    ok_old, detail_old = sufficiency_check(old)
    ck("a record with NO axis is reported as axis_measured: false", detail_old["axis_measured"], False)
    ck("...and is not failed for a field it was never asked to carry", ok_old, True)

    print("\n[7] THE REPLAY FALSE ALARM -- two records cried instrument-failure and the record was fine")
    # THE DISTRACTOR CASE IS THE ONE THAT BROKE. An entrant that takes the torch before the key gets two
    # different `took_item_at_step` readings, and the OLD call -- with no required item -- filed the
    # record as unreproducible. The record is reproduced here in both directions.
    torch_first = Z.play(text, ["take torch", "north", "take brasskey", "south", "east", "north", "east"])
    rec_tf = dict(torch_first, level_text=text)
    ck("the torch-first crawl takes the required item at step 2", rec_tf["took_item_at_step"], 2)
    ok_tf, det_tf = sufficiency_check(rec_tf)
    ck("...and its record REPRODUCES -- no false instrument failure", ok_tf, True)
    ck("...with the replay reading the REQUIRED take", det_tf["simulator_replay_mismatched"], [])
    ck("THE OLD CALL WOULD HAVE MISMATCHED, and this asserts it so the fix is not invisible",
       Z.replay(rec_tf["trace"], rec_tf["start_room"])["took_item_at_step"], 0)
    ck("...while the fixed call returns what the field claims",
       Z.replay(rec_tf["trace"], rec_tf["start_room"], required_item="brasskey")["took_item_at_step"], 2)

    print("\n" + "=" * 100)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{total - len(fails)}/{total}")
    print("=" * 100)
    return 1 if fails else 0


def main():
    global LLAMA_SELECTED, ARTIFACT_OVERRIDE, NGL
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrant")
    ap.add_argument("--level")
    ap.add_argument("--cap", type=int, default=COMMAND_CAP)
    ap.add_argument("--port", type=int, default=8752)
    ap.add_argument("--self-test", action="store_true")
    # THE ESCAPE HATCH CARRIES A REASON RATHER THAN A FORCE: the gate above refuses to write over a record
    # this run did not take, and a replacement still has to be possible -- but a gate with an override that
    # is not written down is a gate nobody can audit.
    ap.add_argument("--overwrite-artifact", dest="overwrite_artifact", default=None, metavar="REASON",
                    help="replace the record already at this cell's artifact path, saying WHY. The reason "
                         "is written into the replacement beside the digest of the record it replaced.")
    ap.add_argument("--llama-server", dest="llama_server", default=None,
                    help="path to the llama-server BINARY to run (default: the declared default). A "
                         "Bonsai ternary gguf needs the PrismML fork; the binary's digest is recorded.")
    ap.add_argument("--ngl", type=int, default=NGL_DECLARED,
                    help="--n-gpu-layers for the entrant's server (default: the registered %d). A "
                         "COMPUTE-PATH field only: the prompt and the scorer are untouched, and the "
                         "value travels in the argv the server is started with." % NGL_DECLARED)
    ap.add_argument("--parallel", type=int, default=PARALLEL_DECLARED,
                    help="--parallel for the entrant's server (default: the registered launch, which "
                         "passes no such flag). A COMPUTE-PATH field; the value travels in the argv.")
    a = ap.parse_args()
    global PARALLEL
    NGL = a.ngl
    PARALLEL = a.parallel
    if a.self_test:
        return _self_test()
    if not a.entrant or not a.level:
        ap.error("--entrant and --level are required")
    if a.llama_server:
        # A PATH THAT DOES NOT EXIST OR IS NOT EXECUTABLE IS REFUSED HERE RATHER THAN HANDED TO exec:
        # `--llama-server /typo` would otherwise surface as a launch failure and read like a broken model.
        sel = os.path.expanduser(a.llama_server)
        if not (os.path.exists(sel) and os.access(sel, os.X_OK)):
            print(f"  BINARY ABSENT OR NOT EXECUTABLE: {a.llama_server}")
            return 2
        LLAMA_SELECTED = sel
    p = a.entrant if os.path.exists(a.entrant) else os.path.join(MODELS, a.entrant)
    if not os.path.exists(p):
        print(f"  ENTRANT ABSENT: {a.entrant}")
        return 2

    # ---- THE ARTIFACT GATE, AT ADMISSION -- BEFORE ANY SERVER IS SPAWNED -------------------------
    out = artifact_path(p, a.level)
    if a.overwrite_artifact is not None and not a.overwrite_artifact.strip():
        print("  --overwrite-artifact WAS GIVEN AN EMPTY REASON: a replacement has to say why. Nothing "
              "written.")
        return 2
    ARTIFACT_OVERRIDE = a.overwrite_artifact
    gate_ok, gate_msg, replaced = artifact_gate(out, ARTIFACT_OVERRIDE)
    if not gate_ok:
        for line in gate_msg.splitlines():
            print(f"  {line}")
        return 4

    r = run(p, a.level, a.cap, a.port)
    print(f"  entrant   {r['entrant']}")
    print(f"  level     {r['level']}")
    if LLAMA_SELECTED:
        print(f"  binary    {LLAMA_SELECTED}  (server_binary_digest {binary_digest()})")
    os.makedirs(os.path.join(HERE, "probes"), exist_ok=True)
    if replaced is not None:
        r["artifact_replaced"] = replaced
    json.dump(r, open(out, "w"), indent=1)
    print(f"  artifact  {os.path.relpath(out, HERE)}")
    if replaced is not None:
        print(f"  REPLACED  {replaced['path']}  ({replaced['bytes']} B, sha256 "
              f"{replaced['sha256'][:16]}...) -- reason given: {replaced['reason_given']!r}")
    if not r.get("loaded"):
        print(f"  DID NOT LOAD -- {r['why']}")
        return 3
    print(f"  ended     {r['ended']}    finished={r['finished']}    carried_item={r['carried_required_item']}"
          f"    took_item_at_step={r['took_item_at_step']}")
    print(f"  counts    parsed={r['counts']['parsed']}  unparsed={r['counts']['unparsed']}  "
          f"recognised-but-impossible={r['counts']['recognised-but-impossible']}")
    print(f"  route     {' -> '.join(r['rooms_visited'])}")
    print(f"  commands  {[t['command'] for t in r['turns']]}")
    print(f"  sufficiency  reproduces={r.get('sufficiency_ok')}")
    if not r.get("sufficiency_ok"):
        print("  THE RECORD DOES NOT REPRODUCE ITS OWN SCORE. THIS IS NOT A RESULT -- it is an instrument "
              "failure, and the number above it must not be filed.")
        return 6
    return 0


if __name__ == "__main__":
    sys.exit(main())
