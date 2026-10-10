#!/usr/bin/env python3
# sokoban2.py -- INDEPENDENT IMPLEMENTATION of the SOKOBAN cabinet simulator.
#
# Second implementation.  Written against SOKOBAN_READ_GRAMMAR.md and the two
# levels on disk; it does not share code with sokoban.py and was not derived
# from it.  Where the frozen artifacts leave something open, the decision is
# marked [G<n>] here and argued in SOKOBAN2_AMBIGUITIES.md.
#
# THE FROZEN TRANSITION FUNCTION:
#
#     step(state, action)  ->  (position_after_the_action, word)
#
# TWO values.  Not three.  `word` says what happened.  The board is mutated on
# the state you passed in; the returned position is the PLAYER's position after
# the action -- unchanged when the action was blocked.  [G5]
#
# Stdlib only.

import argparse
import hashlib
import os
import sys

from sokoban_reader import (ACTIONS, OUTCOME_ACTION, OUTCOME_GIVE_UP,
                            OUTCOME_NOT_AN_ACTION, read_answer)

HARNESS = "handicap-arena"
VERSION = "1.0"
EVENT = "SOKOBAN"

# ---------------------------------------------------------------------------
# 1. LEVELS -- the alphabet, and what makes a level MALFORMED
# ---------------------------------------------------------------------------

WALL = "#"
FLOOR = " "
TARGET = "."
BOX = "$"
BOX_ON_TARGET = "*"
PLAYER = "@"
PLAYER_ON_TARGET = "+"

LEGAL_CHARS = frozenset((WALL, FLOOR, TARGET, BOX, BOX_ON_TARGET,
                         PLAYER, PLAYER_ON_TARGET))

DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

# The three words step() can say.  `give_up` and `not_an_action` are owned by
# the READER, not by the transition function -- a malformed token never reaches
# step().  [G4]
WORD_MOVED = "moved"
WORD_PUSHED = "pushed"
WORD_BLOCKED = "blocked"
STEP_WORDS = (WORD_MOVED, WORD_PUSHED, WORD_BLOCKED)


class MalformedLevel(ValueError):
    """A level that is not a board.  Never silently parsed into one.

    Dossier section 8 group [2]: "A MALFORMED LEVEL IS AN ERROR, NOT A BOARD."
    A board parsed out of a malformed level measures something else entirely.
    """


class Level(object):
    """The static part of a level: walls, targets, and the start position."""

    __slots__ = ("name", "text", "sha256", "walls", "targets", "start_boxes",
                 "start_player", "height", "width", "enclosed", "ragged")

    def __init__(self, name, text, walls, targets, start_boxes, start_player,
                 height, width, enclosed, ragged, sha256):
        self.name = name
        self.text = text
        self.sha256 = sha256
        self.walls = walls
        self.targets = targets
        self.start_boxes = start_boxes
        self.start_player = start_player
        self.height = height
        self.width = width
        self.enclosed = enclosed
        self.ragged = ragged

    @property
    def n_boxes(self):
        return len(self.start_boxes)

    @property
    def n_targets(self):
        return len(self.targets)


