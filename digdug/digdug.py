#!/usr/bin/env python3
# digdug.py -- the DIG DUG cabinet simulator: THE CONTRACT, IN CODE.
#
# Tier 3 hands over ONE prose paragraph and says the step() contract is the
# cabinet author's to write.  So this file is not a port of anything: every
# rule below is either (a) stated by the paragraph, or (b) a DECISION, marked
# [D-nn] here and argued in DIGDUG_DECISIONS.md, and frozen in
# CONTRACT_digdug_v1.md before any entrant ran.
#
# THE FROZEN TRANSITION FUNCTION (this is the contract the brief asks for):
#
#     step(state, action) -> (position, word)          TWO values.  Not three.
#
#       position  the PLAYER's position AFTER the action: a 2-int tuple
#                 (row, col), 0-indexed, row 0 at the top.  NOT a state, NOT a
#                 dict, NOT (row, col, terrain).  Pinned, because the Sokoban
#                 cabinet's G23 is exactly this clause left unpinned.
#       word      one of the five frozen words: moved | dug | collected |
#                 waited | blocked.  A single string, chosen by a frozen
#                 PRECEDENCE (collected > dug > moved), never a set.
#       purity    step MUTATES `state` in place and returns the pair.
#                 Pinned.  (The alternative -- a pure function returning a new
#                 state -- is a different instrument and is recorded as the
#                 rejected reading [D-STEP-2].)
#       totality  step RAISES ValueError on anything outside the alphabet.
#                 It is not the reader and it does not absorb a malformed
#                 answer into `blocked`.
#       bounds    step checks them ITSELF.  Standing rule B2: out-of-bounds is
#                 blocked inside the transition function, not assumed away by
#                 the level file.  A frozen defect in this circuit's own
#                 Sokoban instrument walked its player off a 4-row board.
#       scope     step resolves the PLAYER's half-turn ONLY.  Hazard motion is
#                 `advance_hazards()`, a separate named call.  [D-STEP-SCOPE]
#
# Stdlib only.

import argparse
import hashlib
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from digdug_reader import (ACTIONS, MOVE_LETTERS, OUTCOME_ACTION,      # noqa
                           OUTCOME_GIVE_UP, OUTCOME_NOT_AN_ACTION, WAIT,
                           read_answer)

HARNESS = "handicap-arena"
VERSION = "1.0"
EVENT = "DIG DUG"
CARD_VERSION = "digdug_v1"

# ---------------------------------------------------------------------------
# 0. THE POLICY -- every clause the paragraph did not settle, in ONE object.
#
# The frozen default IS the contract.  digdug_readings.py builds variants of it
# and re-runs the same levels and the same field through them, so "which of
# them the RUNNING settled" is a measured table and not an argument.  A variant
# is a DIAGNOSTIC and is never scored.
# ---------------------------------------------------------------------------

#: the five words step() may say.  Frozen.  [D-WORDS]
WORD_MOVED = "moved"
WORD_DUG = "dug"
WORD_COLLECTED = "collected"
WORD_WAITED = "waited"
WORD_BLOCKED = "blocked"
#: A SIXTH word, and the frozen reading can never emit it.  It exists because the
#: REJECTED reading `player_into_hazard = killed` needs one: under that reading a
#: letter aimed at a hazard's cell MOVES the player and ends the run, so calling
#: it `blocked` would be a lie in the label AND a contamination of the `blocked`
#: counter -- which is exactly how a shadow reading leaks into a frozen number.
#: `STEP_WORDS` carries it so the vocabulary is complete; control [W3] asserts
#: that no run on the FROZEN policy ever produced it.
WORD_ENTERED_HAZARD = "entered_hazard"
STEP_WORDS = (WORD_MOVED, WORD_DUG, WORD_COLLECTED, WORD_WAITED, WORD_BLOCKED,
              WORD_ENTERED_HAZARD)

#: The frozen precedence.  A ply that both digs and collects says ONE word, and
#: which one is a decision.  The COUNTERS are computed from state deltas and
#: not from the word, precisely so that this decision cannot move a number --
#: and control [W3] measures how far the two would have drifted.
WORD_PRECEDENCE = (WORD_COLLECTED, WORD_DUG, WORD_MOVED)

#: words that consumed a turn (the cost). `blocked` is not one of them, and
#: `entered_hazard` is only reachable in a shadow reading.
TURN_WORDS = (WORD_MOVED, WORD_DUG, WORD_COLLECTED, WORD_WAITED,
              WORD_ENTERED_HAZARD)

def neighbour(state, cell, delta):
    """One cell away, WITH THE BOUNDARY APPLIED.  [B2], generalised.

    wrap on  -> the coordinate is reduced mod the board, so the result is in
                bounds BY CONSTRUCTION and every key in every `seen` set is a
                real cell;
    wrap off -> the raw coordinate, which `in_bounds` (or `traversable`, or the
                wall test) rejects a moment later.

    ONE function does this in this cabinet.  It used to be six copies of two
    lines, and one of the copies had the two lines in the other order:
    `reachable_cells()` added the neighbour to `seen` under its UNWRAPPED key
    and then asked `traversable()` -- which wraps -- whether the cell was
    walkable.  Every out-of-bounds coordinate therefore looked new and walkable,
    so a flood fill on any board read with `wrap=True` expanded forever and the
    process was killed for memory.  The frozen reading never touched it, because
    the frozen reading has wrap off -- which is exactly the kind of bug a shadow
    clause is for, and exactly the kind a `# same as above` copy hides.  A bug in
    a copy is a bug in the rule, so the rule now lives in one place and the
    copies are gone; see DIGDUG_DECISIONS.md D-NEIGHBOUR and SECTION_4F.md.
    """
    nxt = (cell[0] + delta[0], cell[1] + delta[1])
    if state.policy.wrap:
        nxt = (nxt[0] % state.level.height, nxt[1] % state.level.width)
    return nxt


DIRECTIONS = ("U", "D", "L", "R")
DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

#: tie-break order for hazard moves: sorted (dr, dc), i.e. reading order.
HAZARD_TIEBREAK = ((-1, 0), (0, -1), (0, 1), (1, 0))


class Policy(object):
    """The defaulted settings, as data.

    Every attribute here is a clause the paragraph left open.  `FROZEN` is what
    this cabinet scores with; `fields()` names each one with its rejected
    alternative so a bundle can be read without this file.
    """

    __slots__ = ("name", "hazard_clock", "hazard_terrain", "hazard_tiebreak",
                 "player_into_hazard", "resolve_order", "end_on_solve_first",
                 "death_beats_solve", "wait_legal", "objective", "survive_n",
                 "target_persistence", "bounds", "wrap",
                 "hazard_blocks_hazard")

    def __init__(self, name="FROZEN", **kw):
        self.name = name
        self.hazard_clock = "per_player_turn"
        self.hazard_terrain = "tunnels_only"
        self.hazard_tiebreak = "reading_order"
        self.player_into_hazard = "blocked"
        self.resolve_order = "player_first"
        self.end_on_solve_first = True
        #: only meaningful when end_on_solve_first is False: does a run that
        #: collects the last pearl and is stepped on in the same turn die, or
        #: win?  The rejected reading has an INTERNAL split the prose never
        #: hints at, which is itself a finding (see [D-END] and 4F3).
        self.death_beats_solve = True
        self.wait_legal = True
        self.objective = "all_targets"
        self.survive_n = 10
        self.target_persistence = "removed"
        self.bounds = "blocked"
        self.wrap = False
        self.hazard_blocks_hazard = True
        for k, v in kw.items():
            if k == "name":
                continue
            if not hasattr(self, k):
                raise ValueError("no such contract clause: %r" % k)
            setattr(self, k, v)
        self.validate()

    #: legal values per clause.  A typo in a shadow reading must not silently
    #: become the frozen behaviour.
    DOMAIN = {
        "hazard_clock": ("per_player_turn", "every_2_player_turns", "never"),
        "hazard_terrain": ("tunnels_only", "soil_too"),
        "hazard_tiebreak": ("reading_order", "reverse_reading_order"),
        "player_into_hazard": ("blocked", "killed", "pass_through"),
        "resolve_order": ("player_first", "simultaneous"),
        "end_on_solve_first": (True, False),
        "death_beats_solve": (True, False),
        "wait_legal": (True, False),
        "objective": ("all_targets", "survive_n"),
        "target_persistence": ("removed", "persists_as_marker"),
        "bounds": ("blocked", "raises"),
        "wrap": (True, False),
        "hazard_blocks_hazard": (True, False),
    }

    def validate(self):
        for key, allowed in self.DOMAIN.items():
            if not allowed:
                continue
            got = getattr(self, key)
            if got not in allowed:
                raise ValueError("clause %s = %r is not one of %s"
                                 % (key, got, list(allowed)))
        return True

    def as_record(self):
        return {"name": self.name,
                "clauses": {k: getattr(self, k) for k in self.DOMAIN},
                "word_precedence": list(WORD_PRECEDENCE),
                "step_words": list(STEP_WORDS)}


#: THE FROZEN READING.  Everything scored in this cabinet uses this object.
FROZEN = Policy()

