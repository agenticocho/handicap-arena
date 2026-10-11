#!/usr/bin/env python3
# sokoban2_run.py -- THE RUNNER and THE SCORER for the independent Sokoban
# cabinet.  Second implementation.
#
#   * it gives the task (build_prompt, from the simulator -- never built here)
#   * it collects the answer
#   * IT CHECKS THE ANSWER BY EXECUTING IT (feed() -> step()) -- never by
#     reading it and comparing it to a solution string
#   * IT WRITES THE RECORD TO DISK BEFORE THE SUCCESS/FAILURE BRANCH
#   * it records the model file's DIGEST, not only its name
#   * it records WHICH CODE produced the verdict, not only the verdict
#   * it records the REASONING SETTING and the GPU, per run
#   * a failed load NAMES THE HOLDER, never "failed to load"
#   * the exit code reflects the run, and the self-test drives every path that
#     returns one
#
# Stdlib only.

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from sokoban_reader import (OUTCOME_ACTION, OUTCOME_GIVE_UP,   # noqa: E402
                            OUTCOME_NOT_AN_ACTION, grammar_as_record,
                            read_answer, reader_sha256)
import sokoban2                                                # noqa: E402
from sokoban2 import (State, build_prompt, check_prompt_legal,  # noqa: E402
                      feed, find_level, load_level, render)
import sokoban2_solve                                          # noqa: E402

HARNESS = "handicap-arena"
VERSION = "1.0"
EVENT = "SOKOBAN"
CARD_VERSION = "sokoban_v1"
TASKS = "sokoban2/tasks/sokoban_v1.json"
LEVEL_FILES = sokoban2.LEVEL_FILES

#: The budget.  NOT in the frozen artifacts.  [G13]  The dossier says "NO TIME
#: LIMIT -- the cap is the budget, not the clock" and its own control is
#: "fifty wall bumps".  Fifty is a control, not a budget.  This is a declared
#: parameter of the run, recorded in every bundle, because `attempted` and
#: `blocked` have no ceiling without it and two runs with different budgets are
#: not comparable.
DEFAULT_ATTEMPT_BUDGET = 60

#: The number of times the runner may hand an unreadable answer back to the
#: entrant with a correction.  [G14]  NOT in the frozen artifacts.  Zero means
#: one malformed answer ends the level.
DEFAULT_RETRIES = 2

# ---------------------------------------------------------------------------
# EXIT CODES -- declared, printed, and exercised by the self-test.
#
# The defect this table exists for: a CLI that returned 1 for EVERY real
# invocation while its self-test reported all green, because the self-test
# never reached the code path that raised.  So every code below is produced by
# a path the self-test actually calls.
# ---------------------------------------------------------------------------
EXIT_SCORED = 0                # measured > 0 and the harness is sound
EXIT_INSTRUMENT = 1            # the INSTRUMENT is not proven (self-test /
                               # instrument-check / level verification failed)
EXIT_ZERO_MEASURED = 2         # ZERO RULE: a run with no measured entrant is
                               # an ERROR, never a verdict
EXIT_USAGE = 3                 # unknown entrant, bad arguments, never-started
                               # is NOT this -- see EXIT_NEVER_STARTED
EXIT_NEVER_STARTED = 4         # the entrant never loaded: counted separately
                               # from played-and-failed, because they are
                               # different claims
EXIT_WRITE_FAILED = 5          # the record could not be written.  A run with
                               # no record is not a run.

EXIT_CODES = {
    EXIT_SCORED: "SCORED -- measured > 0, harness sound",
    EXIT_INSTRUMENT: "INSTRUMENT NOT PROVEN -- self-test / instrument-check / "
                     "level verification failed",
    EXIT_ZERO_MEASURED: "ZERO MEASURED -- ERROR, never a verdict "
                        "(grammar section 4)",
    EXIT_USAGE: "USAGE -- unknown entrant or bad arguments",
    EXIT_NEVER_STARTED: "ENTRANT NEVER STARTED -- counted separately from "
                        "played-and-failed",
    EXIT_WRITE_FAILED: "RECORD NOT WRITTEN -- a run with no record is not a run",
}