def parse_level(text, name="<level>"):
    """Parse ASCII into a Level, or raise MalformedLevel.

    Malformed (all ERROR, never a board):
      - empty or whitespace-only                          [G6]
      - a character outside # . $ * @ + and space         [G6]
      - not exactly one player (@ or +)                   [G6]
      - zero boxes, or zero targets                       [G6]
      - boxes != targets                                  [G7]
      - a box or the player standing on a wall-adjacent
        impossible cell is NOT checked here -- that is a
        solvability question, not a parse question.

    Ragged rows are PADDED with floor, not rejected, and the fact is recorded
    on the level (`ragged`).  [G8]  Standard Sokoban files pad short rows; a
    level that is merely short is not the same defect as a level with a
    character nobody defined.
    """
    if text is None or not text.strip():
        raise MalformedLevel("%s: empty level text" % name)

    raw_lines = [ln for ln in text.split("\n")]
    # A trailing newline is not a row.
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    if not raw_lines:
        raise MalformedLevel("%s: empty level text" % name)

    width = max(len(ln) for ln in raw_lines)
    ragged = any(len(ln) != width for ln in raw_lines)
    rows = [ln.ljust(width) for ln in raw_lines]
    height = len(rows)

    walls = set()
    targets = set()
    boxes = set()
    players = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch not in LEGAL_CHARS:
                raise MalformedLevel(
                    "%s: illegal character %r at row %d col %d "
                    "(legal: # . $ * @ + and space)" % (name, ch, r, c))
            if ch == WALL:
                walls.add((r, c))
            elif ch == TARGET or ch == BOX_ON_TARGET or ch == PLAYER_ON_TARGET:
                targets.add((r, c))
            if ch == BOX or ch == BOX_ON_TARGET:
                boxes.add((r, c))
            if ch == PLAYER or ch == PLAYER_ON_TARGET:
                players.append((r, c))

    if len(players) != 1:
        raise MalformedLevel(
            "%s: expected exactly one player (@ or +), found %d"
            % (name, len(players)))
    if not boxes:
        raise MalformedLevel("%s: no boxes ($ or *)" % name)
    if not targets:
        raise MalformedLevel("%s: no targets (. or * or +)" % name)
    if len(boxes) != len(targets):
        # [G7] "Push EVERY crate onto a target" only has a referent when the
        # counts match.  A level with 3 crates and 2 targets is not a level
        # with a hard solution; it is a level with no defined win condition.
        # Failing closed here is a DECISION, and it is the defensible one: the
        # alternative is to invent a win condition.
        raise MalformedLevel(
            "%s: %d boxes but %d targets -- the win condition "
            "('every crate on a target') has no referent [G7]"
            % (name, len(boxes), len(targets)))
    for cell in boxes:
        if cell in walls:
            raise MalformedLevel("%s: box inside a wall at %r" % (name, cell))
    if players[0] in walls:
        raise MalformedLevel("%s: player inside a wall at %r"
                             % (name, players[0]))

    enclosed = _is_enclosed(walls, targets | boxes | {players[0]},
                            height, width)

    return Level(name=name, text="\n".join(rows) + "\n",
                 walls=frozenset(walls), targets=frozenset(targets),
                 start_boxes=frozenset(boxes), start_player=players[0],
                 height=height, width=width, enclosed=enclosed, ragged=ragged,
                 sha256=hashlib.sha256(
                     ("\n".join(rows) + "\n").encode("utf-8")).hexdigest())


def _is_enclosed(walls, playable, height, width):
    """True if no playable cell touches the outside of the bounding box.

    Recorded, not enforced.  [G9]  An unenclosed level is allowed here and
    out-of-bounds is treated as a wall -- but the fact is measured and carried,
    because on an unenclosed level "blocked" and "walked off the board" are the
    same event, and a reader who does not know the level is open will read the
    counters wrong.
    """
    for (r, c) in playable:
        if r in (0, height - 1) or c in (0, width - 1):
            if (r, c) not in walls:
                return False
    return True


def load_level(path, name=None):
    with open(path, "r") as fh:
        text = fh.read()
    return parse_level(text, name or os.path.basename(path))


# ---------------------------------------------------------------------------
# 1b. WHERE THE LEVELS LIVE -- the frozen bytes are NOT duplicated
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: 01 and 02 are FROZEN and live in sokoban/levels/.  This implementation does
#: NOT copy them: a copy drifts.  It reads them in place and checks the digests
#: against sokoban/MANIFEST.txt (control group [0]).  03 is new and lives here,
#: because it does not exist anywhere else in the tree.
LEVEL_DIRS = (os.path.join(HERE, "levels"),
              os.path.join(REPO, "sokoban", "levels"))

LEVEL_FILES = ("01_one_push.txt", "02_two_boxes.txt",
               "03_the_corner_waiting.txt")

#: The frozen digests, as recorded in sokoban/MANIFEST.txt at pin time.
FROZEN_SHA256 = {
    "01_one_push.txt":
        "db6ca59655f0d7d1f1ce48e36e0b0c90a3bca5158b96a31a7a4fe37006a6a313",
    "02_two_boxes.txt":
        "7549657f1768607cefab6d892b1756b1cabf23f51144a7679d76f331b38a57d7",
}
MANIFEST = os.path.join(REPO, "sokoban", "MANIFEST.txt")

