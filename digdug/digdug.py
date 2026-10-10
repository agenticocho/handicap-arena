#!/usr/bin/env python3
# digdug.py -- THE DIG DUG CABINET: the frozen contract, implemented once.
#
# THE PROSE THIS WAS BUILT FROM is quoted in full in CONTRACT_DIGDUG.md
# section 1.  It is one paragraph, it is under-specified on purpose, and
# every clause it does not settle is DECIDED here, marked [U<n>] (the prose
# was silent and the brief named the gap) or [A<n>] (the prose was silent and
# the brief did not even raise it), argued in DIGDUG_PROSE_TRAPS.md, and
# frozen by freeze.py before any entrant ran.
#
# THE FROZEN TRANSITION FUNCTION (CONTRACT section 3):
#
#     step(state, action) -> (new_state, word)
#
# TWO values.  Not three.  `new_state` is a NEW State: step() NEVER mutates
# the state it was given [A2].  `word` in {dug, moved, blocked, collected}.
# Bounds are checked HERE, in the transition function [B2].
#
#     turn(state, action) -> (new_state, word, events)
#
# The whole turn: the player's move, the collection, the hazard clock, the
# death check.  `word` may also be "killed".
#
# Stdlib only.

import argparse
import hashlib
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import digdug_reader                                       # noqa: E402
from digdug_reader import (ACTIONS, STEP_WORDS, TURN_WORDS,   # noqa: E402
                           contract_agrees_with_code, read_answer,
                           OUTCOME_ACTION, OUTCOME_GIVE_UP,
                           OUTCOME_NOT_AN_ACTION)

HARNESS = "handicap-arena"
VERSION = "1.0"
EVENT = "DIG DUG"
CONTRACT = os.path.join(HERE, "CONTRACT_DIGDUG.md")

# ---------------------------------------------------------------------------
# 1. THE BOARD -- glyphs, and what makes a level MALFORMED
# ---------------------------------------------------------------------------

WALL = "#"          # rock.  impassable, undiggable, forever.
SOIL = "%"          # dirt.  impassable UNTIL dug; digging is what opens it.
TUNNEL = " "        # already-dug ground, open at t=0.
PLAYER = "P"        # the player.  Its cell is a TUNNEL at t=0.  [U2]
HAZARD = "H"        # a hazard.  Its cell is a TUNNEL at t=0.  [U2]
TARGET_SOIL = "T"   # a target buried in soil.
TARGET_TUNNEL = "*" # a target standing in an open tunnel.

LEGAL_CHARS = frozenset((WALL, SOIL, TUNNEL, PLAYER, HAZARD,
                         TARGET_SOIL, TARGET_TUNNEL))

DELTAS = (("U", (-1, 0)), ("D", (1, 0)), ("L", (0, -1)), ("R", (0, 1)))
DELTA = dict(DELTAS)
#: The direction order every tie in this cabinet is broken by.  Declared
#: once, used by the hazard policy and by the solver, so "the hazard moved
#: left" is a fact about the frozen contract and not about dict ordering.
DIRECTION_ORDER = ("U", "D", "L", "R")


class MalformedLevel(ValueError):
    """A level that is not a board.  Never silently parsed into one."""


class Level(object):
    """The static part of a level: rock, soil, targets, and the two starts."""

    __slots__ = ("name", "text", "sha256", "walls", "soil", "open", "targets",
                 "player_start", "hazard_starts", "height", "width",
                 "enclosed", "ragged")

    def __init__(self, name, text, walls, soil, open_cells, targets,
                 player_start, hazard_starts, height, width, enclosed, ragged,
                 sha256):
        self.name = name
        self.text = text
        self.sha256 = sha256
        self.walls = walls                # frozenset
        self.soil = soil                  # frozenset
        self.open = open_cells            # frozenset -- tunnels at t=0 [U2]
        self.targets = targets            # frozenset
        self.player_start = player_start
        self.hazard_starts = hazard_starts    # tuple, in reading order
        self.height = height
        self.width = width
        self.enclosed = enclosed          # MEASURED, not assumed [B2]
        self.ragged = ragged

    @property
    def n_targets(self):
        return len(self.targets)

    @property
    def n_hazards(self):
        return len(self.hazard_starts)

    @property
    def playable(self):
        """Every cell that is not rock.  Digging never changes this set."""
        return self.soil | self.open


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_level(text, name="<level>"):
    """Parse ASCII into a Level, or raise MalformedLevel.

    Malformed -- an ERROR, never a board:
      * empty or whitespace-only text                        [A3]
      * a character outside the seven glyphs                 [A3]
      * not exactly one player                               [A3]
      * zero targets   (prose: "at least one target")        [U3]
      * zero hazards   (prose: "at least one hazard")        [U3]
      * fewer than 3 rows or 3 columns                       [A3]
      * the player's cell adjacent to nothing playable       [A3]

    Ragged rows are PADDED WITH ROCK, not with soil [A4].  Padding with soil
    would invent diggable ground outside the author's board, and a hazard
    could then arrive from a column nobody drew.  The fact is recorded.

    Enclosure is MEASURED [B2]: every border cell must be rock.  A level that
    is not enclosed is not rejected here -- it is recorded, and the runner
    refuses to score it, and `step()` still checks bounds, because the check
    belongs in the transition function and not in the loader.
    """
    if text is None or not text.strip():
        raise MalformedLevel("%s: empty level text" % name)

    raw_lines = text.split("\n")
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    if not raw_lines:
        raise MalformedLevel("%s: empty level text" % name)

    width = max(len(ln) for ln in raw_lines)
    ragged = any(len(ln) != width for ln in raw_lines)
    rows = [ln.ljust(width, WALL) for ln in raw_lines]     # [A4]
    height = len(rows)
    if height < 3 or width < 3:
        raise MalformedLevel("%s: a board needs at least 3 rows and 3 columns "
                             "(got %dx%d)" % (name, height, width))

    walls, soil, open_cells, targets = set(), set(), set(), set()
    players, hazards = [], []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch not in LEGAL_CHARS:
                raise MalformedLevel(
                    "%s: illegal character %r at row %d col %d (legal: "
                    "%s)" % (name, ch, r, c, " ".join(sorted(LEGAL_CHARS))))
            cell = (r, c)
            if ch == WALL:
                walls.add(cell)
            elif ch == SOIL:
                soil.add(cell)
            elif ch == TUNNEL:
                open_cells.add(cell)
            elif ch == PLAYER:
                players.append(cell)
                open_cells.add(cell)          # [U2] the player stands in a
            elif ch == HAZARD:                #        tunnel at t=0
                hazards.append(cell)
                open_cells.add(cell)          # [U2]
            elif ch == TARGET_SOIL:
                targets.add(cell)
                soil.add(cell)                # buried: the cell IS soil
            elif ch == TARGET_TUNNEL:
                targets.add(cell)
                open_cells.add(cell)

    if len(players) != 1:
        raise MalformedLevel("%s: exactly one player required, found %d"
                             % (name, len(players)))
    if not targets:
        raise MalformedLevel("%s: zero targets -- the prose requires at "
                             "least one [U3]" % name)
    if not hazards:
        raise MalformedLevel("%s: zero hazards -- the prose requires at "
                             "least one [U3]" % name)

    enclosed = all((r, c) in walls
                   for r in range(height) for c in range(width)
                   if r in (0, height - 1) or c in (0, width - 1))

    lvl = Level(name, text, frozenset(walls), frozenset(soil),
                frozenset(open_cells), frozenset(targets), players[0],
                tuple(hazards), height, width, enclosed, ragged,
                _sha256_text(text))

    if not _neighbours(lvl, lvl.player_start):
        raise MalformedLevel("%s: the player at %s has no playable neighbour "
                             "-- it cannot move at all" % (name, players[0]))
    return lvl


