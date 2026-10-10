#!/usr/bin/env python3
# alt_reading.py -- A SECOND, DELIBERATELY LITERAL READING OF THE SAME PROSE.
#
# This file is NOT part of the frozen cabinet.  It is the evidence for
# section 4F: it implements the same 91-word paragraph with the OPPOSITE
# decision on every clause the prose left open, and `prose_check.py` runs the
# two readings on identical answer streams to measure where they diverge.
#
# It shares no code with digdug.py.  It re-parses the level text itself.  It
# is deliberately small: a second implementation that is a copy of the first
# proves nothing.
#
# Every switch below is a place where two competent implementers, reading the
# same paragraph, would both have been reasonable -- and would have produced
# different scores from identical answers.
#
# Stdlib only.

from collections import deque

WALL, SOIL, TUNNEL, PLAYER, HAZARD, TGT_SOIL, TGT_TUN = "#", "%", " ", "P", \
                                                        "H", "T", "*"
DELTA = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
ORDER = ("U", "D", "L", "R")

#: THE LITERAL DEFAULTS.  Each one is the reading a careful implementer gets
#: by refusing to add anything the paragraph does not say.
LITERAL = {
    "U1_hazard_clock_every": 2,     # "its own clock" -- the prose gives no
                                    # rate, so the smallest non-trivial one
    "U2_hazard_starts_in_soil": True,   # "a grid of soil": a hazard stands in
                                    # soil, and soil is not a tunnel, so it
                                    # has no route at t=0 and never moves
    "U3_target_persists": True,     # nothing says a collected target is
                                    # removed from the board
    "U4_adjacent_kills": True,      # "what happens when they are adjacent"
                                    # -- the literal answer is: something
    "U5_wait_is_a_turn": True,      # "whether the player may stop" -- yes
    "U7_collection_after_clock": True,  # the turn resolves in full, then the
                                    # objective is awarded
    "U8_hazards_sequential": True,  # index order
    "U9_grid_wraps": True,          # nothing says the grid is bounded
    "A1_hazards_dig": True,         # nothing says a hazard cannot dig
    "A6_unknown_letter_blocks": True,   # step() is total
    "A8_blocked_is_free": True,     # a move that went nowhere cost nothing
    "A11_tokens": ("RESIGN", "GIVEUP"),  # the intersection of the two
                                    # Sokoban lists -- the minimal reading
    "A13_first_line_is_the_answer": True,  # a permissive reader
    "A17_counters_from_state": False,  # count the WORD, not the state:
                                    # a move that collects buried treasure
                                    # is a collection and not also a dig
}

#: The frozen cabinet's decisions, for the side-by-side.
FROZEN = {
    "U1_hazard_clock_every": 1, "U2_hazard_starts_in_soil": False,
    "U3_target_persists": False, "U4_adjacent_kills": False,
    "U5_wait_is_a_turn": False, "U7_collection_after_clock": False,
    "U8_hazards_sequential": False, "U9_grid_wraps": False,
    "A1_hazards_dig": False, "A6_unknown_letter_blocks": False,
    "A8_blocked_is_free": False,
    "A11_tokens": "<31 tokens -- see digdug_reader.GIVE_UP_TOKENS>",
    "A13_first_line_is_the_answer": False,
    "A17_counters_from_state": True,
}


class AltLevel(object):
    def __init__(self, text, name="<alt>"):
        rows = [ln for ln in text.split("\n") if ln.strip() or ln == ""]
        while rows and not rows[-1].strip():
            rows.pop()
        w = max(len(r) for r in rows)
        self.rows = [r.ljust(w, WALL) for r in rows]
        self.h, self.w = len(self.rows), w
        self.name = name
        self.walls, self.soil, self.open = set(), set(), set()
        self.targets, self.player, self.hazards = set(), None, []
        for r, row in enumerate(self.rows):
            for c, ch in enumerate(row):
                cell = (r, c)
                if ch == WALL:
                    self.walls.add(cell)
                elif ch == SOIL:
                    self.soil.add(cell)
                elif ch == TUNNEL:
                    self.open.add(cell)
                elif ch == PLAYER:
                    self.player = cell
                    self.open.add(cell)
                elif ch == HAZARD:
                    self.hazards.append(cell)
                    self.open.add(cell)
                elif ch == TGT_SOIL:
                    self.targets.add(cell)
                    self.soil.add(cell)
                elif ch == TGT_TUN:
                    self.targets.add(cell)
                    self.open.add(cell)