#: The claim this implementation was asked to verify.  Verified by exhaustive
#: BFS in sokoban2_solve.py, NOT asserted here.
EXPECTED_OPTIMAL = {"01_one_push.txt": 1, "02_two_boxes.txt": 12,
                    "03_the_corner_waiting.txt": 6}


def find_level(name, extra_dirs=()):
    """Locate a level by filename without duplicating the frozen bytes."""
    for d in tuple(extra_dirs) + LEVEL_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return load_level(p, name)
    raise IOError("level %r not found in %s" % (name, list(LEVEL_DIRS)))


def load_level_set(extra_dirs=()):
    return {name: find_level(name, extra_dirs) for name in LEVEL_FILES}


# ---------------------------------------------------------------------------
# 2. THE STATE, AND THE TRANSITION FUNCTION
# ---------------------------------------------------------------------------

class State(object):
    """Mutable game state over a static Level."""

    def __init__(self, level):
        self.level = level
        self.boxes = set(level.start_boxes)
        self.player = level.start_player
        # counters -- every one of them named, because a naive counter merges
        # them and calls a wall-bumper's run "a long game".
        self.moves = 0            # moved + pushed.  THE SCORE.
        self.attempted = 0        # every token read from the entrant
        self.blocked = 0
        self.not_an_action = 0
        self.give_up = 0
        self.after_end = 0        # tokens emitted AFTER the attempt ended:
                                  # COUNTED, not played, and NOT folded into
                                  # not_an_action -- a legal "R" after the end
                                  # is not a malformed answer [G10]
        self.gave_up = False
        self.gave_up_at = None        # the ATTEMPT NUMBER at which it abstained
        self.ended = False
        self.trace = []

    @property
    def solved(self):
        return self.boxes == set(self.level.targets)

    def render(self):
        return render(self.level, self.boxes, self.player)

    def as_dict(self):
        return {
            "moves": self.moves, "attempted": self.attempted,
            "blocked": self.blocked, "not_an_action": self.not_an_action,
            "after_end": self.after_end,
            "give_up": self.give_up, "solved": self.solved,
            "ended": self.ended,
        }


def render(level, boxes, player):
    """Render the board as ASCII.  The grid is the screen; no decoration."""
    out = []
    for r in range(level.height):
        row = []
        for c in range(level.width):
            cell = (r, c)
            if cell in boxes:
                row.append(BOX_ON_TARGET if cell in level.targets else BOX)
            elif cell == player:
                row.append(PLAYER_ON_TARGET if cell in level.targets
                           else PLAYER)
            elif cell in level.walls:
                row.append(WALL)
            elif cell in level.targets:
                row.append(TARGET)
            else:
                row.append(FLOOR)
        out.append("".join(row))
    return "\n".join(out)


def step(state, action):
    """THE TRANSITION FUNCTION.

        step(state, action) -> ( (row, col), word )

    TWO values.  The first is the PLAYER'S POSITION AFTER THE ACTION -- which
    is the old position when the action was blocked, because a blocked action
    moved nobody.  [G5]  The second is one of "moved" / "pushed" / "blocked".

    The state is mutated in place; the board after the move is `state.render()`
    and is also copied into the trace by `feed()`/`play()`.

    `action` must already be a single upper-cased letter in {U,D,L,R}.  The
    reader owns everything else: `not_an_action` and `give_up` never reach
    here.  [G4]
    """
    if action not in DELTAS:
        raise ValueError("step() takes a resolved action letter in %s, got %r"
                         % (list(ACTIONS), action))
    level = state.level
    dr, dc = DELTAS[action]
    r, c = state.player
    dst = (r + dr, c + dc)

    # Out of bounds is a wall.  [G9] -- recorded, not enforced, at parse time.
    if dst in level.walls or not (0 <= dst[0] < level.height
                                  and 0 <= dst[1] < level.width):
        return state.player, WORD_BLOCKED

    if dst in state.boxes:
        beyond = (dst[0] + dr, dst[1] + dc)
        if (beyond in level.walls or beyond in state.boxes
                or not (0 <= beyond[0] < level.height
                        and 0 <= beyond[1] < level.width)):
            return state.player, WORD_BLOCKED
        state.boxes.remove(dst)
        state.boxes.add(beyond)
        state.player = dst
        return state.player, WORD_PUSHED

    state.player = dst
    return state.player, WORD_MOVED


