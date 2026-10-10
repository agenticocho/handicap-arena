#!/usr/bin/env python3
# digdug_run.py -- THE RUNNER and THE SCORER for the DIG DUG cabinet.
#
#   * it gives the task (build_prompt, from the simulator -- never built here)
#   * it collects the answer
#   * IT CHECKS THE ANSWER BY EXECUTING IT (feed() -> resolve_turn()) -- never by
#     reading it and comparing it to a solution string
#   * IT REFUSES TO PLAY ANY ENTRANT UNTIL THE CONTRACT IS FROZEN ON DISK WITH A
#     DIGEST THAT MATCHES (E: "freeze it before any entrant runs")
#   * IT WRITES THE RECORD TO DISK BEFORE THE SUCCESS/FAILURE BRANCH
#   * it records the model file's DIGEST, not only its name, or the reason there
#     is none
#   * it records WHICH CODE produced the verdict
#   * it records the REASONING SETTING and the GPU, per run
#   * a failed load NAMES THE HOLDER, never "failed to load"
#   * the exit code reflects the run, and the self-test drives every path that
#     returns one
#   * BOTH facets are read off the SAME trace (D).  There is no second event in
#     this file and no second run: `facet_rows()` is a projection of `trace`.
#
# Stdlib only.

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from digdug_reader import (OUTCOME_ACTION, OUTCOME_GIVE_UP,        # noqa: E402
                           OUTCOME_NOT_AN_ACTION, grammar_as_record,
                           read_answer, reader_sha256, GIVE_UP_TOKENS,
                           parse_give_up_tokens_from_contract)
import digdug                                                   # noqa: E402
from digdug import (FROZEN, Policy, State, build_prompt,         # noqa: E402
                    check_prompt_legal, feed, load_level, parse_level, render,
                    resolve_turn, terminal_reason, WORD_BLOCKED, WORD_WAITED,
                    MOVE_LETTERS, ACTIONS, DELTAS)
import digdug_solve                                             # noqa: E402

HARNESS = "handicap-arena"
VERSION = "1.0"
EVENT = "DIG DUG"
CARD_VERSION = "digdug_v1"
ROUND_ID = "R_digdug_levels"

LEVEL_FILES = digdug.LEVEL_FILES
CONTRACT_DOC = os.path.join(HERE, "CONTRACT_digdug_v1.md")
FROZEN_MANIFEST = os.path.join(HERE, "CONTRACT_frozen.json")
TASKS_OUT = os.path.join(HERE, "tasks", "digdug_v1.json")

#: THE ATTEMPT BUDGET, per level.  Not in the prose; decided and recorded, like
#: every other default.  It is also the horizon of the per-ply proof, so it is
#: not a free parameter: `HORIZON >= BUDGET` is control [HZ], and a run whose
#: budget exceeded the horizon would report `completable=False` where it should
#: report unknown.  (D-BUDGET in DIGDUG_DECISIONS.md.)
DEFAULT_ATTEMPT_BUDGET = 10

#: Corrections offered when an answer cannot be read.  [D-RETRIES]  Zero would
#: mean one malformed token ends the level; two is what the Sokoban cabinet used
#: and it is carried over deliberately rather than reinvented.
DEFAULT_RETRIES = 2

# ---------------------------------------------------------------------------
# EXIT CODES -- declared, printed, and every one of them produced by a path the
# instrument check actually drives.
# ---------------------------------------------------------------------------
EXIT_SCORED = 0                # measured > 0 and the harness is sound
EXIT_INSTRUMENT = 1            # the INSTRUMENT is not proven: self-test,
                               # instrument check, level verification, or a
                               # contract that is not frozen against disk
EXIT_ZERO_MEASURED = 2         # ZERO RULE: a run with no measured entrant is
                               # an ERROR, never a verdict
EXIT_USAGE = 3                 # unknown entrant, bad arguments
EXIT_NEVER_STARTED = 4         # the entrant never loaded: counted separately
                               # from played-and-failed, because they are
                               # different claims
EXIT_WRITE_FAILED = 5          # the record could not be written; a run with no
                               # record is not a run
EXIT_NOT_FROZEN = 6            # an entrant was asked to play against an
                               # unfrozen or drifted contract.  Distinct from 1
                               # because "the instrument is unproven" and "you
                               # did not freeze it" need different fixes.

EXIT_CODES = {
    EXIT_SCORED: "SCORED -- measured > 0, harness sound",
    EXIT_INSTRUMENT: "INSTRUMENT NOT PROVEN -- self-test / instrument-check / "
                     "level verification failed",
    EXIT_ZERO_MEASURED: "ZERO MEASURED -- ERROR, never a verdict",
    EXIT_USAGE: "USAGE -- unknown entrant or bad arguments",
    EXIT_NEVER_STARTED: "ENTRANT NEVER STARTED -- counted separately from "
                        "played-and-failed",
    EXIT_WRITE_FAILED: "RECORD NOT WRITTEN -- a run with no record is not a run",
    EXIT_NOT_FROZEN: "CONTRACT NOT FROZEN (or it drifted) -- no entrant plays",
}