def _sha256_of(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def _sha256_of_source(path):
    return _sha256_of(path)


# ---------------------------------------------------------------------------
# 1. THE HOLDER -- a failed load must NAME THE HOLDER, never "failed to load"
# ---------------------------------------------------------------------------

def _proc_comm(pid):
    try:
        with open("/proc/%s/comm" % pid) as fh:
            return fh.read().strip()
    except OSError:
        return None


def _proc_cmdline(pid):
    try:
        with open("/proc/%s/cmdline" % pid) as fh:
            return fh.read().replace("\0", " ").strip()
    except OSError:
        return None


def _proc_holders_for_path(path):
    """Fallback probe: which PID has this file open?  Linux /proc only."""
    try:
        target = os.path.realpath(path)
    except OSError:
        target = path
    out = []
    try:
        pids = [d for d in os.listdir("/proc") if d.isdigit()]
    except OSError:
        return None                      # not a /proc host: probe unavailable
    for pid in pids:
        fdd = "/proc/%s/fd" % pid
        try:
            fds = os.listdir(fdd)
        except OSError:
            continue
        for fd in fds:
            try:
                link = os.readlink(os.path.join(fdd, fd))
            except OSError:
                continue
            if link == target:
                out.append({"pid": pid, "command": _proc_comm(pid),
                            "cmdline": _proc_cmdline(pid), "raw": link})
                break
    return out


def _proc_holders_for_port(port):
    """Fallback probe: which PID is LISTENing on this TCP port?  /proc/net/tcp
    gives socket inodes; /proc/<pid>/fd maps them back to a process."""
    try:
        port = int(port)
    except (TypeError, ValueError):
        return None
    hexport = "%04X" % port
    inodes = set()
    for f in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(f) as fh:
                lines = fh.read().splitlines()[1:]
        except OSError:
            continue
        for ln in lines:
            parts = ln.split()
            if len(parts) < 10:
                continue
            local, state, inode = parts[1], parts[3], parts[9]
            try:
                lport = local.rsplit(":", 1)[1].upper()
            except IndexError:
                continue
            if state == "0A" and lport == hexport:      # 0A == TCP_LISTEN
                inodes.add(inode)
    if not inodes:
        return []
    want = {"socket:[%s]" % i for i in inodes}
    out = []
    for pid in [d for d in os.listdir("/proc") if d.isdigit()]:
        fdd = "/proc/%s/fd" % pid
        try:
            fds = os.listdir(fdd)
        except OSError:
            continue
        hit = None
        for fd in fds:
            try:
                link = os.readlink(os.path.join(fdd, fd))
            except OSError:
                continue
            if link in want:
                hit = link
                break
        if hit:
            out.append({"pid": pid, "command": _proc_comm(pid),
                        "cmdline": _proc_cmdline(pid), "socket": hit,
                        "inodes": sorted(inodes)})
    return out


def probe_holder(resource, kind="port"):
    """Who is holding this?  -> a dict NAMING THE PROCESS, or a dict saying
    which probe ran and found nobody.

    'failed to load' is not a finding.  If a model will not load because
    something else has the port, or because the weights are held open by a live
    server, the record says WHICH PROCESS, by pid and command -- or it names the
    probe that found nobody, so a null reads as 'nobody found, by this method'
    and not 'nobody asked'.

    Two probes, tried in order: `lsof`, then Linux /proc.  Both are named in the
    record, so a reader can see which one answered.
    """
    out = {"resource": resource, "kind": kind, "probe": None,
           "holder": None, "note": None, "probes_tried": []}

    if kind == "port":
        lsof_args = ["lsof", "-nP", "-iTCP:%s" % resource, "-sTCP:LISTEN"]
        lsof_name = "lsof -nP -iTCP:%s -sTCP:LISTEN" % resource
        try:
            p = subprocess.run(lsof_args, capture_output=True, text=True,
                               timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            out["probes_tried"].append(
                {"probe": lsof_name, "result": "unavailable: %r" % (exc,)})
        else:
            lines = [ln for ln in (p.stdout or "").splitlines()[1:]
                     if ln.strip()]
            out["probes_tried"].append(
                {"probe": lsof_name, "result": "%d holder(s)" % len(lines)})
            if lines:
                parts = lines[0].split()
                out["probe"] = lsof_name
                out["holder"] = {
                    "command": parts[0] if parts else None,
                    "pid": parts[1] if len(parts) > 1 else None,
                    "user": parts[2] if len(parts) > 2 else None,
                    "raw": lines[0], "n_holders": len(lines)}
                return out
        found = _proc_holders_for_port(resource)
        out["probe"] = ("lsof (unavailable or no holder) -> "
                        "/proc/net/tcp + /proc/<pid>/fd")
        out["probes_tried"].append(
            {"probe": "/proc/net/tcp + /proc/<pid>/fd",
             "result": "unavailable" if found is None
                       else "%d holder(s)" % len(found)})
        if found is None:
            out["note"] = ("NO PROBE AVAILABLE on this host (neither lsof nor "
                           "/proc). The holder is UNKNOWN, and it is NOT "
                           "recorded as 'none'.")
        elif found:
            out["holder"] = {"n_holders": len(found), "holders": found}
        else:
            out["note"] = ("probe ran and named nobody: nothing is LISTENing "
                           "on %s, so the holder is not a live process"
                           % resource)
        return out

    if kind == "path":
        lsof_args = ["lsof", "-nP", "--", resource]
        lsof_name = "lsof -nP -- %s" % resource
        try:
            p = subprocess.run(lsof_args, capture_output=True, text=True,
                               timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            out["probes_tried"].append(
                {"probe": lsof_name, "result": "unavailable: %r" % (exc,)})
        else:
            lines = [ln for ln in (p.stdout or "").splitlines()[1:]
                     if ln.strip()]
            out["probes_tried"].append(
                {"probe": lsof_name, "result": "%d holder(s)" % len(lines)})
            if lines:
                out["probe"] = lsof_name
                out["holder"] = [
                    {"command": ln.split()[0],
                     "pid": ln.split()[1] if len(ln.split()) > 1 else None,
                     "raw": ln} for ln in lines]
                return out
        found = _proc_holders_for_path(resource)
        out["probe"] = ("lsof (unavailable or no holder) -> "
                        "/proc/<pid>/fd symlinks")
        out["probes_tried"].append(
            {"probe": "/proc/<pid>/fd",
             "result": "unavailable" if found is None
                       else "%d holder(s)" % len(found)})
        if found is None:
            out["note"] = ("NO PROBE AVAILABLE on this host (neither lsof nor "
                           "/proc). The holder is UNKNOWN, and it is NOT "
                           "recorded as 'none'.")
        elif found:
            out["holder"] = found
        else:
            out["note"] = ("probe ran and named nobody: no process holds %s "
                           "open" % resource)
        return out

    out["note"] = "no probe defined for kind %r" % (kind,)
    return out


# ---------------------------------------------------------------------------
# 2. THE GPU -- declared per run, because a setting nobody wrote down is
#    indistinguishable from a decision
# ---------------------------------------------------------------------------

def probe_gpu():
    """-> a dict.  The probe that ran is always named.  No GPU is NOT recorded
    as 0 GB or as the string 'none': a machine with no probe is not a machine
    with no GPU, and those are different claims."""
    gpu = {"probe": None, "name": None, "index": None,
           "memory_total_gb": None, "memory_free_gb": None,
           "driver": None, "n_devices": None,
           "note": None, "raw": None}

    try:
        p = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,name,memory.total,memory.free,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        p = None
        gpu["note"] = "nvidia-smi not runnable: %r" % (exc,)

    if p is not None and p.returncode == 0 and (p.stdout or "").strip():
        rows = [ln.strip() for ln in p.stdout.strip().splitlines() if ln.strip()]
        gpu["probe"] = ("nvidia-smi --query-gpu=index,name,memory.total,"
                        "memory.free,driver_version")
        gpu["n_devices"] = len(rows)
        cells = [c.strip() for c in rows[0].split(",")]
        try:
            gpu["index"] = int(cells[0])
            gpu["name"] = cells[1]
            gpu["memory_total_gb"] = round(float(cells[2]) / 1024.0, 3)
            gpu["memory_free_gb"] = round(float(cells[3]) / 1024.0, 3)
            gpu["driver"] = cells[4] if len(cells) > 4 else None
        except (ValueError, IndexError):
            gpu["note"] = "nvidia-smi output not parsed: %r" % (rows[0],)
        gpu["raw"] = rows
        return gpu

    if p is not None:
        gpu["probe"] = "nvidia-smi (exited %s)" % p.returncode
        gpu["note"] = (gpu["note"] or ("nvidia-smi exited %s: %s"
                                       % (p.returncode,
                                          (p.stderr or "").strip()[:200])))
        return gpu

    # No nvidia-smi at all.  Say which box this is and that no accelerator was
    # found by a probe that actually ran -- never 0.00, never "none".
    gpu["probe"] = ("nvidia-smi (absent) -> host is %s %s"
                    % (platform.system(), platform.machine()))
    gpu["note"] = ("NO ACCELERATOR FOUND by this probe. Recorded as null, not "
                   "0.00 and not 'none': an unprobed machine is not a machine "
                   "with no GPU. A model run on this host is CPU-only and its "
                   "numbers are not comparable to a GPU run.")
    return gpu


def host_block():
    return {
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "gpu": probe_gpu(),
    }


# ---------------------------------------------------------------------------
# 3. ENTRANTS
# ---------------------------------------------------------------------------

class Entrant(object):
    """An entrant answers ONE TURN AT A TIME, in prose, and its answer is read
    by the reader of record and executed by the simulator."""
    kind = "?"
    is_model = False
    instrument = "code"

    def start(self):
        """Admission. -> (rc, secs, started, holder_or_None)"""
        return 0, 0.0, True, None

    def answer(self, prompt, view):
        raise NotImplementedError

    def weights_info(self):
        return None


class _Planner(Entrant):
    """Base for entrants that replay a fixed per-level letter stream."""

    def __init__(self, plans=None):
        self.plans = plans or {}
        self._i = {}

    def answer(self, prompt, view):
        name = view["level"]
        i = self._i.get(name, 0)
        self._i[name] = i + 1
        plan = self.plans.get(name, "")
        if i < len(plan):
            return plan[i]
        return "GIVE UP"


class ReferenceSolver(Entrant):
    """Plays OPTIMALLY, one letter per turn, recomputed from the live position
    by the exhaustive solver.  The REFERENCE, not a contestant: it proves the
    harness end to end.  It is not on the board."""
    kind = "reference-solver"

    def answer(self, prompt, view):
        st = view["state"]
        level = st.level
        ok, depth = sokoban2_solve.is_solvable(level, frozenset(st.boxes),
                                               st.player)
        if ok is False:
            # The position is provably dead.  The reference ABSTAINS, which is
            # the behaviour the cabinet exists to measure.
            return "GIVE UP"
        if ok is None:
            return "GIVE UP"
        res = sokoban2_solve.solve(_at(level, st.boxes, st.player))
        return res["plan"][0] if res["plan"] else "GIVE UP"


def _at(level, boxes, player):
    """A Level whose start position is the CURRENT position -- so the solver
    can be asked about a mid-game state."""
    import copy
    sub = sokoban2.Level(
        name=level.name, text=level.text, sha256=level.sha256,
        walls=level.walls, targets=level.targets,
        start_boxes=frozenset(boxes), start_player=player,
        height=level.height, width=level.width, enclosed=level.enclosed,
        ragged=level.ragged)
    return sub


class Liar(Entrant):
    """Emits legal letters that never solve anything.  Plausible, wrong."""
    kind = "adversarial-reference"

    def __init__(self):
        self._n = 0

    def answer(self, prompt, view):
        self._n += 1
        return ("RDLU" * 4)[self._n % 16]


class Garbage(Entrant):
    """Prose.  Must read not_an_action, never a move."""
    kind = "malformed-reference"

    def answer(self, prompt, view):
        return ("Sure! The best move here is to push the crate toward the "
                "target, you should aim for the dot.")


class NeverStarts(Entrant):
    """The population-does-not-load case.  Must be counted SEPARATELY from
    played-and-failed -- different claims."""
    kind = "never-started-reference"

    def start(self):
        return 2, 0.0, False, probe_holder("(no resource: no weights)",
                                           kind="path")

    def answer(self, prompt, view):
        raise AssertionError("must never be asked -- the run never started")


class WallBumper(Entrant):
    """The dossier's control: 50 attempts, 0 moves.  A naive counter would call
    it a long game."""
    kind = "wall-bumper-reference"

    def answer(self, prompt, view):
        return "L"


class Resigner(Entrant):
    """Abstains immediately on every level.  Tests the give_up path -- the
    counter the cabinet's faculty depends on."""
    kind = "abstainer-reference"

    def answer(self, prompt, view):
        return "RESIGN"


class SoftResigner(Entrant):
    """Abstains the way a model actually would -- in a sentence.

    Under the STRICT token rule this is not_an_action, not give_up.  This
    entrant exists to MEASURE that: it is the instrument's own finding, and it
    is the reason [G1] is on the ambiguities list.
    """
    kind = "soft-abstainer-reference"

    def answer(self, prompt, view):
        return "I give up, there is no way to finish this one."


class CornerWalker(Entrant):
    """Walks into the dead end on level 03 and KEEPS PLAYING.  The failure the
    cabinet exists to measure, in its expensive direction."""
    kind = "dead-end-walker-reference"

    def __init__(self):
        self._i = {}

    def answer(self, prompt, view):
        name = view["level"]
        i = self._i.get(name, 0)
        self._i[name] = i + 1
        if name == "03_the_corner_waiting.txt":
            # up, then push the crate right into the waiting corner, then
            # demonstrate that it cannot be recovered.
            return ("URLRLDU")[i % 7]
        if name == "01_one_push.txt":
            return "U"                       # a wall, forever
        return "L"


class ModelEntrant(Entrant):
    """A served GGUF, reached over llama.cpp's HTTP API.

    The record carries the model file's DIGEST, not only its name: two
    same-named files in two directories is otherwise an unresolvable confound.
    """
    kind = "model"
    is_model = True
    instrument = "model"

    def __init__(self, model_path=None, server_url="http://127.0.0.1:8080",
                 port=8080):
        self.model_path = model_path
        self.server_url = server_url
        self.port = port

    def weights_info(self):
        info = {"path": self.model_path,
                "name": os.path.basename(self.model_path)
                        if self.model_path else None,
                "sha256": None, "bytes": None, "note": None}
        if not self.model_path or not os.path.isfile(self.model_path):
            info["note"] = ("NOT MEASURED -- model path %r is not a file, so "
                            "no digest exists to record. The NAME is carried "
                            "and the DIGEST is null WITH THIS REASON: never "
                            "0, never a name standing in for a digest, and "
                            "never a missing digest with no explanation."
                            % (self.model_path,))
            return info
        info["sha256"] = _sha256_of(self.model_path)
        try:
            info["bytes"] = os.path.getsize(self.model_path)
        except OSError:
            info["bytes"] = None
        return info

    def start(self):
        """Admission for a served model: the port must be LISTENing, and the
        server must answer /health.  A failure NAMES THE HOLDER."""
        t0 = time.perf_counter()
        if self.model_path and not os.path.isfile(self.model_path):
            return (2, round(time.perf_counter() - t0, 3), False,
                    probe_holder(self.model_path, kind="path"))
        try:
            import urllib.request
            with urllib.request.urlopen(self.server_url.rstrip("/")
                                        + "/health", timeout=10) as resp:
                body = resp.read(64)
            return (0, round(time.perf_counter() - t0, 3), True, None) \
                if body is not None else (0, 0.0, True, None)
        except Exception as exc:                                # noqa: BLE001
            holder = probe_holder(str(self.port), kind="port")
            holder["load_error"] = "%s: %s" % (type(exc).__name__, exc)
            return 2, round(time.perf_counter() - t0, 3), False, holder

    def answer(self, prompt, view):
        import urllib.request
        payload = json.dumps({
            "prompt": prompt, "n_predict": int(view.get("max_tokens", 8)),
            "temperature": float(view.get("temperature", 0.0)),
            "stop": ["\n"], "cache_prompt": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.server_url.rstrip("/") + "/completion",
            data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("content", "")


ENTRANTS = {
    "reference": ReferenceSolver,
    "liar": Liar,
    "garbage": Garbage,
    "never-starts": NeverStarts,
    "wall-bumper": WallBumper,
    "resigner": Resigner,
    "soft-resigner": SoftResigner,
    "corner-walker": CornerWalker,
    "model": ModelEntrant,
}

#: Entrants that are CODE.  A code entrant is a DIFFERENT INSTRUMENT and is
#: never pooled into a model table.  (Darts A1, applied.)
ON_BOARD = {"model"}


# ---------------------------------------------------------------------------
# 4. THE ROUND -- one level, played to its end
# ---------------------------------------------------------------------------

def play_level(level, entrant, budget, retries, max_tokens, temperature):
    """Play one level to its end.  -> dict.

    The answer is CHECKED BY EXECUTING IT.  `feed()` reads it with the one
    reader and runs it through `step()`.  Nothing here compares the answer to
    the known solution; the board decides `solved`.
    """
    state = State(level)
    history = []
    corrections = 0
    corrections_ignored = 0
    raws = []
    dead_diag = []

    t0 = time.perf_counter()
    while not state.ended and state.attempted < budget:
        prompt = build_prompt(level, state.render(), history, state.moves,
                              state.solved)
        view = {"level": level.name, "state": state,
                "max_tokens": max_tokens, "temperature": temperature}
        raw = entrant.answer(prompt, view)
        raws.append(raw)
        before_na = state.not_an_action
        ply = feed(state, raw)
        ply["raw"] = raw
        ply["prompt_was"] = "SHA256:" + hashlib.sha256(
            prompt.encode("utf-8")).hexdigest()[:16]

        # -- the dead-end DIAGNOSTIC.  Recorded, NEVER scored. -------------
        if ply.get("outcome") in ("moved", "pushed"):
            ok, depth = sokoban2_solve.is_solvable(
                level, frozenset(state.boxes), state.player)
            dead_diag.append({"attempt": state.attempted,
                              "solvable_after": ok,
                              "to_go": depth})
            ply["solvable_after"] = ok
            ply["moves_to_go"] = depth

        if state.not_an_action > before_na and retries > 0 \
                and corrections < retries:
            corrections += 1
            # "it ignored the correction" vs "it tried and failed" must be
            # distinguishable: we OFFER a correction and record how many were
            # offered and whether the entrant ever produced a legal action.
            continue
        history.append(ply.get("action") or "?")

    secs = round(time.perf_counter() - t0, 3)
    never_acted = (state.moves == 0 and state.blocked == 0)
    if corrections and never_acted:
        corrections_ignored = corrections

    # -- THE TERMINAL REASON.  Which code decided, and why. -----------------
    # ORDER MATTERS and is deliberate: "never produced a legal action" is a more
    # specific finding than "ran out of budget", and the brief requires the two
    # to be distinguishable.  Budget exhaustion is recorded separately, below,
    # so nothing is lost by ranking it last.
    if state.solved:
        term = "SOLVED"
    elif state.gave_up:
        term = "GAVE_UP"
    elif state.moves == 0 and state.blocked == 0:
        term = "NO_LEGAL_ACTION_PRODUCED"
    elif state.moves == 0 and state.blocked > 0:
        term = "WALL_BUMPED_ONLY"          # it tried, and the wall said no
    elif state.attempted >= budget:
        term = "BUDGET_EXHAUSTED"
    else:
        term = "UNSOLVED"

    return {
        "level": level.name,
        "level_sha256": level.sha256,
        "solved": state.solved,
        "moves": state.moves,
        "attempted": state.attempted,
        "blocked": state.blocked,
        "not_an_action": state.not_an_action,
        "after_end": state.after_end,
        "give_up": state.give_up,
        "gave_up": state.gave_up,
        "gave_up_at": state.gave_up_at,
        "ended": state.ended,
        "terminal": term,
        "budget": budget,
        "budget_exhausted": state.attempted >= budget,
        "corrections_offered": corrections,
        "corrections_ignored": corrections_ignored,
        "never_produced_a_legal_action": never_acted,
        "produced_a_legal_action": not never_acted,
        "final_board": state.render(),
        "board_is": "BOARD AFTER THE LAST MOVE",
        "trace": state.trace,
        "dead_end_diagnostic": dead_diag,
        "secs": secs,
        "prompt_legal": check_prompt_legal(build_prompt(
            level, level.text.strip("\n"), [], 0, False)) == [],
    }


# ---------------------------------------------------------------------------
# 5. THE RUN
# ---------------------------------------------------------------------------

def run_entrant(entrant, levels, budget=DEFAULT_ATTEMPT_BUDGET,
                retries=DEFAULT_RETRIES, max_tokens=8, temperature=0.0):
    rc, secs, started, holder = entrant.start()
    admission = {"rc": rc, "secs": secs, "started": bool(started),
                 "never_started": (not started), "holder": holder}

    items = {}
    if started:
        for name in LEVEL_FILES:
            items[name] = play_level(levels[name], entrant, budget, retries,
                                     max_tokens, temperature)
    else:
        for name in LEVEL_FILES:
            items[name] = {
                "level": name, "level_sha256": levels[name].sha256,
                "solved": False, "moves": 0, "attempted": 0, "blocked": 0,
                "not_an_action": 0, "after_end": 0, "give_up": 0,
                "gave_up": False, "gave_up_at": None,
                "ended": False, "terminal": "NEVER_STARTED",
                "budget": budget, "budget_exhausted": False,
                "corrections_offered": 0, "corrections_ignored": 0,
                "never_produced_a_legal_action": True,
                "produced_a_legal_action": False,
                # NOT null.  The board after zero moves is the start board, and
                # that is a fact, not a measurement we did not take.  A null
                # board would be a missing field wearing the clothes of an
                # honest one; `board_is` says which it is.
                "final_board": render(levels[name],
                                      set(levels[name].start_boxes),
                                      levels[name].start_player),
                "board_is": "START BOARD -- the entrant never moved; this is "
                            "the level's initial state, not a result",
                "trace": [], "dead_end_diagnostic": [],
                "secs": 0.0, "prompt_legal": None,
                "reason": "entrant never started (rc=%s in %ss); holder: %s"
                          % (rc, secs, (holder or {}).get("holder")),
            }

    started_n = sum(1 for it in items.values() if it["terminal"]
                    != "NEVER_STARTED")
    measured = sum(1 for it in items.values()
                   if it["terminal"] != "NEVER_STARTED"
                   and (it["attempted"] > 0))
    # measured, for the zero rule, means: an entrant TOOK A TURN and the run
    # produced at least one READABLE token.  An all-unreadable run is a broken
    # READER, not a failed population (darts A6, applied here).
    readable = sum(1 for it in items.values()
                   if it["attempted"] > it["not_an_action"])
    solved_n = sum(1 for it in items.values() if it["solved"])
    planned = len(LEVEL_FILES)
    never_started_n = planned - started_n

    coverage = round(started_n / float(planned), 6) if planned else 0.0
    # The score: the read grammar makes `moves` the score, but the dossier's
    # gate is a RATE, so the round carries BOTH and names which is which.
    # [G15] THE SCORE OF A SOKOBAN RUN IS NOT DEFINED BY THE FROZEN ARTIFACTS.
    score = round(solved_n / float(started_n), 6) if started_n else None

    if not started or started_n == 0:
        verdict = "ERROR: POPULATION NEVER STARTED"
        exit_code = EXIT_NEVER_STARTED
    elif readable == 0:
        # ZERO RULE -- grammar section 4: a run with zero measured entrants is
        # an ERROR, never a verdict.  coverage 1.000 with readable 0 is a
        # BROKEN RUNNER, not a clean field.
        verdict = "ERROR: ZERO MEASURED (nothing readable was produced)"
        exit_code = EXIT_ZERO_MEASURED
    else:
        verdict = "SCORED"
        exit_code = EXIT_SCORED

    rnd = {
        "score": score,
        "wins": solved_n,
        "trials": started_n,
        "kind": "grid_puzzle",
        "class": "CONTEST",
        "oracle": "rules_of_the_game_implemented_once_with_controls",
        "staged_as": "arcade cabinet -- SOKOBAN: push every crate, and the "
                     "crates never pull",
        "denominator_rule": "trials = levels the entrant TOOK A TURN on; "
                            "NEVER_STARTED is OUTSIDE, counted separately; "
                            "the zero-rule gate counts READABLE tokens, not "
                            "turns [G15]",
        "score_is": "solved levels / levels attempted -- a RATE, for the gate. "
                    "`moves` (the read grammar's SCORE) is carried per level "
                    "and is NOT averaged: a move count is not a rate [G15]",
        "items": items,
        "started": started_n, "measured": measured, "readable": readable,
        "never_started": never_started_n, "coverage": coverage,
        "totals": {
            "moves": sum(it["moves"] for it in items.values()),
            "attempted": sum(it["attempted"] for it in items.values()),
            "blocked": sum(it["blocked"] for it in items.values()),
            "not_an_action": sum(it["not_an_action"] for it in items.values()),
            "after_end": sum(it["after_end"] for it in items.values()),
            "give_up": sum(it["give_up"] for it in items.values()),
            "corrections_offered": sum(it["corrections_offered"]
                                       for it in items.values()),
            "corrections_ignored": sum(it["corrections_ignored"]
                                       for it in items.values()),
            "loose_give_up_unscored": sum(
                1 for it in items.values() for ply in it["trace"]
                if ply["reading"].get("loose_give_up_diagnostic")
                and ply["reading"]["outcome"] != "give_up"),
        },
        "loose_give_up_note": "answers that LOOKED like an abstention to a "
                              "substring test but were scored not_an_action "
                              "by the strict token rule. DIAGNOSTIC ONLY -- "
                              "never scored, and never folded into give_up "
                              "[G1].",
        "attempt_budget_per_level": budget,
    }
    return {"admission": admission, "round": rnd, "verdict": verdict,
            "exit_code": exit_code, "aggregate": score,
            "coverage": coverage}


# ---------------------------------------------------------------------------
# 6. THE BUNDLE
# ---------------------------------------------------------------------------

def build_bundle(entrant_name, result, levels, reasoning="unset",
                 gpu=None, weights=None, config_extra=None):
    """-> the bundle dict.  Everything the record must carry, carried."""
    ent = ENTRANTS.get(entrant_name)
    on_board = entrant_name in ON_BOARD
    w = weights if weights is not None else (
        ent().weights_info() if ent else None)

    rnd = result["round"]
    items = rnd["items"]
    terminals = sorted({it["terminal"] for it in items.values()})

    return {
        "harness": HARNESS,
        "version": VERSION,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": EVENT,
        "card_version": CARD_VERSION,

        # -- THE TWO FIELDS THAT DECIDE EVERYTHING, at the TOP of the record,
        #    where a reader cannot miss them.  A setting nobody wrote down is
        #    indistinguishable from a decision.
        "declared": {
            "reasoning": reasoning,
            "reasoning_note": "DECLARED per-run instrument field. 'unset' is "
                              "NOT 'off': an undeclared run must not be "
                              "pooled with a declared one. Same weights with "
                              "thinking ON vs OFF produced OPPOSITE outcomes "
                              "on this project's cabinet task.",
            "gpu": gpu if gpu is not None else probe_gpu(),
            "gpu_note": "DECLARED per-run. No accelerator is recorded as null "
                        "with the probe that ran, never 0.00 and never "
                        "'none'.",
        },

        "results": [{
            "entrant": entrant_name,
            "kind": (ent.kind if ent else "model"),
            "instrument": (ent.instrument if ent else "model"),
            "instrument_note": "CODE entrant, not a model -- a DIFFERENT "
                               "INSTRUMENT; never pooled into a model table"
                               if not on_board else
                               "MODEL entrant: weights were loaded and "
                               "served.",
            "entrant_is_a_model": bool(ent.is_model if ent else True),
            "on_board": on_board,

            # -- DIGEST, not only a name.  Two same-named files in two
            #    directories is otherwise an unresolvable confound.
            "weights": w,
            "weights_sha256": (w or {}).get("sha256"),

            # -- WHICH CODE PRODUCED THE VERDICT, not only the verdict.
            #    Without this, "it ignored the correction" and "it tried and
            #    failed" are indistinguishable, and they are not the same
            #    finding.
            "verdict_code": {
                "module": "sokoban2_run.py",
                "function": "run_entrant",
                "sha256": _sha256_of_source(
                    os.path.join(HERE, "sokoban2_run.py")),
                "simulator": {
                    "module": "sokoban2.py",
                    "sha256": _sha256_of_source(
                        os.path.join(HERE, "sokoban2.py")),
                    "transition": "step(state, action) -> (position, word)",
                },
                "reader": {
                    "module": "sokoban_reader.py",
                    "sha256": reader_sha256(),
                    "note": "ONE reader of record, imported by every side "
                            "script, never reimplemented.",
                },
                "solver": {
                    "module": "sokoban2_solve.py",
                    "sha256": _sha256_of_source(
                        os.path.join(HERE, "sokoban2_solve.py")),
                    "role": "verifies the frozen optima and supplies the "
                            "dead-end DIAGNOSTIC. Never scores.",
                },
            },
            "terminals": terminals,
            "terminal_reason": {
                "per_level": {k: v["terminal"] for k, v in items.items()},
                "corrections_offered": rnd["totals"]["corrections_offered"],
                "corrections_ignored": rnd["totals"]["corrections_ignored"],
                "note": "corrections_ignored > 0 means the entrant was TOLD "
                        "its answer was unreadable and produced no legal "
                        "action anyway -- which is not the same finding as "
                        "producing legal actions that failed.",
            },

            "config": {
                "temperature": (config_extra or {}).get("temperature", 0.0),
                "max_tokens": (config_extra or {}).get("max_tokens", 8),
                "trials": 1,
                "ctx": (config_extra or {}).get("ctx", None),
                "n_gpu_layers": (config_extra or {}).get("n_gpu_layers", None),
                "server_flags": (config_extra or {}).get("server_flags", None),
                "attempt_budget_per_level": rnd["attempt_budget_per_level"],
                "retries_on_unreadable": (config_extra or {}).get("retries"),
                # [A11] THE REASONING SETTING IS AN INSTRUMENT FIELD.
                "reasoning": reasoning,
                "reasoning_note": "DECLARED per-run instrument field; 'unset' "
                                  "is NOT 'off'.",
                # [G16] ...but a CODE entrant has no reasoning setting at all.
                # 'null with a written reason', not 'off' and not omitted: the
                # run's declaration and the entrant's own setting are two
                # different quantities and the format has one field for both.
                "entrant_reasoning": None if not on_board else reasoning,
                "entrant_reasoning_note": (
                    "NOT APPLICABLE -- this entrant is code; no model was "
                    "served and no reasoning setting existed. Recorded as "
                    "null with this reason, never 'off' and never omitted "
                    "[G16]." if not on_board else
                    "the entrant is a served model; its reasoning setting is "
                    "the run's declaration."),
                "config_note": "RUN_FACTS that do not exist on this host are "
                               "null, not omitted and not zeroed.",
            },

            "hardware": (config_extra or {}).get("hardware") or host_block(),
            "admission": result["admission"],
            "rounds": {"R_sokoban_levels": result["round"]},
            "grammar": grammar_as_record(),
            "levels": {
                name: {"sha256": levels[name].sha256,
                       "optimal_moves": sokoban2.EXPECTED_OPTIMAL[name],
                       "optimal_proven_by": "sokoban2_solve.py (exhaustive "
                                            "BFS, complete over the state "
                                            "space)"}
                for name in LEVEL_FILES
            },
            "aggregate": result["aggregate"],
            "coverage": result["coverage"],
            "verdict": result["verdict"],
            "exit_code": result["exit_code"],
            "exit_code_table": EXIT_CODES,
            "certification": ("REFERENCE RUN -- not an entrant, not for the "
                              "board." if not on_board else
                              "MODEL RUN -- on the board."),
            "tasks": TASKS,
            "ambiguities": "sokoban2/SOKOBAN2_AMBIGUITIES.md",
        }],
    }


def write_bundle(bundle, out_dir, name):
    """WRITE THE RECORD.  Called BEFORE the success/failure branch, always."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "sokoban_v1_%s.json" % name)
    tmp = path + ".partial"
    with open(tmp, "w") as fh:
        json.dump(bundle, fh, indent=2, default=str)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------------------
# 7. SUBCOMMANDS
# ---------------------------------------------------------------------------

class _Args(object):
    """Minimal stand-in so the self-test can call cmd_run in process."""

    def __init__(self, entrant, out=None, reasoning="unset", budget=None,
                 retries=None, model_path=None, server_url=None,
                 max_tokens=8, temperature=0.0):
        self.entrant = entrant
        self.out = out
        self.reasoning = reasoning
        self.budget = budget
        self.retries = retries
        self.model_path = model_path
        self.server_url = server_url
        self.max_tokens = max_tokens
        self.temperature = temperature


def _make_entrant(name, args):
    if name == "model":
        return ModelEntrant(
            model_path=getattr(args, "model_path", None),
            server_url=getattr(args, "server_url", None)
            or "http://127.0.0.1:8080")
    return ENTRANTS[name]()


def cmd_run(args):
    """Run one entrant.  RETURNS THE EXIT CODE.  The record is written before
    any branch that could return."""
    if args.entrant not in ENTRANTS:
        print("unknown entrant %r; choose from %s"
              % (args.entrant, ", ".join(sorted(ENTRANTS))), file=sys.stderr)
        return EXIT_USAGE

    levels = sokoban2.load_level_set()
    budget = args.budget or DEFAULT_ATTEMPT_BUDGET
    retries = DEFAULT_RETRIES if args.retries is None else args.retries

    entrant = _make_entrant(args.entrant, args)
    result = run_entrant(entrant, levels, budget=budget, retries=retries,
                         max_tokens=args.max_tokens,
                         temperature=args.temperature)
    weights = entrant.weights_info() if hasattr(entrant, "weights_info") \
        else None
    bundle = build_bundle(
        args.entrant, result, levels, reasoning=args.reasoning,
        weights=weights,
        config_extra={"retries": retries,
                      "max_tokens": args.max_tokens,
                      "temperature": args.temperature})

    out_dir = args.out or os.path.join(HERE, "results")
    # ---- THE RECORD IS WRITTEN HERE, BEFORE THE SUCCESS/FAILURE BRANCH. ----
    # The failure path is where the record matters most; a runner that writes
    # nothing there has no evidence that it ran at all.
    try:
        path = write_bundle(bundle, out_dir, args.entrant)
        print("wrote %s" % path)
    except OSError as exc:
        print("RECORD NOT WRITTEN: %r" % (exc,), file=sys.stderr)
        return EXIT_WRITE_FAILED

    rnd = result["round"]
    print("  %-14s solved=%s/%s  moves=%-4d attempted=%-4d blocked=%-4d "
          "not_an_action=%-4d give_up=%d"
          % (args.entrant, rnd["wins"], rnd["trials"],
             rnd["totals"]["moves"], rnd["totals"]["attempted"],
             rnd["totals"]["blocked"], rnd["totals"]["not_an_action"],
             rnd["totals"]["give_up"]))
    print("  %-14s coverage=%.3f  measured=%d  readable=%d  %s  (exit %d)"
          % ("", rnd["coverage"], rnd["measured"], rnd["readable"],
             result["verdict"], result["exit_code"]))
    gpu = bundle["declared"]["gpu"]
    print("  %-14s reasoning=%s   entrant_reasoning=%s"
          % ("", bundle["declared"]["reasoning"],
             bundle["results"][0]["config"]["entrant_reasoning"]))
    print("  %-14s gpu=%s  (probe: %s)"
          % ("", gpu.get("name") or "null -- no accelerator found",
             gpu.get("probe")))
    for name in LEVEL_FILES:
        it = rnd["items"][name]
        print("     %-28s %-22s moves=%-3d attempted=%-3d blocked=%-3d na=%-3d"
              % (name, it["terminal"], it["moves"], it["attempted"],
                 it["blocked"], it["not_an_action"]))
    return result["exit_code"]


def instrument_check(out_dir=None, reasoning="unset",
                     include_simulator_self_test=True):
    """Prove the HARNESS can run SOKOBAN, with a known-good solver as the
    entrant -- NOT a contest.  Enters nothing.  Exit 1 if not proven.

    `include_simulator_self_test=False` breaks the mutual recursion when the
    SIMULATOR's self-test drives the runner: each one otherwise calls the
    other forever.  Both still run; they just do not call each other.
    """
    ok = True
    print("INSTRUMENT CHECK -- solver-as-entrant; proves the harness, "
          "enters nothing.")
    print()

    # 0. THE INSTRUMENT'S OWN CONTROLS
    if include_simulator_self_test:
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = sokoban2.self_test()
        ok &= _say(rc == 0, "SIMULATOR: --self-test exits 0", rc)

    # 1. THE LEVELS -- the frozen optima, VERIFIED, not asserted
    levels = sokoban2.load_level_set()
    lv_ok, rows = sokoban2_solve.verify_levels(levels)
    for r in rows:
        _say(r["agree"],
             "LEVEL: %s optimal %s (claim %s), %d states exhausted"
             % (r["level"], r["proven_optimal"], r["expected_optimal"],
                r["n_states_exhausted"]),
             r["shortest_plan"])
        ok &= r["agree"]
    ok &= _say(lv_ok, "LEVELS: all three optima verified by exhaustive BFS")

    # 2. THE ORACLE -- a known-good solver must solve every level
    result = run_entrant(ReferenceSolver(), levels)
    rnd = result["round"]
    ok &= _say(rnd["wins"] == rnd["trials"] == len(LEVEL_FILES),
               "ORACLE: the reference solver solves all %d levels"
               % len(LEVEL_FILES), (rnd["wins"], rnd["trials"]))
    for name in LEVEL_FILES:
        it = rnd["items"][name]
        opt = sokoban2.EXPECTED_OPTIMAL[name]
        ok &= _say(it["solved"] and it["moves"] == opt,
                   "ORACLE: %s solved in exactly %d moves (the proven optimum)"
                   % (name, opt), (it["solved"], it["moves"]))

    # 3. THE READER -- the malformed-answer controls, against the real reader
    ok &= _say(read_answer("RESIGN").outcome == OUTCOME_GIVE_UP
               and read_answer("RESIGN").action is None,
               "READER: RESIGN is give_up, never R")
    ok &= _say(read_answer("W").outcome == OUTCOME_NOT_AN_ACTION,
               "READER: W is not a synonym for up")
    ok &= _say(read_answer("UR").outcome == OUTCOME_NOT_AN_ACTION,
               "READER: two letters are never truncated to one")
    ok &= _say(read_answer("r").action == "R", "READER: case-insensitive")

    # 4. THE WALL BUMPER -- moves and attempted are different claims
    bump = run_entrant(WallBumper(), levels, budget=50)
    tot = bump["round"]["totals"]
    # 50 attempts on each of three levels.  On 01 and 02 the player starts
    # against the left wall, so all 50 are blocked.  On 03 the player starts at
    # (2,3) with two cells of floor to its LEFT, so the first two L's are legal
    # moves and the remaining 48 are blocked.  Stated exactly, because a
    # control that is approximately right is not a control.
    ok &= _say(tot["attempted"] == 150 and tot["blocked"] == 148
               and tot["moves"] == 2,
               "COUNTERS: 3 levels x 50 attempts = 150 attempted, 148 blocked, "
               "2 moves -- and 0 SOLVED. A counter that reported 'moves' as "
               "'attempted' would call this a long game.",
               (tot["attempted"], tot["blocked"], tot["moves"]))

    # -- THE DEAD-END DIAGNOSTIC must fire, and must never be a score --------
    cw = run_entrant(CornerWalker(), levels, budget=20)
    it3 = cw["round"]["items"]["03_the_corner_waiting.txt"]
    dead = [d for d in it3["dead_end_diagnostic"]
            if d["solvable_after"] is False]
    ok &= _say(len(dead) > 0 and it3["solved"] is False,
               "FACULTY: the corner-walker is recorded as UNSOLVABLE from move "
               "%s onward, and the board never says so"
               % (dead[0]["attempt"] if dead else "?"), len(dead))
    ok &= _say(it3["terminal"] == "BUDGET_EXHAUSTED",
               "FACULTY: it kept playing to the budget instead of abstaining",
               it3["terminal"])

    # -- THE ABSTENTION RULE, MEASURED --------------------------------------
    soft = run_entrant(SoftResigner(), levels, budget=2)
    stot = soft["round"]["totals"]
    ok &= _say(stot["give_up"] == 0 and stot["not_an_action"] > 0,
               "READER [G1]: a NATURAL abstention ('I give up, ...') is "
               "counted not_an_action, not give_up -- by the strict token "
               "rule. This is the instrument's own finding, not the "
               "entrant's.", (stot["give_up"], stot["not_an_action"]))
    hard = run_entrant(Resigner(), levels, budget=2)
    ok &= _say(hard["round"]["totals"]["give_up"] == len(LEVEL_FILES),
               "READER: the exact token abstains on every level",
               hard["round"]["totals"]["give_up"])

    # 5. THE ZERO RULE -- enforced, not described
    garb = run_entrant(Garbage(), levels, budget=3)
    ok &= _say(garb["exit_code"] == EXIT_ZERO_MEASURED
               and garb["round"]["coverage"] == 1.0,
               "ZERO RULE: an all-unreadable run is an ERROR at coverage 1.000",
               (garb["exit_code"], garb["round"]["coverage"]))
    ns = run_entrant(NeverStarts(), levels)
    ok &= _say(ns["exit_code"] == EXIT_NEVER_STARTED
               and ns["round"]["never_started"] == len(LEVEL_FILES),
               "NEVER-STARTED is counted SEPARATELY from played-and-failed",
               (ns["exit_code"], ns["round"]["never_started"]))

    # 6. THE BUNDLE SHAPE
    bundle = build_bundle("reference", result, levels, reasoning=reasoning)
    ent = bundle["results"][0]
    ent["certification"] = ("INSTRUMENT CHECK -- the solver-as-entrant path; "
                            "proves the harness and ENTERS NOTHING.")
    ent["on_board"] = False
    # [A1/A8] it must not be sweepable AS an entrant: it is written under its
    # own name, so a table that keys on `entrant` cannot mistake the harness
    # proof for a contestant named "reference".
    ent["entrant"] = "instrument-check"
    ent["is_harness_proof"] = True
    for key in ("harness", "version", "event", "card_version", "results",
                "declared"):
        ok &= _say(key in bundle, "BUNDLE SHAPE: has %r" % key, sorted(bundle))
    for key in ("tasks", "ambiguities", "instrument", "admission", "rounds",
                "grammar", "verdict_code", "weights", "hardware", "levels"):
        ok &= _say(key in ent, "BUNDLE SHAPE: result carries %r" % key,
                   sorted(ent))
    ok &= _say(all(k in rnd for k in ("score", "wins", "trials", "started",
                                      "measured", "readable", "never_started",
                                      "coverage")),
               "BUNDLE SHAPE: the round carries the full count set",
               sorted(rnd))

    # 7. THE TWO DECLARED FIELDS [A11] -- reasoning and GPU, per run
    ok &= _say("reasoning" in bundle["declared"]
               and bundle["declared"]["reasoning"] in ("on", "off", "unset"),
               "DECLARED [A11]: the bundle records config.reasoning",
               bundle["declared"].get("reasoning"))
    ok &= _say("gpu" in bundle["declared"]
               and "probe" in bundle["declared"]["gpu"],
               "DECLARED: the bundle records the GPU AND the probe that ran",
               bundle["declared"].get("gpu"))
    ok &= _say("reasoning" in ent["config"]
               and ent["config"]["reasoning"] == reasoning,
               "DECLARED [A11]: config.reasoning matches the declared value",
               ent["config"].get("reasoning"))

    # 8. THE DIGEST AND THE VERDICT CODE
    ok &= _say(ent["verdict_code"]["sha256"]
               == _sha256_of_source(os.path.join(HERE, "sokoban2_run.py")),
               "PROVENANCE: the bundle carries the digest of the code that "
               "produced the verdict", ent["verdict_code"]["sha256"])
    ok &= _say(ent["verdict_code"]["reader"]["sha256"] == reader_sha256(),
               "PROVENANCE: the bundle carries the reader's digest")
    ok &= _say(ent["verdict_code"]["simulator"]["sha256"]
               == _sha256_of_source(os.path.join(HERE, "sokoban2.py")),
               "PROVENANCE: the bundle carries the simulator's digest")

    # 9. THE HOLDER -- a failed load names the holder, never "failed to load"
    holder = probe_holder("8080", kind="port")
    ok &= _say("probe" in holder and
               (holder.get("holder") is not None or holder.get("note")),
               "HOLDER: a failed load names the holder or says which probe "
               "found nobody", holder)

    if out_dir:
        write_bundle(bundle, out_dir, "instrument-check")
        print("wrote %s" % os.path.join(out_dir,
                                        "sokoban_v1_instrument-check.json"))
    print("")
    print("INSTRUMENT CHECK %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else EXIT_INSTRUMENT


def _say(cond, label, seen=None):
    print("  %s %s%s" % ("ok  " if cond else "FAIL", label,
                         "" if cond or seen is None else "   <- %r" % (seen,)))
    return bool(cond)


def cmd_levels(args):
    ok, rows = sokoban2_solve.verify_levels(sokoban2.load_level_set())
    for r in rows:
        print("  %-28s optimal %-3s (claim %-3s)  %d states  plan %s  "
              "sha256 %s" % (r["level"], r["proven_optimal"],
                             r["expected_optimal"], r["n_states_exhausted"],
                             r["shortest_plan"], r["sha256"][:16]))
    print()
    print("LEVEL VERIFICATION %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else EXIT_INSTRUMENT


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sokoban2_run.py",
        description="SOKOBAN runner/scorer -- independent implementation #2")
    sub = ap.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="run one entrant")
    p_run.add_argument("--entrant", required=True,
                       choices=sorted(ENTRANTS))
    p_run.add_argument("--out", default=None)
    p_run.add_argument("--reasoning", choices=("on", "off", "unset"),
                       default="unset",
                       help="DECLARED per-run instrument field [A11]. "
                            "'unset' is NOT 'off'.")
    p_run.add_argument("--budget", type=int, default=None,
                       help="attempt budget per level [G13]")
    p_run.add_argument("--retries", type=int, default=None,
                       help="corrections offered on an unreadable answer [G14]")
    p_run.add_argument("--model-path", default=None)
    p_run.add_argument("--server-url", default=None)
    p_run.add_argument("--max-tokens", type=int, default=8)
    p_run.add_argument("--temperature", type=float, default=0.0)

    p_ic = sub.add_parser("instrument-check",
                          help="prove the harness; enters nothing")
    p_ic.add_argument("--out", default=None)
    p_ic.add_argument("--reasoning", choices=("on", "off", "unset"),
                      default="unset")

    sub.add_parser("levels", help="verify the frozen optima by exhaustive BFS")
    p_ex = sub.add_parser("exit-codes", help="print the exit code table")
    p_ex.set_defaults(_ex=True)
    sub.add_parser("verify", help="replay every bundle from the record")

    p_all = sub.add_parser("run-all", help="run the whole field, one declared "
                                           "instrument setting")
    p_all.add_argument("--reasoning", choices=("on", "off", "unset"),
                       default="off")
    p_all.add_argument("--out", default=None)

    args = ap.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "instrument-check":
        return instrument_check(args.out, reasoning=args.reasoning)
    if args.cmd == "levels":
        return cmd_levels(args)
    if args.cmd == "verify":
        import test_sokoban2
        return 0 if test_sokoban2.verify_all() else EXIT_INSTRUMENT
    if args.cmd == "run-all":
        # ONE declared instrument setting for the WHOLE field.  Two bundles for
        # the same event that declare different settings are not the same
        # measurement (darts A11), so there is deliberately no per-entrant
        # override here.
        codes = {}
        for name in sorted(ENTRANTS):
            if name == "model":
                continue                 # needs --model-path and a server
            codes[name] = cmd_run(_Args(name, args.out, args.reasoning))
            print("  exit %d\n" % codes[name])
        print("  -- field summary")
        for name in sorted(codes):
            print("     %-16s exit %d  %s" % (name, codes[name],
                                              EXIT_CODES[codes[name]]))
        # NOT a constant.  A non-zero here means a record was not written, and
        # a run with no record is not a run.
        bad = [n for n, c in codes.items() if c == EXIT_WRITE_FAILED]
        if bad:
            print("  RECORDS NOT WRITTEN for: %s" % ", ".join(bad))
            return EXIT_WRITE_FAILED
        return EXIT_SCORED
    if args.cmd == "exit-codes":
        for code in sorted(EXIT_CODES):
            print("  %d  %s" % (code, EXIT_CODES[code]))
        return 0
    ap.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