# ---------------------------------------------------------------------------
# 3. FEEDING ANSWERS -- where the reader and the transition function meet
# ---------------------------------------------------------------------------

def feed(state, raw):
    """Read ONE raw answer and, if it is an action, EXECUTE it.

    -> dict describing the ply.  The answer is never checked by reading it and
    comparing to a solution string; it is executed and the board decides.
    """
    reading = read_answer(raw)
    state.attempted += 1
    ply = {"attempt": state.attempted, "reading": reading.as_record()}

    if state.ended:
        # Nothing may be played after the attempt ended.  Counted anyway, so
        # the record shows the entrant was still talking.  [G10]
        state.after_end += 1
        ply.update(outcome="after_end", word=None, position=None,
                   board=state.render(), note="attempt already ended")
        return ply

    if reading.outcome == OUTCOME_GIVE_UP:
        state.give_up += 1
        state.gave_up = True
        state.gave_up_at = state.attempted
        state.ended = True            # [G11] "give_up -> Attempt ENDS"
        ply.update(outcome="give_up", word="give_up", position=state.player,
                   board=state.render())
        state.trace.append(ply)
        return ply

    if reading.outcome == OUTCOME_NOT_AN_ACTION:
        state.not_an_action += 1
        ply.update(outcome="not_an_action", word="not_an_action",
                   position=state.player, board=state.render())
        state.trace.append(ply)
        return ply

    # OUTCOME_ACTION -- execute it.  Two values back, always.
    pos, word = step(state, reading.action)
    if word == WORD_BLOCKED:
        state.blocked += 1
    else:
        state.moves += 1
    ply.update(outcome=word, word=word, action=reading.action,
               position=list(pos), board=state.render())
    state.trace.append(ply)
    if state.solved:
        state.ended = True            # [G12] solved ends the attempt
    return ply


def play(level, tokens):
    """Play a whole stream.  -> the result dict the dossier section 5.2 names.

    `tokens` is a list of raw answers (one per turn), already in order.  Every
    ply in the trace carries the token, the action it resolved to, the outcome
    and the board after it -- so a later reader can replay the game without
    trusting anyone's summary.
    """
    state = State(level)
    # The WHOLE stream is consumed.  A token emitted after the attempt ended is
    # COUNTED and not played [G10] -- if we stopped reading there, the record
    # would silently drop evidence that the entrant was still talking.  (The
    # interactive runner does stop asking once the attempt has ended; it never
    # generates those tokens in the first place.  This is the stream path.)
    for tok in tokens:
        feed(state, tok)
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
        "gave_up_at": state.gave_up_at,
        "ended": state.ended,
        "final_board": state.render(),
        "trace": state.trace,
    }


# ---------------------------------------------------------------------------
# 4. PROMPT -- what the entrant may see.  Grammar section 5.
# ---------------------------------------------------------------------------

LEGEND = ("The board is a warehouse.  A hash sign is a wall you cannot walk "
          "through.  A dollar sign is a crate you can push but never pull. "
          "A full stop is a target the crates have to end up on.  An at sign "
          "is you.  A crate sitting on a target is a star, and you standing "
          "on a target is a plus sign.")

#: Grammar section 5 forbids the word "schema", any key-value framing, any
#: JSON example, any "fill in" language -- because a legend formatted as
#: key-value pairs reads as a FORM to a schema-filling model and that model
#: transcribes the prompt instead of playing.  The prohibition is measured
#: here rather than asserted: `check_prompt_legal()` is a control.
FORBIDDEN_IN_PROMPT = ("schema", "json", "key-value", "fill in", "field:",
                       "key:", "value:", "{", "}", "```")