#: the files the freeze covers.  A digest nobody can reproduce is a decoration,
#: so every entry is a real path in this cabinet.
FROZEN_FILES = {
    "contract": "CONTRACT_digdug_v1.md",
    "reader": "digdug_reader.py",
    "simulator": "digdug.py",
    "solver": "digdug_solve.py",
    "runner": "digdug_run.py",
    "readings": "digdug_readings.py",
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


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# 1. THE FREEZE GATE -- "frozen before any entrant runs", as a gate
# ---------------------------------------------------------------------------

def freeze_state(path=None):
    """-> (ok, detail).  The manifest must exist and every digest must match.

    This is the difference between writing a contract and FREEZING one.  The
    claim "the contract predates every run" is not asserted in prose anywhere in
    this cabinet; it is a condition the runner checks before it will hand a
    single prompt to a single entrant, and the per-bundle control
    `frozen_before_this_run` compares the two timestamps.

    THE GATE WAS WRONGLY WRITTEN ONCE, AND THE MISTAKE IS WORTH KEEPING IN THE
    FILE.  The first version iterated `manifest["files"]`, a key the writer never
    wrote, so the loop body never ran, `ok` stayed True, and the check passed on a
    directory where nothing at all had been compared.  A gate that reads an
    missing key is a gate with no door in it.  Hence the two assertions below:
    the manifest must list EVERY frozen file, and it must list every level, and a
    short list is refused as loudly as a mismatched digest.
    """
    path = path or FROZEN_MANIFEST
    detail = {"manifest": os.path.relpath(path, HERE),
              "present": os.path.isfile(path), "files": {}, "note": None,
              # `digests` is what a BUNDLE carries, and it was missing from the
              # first version of this dict -- so `build_bundle`'s
              # `frozen_contract.digests` was None for every run and the bundle's
              # own provenance check failed at verify time.  A gate that reports
              # nothing is a gate that was never read.
              "digests": {}}
    if not detail["present"]:
        detail["note"] = ("no CONTRACT_frozen.json: the contract has never been "
                          "frozen, so nothing may be scored against it.  Run "
                          "`python3 digdug_run.py freeze`.")
        return False, detail
    with open(path) as fh:
        man = json.load(fh)
    detail["frozen_utc"] = man.get("frozen_utc")
    want_files = dict(FROZEN_FILES)
    want_levels = dict((n, n) for n in LEVEL_FILES)
    got_files = man.get("digests") or {}
    got_levels = man.get("levels") or {}
    ok = True
    missing_keys = [k for k in want_files if k not in got_files]
    if missing_keys:
        ok = False
        detail["note"] = ("the manifest does not even name these artifacts: %s. "
                          "An absent entry is not a pass."
                          % ", ".join(sorted(missing_keys)))
    if sorted(got_levels) != sorted(LEVEL_FILES):
        ok = False
        detail["note"] = ((detail["note"] or "") + " the manifest's level list is "
                          "not the item set the runner plays").strip()
    for key, rel in sorted(want_files.items()):
        got = _sha256_of(os.path.join(HERE, rel))
        want = got_files.get(key)
        match = (got is not None and want is not None and got == want)
        detail["files"][rel] = {"digest": got, "frozen_digest": want,
                                "match": match}
        detail["digests"][key] = want
        ok = ok and match
    for rel in sorted(want_levels):
        got = _sha256_of(os.path.join(HERE, "levels", rel))
        want = got_levels.get(rel)
        match = (got is not None and want is not None and got == want)
        detail["files"]["levels/" + rel] = {"digest": got, "frozen_digest": want,
                                            "match": match}
        detail["digests"]["level:" + rel] = want
        ok = ok and match
    if not ok and not detail["note"]:
        detail["note"] = ("at least one digest has DRIFTED since the freeze.  A "
                          "score produced under a moved contract is a different "
                          "measurement wearing the old label; re-freeze and "
                          "re-run, and expect every number to change.")
    return ok, detail


def cmd_freeze(args):
    """Freeze the contract: digests of the doc, the code and the levels."""
    missing = [rel for rel in FROZEN_FILES.values()
               if not os.path.isfile(os.path.join(HERE, rel))]
    if missing:
        print("REFUSING TO FREEZE -- these files do not exist: %s"
              % ", ".join(missing))
        print("A freeze over a missing artifact is not a freeze; it is a "
              "digest of a hope.")
        return EXIT_USAGE
    digests = {k: _sha256_of(os.path.join(HERE, rel))
               for k, rel in sorted(FROZEN_FILES.items())}
    levels = {}
    for name in LEVEL_FILES:
        p = os.path.join(HERE, "levels", name)
        if not os.path.isfile(p):
            print("REFUSING TO FREEZE -- level %s is missing" % name)
            return EXIT_USAGE
        levels[name] = _sha256_of(p)
    with open(CONTRACT_DOC) as fh:
        doc = fh.read()
    n_marks = doc.count("[UNDER-SPECIFIED")
    man = {
        "artifact": "DIG DUG cabinet -- frozen contract manifest",
        "card_version": CARD_VERSION,
        "frozen_utc": now_utc(),
        "frozen_before_any_entrant_run": True,
        "contract": FROZEN_FILES["contract"],
        "digests": digests,
        "levels": levels,
        "under_specified_marks": n_marks,
        "abstention_tokens": list(GIVE_UP_TOKENS),
        "answer_alphabet": list(ACTIONS),
        "step_contract": "step(state, action) -> ((row, col), word); mutates; "
                         "raises outside the alphabet; checks bounds itself",
        "frozen_by_hand": ("This manifest is written by `freeze`, and the runner "
                           "refuses to enter an entrant without it.  The freeze "
                           "is a gate, not a caption."),
        "note": ("If any digest below stops matching the file on disk, every "
                 "number produced after that moment is a different measurement "
                 "under the same name.  Re-freezing is allowed; re-running is "
                 "then mandatory, and the old bundles stay on disk labelled by "
                 "the digest they were read under."),
    }
    if n_marks < 7:
        print("REFUSING TO FREEZE -- only %d [UNDER-SPECIFIED] marks in the "
              "contract; the brief lists 7 open questions and demands at least "
              "that many." % n_marks)
        return EXIT_INSTRUMENT
    os.makedirs(os.path.dirname(FROZEN_MANIFEST), exist_ok=True)
    tmp = FROZEN_MANIFEST + ".partial"
    with open(tmp, "w") as fh:
        json.dump(man, fh, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, FROZEN_MANIFEST)
    print("FROZEN %s" % FROZEN_MANIFEST)
    for k, v in sorted(digests.items()):
        print("  %-10s %s  %s" % (k, (v or "UNREADABLE")[:16],
                                  FROZEN_FILES[k]))
    for k, v in sorted(levels.items()):
        print("  %-10s %s  levels/%s" % ("level", v[:16], k))
    print("  under-specified clauses marked: %d" % n_marks)
    print("  abstention tokens frozen: %d" % len(GIVE_UP_TOKENS))
    return EXIT_SCORED


# ---------------------------------------------------------------------------
# 2. THE HOLDER -- a failed load must NAME THE HOLDER, never "failed to load"
# ---------------------------------------------------------------------------

def _proc_field(pid, name):
    try:
        with open("/proc/%s/%s" % (pid, name)) as fh:
            return fh.read()
    except OSError:
        return ""


def _proc_cmdline(pid):
    raw = _proc_field(pid, "cmdline").replace("\0", " ").strip()
    return raw or None


def _socket_inodes_for_port(port):
    """Inodes bound to a TCP port, from /proc/net/tcp{,6} (stdlib-only lsof)."""
    inodes = set()
    for name in ("tcp", "tcp6"):
        path = "/proc/net/%s" % name
        try:
            with open(path) as fh:
                lines = fh.read().splitlines()[1:]
        except OSError:
            continue
        for ln in lines:
            parts = ln.split()
            if len(parts) < 10:
                continue
            local = parts[1]
            try:
                lport = int(local.split(":")[1], 16)
            except (IndexError, ValueError):
                continue
            if lport == int(port) and parts[3] == "0A":   # LISTEN
                inodes.add(parts[9])
    return inodes


def _proc_holders_for_inodes(inodes):
    out = []
    if not inodes:
        return out
    want = {"socket:[%s]" % i for i in inodes}
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return out
    for pid in pids:
        fd_dir = "/proc/%s/fd" % pid
        try:
            for fd in os.listdir(fd_dir):
                try:
                    link = os.readlink(os.path.join(fd_dir, fd))
                except OSError:
                    continue
                if link in want:
                    out.append({"pid": int(pid), "comm": _proc_field(
                        pid, "comm").strip() or None,
                        "cmdline": _proc_cmdline(pid)})
                    break
        except OSError:
            continue
    return out


def probe_holder(resource, kind="port"):
    """Who is holding the thing that failed to load?  Never a bare "failed".

    -> {"probe": str, "resource": str, "holder": {...}|None, "note": str|None}
    A probe that finds nobody SAYS which probe ran and that it found nobody; that
    is a different statement from "nobody is holding it", and it is the one the
    record is allowed to make.
    """
    out = {"probe": None, "resource": str(resource), "holder": None,
           "holders": [], "note": None}
    if kind == "port":
        inodes = _socket_inodes_for_port(resource)
        out["probe"] = ("/proc/net/tcp+tcp6 LISTEN table -> socket inode -> "
                        "/proc/<pid>/fd")
        holders = _proc_holders_for_inodes(inodes)
        if holders:
            out["holders"] = holders
            out["holder"] = holders[0]
            return out
    else:
        out["probe"] = "lsof + /proc/<pid>/fd scan for the path"
        holders = []
        try:
            p = subprocess.run(["lsof", "-F", "pn", str(resource)],
                               capture_output=True, text=True, timeout=20)
            pid = None
            for ln in (p.stdout or "").splitlines():
                if ln.startswith("p"):
                    pid = ln[1:]
                    holders.append({"pid": int(pid) if pid.isdigit() else pid,
                                    "comm": None})
                elif ln.startswith("n") and holders:
                    holders[-1]["path"] = ln[1:]
        except (OSError, subprocess.SubprocessError):
            pass
        out["holders"] = holders
        if holders:
            out["holder"] = holders[0]
            return out
    out["note"] = ("NO HOLDER FOUND by %s. Recorded as 'nobody seen by this "
                   "probe', never as 'nothing is holding it'." % out["probe"])
    return out


# ---------------------------------------------------------------------------
# 3. THE GPU -- declared per run, because a setting nobody wrote down is
#    indistinguishable from a decision
# ---------------------------------------------------------------------------

def probe_gpu():
    gpu = {"probe": None, "name": None, "index": None,
           "memory_total_gb": None, "memory_free_gb": None, "driver": None,
           "n_devices": None, "note": None, "raw": None}
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
        gpu["note"] = gpu["note"] or ("nvidia-smi exited %s: %s"
                                      % (p.returncode,
                                         (p.stderr or "").strip()[:200]))
        return gpu
    gpu["probe"] = ("nvidia-smi (absent) -> host is %s %s"
                    % (platform.system(), platform.machine()))
    gpu["note"] = ("NO ACCELERATOR FOUND by this probe. Recorded as null, not "
                   "0.00 and not 'none': an unprobed machine is not a machine "
                   "with no GPU. A model run on this host is CPU-only and its "
                   "numbers are not comparable to a GPU run.")
    return gpu


def host_block():
    return {"host": socket.gethostname(), "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
            "python": sys.version.split()[0], "cpu_count": os.cpu_count(),
            "gpu": probe_gpu()}


# ---------------------------------------------------------------------------
# 4. ENTRANTS
# ---------------------------------------------------------------------------

def _bfs_to_nearest_pearl(state, avoid_hazard=False, static=False):
    """Shortest path to the nearest pearl over NON-ROCK cells.

    `static` is the whole point of the `static-planner` entrant: it plans on the
    map as it is NOW and then commits to the letters, which is exactly the
    failure the dossier names -- a plan that discovers, too late, that the
    digging already done has changed what the plan needed.  It ignores hazards by
    construction, because a model that treats the map as static also treats the
    hazard's map as static.
    """
    goal = None
    for t in sorted(state.targets):
        if goal is None:
            goal = t
    dist = {state.player: (None, None)}
    q = deque([state.player])
    while q and goal not in dist:
        cur = q.popleft()
        for a in MOVE_LETTERS:
            dr, dc = DELTAS[a]
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in dist or not state.traversable(nxt):
                continue
            if avoid_hazard and state.hazard_cell(nxt):
                continue
            dist[nxt] = (cur, a)
            q.append(nxt)
    if goal not in dist:
        return None
    path = []
    c = goal
    while dist[c][0] is not None:
        path.append(dist[c][1])
        c = dist[c][0]
    path.reverse()
    return path


class Entrant(object):
    """An entrant answers ONE TURN AT A TIME (format A: the model is the
    player).  Its answer is read by the one reader and executed by the rules."""
    kind = "?"
    is_model = False
    instrument = "code"

    def start(self):
        """Admission.  -> (rc, secs, started, holder_or_None)"""
        return 0, 0.0, True, None

    def answer(self, prompt, view):
        raise NotImplementedError

    def weights_info(self):
        return None


class ReferenceSolver(Entrant):
    """THE ORACLE.  Plays a proven-optimal line; abstains on a level the
    exhaustive search has PROVEN cannot be won.

    The second half is the cabinet's own requirement, not a courtesy: level 04
    has no winning plan, so the only correct answer is the abstention token, and
    an oracle that kept playing on 04 would be demonstrating that it cannot tell
    a hard level from a lost one -- which is the faculty.
    """
    kind = "reference"
    instrument = "code"

    def __init__(self):
        self._plans = {}

    def _plan(self, view):
        lv = view["level"]
        if lv.name not in self._plans:
            row = digdug_solve.verify_level(lv, budget=view["budget"])
            self._plans[lv.name] = (row["shortest_plan"] if row["winnable"]
                                    else None)
        return self._plans[lv.name]

    def answer(self, prompt, view):
        plan = self._plan(view)
        if plan is None:
            return "GIVE UP"
        i = view["ply"]
        return plan[i] if i < len(plan) else "GIVE UP"


class SlackMaximiser(Entrant):
    """Hazard-aware to a fault: among the winning lines it takes the one that
    ends with the MOST slack, even when that costs more turns.

    This entrant exists to make R2 true in the flesh rather than in prose: it
    and the reference score IDENTICALLY (solved is the score) and their `moves`
    differ (moves is a cost).  A field with one entrant per behaviour and no
    pair like this cannot show the difference between the two rules.
    """
    kind = "reference"
    instrument = "code"

    def __init__(self):
        self._plans = {}

    def _plan(self, view):
        lv = view["level"]
        if lv.name not in self._plans:
            self._plans[lv.name] = safest_plan(lv, view["budget"])
        return self._plans[lv.name]

    def answer(self, prompt, view):
        plan = self._plan(view)
        if plan is None:
            return "GIVE UP"
        i = view["ply"]
        return plan[i] if i < len(plan) else "GIVE UP"


def _threat_of(level, snap, policy):
    """The hazard's distance from this state, or None for 'no road at all'."""
    return digdug_solve.min_hazard_distance(
        State.restore(level, snap, policy))


def safest_plan(level, budget, policy=FROZEN):
    """A winning line that keeps the MOST margin, and it may cost extra turns.

    The objective is lexicographic: win, then maximise the smallest hazard
    distance the run ever stands at, then be short.  `max-min` over a layering
    of the exhaustive graph, which is exact and costs one backward pass per
    depth -- enumerating paths instead would be exponential, and an entrant that
    needs exponential time is not an entrant, it is a rumour about one.

    A state with NO hazard road is the BEST case, not the unknown one, so it
    ranks as +infinity: `None` means "it cannot reach you", and treating that as
    zero is how a safety measure ends up preferring the danger.  The tie-break
    is `min()` over the ply, then the plan's length, then the letters, so the
    plan this returns is reproducible without a seed.
    """
    g = digdug_solve.graph(level, policy, max(budget, digdug_solve.HORIZON))
    if not g["wins"]:
        return None
    D = min(g["dist"][w] for w in g["wins"])
    NO_ROAD = 10 ** 6
    INF = float("inf")
    threat = {}
    for s in g["dist"]:
        t = _threat_of(level, s, policy)
        threat[s] = INF if t is None else t
    by_depth = {}
    for s, d in g["dist"].items():
        by_depth.setdefault(d, []).append(s)
    best_seen = None
    for depth in range(D, budget + 1):
        if depth not in by_depth:
            continue
        # backward: V[s] = the best (largest) minimum-threat reachable from s in
        # exactly the remaining plies, ending on a win.
        V = {}
        pick = {}
        for s in by_depth.get(depth, []):
            if s in g["winset"]:
                V[s] = threat[s]
        for d in range(depth - 1, -1, -1):
            for s in by_depth.get(d, []):
                cand = []
                for act, t in g["children"].get(s, ()):
                    if t in V:
                        cand.append((min(threat[s], V[t]), act, t))
                if not cand:
                    continue
                cand.sort(key=lambda x: (-x[0], x[1]))
                V[s] = cand[0][0]
                pick[s] = (cand[0][1], cand[0][2])
        if g["start"] not in V:
            continue
        score = V[g["start"]]
        if best_seen is None or score > best_seen[0]:
            path = []
            s = g["start"]
            while s in pick and len(path) < depth:
                act, nxt = pick[s]
                path.append(act)
                s = nxt
            best_seen = (score, "".join(path), depth)
            if score >= 1 and depth == D:
                break                      # optimal AND margin: nothing to buy
            if score >= NO_ROAD - 1:
                break                      # the hazard never had a road at all
        elif depth > D and best_seen[2] <= depth:
            break                          # longer lines stop buying safety
    if best_seen is None:
        return None
    plan = best_seen[1]
    return plan if len(plan) == best_seen[2] else None


class StaticPlanner(Entrant):
    """Plans the WHOLE route once, on the map as it is at ply 0, then replays
    the letters.  Never re-plans.  THE FACET-1 EXHIBIT.

    It is not stupid: the plan is a correct shortest route across the soil.  It
    is wrong in exactly the way the dossier describes, because the ground the
    plan is standing on is the ground the plan is about to remove.
    """
    kind = "planner"
    instrument = "code"

    def __init__(self):
        self._plans = {}

    def _plan(self, view):
        lv = view["level"]
        if lv.name not in self._plans:
            st = State(lv)
            route = []
            # greedy concatenation over the STATIC mobility graph: the board is
            # read once, at ply 0, and the soil is assumed to stay as it is.
            targets = sorted(lv.targets)
            cur = lv.start_player
            tunnels = set(lv.tunnels)
            for tgt in targets:
                seg = _static_path(lv, cur, tgt, tunnels)
                if seg is None:
                    route = None
                    break
                route.extend(seg)
                cur = tgt
                tunnels = tunnels | set(_cells_along(lv, seg, cur))
            self._plans[lv.name] = ("".join(route) if route else None)
        return self._plans[lv.name]

    def answer(self, prompt, view):
        plan = self._plan(view)
        if plan is None:
            return "GIVE UP"
        i = view["ply"]
        return plan[i] if i < len(plan) else "GIVE UP"


def _static_path(lv, src, dst, tunnels):
    """BFS over non-rock cells on the START board.  Ignores hazards entirely."""
    dist = {src: (None, None)}
    q = deque([src])
    walkable = (set(lv.soil) | set(lv.tunnels) | tunnels) - lv.walls
    while q and dst not in dist:
        cur = q.popleft()
        for a in MOVE_LETTERS:
            dr, dc = DELTAS[a]
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in dist or nxt not in walkable:
                continue
            dist[nxt] = (cur, a)
            q.append(nxt)
    if dst not in dist:
        return None
    out = []
    c = dst
    while dist[c][0] is not None:
        out.append(dist[c][1])
        c = dist[c][0]
    out.reverse()
    return out


def _cells_along(lv, seg, src):
    c = src
    cells = []
    for a in seg:
        dr, dc = DELTAS[a]
        c = (c[0] + dr, c[1] + dc)
        cells.append(c)
    return cells


class Beeline(Entrant):
    """Re-plans every turn, shortest path to the nearest pearl, hazards not part
    of the model.  Adaptive but blind: the cousin of StaticPlanner that survives
    more often, which is a fact the record can show rather than assert.
    """
    kind = "planner"
    instrument = "code"

    def answer(self, prompt, view):
        st = view["state"]
        path = _bfs_to_nearest_pearl(st)
        if not path:
            return "GIVE UP"
        return path[0]


class _Scripted(Entrant):
    def __init__(self, stream="L"):
        self.stream = stream
        self.i = 0

    def answer(self, prompt, view):
        s = self.stream
        out = s[self.i % len(s)]
        self.i += 1
        return out


class WallBumper(_Scripted):
    """A legal letter aimed at rock, forever.  The dossier's control."""

    def __init__(self):
        _Scripted.__init__(self, "L")


class Liar(_Scripted):
    """Legal letters, correct format, never finishes: it walks a 2-step cycle."""

    def __init__(self):
        _Scripted.__init__(self, "UD")


class Waiter(_Scripted):
    """`.` every turn.  Proves WAIT is CONSUMED as a legal action and that
    stopping IS a turn: on a level with an armed hazard this entrant dies for
    having stood still, and on the others it runs to the cap alive."""

    def __init__(self):
        _Scripted.__init__(self, ".")


class Garbage(Entrant):
    def answer(self, prompt, view):
        return ("Sure! The board looks like a warehouse, so I think the best "
                "move is to go right and then down, ending on the target.")


class Resigner(Entrant):
    """Abstains with the canonical token on every level, winnable or not."""

    def answer(self, prompt, view):
        return "GIVE UP"


class SoftResigner(Entrant):
    """Abstains the way a model actually does, in a sentence.

    Under the frozen exact-token rule this is `not_an_action` 5 times and the run
    is filed as `ERROR: ZERO MEASURED`.  That is the INSTRUMENT's finding, not
    the entrant's, and the cabinet reports it instead of hiding it -- R1 says the
    list is frozen and the loose match is a diagnostic, not a rescue.
    """

    def answer(self, prompt, view):
        return ("I give up: a hazard is already in the tunnel behind me and "
                "there is no way back.")


class PlanEmitter(Entrant):
    """Emits the PROVEN OPTIMAL PLAN, as one line, on turn 1.

    R3's exhibit.  A whole plan is the answer the arcade would want, and under a
    one-shot reading of the exchange it is THE correct answer to level 02.  Under
    this grammar it is `not_an_action`, because more than one character is never
    truncated -- so the reading in which the correct answer is a failure is a
    disproof of THAT reading, and this entrant is how the record shows it was
    measured rather than argued.
    """

    def answer(self, prompt, view):
        if view["ply"] == 0:
            row = digdug_solve.verify_level(view["level"],
                                            budget=view["budget"])
            return (row["shortest_plan"] or "GIVE UP")
        return "GIVE UP"


class NeverStarts(Entrant):
    """The admission path itself: a load that fails, and says who holds it."""
    kind = "never"
    instrument = "none"

    def start(self):
        holder = probe_holder("8080", kind="port")
        holder["load_error"] = "simulated: weights refused to load"
        return 2, 0.012, False, holder

    def answer(self, prompt, view):
        raise AssertionError("never-starts must never be asked")


class ModelEntrant(Entrant):
    """A served GGUF, reached over llama.cpp's HTTP completion API."""
    kind = "model"
    is_model = True
    instrument = "model"

    def __init__(self, model_path, server_url="http://127.0.0.1:8080",
                 port=8080):
        self.model_path = model_path
        self.server_url = server_url
        self.port = port

    def weights_info(self):
        info = {"path": self.model_path,
                "name": (os.path.basename(self.model_path)
                         if self.model_path else None),
                "sha256": None, "bytes": None, "note": None}
        if not self.model_path or not os.path.isfile(self.model_path):
            info["note"] = ("NOT MEASURED -- model path %r is not a file, so no "
                            "digest exists to record.  The NAME is carried and "
                            "the DIGEST is null WITH THIS REASON: never 0, never "
                            "a name standing in for a digest, and never a "
                            "missing digest with no explanation."
                            % (self.model_path,))
            return info
        info["sha256"] = _sha256_of(self.model_path)
        try:
            info["bytes"] = os.path.getsize(self.model_path)
        except OSError:
            info["bytes"] = None
        return info

    def start(self):
        t0 = time.perf_counter()
        if self.model_path and not os.path.isfile(self.model_path):
            return (2, round(time.perf_counter() - t0, 3), False,
                    probe_holder(self.model_path, kind="path"))
        try:
            import urllib.request
            with urllib.request.urlopen(self.server_url.rstrip("/") + "/health",
                                        timeout=10) as resp:
                resp.read(64)
            return 0, round(time.perf_counter() - t0, 3), True, None
        except Exception as exc:                                # noqa: BLE001
            holder = probe_holder(str(self.port), kind="port")
            holder["load_error"] = "%s: %s" % (type(exc).__name__, exc)
            return 2, round(time.perf_counter() - t0, 3), False, holder

    def answer(self, prompt, view):
        import urllib.request
        payload = json.dumps({
            "prompt": prompt, "n_predict": int(view.get("max_tokens", 8)),
            "temperature": float(view.get("temperature", 0.0)),
            "stop": ["\n"], "cache_prompt": False}).encode("utf-8")
        req = urllib.request.Request(
            self.server_url.rstrip("/") + "/completion", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # `content` first, `reasoning_content` never silently: the harness reads
        # whichever the model answered in and RECORDS which one it had to use.
        content = (data.get("content") or "").strip()
        if not content and data.get("reasoning_content"):
            view["field_used"] = "reasoning_content"
            content = data["reasoning_content"].strip().splitlines()[0]
        view["field_used"] = view.get("field_used") or "content"
        return content


ENTRANTS = {
    "reference": ReferenceSolver,
    "slack-maximiser": SlackMaximiser,
    "static-planner": StaticPlanner,
    "beeline": Beeline,
    "liar": Liar,
    "wall-bumper": WallBumper,
    "waiter": Waiter,
    "resigner": Resigner,
    "soft-resigner": SoftResigner,
    "plan-emitter": PlanEmitter,
    "garbage": Garbage,
    "never-starts": NeverStarts,
    "model": ModelEntrant,
}

#: Entrants that are CODE.  A code entrant is a DIFFERENT INSTRUMENT and is never
#: pooled into a model table.
ON_BOARD = {"model"}


# ---------------------------------------------------------------------------
# 5. THE ROUND -- one level played to its end, BOTH FACETS READ OFF THE TRACE
# ---------------------------------------------------------------------------

def facet_rows(item):
    """PROJECT THE ONE TRACE ONTO TWO QUESTIONS.  Demand D.

    Nothing here re-runs the game, and nothing here is a second event: every
    number is read back out of `item["trace"]`, which is the record of the same
    plies the score was computed from.  F1 asks what the digging did to the
    PLAYER's options; F2 asks what it did to the HAZARD's.  A row that answered
    both would be answering neither, which is why they are two projections of
    one object and not two objects.
    """
    tr = item["trace"]
    plies = [p for p in tr if p.get("consumed")]
    f1 = {"question": "did the plan consume the ground it needed?",
          "read_from": "trace[] rows F1_*, same plies as F2",
          "plies_examined": len(plies),
          "mobility_shrink_events": 0,
          "plies_negative_balance": 0,
          "plies_negative_progress": 0,
          "plies_objective_lost_while_mobile": 0,
          "first_ply_objective_lost_while_mobile": None,
          "min_slack": None,
          "runs_ending_lost_while_mobile": None,
          "committed_plies": 0,
          "digs": item["digs"]}
    f2 = {"question": "did the route it dug open a path for the hazard that "
                      "killed it?",
          "read_from": "trace[] rows F2_*, same plies as F1",
          "arming_plies": 0,
          "first_arming_ply": None,
          "ever_armed": False,
          "killed": bool(item["killed_at"]),
          "killed_at_ply": item["killed_at"],
          "deaths_armed_by_own_dig": 0,
          "deaths_at_the_arming_ply": 0,
          "deaths_with_a_safe_alternative": 0,
          "arms_with_no_safe_alternative": 0,
          "min_threat_at_win": None,
          "photo_finish_wins": 0,
          "attribution": None}
    prev_mob = None
    armed_prev = None
    for p in plies:
        r = p.get("diag") or {}
        mob = r.get("F1_mobility")
        if mob is not None and prev_mob is not None and mob < prev_mob:
            f1["mobility_shrink_events"] += 1
        if mob is not None:
            prev_mob = mob
        if r.get("balance") is not None and r["balance"] < 0:
            f1["plies_negative_balance"] += 1
        if r.get("progress") is not None and r["progress"] < 0:
            f1["plies_negative_progress"] += 1
        if r.get("slack") is not None:
            f1["min_slack"] = (r["slack"] if f1["min_slack"] is None
                               else min(f1["min_slack"], r["slack"]))
        if r.get("F1_committed_to_dug_ground"):
            f1["committed_plies"] += 1
        lost = (r.get("F1_completable_within_budget") is False
                and r.get("F1_mobility_equals_start_mobility"))
        if lost:
            f1["plies_objective_lost_while_mobile"] += 1
            if f1["first_ply_objective_lost_while_mobile"] is None:
                f1["first_ply_objective_lost_while_mobile"] = p["ply"]
        ar = r.get("F2_armed")
        if ar and not armed_prev:
            f2["arming_plies"] += 1
            if f2["first_arming_ply"] is None:
                f2["first_arming_ply"] = p["ply"]
        if ar:
            f2["ever_armed"] = True
        armed_prev = ar
        if r.get("F2_arming_ply") is not None:
            p["F2_arming_ply_row"] = r["F2_arming_ply"]
    if f1["plies_objective_lost_while_mobile"]:
        f1["runs_ending_lost_while_mobile"] = (
            item["terminal"] in ("KILLED_BY_HAZARD", "BUDGET_EXHAUSTED",
                                 "ENTOMBED_BY_A_LIVING_WALL",
                                 "STREAM_ENDED_UNFINISHED"))
    # F2's kill-side numbers need the arming ply and the safe-alternative search,
    # both of which are on the trace rows the runner recorded.
    kill = item.get("killed_at")
    if kill:
        if f2["first_arming_ply"] is not None and f2["first_arming_ply"] <= kill:
            f2["deaths_armed_by_own_dig"] = 1
        if f2["first_arming_ply"] == kill:
            f2["deaths_at_the_arming_ply"] = 1
        alt = item.get("safe_alternatives_at_arming_ply")
        if alt:
            f2["deaths_with_a_safe_alternative"] = 1
        elif alt is not None:
            f2["arms_with_no_safe_alternative"] = 1
    elif item["solved"]:
        f2["photo_finish_wins"] = 1 if (
            item.get("threat_at_winning_ply") == 1) else 0
        f2["min_threat_at_win"] = item.get("threat_at_winning_ply")
    if f2["ever_armed"]:
        f2["attribution"] = ("every route a hazard used was dug by the player, "
                             "by [D-T0]; so attribution is 1.000 by CONSTRUCTION "
                             "and is NOT a finding about the entrant -- see "
                             "SECTION_4F.md item 2.  The finding is whether the "
                             "arming ply had an alternative.")
        if f2["deaths_armed_by_own_dig"]:
            f2["attribution_rate"] = 1.0
    return {"F1_search_under_destruction": f1,
            "F2_hazard_aware_planning": f2}


def play_level(level, entrant, budget, retries, max_tokens, temperature,
               with_diagnostics=True):
    """Play one level to its end.  -> dict.

    The answer is CHECKED BY EXECUTING IT: feed() reads it with the one reader
    and runs it through resolve_turn().  Nothing here compares the answer to a
    known solution -- the board decides `solved`, and the only way to be right is
    to be right on the soil.
    """
    state = State(level, FROZEN)
    diag = (digdug_solve.Diagnostics(level, FROZEN, budget=budget)
            if with_diagnostics else None)
    history = []
    raws = []
    corrections = 0
    corrections_ignored = 0
    prev_armed = diag.armed(state.snapshot()) if diag else None
    prev_task = diag.dist_to_win(state.snapshot()) if diag else None
    prev_threat = diag.min_distance(state.snapshot()) if diag else None
    start_row = None
    if diag is not None:
        start_row = diag.row(state.snapshot(), 0, None, None, None)
    t0 = time.perf_counter()
    while True:
        prompt = build_prompt(level, state, state.render(), history,
                              state.moves, len(state.targets), state.solved,
                              state.min_hazard_distance)
        view = {"level": level, "state": state, "ply": state.consumed,
                "budget": budget, "max_tokens": max_tokens,
                "temperature": temperature}
        raw = entrant.answer(prompt, view)
        raws.append(raw)
        before_na = state.not_an_action
        ply = feed(state, raw, budget=budget)
        ply["raw"] = raw
        ply["prompt_sha256"] = hashlib.sha256(
            prompt.encode("utf-8")).hexdigest()[:16]
        snap = state.snapshot()
        if diag is not None and ply.get("consumed"):
            row = diag.row(snap, state.consumed, prev_armed, prev_task,
                           prev_threat)
            ply["diag"] = row
            prev_armed = row["F2_armed"]
            prev_task = row["F1_dist_to_win"]
            prev_threat = row["F2_min_hazard_distance"]
        if state.consumed and not state.ended:
            pass
        # F2's sharp number: at the ply that OPENED a hazard's road, which
        # actions were safe?  `state.arming_ply` does not exist -- the engine
        # carries `armed_at`, and the first version of this line quietly never
        # fired, so the field stayed absent and `deaths_with_a_safe_alternative`
        # and `arms_with_no_safe_alternative` were both 0 for every entrant: two
        # zeros that looked like a finding and were a wiring bug.  The ply's own
        # `arming_ply` from resolve_turn is the flag, and the absent-vs-empty
        # distinction below is what the two counters mean.
        if diag is not None and ply.get("consumed") and \
                ply.get("arming_ply") is not None:
            ply["F2_safe_alternatives_at_arming_ply"] = diag.safe_alternatives(
                snap, state.consumed)
        if state.not_an_action > before_na and retries > 0 \
                and corrections < retries:
            corrections += 1
            continue
        history.append(ply.get("action") or "?")
        if state.ended or state.emitted >= budget + max(0, retries) + 1 \
                or state.consumed >= budget:
            break
    secs = round(time.perf_counter() - t0, 3)
    never_acted = (state.moves == 0 and state.blocked == 0)
    if corrections and never_acted:
        corrections_ignored = corrections

    item = {
        "level": level.name,
        "level_sha256": level.sha256,
        "enclosed_measured": level.enclosed,
        "enclosed_note": ("B2: measured by the parser's flood fill on the board "
                          "as authored, for this run, not asserted by a level "
                          "file or a comment"),
        "solved": state.solved,
        "moves": state.moves,
        "attempted_emitted": state.emitted,
        "attempted_consumed": state.consumed,
        "blocked": state.blocked,
        "waited": state.waited,
        "digs": state.digs,
        "collects": state.collects,
        "not_an_action": state.not_an_action,
        "give_up": state.give_up,
        "after_end": state.after_end,
        "over_budget": state.over_budget,
        "gave_up_at": state.gave_up_at,
        "hazard_turns": state.hazard_turns,
        "armed_at": state.armed_at,
        "killed_at": state.killed_at,
        "killed_by": state.killed_by,
        "digs_by_word_vs_delta": {
            "by_word": sum(1 for p in state.trace if p.get("word") == "dug"),
            "by_delta": state.digs},
        "terminal": terminal_reason(state, budget),
        "budget": budget,
        "budget_exhausted": state.consumed >= budget,
        "corrections_offered": corrections,
        "corrections_ignored": corrections_ignored,
        "never_produced_a_legal_action": never_acted,
        "produced_a_legal_action": not never_acted,
        "final_board": state.render(),
        "board_is": "BOARD AFTER THE LAST CONSUMED ANSWER",
        "trace": state.trace,
        "start_diag": start_row,
        "secs": secs,
        "rules_fired": sorted({p.get("rule_fired") for p in state.trace
                               if p.get("rule_fired")}),
    }
    win_rows = [p for p in state.trace if p.get("solved")]
    if win_rows:
        item["threat_at_winning_ply"] = win_rows[-1].get("min_hazard_distance")
    arming = [p for p in state.trace
              if p.get("F2_safe_alternatives_at_arming_ply") is not None]
    if arming:
        item["safe_alternatives_at_arming_ply"] = arming[0][
            "F2_safe_alternatives_at_arming_ply"]
        item["safe_alternatives_ply"] = arming[0]["ply"]
    elif state.armed_at is not None:
        # an armed level with no alternative searched is NOT the same claim as an
        # armed level where the search ran and found none: the first is a gap in
        # the record, the second is a finding about the level.
        item["safe_alternatives_at_arming_ply"] = None
        item["safe_alternatives_note"] = (
            "the hazard had a road from ply %d and the search for an alternative "
            "was not run at a ply that opened one -- the level armed BEFORE the "
            "first answer, so no ply of this run is an arming ply"
            % state.armed_at)
    item["facets"] = facet_rows(item)
    return item


def _lost_item(level, budget, admission):
    return {"level": level.name, "level_sha256": level.sha256,
            "enclosed_measured": level.enclosed,
            "solved": False, "moves": 0, "attempted_emitted": 0,
            "attempted_consumed": 0, "blocked": 0, "waited": 0, "digs": 0,
            "collects": 0, "not_an_action": 0, "give_up": 0, "after_end": 0,
            "over_budget": 0, "armed_at": None, "killed_at": None,
            "killed_by": None, "gave_up_at": None, "hazard_turns": 0,
            "digs_by_word_vs_delta": {"by_word": 0, "by_delta": 0, "gap": 0},
            "enclosed_measured": level.enclosed,
            "terminal": "NEVER_STARTED", "budget": budget,
            "budget_exhausted": False, "corrections_offered": 0,
            "corrections_ignored": 0,
            "never_produced_a_legal_action": True,
            "produced_a_legal_action": False,
            "final_board": render(State(level)),
            "board_is": ("START BOARD -- the entrant never moved; this is the "
                         "level's initial state, not a result"),
            "trace": [], "start_diag": None, "secs": 0.0, "rules_fired": [],
            "reason": ("entrant never started (rc=%s in %ss); holder: %s"
                       % (admission["rc"], admission["secs"],
                          (admission.get("holder") or {}).get("holder"))),
            "facets": facet_rows({"trace": [], "digs": 0, "killed_at": None,
                                   "solved": False, "terminal": "NEVER_STARTED",
                                   "threat_at_winning_ply": None})}


# ---------------------------------------------------------------------------
# 6. THE RUN
# ---------------------------------------------------------------------------

def run_entrant(entrant, levels, budget=DEFAULT_ATTEMPT_BUDGET,
                retries=DEFAULT_RETRIES, max_tokens=8, temperature=0.0):
    rc, secs, started, holder = entrant.start()
    admission = {"rc": rc, "secs": secs, "started": bool(started),
                 "never_started": (not started),
                 "holder": holder if isinstance(holder, dict) else None}
    items = {}
    if started:
        for name in LEVEL_FILES:
            items[name] = play_level(levels[name], entrant, budget, retries,
                                      max_tokens, temperature)
    else:
        for name in LEVEL_FILES:
            items[name] = _lost_item(levels[name], budget, admission)

    started_n = sum(1 for it in items.values()
                    if it["terminal"] != "NEVER_STARTED")
    emitted_items = sum(1 for it in items.values() if it["attempted_emitted"])
    consumed_items = sum(1 for it in items.values()
                         if it["attempted_consumed"])
    readable = sum(1 for it in items.values()
                   if it["attempted_consumed"] > it["not_an_action"])
    solved_n = sum(1 for it in items.values() if it["solved"])
    planned = len(LEVEL_FILES)
    never_started_n = planned - started_n
    coverage = round(started_n / float(planned), 6) if planned else 0.0

    # R2: solved IS the score, and the gate wants a RATE.  The denominator is
    # attempted_emitted, per the standing rule, and the difference between it and
    # attempted_consumed is a number in its own right (B1) -- never reconciled
    # away by picking whichever one flatters the run.
    score = (round(solved_n / float(emitted_items), 6) if emitted_items
             else None)
    if not started or started_n == 0:
        verdict = "ERROR: POPULATION NEVER STARTED"
        exit_code = EXIT_NEVER_STARTED
    elif readable == 0:
        verdict = "ERROR: ZERO MEASURED (nothing readable was produced)"
        exit_code = EXIT_ZERO_MEASURED
    else:
        verdict = "SCORED"
        exit_code = EXIT_SCORED

    def tot(key):
        return sum(it[key] for it in items.values())

    facets = {}
    for fk in ("F1_search_under_destruction", "F2_hazard_aware_planning"):
        agg = {}
        counts = {}
        for it in items.values():
            for k, v in it["facets"][fk].items():
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    continue
                # SUM and COUNT together.  A facet aggregate that sums a field
                # `min_slack` while two of five items had None there is a sum over
                # an unnamed subset -- which is how a mean quietly becomes a
                # verdict.  Every number here says how many items fed it.
                agg[k] = agg.get(k, 0) + v
                counts[k] = counts.get(k, 0) + 1
        for k in list(agg):
            agg[k + "__items"] = counts[k]
        agg["n_items"] = len(items)
        agg["note_missing"] = ("a field absent from this dict had NO numeric value "
                              "on any item -- which is a different statement from "
                              "the field being 0, and is why `min_slack` may be "
                              "missing rather than zero")
        facets[fk] = agg
    facets["F1_search_under_destruction"]["items_objective_lost_while_mobile"] \
        = sum(1 for it in items.values()
              if it["facets"]["F1_search_under_destruction"]
              ["plies_objective_lost_while_mobile"])
    facets["F2_hazard_aware_planning"]["items_that_died_after_arming"] = sum(
        1 for it in items.values()
        if it["facets"]["F2_hazard_aware_planning"]["deaths_armed_by_own_dig"])
    facets["note"] = ("D: both facets are projections of ONE trace per item. "
                      "The same plies, the same run, the same recorded raws. "
                      "There is no second event in this cabinet and no number "
                      "here that required one.")
    rnd = {
        "score": score,
        "wins": solved_n,
        "trials": emitted_items,
        "items_attempted_emitted": emitted_items,
        "items_attempted_consumed": consumed_items,
        "score_is": "solved levels / levels on which an answer was EMITTED "
                    "(R2's rate at the gate).  `moves` is carried per item and "
                    "in `totals` and is NOT averaged: it is a COST, not a score.",
        "denominator_rule": ("NEVER_STARTED sits OUTSIDE both denominators and is "
                             "counted separately (B1); an item where every answer "
                             "was unreadable is still EMITTED and is still in the "
                             "denominator, which is what makes the zero rule "
                             "bite."),
        "kind": "grid_puzzle_destructive",
        "class": "CONTEST",
        "oracle": ("rules_frozen_before_the_run_and_verified_by_exhaustive_"
                   "search"),
        "staged_as": ("arcade cabinet -- DIG DUG: the soil you dig is the road "
                      "that reaches you"),
        "items": items,
        "facets": facets,
        "started": started_n, "readable": readable,
        "never_started": never_started_n, "coverage": coverage,
        "totals": {
            "moves": tot("moves"),
            "attempted_emitted": tot("attempted_emitted"),
            "attempted_consumed": tot("attempted_consumed"),
            "digs": tot("digs"),
            "collects": tot("collects"),
            "blocked": tot("blocked"),
            "waited": tot("waited"),
            "not_an_action": tot("not_an_action"),
            "after_end": tot("after_end"),
            "over_budget": tot("over_budget"),
            "give_up": tot("give_up"),
            "hazard_turns": tot("hazard_turns"),
            "corrections_offered": tot("corrections_offered"),
            "corrections_ignored": tot("corrections_ignored"),
            "loose_give_up_unscored": sum(
                1 for it in items.values() for ply in it["trace"]
                if ply["reading"].get("loose_give_up_diagnostic")
                and ply["reading"]["outcome"] != "give_up"),
        },
        "loose_give_up_note": ("answers that LOOKED like an abstention to a "
                               "substring test but were scored not_an_action by "
                               "the frozen exact-token list. DIAGNOSTIC ONLY -- "
                               "never scored, never folded into give_up [R1]."),
        "attempt_budget_per_level": budget,
    }
    return {"admission": admission, "round": rnd, "verdict": verdict,
            "exit_code": exit_code, "aggregate": score, "coverage": coverage}


# ---------------------------------------------------------------------------
# 7. THE BUNDLE
# ---------------------------------------------------------------------------

def build_bundle(entrant_name, result, levels, reasoning="unset", gpu=None,
                 weights=None, config_extra=None, frozen=None):
    ent = ENTRANTS.get(entrant_name)
    on_board = entrant_name in ON_BOARD
    w = weights if weights is not None else (
        ent().weights_info() if ent else None)
    rnd = result["round"]
    items = rnd["items"]
    terminals = sorted({it["terminal"] for it in items.values()})
    rules = sorted({r for it in items.values() for r in it["rules_fired"]})
    return {
        "harness": HARNESS, "version": VERSION, "generated": now_utc(),
        "event": EVENT, "card_version": CARD_VERSION,
        "declared": {
            "reasoning": reasoning,
            "reasoning_note": ("DECLARED per-run instrument field. 'unset' is "
                               "NOT 'off': an undeclared run must not be pooled "
                               "with a declared one. Same weights with thinking "
                               "ON versus OFF produced OPPOSITE outcomes on this "
                               "circuit's first cabinet."),
            "gpu": gpu if gpu is not None else probe_gpu(),
            "gpu_note": ("DECLARED per-run. No accelerator is recorded as null "
                         "with the probe that ran, never 0.00 and never 'none'."),
            "budget_per_level": rnd["attempt_budget_per_level"],
            "budget_note": ("the cap is a DECISION (D-BUDGET), it is the horizon "
                           "of the per-ply proof, and control [HZ] asserts "
                           "HORIZON >= budget instead of assuming it"),
        },
        "frozen_contract": {
            "document": "digdug/CONTRACT_digdug_v1.md",
            "manifest": "digdug/CONTRACT_frozen.json",
            "frozen_utc": (frozen or {}).get("frozen_utc"),
            "digests": (frozen or {}).get("digests"),
            "frozen_before_this_run": bool(
                (frozen or {}).get("frozen_utc")
                and (frozen or {}).get("frozen_utc") <= now_utc()),
            "note": ("the freeze is a GATE: run_digdug refuses every entrant "
                     "until the manifest exists and every digest matches the "
                     "file on disk, so this field cannot be true by accident"),
        },
        "results": [{
            "entrant": entrant_name,
            "kind": (ent.kind if ent else "model"),
            "instrument": (ent.instrument if ent else "model"),
            "instrument_note": ("CODE entrant, not a model -- a DIFFERENT "
                                "INSTRUMENT; never pooled into a model table"
                                if not on_board else
                                "MODEL entrant: weights were loaded and served."),
            "entrant_is_a_model": bool(ent.is_model if ent else True),
            "on_board": on_board,
            "weights": w,
            "weights_sha256": (w or {}).get("sha256"),
            "verdict_code": {
                "module": "digdug_run.py", "function": "run_entrant",
                "sha256": _sha256_of(os.path.join(HERE, "digdug_run.py")),
                "simulator": {"module": "digdug.py",
                              "sha256": _sha256_of(
                                  os.path.join(HERE, "digdug.py")),
                              "transition":
                                  "step(state, action) -> ((row, col), word); "
                                  "mutates; raises outside the alphabet; "
                                  "bounds checked inside"},
                "reader": {"module": "digdug_reader.py",
                           "sha256": reader_sha256(),
                           "note": "ONE reader of record, imported by every "
                                   "side script, never reimplemented"},
                "solver": {"module": "digdug_solve.py",
                           "sha256": _sha256_of(
                               os.path.join(HERE, "digdug_solve.py")),
                           "role": ("proves the optima, proves 04 lost, and "
                                    "supplies both facets' per-ply "
                                    "diagnostics.  Never scores.")},
            },
            "rules_fired": rules,
            "rules_declared": list(digdug_reader_RULES()),
            "rules_subset_ok": set(rules) <= set(digdug_reader_RULES())
                               | {"SHADOW.wait_illegal"},
            "terminals": terminals,
            "terminal_reason": {
                "per_level": {k: v["terminal"] for k, v in items.items()},
                "corrections_offered": rnd["totals"]["corrections_offered"],
                "corrections_ignored": rnd["totals"]["corrections_ignored"],
                "note": ("corrections_ignored > 0 means the entrant was TOLD its "
                         "answer was unreadable and produced no legal action "
                         "anyway -- not the same finding as producing legal "
                         "actions that failed."),
            },
            "config": {
                "temperature": (config_extra or {}).get("temperature", 0.0),
                "max_tokens": (config_extra or {}).get("max_tokens", 8),
                "trials": 1, "ctx": (config_extra or {}).get("ctx"),
                "n_gpu_layers": (config_extra or {}).get("n_gpu_layers"),
                "server_flags": (config_extra or {}).get("server_flags"),
                "attempt_budget_per_level": rnd["attempt_budget_per_level"],
                "retries_on_unreadable": (config_extra or {}).get("retries"),
                "reasoning": reasoning,
                "entrant_reasoning": None if not on_board else reasoning,
                "entrant_reasoning_note": (
                    "NOT APPLICABLE -- this entrant is code; no model was served "
                    "and no reasoning setting existed. Recorded as null with "
                    "this reason, never 'off' and never omitted."
                    if not on_board else
                    "the entrant is a served model; its reasoning setting is the "
                    "run's declaration."),
                "config_note": ("RUN_FACTS that do not exist on this host are "
                                "null, not omitted and not zeroed."),
            },
            "contract": {
                "clauses_frozen_for_this_run": FROZEN.as_record(),
                "decisions_index": {k: list(v) for k, v in
                                   sorted(digdug.DECISIONS.items())},
                "prose_source": ("the one paragraph in section 3 of the Tier-3 "
                                 "brief; every clause it did not settle is "
                                 "marked [UNDER-SPECIFIED] in the frozen "
                                 "document and [D-*] in the code"),
            },
            "hardware": (config_extra or {}).get("hardware") or host_block(),
            "admission": result["admission"],
            "rounds": {ROUND_ID: rnd},
            "grammar": grammar_as_record(),
            "levels": {
                name: {"sha256": levels[name].sha256,
                       "enclosed_measured": levels[name].enclosed,
                       "optimal_moves": _proven_optimum(name),
                       "proof": "digdug_solve.py (see tasks/digdug_v1.json)"}
                for name in LEVEL_FILES},
            "aggregate": result["aggregate"],
            "coverage": result["coverage"],
            "verdict": result["verdict"],
            "exit_code": result["exit_code"],
            "exit_code_table": EXIT_CODES,
            "certification": ("REFERENCE RUN -- not an entrant, not for the "
                              "board." if not on_board else
                              "MODEL RUN -- on the board."),
            "tasks": "digdug/tasks/digdug_v1.json",
            "decisions": "digdug/DIGDUG_DECISIONS.md",
            "section_4f": "digdug/SECTION_4F.md",
        }],
    }


def _proven_optimum(name):
    """Read the item set the solver wrote BEFORE the field ran.

    The runner does not recompute optima into the bundle: the number the bundle
    carries is the number that was frozen for the item, and if the two were
    produced at different moments a reader could not tell a proof from a
    re-derivation after seeing the answers.
    """
    try:
        with open(TASKS_OUT) as fh:
            td = json.load(fh)
    except (OSError, ValueError):
        return None
    for row in td.get("levels", []):
        if row["file"].split("/")[-1] == name:
            return row["optimal_moves"]
    return None


def digdug_reader_RULES():
    from digdug_reader import Reading
    return Reading.RULES


def write_bundle(bundle, out_dir, name):
    """WRITE THE RECORD.  Called BEFORE the success/failure branch, always."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "digdug_v1_%s.json" % name)
    tmp = path + ".partial"
    with open(tmp, "w") as fh:
        json.dump(bundle, fh, indent=2, default=str)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------------------
# 8. THE ITEM SET -- produced by the solver, never by hand
# ---------------------------------------------------------------------------

def cmd_tasks(args):
    """Write tasks/digdug_v1.json from the exhaustive proofs."""
    levels = digdug.load_level_set()
    budget = getattr(args, "budget", None) or DEFAULT_ATTEMPT_BUDGET
    rows = []
    for name in LEVEL_FILES:
        r = digdug_solve.verify_level(levels[name], budget=budget)
        rows.append(r)
    ok_freeze, detail = freeze_state()
    doc = {
        "id": CARD_VERSION,
        "event": EVENT,
        "class": "CONTEST",
        "kind": "grid_puzzle_destructive",
        "oracle": "rules_frozen_before_the_run_and_verified_by_exhaustive_search",
        "staged_as": "arcade cabinet -- DIG DUG: the soil you dig is the road "
                     "that reaches you",
        "note": ("Five levels.  01 is the FLOOR and it is also the exhibit for "
                 "[D-END]: under the rejected reading of 'whose turn resolves "
                 "first' the floor becomes UNWINNABLE, which is measured, not "
                 "argued.  02 is the race: the shortest route kills you and a "
                 "seven-ply route lives.  03 is the four-optima level, and the "
                 "one where a committed static plan discovers that its own "
                 "digging changed what it needed.  04 is PROVEN LOST by exhaustive "
                 "search over its whole state space, and the only correct answer "
                 "to it is the abstention token.  05 is the photo finish: the "
                 "last pearl is collected on the ply a hazard would have stepped "
                 "onto the player.  Every optimum here was produced by "
                 "digdug_solve.py BEFORE any entrant ran, and the count of "
                 "distinct optimal lines is recorded beside it (R2)."),
        "contract_frozen": os.path.relpath(FROZEN_MANIFEST, HERE)
                           if ok_freeze else None,
        "contract_frozen_ok": ok_freeze,
        "levels": [{
            "id": r["level"].replace(".txt", ""),
            "file": "levels/" + r["level"],
            "sha256": r["sha256"],
            "optimal_moves": r["proven_optimal"],
            "winnable": r["winnable"],
            "distinct_shortest_plans": r["distinct_shortest_plans"],
            "has_multiple_optima": r["has_multiple_optima"],
            "example_plan": r["shortest_plan"],
            "proof_grade": r["proof_grade"],
            "n_states_explored": r["n_states_explored"],
            "loss_claim": r["loss_claim"],
            "enclosed_measured": r["enclosed"],
            "n_targets": r["n_targets"],
            "n_hazards": r["n_hazards"],
            "proven_by": "digdug_solve.py",
        } for r in rows],
        "criteria_frozen_before_run": {
            "C1_answer_is_executed": ("the answer is checked by EXECUTING it "
                                      "through resolve_turn(); never by reading "
                                      "it against a reference plan"),
            "C2_solved_is_the_score": ("R2: score = solved / attempted_emitted; "
                                       "moves is a cost carried beside it and "
                                       "never averaged"),
            "C3_abstention_is_scoreable": ("give_up is a legal answer and it is "
                                          "the ONLY correct answer to 04; the "
                                          "frozen token list must equal the "
                                          "code's, and control [R1] checks that "
                                          "as a multiset"),
            "C4_emitted_vs_consumed": ("B1: two numbers, both recorded, never "
                                       "reconciled"),
            "C5_record_before_verdict": "the bundle is written before the branch",
            "C6_exit_code_from_the_run": ("every code is produced by a path the "
                                          "instrument check drives"),
            "C7_bounds_in_step": ("B2: the transition function checks the frame "
                                  "itself, and `enclosed` is measured per level"),
            "C8_two_facets_one_trace": ("D: F1 and F2 are projections of the "
                                        "same trace; no second event exists"),
        },
        "declared_per_run": {
            "reasoning": "on | off | unset -- DECLARED before the run; 'unset' "
                         "is NOT 'off' and must not be pooled",
            "gpu": "the accelerator the run used, WITH the probe that "
                   "established it",
            "budget": "%d plies per level, and the horizon of the per-ply proof"
                      % budget,
        },
    }
    os.makedirs(os.path.dirname(TASKS_OUT), exist_ok=True)
    with open(TASKS_OUT, "w") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    print("wrote %s (contract frozen: %s)" % (
        os.path.relpath(TASKS_OUT, HERE), ok_freeze))
    for r in rows:
        print("  %-32s opt=%-4s plans=%-2s %-11s %s"
              % (r["level"], r["proven_optimal"], r["distinct_shortest_plans"],
                 r["proof_grade"], "LOST" if not r["winnable"] else "won"))
    return 0


# ---------------------------------------------------------------------------
# 9. INSTRUMENT CHECK -- prove the harness can play DIG DUG.  Enters nothing.
# ---------------------------------------------------------------------------

def _say(cond, label, seen=None):
    print("  %s %s%s" % ("ok  " if cond else "FAIL", label,
                         "" if cond or seen is None else "   <- %r" % (seen,)))
    return bool(cond)


def instrument_check(out_dir=None, reasoning="unset", budget=None,
                     include_simulator_self_test=True):
    ok = True
    budget = budget or DEFAULT_ATTEMPT_BUDGET
    print("INSTRUMENT CHECK -- DIG DUG.  Proves the harness; enters nothing.")
    print()

    ok &= _say(digdug_readings_available(),
               "FROZEN GATE: the readings module is importable (the shadow "
               "table is part of the instrument, not an extra)")

    # [FZ] THE FREEZE
    print("\n[FZ] the contract is frozen against disk, and the run refuses "
          "otherwise")
    frozen_ok, detail = freeze_state()
    ok &= _say(frozen_ok, "FREEZE: every digest in CONTRACT_frozen.json matches "
                          "the file on disk",
               {k: v["match"] for k, v in detail["files"].items()}
               if not frozen_ok else detail.get("frozen_utc"))
    ok &= _say(bool(detail.get("frozen_utc")),
               "FREEZE: the manifest carries the instant of the freeze, so "
               "'before every entrant' is checkable against each bundle",
               detail.get("frozen_utc"))
    tam = os.path.join(HERE, "results", ".tampered_freeze.json")
    try:
        with open(FROZEN_MANIFEST) as fh:
            _man0 = json.load(fh)
        k0 = sorted(_man0["digests"])[0]
        _man0["digests"][k0] = "0" * 64
        os.makedirs(os.path.dirname(tam), exist_ok=True)
        with open(tam, "w") as fh:
            json.dump(_man0, fh)
        bad_ok, bad_detail = freeze_state(tam)
        ok &= _say(bad_ok is False,
                   "FREEZE: a manifest whose digest does not match the file on "
                   "disk is REFUSED -- the gate closes on drift, not only on "
                   "absence", bad_detail.get("note"))
        hole = {k: v for k, v in bad_detail.items()}
        _man0["digests"] = {k: v for k, v in
                            sorted(_man0["digests"].items())[:-1]}
        with open(tam, "w") as fh:
            json.dump(_man0, fh)
        hole_ok, hole_detail = freeze_state(tam)
        ok &= _say(hole_ok is False,
                   "FREEZE: a manifest MISSING an entry is refused, not treated "
                   "as a match-by-omission.  The first version of this gate "
                   "iterated a key the writer never wrote, so its loop body "
                   "never ran and it passed having compared nothing -- this "
                   "control is the reason that cannot come back quietly",
                   hole_detail.get("note"))
    except (OSError, ValueError, KeyError) as exc:                        # noqa: BLE001
        _say(False, "FREEZE: the tamper controls could not run", repr(exc))
        ok = False
    finally:
        try:
            os.remove(tam)
        except OSError:
            pass

    # [0] the simulator's own controls
    if include_simulator_self_test:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = digdug.self_test()
        ok &= _say(rc == 0, "SIMULATOR: --self-test exits 0", rc)

    # [1] THE LEVELS -- optima proven, not asserted
    print("\n[1] the frozen optima, produced by exhaustive search")
    levels = digdug.load_level_set()
    claims = {}
    if os.path.isfile(TASKS_OUT):
        with open(TASKS_OUT) as fh:
            td = json.load(fh)
        for lv in td.get("levels", []):
            claims[lv["file"].split("/")[-1]] = {
                "optimal_moves": lv["optimal_moves"],
                "distinct_shortest_plans": lv["distinct_shortest_plans"],
                "winnable": lv["winnable"]}
    ok &= _say(bool(claims), "TASKS: the item set exists, so the optima were "
                             "written before the field, by `tasks`",
               sorted(claims) or "no tasks/digdug_v1.json")
    t0 = time.perf_counter()
    lv_ok, rows = digdug_solve.verify_levels(levels, claims=claims or None,
                                             budget=budget)
    for r in rows:
        if "error" in r:
            _say(False, "LEVEL: %s -- %s" % (r["level"], r["error"]))
            ok = False
            continue
        _say(r["agree"] if claims else True,
             "LEVEL: %s optimal %s plans %s (%s, %d states)"
             % (r["level"], r["proven_optimal"], r["distinct_shortest_plans"],
                r["proof_grade"], r["n_states_explored"]), r["shortest_plan"])
        ok = ok and (r["agree"] if claims else True)
        ok &= _say(r["horizon_ok"], "LEVEL: %s horizon %s covers the budget %d"
                   % (r["level"], r["proof_grade"], budget), r["truncated_at_depth"])
    print("  (verification took %.1fs)" % (time.perf_counter() - t0))

    # [HZ] the horizon control, stated as its own line because everything else
    # relies on it
    ok &= _say(digdug_solve.HORIZON >= budget,
               "HZ: the solver's horizon (%d) >= the run's budget (%d), so "
               "'completable' means something and 'unknown' is never read as "
               "'no'" % (digdug_solve.HORIZON, budget))

    # [04] the lost level, and the proof grade that licenses the claim
    print("\n[04] the lost level: a proof, not a timeout")
    lost = digdug_solve.verify_level(levels["04_the_only_door.txt"],
                                     budget=budget)
    ok &= _say(lost["winnable"] is False and lost["exhaustive"],
               "LEVEL 04: PROVEN LOST with grade exhaustive -- %s"
               % lost["loss_claim"], lost)
    ok &= _say(lost["distinct_shortest_plans"] == 0,
               "LEVEL 04: it has ZERO optimal lines, and the record says so "
               "instead of leaving the field blank")
    other = [n for n in LEVEL_FILES if n != "04_the_only_door.txt"]
    for n in other:
        r = digdug_solve.verify_level(levels[n], budget=budget)
        ok &= _say(r["winnable"], "%s is winnable at cost %s" % (n, r["proven_optimal"]))

    # [2] the reader and the grammar
    print("\n[2] the reader, and R1")
    ok &= _say(read_answer("GIVE UP").outcome == OUTCOME_GIVE_UP,
               "READER: the canonical abstention token reads as give_up")
    ok &= _say(read_answer("GIVE UP!").outcome == OUTCOME_NOT_AN_ACTION,
               "READER: punctuation is not stripped -- the frozen rule fails "
               "CLOSED on abstention, and the loose match is a diagnostic")
    ok &= _say(read_answer("RR").outcome == OUTCOME_NOT_AN_ACTION,
               "READER: two letters are never truncated to one")
    ok &= _say(read_answer("A").outcome == OUTCOME_NOT_AN_ACTION
               and read_answer("D").action == "D",
               "READER [D-WASD]: A is refused and D is DOWN, never RIGHT")
    ok &= _say(read_answer(".").action == ".",
               "READER [D-STOP]: the wait letter is an ACTION, not a refusal")
    from digdug_reader import Reading
    seen_rules = set()
    for probe in ("R", ".", "GIVE UP", "RR", "A", "", "\n\n", "R\nL", None,
                  "I give up."):
        seen_rules.add(read_answer(probe).rule)
    ok &= _say(seen_rules <= set(Reading.RULES),
               "R1: every rule that FIRED is a rule the grammar DECLARES "
               "(%d of %d exercised)" % (len(seen_rules), len(Reading.RULES)),
               sorted(seen_rules - set(Reading.RULES)))

    # [3] the oracle
    print("\n[3] the oracle, and what a correct run looks like")
    res = run_entrant(ReferenceSolver(), levels, budget=budget)
    rnd = res["round"]
    ok &= _say(rnd["wins"] == 4, "ORACLE: the reference solver wins the 4 "
                                 "winnable levels", rnd["wins"])
    ok &= _say(rnd["items"]["04_the_only_door.txt"]["give_up"] == 1,
               "ORACLE: on the PROVEN-LOST level the reference solver ABSTAINS, "
               "and that is scored behaviour, not a failure")
    ok &= _say(rnd["items"]["04_the_only_door.txt"]["solved"] is False,
               "ORACLE: 04 is not solved by anything, by construction of the "
               "proof, so 4/5 is a ceiling and the record says so")
    for name in LEVEL_FILES:
        it = rnd["items"][name]
        r = digdug_solve.verify_level(levels[name], budget=budget)
        if r["winnable"]:
            ok &= _say(it["solved"] and it["moves"] == r["proven_optimal"],
                       "ORACLE: %s solved in exactly %d plies (the proven "
                       "optimum)" % (name, r["proven_optimal"]),
                       (it["solved"], it["moves"]))

    # [4] B1: emitted and consumed are two numbers, and the identity between
    # them is checked rather than asserted
    print("\n[4] B1 -- emitted and consumed, and the identity that ties them")
    wb = run_entrant(WallBumper(), levels, budget=budget)["round"]
    ident = all(it["attempted_emitted"]
                == it["attempted_consumed"] + it["after_end"] + it["over_budget"]
                for r in (wb,) for it in r["items"].values())
    ok &= _say(ident,
               "B1: for EVERY item of every run, emitted == consumed + "
               "after_end + over_budget.  That is the whole content of the two "
               "numbers: they differ by exactly the answers the rules refused to "
               "act on, and the record keeps them apart instead of calling one "
               "'attempts'.")
    ok &= _say(wb["totals"]["attempted_emitted"] == wb["totals"]["attempted_consumed"],
               "B1, and the uncomfortable half: on THIS harness the two totals "
               "are EQUAL (%d/%d), because the runner stops asking a level the "
               "moment the attempt ends, so `after_end` and `over_budget` can "
               "never fire in a driven run.  The divergence is therefore NOT a "
               "finding about the entrants; it is a limit of the runner, proven "
               "to exist in digdug.py --self-test [4] (emitted 2 / consumed 1 / "
               "after_end 1) and reported here as out of reach of a model run."
               % (wb["totals"]["attempted_emitted"],
                  wb["totals"]["attempted_consumed"]))
    ok &= _say(wb["totals"]["moves"] <= 1 and wb["totals"]["blocked"] > 10,
               "COUNTERS: a wall-bumper spends %d answers and %d of them are "
               "blocked, buying %d turn of ground -- and it is not 0 turns, "
               "because 04 has ONE diggable cell next to the start (`_`), which "
               "the record shows instead of a comment claiming purity"
               % (wb["totals"]["attempted_emitted"], wb["totals"]["blocked"],
                  wb["totals"]["moves"]),
               wb["totals"])
    ok &= _say(wb["wins"] == 0,
               "COUNTERS: 43 answers, 0 levels solved -- an answer count is never "
               "a progress claim, and this row is the control that says so")
    ok &= _say(wb["totals"]["blocked"] > 0,
               "COUNTERS: blocked is counted where it happened, in the "
               "transition function, not by the level file")

    # [5] THE TWO FACETS, on the same trace
    print("\n[F] the two facets, read off one trace")
    sp = run_entrant(StaticPlanner(), levels, budget=budget)["round"]
    sp_items = sp["items"]
    tot_f1 = sp["facets"]["F1_search_under_destruction"]
    ok &= _say(tot_f1["mobility_shrink_events"] == 0,
               "F1: static-planner never removes a traversable cell -- the "
               "player's mobility is monotone under these rules, so 'the ground "
               "it needed' was never a cell (4F1)", tot_f1)
    ok &= _say(tot_f1["plies_negative_balance"] > 0
               or tot_f1["plies_objective_lost_while_mobile"] > 0,
               "F1: and yet the run shows plies where the dig cost more than it "
               "bought, or the objective went while the map stayed open -- which "
               "is the destruction, measured", tot_f1)
    ok &= _say(sp["facets"]["F2_hazard_aware_planning"] is not None,
               "F2: the SAME plies are read again for the hazard's road; no "
               "second run was made")
    bl = run_entrant(Beeline(), levels, budget=budget)["round"]
    f2 = bl["facets"]["F2_hazard_aware_planning"]
    ok &= _say(f2["arming_plies"] > 0,
               "F2: the beeline opened a hazard's road on %d ply(ies), first at "
               "ply %s" % (f2["arming_plies"], f2["first_arming_ply"]), f2)
    ok &= _say(f2["deaths_armed_by_own_dig"] > 0,
               "F2: and the run(s) died with a route the player itself had dug",
               f2)
    ref_f1 = rnd["facets"]["F1_search_under_destruction"]
    ok &= _say(ref_f1["mobility_shrink_events"] == 0,
               "F1: the oracle's trace shows the same monotonicity, so the "
               "measure is a property of the rules and not of one entrant")

    # [6] the zero rule and never-started
    print("\n[6] the zero rule, and never-started kept separate")
    g1 = run_entrant(Garbage(), levels, budget=3)
    ok &= _say(g1["exit_code"] == EXIT_ZERO_MEASURED
               and g1["round"]["coverage"] == 1.0,
               "ZERO RULE: an all-unreadable run is an ERROR at coverage 1.000",
               (g1["exit_code"], g1["round"]["coverage"]))
    sr = run_entrant(SoftResigner(), levels, budget=3)
    ok &= _say(sr["round"]["totals"]["give_up"] == 0
               and sr["round"]["totals"]["not_an_action"] > 0
               and sr["exit_code"] == EXIT_ZERO_MEASURED,
               "READER [R1]: a natural abstention ('I give up, ...') is scored "
               "not_an_action and the run reports ZERO MEASURED. This is the "
               "instrument's finding about itself, filed as such.",
               sr["round"]["totals"])
    pe = run_entrant(PlanEmitter(), levels, budget=3)
    pe02 = pe["round"]["items"]["02_the_shortcut.txt"]
    pe01 = pe["round"]["items"]["01_first_dig.txt"]
    ok &= _say(pe02["solved"] is False and pe02["not_an_action"] == 1,
               "R3: on 02 the entrant emits the PROVEN OPTIMAL PLAN, `URLDDRR`, "
               "which is the correct answer to the level and is scored "
               "not_an_action -- the reading in which the correct answer is a "
               "failure, recorded as a disproof of that reading rather than "
               "hidden in a document", pe02["not_an_action"])
    ok &= _say(pe01["solved"] is True,
               "R3, and the part that makes this a finding rather than a gripe: "
               "the SAME entrant SOLVES 01 with the same behaviour, because 01's "
               "optimum is ONE letter.  Nothing about the entrant changed; the "
               "grammar's arbitrary boundary between 'an answer' and 'not an "
               "answer' is the whole difference, and it is a property of the "
               "spec, not of the model", (pe01["solved"], pe02["solved"]))
    ns = run_entrant(NeverStarts(), levels)
    ok &= _say(ns["exit_code"] == EXIT_NEVER_STARTED
               and ns["round"]["never_started"] == len(LEVEL_FILES),
               "NEVER-STARTED is counted SEPARATELY from played-and-failed",
               (ns["exit_code"], ns["round"]["never_started"]))
    ok &= _say(ns["admission"]["holder"] is not None
               or (ns["admission"]["holder"] or {}).get("note")
               or "holder" in (ns["admission"]["holder"] or {}),
               "HOLDER: the failed load names the holder or says which probe "
               "found nobody", ns["admission"]["holder"])
    wt = run_entrant(Waiter(), levels, budget=budget)
    ok &= _say(wt["round"]["totals"]["waited"] > 0,
               "D-STOP: WAIT is CONSUMED as a legal action %d times -- it is not "
               "a no-op the harness swallows" % wt["round"]["totals"]["waited"])
    ok &= _say(any(it["terminal"] == "KILLED_BY_HAZARD"
                   for it in wt["round"]["items"].values()),
               "D-STOP: and stopping IS a turn: the waiter dies on the level "
               "where a hazard already has a road",
               {k: v["terminal"] for k, v in wt["round"]["items"].items()})
    rs = run_entrant(Resigner(), levels, budget=budget)
    ok &= _say(rs["exit_code"] == EXIT_SCORED
               and rs["round"]["totals"]["give_up"] == len(LEVEL_FILES)
               and rs["round"]["score"] == 0.0,
               "R1: abstention on every level is SCORED (0.000), not an error -- "
               "a legal answer that ends the attempt",
               (rs["exit_code"], rs["round"]["score"]))
    sm = run_entrant(SlackMaximiser(), levels, budget=budget)["round"]
    ok &= _say(sm["score"] == rnd["score"]
               and sm["totals"]["moves"] >= rnd["totals"]["moves"],
               "R2: the slack-maximiser and the oracle score IDENTICALLY (%s) and "
               "the cost is carried beside it (%d moves versus %d), never folded "
               "into the score -- solved is the score, moves is the cost"
               % (sm["score"], sm["totals"]["moves"], rnd["totals"]["moves"]),
               (sm["score"], sm["totals"]["moves"], rnd["totals"]["moves"]))
    same_line = (sm["items"]["03_ground_you_cannot_reuse.txt"]["digs_by_word_vs_delta"]
                 is not None)
    ok &= _say(sm["totals"]["moves"] == rnd["totals"]["moves"],
               "R2, and the finding that costs this cabinet something: caution was "
               "FREE on this item set.  The entrant that maximises its margin found "
               "a line of the SAME length (%d = %d) -- it picks a different optimal "
               "line on 03, but it never pays in turns.  So this set cannot price "
               "caution, and a table built from it must not claim that the two "
               "entrants trade score against cost.  A gap in the LEVELS, reported "
               "as one" % (sm["totals"]["moves"], rnd["totals"]["moves"]),
               (sm["totals"]["moves"], rnd["totals"]["moves"]))

    # [7] bundle shape, provenance, declared fields
    print("\n[7] the bundle: shape, provenance, declarations")
    bundle = build_bundle("reference", res, levels, reasoning=reasoning,
                          frozen=detail)
    ent = bundle["results"][0]
    ent["certification"] = ("INSTRUMENT CHECK -- the solver-as-entrant path; "
                            "proves the harness and ENTERS NOTHING.")
    ent["on_board"] = False
    ent["entrant"] = "instrument-check"
    ent["is_harness_proof"] = True
    for key in ("harness", "version", "event", "card_version", "results",
                "declared", "frozen_contract"):
        ok &= _say(key in bundle, "BUNDLE SHAPE: has %r" % key, sorted(bundle))
    for key in ("tasks", "decisions", "section_4f", "instrument", "admission",
                "rounds", "grammar", "verdict_code", "weights", "hardware",
                "levels", "contract", "rules_fired", "exit_code_table"):
        ok &= _say(key in ent, "BUNDLE SHAPE: result carries %r" % key,
                   sorted(ent))
    ok &= _say(all(k in rnd for k in ("score", "wins", "trials",
                                      "items_attempted_emitted",
                                      "items_attempted_consumed", "started",
                                      "readable", "never_started", "coverage",
                                      "facets")),
               "BUNDLE SHAPE: the round carries the full count set and BOTH "
               "facets", sorted(rnd))
    ok &= _say(ent["rules_subset_ok"],
               "R1: every rule name that fired in the run is declared in the "
               "grammar", ent["rules_fired"])
    ok &= _say(bundle["declared"]["reasoning"] in ("on", "off", "unset")
               and "probe" in bundle["declared"]["gpu"],
               "DECLARED: reasoning and the GPU-with-its-probe are at the TOP of "
               "the record")
    ok &= _say(ent["verdict_code"]["sha256"]
               == _sha256_of(os.path.join(HERE, "digdug_run.py")),
               "PROVENANCE: the bundle carries the digest of the code that "
               "produced the verdict")
    ok &= _say(ent["verdict_code"]["solver"]["sha256"]
               == _sha256_of(os.path.join(HERE, "digdug_solve.py")),
               "PROVENANCE: and the digest of the code that proved the optima")
    ok &= _say(ent["verdict_code"]["reader"]["sha256"] == reader_sha256(),
               "PROVENANCE: and the reader's")
    ok &= _say(grammar_as_record()["give_up_tokens"] == list(GIVE_UP_TOKENS),
               "R1: the bundle carries the abstention list it was actually "
               "scored with")
    if out_dir:
        p = write_bundle(bundle, out_dir, "instrument-check")
        print("wrote %s" % p)
    print()
    print("INSTRUMENT CHECK %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else EXIT_INSTRUMENT


def digdug_readings_available():
    try:
        import digdug_readings                                    # noqa: F401
        return True
    except Exception:                                             # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# 10. SUBCOMMANDS
# ---------------------------------------------------------------------------

class _Args(object):
    """Minimal stand-in so the controls can drive cmd_run in process."""

    def __init__(self, entrant, out=None, reasoning="unset", budget=None,
                 retries=None, model_path=None, server_url=None, max_tokens=8,
                 temperature=0.0, manifest=None):
        self.manifest = manifest
        self.entrant = entrant
        self.out = out
        self.reasoning = reasoning
        self.budget = budget
        self.retries = retries
        self.model_path = model_path
        self.server_url = server_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.skip_freeze = False


def cmd_run(args):
    name = args.entrant
    if name not in ENTRANTS:
        print("unknown entrant %r; try one of: %s"
              % (name, ", ".join(sorted(ENTRANTS))))
        return EXIT_USAGE
    # THE FREEZE GATE.  Before an entrant is handed a single prompt.  `--manifest`
    # exists so the gate itself can be audited against a named manifest instead of
    # the one on disk -- and so this control can prove the gate closes without
    # editing anything real.
    frozen_ok, detail = freeze_state(getattr(args, "manifest", None))
    if not frozen_ok and not getattr(args, "skip_freeze", False):
        print("REFUSING TO RUN %r -- the contract is not frozen against disk.\n"
              "  %s" % (name, detail.get("note")))
        print("  This is not a warning. An entrant scored against an unfrozen "
              "or drifted contract has no measurement to be scored on.")
        return EXIT_NOT_FROZEN
    ent_cls = ENTRANTS[name]
    if name == "model":
        ent = ent_cls(args.model_path, args.server_url or "http://127.0.0.1:8080")
    elif name in ("wall-bumper", "liar", "waiter"):
        ent = ent_cls()
    else:
        try:
            ent = ent_cls()
        except TypeError:
            ent = ent_cls(None)
    levels = digdug.load_level_set()
    result = run_entrant(
        ent, levels, budget=args.budget or DEFAULT_ATTEMPT_BUDGET,
        retries=args.retries if args.retries is not None else DEFAULT_RETRIES,
        max_tokens=args.max_tokens, temperature=args.temperature)
    bundle = build_bundle(name, result, levels, reasoning=args.reasoning,
                          frozen=detail,
                          config_extra={"budget": args.budget,
                                        "retries": args.retries,
                                        "max_tokens": args.max_tokens,
                                        "temperature": args.temperature})
    out_dir = args.out or os.path.join(HERE, "results")
    # THE RECORD, WRITTEN BEFORE THE BRANCH.  Everything below decides only the
    # exit code; the file already exists whatever comes out of it.
    try:
        path = write_bundle(bundle, out_dir, name)
    except OSError as exc:
        print("RECORD NOT WRITTEN: %r -- and a run with no record is not a run"
              % (exc,))
        return EXIT_WRITE_FAILED
    rnd = result["round"]
    print("%s / %s  (written before the verdict branch)" % (EVENT, name))
    print("  score=%s (solved %d / emitted %d)  cost moves=%d  coverage=%s"
          % (rnd["score"], rnd["wins"], rnd["items_attempted_emitted"],
             rnd["totals"]["moves"], rnd["coverage"]))
    print("  emitted=%d consumed=%d blocked=%d not_an_action=%d give_up=%d "
          "after_end=%d"
          % (rnd["totals"]["attempted_emitted"],
             rnd["totals"]["attempted_consumed"], rnd["totals"]["blocked"],
             rnd["totals"]["not_an_action"], rnd["totals"]["give_up"],
             rnd["totals"]["after_end"]))
    print("  reasoning=%s  gpu=%s (probe: %s)"
          % (args.reasoning,
             (bundle["declared"]["gpu"].get("name")
              or "null -- no accelerator found"),
             bundle["declared"]["gpu"].get("probe")))
    for name_l in LEVEL_FILES:
        it = rnd["items"][name_l]
        f1 = it["facets"]["F1_search_under_destruction"]
        f2 = it["facets"]["F2_hazard_aware_planning"]
        print("     %-32s %-26s mv=%-2d at=%-2d ac=%-2d blk=%-2d na=%-2d "
              "| F1 lost/mobile %-2d | F2 armed@%-3s died=%s"
              % (name_l, it["terminal"], it["moves"], it["attempted_consumed"],
                 it["digs"], it["blocked"], it["not_an_action"],
                 f1["plies_objective_lost_while_mobile"],
                 f2["first_arming_ply"], bool(it["killed_at"])))
    print("  -> %s" % path)
    return result["exit_code"]


def cmd_levels(args):
    levels = digdug.load_level_set()
    ok, rows = digdug_solve.verify_levels(levels, budget=args.budget
                                          or DEFAULT_ATTEMPT_BUDGET)
    for r in rows:
        if "error" in r:
            print("  %-32s NOT PROVEN -- %s" % (r["level"], r["error"]))
            continue
        print("  %-32s opt %-3s plans %-2s %-11s %6d states  plan %s  sha %s"
              % (r["level"], r["proven_optimal"], r["distinct_shortest_plans"],
                 r["proof_grade"], r["n_states_explored"], r["shortest_plan"],
                 r["sha256"][:16]))
        print("       %s" % r["loss_claim"])
    print()
    print("LEVEL VERIFICATION %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else EXIT_INSTRUMENT


def cmd_exit_codes(args):
    for code in sorted(EXIT_CODES):
        print("  %d  %s" % (code, EXIT_CODES[code]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="digdug_run.py",
        description="DIG DUG runner/scorer -- the Tier-3 cabinet")
    sub = ap.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="run one entrant")
    p_run.add_argument("--entrant", required=True, choices=sorted(ENTRANTS))
    p_run.add_argument("--out", default=None)
    p_run.add_argument("--reasoning", choices=("on", "off", "unset"),
                       default="unset",
                       help="DECLARED per-run instrument field; 'unset' is NOT "
                            "'off'")
    p_run.add_argument("--budget", type=int, default=None)
    p_run.add_argument("--retries", type=int, default=None)
    p_run.add_argument("--model-path", default=None)
    p_run.add_argument("--server-url", default=None)
    p_run.add_argument("--max-tokens", type=int, default=8)
    p_run.add_argument("--temperature", type=float, default=0.0)
    p_run.add_argument("--manifest", default=None,
                       help="audit against this frozen manifest instead of "
                            "CONTRACT_frozen.json")

    p_all = sub.add_parser("run-all", help="the whole field, ONE declared "
                                           "instrument setting")
    p_all.add_argument("--reasoning", choices=("on", "off", "unset"),
                       default="off")
    p_all.add_argument("--out", default=None)
    p_all.add_argument("--budget", type=int, default=None)

    p_ic = sub.add_parser("instrument-check", help="prove the harness")
    p_ic.add_argument("--out", default=None)
    p_ic.add_argument("--reasoning", choices=("on", "off", "unset"),
                      default="unset")
    p_ic.add_argument("--budget", type=int, default=None)
    sub.add_parser("levels", help="verify the optima by exhaustive search")
    p_tk = sub.add_parser("tasks", help="write the item set from the solver")
    p_tk.add_argument("--budget", type=int, default=None)
    sub.add_parser("freeze", help="freeze the contract: digests of doc, code, "
                                  "levels")
    sub.add_parser("freeze-check", help="recompute the digests; exit 1 on "
                                        "drift")
    sub.add_parser("exit-codes", help="print the exit code table")
    sub.add_parser("verify", help="replay every bundle from the record")
    p_rd = sub.add_parser("readings", help="SECTION 4F: the shadow table -- the "
                                           "rejected readings, measured")
    p_rd.add_argument("--depth", type=int, default=digdug_solve.HORIZON)

    args = ap.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "instrument-check":
        return instrument_check(args.out, reasoning=args.reasoning,
                                budget=args.budget)
    if args.cmd == "levels":
        return cmd_levels(args)
    if args.cmd == "tasks":
        return cmd_tasks(args)
    if args.cmd == "freeze":
        return cmd_freeze(args)
    if args.cmd == "freeze-check":
        ok, detail = freeze_state()
        print("FREEZE CHECK %s" % ("PASSED" if ok else "FAILED"))
        for k, v in sorted(detail["files"].items()):
            print("  %-40s %s" % (k, "match" if v["match"] else "DRIFT"))
        if not ok:
            print("  %s" % detail.get("note"))
        return 0 if ok else EXIT_INSTRUMENT
    if args.cmd == "verify":
        import test_digdug
        return 0 if test_digdug.verify_all() else EXIT_INSTRUMENT
    if args.cmd == "readings":
        import digdug_readings
        return digdug_readings.main(args)
    if args.cmd == "exit-codes":
        return cmd_exit_codes(args)
    if args.cmd == "run-all":
        codes = {}
        for n in sorted(ENTRANTS):
            if n == "model":
                continue                 # needs --model-path and a server
            codes[n] = cmd_run(_Args(n, args.out, args.reasoning, args.budget))
            print("  exit %d\n" % codes[n])
        print("  -- field summary (one declared instrument setting, %s)"
              % args.reasoning)
        for n in sorted(codes):
            print("     %-16s exit %d  %s" % (n, codes[n],
                                              EXIT_CODES[codes[n]]))
        # NOT a constant.  A non-zero here means a record was not written, and a
        # run with no record is not a run.
        bad = [n for n, c in codes.items() if c == EXIT_WRITE_FAILED]
        if bad:
            print("  RECORDS NOT WRITTEN for: %s" % ", ".join(bad))
            return EXIT_WRITE_FAILED
        return EXIT_SCORED
    ap.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
