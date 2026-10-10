#!/usr/bin/env python3
# digdug_run.py -- THE RUNNER and THE SCORER for the DIG DUG cabinet.
#
#   * it gives the task (build_prompt, from the simulator -- never built here)
#   * it collects the answer
#   * IT CHECKS THE ANSWER BY EXECUTING IT (feed -> step -> turn) -- never by
#     reading it and comparing it to a solution string [A16]
#   * IT REFUSES TO RUN AT ALL unless the contract is the frozen one
#     (freeze.verify()), and that refusal has its own exit code
#   * IT WRITES THE RECORD TO DISK BEFORE THE SUCCESS/FAILURE BRANCH
#   * it records the model file's DIGEST, or states in writing why there is none
#   * it records WHICH CODE produced the verdict, by digest
#   * it records the REASONING SETTING and the GPU, per run
#   * a failed load NAMES THE HOLDER, never "failed to load"
#   * BOTH FACETS are read off the SAME trace, and the record says which
#     facet each number belongs to
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
import urllib.error
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug                                              # noqa: E402
import digdug_reader                                       # noqa: E402
import digdug_solve                                        # noqa: E402
import freeze                                              # noqa: E402
from digdug import (Attempt, DELTA, DIRECTION_ORDER, State,  # noqa: E402
                    build_prompt, check_prompt_legal, find_level,
                    hazard_component, min_moves_to_complete)

HARNESS = "handicap-arena"
VERSION = "1.0"
EVENT = "DIG DUG"
CARD_VERSION = "digdug_v1"
TASKS = os.path.join(HERE, "tasks", "digdug_v1.json")

#: [A14] DECLARED instrument parameter, in every bundle.
DEFAULT_BUDGET = 30
DEFAULT_REASONING = "unset"

# ---------------------------------------------------------------------------
# EXIT CODES -- declared, printed, and exercised by the self-test.
#
# The defect this table exists for: a CLI that returned 1 for EVERY real
# invocation while its self-test reported all green, because the self-test
# never reached the code path that raised.  So every code below is produced by
# a path the self-test actually calls.
# ---------------------------------------------------------------------------
EXIT_SCORED = 0            # measured > 0 and the harness is sound
EXIT_INSTRUMENT = 1        # the INSTRUMENT is not proven -- self-test,
                           # instrument-check or level verification failed.
                           # RESERVED: no entrant's run can produce it.
EXIT_ZERO_MEASURED = 2     # ZERO RULE: a run with no measured entrant is an
                           # ERROR, never a verdict
EXIT_USAGE = 3             # unknown entrant, bad arguments
EXIT_NEVER_STARTED = 4     # the entrant never loaded -- counted separately
                           # from played-and-failed, because they are
                           # different claims
EXIT_WRITE_FAILED = 5      # the record could not be written.  A run with no
                           # record is not a run.
EXIT_NOT_FROZEN = 6        # the contract on disk is not the frozen contract.
                           # No entrant runs against an unfrozen spec.