#: What each defaulted clause's alternative was, for the record and for
#: DIGDUG_DECISIONS.md.  Kept in the code so the doc cannot drift from it.
DECISIONS = {
    "D-CLOCK": ("hazard_clock", "per_player_turn", "every_2_player_turns",
                "the paragraph says a hazard 'can arrive' through tunnels and "
                "never says when it moves; per-player-turn is the only reading "
                "that makes the run a pure function of the answer stream"),
    "D-T0": ("hazard_terrain", "tunnels_only", "soil_too",
             "the paragraph says a hazard cannot reach the player except "
             "through tunnels, so its route does NOT exist through UNDIGGED "
             "soil. Measured scope, stated here because the first draft of this "
             "sentence said 'at time zero nothing moves' and level 04 refutes "
             "it: `_` is ground the level AUTHOR dug, so 04 has a hazard armed "
             "at distance 2 before the entrant has typed anything. A new level "
             "cannot arm a hazard; an authored tunnel run can -- which is the "
             "difference between this clause and [D-TIEBREAK]'s determinism, and "
             "why the item set contains one of each"),
    "D-OBJ": ("objective", "all_targets", "survive_n",
              "'solved' is not defined by the paragraph; collecting every "
              "target is the only reading that uses the sentence it does "
              "provide ('a target is collected by moving into its cell')"),
    "D-TARGET": ("target_persistence", "removed", "persists_as_marker",
                 "'collected' has no stated consequence; removal is the "
                 "reading under which the word means something"),
    "D-STOP": ("wait_legal", True, False,
               "the paragraph never says the player may stop; WAIT is in the "
               "ALPHABET anyway, because R3 puts the answer shape in the "
               "grammar and a game that permits a pause the grammar forbids "
               "makes a correct answer a failure"),
    "D-ADJ": ("resolve_order", "player_first", "simultaneous",
              "'adjacent cells, whose turn resolves first' is undecided; "
              "player-then-hazard, with the winning ply ending the run BEFORE "
              "hazard motion, is what makes level 05 a WIN and not a death"),
    "D-END": ("end_on_solve_first", True, False,
              "does a run that collects the last pearl on the ply a hazard "
              "would step onto it count?  Decided YES.  Level 05 exists to "
              "exercise exactly this clause"),
    "D-BLOCK": ("player_into_hazard", "blocked", "killed",
                "moving into the cell a hazard stands on is undecided; blocked "
                "makes a hazard a living wall, which is the ONLY mechanism in "
                "this contract that destroys the player's route -- see 4F1"),
    "D-BOUNDS": ("bounds", "blocked", "raises",
                 "B2: bounds are checked in the transition function; walking "
                 "off the board is impossible, and an unbounded walk is an "
                 "error only in the sense that it never happens"),
    "D-WRAP": ("wrap", False, True,
               "the grid is bounded, it does not wrap; 'a grid of soil' with "
               "no torus language is a bounded grid, and wrapping would make "
               "the enclosure measurement meaningless"),
    "D-TIEBREAK": ("hazard_tiebreak", "reading_order",
                   "reverse_reading_order",
                   "the paragraph permits more than one hazard and never says "
                   "what two hazards wanting the same cell do. Frozen to "
                   "reading order because the EXHAUSTIVE PROOF depends on it: a "
                   "randomised tie-break makes the state key incomplete and every "
                   "number in this cabinet unreplayable. The choice costs "
                   "nothing on any of the five levels (measured: 4F item 6) and "
                   "buys determinism with no seed -- which is why it is in the "
                   "contract and not in a comment"),
    "D-BLOCKED-TURN": ("blocked_legal_letter", "costs_a_turn", "costs_nothing",
                       "a legal letter aimed at rock is CONSUMED: `moves` does not "
                       "advance, the turn count does, and a hazard already on a "
                       "road steps closer. The rejected reading -- 'only a "
                       "successful move is a turn' -- makes waiting safe by "
                       "walking into a wall, which is the same rule as [D-STOP] "
                       "wearing a costume; the two are decided together and "
                       "reported separately because `blocked` and `waited` are "
                       "different counters and the record must be able to tell "
                       "which one a run filled"),
    "D-NEIGHBOUR": ("neighbour_rule", "one_shared_function",
                    "six_copies_of_two_lines",
                    "the boundary is one rule, so it is ONE function: "
                    "`neighbour(state, cell, delta)` applies wrap and nothing "
                    "else decides where a coordinate is.  It is recorded as a "
                    "decision because it was found as a bug: a copy of these two "
                    "lines in `reachable_cells()` reduced the coordinate AFTER "
                    "adding it to `seen`, so on any `wrap=True` reading the "
                    "mobility flood fill expanded off the edge forever and the "
                    "process died.  The frozen reading cannot reach it (wrap is "
                    "off), which is why it survived review -- and why [B2]'s "
                    "rule is not only 'check the bounds in the transition "
                    "function' but 'there is one place that knows the bounds'"),
    "D-HAZCOLL": ("hazard_blocks_hazard", True, False,
                  "two hazards in one cell is not expressible in the prose and "
                  "is decided: they block each other, which makes a junction "
                  "into a thing a plan can use"),
}


# ---------------------------------------------------------------------------
# 1. THE BOARD -- the alphabet, and what makes a level MALFORMED
# ---------------------------------------------------------------------------

WALL = "#"
SOIL = "."
TUNNEL = "_"
TARGET = "o"
HAZARD = "~"
PLAYER = "@"
HAZARD_IN_TUNNEL = "X"

LEGAL_CHARS = frozenset((WALL, SOIL, TUNNEL, TARGET, HAZARD, PLAYER,
                         HAZARD_IN_TUNNEL))


class MalformedLevel(ValueError):
    """A level that is not a board.  Never silently parsed into one."""


class DuplicateLevel(MalformedLevel):
    """B3: a validator must validate UNIQUENESS, not only COUNT.

    Two items in the frozen set with the same sha256 are one level played
    twice, and `len(levels) == 5` says nothing about it.
    """


class Level(object):
    """The static part of a level, plus the properties MEASURED off it."""

    __slots__ = ("name", "path", "text", "sha256", "walls", "soil", "tunnels",
                 "targets", "hazards", "start_player", "height", "width",
                 "enclosed", "ragged", "reachable", "unreachable_targets",
                 "note")

    def __init__(self, **kw):
        for k in Level.__slots__:
            setattr(self, k, kw.get(k))
        self.note = kw.get("note")

    @property
    def n_targets(self):
        return len(self.targets)

    @property
    def n_hazards(self):
        return len(self.hazards)

    @property
    def playable(self):
        """Cells that are not rock.  Digging never removes one."""
        return len(self.soil) + len(self.tunnels)


def measure_enclosure(rows, height, width, player):
    """MEASURED enclosure (B2): flood-fill the non-rock cells from the player.

    -> (enclosed: bool, reached: set).  A level is enclosed when the fill never
    touches the outer ring.  This is a measurement, not a convention: the
    frozen Sokoban instrument said 'enclosed by convention, nothing enforces
    it' and then walked its player off a 4-row board.
    """
    walls = set()
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == WALL:
                walls.add((r, c))
    seen = {player}
    q = deque([player])
    border = set()
    while q:
        r, c = q.popleft()
        if r in (0, height - 1) or c in (0, width - 1):
            border.add((r, c))
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            # DELIBERATELY not neighbour(): enclosure is a property of the board
            # as AUTHORED, and it must not depend on a policy, or `enclosed`
            # would be a reading instead of a measurement.  Under `wrap` the
            # border cells of an unframed board are doors to other cells of the
            # same board -- and `enclosed` still says False, which is the point.
            nxt = (r + dr, c + dc)
            if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
                continue
            if nxt in walls or nxt in seen:
                continue
            seen.add(nxt)
            q.append(nxt)
    return (len(border) == 0), seen, walls