def _neighbours(level, cell):
    """Playable orthogonal neighbours, in DIRECTION_ORDER."""
    r, c = cell
    out = []
    for d in DIRECTION_ORDER:
        dr, dc = DELTA[d]
        n = (r + dr, c + dc)
        if 0 <= n[0] < level.height and 0 <= n[1] < level.width \
                and n not in level.walls:
            out.append((d, n))
    return out


LEVEL_FILES = ("01_first_blood.txt", "02_the_long_way_round.txt",
               "03_the_open_door.txt", "04_no_safe_line.txt")
#: which levels the GATE scores.  04 is a CONTROL: it has no safe line
#: (proven by exhaustive search in digdug_solve.py), so the only correct
#: answer on it is an abstention, and scoring it would punish a correct
#: answer -- which standing rule R3 calls a disproof of the spec.  [A5]
SCORED_LEVELS = LEVEL_FILES[:3]
CONTROL_LEVELS = LEVEL_FILES[3:]


def find_level(name, extra_dirs=()):
    """Resolve a level by filename.  A path that does not resolve RAISES.

    Fail-soft loading is how an instrument ends up playing an empty field and
    reporting a score for it.
    """
    dirs = [os.path.join(HERE, "levels")] + list(extra_dirs)
    base = os.path.basename(name)
    for d in dirs:
        p = os.path.join(d, base)
        if os.path.isfile(p):
            return load_level(p, base)
    raise MalformedLevel("level %r not found in %s" % (name, dirs))


def load_level(path, name=None):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return parse_level(text, name or os.path.basename(path))


def load_level_set(names=LEVEL_FILES, extra_dirs=()):
    return [find_level(n, extra_dirs) for n in names]


# ---------------------------------------------------------------------------
# 2. THE STATE -- immutable by convention, because step() is pure [A2]
# ---------------------------------------------------------------------------

class State(object):
    """One position in the game.  Never mutated by step() or turn().

    Fields are the whole truth about a position; a reader holding a State can
    replay the rest of the game without asking anybody what happened.
    """

    __slots__ = ("level", "player", "dug", "targets_left", "hazards", "turn",
                 "dead", "solved", "kill")

    def __init__(self, level, player=None, dug=None, targets_left=None,
                 hazards=None, turn=0, dead=False, solved=False, kill=None):
        self.level = level
        self.player = player if player is not None else level.player_start
        #: cells the PLAYER dug.  Kept apart from level.open on purpose: the
        #: facet-2 question is "did the route IT DUG let the hazard in", and
        #: that cannot be answered from a merged set.
        self.dug = frozenset() if dug is None else frozenset(dug)
        self.targets_left = (frozenset(level.targets) if targets_left is None
                             else frozenset(targets_left))
        self.hazards = (tuple(level.hazard_starts) if hazards is None
                        else tuple(hazards))
        self.turn = turn
        self.dead = dead
        self.solved = solved
        #: provenance of a death: which hazard, and the tunnel path it walked.
        self.kill = kill

    # -- derived ------------------------------------------------------------
    @property
    def tunnels(self):
        """Every open cell: what was open at t=0, plus what the player dug."""
        return self.level.open | self.dug

    @property
    def over(self):
        return self.dead or self.solved

    def copy(self, **kw):
        vals = dict(level=self.level, player=self.player, dug=self.dug,
                    targets_left=self.targets_left, hazards=self.hazards,
                    turn=self.turn, dead=self.dead, solved=self.solved,
                    kill=self.kill)
        vals.update(kw)
        return State(**vals)

    def key(self):
        """Hashable identity, for the solver's closed set."""
        return (self.player, self.dug, self.targets_left, self.hazards)

    def render(self):
        return render(self)

    def as_record(self):
        return {
            "player": list(self.player),
            "hazards": [list(h) for h in self.hazards],
            "targets_left": sorted([list(t) for t in self.targets_left]),
            "n_dug_by_player": len(self.dug),
            "turn": self.turn,
            "dead": self.dead,
            "solved": self.solved,
        }


def render(state):
    """The board.  The grid is the screen; no decoration, no legend inside."""
    lvl = state.level
    tun = state.tunnels
    out = []
    for r in range(lvl.height):
        row = []
        for c in range(lvl.width):
            cell = (r, c)
            if cell == state.player and cell in state.hazards:
                row.append("X")           # the player and a hazard, one cell
            elif cell == state.player:
                row.append("P")
            elif cell in state.hazards:
                row.append("H")
            elif cell in lvl.walls:
                row.append(WALL)
            elif cell in state.targets_left:
                row.append(TARGET_SOIL if cell in lvl.soil else TARGET_TUNNEL)
            elif cell in tun:
                row.append(TUNNEL)
            else:
                row.append(SOIL)
        out.append("".join(row))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 3. THE TRANSITION FUNCTION -- step() and turn()
# ---------------------------------------------------------------------------

def step(state, action):
    """THE TRANSITION FUNCTION.  Frozen by CONTRACT section 3.

        step(state, action) -> (new_state, word)

    TWO values.  `word` in {dug, moved, blocked, collected}.

      * PURE.  `state` is untouched; the answer is a NEW State [A2].
      * BOUNDS ARE CHECKED HERE [B2].  Out of bounds is `blocked`, never an
        exception and never a walk off the edge of the board.
      * An action outside {U,D,L,R} RAISES.  It is never folded into
        `blocked`, because `blocked` counts a legal letter aimed at rock, and
        a programming error must not inflate a real counter [A6].
      * The player's move does not advance the turn counter; `turn()` does.

    Words, in precedence order [A7]: a move that opens soil AND collects is
    `collected`, and the dig is still reported in `events`.
    """
    if action not in DELTA:
        raise ValueError("step() takes a resolved action letter in %s, got %r"
                         % (list(ACTIONS), action))
    lvl = state.level
    dr, dc = DELTA[action]
    r, c = state.player
    dst = (r + dr, c + dc)

    # [B2] bounds, in the transition function.  [U9] bounded, NO WRAP:
    # out of bounds is `blocked`, never a torus and never an exception.
    if not (0 <= dst[0] < lvl.height and 0 <= dst[1] < lvl.width):
        return state.copy(), "blocked"
    if dst in lvl.walls:
        return state.copy(), "blocked"

    dug_cell = dst in lvl.soil and dst not in state.dug
    word = "dug" if dug_cell else "moved"
    new_dug = state.dug | {dst} if dst in lvl.soil else state.dug
    new_targets = state.targets_left
    if dst in state.targets_left:
        new_targets = state.targets_left - {dst}
        word = "collected"

    return state.copy(player=dst, dug=new_dug, targets_left=new_targets), word