EXIT_CODES = {
    EXIT_SCORED: "SCORED -- measured > 0, harness sound",
    EXIT_INSTRUMENT: "INSTRUMENT NOT PROVEN -- self-test / instrument-check / "
                     "level verification failed (RESERVED: no entrant's run "
                     "produces it)",
    EXIT_ZERO_MEASURED: "ZERO MEASURED -- ERROR, never a verdict",
    EXIT_USAGE: "USAGE -- unknown entrant or bad arguments",
    EXIT_NEVER_STARTED: "ENTRANT NEVER STARTED -- counted separately from "
                        "played-and-failed",
    EXIT_WRITE_FAILED: "RECORD NOT WRITTEN -- a run with no record is not "
                       "a run",
    EXIT_NOT_FROZEN: "NOT FROZEN -- the contract on disk is not the frozen "
                     "contract; no entrant ran",
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


def _holders_for_path(path):
    out = []
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return out
    try:
        real = os.path.realpath(path)
    except OSError:
        real = path
    for pid in pids:
        fd_dir = "/proc/%s/fd" % pid
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            try:
                tgt = os.readlink(os.path.join(fd_dir, fd))
            except OSError:
                continue
            if tgt == real or tgt == path:
                out.append({"pid": int(pid), "comm": _proc_comm(pid),
                            "cmdline": _proc_cmdline(pid),
                            "probe": "/proc/%s/fd -> %s" % (pid, tgt)})
    return out


def _holders_for_port(port):
    """Who is listening on this port, by reading /proc/net/tcp{,6}."""
    out = []
    want = set()
    for fam, fn in (("tcp", "/proc/net/tcp"), ("tcp6", "/proc/net/tcp6")):
        try:
            with open(fn) as fh:
                lines = fh.read().splitlines()[1:]
        except OSError:
            continue
        for ln in lines:
            parts = ln.split()
            if len(parts) < 10 or parts[3] != "0A":       # 0A == LISTEN
                continue
            local = parts[1]
            try:
                lport = int(local.split(":")[1], 16)
            except (IndexError, ValueError):
                continue
            if lport == port:
                want.add((fam, parts[9]))                 # inode
    if not want:
        return out
    inodes = {w[1] for w in want}
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return [{"inode": i, "probe": "/proc/net/tcp (LISTEN)",
                 "comm": None, "note": "listening, but no /proc fd match"}
                for i in inodes]
    for pid in pids:
        fd_dir = "/proc/%s/fd" % pid
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            try:
                tgt = os.readlink(os.path.join(fd_dir, fd))
            except OSError:
                continue
            if tgt.startswith("socket:[") and tgt[8:-1] in inodes:
                out.append({"pid": int(pid), "comm": _proc_comm(pid),
                            "cmdline": _proc_cmdline(pid),
                            "socket": tgt,
                            "probe": "/proc/net/tcp LISTEN + /proc/%s/fd" % pid})
    return out


def probe_holder(resource, kind="port"):
    """-> dict naming the holder, or saying which probe found nobody.

    "failed to load" is not a diagnosis.  Either something else has the
    resource and this names it, or nothing does and this says which probe
    looked and found nobody.
    """
    holders = (_holders_for_port(resource) if kind == "port"
               else _holders_for_path(resource))
    return {
        "resource": resource,
        "kind": kind,
        "probe": ("/proc/net/tcp{,6} LISTEN + /proc/<pid>/fd"
                  if kind == "port" else "/proc/<pid>/fd"),
        "holders": holders,
        "named": bool(holders),
        "note": (None if holders else
                 "no holder found by %s -- nothing is holding it"
                 % ("/proc/net/tcp" if kind == "port" else "/proc/<pid>/fd")),
    }


# ---------------------------------------------------------------------------
# 2. THE GPU -- declared per run, with the probe that established it
# ---------------------------------------------------------------------------

def probe_gpu():
    """No accelerator is null WITH THE PROBE THAT RAN.  Never 0.00, never
    "none": an unprobed machine is not a machine with no GPU."""
    probe = "nvidia-smi"
    try:
        out = subprocess.run(["nvidia-smi",
                              "--query-gpu=index,name,memory.total,"
                              "memory.free,driver_version",
                              "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=15)
        if out.returncode == 0 and out.stdout.strip():
            rows = [r.split(", ") for r in out.stdout.strip().splitlines()]
            g = rows[0]
            return {"probe": "%s -> ran, %d device(s)" % (probe, len(rows)),
                    "name": g[1] if len(g) > 1 else None,
                    "index": g[0] if g else None,
                    "memory_total_gb": None, "memory_free_gb": None,
                    "driver": g[4] if len(g) > 4 else None,
                    "n_devices": len(rows), "raw": out.stdout.strip(),
                    "note": None}
        probe = "%s -> absent (exit %s)" % (probe, out.returncode)
    except (OSError, subprocess.SubprocessError) as exc:
        probe = "nvidia-smi -> not runnable: %s" % exc.__class__.__name__
    return {"probe": probe, "name": None, "index": None,
            "memory_total_gb": None, "memory_free_gb": None, "driver": None,
            "n_devices": None, "raw": None,
            "note": "NO ACCELERATOR FOUND by this probe.  This is null, not "
                    "0.00 and not 'none': the host was probed and the probe "
                    "found nothing."}


def host_block():
    return {"python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "hostname": platform.node()}


# ---------------------------------------------------------------------------
# 3. THE ENTRANTS
#
# Every entrant below is a CODE entrant except `model`.  A code entrant is a
# DIFFERENT INSTRUMENT and is never pooled into a model table; each one is a
# different shape of failure the cabinet has to classify correctly.
# ---------------------------------------------------------------------------

class Entrant(object):
    name = "entrant"
    kind = "code"
    instrument = "code"
    entrant_is_a_model = False

    def reset(self, level, budget):
        pass

    def answer(self, view):
        raise NotImplementedError


def _legal_moves(view):
    """The moves the board offers, in DIRECTION_ORDER."""
    lvl, st = view["level"], view["state"]
    out = []
    r, c = st.player
    for d in DIRECTION_ORDER:
        dr, dc = DELTA[d]
        n = (r + dr, c + dc)
        if 0 <= n[0] < lvl.height and 0 <= n[1] < lvl.width \
                and n not in lvl.walls:
            out.append((d, n))
    return out


def _dist_field(level, src, passable):
    from collections import deque
    dist = {src: 0}
    q = deque((src,))
    while q:
        cur = q.popleft()
        r, c = cur
        for d in DIRECTION_ORDER:
            dr, dc = DELTA[d]
            n = (r + dr, c + dc)
            if n in passable and n not in dist:
                dist[n] = dist[cur] + 1
                q.append(n)
    return dist


class ReferenceSolver(Entrant):
    """The optimal safe line, by complete search under the frozen contract.

    Not a model and not on the board: it is the yardstick the instrument is
    checked against, and it proves the levels are solvable at all.
    """
    name = "reference"
    kind = "reference-solver"

    def __init__(self):
        self.search = digdug_solve.Search()

    def answer(self, view):
        st, budget = view["state"], view["budget"]
        h = min_moves_to_complete(st)
        if h is None:
            return "UNSOLVABLE"
        left = budget - st.turn
        for limit in range(max(h, 1), left + 1):
            for a in digdug.ACTIONS:
                from digdug import turn
                s2, _w, _e = turn(st, a)
                if s2.dead:
                    continue
                if s2.solved:
                    return a
                n, _nodes, complete = self.search.count_lines(
                    s2, limit - 1)
                if complete and n:
                    return a
        return "UNSOLVABLE"


class _StaticPlannerBase(Entrant):
    """Shared machinery: plan on a map, walk the plan."""

    def _plan_on(self, level, src, passable, targets):
        """BFS shortest path over a FIXED passable set.  Returns a list of
        action letters."""
        from collections import deque
        goal = sorted(targets)[0]
        prev = {src: None}
        q = deque((src,))
        while q:
            cur = q.popleft()
            if cur == goal:
                break
            r, c = cur
            for d in DIRECTION_ORDER:
                dr, dc = DELTA[d]
                n = (r + dr, c + dc)
                if n in passable and n not in prev:
                    prev[n] = (cur, d)
                    q.append(n)
        if goal not in prev:
            return []
        acts = []
        cur = goal
        while prev[cur] is not None:
            acts.append(prev[cur][1])
            cur = prev[cur][0]
        return list(reversed(acts))


class StaticPlanner(_StaticPlannerBase):
    """THE FACULTY'S TARGET.  Plans ONCE, at t=0, on the map it was shown,
    and then executes that plan blindly -- no re-planning, no account of what
    its own digging has done to the board.

    This is the entrant the cabinet exists to expose: a model that plans a
    route and then discovers the plan consumed the ground it needed.
    """
    name = "static-planner"
    kind = "hazard-blind-static-plan"

    def reset(self, level, budget):
        self.level = level
        self.plan = self._plan_on(level, level.player_start, level.playable,
                                  level.targets)
        self.i = 0
        self.last = "R"

    def answer(self, view):
        if self.i < len(self.plan):
            a = self.plan[self.i]
            self.i += 1
            self.last = a
            return a
        return self.last


class HazardBlind(_StaticPlannerBase):
    """Re-plans every turn -- but on a map with no hazards in it.  It knows
    the ground; it does not know what the ground has become."""
    name = "hazard-blind"
    kind = "hazard-blind-replanning"

    def answer(self, view):
        st, lvl = view["state"], view["level"]
        plan = self._plan_on(lvl, st.player, lvl.playable, st.targets_left)
        return plan[0] if plan else "UNSOLVABLE"


class Survivor(Entrant):
    """Never digs the ground that would let a hazard in; otherwise walks away
    from it.  It survives and it does not solve, which is the control that
    proves `solved` is the score and survival is not (standing rule R2)."""
    name = "survivor"
    kind = "survival-only"

    def answer(self, view):
        from digdug import turn
        st = view["state"]
        best, best_score = None, None
        for d in DIRECTION_ORDER:
            s2, w, _e = turn(st, d)
            if s2.dead:
                continue
            comp = hazard_component(s2.level, s2.tunnels, s2.player)
            merged = any(h in comp for h in s2.hazards)
            # never merge if a non-merging move exists; otherwise maximise the
            # tunnel distance to the nearest hazard
            dists, plain = [], []
            for h in s2.hazards:
                dd = _dist_field(s2.level, h, s2.tunnels).get(s2.player)
                # an unconnected hazard is infinitely far, and "infinitely
                # far" must not TIE every legal move or the policy collapses
                # onto the first direction and bumps a wall for 30 turns --
                # which is what the first build did, measurably.
                dists.append(dd if dd is not None else 10 ** 6)
                plain.append(_dist_field(s2.level, h, s2.level.playable)
                             .get(s2.player, 0))
            score = ((0 if merged else 1),
                     min(dists) if dists else 10 ** 6,
                     min(plain) if plain else 0)
            if best_score is None or score > best_score:
                best, best_score = d, score
        return best if best else "UNSOLVABLE"


class RingRunner(Entrant):
    """OPENS THE DOOR ON PURPOSE, THEN RUNS.

    It digs the one cell that connects the hazard's pocket to the player's
    ground -- irreversibly destroying the last safe line -- and then flees
    around the ring for the rest of the budget.  Facet 1 fires and facet 2
    does not: the map is ruined and the entrant is still alive.
    """
    name = "ring-runner"
    kind = "burns-the-barrier-then-flees"

    def answer(self, view):
        from digdug import turn
        st = view["state"]
        if st.turn < 3:
            return "R"                       # open the door
        best, best_score = None, None
        for d in DIRECTION_ORDER:
            s2, w, _e = turn(st, d)
            if s2.dead:
                continue
            dists = []
            for h in s2.hazards:
                dd = _dist_field(s2.level, h, s2.tunnels).get(s2.player)
                dists.append(dd if dd is not None else 999)
            score = min(dists) if dists else 999
            if best_score is None or score > best_score:
                best, best_score = d, score
        return best if best else "UNSOLVABLE"


class Wanderer(Entrant):
    """Digs ground that does not help, until there are not enough turns left
    to finish.  Facet 1b -- and it needs no hazard to fail."""
    name = "wanderer"
    kind = "burns-the-budget"

    def reset(self, level, budget):
        self.seen = {level.player_start}

    def answer(self, view):
        st, lvl = view["level"], view["state"]
        lvl = view["level"]
        moves = _legal_moves(view)
        fresh = [(d, n) for d, n in moves if n not in self.seen]
        pick = fresh[0] if fresh else (moves[0] if moves else None)
        if pick is None:
            return "UNSOLVABLE"
        self.seen.add(pick[1])
        return pick[0]


class WallBumper(Entrant):
    """The dossier's classic control: 30 attempts, 30 blocked, nothing dug,
    nothing solved.  A counter that reported attempts as moves would call
    this a long, active game."""
    name = "wall-bumper"
    kind = "control-wall-bumper"

    def answer(self, view):
        return "U"


class Liar(Entrant):
    """Asserts a plan it knows is wrong: it plays level 01's optimum on every
    level.  The instrument must execute the answer and let the board say no."""
    name = "liar"
    kind = "control-liar"

    def reset(self, level, budget):
        self.plan = list("RRRR")
        self.i = 0

    def answer(self, view):
        if self.i < len(self.plan):
            a = self.plan[self.i]
            self.i += 1
            return a
        return "R"


class Garbage(Entrant):
    """Produces no readable answer at all.  The run must be an ERROR (exit 2),
    never a verdict of 0.00."""
    name = "garbage"
    kind = "control-garbage"
    JUNK = ("hello there", "42", "R R", "{}", "up", "move right please",
            "<<>>", "\n\n", "0x1F")

    def reset(self, level, budget):
        self.i = 0

    def answer(self, view):
        j = self.JUNK[self.i % len(self.JUNK)]
        self.i += 1
        return j


class Resigner(Entrant):
    """Abstains with a token from the FROZEN list, on the first turn."""
    name = "resigner"
    kind = "control-resigner"

    def answer(self, view):
        return "RESIGN"


class SoftResigner(Entrant):
    """Abstains the way a model actually would -- in English.  Under the
    strict rule this is `not_an_action`, and the loose diagnostic sees it.
    The divergence is the finding; the diagnostic is never scored."""
    name = "soft-resigner"
    kind = "control-soft-resigner"

    def answer(self, view):
        return "I give up, there is no way to finish this one."


class NeverStarts(Entrant):
    """Fails to load.  Counted separately from played-and-failed, and the
    record names the holder of whatever it needed."""
    name = "never-starts"
    kind = "control-never-starts"

    def reset(self, level, budget):
        raise RuntimeError("never-starts: this entrant cannot load")

    def answer(self, view):
        raise RuntimeError("unreachable")


class ModelEntrant(Entrant):
    """A model, served by llama.cpp.  Admission is probed before a single
    token is asked for, a failed load NAMES THE HOLDER, and the weights'
    sha256 goes in the record -- or the record says in writing why there is
    none."""
    name = "model"
    kind = "model"
    instrument = "model"
    entrant_is_a_model = True

    def __init__(self, model_path=None, server_url="http://127.0.0.1:8080",
                 max_tokens=8, temperature=0.0, timeout=120):
        self.model_path = model_path
        self.server_url = server_url.rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

    # -- admission ----------------------------------------------------------
    def weights_record(self):
        p = self.model_path
        if not p:
            return {"path": None, "name": None, "sha256": None, "bytes": None,
                    "note": "NO WEIGHTS: no --model-path was given, so there "
                            "is no file to digest.  This is stated rather "
                            "than left empty."}
        if not os.path.isfile(p):
            holder = probe_holder(p, kind="path")
            return {"path": p, "name": os.path.basename(p), "sha256": None,
                    "bytes": None, "holder": holder,
                    "note": "NO DIGEST: the path does not exist on this host, "
                            "so there is nothing to hash.  A digest nobody "
                            "computed is not a digest."}
        return {"path": p, "name": os.path.basename(p),
                "sha256": _sha256_of(p), "bytes": os.path.getsize(p),
                "note": None}

    def admit(self):
        """-> (ok, record).  Probes the port; if nothing serves, NAMES the
        holder or says which probe found nobody."""
        from urllib.parse import urlparse
        port = urlparse(self.server_url).port or 80
        holder = probe_holder(port, kind="port")
        rec = {"server_url": self.server_url, "port": port, "holder": holder,
               "probe": "socket connect to %s" % self.server_url,
               "weights": self.weights_record()}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect((urlparse(self.server_url).hostname or "127.0.0.1",
                       port))
            s.close()
            rec["ok"] = True
            rec["note"] = "something is listening"
            return True, rec
        except OSError as exc:
            rec["ok"] = False
            rec["error"] = "%s: %s" % (exc.__class__.__name__, exc)
            rec["note"] = ("nothing is listening on port %d; %s"
                           % (port, holder["note"]))
            return False, rec

    def answer(self, view):
        body = json.dumps({
            "prompt": view["prompt"],
            "n_predict": self.max_tokens,
            "temperature": self.temperature,
            "stop": ["\n\n", "\nLevel:", "\nThe board now:"],
        }).encode("utf-8")
        req = urllib.request.Request(self.server_url + "/completion",
                                     data=body,
                                     headers={"Content-Type":
                                              "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
        doc = json.loads(raw)
        # A reasoning model can answer in reasoning_content and leave content
        # empty.  Read BOTH and report which one carried the answer.
        content = doc.get("content")
        reasoning = doc.get("reasoning_content")
        view.setdefault("fields_seen", []).append(
            {"content": bool(content), "reasoning_content": bool(reasoning)})
        if content is None or not str(content).strip():
            if reasoning:
                view["answer_field"] = "reasoning_content"
                return str(reasoning)
            return ""
        view["answer_field"] = "content"
        return str(content)


ENTRANTS = {
    "reference": ReferenceSolver,
    "static-planner": StaticPlanner,
    "hazard-blind": HazardBlind,
    "survivor": Survivor,
    "ring-runner": RingRunner,
    "wanderer": Wanderer,
    "wall-bumper": WallBumper,
    "liar": Liar,
    "garbage": Garbage,
    "resigner": Resigner,
    "soft-resigner": SoftResigner,
    "never-starts": NeverStarts,
    "model": ModelEntrant,
}


# ---------------------------------------------------------------------------
# 4. PLAYING A LEVEL
# ---------------------------------------------------------------------------

def play_level(level, entrant, budget, trace_boards=True):
    """One entrant, one level, one turn at a time.  -> the Attempt."""
    a = Attempt(level, budget)
    entrant.reset(level, budget)
    history = []
    while not a.over:
        view = {"level": level, "state": a.state, "budget": budget,
                "history": list(history), "turn": a.state.turn}
        view["prompt"] = build_prompt(level, a.state, history, budget)
        raw = entrant.answer(view)
        ply = a.feed(raw)
        if ply.get("action"):
            history.append(ply["action"])
        if not trace_boards and "board" in ply:
            del ply["board"]
    return a


# ---------------------------------------------------------------------------
# 5. SCORING
# ---------------------------------------------------------------------------

def score_field(items):
    """[A15] THE GATE, standing rule R2: solved IS the score, moves are a
    COST.  The rate at the gate is solved / attempted_emitted, where
    attempted_emitted counts LEVELS on which the entrant emitted at least one
    answer.  The other reading of R2 -- solved per ANSWER -- is recorded
    beside it, because the rule does not say which and the two can rank a
    field differently."""
    scored = [it for it in items.values() if it.get("scored", True)]
    solved = sum(1 for it in scored if it["solved"])
    attempted_emitted = sum(1 for it in scored
                            if it["answers_emitted"] > 0)
    answers_emitted = sum(it["answers_emitted"] for it in scored)
    answers_consumed = sum(it["answers_consumed"] for it in scored)
    return {
        "solved": solved,
        "attempted_emitted": attempted_emitted,
        "score": (solved / attempted_emitted) if attempted_emitted else None,
        "score_is": "solved / attempted_emitted (LEVELS that emitted at least "
                    "one answer) -- standing rule R2 [A15]",
        "alt_reading_solved_per_answer": ((solved / answers_emitted)
                                          if answers_emitted else None),
        "alt_reading_is": "solved / answers_emitted -- the OTHER reading of "
                          "R2, recorded, NOT the gate [A15]",
        "answers_emitted": answers_emitted,
        "answers_consumed": answers_consumed,
        "answers_after_end": sum(it["answers_after_end"]
                                 for it in scored),
        "B1_note": "emitted and consumed are DIFFERENT numbers and both are "
                   "here; tokens emitted after the attempt ended are "
                   "answers_after_end and are not not_an_action",
        "moves_are_a_cost": {
            "dug": sum(it["dug"] for it in scored),
            "moved": sum(it["moved"] for it in scored),
            "blocked": sum(it["blocked"] for it in scored),
            "collected": sum(it["collected"] for it in scored),
            "turns_used": sum(it["turns_used"] for it in scored),
            "averaged": False,
            "why_not_averaged": "a move count is not a rate, and averaging "
                                "counts across levels of different sizes "
                                "produces a number with no denominator",
        },
        "not_an_action": sum(it["not_an_action"] for it in scored),
        "give_up": sum(it["give_up"] for it in scored),
        "readable_answers": sum(it["answers_emitted"] - it["not_an_action"]
                                for it in scored),
    }


def facet_field(items):
    """BOTH FACETS, per level, with the facet named on every number.

    Every number below was read off the SAME trace as every other number for
    that level: the trace digests are compared and the claim is recorded.
    """
    scored = {k: v for k, v in items.items() if v.get("scored", True)}
    digests = {k: v["facets"]["trace_sha256"] for k, v in scored.items()}
    out = {
        "one_trace_per_level": all(
            v["facets"]["facet1_destruction"]["trace_sha256"] ==
            v["facets"]["facet2_hazard_aware"]["trace_sha256"] ==
            v["facets"]["trace_sha256"] for v in scored.values()),
        "trace_sha256_per_level": digests,
        "facet1_destruction": {
            "facet": "search under destruction",
            "failed_on": sorted(k for k, v in scored.items()
                                if v["facets"]["facet1_destruction"]
                                ["barrier_lost"] or
                                v["facets"]["facet1_destruction"]
                                ["budget_ruin"]),
            "barrier_lost_on": sorted(k for k, v in scored.items()
                                      if v["facets"]["facet1_destruction"]
                                      ["barrier_lost"]),
            "budget_ruin_on": sorted(k for k, v in scored.items()
                                     if v["facets"]["facet1_destruction"]
                                     ["budget_ruin"]),
            "first_barrier_lost_at_turn": min(
                [v["facets"]["facet1_destruction"]["barrier_lost_at_turn"]
                 for v in scored.values()
                 if v["facets"]["facet1_destruction"]["barrier_lost_at_turn"]
                 is not None] or [None]),
            "first_budget_ruin_at_turn": min(
                [v["facets"]["facet1_destruction"]["budget_ruin_at_turn"]
                 for v in scored.values()
                 if v["facets"]["facet1_destruction"]["budget_ruin_at_turn"]
                 is not None] or [None]),
        },
        "facet2_hazard_aware": {
            "facet": "hazard-aware planning",
            "failed_on": sorted(k for k, v in scored.items()
                                if v["facets"]["facet2_hazard_aware"]
                                ["killed"]),
            "died_on": sorted(k for k, v in scored.items()
                              if v["facets"]["facet2_hazard_aware"]["killed"]),
            "killed_through_own_digging": sorted(
                k for k, v in scored.items()
                if v["facets"]["facet2_hazard_aware"]["killed"] and
                (v["facets"]["facet2_hazard_aware"]
                 ["kill_path_cells_dug_by_player"] or 0) > 0),
            "kill_path_cells_dug_by_player": sum(
                v["facets"]["facet2_hazard_aware"]
                ["kill_path_cells_dug_by_player"] or 0
                for v in scored.values()),
            "kill_path_cells_pre_existing": sum(
                v["facets"]["facet2_hazard_aware"]
                ["kill_path_cells_pre_existing"] or 0
                for v in scored.values()),
            "dig_to_death_turns": [
                {"level": k,
                 "turns": v["facets"]["facet2_hazard_aware"]
                 ["dig_to_death_turns"]}
                for k, v in scored.items()
                if v["facets"]["facet2_hazard_aware"]["killed"]],
        },
    }
    f1, f2 = out["facet1_destruction"], out["facet2_hazard_aware"]
    out["the_two_facets"] = {
        "facet1_only": sorted(set(f1["failed_on"]) - set(f2["died_on"])),
        "facet2_only": sorted(set(f2["died_on"]) - set(f1["failed_on"])),
        "both": sorted(set(f1["failed_on"]) & set(f2["died_on"])),
        "neither": sorted(set(scored) - set(f1["failed_on"]) -
                          set(f2["died_on"])),
        "nesting": "facet 2 implies facet 1: a death needs the components to "
                   "have merged.  Under this prose the two facets share one "
                   "mechanism and are separated by outcome, not by mechanic "
                   "-- measured here, not asserted.",
    }
    return out


# ---------------------------------------------------------------------------
# 6. THE RECORD
# ---------------------------------------------------------------------------

def verdict_code_record():
    """WHICH CODE produced the verdict.  Four digests, because a verdict
    without its code is a rumour."""
    def dig(mod):
        return _sha256_of(os.path.join(HERE, mod))
    frozen = freeze.read_record() or {}
    return {
        "module": "digdug/digdug_run.py",
        "function": "cmd_run -> score_field -> write_bundle",
        "sha256": dig("digdug_run.py"),
        "simulator": dig("digdug.py"),
        "reader": dig("digdug_reader.py"),
        "solver": dig("digdug_solve.py"),
        "contract": frozen.get("contract_sha256"),
        "contract_combined_digest": frozen.get("combined_digest"),
        "frozen_at": frozen.get("frozen_at"),
    }


def build_bundle(entrant_name, entrant, result, items, reasoning, gpu,
                 admission, budget, levels_meta, out_dir):
    sc = score_field(items)
    fac = facet_field(items)
    measurable = sc["readable_answers"] > 0
    if not measurable:
        verdict, code = "ERROR: ZERO MEASURED", EXIT_ZERO_MEASURED
    else:
        verdict, code = "SCORED", EXIT_SCORED
    never_started = result.get("never_started", False)
    if never_started:
        verdict, code = "ENTRANT NEVER STARTED", EXIT_NEVER_STARTED
    weights = getattr(entrant, "weights_record", lambda: None)()
    bundle = {
        "harness": HARNESS,
        "version": VERSION,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": EVENT,
        "card_version": CARD_VERSION,
        "declared": {
            "reasoning": reasoning,
            "reasoning_note": {
                "off": "DECLARED BEFORE THE RUN, one setting for the whole "
                       "event.  OFF, because the answer is ONE CHARACTER per "
                       "turn: this is a format-carry task, not multi-step "
                       "arithmetic.  A setting nobody wrote down is "
                       "indistinguishable from a decision.",
                "on": "DECLARED BEFORE THE RUN, one setting for the whole "
                      "event.  ON.",
                "unset": "UNSET is not OFF and the two are never pooled: "
                         "nobody declared a setting for this run.",
            }.get(reasoning, "reasoning=%r -- declared per run" % reasoning),
            "gpu": gpu,
            "gpu_note": gpu.get("note"),
            "budget_turns_per_level": budget,
            "budget_note": "a DECLARED instrument parameter [A14], not a "
                           "discovery; two runs with different budgets are "
                           "not comparable",
        },
        "results": [{
            "entrant": entrant_name,
            "kind": entrant.kind,
            "instrument": entrant.instrument,
            "instrument_note": ("CODE entrant, not a model -- a DIFFERENT "
                                "INSTRUMENT; never pooled into a model table"
                                if entrant.instrument == "code" else
                                "model entrant"),
            "entrant_is_a_model": entrant.entrant_is_a_model,
            "weights": weights,
            "weights_sha256": (weights or {}).get("sha256"),
            "admission": admission,
            "verdict_code": verdict_code_record(),
            "contract": {
                "path": "digdug/CONTRACT_DIGDUG.md",
                "sha256": (freeze.read_record() or {}).get(
                    "contract_sha256"),
                "combined_digest": (freeze.read_record() or {}).get(
                    "combined_digest"),
                "frozen_at": (freeze.read_record() or {}).get("frozen_at"),
                "decisions_recorded": (freeze.read_record() or {}).get(
                    "decision_register", {}).get("n_decisions_recorded"),
                "clause_the_prose_did_not_settle": sorted(
                    (freeze.read_record() or {}).get(
                        "decision_register", {}).get("code", [])),
            },
            "config": {
                "attempt_budget_per_level": budget,
                "levels_scored": [k for k, v in items.items()
                                  if v.get("scored", True)],
                "levels_control": [k for k, v in items.items()
                                   if not v.get("scored", True)],
                "tasks": "digdug/tasks/digdug_v1.json",
            },
            "hardware": host_block(),
            "grammar": digdug_reader.grammar_as_record(),
            "rounds": {
                "R_digdug_levels": dict(
                    sc, kind="grid_puzzle_destructive_search",
                    class_="CONTEST",
                    items=items,   # the TRACE IS PART OF THE RECORD.  Both
                    # facets are read off it and the side script replays it;
                    # a bundle without its trace cannot be checked, only
                    # believed.
                ),
            },
            "facets": fac,
            "levels": levels_meta,
            "aggregate": sc["score"],
            "verdict": verdict,
            "exit_code": code,
            "exit_code_table": EXIT_CODES,
            "certification": ("CODE ENTRANT -- a different instrument; not "
                              "for the board."
                              if entrant.instrument == "code" else
                              "model entrant"),
            "tasks": "digdug/tasks/digdug_v1.json",
            "contract_document": "digdug/CONTRACT_DIGDUG.md",
            "prose_traps": "digdug/DIGDUG_PROSE_TRAPS.md",
        }],
    }
    return bundle


def write_bundle(bundle, out_dir, name):
    """Atomic: .partial then os.replace.  A half-written record is worse than
    none, because it looks like one."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "%s_%s.json" % (CARD_VERSION, name))
    tmp = path + ".partial"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)
    return path


def load_tasks():
    with open(TASKS, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 7. RUNNING AN ENTRANT
# ---------------------------------------------------------------------------

def run_entrant(entrant, tasks, budget=DEFAULT_BUDGET, out_dir=None,
                reasoning=DEFAULT_REASONING, gpu=None, write=True,
                trace_boards=True):
    """Run one entrant over the whole item set.  THE RECORD IS WRITTEN BEFORE
    THE SUCCESS/FAILURE BRANCH -- always, including when the entrant never
    started, and including when the run is an error."""
    gpu = gpu if gpu is not None else probe_gpu()
    items = {}
    levels_meta = {}
    admission = {"admitted": True}
    never_started = False
    load_error = None

    scored_levels = [lv for lv in tasks["levels"] if lv.get("scored", True)]
    control_levels = [lv for lv in tasks["levels"] if not lv.get("scored", True)]

    for meta in scored_levels:
        lvl = find_level(meta["file"])
        try:
            a = play_level(lvl, entrant, budget, trace_boards)
            res = a.result()
        except Exception as exc:                       # noqa: BLE001
            if not items:
                never_started = True
                load_error = "%s: %s" % (exc.__class__.__name__, exc)
                holder = probe_holder(8080, kind="port")
                admission = {"admitted": False, "stage": "load",
                             "error": load_error, "holder": holder}
                break
            raise
        res["scored"] = True
        res["trace_sha256"] = digdug.trace_digest(res["trace"])
        res["optimal_moves"] = meta.get("optimal_moves")
        res["n_distinct_optimal_lines"] = meta.get("n_distinct_optimal_lines")
        items[meta["file"]] = res
        levels_meta[meta["file"]] = {
            "sha256": lvl.sha256, "enclosed": lvl.enclosed,
            "targets": lvl.n_targets, "hazards": lvl.n_hazards,
            "optimal_moves": meta.get("optimal_moves"),
            "distinct_optimal_lines": meta.get("n_distinct_optimal_lines"),
        }

    # the CONTROL level: run, recorded, never scored [A5]
    if not never_started:
        for meta in control_levels:
            lvl = find_level(meta["file"])
            a = play_level(lvl, entrant, budget, trace_boards)
            res = a.result()
            res["scored"] = False
            res["control_role"] = meta.get("role")
            res["correct_answer_was"] = ("an abstention -- there is no safe "
                                         "line, proved exhaustively")
            res["abstained"] = bool(res["give_up"])
            res["was_right"] = bool(res["give_up"])
            items[meta["file"]] = res
            levels_meta[meta["file"]] = {
                "sha256": lvl.sha256, "enclosed": lvl.enclosed,
                "targets": lvl.n_targets, "hazards": lvl.n_hazards,
                "optimal_moves": None, "distinct_optimal_lines": 0,
                "role": meta.get("role"),
            }

    result = {"never_started": never_started, "load_error": load_error}
    bundle = build_bundle(entrant.name, entrant, result, items, reasoning,
                          gpu, admission, budget, levels_meta, out_dir)
    bundle["results"][0]["never_started"] = never_started
    if never_started:
        bundle["results"][0]["verdict"] = "ENTRANT NEVER STARTED"
        bundle["results"][0]["exit_code"] = EXIT_NEVER_STARTED
        bundle["results"][0]["rounds"] = {"R_digdug_levels":
                                          {"load_error": load_error,
                                           "items": {}}}
        bundle["results"][0]["facets"] = None
        bundle["results"][0]["aggregate"] = None
    path = None
    if write and out_dir:
        path = write_bundle(bundle, out_dir, entrant.name)
    code = bundle["results"][0]["exit_code"]
    return {"bundle": bundle, "path": path, "exit_code": code,
            "never_started": never_started, "items": items}


# ---------------------------------------------------------------------------
# 8. COMMANDS
# ---------------------------------------------------------------------------

def _check_frozen(quiet=False):
    ok, why = freeze.verify()
    if not quiet:
        print(("FROZEN  %s" % why) if ok else ("REFUSED %s" % why))
    return ok


def cmd_run(args):
    if args.entrant not in ENTRANTS:
        print("unknown entrant %r -- known: %s"
              % (args.entrant, ", ".join(sorted(ENTRANTS))))
        return EXIT_USAGE
    if not _check_frozen():
        return EXIT_NOT_FROZEN
    tasks = load_tasks()
    gpu = probe_gpu()
    if args.entrant == "model":
        ent = ModelEntrant(model_path=args.model_path,
                           server_url=args.server_url)
        ok, adm = ent.admit()
        if not ok:
            # NEVER STARTED is counted separately from played-and-failed, and
            # the record still gets written -- a run with no record is not a
            # run.
            res = run_entrant(ent, tasks, budget=args.budget,
                              out_dir=args.out, reasoning=args.reasoning,
                              gpu=gpu)
            res["bundle"]["results"][0]["admission"] = adm
            if args.out:
                write_bundle(res["bundle"], args.out, ent.name)
            print("NEVER STARTED -- %s" % adm["note"])
            return EXIT_NEVER_STARTED
        admission = adm
    else:
        ent = ENTRANTS[args.entrant]()
        admission = {"admitted": True, "instrument": "code"}
    res = run_entrant(ent, tasks, budget=args.budget, out_dir=args.out,
                      reasoning=args.reasoning, gpu=gpu)
    b = res["bundle"]["results"][0]
    print("entrant %-16s verdict %-22s exit %d"
          % (args.entrant, b["verdict"], b["exit_code"]))
    if b.get("rounds") and b["rounds"].get("R_digdug_levels", {}).get("score") is not None:
        sc = b["rounds"]["R_digdug_levels"]
        print("  solved %d/%d  score %s  emitted %d consumed %d  "
              "dug %d blocked %d  not_an_action %d give_up %d"
              % (sc["solved"], sc["attempted_emitted"], sc["score"],
                 sc["answers_emitted"], sc["answers_consumed"],
                 sc["moves_are_a_cost"]["dug"],
                 sc["moves_are_a_cost"]["blocked"],
                 sc["not_an_action"], sc["give_up"]))
        f = b["facets"]
        print("  FACET 1 destruction: barrier_lost_on %s  budget_ruin_on %s"
              % (f["facet1_destruction"]["barrier_lost_on"],
                 f["facet1_destruction"]["budget_ruin_on"]))
        print("  FACET 2 hazard-aware: died_on %s  own_digging %s"
              % (f["facet2_hazard_aware"]["died_on"],
                 f["facet2_hazard_aware"]["killed_through_own_digging"]))
        print("  one trace for both facets: %s" % f["one_trace_per_level"])
    if res["path"]:
        print("  record %s" % res["path"])
    return res["exit_code"]


def cmd_run_all(args):
    if not _check_frozen():
        return EXIT_NOT_FROZEN
    tasks = load_tasks()
    gpu = probe_gpu()
    names = [n for n in ENTRANTS if n not in ("model",)]
    codes = {}
    for n in names:
        ent = ENTRANTS[n]()
        res = run_entrant(ent, tasks, budget=args.budget, out_dir=args.out,
                          reasoning=args.reasoning, gpu=gpu)
        codes[n] = res["exit_code"]
        b = res["bundle"]["results"][0]
        print("%-16s exit %d  %-22s" % (n, res["exit_code"], b["verdict"]))
    print()
    print("run-all: %d entrants, exit codes %s"
          % (len(codes), sorted(set(codes.values()))))
    # The exit code of run-all reflects the FIELD, and is never a constant:
    # if any entrant's record could not be written, that is what comes back.
    if any(c == EXIT_WRITE_FAILED for c in codes.values()):
        return EXIT_WRITE_FAILED
    return EXIT_SCORED


def instrument_check(out_dir=None, reasoning=DEFAULT_REASONING,
                     budget=DEFAULT_BUDGET):
    """Prove the instrument before trusting a number from it."""
    print("== 1. the contract is frozen ==")
    ok, why = freeze.verify()
    print("   %s" % why)
    if not ok:
        return EXIT_INSTRUMENT
    print("== 2. the simulator's controls ==")
    rc = digdug.self_test()
    if rc != 0:
        return EXIT_INSTRUMENT
    print("== 3. the levels, proved by complete search ==")
    ok_levels, rows = digdug_solve.verify_levels(budget=budget)
    if not ok_levels:
        return EXIT_INSTRUMENT
    print("== 4. the two destruction proofs ==")
    for n in digdug.LEVEL_FILES:
        lvl = find_level(n)
        r = digdug_solve.destruction_reachability_proof(lvl)
        h = digdug_solve.hazard_reach_proof(lvl)
        print("   %-30s route %s  barrier %s"
              % (n, "HOLDS" if r["holds"] else "VIOLATED",
                 "MONOTONE" if h["holds"] else "VIOLATED"))
        if not (r["holds"] and h["holds"]):
            return EXIT_INSTRUMENT
    print("== 5. the field, in process ==")
    tasks = load_tasks()
    gpu = probe_gpu()
    codes = {}
    for n in sorted(ENTRANTS):
        if n == "model":
            continue
        ent = ENTRANTS[n]()
        res = run_entrant(ent, tasks, budget=budget, out_dir=out_dir,
                          reasoning=reasoning, gpu=gpu, trace_boards=False)
        codes[n] = res["exit_code"]
    for n in sorted(codes):
        print("   %-16s exit %d" % (n, codes[n]))
    print("   no entrant's run exits 1: %s"
          % all(c != EXIT_INSTRUMENT for c in codes.values()))
    if any(c == EXIT_INSTRUMENT for c in codes.values()):
        return EXIT_INSTRUMENT
    print()
    print("INSTRUMENT CHECK PASSED")
    return EXIT_SCORED


def verify_all(out_dir):
    """Replay EVERY bundle from its own record and recompute the numbers.

    A bundle that cannot be replayed from what is in it is a claim, not a
    record.  This also refuses a results directory whose bundles do not all
    declare the same reasoning setting and the same GPU: two bundles for one
    event that declare different instruments are not the same measurement.
    """
    import glob
    paths = sorted(glob.glob(os.path.join(out_dir, "%s_*.json" % CARD_VERSION)))
    if not paths:
        print("no bundles in %s" % out_dir)
        return EXIT_USAGE
    reasonings, gpus = set(), set()
    bad = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as fh:
            b = json.load(fh)
        r = b["results"][0]
        reasonings.add(b["declared"]["reasoning"])
        g = b["declared"]["gpu"]
        gpus.add(json.dumps(g, sort_keys=True))
        if r.get("never_started"):
            print("  %-24s NEVER STARTED (record present, holder probed)"
                  % os.path.basename(p))
            continue
        items = r["rounds"]["R_digdug_levels"]["items"]
        # recompute the score from the primitives in the record
        sc = score_field(items)
        stored = r["rounds"]["R_digdug_levels"]
        for k in ("solved", "attempted_emitted", "answers_emitted",
                  "answers_consumed"):
            if sc[k] != stored.get(k):
                bad.append("%s: %s recomputes to %s, record says %s"
                           % (os.path.basename(p), k, sc[k], stored.get(k)))
        if stored.get("score") != sc["score"]:
            bad.append("%s: score recomputes to %s, record says %s"
                       % (os.path.basename(p), sc["score"], stored.get("score")))
        # recompute the facets from the STORED traces
        fac = {}
        for name, it in items.items():
            if not it.get("scored", True):
                continue
            lvl = find_level(name)
            trace = it.get("trace")
            if trace is None:
                bad.append("%s: %s has no trace to replay"
                           % (os.path.basename(p), name))
                continue
            f = digdug.facets_from_trace(lvl, trace, it["budget"])
            fac[name] = f
            if f["trace_sha256"] != it["facets"]["trace_sha256"]:
                bad.append("%s: %s trace digest moved on replay"
                           % (os.path.basename(p), name))
            for fk in ("facet1_destruction", "facet2_hazard_aware"):
                for kk in ("barrier_lost_at_turn", "budget_ruin_at_turn",
                           "died_at_turn",
                           "kill_path_cells_dug_by_player"):
                    a = f[fk].get(kk)
                    bb = it["facets"][fk].get(kk)
                    if a != bb:
                        bad.append("%s: %s %s.%s recomputes to %s, record %s"
                                   % (os.path.basename(p), name, fk, kk,
                                      a, bb))
        both = all(v["facet1_destruction"]["trace_sha256"] ==
                   v["facet2_hazard_aware"]["trace_sha256"]
                   for v in fac.values())
        if fac and not both:
            bad.append("%s: the two facets do not cite one trace"
                       % os.path.basename(p))
        print("  %-30s solved %d/%d  score %s  F1 %s  F2 %s  replayed"
              % (os.path.basename(p), sc["solved"], sc["attempted_emitted"],
                 sc["score"],
                 r["facets"]["facet1_destruction"]["failed_on"],
                 r["facets"]["facet2_hazard_aware"]["died_on"]))
    if len(reasonings) > 1:
        bad.append("the directory declares MORE THAN ONE reasoning setting: %s"
                   % sorted(reasonings))
    if len(gpus) > 1:
        bad.append("the directory declares MORE THAN ONE GPU")
    print()
    if bad:
        print("BUNDLE VERIFICATION FAILED -- %d problem(s)" % len(bad))
        for x in bad:
            print("   %s" % x)
        return EXIT_INSTRUMENT
    print("BUNDLE VERIFICATION PASSED -- %d bundles replayed, one declared "
          "reasoning (%s) and one declared GPU" % (len(paths),
                                                   sorted(reasonings)))
    return EXIT_SCORED


def cmd_exit_codes(args):
    print("exit codes, each produced by a path the self-test calls:")
    for k in sorted(EXIT_CODES):
        print("  %d  %s" % (k, EXIT_CODES[k]))
    return EXIT_SCORED


def main(argv=None):
    ap = argparse.ArgumentParser(description="the DIG DUG runner")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("run", help="run one entrant")
    p.add_argument("entrant")
    p.add_argument("--out", default=os.path.join(HERE, "results"))
    p.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    p.add_argument("--reasoning", default=DEFAULT_REASONING)
    p.add_argument("--model-path")
    p.add_argument("--server-url", default="http://127.0.0.1:8080")

    p = sub.add_parser("run-all", help="run the whole field")
    p.add_argument("--out", default=os.path.join(HERE, "results"))
    p.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    p.add_argument("--reasoning", default=DEFAULT_REASONING)

    p = sub.add_parser("instrument-check")
    p.add_argument("--out", default=os.path.join(HERE, "results"))
    p.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    p.add_argument("--reasoning", default=DEFAULT_REASONING)

    p = sub.add_parser("verify")
    p.add_argument("--out", default=os.path.join(HERE, "results"))

    sub.add_parser("exit-codes")
    sub.add_parser("levels")

    a = ap.parse_args(argv)
    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "run-all":
        return cmd_run_all(a)
    if a.cmd == "instrument-check":
        return instrument_check(out_dir=a.out, reasoning=a.reasoning,
                                budget=a.budget)
    if a.cmd == "verify":
        return verify_all(a.out)
    if a.cmd == "exit-codes":
        return cmd_exit_codes(a)
    if a.cmd == "levels":
        ok, _rows = digdug_solve.verify_levels()
        return 0 if ok else EXIT_INSTRUMENT
    ap.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