class AltState(object):
    def __init__(self, lvl, cfg):
        self.lvl = lvl
        self.cfg = cfg
        self.player = lvl.player
        self.dug = set()
        self.collected = set()
        self.hazards = list(lvl.hazards)
        # [U2] the literal reading: a hazard stands in SOIL, so its cell is
        # not a tunnel and it has no route anywhere.
        self.open = set(lvl.open)
        if cfg["U2_hazard_starts_in_soil"]:
            self.open -= set(lvl.hazards)
        self.turn = 0
        self.dead = False
        self.solved = False
        self.last_moved = False
        self.last_dug = False

    @property
    def tunnels(self):
        return self.open | self.dug

    def targets_left(self):
        return self.lvl.targets - self.collected


def _wrap(cfg, lvl, cell):
    r, c = cell
    if cfg["U9_grid_wraps"]:
        return r % lvl.h, c % lvl.w
    return cell


def _in_bounds(lvl, cell):
    return 0 <= cell[0] < lvl.h and 0 <= cell[1] < lvl.w


def _passable(st, cell):
    return cell in st.tunnels


def _neighbours(st, cell):
    out = []
    for d in ORDER:
        dr, dc = DELTA[d]
        n = _wrap(st.cfg, st.lvl, (cell[0] + dr, cell[1] + dc))
        if not _in_bounds(st.lvl, n):
            continue
        if n in st.lvl.walls:
            continue
        out.append((d, n))
    return out


def _tunnel_neighbours(st, cell):
    return [(d, n) for d, n in _neighbours(st, cell) if _passable(st, n)]


def alt_step(st, action):
    """The literal transition function.  Total: an unknown letter is a block
    [A6], and out-of-bounds wraps [U9] instead of blocking."""
    cfg, lvl = st.cfg, st.lvl
    if action not in DELTA:
        if cfg["A6_unknown_letter_blocks"]:
            return st.player, "blocked", False
        raise ValueError(action)
    dr, dc = DELTA[action]
    dst = _wrap(cfg, lvl, (st.player[0] + dr, st.player[1] + dc))
    if not _in_bounds(lvl, dst) or dst in lvl.walls:
        return st.player, "blocked", False
    dug_now = dst in lvl.soil and dst not in st.dug
    if dst in lvl.soil:
        st.dug.add(dst)
    word = "dug" if dug_now else "moved"
    if dst in st.targets_left():
        st.collected.add(dst)
        if not cfg["U3_target_persists"]:
            word = "collected"
        else:
            word = "collected"
    st.player = dst
    return st.player, word, True


def _hazard_bfs(st, h, target, allow_dig):
    """One hazard step.  With A1 on, the hazard digs through soil too, so the
    soil barrier does not exist at all."""
    if h == target:
        return h
    # [U2] the literal reading, taken seriously: a hazard that is standing in
    # SOIL is not in a tunnel, and the prose lets it travel only through
    # tunnels, so it cannot move at all -- however much open ground is next
    # to it.  The first build of this probe only removed the hazard's own
    # cell from the tunnel set and it still walked out; that was the probe
    # being wrong, not the clause being unobservable.
    if st.cfg["U2_hazard_starts_in_soil"] and h not in st.tunnels             and not allow_dig:
        return h
    prev = {h: None}
    q = deque((h,))
    while q:
        cur = q.popleft()
        if cur == target:
            break
        for _d, n in _neighbours(st, cur):
            if allow_dig or _passable(st, n):
                if n not in prev:
                    prev[n] = cur
                    q.append(n)
    if target not in prev:
        return h
    node = target
    while prev[node] != h:
        node = prev[node]
    return node