def hazard_next(level, tunnels, hazard, player):
    """THE HAZARD POLICY.  [U1] -- and it is load-bearing, so it is frozen.

    One cell per player turn, through TUNNELS ONLY (the prose: a hazard
    "cannot reach the player except through tunnels"), along a SHORTEST path
    to the player's CURRENT cell, ties broken by DIRECTION_ORDER.  Hazards
    never dig: a hazard in sealed soil stays there until the player opens a
    way in, which is the whole reason the tunnels the player digs are also
    the routes by which a hazard can arrive.

    [A1] HAZARDS NEVER DIG.  The prose implies it ("cannot reach the
    player except through tunnels") but never says it, and a hazard that
    dug would make that sentence false.

    Rejected alternatives, all recorded in the contract:
      * a random walk        -- unreproducible, so the record could not be
                               replayed and the cabinet could not certify.
      * a one-step greedy    -- parity artefacts: a greedy hazard oscillates
        in a corridor and never arrives, so "it killed me" depends on a tie
        nobody wrote down.
      * hazards that dig     -- makes the prose's own sentence false.
    """
    if hazard == player:
        return hazard
    # BFS over the tunnel graph.  The player's cell is a tunnel by
    # construction, so it is always a legal destination.
    prev = {hazard: None}
    q = deque((hazard,))
    found = False
    while q:
        cur = q.popleft()
        if cur == player:
            found = True
            break
        for _d, n in _tunnel_neighbours(level, tunnels, cur):
            if n not in prev:
                prev[n] = cur
                q.append(n)
    if not found or player not in prev:
        return hazard                      # sealed: it cannot reach, it waits
    # walk back to the first step
    node = player
    while prev[node] != hazard:
        node = prev[node]
    return node


def _tunnel_neighbours(level, tunnels, cell):
    r, c = cell
    out = []
    for d in DIRECTION_ORDER:
        dr, dc = DELTA[d]
        n = (r + dr, c + dc)
        if 0 <= n[0] < level.height and 0 <= n[1] < level.width \
                and n in tunnels:
            out.append((d, n))
    return out


def hazard_moves(state):
    """All hazards, SIMULTANEOUSLY, from their pre-move cells.  [U8]

    Rejected: sequential movement in index order.  Under a sequential clock
    the ORDER of the hazards in the level file decides who gets the corner,
    so two files with the same board and the hazards listed the other way
    round are different games.  Simultaneous movement from a single snapshot
    makes the board the only input.

    [A10] Hazards may share a cell with each other and do not block each
    other, so the board is the only input to any of them.
    """
    tunnels = state.tunnels
    return tuple(hazard_next(state.level, tunnels, h, state.player)
                 for h in state.hazards)


def turn(state, action):
    """THE WHOLE TURN.  Frozen order, CONTRACT section 3:

        1. the player's move resolves (step)
        2. a target in the entered cell is collected, and collecting the LAST
           target ENDS the attempt -- before the hazards move [U7]
        3. the hazard clock ticks once, for every hazard, simultaneously [U1]
        4. the death check: a hazard in the player's cell kills [U4]

    -> (new_state, word, events)

    A BLOCKED move still costs the turn and still ticks the hazard clock
    [A8].  Rejected: a blocked move being free.  Under a free block a
    wall-bumper is immortal, and `blocked` stops being a cost.
    """
    s, word = step(state, action)
    events = [word]
    if word == "collected" and s.player in s.level.soil:
        events.append("dug")
    s = s.copy(turn=state.turn + 1)

    if not s.targets_left:
        # [U6] SOLVED = every target collected, alive, on the collecting
        # turn.  Rejected: a designated exit cell, surviving N turns.
        # [U7] ... and the objective is awarded the moment it is
        # achieved, BEFORE the hazard clock ticks.
        return s.copy(solved=True), word, events + ["solved"]

    hazards = hazard_moves(s)
    if s.player in hazards:
        killer = None
        for i, h in enumerate(hazards):
            if h == s.player:
                killer = i
                break
        path = hazard_path(s.level, s.tunnels, state.hazards[killer],
                           s.player)
        kill = {
            "hazard_index": killer,
            "hazard_from": list(state.hazards[killer]),
            "hazard_to": list(s.player),
            "path": [list(p) for p in path],
        }
        return (s.copy(hazards=hazards, dead=True, kill=kill),
                "killed", events + ["killed"])

    return s.copy(hazards=hazards), word, events


def hazard_path(level, tunnels, src, dst):
    """The tunnel path a hazard walked, for the death provenance."""
    if src == dst:
        return [dst]
    prev = {src: None}
    q = deque((src,))
    while q:
        cur = q.popleft()
        if cur == dst:
            break
        for _d, n in _tunnel_neighbours(level, tunnels, cur):
            if n not in prev:
                prev[n] = cur
                q.append(n)
    if dst not in prev:
        return [src, dst]
    out = [dst]
    while prev[out[-1]] is not None:
        out.append(prev[out[-1]])
    out.reverse()
    return out


# ---------------------------------------------------------------------------
# 4. THE TWO FACETS, READ OFF ONE TRACE
# ---------------------------------------------------------------------------
#
# Standing demand D: TWO FACETS, ONE RUN.  Both functions below take the SAME
# trace object and nothing else -- not a second playthrough, not a second
# event.  `facets_from_trace()` calls them both on one list and stamps both
# results with the digest of that list, so a reader can see that the two
# numbers came from one run.