def build_prompt(level, board, history, moves, solved):
    """The turn prompt.  Prose legend only.  No schema, no key-value."""
    hist = " ".join(history) if history else "(you have not moved yet)"
    return (
        "SOKOBAN -- the warehouse.\n"
        "\n"
        + LEGEND + "\n"
        "\n"
        "The board right now:\n"
        "\n"
        + board + "\n"
        "\n"
        "You have made " + str(moves) + " move"
        + ("" if moves == 1 else "s")
        + " so far.  Your moves in order: " + hist + ".\n"
        "The level is " + ("SOLVED" if solved else "not solved yet") + ".\n"
        "\n"
        "What is your next move?\n"
        "\n"
        "Answer with one letter and nothing else:\n"
        "U for up, D for down, L for left, R for right.\n"
        "If you believe this level can no longer be finished, write "
        "\"GIVE UP\" and nothing else.\n"
    )


def check_prompt_legal(prompt):
    """-> list of forbidden strings present in the prompt.  Empty == legal."""
    low = prompt.lower()
    return [w for w in FORBIDDEN_IN_PROMPT if w in low]


# ---------------------------------------------------------------------------
# 5. SELF-TEST -- the instrument's own controls
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


def self_test(levels_dir=None):
    c = _C()
    extra = (levels_dir,) if levels_dir else ()

    print("[0] the FROZEN bytes are the bytes we are playing")
    for name, want in sorted(FROZEN_SHA256.items()):
        try:
            got = find_level(name, extra).sha256
        except IOError:
            got = None
        c.ok(got == want, "%s digest matches sokoban/MANIFEST.txt" % name,
             (got, want))

    print("[1] parsing and round-tripping")
    one = find_level("01_one_push.txt", extra)
    two = find_level("02_two_boxes.txt", extra)
    three = find_level("03_the_corner_waiting.txt", extra)
    c.ok(one.n_boxes == 1 and one.n_targets == 1,
         "01 parses to 1 box / 1 target", (one.n_boxes, one.n_targets))
    c.ok(two.n_boxes == 2 and two.n_targets == 2,
         "02 parses to 2 boxes / 2 targets", (two.n_boxes, two.n_targets))
    c.ok(three.n_boxes == 1 and three.n_targets == 1,
         "03 parses to 1 box / 1 target", (three.n_boxes, three.n_targets))
    c.ok(render(one, set(one.start_boxes), one.start_player)
         == one.text.strip("\n"), "render(parse(x)) == x for 01")
    c.ok(render(two, set(two.start_boxes), two.start_player) == two.text.strip("\n"),
         "render(parse(x)) == x for 02")
    c.ok(render(three, set(three.start_boxes), three.start_player) == three.text.strip("\n"),
         "render(parse(x)) == x for 03")
    c.ok(one.enclosed and two.enclosed and three.enclosed,
         "all three levels are enclosed",
         (one.enclosed, two.enclosed, three.enclosed))
    c.ok(one.sha256 and len(one.sha256) == 64, "level carries a sha256")

    print("[2] A MALFORMED LEVEL IS AN ERROR, NOT A BOARD")
    for label, blob in (
            ("empty", "   \n"),
            ("illegal char", "#####\n#@$X#\n#####\n"),
            ("two players", "######\n#@ @ #\n######\n"),
            ("no player", "#####\n#$ .#\n#####\n"),
            ("no box", "#####\n#@ .#\n#####\n"),
            ("no target", "#####\n#@$ #\n#####\n"),
            ("box/target mismatch", "#######\n#@$$ .#\n#######\n"),
            ("box in a wall", "#####\n#@  #\n#####\n"),
    ):
        try:
            parse_level(blob, label)
            c.ok(False, "malformed (%s) raises" % label, "parsed anyway")
        except MalformedLevel:
            c.ok(True, "malformed (%s) raises MalformedLevel" % label)
    c.ok(parse_level("#####\n#@$.#\n####\n", "ragged").ragged is True,
         "a ragged level is PADDED, not refused [G8]")

    print("[3] the movement rules, one at a time")
    st = State(one)                      # ###### / #@$.# / #####
    c.ok(st.player == (1, 1), "01 player starts at (1,1)", st.player)
    pos, w = step(st, "U")
    c.ok(w == WORD_BLOCKED and pos == (1, 1),
         "into a wall -> blocked, position UNCHANGED [G5]", (pos, w))
    pos, w = step(st, "D")
    c.ok(w == WORD_BLOCKED and pos == (1, 1), "down is a wall too", (pos, w))
    pos, w = step(st, "L")
    c.ok(w == WORD_BLOCKED and pos == (1, 1), "left is a wall too", (pos, w))
    st2 = State(two)
    pos, w = step(st2, "D")
    c.ok(w == WORD_MOVED and pos == (2, 1), "an empty floor cell -> moved",
         (pos, w))
    try:
        step(st2, "X")
        c.ok(False, "step() refuses an unresolved letter", "accepted")
    except ValueError:
        c.ok(True, "step() refuses an unresolved letter")
    try:
        step(st2, "u")
        c.ok(False, "step() refuses a lower-case letter (the reader "
                    "upper-cases, so this is a bug if it passes)", "accepted")
    except ValueError:
        c.ok(True, "step() refuses a lower-case letter")

    print("[4] pushing -- including the push that kills the level")
    st = State(one)
    pos, w = step(st, "R")
    c.ok(w == WORD_PUSHED and pos == (1, 2) and st.boxes == {(1, 3)},
         "push the crate one cell right", (pos, w, st.boxes))
    c.ok(st.solved, "and the level is now solved")
    st = State(two)
    # 02:  ######## / #@  $ .# / #      # / #  $  .# / ########
    st.boxes = {(1, 4)}
    st.player = (1, 3)
    pos, w = step(st, "R")
    c.ok(w == WORD_PUSHED and st.boxes == {(1, 5)},
         "push a crate onto a target", (w, st.boxes))
    st.boxes = {(1, 4), (1, 5)}
    st.player = (1, 3)
    pos, w = step(st, "R")
    c.ok(w == WORD_BLOCKED and pos == (1, 3),
         "a crate pushed into another crate -> blocked", (w, pos))
    st.boxes = {(1, 6)}
    st.player = (1, 5)
    pos, w = step(st, "R")
    c.ok(w == WORD_BLOCKED, "a crate pushed into a wall -> blocked", w)
    # the irreversibility control is in group [8]

    print("[5] solved, and the move counter")
    st = State(one)
    r = play(one, ["R"])
    c.ok(r["solved"] is True and r["moves"] == 1,
         "01 is solved in ONE move", (r["solved"], r["moves"]))
    c.ok(r["attempted"] == 1 and r["blocked"] == 0
         and r["not_an_action"] == 0 and r["give_up"] == 0,
         "one clean token: attempted 1, nothing else", r)
    st = State(two)
    r = play(two, ["D", "R", "R", "R", "R", "U", "U", "R", "R", "D", "D", "L"])
    # that stream is only a smoke test -- optimality is checked by the solver,
    # not asserted here.
    c.ok(r["attempted"] == 12, "twelve tokens -> attempted 12", r["attempted"])
    c.ok(len(r["trace"]) == len(r["trace"]) and
         all("board" in ply for ply in r["trace"]),
         "every ply in the trace carries the board after it")

    print("[6] the wall-bumper -- why `moves` and `attempted` differ")
    st = State(one)
    r = play(one, ["U"] * 50)
    c.ok(r["moves"] == 0 and r["attempted"] == 50 and r["blocked"] == 50,
         "fifty wall bumps = 0 moves, 50 attempted, 50 blocked, UNSOLVED",
         (r["moves"], r["attempted"], r["blocked"], r["solved"]))

    print("[7] not-an-action and GIVE-UP are DIFFERENT COUNTERS")
    st = State(one)
    r = play(one, ["RESIGN"])
    c.ok(r["give_up"] == 1 and r["not_an_action"] == 0 and r["moves"] == 0,
         "RESIGN -> give_up 1, not_an_action 0, moves 0",
         (r["give_up"], r["not_an_action"]))
    c.ok(r["ended"] is True, "give_up ENDS the attempt [G11]")
    r = play(one, ["W"] * 3)
    c.ok(r["not_an_action"] == 3 and r["give_up"] == 0,
         "W A S D are not synonyms: three W's -> 3 not_an_action",
         (r["not_an_action"], r["give_up"]))
    r = play(one, ["Sure! I think you should push the crate right."])
    c.ok(r["not_an_action"] == 1 and r["moves"] == 0,
         "prose -> not_an_action, and it moves nothing",
         (r["not_an_action"], r["moves"]))
    r = play(one, ["UR"])
    c.ok(r["not_an_action"] == 1 and r["moves"] == 0,
         "two letters -> not_an_action, NEVER the first character [G-sec3]",
         (r["not_an_action"], r["moves"]))
    r = play(one, ['{"move": "R"}'])
    c.ok(r["not_an_action"] == 1 and r["moves"] == 0,
         "JSON -> not_an_action, and it is never read for a move")
    r = play(one, ["give up"])
    c.ok(r["give_up"] == 1, "case-insensitive abstention is accepted",
         r["give_up"])
    r = play(one, ["RESIGN", "R"])
    c.ok(r["attempted"] == 2 and r["moves"] == 0 and r["after_end"] == 1
         and r["not_an_action"] == 0,
         "a move after the attempt ended is COUNTED and not played, in its "
         "OWN counter -- not folded into not_an_action [G10]",
         (r["attempted"], r["moves"], r["after_end"], r["not_an_action"]))
    c.ok(play(one, ["R", "R", "R"])["after_end"] == 2,
         "two tokens after the level is solved -> after_end 2",
         play(one, ["R", "R", "R"])["after_end"])

    print("[8] irreversibility -- a push that can never be undone")
    st = State(three)
    # 03: ####### / #.  $ # / #  @  # / #######
    pos, w = step(st, "U")
    c.ok(w == WORD_MOVED and pos == (1, 3), "step up to row 1", (pos, w))
    pos, w = step(st, "R")
    c.ok(w == WORD_PUSHED and st.boxes == {(1, 5)},
         "the TEMPTING push: crate goes right, into the corner", (w, st.boxes))
    c.ok(not st.solved, "and the level is not solved")
    before = set(st.boxes)
    for a in ("L", "D", "U", "R", "L", "D"):
        step(st, a)
    c.ok(st.boxes == before,
         "the crate in the corner can never be moved again", st.boxes)
    c.ok(not st.solved, "the level is DEAD and the board does not say so")

    print("[9] the read grammar is the instrument")
    rd = read_answer("R")
    c.ok(rd.outcome == OUTCOME_ACTION and rd.action == "R", "'R' -> action R")
    c.ok(read_answer("r").action == "R", "case-insensitive")
    c.ok(read_answer(" R ").action == "R", "surrounding whitespace stripped [G3]")
    c.ok(read_answer("RESIGN").outcome == OUTCOME_GIVE_UP,
         "RESIGN is give_up and is NEVER read as R [G-sec3]")
    c.ok(read_answer("RD").outcome == OUTCOME_NOT_AN_ACTION,
         "RD is not_an_action, never truncated to R")
    c.ok(read_answer("R\nD").outcome == OUTCOME_NOT_AN_ACTION,
         "two non-empty lines -> not_an_action [G2]")
    c.ok(read_answer("").outcome == OUTCOME_NOT_AN_ACTION, "empty -> not_an_action")
    c.ok(read_answer(None).outcome == OUTCOME_NOT_AN_ACTION,
         "None -> not_an_action, and does not raise")
    c.ok(read_answer("W").outcome == OUTCOME_NOT_AN_ACTION,
         "W is not 'up'")
    c.ok(read_answer("R.").outcome == OUTCOME_NOT_AN_ACTION,
         "trailing punctuation -> not_an_action (fails closed)")
    c.ok(read_answer("I give up.").outcome == OUTCOME_GIVE_UP,
         "'I give up.' is an abstention")
    c.ok(read_answer("I think I will give up soon").outcome
         == OUTCOME_NOT_AN_ACTION,
         "prose containing 'give up' is NOT the token (strict match) [G1]")
    c.ok(read_answer("I think I will give up soon").loose_give_up is True,
         "...and the loose diagnostic records it, unscored [G1]")

    print("[10] what the entrant may see")
    p = build_prompt(one, one.text.strip("\n"), [], 0, False)
    c.ok(check_prompt_legal(p) == [], "the prompt is legal for the entrant",
         check_prompt_legal(p))
    for bad in ('{"move": "R"}', "key: value", "fill in the schema"):
        c.ok(check_prompt_legal(bad) != [],
             "the checker REFUSES a prompt containing %r" % bad[:18])

    print("[11] THE EXIT CODE REFLECTS THE RUN -- driven end to end")
    # The failure this group exists for: a CLI whose every real invocation
    # returned a constant 1, while the self-test reported everything green,
    # because the self-test never reached the code path that raised.
    # So this group does not inspect the return statements -- it CALLS the
    # runner, in process, for every entrant, and asserts the code that comes
    # back.  A path that is never executed has no exit code.
    try:
        import sokoban2_run as _run
        import test_sokoban2 as _side
        import io as _io
        import contextlib as _ctx
        # EVERY entrant, end to end, and the code that comes back is asserted.
        # A return statement nobody executes has no exit code.
        want = {"reference": _run.EXIT_SCORED, "liar": _run.EXIT_SCORED,
                "garbage": _run.EXIT_ZERO_MEASURED,
                "never-starts": _run.EXIT_NEVER_STARTED,
                "wall-bumper": _run.EXIT_SCORED,
                "resigner": _run.EXIT_SCORED,
                "soft-resigner": _run.EXIT_ZERO_MEASURED,
                "corner-walker": _run.EXIT_SCORED}
        for entrant in sorted(want):
            buf = _io.StringIO()
            try:
                with _ctx.redirect_stdout(buf), \
                        _ctx.redirect_stderr(_io.StringIO()):
                    got = _run.cmd_run(_run._Args(entrant, None, "off"))
            except Exception as exc:                 # noqa: BLE001
                got = "raised %r" % (exc,)
            c.ok(got == want[entrant],
                 "runner exits %s for entrant %r (got %r)"
                 % (want[entrant], entrant, got))
        # no code in the table is 1: nothing that merely ran-and-failed may
        # report 1, which is reserved for 'the instrument is not proven'.
        c.ok(1 not in want.values(),
             "no entrant's run exits 1 -- 1 is reserved for an UNPROVEN "
             "INSTRUMENT, not for a run that failed")
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(_io.StringIO()):
            got = _run.cmd_run(_run._Args("no-such-entrant", None, "off"))
        c.ok(got == _run.EXIT_USAGE,
             "an unknown entrant exits %d, not 0 and not 1"
             % _run.EXIT_USAGE, got)
        # the side script replays every bundle from the record
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf):
            good = _side.verify_all()
        c.ok(good, "RECORD: the side script replays every bundle from the "
                   "record and reproduces the counters")
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(_io.StringIO()):
            got = _run.instrument_check(None, reasoning="off",
                                        include_simulator_self_test=False)
        c.ok(got == 0, "instrument-check exits 0 when the harness is proven",
             got)
    except ImportError as exc:
        c.ok(False, "runner importable from the simulator self-test", exc)

    print("")
    total, failed = c.n, len(c.failed)
    print("SELF-TEST %s -- %d/%d controls pass"
          % ("PASS" if not failed else "FAIL", total - failed, total))
    for lab in c.failed:
        print("  FAILED: %s" % lab)
    return 0 if not failed else 1


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sokoban2.py",
        description="SOKOBAN simulator -- independent implementation #2")
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls; exit 0 iff all pass")
    ap.add_argument("--level", help="path to a level file")
    ap.add_argument("--moves", default="",
                    help="move stream, e.g. 'R' or 'U D L R'")
    ap.add_argument("--levels-dir", default=None)
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.levels_dir)

    if not args.level:
        ap.print_help()
        return 3

    level = load_level(args.level)
    toks = args.moves.split() if args.moves.strip() else []
    r = play(level, toks)
    print("  level       %s   sha256 %s" % (r["level"], r["level_sha256"][:16]))
    print("  solved      %s" % r["solved"])
    print("  moves       %-4d (successful actions -- the score)" % r["moves"])
    print("  attempted   %-4d blocked %-4d not_an_action %-4d give_up %d"
          % (r["attempted"], r["blocked"], r["not_an_action"], r["give_up"]))
    print()
    print(r["final_board"])
    return 0 if r["solved"] else 1


if __name__ == "__main__":
    sys.exit(main())