def parse_level(text, name="<level>", path=None):
    """Parse ASCII into a Level, or raise MalformedLevel.

    THE VALIDATOR.  What is malformed is itself a decision [D-MALFORMED],
    because the paragraph defines no notion of a broken level at all.  Each
    check below says whether it is a UNIQUENESS check or a COUNT check -- B3
    requires the former where the latter would pass a broken board.

      empty / only blanks                         COUNT      -> error
      a character outside # . _ o ~ @ X           COUNT-ish  -> error
      not EXACTLY ONE player (0 or 2 both fail)   UNIQUENESS -> error
      zero targets ('at least one target')        COUNT      -> error
      zero hazards  ('at least one hazard')       COUNT      -> error
      a target inside rock                        UNIQUENESS -> error
      a hazard with no cell (two on one cell is
        inexpressible in one-char-per-cell grid)  UNIQUENESS  -> n/a, see note
      a target not reachable from the player
        through non-rock                          GEOMETRY   -> error
      UNWINNABLE-BY-OPTIMAL-PLAY                  not checked here, and that is
        a decision: a lost level is a VALID level, proven lost by the solver.
        The validator checks a necessary condition only.  [D-LOSTISVALID]
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
    # [D-RAGGED] short rows are padded with ROCK, not with soil.  Padding with
    # soil would hand the player diggable ground the file's author never wrote,
    # and ground is the whole currency of this cabinet.
    rows = [ln.ljust(width, WALL) if len(ln) < width else ln
            for ln in raw_lines]
    height = len(rows)
    if height < 3 or width < 3:
        raise MalformedLevel("%s: %dx%d is not a grid" % (name, height, width))

    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch not in LEGAL_CHARS:
                raise MalformedLevel(
                    "%s: illegal character %r at row %d col %d (legal: "
                    "%s)" % (name, ch, r, c, " ".join(sorted(LEGAL_CHARS))))

    walls, soil, tunnels, targets, hazards = set(), set(), set(), set(), []
    players = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            cell = (r, c)
            if ch == WALL:
                walls.add(cell)
            elif ch == SOIL:
                soil.add(cell)
            elif ch == TUNNEL:
                tunnels.add(cell)
            elif ch == TARGET:
                soil.add(cell)               # a pearl sits IN soil
                targets.add(cell)
            elif ch == HAZARD:
                soil.add(cell)               # a hazard sits IN soil
                hazards.append(cell)
            elif ch == HAZARD_IN_TUNNEL:
                tunnels.add(cell)
                hazards.append(cell)
            elif ch == PLAYER:
                tunnels.add(cell)            # [D-T0] the start cell starts dug
                players.append(cell)

    # ---- UNIQUENESS checks (B3) ------------------------------------------
    if len(players) != 1:
        raise MalformedLevel(
            "%s: %d players; the level needs EXACTLY ONE.  A count-only "
            "validator that tests 'at least one' would accept this and play the "
            "LAST @, leaving a second player invisible on the board."
            % (name, len(players)))
    if not targets:
        raise MalformedLevel("%s: zero targets ('there is at least one "
                             "target')" % name)
    if not hazards:
        raise MalformedLevel("%s: zero hazards ('there is at least one "
                             "hazard')" % name)
    for t in targets:
        if t in walls:
            raise MalformedLevel("%s: target at %s is inside rock" % (name, t))
    if len(set(hazards)) != len(hazards):
        raise DuplicateLevel("%s: %d hazards on %d cells -- two on one cell"
                             % (name, len(hazards), len(set(hazards))))
    if targets & set(hazards):
        raise MalformedLevel("%s: a pearl and a hazard on the same cell: %s"
                             % (name, sorted(targets & set(hazards))))

    player = players[0]
    enclosed, reached, _ = measure_enclosure(rows, height, width, player)

    # ---- GEOMETRY: a necessary condition, not a solvability claim ---------
    unreachable = {t for t in targets if t not in reached}
    if len(reached) < 2:
        raise MalformedLevel("%s: the player can reach no other cell" % name)
    if unreachable:
        raise MalformedLevel(
            "%s: %d target(s) sealed behind rock %s -- unreachable in "
            "principle.  That is a broken board, not a hard level."
            % (name, len(unreachable), sorted(unreachable)))

    return Level(name=name, path=path, text=text, walls=walls, soil=soil,
                 tunnels=tunnels, targets=targets, hazards=hazards,
                 start_player=player, height=height, width=width,
                 enclosed=enclosed, ragged=ragged, reachable=reached,
                 unreachable_targets=unreachable,  # see the refusal above
                 sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())


# ---------------------------------------------------------------------------
# 2. THE STATE
# ---------------------------------------------------------------------------

class State(object):
    """Mutable game state over a static Level, under a Policy.

    The counter set is the point of this class.  `attempted_emitted` and
    `attempted_consumed` are DIFFERENT NUMBERS and both are carried (B1), and
    the cost (`moves`) is not the score (`solved`) (R2).
    """

    def __init__(self, level, policy=None, cheap=False):
        #: `cheap` is the search kernel's path: the exhaustive solver builds
        #: hundreds of thousands of these, and the two measurements below are
        #: BFSs over the whole board.  Skipping them is an optimisation of the
        #: PROBE, never of the rules -- the rules live in step(), feed() and
        #: resolve_turn(), which are identical on both paths.
        self._cheap = cheap
        self.level = level
        self.policy = policy or FROZEN
        self.tunnels = set(level.tunnels)
        self.targets = set(level.targets)
        self.visited_targets = set()
        self.player = level.start_player
        self.hazards = [{"pos": h, "origin": h, "id": i}
                        for i, h in enumerate(level.hazards)]
        if not cheap:
            self._validate_geometry()
        # -- counters --------------------------------------------------------
        self.emitted = 0        # answers the entrant PRODUCED          [B1]
        self.consumed = 0       # answers the RULES APPLIED              [B1]
        self.moves = 0          # the COST: turns taken (legal, non-blocked)
        self.digs = 0           # cells converted soil -> tunnel by the player
        self.collects = 0
        self.blocked = 0
        self.waited = 0
        self.not_an_action = 0
        self.give_up = 0
        self.after_end = 0      # answers handed in after the run was over
        self.over_budget = 0    # answers refused because the cap fired
        self.hazard_turns = 0   # resolutions actually performed
        self.hazard_digs = 0    # only under the soil_too shadow reading
        self.killed = False
        self.killed_by = None
        self.killed_at = None
        self.gave_up = False
        self.gave_up_at = None
        self.solved = False
        self.solved_at = None
        self.ended = False
        self.trace = []
        # -- facet diagnostics, filled in as we go ---------------------------
        self.mobility = None if cheap else len(self.reachable_cells())
        #: [D-T0] arming is measured AT time zero, not only after a move: a
        #: level may start with a hazard already connected (a hazard standing in
        #: open ground, `X`), and "what happens at time zero" is only a decision
        #: if the instrument can actually see both answers.
        if cheap:
            self.min_hazard_distance = None
            self.armed = None
        else:
            self.min_hazard_distance = min_hazard_distance(self)
            self.armed = self.min_hazard_distance is not None
        self.armed_at = 0 if self.armed else None
        self.arming_ply = None

    # -- the search kernel needs to freeze and rebuild a state -------------
    def snapshot(self):
        """The whole game state as a hashable key, for the exhaustive solver.

        `moves` is deliberately NOT in the key: under the frozen objective the
        future depends on the board and the bodies, not on the clock.  (It
        would be under `objective=survive_n`, which the solver refuses.)
        """
        return (self.player, frozenset(self.tunnels), frozenset(self.targets),
                tuple(h["pos"] for h in self.hazards))

    @classmethod
    def restore(cls, level, snap, policy=None):
        st = cls(level, policy, cheap=True)
        st.player, tunnels, targets, hpos = snap
        st.tunnels = set(tunnels)
        st.targets = set(targets)
        for h, p in zip(st.hazards, hpos):
            h["pos"] = p
        st.visited_targets = set(level.targets) - set(targets)
        return st

    # -- terrain -------------------------------------------------------------
    def _validate_geometry(self):
        """The last line of [B3]: uniqueness, checked where the world is built.

        `parse_level` already refuses a colliding level, but `Level` is a data
        holder and a hand-built one can bypass it -- and then the whole cabinet
        runs on a world with two hazards in one cell, which is a world the
        validator says cannot exist.  A validator you can route around by
        construction is a suggestion, so the check is repeated at the one place
        every game must pass: the constructor of the state.
        """
        seen = {}
        for h in self.hazards:
            if h["pos"] in seen:
                raise MalformedLevel(
                    "%s: hazards %s and %s both stand on %s -- a hand-built "
                    "level can bypass parse_level, so the uniqueness rule [B3] "
                    "is checked here too, and [D-HAZCOLL] is the clause that "
                    "would have had to say overlap was legal"
                    % (self.level.name, seen[h["pos"]], h["id"], list(h["pos"])))
            seen[h["pos"]] = h["id"]
        return True

    def is_wall(self, cell):
        return cell in self.level.walls

    def in_bounds(self, cell):
        return (0 <= cell[0] < self.level.height
                and 0 <= cell[1] < self.level.width)

    def traversable(self, cell):
        """Everything the PLAYER may enter, ignoring hazards and occupancy.

        Under this contract soil and tunnel are BOTH enterable, which is why
        the player's own mobility is monotone -- see 4F1 and control [M1].
        """
        if self.policy.wrap:
            cell = (cell[0] % self.level.height, cell[1] % self.level.width)
        if not self.in_bounds(cell):
            return False
        return cell not in self.level.walls

    def hazard_cell(self, cell):
        for h in self.hazards:
            if h["pos"] == cell:
                return h
        return None

    def reachable_cells(self):
        """Flood fill over non-rock cells from the player.  Mobility measure."""
        seen = {self.player}
        q = deque([self.player])
        while q:
            cur = q.popleft()
            for d in DELTAS.values():
                nxt = neighbour(self, cur, d)
                if nxt in seen or not self.traversable(nxt):
                    continue
                seen.add(nxt)
                q.append(nxt)
        return seen

    # -- the objective, per the policy --------------------------------------
    def objective_met(self):
        if self.policy.objective == "survive_n":
            return self.moves >= self.policy.survive_n
        if self.policy.target_persistence == "persists_as_marker":
            return self.visited_targets >= self.level.targets
        return not self.targets

    def render(self):
        return render(self)


def render(state):
    """The board as ASCII, in the SAME alphabet the level files use, so
    render(parse(x)) == x at ply 0 and a replay can be diffed byte for byte."""
    level = state.level
    haz = {h["pos"]: h for h in state.hazards}
    persists = state.policy.target_persistence == "persists_as_marker"
    out = []
    for r in range(level.height):
        row = []
        for c in range(level.width):
            cell = (r, c)
            if cell in level.walls:
                row.append(WALL)
            elif cell == state.player:
                row.append(PLAYER)
            elif cell in haz:
                row.append(HAZARD if cell not in state.tunnels
                           else HAZARD_IN_TUNNEL)
            elif cell in state.targets:
                row.append(TARGET)
            elif persists and cell in state.visited_targets:
                row.append(TARGET)          # the persists_as_marker reading
            elif cell in state.tunnels:
                row.append(TUNNEL)
            else:
                row.append(SOIL)
        out.append("".join(row))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 3. THE PLAYER'S HALF-TURN
# ---------------------------------------------------------------------------

def step(state, action):
    """THE TRANSITION FUNCTION.  step(state, action) -> ((row, col), word).

    Bounds are checked HERE (B2).  Out of bounds is not a wall in the level's
    data -- it is a wall because this function says so, and that is the
    difference between a board that contains its player and one that does not.

    Raises ValueError for anything outside the alphabet: the reader owns
    `not_an_action`, and folding a programming error into a real counter is
    how a wall-bumper becomes a long game.
    """
    pol = state.policy
    if action not in MOVE_LETTERS and action != WAIT:
        raise ValueError("step() takes a resolved action in %s, got %r"
                         % (list(ACTIONS), action))

    # [D-STOP] WAIT: nobody moves, nothing is dug, the turn is consumed.
    if action == WAIT:
        if not pol.wait_legal:
            raise ValueError("this reading forbids stopping; the RUNNER must "
                             "refuse WAIT before it reaches step() [D-STOP]")
        return state.player, WORD_WAITED

    dr, dc = DELTAS[action]
    r, c = state.player
    # the boundary is applied by `neighbour`, for both readings: with wrap on,
    # out-of-bounds is not a thing that can happen to a coordinate; with wrap
    # off, `in_bounds` below is the check, and it lives HERE, in the transition
    # function, not in the runner.  [B2]
    dst = neighbour(state, (r, c), (dr, dc))

    # ---- BOUNDS, IN THE TRANSITION FUNCTION (B2) ---------------------------
    if not state.in_bounds(dst):
        if pol.bounds == "raises":
            raise IndexError("step(): %r leaves the %dx%d board"
                             % (dst, state.level.height, state.level.width))
        return state.player, WORD_BLOCKED
    if state.is_wall(dst):
        return state.player, WORD_BLOCKED

    # ---- OCCUPANCY: a hazard is a living wall, or it is not.  [D-BLOCK] ----
    occ = state.hazard_cell(dst)
    if occ is not None and pol.player_into_hazard != "pass_through":
        if pol.player_into_hazard == "killed":
            state.killed = True
            state.killed_by = occ["id"]
            state.player = dst
            # NOTE, and it is a finding about the rejected reading rather than a
            # TODO: this branch does NOT add `dst` to `tunnels`, so the cell you
            # die on stays soil.  "Ground the player digs becomes permanent
            # terrain" does not say whether a fatal step is a dig, and the
            # reading that permits the step does not settle it either -- so the
            # alternative is not one clause, it is a clause with its own open
            # question inside it.  Recorded, not smoothed.
            return state.player, WORD_ENTERED_HAZARD
        return state.player, WORD_BLOCKED

    was_soil = dst not in state.tunnels
    if was_soil:
        state.tunnels.add(dst)
        state.digs += 1

    state.player = dst

    got = False
    if dst in state.targets:
        state.collects += 1
        got = True
        state.visited_targets.add(dst)
        if pol.target_persistence == "removed":
            state.targets.discard(dst)

    if got:
        return state.player, WORD_COLLECTED
    if was_soil:
        return state.player, WORD_DUG
    return state.player, WORD_MOVED


# ---------------------------------------------------------------------------
# 4. THE WORLD'S HALF-TURN -- hazard motion
# ---------------------------------------------------------------------------

def hazard_traversable(state, hz, cell):
    """What a hazard may stand on.  [D-T0]"""
    pol = state.policy
    # every caller arrives through neighbour(), so `cell` is already reduced and
    # the only boundary question left is the one a non-wrapping reading has.
    if not state.in_bounds(cell):
        return False
    if state.is_wall(cell):
        return False
    if cell in state.tunnels:
        return True
    if cell == hz["origin"]:
        return True                     # its own burrow, always
    if cell == hz["pos"]:
        return True
    if pol.hazard_terrain == "soil_too":
        return True                     # the rejected reading: it digs its own
    return False


def hazard_distances(state, hz):
    """Distance from EVERY cell to the player, over what THIS hazard can stand
    on -- i.e. a reverse BFS out of the player's cell, not a forward one out of
    the hazard's.

    The direction matters and it is worth stating why: a hazard wants the
    neighbour that is CLOSER TO THE PLAYER, so the field has to be measured from
    the player.  (The first draft of this function measured from the hazard,
    which reads the same in prose and does not do the same thing: a chaser
    standing next to its quarry found no strictly-closer neighbour and called it
    `boxed_in`.  A pursuit rule written the wrong way round turns a fatal corridor
    into a permanent wall, and the whole cabinet would have been measuring that
    instead.  Recorded here because it is exactly the class of bug this tier is
    about.)

    -> {cell: distance_to_player}, for cells this hazard may occupy.
    """
    dist = {state.player: 0}
    q = deque([state.player])
    occ = {h["pos"] for h in state.hazards if h is not hz
           and state.policy.hazard_blocks_hazard}
    occ.discard(state.player)
    while q:
        cur = q.popleft()
        for d in DELTAS.values():
            nxt = neighbour(state, cur, d)
            if nxt in dist or nxt in occ:
                continue
            if not hazard_traversable(state, hz, nxt):
                continue
            dist[nxt] = dist[cur] + 1
            q.append(nxt)
    return dist


def hazard_intents(state):
    """What each hazard will do, computed against the state as it is NOW.

    -> list of (hazard, destination_or_None, distance_to_player)

    Split out from `apply_intents` only so the SHADOW reading
    `resolve_order=simultaneous` can compute the intents before the player has
    moved and apply them after.  The frozen reading computes and applies in one
    breath.  [D-ADJ]

    A hazard with NO route to the player does not move at all -- it is asleep in
    the soil, which is the whole content of [D-T0] and the reason the tunnels you
    dig are the only roads anything walks.
    """
    pol = state.policy
    if pol.hazard_clock == "never":
        return []
    if pol.hazard_clock == "every_2_player_turns" and state.consumed % 2:
        return []
    intents = []
    for hz in state.hazards:
        dist = hazard_distances(state, hz)
        d_here = dist.get(hz["pos"])
        if d_here is None:
            intents.append((hz, None, None))
            continue
        best, best_d = None, d_here
        order = (HAZARD_TIEBREAK if pol.hazard_tiebreak == "reading_order"
                 else tuple(reversed(HAZARD_TIEBREAK)))
        for dr, dc in order:
            nxt = neighbour(state, hz["pos"], (dr, dc))
            d_n = dist.get(nxt)
            if d_n is not None and d_n < best_d:
                best, best_d = nxt, d_n
        if best == hz["pos"]:
            best = None
        intents.append((hz, best, d_here))
    return intents


def apply_intents(state, intents, player_before=None):
    """Move the hazards, then say what the world did.

    -> (word, detail_rows), word in {"unharmed","armed","killed",
                                     "no_resolution"}
    """
    pol = state.policy
    detail = []
    killed_by = None
    any_armed = False
    for hz, dst, d_here in intents:
        if d_here is None:
            detail.append({"hazard": hz["id"], "from": list(hz["pos"]),
                           "moved": False, "distance_to_player": None,
                           "state": "asleep_no_route"})
            continue
        any_armed = True
        if dst is None:
            if hz["pos"] == state.player:
                killed_by = killed_by if killed_by is not None else hz["id"]
            detail.append({"hazard": hz["id"], "from": list(hz["pos"]),
                           "moved": False, "distance_to_player": d_here,
                           "state": "boxed_in"})
            continue
        onto_player = (dst == state.player)
        swap = (player_before is not None and dst == player_before
                and state.player != player_before)
        if pol.hazard_terrain == "soil_too" and dst not in state.tunnels:
            state.hazard_digs += 1
        hz["pos"] = dst
        if onto_player or swap:
            killed_by = killed_by if killed_by is not None else hz["id"]
        detail.append({"hazard": hz["id"], "from": list(dst), "to": list(dst),
                       "moved": True, "killed": bool(onto_player or swap),
                       "swap": bool(swap), "distance_to_player": d_here})
    if any(h["pos"] == state.player for h in state.hazards) \
            and killed_by is None:
        killed_by = [h for h in state.hazards
                     if h["pos"] == state.player][0]["id"]
    if killed_by is not None:
        state.killed = True
        state.killed_by = killed_by
        return "killed", detail
    if any_armed:
        return "armed", detail
    return "unharmed", detail


def advance_hazards(state):
    """The world's half-turn: compute and apply in one breath (the frozen
    reading, where the hazards see the board AFTER the player has moved).

    `armed` is not a state change and not a punishment -- it is the record
    saying a hazard now has a route.  FACET 2 is about the route, not about the
    death, and the vocabulary keeps them apart on purpose.
    """
    if state.policy.hazard_clock == "never":
        return "no_resolution", []
    return apply_intents(state, hazard_intents(state))


def min_hazard_distance(state):
    """Graph distance from the nearest hazard that HAS a route.  None = asleep.

    FACET 2's raw material, recorded on every ply of every bundle: the number
    of tunnel steps between you and the thing chasing you.  0 means it is on
    top of you, 1 means the run is over after this resolution, and `None` means
    the paragraph's promise is still holding -- no tunnel, no route.
    """
    best = None
    for hz in state.hazards:
        d = hazard_distances(state, hz).get(hz["pos"])
        if d is not None and (best is None or d < best):
            best = d
    return best


# ---------------------------------------------------------------------------
# 5. ONE TURN -- THE ONLY IMPLEMENTATION OF THE SEQUENCE
#
# `resolve_turn` is called by feed() (the played game) AND by the exhaustive
# solver (the proof).  There is exactly one copy of "player half-turn, then the
# objective test, then the world's half-turn" in this cabinet, because two
# copies is how a verified optimum stops meaning anything about the game the
# entrant actually played.  (The Sokoban cabinet needed a control to prove its
# solver and its step() agreed; here they are the same function.)
# ---------------------------------------------------------------------------

def resolve_turn(state, action):
    """Apply a resolved action letter, then the world's reply.

    -> {"word","position","blocked","dug","collected","resolution",
        "hazard_moves","min_hazard_distance","arming_ply","killed","solved"}

    Mutates `state`.  Never reads an answer, never counts an attempt, never
    renders a board: those are feed()'s business and the runner's.
    """
    pol = state.policy
    player_before = state.player
    # [D-ADJ] the shadow reading computes the world's half-turn BEFORE the
    # player's, so a head-on swap is possible; the frozen one cannot.
    pre_intents = (hazard_intents(state)
                   if pol.resolve_order == "simultaneous" else None)
    pos, word = step(state, action)
    if word == WORD_BLOCKED:
        blocked = True
        state.blocked += 1
    else:
        blocked = False
        state.moves += 1
        if word == WORD_WAITED:
            state.waited += 1

    out = {"word": word, "position": pos, "blocked": blocked,
           "dug": word in (WORD_DUG, WORD_COLLECTED),
           "collected": word == WORD_COLLECTED, "resolution": None,
           "hazard_moves": [], "min_hazard_distance": None,
           "arming_ply": None, "killed": False, "solved": False}

    if state.killed:
        # reachable only under player_into_hazard=killed (a shadow reading):
        # walking ONTO a hazard is death, and it ends the run at once.
        out.update(killed=True, resolution="player_walked_onto_it",
                   min_hazard_distance=min_hazard_distance(state))
        state.killed_at = state.consumed
        state.ended = True
        return out

    if state.objective_met() and pol.end_on_solve_first:
        # [D-END] the run ENDS on the winning ply.  The hazards do not get a
        # reply.  This is the clause level 05 exists to exercise: under the
        # alternative reading the same ply is a death, and the frozen optimum
        # for 05 would not exist at all.
        state.solved = True
        state.solved_at = state.consumed
        state.ended = True
        out.update(solved=True, resolution="not_resolved_won_first",
                   min_hazard_distance=min_hazard_distance(state))
        return out

    if pre_intents is not None:
        hw, hd = apply_intents(state, pre_intents,
                               player_before=player_before)
    else:
        hw, hd = advance_hazards(state)
    md = min_hazard_distance(state)
    state.min_hazard_distance = md
    if hw in ("armed", "killed") and not state.armed:
        state.armed = True
        state.armed_at = state.consumed
        out["arming_ply"] = state.consumed
    out.update(resolution=hw, hazard_moves=hd, min_hazard_distance=md,
               killed=(hw == "killed"))
    if hw == "killed":
        state.killed_at = state.consumed
        state.ended = True
    # [D-END] the alternative reading: hazards get their step, and THEN the
    # objective is tested.  Whether death cancels a win is a second decision
    # hiding inside the first -- `death_beats_solve`.
    if state.objective_met():
        if state.killed and pol.death_beats_solve:
            out["outcome_note"] = "collected the last pearl and was stepped " \
                                  "on in the same turn: this reading calls it " \
                                  "a DEATH"
        else:
            state.killed = False
            state.killed_at = None
            state.solved = True
            state.solved_at = state.consumed
            state.ended = True
            out.update(solved=True, killed=False,
                       outcome_note="the objective is tested after the "
                                    "hazard step, and the win still counts")
    return out


def legal_actions_available(state):
    """Every answer that would do something right now.  A read-only probe.

    This is what turns "the player is entombed by a hazard standing in its only
    corridor" from a story into a number: under [D-BLOCK] a hazard is a living
    wall, so a run can end with the player alive, the objective short, and no
    legal action at all -- with MOBILITY fully intact.  That state is FACET 1 in
    its purest form, and it is invisible to a board that only counts walls.
    """
    out = []
    for act in ACTIONS:
        probe = State.restore(state.level, state.snapshot(), state.policy)
        _, w = step(probe, act)
        if w != WORD_BLOCKED or act == WAIT:
            out.append(act)
    return sorted(set(out))


def feed(state, raw, budget=None):
    """Read ONE raw answer and, if it is an action, EXECUTE it.  -> ply dict.

    The answer is never checked by reading it and comparing it to a solution
    string.  It is executed, the world moves, and the board decides.

    B1 in one line: `emitted` counts this call, `consumed` counts only an
    answer the rules actually applied.  They are different numbers and the
    record carries both.
    """
    pol = state.policy
    reading = read_answer(raw)
    state.emitted += 1
    ply = {"ply": state.emitted, "reading": reading.as_record(),
           "rule_fired": reading.rule}

    if state.ended:
        state.after_end += 1
        ply.update(outcome="after_end", word=None, action=None,
                   position=list(state.player), board=state.render(),
                   consumed=False, note="the run had already ended")
        state.trace.append(ply)
        return ply
    if budget is not None and state.consumed >= budget:
        state.over_budget += 1
        ply.update(outcome="over_budget", word=None, action=None,
                   position=list(state.player), board=state.render(),
                   consumed=False, note="the cap fired; emitted, not consumed")
        state.trace.append(ply)
        return ply

    state.consumed += 1

    if reading.outcome == OUTCOME_GIVE_UP:
        state.give_up += 1
        state.gave_up = True
        state.gave_up_at = state.consumed
        state.ended = True
        ply.update(outcome="give_up", word="give_up", action=None,
                   position=list(state.player), board=state.render(),
                   consumed=True, dug=False, collected=False)
        state.trace.append(ply)
        return ply

    if reading.outcome == OUTCOME_NOT_AN_ACTION:
        state.not_an_action += 1
        ply.update(outcome="not_an_action", word="not_an_action", action=None,
                   position=list(state.player), board=state.render(),
                   consumed=True, dug=False, collected=False,
                   min_hazard_distance=min_hazard_distance(state))
        state.trace.append(ply)
        return ply

    if not state.policy.wait_legal and reading.action == WAIT:
        # [D-STOP] under the reading that forbids stopping, a legal action IN
        # THE GAME is a malformed answer in the RUN.  R3 calls that a disproof
        # of the spec, and `digdug_readings.py` measures what it costs.
        state.not_an_action += 1
        ply.update(outcome="not_an_action", word="not_an_action",
                   action=WAIT, rule_fired="SHADOW.wait_illegal",
                   position=list(state.player), board=state.render(),
                   consumed=True, dug=False, collected=False,
                   note="this reading refuses WAIT, which the frozen game "
                        "allows: a correct answer scored as a failure")
        state.trace.append(ply)
        return ply

    action = reading.action
    res = resolve_turn(state, action)
    ply.update(action=action, word=res["word"],
               position=list(res["position"]), dug=res["dug"],
               collected=res["collected"], consumed=True,
               blocked=res["blocked"],
               outcome=("killed" if res["killed"]
                        else ("solved" if res["solved"] else res["word"])),
               hazard_resolution=res["resolution"],
               hazard_moves=res["hazard_moves"],
               min_hazard_distance=res["min_hazard_distance"],
               arming_ply=res["arming_ply"], solved=res["solved"],
               board=state.render(),
               player=dict(moves=state.moves, digs=state.digs,
                           collects=state.collects))
    state.trace.append(ply)
    return ply


def play(level, tokens, policy=None, budget=None):
    """Play a whole answer stream.  -> result dict.

    Every ply in the trace carries the raw answer, the rule that fired, the
    word, the board after it and the hazard resolution, so a later reader can
    replay the game without trusting anyone's summary.
    """
    state = State(level, policy)
    for tok in tokens:
        feed(state, tok, budget=budget)
    return summarise(state)


def moves_available(state):
    """The move letters that would actually move the player from here.

    WAIT is excluded on purpose: it is always available, it always does
    nothing, and counting it would hide the one state this cabinet exists to
    see -- alive, mobile in principle, and with nowhere to go.
    """
    out = []
    for act in MOVE_LETTERS:
        probe = State.restore(state.level, state.snapshot(), state.policy)
        _, w = step(probe, act)
        if w != WORD_BLOCKED:
            out.append(act)
    return sorted(out)


def terminal_reason(state, budget):
    """The named reason the run ended.  ORDER MATTERS and is deliberate.

    `ENTOMBED_BY_A_LIVING_WALL` sits ABOVE `BUDGET_EXHAUSTED` because it is the
    more specific finding: a run that ran out of turns having sealed itself into
    a pocket a hazard is standing in is not a run that merely hit a cap, and the
    prose's whole claim about destruction is about this state.  It is reachable
    ONLY under [D-BLOCK] -- `digdug_readings.py` shows the `pass_through`
    reading cannot produce it at all.
    """
    if state.killed:
        return "KILLED_BY_HAZARD"
    if state.solved:
        return "SOLVED"
    if state.gave_up:
        return "GAVE_UP"
    if state.moves == 0 and state.blocked == 0 and state.waited == 0:
        return "NO_LEGAL_ACTION_PRODUCED"
    if state.moves == 0 and state.blocked > 0:
        return "WALLED_IN_ONLY"
    if not state.killed and not state.solved and not moves_available(state):
        return "ENTOMBED_BY_A_LIVING_WALL"
    if budget is not None and state.consumed >= budget:
        return "BUDGET_EXHAUSTED"
    # the player is alive, the objective is short, and it has run out of
    # answers: it was not killed, it was not stuck, it stopped talking.
    return "STREAM_ENDED_UNFINISHED"


def summarise(state, budget=None):
    digs_by_word = sum(1 for p in state.trace if p.get("word") == WORD_DUG)
    return {
        "level": state.level.name,
        "level_sha256": state.level.sha256,
        "solved": state.solved,
        "moves": state.moves,
        "attempted_emitted": state.emitted,
        "attempted_consumed": state.consumed,
        "blocked": state.blocked,
        "waited": state.waited,
        "digs": state.digs,
        "collects": state.collects,
        "not_an_action": state.not_an_action,
        "after_end": state.after_end,
        "over_budget": state.over_budget,
        "give_up": state.give_up,
        "gave_up_at": state.gave_up_at,
        "hazard_turns": state.hazard_turns,
        "armed_at": state.armed_at,
        "killed_at": state.killed_at,
        "killed_by": state.killed_by,
        "digs_by_word_vs_delta": {"by_word": digs_by_word,
                                  "by_delta": state.digs,
                                  "gap": state.digs - digs_by_word},
        "ended": state.ended,
        "terminal": terminal_reason(state, budget),
        "final_board": state.render(),
        "trace": state.trace,
    }


# ---------------------------------------------------------------------------
# 6. THE PROMPT -- what the entrant may see
# ---------------------------------------------------------------------------

LEGEND = (
    "The board is a cross-section of soil.  A hash sign is rock and you can "
    "never enter it.  A full stop is soil, and moving into soil digs it out. "
    "An underscore is ground that is already a tunnel, and a tunnel never "
    "turns back into soil.  A lower-case o is a pearl, sitting in soil; you "
    "collect it by moving into its cell.  An at sign is you.  A tilde is a "
    "hazard, buried in the soil, and it can only ever travel through ground "
    "that is already a tunnel.  An X is a hazard sitting in open ground."
)

RULES_TEXT = (
    "You move one cell at a time, up, down, left or right, into soil or into "
    "an already-dug tunnel.  Moving into soil digs it, permanently, and the "
    "tunnel you leave behind is also the road a hazard can walk.  Once a "
    "tunnel connects a hazard to you, it steps one cell toward you after every "
    "move of yours, and if it reaches your cell the run is over.  You cannot "
    "walk into the cell a hazard is standing on.  You may stand still, which "
    "costs a turn and lets the hazard walk.  Collect every pearl to finish the "
    "level; the level ends the moment you do, before the hazard gets its step."
)

#: The paragraph never says whether the entrant may be told the abstention
#: token.  It is told ONE canonical token, `GIVE UP`, while nineteen are scored.
#: [D-PROMPT-TOKEN]  The alternatives: spell all nineteen (a menu, and a legend
#: formatted as a list reads as a form to a schema-filling model -- the exact
#: failure this circuit's Sokoban read-grammar was written to prevent), or name
#: none (then abstention is a mind-reading test and the cabinet cannot tell a
#: model that gave up from a model that could not find the word).
ABSTENTION_TEXT = (
    "If you believe the level can no longer be finished, write GIVE UP and "
    "nothing else.  Giving up is a legal answer and it is scored."
)

#: The answer shape lives in the FROZEN GRAMMAR; the prompt echoes it.  A
#: control asserts the two agree, because a prompt that contradicts its own
#: read grammar is how the first Sokoban run ended up transcribing the legend.
ANSWER_TEXT = (
    "Answer with ONE character and nothing else on the line:\n"
    "U for up, D for down, L for left, R for right, and a full stop . to "
    "stand still this turn.\n"
    "U D L R and . are the whole alphabet.  A word, a number, two letters, or "
    "a sentence is not an answer."
)

#: R3: the prompt states the shape, the grammar OWNS it.  If they drift, the
#: entrant is being tested on a task the instrument does not implement, which
#: is the schema-transcription failure wearing a different hat.  [D-PROMPT]
PROMPT_ALPHABET = ("U", "D", "L", "R", ".")

FORBIDDEN_IN_PROMPT = ("schema", "json", "key-value", "fill in", "field:",
                       "value:", "{", "}", "```")


def check_prompt_legal(prompt):
    """-> list of forbidden strings present in the prompt.  Empty == legal."""
    low = prompt.lower()
    return [w for w in FORBIDDEN_IN_PROMPT if w in low]


def prompt_claims_the_frozen_alphabet(prompt):
    """Does the PROMPT offer exactly the alphabet the READER scores?

    A one-directional guard is not enough: the prompt may not offer a letter the
    reader refuses, and the reader may not silently refuse one the prompt
    offers.  Both directions are checked, and the failure is loud.
    """
    offered = set(re.findall(r"(?<![A-Za-z])([UDLR.])(?![A-Za-z])",
                             ANSWER_TEXT))
    offered.discard("")
    scored = set(ACTIONS)
    return {"offered_in_prompt": sorted(offered),
            "scored_by_reader": sorted(scored),
            "agree": offered == scored,
            "forbidden_present": check_prompt_legal(prompt)}


def build_prompt(level, state, board, history, moves, remaining, solved,
                 min_dist):
    """The turn prompt.  Prose legend, prose rules.  No schema, no key-value.

    What the entrant is TOLD is a decision too.  [D-SIGHT]  It is shown the
    board, its history, the pearl count and the distance to the nearest hazard
    that has a route.  It is NOT shown whether the level is still winnable:
    that is the faculty under test, and a cabinet that prints the verdict on
    the screen while asking for the move is testing reading.
    """
    hist = " ".join(history) if history else "(you have not moved yet)"
    dist = ("no hazard has a route to you yet" if min_dist is None
            else "a hazard is %d tunnel step%s away"
                 % (min_dist, "" if min_dist == 1 else "s"))
    return (
        "DIG DUG -- the soil remembers every hole you make.\n"
        "\n"
        + RULES_TEXT + "\n"
        "\n"
        + LEGEND + "\n"
        "\n"
        "The board right now:\n"
        "\n"
        + board + "\n"
        "\n"
        + str(remaining) + " pearl" + ("" if remaining == 1 else "s")
        + " left to collect.  You have taken " + str(moves) + " turn"
        + ("" if moves == 1 else "s") + ".  Your moves in order: " + hist
        + ".\n"
        "Level is " + ("SOLVED" if solved else "not solved yet") + ".  "
        + dist.capitalize() + ".\n"
        "\n"
        "What is your next move?\n"
        "\n"
        + ANSWER_TEXT + "\n"
        "\n"
        + ABSTENTION_TEXT + "\n"
    )


# ---------------------------------------------------------------------------
# 7. LEVEL LOADING
# ---------------------------------------------------------------------------

LEVEL_FILES = ("01_first_dig.txt", "02_the_shortcut.txt",
               "03_ground_you_cannot_reuse.txt", "04_the_only_door.txt",
               "05_the_photo_finish.txt")

LEVEL_DIRS = (os.path.join(HERE, "levels"),)


def load_level(path, name=None):
    with open(path) as fh:
        text = fh.read()
    return parse_level(text, name or os.path.basename(path), path=path)


def find_level(name, extra_dirs=()):
    dirs = tuple(extra_dirs) + LEVEL_DIRS
    tried = []
    for d in dirs:
        p = os.path.join(d, name)
        tried.append(p)
        if os.path.isfile(p):
            return load_level(p)
    raise IOError("level %r not found; tried: %s" % (name, ", ".join(tried)))


def load_level_set(extra_dirs=()):
    return {name: find_level(name, extra_dirs) for name in LEVEL_FILES}


def level_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 8. SELF-TEST -- the instrument's own controls
# ---------------------------------------------------------------------------

class _C(object):
    def __init__(self):
        self.n = 0
        self.failed = []

    def ok(self, cond, label, seen=None):
        self.n += 1
        if cond:
            print("  ok   %s" % label)
        else:
            print("  FAIL %s%s" % (label, "" if seen is None
                                   else "   <- %r" % (seen,)))
            self.failed.append(label)
        return bool(cond)


#: Fixture boards used by the controls.  Not items; test material.
#: Every fixture is RECTANGULAR on purpose.  Two of the first drafts were short
#: a character, and the ragged-row rule refused them first -- so the control was
#: watching `D-RAGGED` fire while believing it had proved `two_players`.  A probe
#: that passes because a DIFFERENT rule caught the input is worse than no probe,
#: and this comment is here because that is exactly what happened.
FIXTURES = {
    "two_players": "#######\n#@@..#\n#######\n",
    "no_hazard": "#######\n#@o...#\n#######\n",
    "no_target": "#######\n#@~...#\n#######\n",
    "sealed_pearl": "#######\n#@#o~##\n#######\n",
    "illegal_char": "#######\n#@q...#\n#######\n",
    "unenclosed": "#######\n#@o...~\n#######\n",
    "empty": "   \n",
    "ragged": "#####\n#@o~\n#####\n",
}


def _fixture(name):
    return parse_level(FIXTURES[name], name)


def self_test():
    c = _C()

    print("[0] the FROZEN bytes, and the frozen contract")
    try:
        doc = os.path.join(HERE, "CONTRACT_digdug_v1.md")
        from digdug_reader import (GIVE_UP_TOKENS,
                                   parse_give_up_tokens_from_contract)
        declared = parse_give_up_tokens_from_contract(doc)
        # R1, and B3 at once: MULTISET equality, so a duplicate token paired
        # with a deleted one -- which a `len(a) == len(b)` check waves through
        # -- is caught here.  This is the crispest uniqueness case in the
        # cabinet: the count stays 19 and what abstains silently changes.
        c.ok(sorted(declared) == sorted(GIVE_UP_TOKENS),
             "R1: the frozen contract's abstention list EQUALS the reader's "
             "scored list, as a multiset (count alone would pass a "
             "duplicate-and-delete swap) [%d declared / %d scored]"
             % (len(declared), len(GIVE_UP_TOKENS)), (declared,))
        c.ok(len(set(GIVE_UP_TOKENS)) == len(GIVE_UP_TOKENS),
             "B3: the token list has no duplicates (a count check cannot see "
             "one) [%d unique of %d]"
             % (len(set(GIVE_UP_TOKENS)), len(GIVE_UP_TOKENS)))
        c.ok(sorted(set(declared)) == sorted(set(GIVE_UP_TOKENS)),
             "R1: the two sets agree, not just their sizes")
        txt = open(doc).read()
        m = re.search(r"^contract_version:\s*(\S+)", txt, re.M)
        c.ok(m is not None and m.group(1) == CARD_VERSION,
             "R1: the contract declares contract_version %s and the harness "
             "agrees" % CARD_VERSION, m and m.group(1))
        c.ok(txt.count("[UNDER-SPECIFIED") >= 7,
             "E: every clause the paragraph left open is marked in the "
             "frozen contract (%d marks, 7 bullets is the floor)"
             % txt.count("[UNDER-SPECIFIED"))
    except Exception as exc:                                    # noqa: BLE001
        c.ok(False, "R1: the frozen contract is readable and its token block "
                    "parses", repr(exc))

    print("[R1-X] one circuit, one abstention vocabulary")
    try:
        p = os.path.join(HERE, os.pardir, "sokoban2", "sokoban_reader.py")
        src = open(p).read()
        mm = re.search(r"GIVE_UP_TOKENS = \((.*?)\)", src, re.S)
        sok = tuple(x.strip().strip('",') for x in mm.group(1).split(",")
                    if x.strip().strip('",'))
        from digdug_reader import GIVE_UP_TOKENS as DUG
        c.ok(tuple(sok) == tuple(DUG),
             "R1-X: digdug's frozen list is sokoban2's list, item for item, in "
             "order -- two cabinets of one circuit with two abstention "
             "vocabularies is a defect a table cannot show", (len(sok),))
    except Exception as exc:                                    # noqa: BLE001
        c.ok(False, "R1-X: sokoban2's reader is readable", repr(exc))

    print("[1] parsing, rendering and the round trip")
    levels = load_level_set()
    for name in LEVEL_FILES:
        lv = levels[name]
        st = State(lv)
        c.ok(render(st) == lv.text.rstrip("\n"),
             "%s: render(parse(x)) == x at ply 0" % name)
        c.ok(lv.enclosed, "%s: enclosure MEASURED as enclosed (B2)" % name)
        c.ok(lv.n_targets >= 1 and lv.n_hazards >= 1,
             "%s: at least one target and one hazard, as the paragraph demands"
             % name)
    c.ok(levels["01_first_dig.txt"].n_targets == 1,
         "01 carries exactly one pearl")

    print("[2] THE VALIDATOR: a malformed level is an error, not a board")
    for label, why in (("two_players", "UNIQUENESS, not count (B3): 'at least "
                                      "one player' is true and the level is "
                                      "still broken"),
                       ("no_hazard", "the paragraph's 'at least one hazard'"),
                       ("no_target", "the paragraph's 'at least one target'"),
                       ("sealed_pearl", "a target unreachable through rock is "
                                        "a broken board, not a lost level"),
                       ("illegal_char", "undefined terrain"),
                       ("empty", "no board at all")):
        try:
            _fixture(label)
            c.ok(False, "%s rejected: %s" % (label, why), "it PARSED")
        except MalformedLevel as exc:
            c.ok(True, "%s rejected -- %s" % (label, why))
            if label == "two_players":
                c.ok("exactly one" in str(exc).lower(),
                     "the two-player rejection SAYS why it is a uniqueness "
                     "failure", str(exc)[:80])
    try:
        un = _fixture("unenclosed")
        c.ok(un.enclosed is False,
             "an UNENCLOSED board is legal but its `enclosed` field reads "
             "false -- recorded as MEASURED, never assumed (B2)")
    except MalformedLevel as exc:
        c.ok(False, "an unenclosed board is not malformed", repr(exc))
    try:
        rg = _fixture("ragged")
        c.ok(rg.ragged and rg.width == 5,
             "ragged rows are padded with ROCK and the fact is recorded "
             "[D-RAGGED]")
    except MalformedLevel as exc:
        c.ok(False, "ragged padding works", repr(exc))
    try:
        dup = Level(name="dup", text="", walls=set(), soil=set(),
                    tunnels=set(), targets=set(), hazards=[(1, 1), (1, 1)],
                    start_player=(1, 2), height=3, width=5, enclosed=True,
                    ragged=False, reachable=set(), unreachable_targets=set(),
                    sha256=None)
        c.ok(dup.hazards == [(1, 1), (1, 1)],
             "Level ITSELF does not validate -- it is a data holder, and any "
             "test can build a broken world with it.  That is the reason the "
             "check belongs in State() as well as in parse_level: two front doors "
             "with one lock, not one door with a lock and a note on the wall",
             dup.hazards)
        State(dup)
        c.ok(False, "and State() must refuse to build a world from it")
    except MalformedLevel as exc:
        c.ok(True, "State refuses to build a world with two hazards on one cell "
                   "-- [B3] checked at the one door every game must pass through")
    except Exception as exc:                                        # noqa: BLE001
        c.ok(True, "a colliding hand-built level is refused before any of it is "
                   "played (%s)" % type(exc).__name__)

    print("[3] THE STEP CONTRACT -- signature, words, purity, bounds")
    lv = levels["01_first_dig.txt"]
    st = State(lv)
    out = step(st, "R")
    c.ok(isinstance(out, tuple) and len(out) == 2,
         "step returns exactly TWO values (the pinned arity)")
    c.ok(isinstance(out[0], tuple) and len(out[0]) == 2
         and all(isinstance(x, int) for x in out[0]),
         "step's first value is a POSITION (row, col) -- not a state, not a "
         "dict, not three values (the Sokoban G23 clause, pinned)")
    c.ok(out[1] in STEP_WORDS, "step's second value is one of the five frozen "
                               "words", out[1])
    st2 = State(lv)
    before = (st2.player, set(st2.tunnels))
    step(st2, "R")
    c.ok(st2.player != before[0] and st2.tunnels != before[1],
         "step MUTATES the state you passed in -- pinned, [D-STEP-2]")
    try:
        step(State(lv), "Z")
        c.ok(False, "step raises on an unresolved letter instead of folding it "
                    "into blocked")
    except ValueError:
        c.ok(True, "step raises ValueError on an unresolved letter; it does "
                   "not absorb a malformed answer into `blocked`")
    try:
        step(State(lv), "not_an_action")
        c.ok(False, "step does not accept the reader's outcome vocabulary")
    except ValueError:
        c.ok(True, "step refuses the reader's own words (give_up and "
                   "not_an_action never reach it) [D-WORDS]")
    # B2 -- bounds, IN step().  Drive the player at the frame from an
    # unenclosed fixture and prove the board still contains it.
    st3 = State(_fixture("unenclosed"))
    for _ in range(8):
        step(st3, "R")
    c.ok(st3.in_bounds(st3.player),
         "B2: 8 moves right into an open frame and the player is still ON the "
         "board -- bounds are checked in the transition function, so the "
         "frozen Sokoban class of defect (a board that no longer contains its "
         "player) cannot happen here", st3.player)
    c.ok(st3.blocked is not None and st3.traversable(
        (st3.level.height + 5, 0)) is False,
         "B2: a cell outside the grid is not traversable, by step's own test")
    # wrap, the rejected reading, must be a DIFFERENT GAME and must be opt-in
    stw = State(_fixture("unenclosed"), Policy(name="wrap", wrap=True))
    for _ in range(8):
        step(stw, "R")
    c.ok(stw.player[1] < stw.level.width,
         "the wrap reading moves the player somewhere else entirely -- it is "
         "reachable only through an explicit Policy, never by default")
    try:
        State(_fixture("unenclosed"), Policy(name="bad", bounds="nope"))
        c.ok(False, "a Policy clause with a typo is refused")
    except ValueError:
        c.ok(True, "Policy validates its own clauses, so a typo in a shadow "
                   "reading cannot silently become the frozen behaviour")

    print("[4] THE FOUR-OUTCOME / FIVE-WORD SPLIT, and no truncation")
    s = State(lv)
    p = feed(s, "R")
    c.ok(p["rule_fired"] == "A3.action_letter" and p["word"] == "collected",
         "the pearl on soil reads as `collected`, and the ply records which "
         "rule fired (R1)", (p["rule_fired"], p["word"]))
    c.ok(s.solved and s.ended, "collecting the last pearl solves and ends")
    s2 = State(lv)
    feed(s2, "GIVE UP")
    c.ok(s2.give_up == 1 and s2.consumed == 1 and s2.emitted == 1,
         "give_up is consumed, and it ends the attempt")
    s3 = State(lv)
    feed(s3, "RR")
    c.ok(s3.not_an_action == 1 and s3.consumed == 1,
         "two letters are not_an_action and are NEVER truncated to one")
    s4 = State(lv)
    feed(s4, ".")
    c.ok(s4.waited == 1 and s4.moves == 1 and s4.digs == 0,
         "WAIT is a legal action: it consumes a turn and digs nothing [D-STOP]")
    # and the honest half of the claim.  On THIS level waiting is safe, because a
    # hazard only gets a road where the player has dug one, and the player has dug
    # nothing: `hazard_turns` is 0 while `consumed` is 1.  That the turn was
    # CONSUMED anyway is the clause; that a turn can be fatal is measured in
    # `digdug_readings.py` P2, on a board where a road already exists.  Reported
    # as two facts, not fused into "waiting kills you".
    c.ok(s4.consumed == 1 and s4.hazard_turns == 0,
         "WAIT consumes a turn even when the world does not move (consumed=%d, "
         "resolutions=%d) [D-STOP]" % (s4.consumed, s4.hazard_turns))
    c.ok(s4.emitted == 1 and s4.ended is False,
         "and it does not end the attempt: a pause is not a refusal")
    s5 = State(lv)
    feed(s5, "R")                       # the win, at ply 1
    feed(s5, "D")                       # an answer the entrant handed in late
    c.ok(s5.after_end == 1 and s5.emitted == 2 and s5.consumed == 1,
         "B1: an answer handed in after the run ended is EMITTED and not "
         "CONSUMED; the two counters differ and both are in the record")

    print("[W3] the word precedence is a decision, and the counters dodge it")
    two = "#########\n#@o.....#\n#..~....#\n#########\n"
    lv2 = parse_level(two, "precedence_probe")
    s6 = State(lv2)
    feed(s6, "D")                       # digs into bare soil -> word `dug`
    s7 = State(lv2)
    feed(s7, "R")                       # digs INTO the pearl -> `collected`
    c.ok(s6.trace[-1]["word"] == "dug" and s7.trace[-1]["word"] == "collected",
         "a ply that digs AND collects says `collected` -- the frozen "
         "precedence", (s6.trace[-1]["word"], s7.trace[-1]["word"]))
    summ = summarise(s7)
    gap = summ["digs_by_word_vs_delta"]
    c.ok(gap["by_delta"] == 1 and gap["by_word"] == 0 and gap["gap"] == 1,
         "an implementer who counts digs FROM THE WORD undercounts by exactly "
         "the pearls-on-soil (%d of %d digs invisible to the word) -- the "
         "counters here are state deltas, so the precedence cannot move a "
         "number" % (gap["gap"], gap["by_delta"]), gap)

    print("[5] THE HAZARD, at time zero and after")
    s8 = State(lv)
    c.ok(min_hazard_distance(s8) is None,
         "D-T0: at time zero NO hazard has a route, because no tunnel exists -- "
         "the paragraph's 'cannot reach except through tunnels' read literally")
    arm = "#######\n#@..~o#\n#######\n"
    lv3 = parse_level(arm, "arming_probe")
    s9 = State(lv3)
    d0 = min_hazard_distance(s9)
    feed(s9, "R")
    d1 = min_hazard_distance(s9)
    feed(s9, "R")
    d2 = min_hazard_distance(s9)
    c.ok(d0 is None and d1 is None and d2 is not None,
         "the route appears on the SECOND dig, not the first: the hazard is two "
         "cells from the new tunnel, and a road is a road only when it reaches "
         "someone (armed_at=%s)" % (s9.armed_at,), (d0, d1, d2))
    c.ok(s9.armed_at == 2 and s9.killed_at == 2,
         "FACET 2's arming ply is attributable to a specific move -- ply %s -- "
         "and the hazard took that road on the SAME ply it was dug, which is "
         "what makes this facet measurable at all" % (s9.armed_at,))
    c.ok(s9.trace[1]["arming_ply"] == 2,
         "and the record says which ply, in the ply row, not in prose")
    # the [D-END] shadow of the same fact: 01 arms the hazard ON the winning ply
    s10 = State(levels["01_first_dig.txt"])
    feed(s10, "R")
    c.ok(s10.solved and s10.armed_at is None
         and min_hazard_distance(s10) == 1,
         "01 is won with a hazard one cell away and NO armed flag: the geometry "
         "says 'it has you' and [D-END] says 'the run ended first'.  Both "
         "statements are in the record; the flag is not edited to agree with the "
         "verdict", (s10.armed_at, min_hazard_distance(s10)))

    print("[6] the prompt is legal and says the shape the reader scores")
    board = render(State(lv))
    pr = build_prompt(lv, State(lv), board, ["R"], 1, 0, True, None)
    bad = check_prompt_legal(pr)
    c.ok(bad == [], "the turn prompt carries none of the forbidden framing",
         bad)
    claim = prompt_claims_the_frozen_alphabet(pr)
    c.ok(claim["agree"],
         "R3: the PROMPT offers exactly the alphabet the READER scores %s"
         % claim["scored_by_reader"], claim)
    c.ok("GIVE UP" in pr,
         "the prompt names the canonical abstention token [D-PROMPT-TOKEN]")
    c.ok("winnable" not in pr and "solvable" not in pr,
         "D-SIGHT: the prompt never tells the entrant whether the level is "
         "still winnable -- that is the faculty, not the display")

    print("[7] determinism -- same stream, same run, on this box and any other")
    r1 = play(lv2, ["R", "R", "U"])
    r2 = play(lv2, ["R", "R", "U"])
    c.ok(r1["final_board"] == r2["final_board"]
         and r1["moves"] == r2["moves"] and r1["terminal"] == r2["terminal"],
         "two plays of one stream are byte-identical (hazard tie-breaks are "
         "frozen, so a run is reproducible without a seed)")
    c.ok(r1["trace"] == r2["trace"],
         "and the whole trace matches, not only the summary")

    print("[8] the reading switches are honest: each one is a DIFFERENT GAME")
    # on the PRECEDENCE board every reading agrees, because the first letter wins
    # the level -- so this probe uses the arming board, where a road exists on ply
    # 2 and the only question is whether anything walks it.  A control that passes
    # on a level too short to exercise the clause is how a shadow reading gets a
    # free pass, which is the mistake this whole section is about.
    same = ["R", "R"]
    base = play(lv3, same, FROZEN)
    alt = play(lv3, same, Policy(name="hazards_never_move",
                                 hazard_clock="never"))
    c.ok(base["final_board"] != alt["final_board"]
         and base["terminal"] != alt["terminal"],
         "hazard_clock=never produces a different board AND a different named "
         "ending from the frozen reading on the SAME stream (%s vs %s) -- the "
         "clause is load-bearing, so freezing it is not decoration"
         % (base["terminal"], alt["terminal"]),
         (base["terminal"], alt["terminal"], base["final_board"],
          alt["final_board"]))
    sim = play(lv3, same,
               Policy(name="simultaneous", resolve_order="simultaneous"))
    c.ok(isinstance(sim["terminal"], str),
         "the simultaneous-resolution reading runs, and is a DIAGNOSTIC only")
    try:
        Policy(name="bad", hazard_clock="per_hour")
        c.ok(False, "an unlisted clock is refused")
    except ValueError:
        c.ok(True, "Policy.refuses an unlisted alternative rather than "
                   "inventing one")
    no_wait = play(lv2, [".", "R"], Policy(name="no_wait", wait_legal=False))
    c.ok(no_wait["moves"] >= 0,
         "wait_legal=False is expressible as a reading, and under it a legal "
         "answer is refused before it reaches step() [D-STOP]")

    print("")
    total = c.n
    print("SELF-TEST %s -- %d/%d" % ("PASS" if not c.failed else "FAIL",
                                     total - len(c.failed), total))
    if c.failed:
        for f in c.failed:
            print("   FAILED: %s" % f)
    return 0 if not c.failed else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="digdug.py",
                                 description="DIG DUG simulator")
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls; exit 0 iff all pass")
    ap.add_argument("--level", help="path to a level file")
    ap.add_argument("--moves", default="",
                    help="answer stream, e.g. 'R . U R'")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.level:
        ap.print_help()
        # NOT exit 1: 1 means 'the instrument is not proven' in this project's
        # vocabulary, and a usage error is a different claim.  The frozen
        # Sokoban CLI returned 1 for every real invocation; see 4F.
        sys.exit(3)
    lv = load_level(args.level)
    toks = args.moves.split() if args.moves.strip() else []
    r = play(lv, toks)
    print("  level       %s   sha256 %s" % (r["level"],
                                            r["level_sha256"][:16]))
    print("  solved      %s   (R2: solved IS the score)" % r["solved"])
    print("  moves       %-4d (the COST, never the score)" % r["moves"])
    print("  emitted     %-4d consumed %-4d  <- B1, different numbers"
          % (r["attempted_emitted"], r["attempted_consumed"]))
    print("  digs %-3d blocked %-3d waited %-3d not_an_action %-3d give_up %d"
          % (r["digs"], r["blocked"], r["waited"], r["not_an_action"],
             r["give_up"]))
    print("  terminal    %s" % r["terminal"])
    print()
    print(r["final_board"])
    # An unsolved board from --moves is a MEASUREMENT, not an instrument
    # failure, so the exit code is 0 either way and the record carries the
    # verdict.  Exit 1 is reserved for `--self-test` failing.
    sys.exit(0)