def trace_digest(trace):
    import json
    blob = json.dumps(trace, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def hazard_component(level, tunnels, cell):
    """Every cell connected to `cell` through tunnels.  Digging only ADDS
    edges, so this set is monotone: once the player and a hazard share a
    component they share it forever."""
    seen = {cell}
    q = deque((cell,))
    while q:
        cur = q.popleft()
        for _d, n in _tunnel_neighbours(level, tunnels, cur):
            if n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def facet_destruction(level, trace, budget):
    """FACET 1 -- SEARCH UNDER DESTRUCTION.

    "Did the plan consume the ground it needed?"  Two numbers, both provable
    from the recorded map, neither of them needing the hazard to have moved:

      1a BARRIER LOST -- the first turn at which the player's own digging put
         it in the same connected tunnel component as a hazard.  Irreversible
         by construction (digging is permanent), so the soil that was keeping
         the hazard out is gone for the rest of the run.

      1b BUDGET RUIN -- the first turn at which the shortest possible
         completion is longer than the turns left.  Moving into soil costs
         exactly one move, the same as moving through a tunnel, so on a
         single-target level the shortest completion is the rock-free distance
         to the target -- exact, not a heuristic, and independent of what has
         been dug.  The plan spent its ground and its turns on a corridor
         that does not help.

    1a and 1b are different failures.  1b needs no hazard at all.
    """
    barrier_lost_at = None
    budget_ruin_at = None
    per_turn = []
    for ply in trace:
        st = ply.get("state_after")
        if not st:
            continue
        t = st["turn"]
        merged = st["hazard_component_includes_player"]
        if merged and barrier_lost_at is None:
            barrier_lost_at = t
        remaining = st["min_moves_to_complete"]
        # the cap is on ANSWERS [A14], so the moves left can never exceed the
        # answers left -- which makes this comparison a proof, not a guess.
        left = budget - ply.get("answers_emitted", t)
        ruined = remaining is not None and remaining > left
        if ruined and budget_ruin_at is None:
            budget_ruin_at = t
        per_turn.append({"turn": t, "merged": merged,
                         "min_moves_to_complete": remaining,
                         "answers_left": left, "budget_ruined": ruined})
    return {
        "facet": "search under destruction",
        "facet_id": 1,
        "barrier_lost": barrier_lost_at is not None,
        "barrier_lost_at_turn": barrier_lost_at,
        "budget_ruin": budget_ruin_at is not None,
        "budget_ruin_at_turn": budget_ruin_at,
        "budget": budget,
        "irreversible": "digging is permanent, so 1a can never become False "
                        "again -- this is the only monotone loss in the game",
        "measured_from": "the recorded map on each ply of THIS trace",
        "per_turn": per_turn,
    }


def facet_hazard(level, trace):
    """FACET 2 -- HAZARD-AWARE PLANNING.

    "Did the route it dug open a path for the hazard that killed it?"  Read
    off the death record on the same trace: the killing hazard's path, how
    many of its cells the PLAYER dug, and how many turns passed between the
    first of those cells being dug and the death.  A death the player did not
    dig a road for -- a hazard that was already in the player's component at
    t=0 -- is recorded as such, because that is a level defect and not an
    entrant failure.
    """
    killed = False
    kill = None
    for ply in trace:
        if ply.get("word") == "killed":
            killed = True
            kill = ply
    if not killed or not kill:
        return {
            "facet": "hazard-aware planning",
            "facet_id": 2,
            "killed": False,
            "died_at_turn": None,
            "kill_path_cells": 0,
            "kill_path_cells_dug_by_player": 0,
            "kill_path_cells_pre_existing": 0,
            "kill_path_all_player_dug": None,
            "hazard_index": None,
            "first_kill_cell_dug_at_turn": None,
            "dig_to_death_turns": None,
            "measured_from": "the recorded death on THIS trace",
        }
    st = kill["state_after"]
    path = [tuple(p) for p in (kill.get("kill_path") or [])]
    dug_by_player = [p for p in path if p in set(
        tuple(x) for x in st.get("dug_by_player", []))]
    first_dug = None
    for cell in dug_by_player:
        for ply in trace:
            if ply.get("dug_cell") and tuple(ply["dug_cell"]) == cell:
                first_dug = ply["turn"]
                break
        if first_dug is not None:
            break
    return {
        "facet": "hazard-aware planning",
        "facet_id": 2,
        "killed": True,
        "died_at_turn": st["turn"],
        "kill_path_cells": len(path),
        "kill_path_cells_dug_by_player": len(dug_by_player),
        "kill_path_all_player_dug": bool(path) and len(dug_by_player) == len(
            [p for p in path if p != tuple(kill["kill_from"])]),
        "kill_path_cells_pre_existing": len(path) - len(dug_by_player),
        "first_kill_cell_dug_at_turn": first_dug,
        "dig_to_death_turns": (st["turn"] - first_dug
                               if first_dug is not None else None),
        "hazard_index": kill.get("hazard_index"),
        "measured_from": "the recorded death on THIS trace",
    }


def facets_from_trace(level, trace, budget):
    """BOTH FACETS, ONE TRACE.  This is the only entry point the scorer uses.

    A second event is not a second facet: both dicts below are computed from
    the same list object, and both carry that list's digest, so a reader can
    check the claim rather than take it.
    """
    d = trace_digest(trace)
    f1 = facet_destruction(level, trace, budget)
    f2 = facet_hazard(level, trace)
    f1["trace_sha256"] = d
    f2["trace_sha256"] = d
    return {"facet1_destruction": f1, "facet2_hazard_aware": f2,
            "trace_sha256": d, "one_trace": True}


# ---------------------------------------------------------------------------
# 5. FEEDING ANSWERS -- where the reader and the transition function meet
# ---------------------------------------------------------------------------

class Attempt(object):
    """One entrant, one level.  Owns the counters and the trace."""

    def __init__(self, level, budget):
        # [A14] the turn budget is a DECLARED instrument parameter (30 by
        # default), written into every bundle.  Two runs with different
        # budgets are not comparable: `attempted`, `blocked` and facet 1b
        # all move with it.
        self.level = level
        self.budget = budget
        self.state = State(level)
        self.emitted = 0          # answers the entrant PRODUCED      [B1]
        self.consumed = 0         # answers the game actually TOOK     [B1]
        self.after_end = 0
        self.blocked = 0
        self.dug = 0
        self.moved = 0
        self.collected = 0
        self.not_an_action = 0
        self.give_up = 0
        self.gave_up = False
        self.gave_up_at = None
        self.over_budget = False
        self.trace = []
        self.rules_fired = {}

    @property
    def over(self):
        return self.state.over or self.gave_up or self.over_budget

    def _count_rule(self, name):
        self.rules_fired[name] = self.rules_fired.get(name, 0) + 1

    def _record_state(self, ply):
        """The per-ply state the facets are read from.  Everything the two
        facet functions need is written here, once, by the instrument."""
        s = self.state
        comp = hazard_component(self.level, s.tunnels, s.player)
        ply["state_after"] = dict(
            s.as_record(),
            dug_by_player=[list(c) for c in sorted(s.dug)],
            hazard_component_size=len(comp),
            hazard_component_includes_player=any(h in comp
                                                 for h in s.hazards),
            min_moves_to_complete=min_moves_to_complete(s),
        )

    def feed(self, raw):
        """Read ONE raw answer and, if it is an action, EXECUTE it.

        The answer is never checked by reading it and comparing it to a plan;
        it is executed and the board decides [A16].  The solver's optimal plan
        is recorded as a fact about the LEVEL and is never used to judge an
        entrant: level 02's optimum is a fact, "the plan" is not.
        """
        reading = read_answer(raw)
        self.emitted += 1
        self._count_rule(reading.rule_fired)
        ply = {"turn": self.emitted, "answers_emitted": self.emitted,
               "reading": reading.as_record()}

        if self.over:
            # [B1] emitted, not consumed.  Counted, never played, and NOT
            # folded into not_an_action: a legal "R" after the end is not a
            # malformed answer.
            self.after_end += 1
            ply.update(outcome="after_end", word=None)
            self.trace.append(ply)
            return ply

        self.consumed += 1

        if reading.outcome == OUTCOME_GIVE_UP:
            # [U5] abstaining is the ONLY way to stop, and it ENDS the
            # attempt.  There is no pass action.
            self.give_up += 1
            self.gave_up = True
            self.gave_up_at = self.emitted
            ply.update(outcome="give_up", word="give_up",
                       position=list(self.state.player))
            self.trace.append(ply)
            self._cap()
            return ply

        if reading.outcome == OUTCOME_NOT_AN_ACTION:
            self.not_an_action += 1
            ply.update(outcome="not_an_action", word="not_an_action",
                       position=list(self.state.player))
            self.trace.append(ply)
            self._cap()
            return ply

        before = self.state
        s, word, events = turn(before, reading.action)
        self.state = s
        # [A17] THE COUNTERS COME FROM THE STATE CHANGE, NOT FROM THE WORD.
        #
        # The first build counted the word, and a move that killed the player
        # reported the word "killed" -- so the cell it dug on the way in never
        # reached the `dug` counter and the wall it bumped never reached
        # `blocked`, while the board in the same record showed both.  The
        # counter and the board disagreed by one on every fatal move, and the
        # disagreement was found by a SECOND implementation, not by reading
        # the first one.  dug + moved + blocked now partitions the action
        # answers exactly, and `collected` counts a subset of them.
        if s.player == before.player:
            self.blocked += 1
        elif s.dug != before.dug:
            self.dug += 1
        else:
            self.moved += 1
        if word == "collected":
            self.collected += 1
        dug_cell = None
        if s.dug != before.dug:
            dug_cell = list(sorted(s.dug - before.dug)[0])
        ply.update(outcome=word, word=word, action=reading.action,
                   events=events, position=list(s.player),
                   hazards=[list(h) for h in s.hazards],
                   dug_cell=dug_cell,
                   targets_left=len(s.targets_left),
                   board=render(s),
                   kill_path=(s.kill or {}).get("path"),
                   kill_from=(s.kill or {}).get("hazard_from"),
                   hazard_index=(s.kill or {}).get("hazard_index"))
        self._record_state(ply)
        self.trace.append(ply)
        self._cap()
        return ply

    def _cap(self):
        """[A14] THE CAP IS ON ANSWERS EMITTED, not on game turns.

        The game clock advances only on an answer that resolves to an action,
        so a cap on turns alone would never be reached by an entrant that
        emits nothing but malformed answers -- the runner would ask it
        forever.  That is a hang, and it was found by running the field, not
        by reading the code.  An unreadable answer is a wasted turn: it costs
        the same budget a move would have cost.
        """
        if self.emitted >= self.budget and not self.over:
            self.over_budget = True

    def terminal(self):
        if self.state.solved:
            return "SOLVED"
        if self.state.dead:
            return "KILLED"
        if self.gave_up:
            return "GAVE_UP"
        if self.over_budget:
            return "BUDGET_EXHAUSTED"
        return "UNSOLVED"

    def facets(self):
        return facets_from_trace(self.level, self.trace, self.budget)

    def result(self):
        f = self.facets()
        return {
            "level": self.level.name,
            "level_sha256": self.level.sha256,
            "solved": self.state.solved,
            "terminal": self.terminal(),
            "turns_used": self.state.turn,
            "budget": self.budget,
            "answers_emitted": self.emitted,
            "answers_consumed": self.consumed,
            "answers_after_end": self.after_end,
            "blocked": self.blocked,
            "dug": self.dug,
            "moved": self.moved,
            "collected": self.collected,
            "not_an_action": self.not_an_action,
            "give_up": self.give_up,
            "gave_up_at": self.gave_up_at,
            "died_at_turn": (self.state.turn if self.state.dead else None),
            "rules_fired": dict(self.rules_fired),
            "final_board": render(self.state),
            "kill": self.state.kill,
            "facets": f,
            "trace": self.trace,
        }


def play(level, tokens, budget=30):
    """Play a whole stream.  The WHOLE stream is consumed; tokens emitted
    after the attempt ended are counted in `after_end` and not played [B1]."""
    a = Attempt(level, budget)
    for tok in tokens:
        a.feed(tok)
    return a.result()


def min_moves_to_complete(state):
    """The exact fewest moves that could still finish the level.

    Moving into soil costs ONE move -- the same as moving through a tunnel --
    and digging never blocks anything, so what has been dug is irrelevant to
    this number: it is the rock-free distance from the player to the nearest
    remaining target.  Exact, not a heuristic, and that is why facet 1b can
    say RUINED rather than PROBABLY RUINED.  [A9]
    """
    if not state.targets_left:
        return 0
    lvl = state.level
    dist = {state.player: 0}
    q = deque((state.player,))
    while q:
        cur = q.popleft()
        for _d, n in _neighbours(lvl, cur):
            if n not in dist:
                dist[n] = dist[cur] + 1
                q.append(n)
    best = None
    for t in state.targets_left:
        d = dist.get(t)
        if d is not None and (best is None or d < best):
            best = d
    return best


# ---------------------------------------------------------------------------
# 6. THE PROMPT -- what the entrant is allowed to see
# ---------------------------------------------------------------------------

LEGEND = ("The board is underground.  A hash sign is rock: you cannot move "
          "into it and you cannot dig it.  A percent sign is soil: you cannot "
          "walk through it, but you can move into it and that digs it, and "
          "dug ground is a tunnel forever - it never becomes soil again.  A "
          "space is a tunnel that is already open.  A capital T is a target "
          "buried in the soil and an asterisk is a target standing in an open "
          "tunnel; you collect a target by moving into its cell, and "
          "collecting the last one finishes the level.  A capital H is a "
          "hazard.  A hazard cannot dig.  It moves one cell per turn, after "
          "you have moved, and only through tunnels - so every tunnel you dig "
          "is also a road it can reach you by, and you cannot close a road "
          "you have opened.  If a hazard ends a turn in your cell, you are "
          "dead.  P is you, and X is you and a hazard in the same cell.")

#: The prompt is prose.  No schema, no key-value framing, no JSON example, no
#: "fill in" language: a legend formatted as key-value pairs reads as a FORM
#: to a schema-filling model, and that model transcribes the prompt instead
#: of playing.  The prohibition is measured by check_prompt_legal(), not
#: asserted in a comment.
FORBIDDEN_IN_PROMPT = ("schema", "json", "key-value", "fill in", "field:",
                       "key:", "value:", "{", "}", "```")

ANSWER_SHAPE = ("Answer with exactly one character on one line: U, D, L or R. "
                "Nothing else on the line.  More than one letter is not read "
                "as the first letter - it is counted as a malformed answer. "
                "If the level cannot be finished, answer with one of these "
                "and the attempt ends: ")


def build_prompt(level, state, history, budget):
    """[A13] The turn prompt.  Prose legend, the board, the answer shape,
    the budget.

    The entrant sees the board, the turn number, the move history and how
    many turns are left.  It does NOT see `min_moves_to_complete`, the
    hazard's intended move, or whether a safe line still exists: those are
    the instrument's diagnostics, and showing them would measure the
    instrument's advice instead of the entrant's planning.
    """
    tokens = " / ".join(digdug_reader.GIVE_UP_TOKENS)
    hist = " ".join(history) if history else "(you have not moved yet)"
    head = "DIG DUG -- the soil.\n\n" + LEGEND + "\n\n"
    body = ("Level: %s.  Targets left: %d.  Turn %d of at most %d.\n\n"
            "The board now:\n%s\n\n"
            "Your moves so far: %s\n\n"
            % (level.name, len(state.targets_left), state.turn + 1, budget,
               render(state), hist))
    return head + body + ANSWER_SHAPE + tokens + "\n"


def check_prompt_legal(prompt):
    """-> (ok, offenders).  A control, not a comment."""
    low = prompt.lower()
    bad = [w for w in FORBIDDEN_IN_PROMPT if w.lower() in low]
    return (not bad, bad)


# ---------------------------------------------------------------------------
# 7. CONTROLS
# ---------------------------------------------------------------------------

class _C(object):
    def __init__(self):
        self.n = 0
        self.fails = []
        self.group = ""

    def g(self, name):
        self.group = name
        print("  [%s]" % name)

    def ok(self, cond, label, seen=None):
        self.n += 1
        if cond:
            print("ok   %s" % label)
        else:
            extra = "" if seen is None else "   (got %r)" % (seen,)
            print("FAIL %s%s" % (label, extra))
            self.fails.append("%s :: %s%s" % (self.group, label, extra))
        return bool(cond)


def self_test(levels_dir=None):
    """The controls.  Every one of them can fail, and the ones that guard a
    standing rule say which rule they guard."""
    c = _C()
    extra = (levels_dir,) if levels_dir else ()
    L1 = find_level("01_first_blood.txt", extra)
    L2 = find_level("02_the_long_way_round.txt", extra)
    L3 = find_level("03_the_open_door.txt", extra)
    L4 = find_level("04_no_safe_line.txt", extra)

    # -- [0] the levels on disk are the levels in the record ----------------
    c.g("0 levels")
    import json
    tasks_path = os.path.join(HERE, "tasks", "digdug_v1.json")
    tasks = None
    if os.path.isfile(tasks_path):
        with open(tasks_path) as fh:
            tasks = json.load(fh)
    if tasks:
        for item in tasks["levels"]:
            lvl = find_level(item["file"], extra)
            c.ok(lvl.sha256 == item["sha256"],
                 "%s digest matches tasks/digdug_v1.json" % item["file"],
                 lvl.sha256)
    else:
        c.ok(False, "tasks/digdug_v1.json exists")
    c.ok(all(l.enclosed for l in (L1, L2, L3, L4)),
         "B2: enclosure is MEASURED true on every level",
         [l.enclosed for l in (L1, L2, L3, L4)])
    c.ok(L1.n_targets >= 1 and L1.n_hazards >= 1,
         "U3: every level has at least one target and one hazard")

    # -- [1] parse and malformed -------------------------------------------
    c.g("1 parse / malformed")
    for bad, why in (("", "empty"), ("   \n  ", "whitespace"),
                     ("###\n#@#\n###", "zero targets and zero hazards"),
                     ("###\n#P#\n###", "zero targets"),
                     ("#####\n#P%T#\n#####", "zero hazards"),
                     ("#####\n#P%T#Q\n#####", "illegal character"),
                     ("####\n#P%T#H#\n####", "ragged rows are padded, not "
                                             "fatal -- see the next control")):
        if why.startswith("ragged"):
            continue
        try:
            parse_level(bad, "<probe>")
            c.ok(False, "malformed rejected: %s" % why)
        except MalformedLevel:
            c.ok(True, "malformed rejected: %s" % why)
    rag = parse_level("#####\n#P%T#\n#H#####\n", "<ragged>")
    c.ok(rag.ragged is True, "A4: a ragged level is PADDED WITH ROCK and the "
                             "fact is recorded", rag.ragged)
    c.ok((0, 5) in rag.walls and (1, 6) in rag.walls,
         "A4: the padding is rock, not soil", sorted(rag.walls)[:8])
    two = "#####\n#P@T#\n#####"
    try:
        parse_level("#####\n#PP%T#\n#####", "<two players>")
        c.ok(False, "two players rejected")
    except MalformedLevel:
        c.ok(True, "two players rejected")

    # -- [2] step(): the frozen contract ------------------------------------
    c.g("2 step() -- the frozen contract")
    s0 = State(L1)
    out = step(s0, "R")
    c.ok(isinstance(out, tuple) and len(out) == 2,
         "step() returns TWO values, not three", len(out))
    s1, w1 = out
    c.ok(w1 == "dug", "moving into soil says 'dug'", w1)
    c.ok(s0.player == L1.player_start and not s0.dug,
         "A2: step() is PURE -- the state it was given is untouched",
         (s0.player, s0.dug))
    c.ok(s1 is not s0, "A2: the returned state is a NEW object")
    c.ok(s1.player == (1, 2) and (1, 2) in s1.dug,
         "the dug cell is recorded as dug BY THE PLAYER", s1.dug)
    c.ok((1, 2) in s1.tunnels, "a dug cell is a tunnel")
    s2, w2 = step(s1, "L")
    c.ok(w2 == "moved", "moving back into a tunnel says 'moved'", w2)
    c.ok((1, 2) in s2.dug, "digging is PERMANENT -- the cell stays dug "
                           "after the player leaves it", s2.dug)
    _sb, wb = step(s0, "U")
    c.ok(wb == "blocked", "moving into rock says 'blocked'", wb)
    c.ok(_sb.player == s0.player,
         "a blocked move moves nobody, and the position returned is the "
         "player's own")
    try:
        step(s0, "X")
        c.ok(False, "A6: an unresolved letter RAISES, it is not folded "
                    "into 'blocked'")
    except ValueError:
        c.ok(True, "A6: an unresolved letter RAISES, it is not folded "
                   "into 'blocked'")
    for w in STEP_WORDS:
        c.ok(w in TURN_WORDS, "step's word %r is a legal turn word" % w)
    c.ok("killed" in TURN_WORDS and "killed" not in STEP_WORDS,
         "'killed' belongs to turn(), never to step()")

    # -- [3] B2: bounds, in the transition function -------------------------
    c.g("3 B2 bounds in the transition function")
    open_lvl = parse_level("#####\n#P%T#\n#H% \n", "<unenclosed>")
    c.ok(open_lvl.enclosed is False,
         "B2: enclosure is MEASURED, and this level measures False",
         open_lvl.enclosed)
    so = State(open_lvl)
    for _ in range(6):
        so, wo = step(so, "D")
    c.ok(wo == "blocked" and so.player[0] <= open_lvl.height - 1,
         "B2: out of bounds is 'blocked' in step(), never a walk off the "
         "board", (wo, so.player))
    c.ok(all(0 <= p[0] < open_lvl.height and 0 <= p[1] < open_lvl.width
             for p in [so.player]),
         "B2: the player is still inside the board after 6 downs")

    # -- [4] the turn: order, clock, death ----------------------------------
    c.g("4 turn() -- the frozen order")
    t0 = State(L2)
    t1, w, ev = turn(t0, "R")
    c.ok(t1.turn == 1, "turn() advances the clock once", t1.turn)
    c.ok(t1.hazards == t0.hazards,
         "a hazard with no tunnel route to the player does not move",
         t1.hazards)
    tb, wb2, _ = turn(t0, "U")
    c.ok(tb.turn == 1, "A8: a BLOCKED move still costs the turn", tb.turn)
    # digging the cell next to the hazard releases it, and it arrives
    t2, _, _ = turn(t1, "R")
    c.ok(t2.dead and t2.player == (1, 3),
         "U4: digging the cell beside a hazard lets it arrive on the same "
         "turn -- the player at (1,3) is dead", (t2.dead, t2.player))
    c.ok(t2.kill is not None and t2.kill["hazard_from"] == [1, 4],
         "the death record names the hazard and where it came from",
         t2.kill)
    # moving INTO a hazard's cell: the hazard need not move at all
    sw = parse_level("######\n#P H%T#\n######", "<into-hazard>")
    sw = State(sw, dug=frozenset(((1, 2), (1, 3))))
    sw2, wsw, _ = turn(sw, "R")
    c.ok(sw2.dead and wsw == "killed",
         "U4: moving INTO a hazard's cell is a death even though the hazard "
         "does not move -- the check runs after the clock",
         (wsw, sw2.player, sw2.hazards))
    # A1: hazards never dig.  On level 01 the hazard has three soil
    # neighbours it could dig through to reach the player; it does not.
    hz = Attempt(L1, 30)
    for _ in range(4):
        hz.feed("R")
    c.ok(hz.state.hazards == L1.hazard_starts,
         "A1: a sealed hazard does not dig its way out -- it is still where "
         "the level put it", hz.state.hazards)
    c.ok(len(hz.state.dug) == 4 and
         all(cell in L1.soil for cell in hz.state.dug),
         "A1: the tunnel set only ever grows by the PLAYER's digging",
         sorted(hz.state.dug))
    c.ok(hz.state.tunnels == L1.open | hz.state.dug,
         "A1: tunnels = what was open at t=0 + what the player dug, nothing "
         "else")

    # -- [5] U7: collection ends the attempt before the clock ---------------
    c.g("5 U7 collection ends the attempt before the hazard clock")
    col = parse_level("#####\n#PHT#\n#####", "<collect>")
    cs = State(col, dug=frozenset(((1, 2),)))
    # hazard at (1,2)? no: H at (1,2), T at (1,3). Player at (1,1) is boxed.
    col2 = parse_level("######\n#PT H#\n######", "<collect2>")
    cs2 = State(col2)
    cs2, w3, ev3 = turn(cs2, "R")
    c.ok(cs2.solved and w3 == "collected",
         "U7: collecting the last target ends the attempt", (cs2.solved, w3))
    c.ok(cs2.hazards == col2.hazard_starts,
         "U7: ... and the hazards do NOT move on the collecting turn",
         cs2.hazards)
    c.ok("solved" in ev3, "the events list says so", ev3)

    # -- [6] R1/R3: the reader ---------------------------------------------
    c.g("6 R1/R3 the reader")
    agrees, detail = contract_agrees_with_code(CONTRACT)
    c.ok(agrees, "R1: the CONTRACT's token list EQUALS the code's scored "
                 "list (%d tokens)" % detail.get("code_count", -1),
         detail.get("why"))
    c.ok(not detail.get("uniqueness_problems"),
         "B3: the token list is UNIQUE -- no duplicates, no two tokens that "
         "normalise onto each other, none colliding with an action letter",
         detail.get("uniqueness_problems"))
    probes = {
        "R": (OUTCOME_ACTION, "R", "action_letter"),
        " r ": (OUTCOME_ACTION, "R", "action_letter"),
        "RR": (OUTCOME_NOT_AN_ACTION, None, "multi_char_no_truncation"),
        "RESIGN": (OUTCOME_GIVE_UP, None, "give_up_token_exact"),
        "resign": (OUTCOME_GIVE_UP, None, "give_up_token_exact"),
        "W": (OUTCOME_NOT_AN_ACTION, None, "wasd_not_a_synonym"),
        "WAIT": (OUTCOME_NOT_AN_ACTION, None, "wait_is_not_an_action"),
        "R\nR": (OUTCOME_NOT_AN_ACTION, None, "multi_line"),
        "": (OUTCOME_NOT_AN_ACTION, None, "empty_answer"),
        "I give up, there is no way to finish this one.":
            (OUTCOME_NOT_AN_ACTION, None, "multi_char_no_truncation"),
    }
    for raw, (o, a, rule) in probes.items():
        r = read_answer(raw)
        c.ok(r.outcome == o and r.action == a and r.rule_fired == rule,
             "read_answer(%r) -> %s/%s" % (raw, o, rule),
             (r.outcome, r.action, r.rule_fired))
    soft = read_answer("I give up, there is no way to finish this one.")
    c.ok(soft.loose_give_up is True and soft.outcome == OUTCOME_NOT_AN_ACTION,
         "R1: a free-text abstention is not_an_action, and the LOOSE "
         "diagnostic sees it -- recorded, never scored")
    for tok in ("R", "RESIGN"):
        r = read_answer(tok)
        c.ok(r.rule_fired in ("action_letter", "give_up_token_exact"),
             "R1: the rule that fired is NAMED in the record (%s)" % tok,
             r.rule_fired)

    # -- [7] the prompt -----------------------------------------------------
    c.g("7 the prompt")
    p = build_prompt(L1, State(L1), [], 30)
    okp, bad = check_prompt_legal(p)
    c.ok(okp, "the prompt is prose: no schema, no JSON, no key-value", bad)
    c.ok("U, D, L or R" in p, "R3: the prompt states the ANSWER SHAPE")
    DIAGNOSTICS = ("min_moves", "safe_line", "barrier_lost", "budget_ruin",
                   "kill_path", "hazard_component", "solvable_after",
                   "safe_completion")
    leaked = [d for d in DIAGNOSTICS if d in p.lower()]
    c.ok(not leaked,
         "the instrument's diagnostics are NOT shown to the entrant -- the "
         "prompt never says whether a safe line is left", leaked)
    import digdug_reader
    c.ok(all(t in p for t in digdug_reader.GIVE_UP_TOKENS),
         "R1: the prompt offers the entrant the SAME frozen token list the "
         "code scores")

    # -- [8] the two facets, one trace --------------------------------------
    c.g("8 D -- two facets, one trace")
    res = play(L2, ["R", "R", "R"], budget=30)
    f = res["facets"]
    c.ok(f["one_trace"] is True, "both facets come from one trace object")
    c.ok(f["facet1_destruction"]["trace_sha256"] ==
         f["facet2_hazard_aware"]["trace_sha256"] == f["trace_sha256"],
         "both facet records cite the SAME trace digest",
         (f["facet1_destruction"]["trace_sha256"][:8],
          f["facet2_hazard_aware"]["trace_sha256"][:8]))
    c.ok(f["facet1_destruction"]["facet_id"] == 1 and
         f["facet2_hazard_aware"]["facet_id"] == 2,
         "the record says which facet each number belongs to")
    c.ok(f["facet2_hazard_aware"]["killed"] is True and
         f["facet2_hazard_aware"]["kill_path_cells_dug_by_player"] >= 1,
         "facet 2 sees the death and how much of the killing road the "
         "player dug", f["facet2_hazard_aware"])
    c.ok(f["facet1_destruction"]["barrier_lost_at_turn"] is not None,
         "facet 1 sees the barrier go, on the same trace",
         f["facet1_destruction"]["barrier_lost_at_turn"])

    # -- [9] U1 corollary: digging never removes a route --------------------
    c.g("9 U1 corollary -- digging never removes a route")
    for lvl in (L1, L2, L3, L4):
        before = min_moves_to_complete(State(lvl))
        s = State(lvl)
        worst = before
        # dig everything reachable, in a fixed order, and watch the distance
        for cell in sorted(lvl.soil):
            s = s.copy(dug=s.dug | {cell})
            d = min_moves_to_complete(s)
            if d is not None and (worst is None or d > worst):
                worst = d
        c.ok(worst == before,
             "%s: digging EVERY cell never lengthens the route to the "
             "target (%s -> %s)" % (lvl.name, before, worst), worst)

    # -- [10] the freeze ----------------------------------------------------
    c.g("10 E -- the frozen contract")
    import freeze
    ok, why = freeze.verify()
    c.ok(ok, "the contract on disk IS the frozen contract (digest)", why)
    rec = freeze.read_record()
    c.ok(rec is not None and rec.get("combined_digest"),
         "FROZEN.json carries a combined digest", None if not rec else
         rec.get("combined_digest", "")[:12])
    c.ok(rec is not None and rec.get("contract_sha256"),
         "FROZEN.json carries the CONTRACT's own digest")
    # the mechanism, exercised: perturb the normative set and watch it refuse
    saved = freeze.NORMATIVE
    try:
        probe_path = os.path.join(HERE, "_freeze_probe.txt")
        with open(probe_path, "w") as fh:
            fh.write("perturbation\n")
        freeze.NORMATIVE = saved + (("_freeze_probe.txt", "probe"),)
        ok2, why2 = freeze.verify()
        c.ok(not ok2 and "NOT FROZEN" in why2,
             "E: a normative file added after the freeze is REFUSED, not "
             "ignored", why2)
    finally:
        freeze.NORMATIVE = saved
        if os.path.exists(probe_path):
            os.remove(probe_path)
    ok3, why3 = freeze.verify()
    c.ok(ok3, "E: and the tree verifies again once the probe is gone", why3)

    # -- [11] B3: the uniqueness counter can say more than one --------------
    c.g("11 B3 -- uniqueness, not only count")
    import digdug_solve
    multi = parse_level("######\n#P%%%#\n#%%%#H\n#%%%T#\n######", "<multi>")
    r = digdug_solve.Search().optimal(multi)
    c.ok(r["optimal_moves"] == 5,
         "the probe level's optimum is 5", r["optimal_moves"])
    c.ok(r["n_distinct_optimal_lines"] > 1,
         "B3: the counter reports MORE THAN ONE optimal line when there is "
         "more than one (a validator that only counts would say 1)",
         r["n_distinct_optimal_lines"])
    one = digdug_solve.Search().optimal(L2)
    c.ok(one["n_distinct_optimal_lines"] == 1,
         "B3: and it reports ONE when there is one -- level 02's safe line is "
         "unique", one["n_distinct_optimal_lines"])

    # -- [12] the exit codes, driven by real runs ---------------------------
    c.g("12 exit codes -- driven, not read")
    import digdug_run
    tasks = digdug_run.load_tasks()
    gpu = digdug_run.probe_gpu()
    codes = {}
    for name in sorted(digdug_run.ENTRANTS):
        if name == "model":
            continue
        ent = digdug_run.ENTRANTS[name]()
        res = digdug_run.run_entrant(ent, tasks, out_dir=None,
                                     reasoning="off", gpu=gpu,
                                     trace_boards=False)
        codes[name] = res["exit_code"]
    for name, code in sorted(codes.items()):
        c.ok(code in digdug_run.EXIT_CODES,
             "runner exits %d for entrant %r" % (code, name), code)
    c.ok(codes.get("garbage") == digdug_run.EXIT_ZERO_MEASURED,
         "ZERO RULE: an entrant with no readable answer exits 2, an ERROR, "
         "never a verdict of 0.00", codes.get("garbage"))
    c.ok(codes.get("soft-resigner") == digdug_run.EXIT_ZERO_MEASURED,
         "R1: a free-text abstention exits 2 -- the instrument's own failure "
         "to read, filed as an error and not as a score",
         codes.get("soft-resigner"))
    c.ok(codes.get("never-starts") == digdug_run.EXIT_NEVER_STARTED,
         "an entrant that never loaded exits 4, counted separately from "
         "played-and-failed", codes.get("never-starts"))
    c.ok(all(v != digdug_run.EXIT_INSTRUMENT for v in codes.values()),
         "no entrant's run exits 1 -- 1 is reserved for an UNPROVEN "
         "INSTRUMENT, not for a run that failed")
    c.ok(codes.get("reference") == digdug_run.EXIT_SCORED,
         "the reference solver exits 0", codes.get("reference"))
    unk = type("A", (), {"entrant": "no-such-entrant", "out": None,
                         "budget": 30, "reasoning": "off",
                         "model_path": None,
                         "server_url": "http://127.0.0.1:8080"})()
    c.ok(digdug_run.cmd_run(unk) == digdug_run.EXIT_USAGE,
         "an unknown entrant exits 3, not 0 and not 1")

    print()
    if c.fails:
        print("SELF-TEST FAIL -- %d/%d, %d failed" % (c.n - len(c.fails),
                                                      c.n, len(c.fails)))
        for f_ in c.fails:
            print("     %s" % f_)
        return 1
    print("SELF-TEST PASS -- %d/%d" % (c.n, c.n))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="the DIG DUG cabinet simulator")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--level")
    ap.add_argument("--moves", default="")
    ap.add_argument("--budget", type=int, default=30)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.level:
        lvl = find_level(a.level)
        toks = [t for t in a.moves.replace(",", " ").split()]
        res = play(lvl, toks, budget=a.budget)
        import json
        out = {k: v for k, v in res.items() if k != "trace"}
        print(json.dumps(out, indent=1, sort_keys=True))
        if a.show:
            for ply in res["trace"]:
                print("turn %s %s -> %s" % (ply["turn"],
                                            ply.get("action"), ply.get("word")))
        return 0 if res["solved"] else 2
    ap.print_help()
    return 3


if __name__ == "__main__":
    sys.exit(main())