def alt_turn(st, action):
    """The literal turn.  Note the ORDER: the clock ticks first when
    U7_collection_after_clock is set, so a player that collects the last
    target beside a hazard dies and does NOT solve."""
    cfg = st.cfg
    pos, word, moved = alt_step(st, action)
    events = [word]
    st.last_moved = moved
    st.last_dug = (word in ("dug", "collected")
                   and st.player in st.lvl.soil)

    tick = True
    if not moved and cfg["A8_blocked_is_free"]:
        tick = False
    if action == "WAIT" and cfg["U5_wait_is_a_turn"]:
        tick = True

    solved_now = not st.targets_left()

    if solved_now and not cfg["U7_collection_after_clock"]:
        st.solved = True
        st.turn += 1
        return word, events

    if tick and (st.turn + 1) % cfg["U1_hazard_clock_every"] == 0:
        if cfg["U8_hazards_sequential"]:
            for i, h in enumerate(st.hazards):
                st.hazards[i] = _hazard_bfs(st, h, st.player,
                                            cfg["A1_hazards_dig"])
        else:
            snap = list(st.hazards)
            st.hazards = [_hazard_bfs(st, h, st.player, cfg["A1_hazards_dig"])
                          for h in snap]

    # the death check: same cell, or adjacent [U4]
    for h in st.hazards:
        if h == st.player:
            st.dead = True
            events.append("killed")
            break
        if cfg["U4_adjacent_kills"]:
            for _d, n in _neighbours(st, st.player):
                if n == h:
                    st.dead = True
                    events.append("killed_adjacent")
                    break
        if st.dead:
            break

    st.turn += 1
    if solved_now and not st.dead:
        st.solved = True
        events.append("solved")
    return word, events


def alt_read(raw, cfg):
    """The literal reader: the FIRST line is the answer [A13], and the
    abstention list is two tokens [A11]."""
    if raw is None:
        return None, "not_an_action"
    lines = [ln for ln in str(raw).splitlines() if ln.strip()]
    if not lines:
        return None, "not_an_action"
    line = lines[0].strip()
    up = line.upper()
    if up in cfg["A11_tokens"]:
        return None, "give_up"
    if cfg["U5_wait_is_a_turn"] and up in ("WAIT", "STAY", "HOLD", "PASS"):
        return "WAIT", "action"
    if len(line) == 1 and up in DELTA:
        return up, "action"
    if cfg["A13_first_line_is_the_answer"] and len(line) > 1:
        for ch in line:
            if ch.upper() in DELTA:
                return ch.upper(), "action"
    return None, "not_an_action"


def alt_play(text, tokens, cfg=None, budget=30, name="<alt>"):
    """Play one stream under one reading.  -> the fields prose_check diffs."""
    cfg = dict(LITERAL if cfg is None else cfg)
    lvl = AltLevel(text, name)
    st = AltState(lvl, cfg)
    emitted = consumed = after_end = 0
    blocked = dug = moved = collected = not_an = give_up = 0
    died_at = None
    gave_up = False
    for raw in tokens:
        if st.dead or st.solved or gave_up or emitted >= budget:
            after_end += 1
            emitted += 1
            continue
        emitted += 1
        consumed += 1
        action, outcome = alt_read(raw, cfg)
        if outcome == "give_up":
            give_up += 1
            gave_up = True
            continue
        if outcome == "not_an_action":
            not_an += 1
            continue
        word, events = alt_turn(st, action)
        if cfg["A17_counters_from_state"]:
            if not st.last_moved:
                blocked += 1
            elif st.last_dug:
                dug += 1
            else:
                moved += 1
            if word == "collected":
                collected += 1
        elif word == "blocked":
            blocked += 1
        elif word == "dug":
            dug += 1
        elif word == "moved":
            moved += 1
        elif word == "collected":
            collected += 1
        if st.dead and died_at is None:
            died_at = st.turn
    if st.solved:
        terminal = "SOLVED"
    elif st.dead:
        terminal = "KILLED"
    elif gave_up:
        terminal = "GAVE_UP"
    elif emitted >= budget:
        terminal = "BUDGET_EXHAUSTED"
    else:
        terminal = "UNSOLVED"
    return {
        "solved": bool(st.solved), "terminal": terminal,
        "died_at_turn": died_at, "turns_used": st.turn,
        "answers_emitted": emitted, "answers_consumed": consumed,
        "answers_after_end": after_end, "blocked": blocked, "dug": dug,
        "moved": moved, "collected": collected, "not_an_action": not_an,
        "give_up": give_up,
        "hazards_moved": any(h != o for h, o in zip(st.hazards,
                                                    lvl.hazards)),
        "cells_dug": len(st.dug),
    }
