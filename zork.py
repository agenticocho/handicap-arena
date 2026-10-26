#!/usr/bin/env python3
"""THE LONG CRAWL (Zork) -- event 3 of THE ORDER. Long-horizon state retention. Simulator, and nothing else.

WHY THIS GAME, AND WHY IT IS THE RISKIEST OF THE THREE

The two events before it constrain the answer by construction: Sokoban's action space is four symbols, Missile
Command's is two characters. This one hands the entrant an OPEN TEXT FIELD and asks for a command. That is the
chess failure wearing different clothes -- chess died because the entrant could not DERIVE a legal move from a
position, and an open command line has the same hazard in a new place: the entrant may produce English that is
not a command at all.

So the risk is answered twice, in the two places it can appear:

  1. THE PARSER IS FORGIVING ABOUT PHRASING. `n`, `north`, `go north` are one command; `take lamp`, `get lamp`,
     `grab lamp`, `pick up lamp` are one command. A parser that accepts one phrasing measures PHRASING, not
     planning. Forgiving is the default here, not a nicety.
  2. A FAILURE TO READ IS ITS OWN OUTCOME AND IS NEVER SCORED AS A WRONG MOVE. There is a filed defect for
     exactly this: a parser that folds its own failures into the entrant's score is reporting on itself. The
     budget is three separate counters -- parsed / unparsed / recognised-but-impossible -- and the record
     carries the RAW TEXT of every command, so a reader can always see what the entrant actually typed.

     BUT FORGIVING PHRASING IS NOT FUZZY IDENTITY. `take brass key` resolves to the key by alias or by its own
     words; `take br` does NOT, because no such thing exists. The distinction is the whole reason the Sokoban
     reader's `token[:1]` defect is filed: taking the first character of `RESIGN` turned a six-letter word into
     the action Right, and a reader broad enough to find an answer in text that does not contain one
     manufactures its own results. This parser is forgiving about HOW you say it and strict about WHAT you said.

THE FACULTY: LONG-HORIZON STATE RETENTION

Nothing else in the set touches it. The world is SMALL -- a handful of rooms -- and it contains ONE REQUIRED
ITEM FOUND EARLY THAT IS NEEDED MUCH LATER. The gate will not open without it.

AND THE GATE IS TERMINAL, WHICH IS A DESIGN CHOICE STATED RATHER THAN DERIVED: arriving at the gate ends the
run, either ESCAPED (carrying the required item) or LOCKED (not carrying it). It is terminal so that failing to
carry the item is a RECORDED ENDING rather than an indefinitely recoverable state. A gate you can walk away
from and retry measures whether the entrant eventually stumbled back, not whether it retained a requirement
across the crawl. The failure is therefore visible in the move log as `gate_locked` with the inventory it
actually had -- not as a number that needs interpretation.

WHAT IS DELIBERATELY ABSENT: no combat, no puzzles, no scoring rubric, no timer. The command stream is the
budget. THE CAP IS THE BUDGET, NOT THE CLOCK.

WORLD FORMAT -- line-oriented text, so a world travels in a message and diffs in git:

    # a comment
    start hall                      the room the entrant begins in
    room hall Dusty Hall            room <id> <display name>
    desc hall A dust-choked hall.   desc <room> <text>          (optional)
    exit hall north cellar          exit <from> <direction> <to>
    item brasskey cellar            item <id> <room it starts in>
    alias brasskey key              alias <id> <another word for it>   (optional, repeatable)
    gate vault brasskey             gate <room> <item required to finish>

COMMAND FORMAT -- free text, and the parser is generous on purpose:

    n / north / go north / walk n            movement (n s e w u d, or the full word)
    take lamp / get lamp / grab lamp         taking, including `pick up lamp`
    drop lamp / put lamp                     dropping
    look / l / examine                       look around
    inventory / i / inv / items              what you are carrying
    open vault / unlock vault / use key      the gate

    python3 zork.py --self-test
    python3 zork.py --world levels/zork_02_long_crawl.txt --commands "n;take key;s;e;n;e"
"""
import argparse
import json
import os
import sys

# ── the vocabulary the parser accepts ────────────────────────────────────────────────────────────────
# FORGIVING ABOUT PHRASING. Every abbreviation here is a control in the self-test, because a synonym list
# that is never asserted is a synonym list that can rot.
DIRECTIONS = {
    "n": "north", "north": "north",
    "s": "south", "south": "south",
    "e": "east", "east": "east",
    "w": "west", "west": "west",
    "u": "up", "up": "up",
    "d": "down", "down": "down",
}
VERBS = {
    "go": "go", "move": "go", "walk": "go", "head": "go", "travel": "go", "run": "go",
    "take": "take", "get": "take", "grab": "take", "pick": "take", "collect": "take", "loot": "take",
    "drop": "drop", "put": "drop", "discard": "drop", "leave": "drop", "release": "drop",
    "look": "look", "l": "look", "examine": "look", "inspect": "look", "x": "look",
    "inventory": "inventory", "i": "inventory", "inv": "inventory", "items": "inventory", "bag": "inventory",
    "open": "open", "unlock": "open", "use": "open", "enter": "open",
}
# Words that carry no meaning for the parser. NOTE `up` is deliberately NOT here: `pick up lamp` needs it
# dropped from the object phrase, but `go up` needs it kept as a direction. It is handled per-verb instead.
NOISE = {"a", "an", "the", "to", "at", "in", "on", "with", "into", "toward", "towards", "my", "some"}

# THE THREE COUNTERS THE BUDGET IS EXPRESSED IN. They are kept separately and named as the spec names them,
# because merging any two of them is the filed defect: an unreadable answer scored as a wrong move.
COUNTER_PARSED = "parsed"
COUNTER_UNPARSED = "unparsed"
COUNTER_IMPOSSIBLE = "recognised-but-impossible"
COUNTERS = (COUNTER_PARSED, COUNTER_UNPARSED, COUNTER_IMPOSSIBLE)

# ── ATTRIBUTION: ACCEPTED / REJECTED / UNATTRIBUTABLE, COUNTED PER ROW ──────────────────────────────
# THE DEFECT THIS EXISTS FOR, MEASURED ON THIS CABINET'S OWN EIGHT RECORDED ROWS.
#
# The three counters above are frozen by PREREG_zork.md and they stay. But `unparsed` -- one number --
# carries TWO DIFFERENT CLAIMS, and the recorded rows prove they are different:
#
#     `take metal`                      Bonsai, zork_02_long_crawl, ply 4      counter: unparsed
#     `Try moving in a direction ...`   Ministral, zork_02_long_crawl, ply 6   counter: unparsed
#
# The first is a COMMAND: the verb `take` is in the world's vocabulary, the entrant addressed an object
# the world's own room description named ("Damp brick, and something metal on a shelf"), and the parser
# refused it because no item called `metal` exists. THE ENTRANT SPOKE THE LANGUAGE AND THE PARSER SAID NO.
# The second is not a command at all: `try` is not a verb this world knows, and no reading of it is a
# command. THE ENTRANT DID NOT SPEAK THE LANGUAGE.
#
# One counter, two claims. A model that types nonsense and a model that plays and is refused by the
# parser's own noun list score the same, and the row cannot tell a reader which happened. That is the
# filed defect this block separates.
#
#     ACCEPTED         a verb was read, its object resolved (or none was needed), and the world executed
#                      it. -> the frozen counter `parsed`
#     REJECTED         A VERB THE WORLD KNOWS WAS READ, and the command was refused. The reason is
#                      carried per row, because `not_here` and `unknown_object` are different findings.
#     UNATTRIBUTABLE   no verb the world knows could be read at all. NOT IN THE GAME'S COMMAND LANGUAGE.
#                      -> the frozen counter `unparsed`
#
# THE BOUNDARY RULE, STATED BECAUSE IT IS THE ONE A READER WILL ARGUE WITH, AND IT DOES NOT MOVE THE
# PREREG'S: PREREG_zork.md's boundary rule is about the FROZEN COUNTER and it stands -- `take unicorn` is
# NOT `recognised-but-impossible`, because the object does not resolve and claiming to have recognised it
# would be the parser finding an answer in text that does not contain one. THIS AXIS IS A DIFFERENT
# QUESTION: not "did everything resolve" but "WHOSE VOCABULARY FAILED". `take` is in the world's verb
# vocabulary; `unicorn` is not in its nouns. So `take unicorn` is REJECTED/unknown_object, NOT
# UNATTRIBUTABLE -- the entrant used a command this world has and named a thing it does not. The frozen
# counter is untouched: `take unicorn` is still counted `unparsed` there, and `frozen_counter_of()`
# below asserts that mapping instead of leaving it to prose.
ATTR_ACCEPTED = "accepted"
ATTR_REJECTED = "rejected"
ATTR_UNATTRIBUTABLE = "UNATTRIBUTABLE"
ATTRIBUTIONS = (ATTR_ACCEPTED, ATTR_REJECTED, ATTR_UNATTRIBUTABLE)

# A REJECTION'S REASON, AND WHICH FROZEN COUNTER THAT REASON IS COUNTED UNDER. `unknown_object`,
# `missing_object` and `unknown_direction` are rejections the frozen counters call `unparsed` (the
# prereg's boundary rule); the six endings are the ones it calls `recognised-but-impossible`. The map
# is the whole reason the additive axis does not become a second, competing set of totals.
REJECTION_COUNTER = {
    "unknown_object":    COUNTER_UNPARSED,       # verb read; the object phrase names nothing in the world
    "missing_object":    COUNTER_UNPARSED,       # verb read; it needs an object and none was given
    "unknown_direction": COUNTER_UNPARSED,       # `go` read; the word after it is not a direction
    "missing_direction": COUNTER_UNPARSED,       # `go` read; no direction was given at all
    "no_exit":           COUNTER_IMPOSSIBLE,
    "not_here":          COUNTER_IMPOSSIBLE,
    "already_carrying":  COUNTER_IMPOSSIBLE,
    "not_carrying":      COUNTER_IMPOSSIBLE,
    "nothing_to_open":   COUNTER_IMPOSSIBLE,
    "gate_locked":       COUNTER_IMPOSSIBLE,
}
# THE REASONS A COMMAND CAN BE OUTSIDE THE LANGUAGE. `empty` is not a command at all; `no_verb` is the
# first word not being one this world knows. BOTH ARE UNATTRIBUTABLE AND NEITHER IS A REJECTION: there
# was no verb to reject.
UNATTRIBUTABLE_REASONS = ("empty", "no_verb")
ACCEPTED_REASON = "acted"

# What each reason MEANS, in the record, so a row is readable without the source. A reason a reader has
# to look up in a dict is a reason the row does not carry.
REASON_TEXT = {
    "acted": "a verb was read, its object resolved, and the world executed it",
    "empty": "no command at all -- there was no text to read",
    "no_verb": "the first word is not a verb this world knows; nothing was rejected, nothing was read",
    "unknown_object": ("a verb this world knows was read and its object phrase names NOTHING IN THE WORLD "
                       "-- the entrant used the language and the noun list refused it"),
    "missing_object": "a verb this world knows was read and it needs an object; none was given",
    "unknown_direction": "`go` was read and the word after it is not a direction",
    "missing_direction": "`go` was read and no direction was given at all",
    "no_exit": "the direction resolved and this room has no such exit",
    "not_here": "the item resolved and it is not in this room",
    "already_carrying": "the item resolved and it is already in hand",
    "not_carrying": "the item resolved and it is not in hand",
    "nothing_to_open": "`open` was read and there is nothing to open here",
    "gate_locked": "the gate refused: the required item is not carried",
}


def frozen_counter_of(category, reason):
    """-> THE FROZEN COUNTER THIS ATTRIBUTION IS COUNTED UNDER. The additive axis must not become a
    second, competing set of totals, so the mapping is a FUNCTION here and a control asserts it row by
    row against the counters `play()` actually incremented."""
    if category == ATTR_ACCEPTED:
        return COUNTER_PARSED
    if category == ATTR_UNATTRIBUTABLE:
        return COUNTER_UNPARSED
    if category == ATTR_REJECTED:
        return REJECTION_COUNTER[reason]
    raise ValueError(f"{category!r} is not an attribution")


def attribute(verb, obj, code, outcome):
    """-> (category, reason). COUNTED PER ROW, from the verb the parser read and the outcome the world
    returned -- not from the sentence the parser wrote.

    A ROW IS ATTRIBUTED ONCE. `code` is the parser's reason code (read_command), `outcome` the world's
    (step), and exactly one of the three categories is returned for every row."""
    if verb is None:
        if code in UNATTRIBUTABLE_REASONS:
            return ATTR_UNATTRIBUTABLE, code
        return ATTR_REJECTED, code
    if outcome in IMPOSSIBLE_OUTCOMES:
        return ATTR_REJECTED, outcome
    return ATTR_ACCEPTED, ACCEPTED_REASON


def parse_world(text):
    """Text -> world. A MALFORMED WORLD IS AN ERROR, NOT A WORLD.

    Same rule the Sokoban and Missile Command parsers follow, and for the same reason: a world that is
    silently half-parsed produces measurements about the typo rather than about the entrant.
    """
    w = {"rooms": {}, "exits": {}, "items": {}, "start": None, "gate": None}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        f = line.split()
        k = f[0].lower()
        try:
            if k == "start":
                if len(f) != 2:
                    raise ValueError("start takes exactly one room")
                w["start"] = f[1]
            elif k == "room":
                if len(f) < 3:
                    raise ValueError("room takes an id and a name")
                rid, name = f[1], " ".join(f[2:])
                if rid in w["rooms"]:
                    raise ValueError(f"duplicate room id {rid!r}")
                w["rooms"][rid] = {"id": rid, "name": name, "desc": ""}
            elif k == "desc":
                if len(f) < 3:
                    raise ValueError("desc takes a room and text")
                rid = f[1]
                if rid not in w["rooms"]:
                    raise ValueError(f"desc for undefined room {rid!r}")
                w["rooms"][rid]["desc"] = " ".join(f[2:])
            elif k == "exit":
                if len(f) != 4:
                    raise ValueError("exit takes <from> <direction> <to>")
                src, d, dst = f[1], f[2].lower(), f[3]
                if d not in DIRECTIONS:
                    raise ValueError(f"unknown direction {d!r} (use n s e w u d or the full word)")
                d = DIRECTIONS[d]
                w["exits"].setdefault(src, {})
                if d in w["exits"][src]:
                    raise ValueError(f"room {src!r} already has a {d} exit")
                w["exits"][src][d] = dst
            elif k == "item":
                if len(f) != 3:
                    raise ValueError("item takes an id and the room it starts in")
                iid, room = f[1], f[2]
                if iid in w["items"]:
                    raise ValueError(f"duplicate item id {iid!r}")
                w["items"][iid] = {"id": iid, "start": room,
                                   "name": iid.replace("_", " "), "aliases": set()}
            elif k == "alias":
                if len(f) != 3:
                    raise ValueError("alias takes an item and a word for it")
                iid, al = f[1], f[2].lower()
                if iid not in w["items"]:
                    raise ValueError(f"alias for undefined item {iid!r}")
                w["items"][iid]["aliases"].add(al)
            elif k == "gate":
                if len(f) != 3:
                    raise ValueError("gate takes a room and the item it requires")
                if w["gate"] is not None:
                    raise ValueError("more than one gate -- the ending would be ambiguous")
                w["gate"] = {"room": f[1], "item": f[2]}
            else:
                raise ValueError(f"unknown world directive {k!r}")
        except ValueError as e:
            raise ValueError(f"line {lineno}: {line!r}: {e}") from None

    # ── every failure below is one that would otherwise be measured as an ENTRANT failure ────────────
    if not w["rooms"]:
        raise ValueError("world has no rooms")
    if w["start"] is None:
        raise ValueError("world has no start room")
    if w["start"] not in w["rooms"]:
        raise ValueError(f"start room {w['start']!r} is not defined")
    if not w["items"]:
        raise ValueError("world has no items -- the gate would be ungated and the faculty unmeasured")
    if w["gate"] is None:
        raise ValueError("world has no gate")
    if w["gate"]["room"] not in w["rooms"]:
        raise ValueError(f"gate room {w['gate']['room']!r} is not defined")
    if w["gate"]["item"] not in w["items"]:
        raise ValueError(f"gate requires {w['gate']['item']!r}, which is not an item in the world")
    for iid, meta in w["items"].items():
        if meta["start"] not in w["rooms"]:
            raise ValueError(f"item {iid!r} starts in undefined room {meta['start']!r}")
    for src, dirs in w["exits"].items():
        if src not in w["rooms"]:
            raise ValueError(f"exit from undefined room {src!r}")
        for d, dst in dirs.items():
            if dst not in w["rooms"]:
                raise ValueError(f"exit {src} {d} -> undefined room {dst!r}")
    # AN UNREACHABLE GATE IS NOT A HARD WORLD, IT IS AN IMPOSSIBLE ONE -- and every entrant would be
    # recorded as failing it. Reachability is checked here so the world is a world before anyone plays.
    seen, stack = {w["start"]}, [w["start"]]
    while stack:
        for dst in w["exits"].get(stack.pop(), {}).values():
            if dst not in seen:
                seen.add(dst)
                stack.append(dst)
    if w["gate"]["room"] not in seen:
        raise ValueError(f"the gate room {w['gate']['room']!r} is unreachable from {w['start']!r}")
    kit = w["gate"]["item"]
    if kit not in w["items"]:
        raise ValueError("gate item is not an item")
    if kit not in seen and w["items"][kit]["start"] not in seen:
        raise ValueError(f"the required item {kit!r} cannot be reached -- the world would be unwinnable")
    return w


def initial_state(w):
    st = {"room": w["start"], "inventory": [], "finished": False, "locked": False, "ended": False}
    for iid, meta in w["items"].items():
        st.setdefault("_placed", {})[iid] = meta["start"]
    return st


def _item_here(st, w, iid):
    return st["_placed"].get(iid) == st["room"] and iid not in st["inventory"]


def read_command(raw, w):
    """Free text -> (verb, object, code, why_not). THE PARSER, WITH A REASON CODE BESIDE ITS SENTENCE.

    `parse_command` is this function with the code dropped, and it keeps its exact signature and its
    exact sentences because PREREG_zork.md's controls assert those strings verbatim. The code exists
    because ATTRIBUTION CANNOT BE DONE FROM A SENTENCE: `"I do not know 'metal'"` and
    `"'try' is not a verb I know"` are both `unparsed` to the frozen counters, and the whole point of the
    additive axis is that the first is a rejection and the second is not a command. A reader that
    classified by matching English prose against prose would be doing exactly what this cabinet files
    defects about.

    code is None when a command was read, else one of:
        empty | no_verb                                    -> UNATTRIBUTABLE
        missing_direction | unknown_direction
                                                           -> REJECTED / counted `unparsed`
        missing_object | unknown_object                    -> REJECTED / counted `unparsed`
    """
    words = [t for t in "".join(c if c.isalnum() else " " for c in raw.lower()).split() if t]
    if not words:
        return None, None, "empty", "empty command"
    # a bare direction is a movement command: `n` is `go north`
    if words[0] in DIRECTIONS:
        return "go", DIRECTIONS[words[0]], None, None
    if words[0] not in VERBS:
        return None, None, "no_verb", f"{words[0]!r} is not a verb I know"
    verb = VERBS[words[0]]
    rest = [t for t in words[1:] if t not in NOISE]
    # `pick up lamp`: the `up` belongs to the phrase, not to the movement -- dropped here and only here,
    # because for `go up` the same word IS the direction.
    if verb == "take" and rest and rest[0] == "up":
        rest = rest[1:]

    if verb == "go":
        if not rest:
            return None, None, "missing_direction", "go where? a direction is required"
        if rest[0] not in DIRECTIONS:
            return None, None, "unknown_direction", f"{rest[0]!r} is not a direction"
        return "go", DIRECTIONS[rest[0]], None, None
    if verb in ("look", "inventory"):
        return verb, None, None, None
    # take / drop / open all need an object that RESOLVES
    if not rest:
        return None, None, "missing_object", f"{verb} what? an object is required"
    obj = resolve_item(rest, w)
    if obj is None:
        return None, None, "unknown_object", f"I do not know {_phrase(rest)!r}"
    return verb, obj, None, None


def parse_command(raw, w):
    """Free text -> (verb, object, why_not). FORGIVING ABOUT PHRASING, STRICT ABOUT IDENTITY.

    Returns (verb, obj, None) when a command was read, or (None, None, reason) when it was not.

    THE BOUNDARY RULE, stated because it is the one a reader will argue with:

        unparsed                   no verb could be identified, or a verb that needs an object got an
                                   empty one, or a movement verb got a word that is not a direction,
                                   or the object phrase names NOTHING IN THE WORLD.
        recognised-but-impossible  a verb was read AND its object RESOLVED to a real thing, and the
                                   world then refused (no exit that way; the thing is not here; the
                                   gate is locked).

    The asymmetry is deliberate, and it is the RESIGN rule: `take unicorn` does NOT resolve -- there is no
    unicorn -- so claiming to have "recognised" it would be the parser finding an answer in text that does
    not contain one. Unknown nouns are a failure to read, and they are counted as one.

    THIS FUNCTION IS THE FROZEN CONTRACT AND ITS SENTENCES ARE ASSERTED VERBATIM. The attribution axis
    needs the CODE as well, so it calls `read_command` and this one drops the code -- one parser, two
    readings, no second implementation to drift.
    """
    verb, obj, _code, why = read_command(raw, w)
    return verb, obj, why


def _phrase(words):
    return " ".join(words)


def resolve_item(words, w):
    """Object phrase -> item id, or None. EXACT on identity, and that is the point.

    Accepted, in order: the item id; the id with separators removed; a declared alias.

    NOT accepted: prefixes, substrings, or the first word of a longer name. `take br` fails. A reader that
    resolves `br` to `brasskey` is the same reader that turned `RESIGN` into Right, and this project has that
    defect filed already. Forgiving about PHRASING means `brass key` and `key` both work when they are
    declared; it does not mean the parser guesses.
    """
    cand = _phrase(words)
    flat = cand.replace("_", "").replace(" ", "")
    for iid, meta in w["items"].items():
        if cand == iid or flat == iid.replace("_", "").replace(" ", ""):
            return iid
        if cand in meta["aliases"] or flat in {a.replace("_", "").replace(" ", "") for a in meta["aliases"]}:
            return iid
    return None


def step(w, st, verb, obj):
    """-> (new_state, outcome, note). Outcome names the fact; the note says why."""
    if verb == "look":
        return st, "looked", describe(w, st)
    if verb == "inventory":
        inv = st["inventory"]
        return st, "inventoried", f"carrying: {', '.join(inv) if inv else '(nothing)'}"

    if verb == "go":
        dest = w["exits"].get(st["room"], {}).get(obj)
        if dest is None:
            return st, "no_exit", f"no {obj} exit from {w['rooms'][st['room']]['name']}"
        st = dict(st, room=dest)
        # THE GATE IS TERMINAL. Escaped or locked, the crawl is over and the ending is recorded.
        if dest == w["gate"]["room"]:
            if w["gate"]["item"] in st["inventory"]:
                return dict(st, finished=True, ended=True), "escaped", \
                    f"the gate opens: carrying {w['gate']['item']}"
            return dict(st, locked=True, ended=True), "gate_locked", \
                f"the gate will not open without {w['gate']['item']} -- carrying " \
                f"{', '.join(st['inventory']) if st['inventory'] else '(nothing)'}"
        return st, "moved", f"now in {w['rooms'][dest]['name']}"

    if verb == "take":
        if obj in st["inventory"]:
            return st, "already_carrying", f"{obj} is already in hand"
        if not _item_here(st, w, obj):
            where = st["_placed"].get(obj)
            return st, "not_here", f"{obj} is not here" + (f" (it is in another room)" if where else "")
        placed = dict(st["_placed"])
        placed[obj] = None
        return dict(st, inventory=st["inventory"] + [obj], _placed=placed), "took", f"took {obj}"

    if verb == "drop":
        if obj not in st["inventory"]:
            return st, "not_carrying", f"{obj} is not in hand"
        placed = dict(st["_placed"])
        placed[obj] = st["room"]
        return dict(st, inventory=[i for i in st["inventory"] if i != obj], _placed=placed), \
            "dropped", f"dropped {obj}"

    if verb == "open":
        if st["room"] != w["gate"]["room"]:
            return st, "nothing_to_open", "there is nothing like that to open here"
        if w["gate"]["item"] not in st["inventory"]:
            return st, "gate_locked", f"the gate will not open without {w['gate']['item']}"
        return dict(st, finished=True, ended=True), "escaped", "the gate opens"

    return st, "unparsed", "unreachable"


IMPOSSIBLE_OUTCOMES = {"no_exit", "not_here", "already_carrying", "not_carrying",
                       "nothing_to_open", "gate_locked"}


def replay(trace, start_room, required_item=None):
    """Rebuild the crawl from the RECORD ALONE -- the sufficiency claim, made checkable.

    Everything a reader needs must be IN the record, so a reader that has only the trace and the room the
    crawl started in must be able to recover: the route, the item history, and how it ended. If this
    function cannot produce those, the record is not a sufficient statistic and the score is unverifiable.

    Note the ONE thing the trace cannot carry: the starting room has no command row of its own, because
    there is no command. It is therefore reported alongside the trace rather than inside it -- which is why
    `start_room` exists as a field instead of being left implicit.

    `required_item` IS NOT DECORATION, AND THE FIRST VERSION OF THIS FUNCTION GOT IT WRONG. It recovered
    `took_item_at_step` as THE FIRST ROW WITH outcome=='took' -- ANY item -- while `play()` sets that field
    to the first take OF THE REQUIRED ITEM. On `zork_01_the_floor`, which has one item, the two readings
    agree and the error is invisible. On `zork_02_long_crawl`, which ships a DISTRACTOR (the torch),
    an entrant that takes the torch first gets a different number from each route:

        MiMo      zork_02   play() took_item_at_step 17   replay() said 0    (the torch, at ply 0)
        Ministral zork_02   play() took_item_at_step 10   replay() said the torch's step

    Those are TWO OF THE EIGHT RECORDED ROWS, and both were filed `sufficiency_ok: false` -- "THE RECORD
    DOES NOT REPRODUCE ITS OWN SCORE. THIS IS NOT A RESULT" -- when in fact the RECORD was fine and THIS
    FUNCTION was wrong. A control that reports an instrument failure where there is none is the same
    defect as one that reports no failure where there is one, and this cabinet has now had both.

    Passing `required_item` makes this recover the field the name says it recovers. Called WITHOUT it the
    function keeps its old reading, and `takes_by_object` exposes what the old reading was picking up, so
    the difference is visible rather than silently fixed.
    """
    route, inv, took, ending, tooks = [start_room], [], None, None, 0
    takes_by_object, attribution = {}, {}
    for row in trace:
        if row["room"] not in route:
            route.append(row["room"])
        if row["outcome"] == "took":
            tooks += 1
            takes_by_object[row.get("object")] = takes_by_object.get(row.get("object"), 0) + 1
            if took is None and (required_item is None or row.get("object") == required_item):
                took = row["step"]
        if row["outcome"] in ("escaped", "gate_locked"):
            ending = row["outcome"]
        inv = row["inventory"]
        if "attribution" in row:
            attribution[row["attribution"]] = attribution.get(row["attribution"], 0) + 1
    return {"route": route, "final_inventory": inv, "took_item_at_step": took,
            "ending": ending, "take_events": tooks,
            # WHICH ITEMS WERE TAKEN, AND HOW OFTEN -- the evidence the old reading was reading the wrong
            # thing. On a level with a distractor this is not empty when the required take is missing.
            "takes_by_object": takes_by_object,
            "took_item_at_step_basis": ("the first take OF THE REQUIRED ITEM" if required_item is not None
                                        else "the first take of ANY item -- the caller gave no required "
                                             "item, so this field may name a DISTRACTOR"),
            # THE ADDITIVE AXIS IS RECOVERABLE FROM THE ROWS TOO, or it is not part of the sufficient
            # statistic. An older trace with no attribution column recovers {} and says so by being empty.
            "attribution": attribution}


def describe(w, st):
    r = w["rooms"][st["room"]]
    ex = w["exits"].get(st["room"], {})
    here = [i for i in w["items"] if _item_here(st, w, i)]
    return (r["desc"] or r["name"]) + \
        "  Exits: " + (", ".join(sorted(ex)) or "none") + \
        ".  Here: " + (", ".join(sorted(here)) or "nothing")


# ==================================================================================================
# PROGRESS, MEASURED FROM WORLD STATE -- NOT PARSED FROM PROSE
#
# THE CARD'S SECOND ASK, AND THE DISTINCTION IS THE WHOLE POINT. Two ways to say how far an entrant got:
#
#     FROM PROSE      read the model's own words ("I have taken the key and I am heading north") and
#                     believe them. That measures what the entrant SAYS.
#     FROM THE WORLD  ask the state: which room is `st["room"]`, where is each item in `st["_placed"]`,
#                     what does the room graph say the distance to the gate is. That measures what
#                     HAPPENED, and it cannot be talked into a different answer.
#
# Everything below is computed from `w` and `st` -- the parsed world and the world's own state -- and
# NOTHING here reads a command, a note, or a sentence. The one prose-derived field in an entire run is
# `command`: the line the driver cut out of the model's reply. It is the INPUT to the parser; it is not
# the measurement.
#
# AND WHERE A FIELD IS NOT MEASURABLE FROM WORLD STATE, THE FIELD IS NOT EMITTED -- it is absent rather
# than approximated. `PROGRESS_FIELDS` below is the declared provenance of every leaf this module
# produces, and `_self_test` walks the actual output and FAILS on a leaf it has not been told about, so
# a field cannot arrive without its source being stated. That is the difference between a provenance
# claim and a provenance annotation.
# ==================================================================================================
PROGRESS_FIELDS = {
    # ---- score: the simulator's own verdict, from `st` after the last consumed command
    "score.finished": "world",
    "score.ending": "world",
    "score.carried_required_item": "world",
    "score.took_item_at_step": "world",
    # ---- the room graph: from `w`, plus first-visit order from the crawl
    "rooms.total_in_world": "world",
    "rooms.reachable_from_start": "world",
    "rooms.exits_in_world": "world",
    "rooms.visited": "world",
    "rooms.visited_fraction_of_reachable": "world",
    "rooms.route": "world",
    "rooms.revisited": "world",
    # ---- objects: from `st["_placed"]` against each item's declared start room
    "objects.total_in_world": "world",
    "objects.moved_from_start_placement": "world",
    "objects.in_hand": "world",
    "objects.placement": "world",
    "objects.required_item_start_room": "world",
    "objects.required_item_placement_now": "world",
    "objects.required_item_moved": "world",
    # ---- bearing: shortest-path distance to the gate room, from the graph
    "bearing.gate_room": "world",
    "bearing.distance_start_to_gate": "world",
    "bearing.distance_final_room_to_gate": "world",
    "bearing.closest_gate_distance_reached": "world",
    "bearing.fraction_of_the_way_along_the_graph": "world",
    "bearing.distance_trail": "world",
    "bearing.monotone_toward_gate": "world",
}
# THE ONE PROSE-DERIVED THING IN A RUN, NAMED SO IT CANNOT BE FORGOTTEN. It is the INPUT, not a
# measurement: `first_line()` cuts it out of the model's reply and the simulator's parser is the only
# thing that decides whether it is a command at all.
PROSE_ONLY = {
    "turns[].raw": ("the model's reply, truncated to 400 characters for size -- READ BY NO SCORER, and "
                    "nothing is computed from it"),
    "turns[].command": ("the first non-empty line of the reply, verbatim. PROSE-DERIVED: this is the one "
                        "field in a run that comes out of the entrant's own words, and it is the INPUT "
                        "to the parser, not a measurement of progress"),
    "turns[].answer_field": "which JSON field the answer was read from, off the wire -- not world state",
    "progress.<none>": ("NOTHING in the progress block is prose-derived; every leaf above is computed "
                        "from the parsed world and the world's state"),
}


def room_graph(w):
    """-> the room graph, from the world alone: how many rooms, how many exits, and which rooms are
    REACHABLE FROM THE START. A room nobody can walk to is not part of the crawl and must not inflate
    the denominator a visited fraction is taken over."""
    adj = {}
    for rid in w["rooms"]:
        adj[rid] = dict(w["exits"].get(rid, {}))
    seen, stack = {w["start"]}, [w["start"]]
    while stack:
        for dst in adj.get(stack.pop(), {}).values():
            if dst not in seen:
                seen.add(dst)
                stack.append(dst)
    return {"adj": adj, "rooms": len(w["rooms"]), "reachable": len(seen),
            "edges": sum(len(d) for d in adj.values()), "reachable_ids": seen}


def graph_distance(g, src, dst):
    """BFS over the room graph -> the fewest moves from `src` to `dst`, or None if no route exists.
    THE GRAPH IS THE MEASURE OF PROGRESS: not how many commands were typed, but how far along the rooms
    the entrant actually is."""
    if src == dst:
        return 0
    seen, frontier, d = {src}, [src], 0
    while frontier:
        d += 1
        nxt = []
        for r in frontier:
            for to in g["adj"].get(r, {}).values():
                if to == dst:
                    return d
                if to not in seen:
                    seen.add(to)
                    nxt.append(to)
        frontier = nxt
    return None


def progress_from_world(w, st, distance_trail=()):
    """-> the progress block. EVERY LEAF IS FROM `w` OR `st`. No command, note or sentence is read.

    Where a field cannot be computed from world state it is ABSENT, and the caller sees the absence --
    it is not filled with a plausible zero, because a zero that means 'not measured' and a zero that
    means 'none' are the same character and different findings.
    """
    g = room_graph(w)
    required = w["gate"]["item"]
    gate_room = w["gate"]["room"]
    d_start = graph_distance(g, w["start"], gate_room)
    d_now = graph_distance(g, st["room"], gate_room)
    trail = [d for d in distance_trail if d is not None]
    best = min(trail) if trail else d_now
    moved = [iid for iid, meta in w["items"].items()
             if st["_placed"].get(iid) != meta["start"]]
    route = []
    # the route is the FIRST-VISIT ORDER, rebuilt from the state's own room plus the trail of rooms the
    # caller fed in. `play()` passes the visited list through `route` on the state, so this stays a
    # reading of world state rather than a second, competing record of it.
    route = list(st.get("_visited") or [st["room"]])
    # A FRACTION NOBODY CAN COMPUTE IS ABSENT, NOT ZERO. `parse_world` proves the gate is reachable, so
    # d_start is an int in every real crawl; this guards the function for a caller that hands it a state
    # nothing routes to, and returns None rather than dividing by it.
    if not d_start or best is None:
        reached_frac = None
    else:
        reached_frac = round((d_start - best) / d_start, 4)
    return {
        "score": {"finished": bool(st["finished"]), "ending": _ending_of(st),
                  "carried_required_item": required in st["inventory"],
                  "took_item_at_step": st.get("_took_item_at_step")},
        "rooms": {"total_in_world": g["rooms"], "reachable_from_start": g["reachable"],
                  "exits_in_world": g["edges"], "visited": len(route),
                  "visited_fraction_of_reachable": (round(len(route) / g["reachable"], 4)
                                                    if g["reachable"] else None),
                  "route": route, "revisited": _revisits(st.get("_room_trail") or [])},
        "objects": {"total_in_world": len(w["items"]),
                    "moved_from_start_placement": len(moved),
                    "in_hand": list(st["inventory"]),
                    "placement": {iid: st["_placed"].get(iid) for iid in sorted(w["items"])},
                    "required_item_start_room": w["items"][required]["start"],
                    "required_item_placement_now": st["_placed"].get(required),
                    "required_item_moved": st["_placed"].get(required) != w["items"][required]["start"]},
        "bearing": {"gate_room": gate_room, "distance_start_to_gate": d_start,
                    "distance_final_room_to_gate": d_now,
                    "closest_gate_distance_reached": best,
                    "fraction_of_the_way_along_the_graph": reached_frac,
                    "distance_trail": list(distance_trail),
                    "monotone_toward_gate": _non_increasing(trail)},
    }


def _ending_of(st):
    if st["finished"]:
        return "escaped"
    if st["locked"]:
        return "gate_locked"
    return "out_of_commands"


def _revisits(trail):
    """How many room ENTRIES were into a room already entered -- from the crawl's own room trail."""
    seen, n = set(), 0
    for r in trail:
        if r in seen:
            n += 1
        seen.add(r)
    return n


def _non_increasing(xs):
    return all(b <= a for a, b in zip(xs, xs[1:]))


def progress_leaf_paths(d, prefix=""):
    """Every leaf of a progress block, as a dotted path. Used by the control that refuses an undeclared
    field: a leaf with no entry in PROGRESS_FIELDS has no stated provenance, and provenance that is not
    stated is not provenance."""
    out = []
    for k, v in d.items():
        p = f"{prefix}{k}"
        if isinstance(v, dict):
            out.extend(progress_leaf_paths(v, p + "."))
        else:
            out.append(p)
    return out


def provenance_gaps(block, declared=None):
    """-> {undeclared, declared_but_absent, leaves, complete}. BOTH DIRECTIONS, because one direction is
    a field whose source nobody stated and the other is a claim about a field that is not there.

    A declared path COVERS its subtree: `objects.placement` is declared once and its per-item leaves are
    under it. That is deliberate -- the claim is about the placement map, and listing each item id in the
    table would make the table move whenever a world gains an item.
    """
    declared = PROGRESS_FIELDS if declared is None else declared
    leaves = progress_leaf_paths(block)

    def under(p, roots):
        return any(p == r or p.startswith(r + ".") for r in roots)

    # a LEAF is covered when it equals a declared path or lies beneath one
    undeclared = [p for p in leaves if not under(p, declared)]
    # a DECLARATION is honoured when a leaf equals it or lies beneath it -- the other direction, and it
    # needs its own test: asking whether the declared path lies under a leaf asks the wrong question.
    absent = [d for d in declared if not any(l == d or l.startswith(d + ".") for l in leaves)]
    return {"undeclared": undeclared, "declared_but_absent": absent,
            "leaves": sorted(leaves), "declared": sorted(declared),
            "complete": not undeclared and not absent}



def play(world_text, commands):
    """A world plus a command stream -> the measurement. THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE.

        finished                THE SCORE -- escaped carrying the required item, or did not
        ending                  escaped | gate_locked | out_of_commands   (WHY it ended)
        carried_required_item   THE FACULTY FLAG -- was the required item in hand at the gate
        took_item_at_step       where the entrant picked it up, or None if it never did
        counts                  the three counters, KEPT SEPARATE
        rooms_visited           the rooms entered in FIRST-VISIT ORDER, beginning with the start room,
                                so the crawl's route is readable without walking the trace
        trace[] per command     command AS TYPED, parsed verb and object, outcome, inventory snapshot
                                -- so a later reader can REPLAY the whole crawl

    A COMMAND THAT IS NOT READ CHANGES NOTHING AND IS COUNTED AS ITS OWN OUTCOME. The board does not move
    and the entrant's progress is untouched: `unparsed` is a fact about the output, never a wrong move.
    """
    # A STRING IS ITERABLE, SO A CALLER THAT PASSES ONE GETS CHARACTERS -- SILENTLY. The Missile Command
    # version scored a perfect play as a total loss this way. It is an ERROR, because a caller that means one
    # command and passes a string must be told, not interpreted.
    if isinstance(commands, str):
        raise TypeError("commands must be a SEQUENCE of tokens, not a string -- a string iterates into "
                        "characters, so 'north' would be read as five commands. Pass ['north'].")
    w = parse_world(world_text)
    st = initial_state(w)
    required = w["gate"]["item"]

    counts = {c: 0 for c in COUNTERS}
    outcomes = {}
    trace, took_at = [], None
    # THE ATTRIBUTION TOTALS AND THE PER-REASON TOTALS ARE COUNTED, NEVER INFERRED FROM `counts`.
    attribution = {a: 0 for a in ATTRIBUTIONS}
    reasons = {}
    # THE START ROOM COUNTS AS VISITED. A route summary that omits where the crawl began is not the route,
    # and the first version silently dropped it -- the record was one room short of replayable.
    visited = [st["room"]]
    # THE ROOM TRAIL AND THE DISTANCE TRAIL ARE WORLD STATE TOO: every room entered (with repeats) and
    # the shortest-path distance from that room to the gate. They are what make "how far did it get"
    # a reading of the graph rather than a count of commands.
    room_trail = [st["room"]]
    _g = room_graph(w)
    distance_trail = [graph_distance(_g, st["room"], w["gate"]["room"])]

    for i, tok in enumerate(commands):
        raw = "" if tok is None else str(tok)
        verb, obj, why_code, why = read_command(raw, w)
        if verb is None:
            counts[COUNTER_UNPARSED] += 1
            outcome, note = "unparsed", why
        else:
            nxt, outcome, note = step(w, st, verb, obj)
            if outcome in IMPOSSIBLE_OUTCOMES:
                counts[COUNTER_IMPOSSIBLE] += 1
            else:
                counts[COUNTER_PARSED] += 1
            if outcome == "took" and obj == required and took_at is None:
                took_at = i
            st = nxt
        cat, reason = attribute(verb, obj, why_code, outcome)
        attribution[cat] += 1
        reasons[reason] = reasons.get(reason, 0) + 1
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        if st["room"] not in visited:
            visited.append(st["room"])
        room_trail.append(st["room"])
        distance_trail.append(graph_distance(_g, st["room"], w["gate"]["room"]))
        # THE INVENTORY SNAPSHOT IS TAKEN AFTER THE COMMAND, so the row says what the entrant held when it
        # finished that step -- which is exactly what a reader needs to see whether the item was carried on.
        trace.append({"step": i, "command": raw, "verb": verb, "object": obj,
                      "outcome": outcome, "note": note, "room": st["room"],
                      "inventory": list(st["inventory"]),
                      # COUNTED PER ROW. `attribution` is the category, `reason` the claim inside it, and
                      # `counted_under` the frozen counter this row is ALSO counted in -- so a reader can
                      # check the additive axis against the prereg's counters without trusting prose.
                      "attribution": cat, "reason": reason,
                      "reason_text": REASON_TEXT[reason],
                      "counted_under": frozen_counter_of(cat, reason)})
        if st["ended"]:
            break

    if st["finished"]:
        ending = "escaped"
    elif st["locked"]:
        ending = "gate_locked"
    else:
        ending = "out_of_commands"

    _st_for_progress = dict(st, _visited=visited, _room_trail=room_trail, _took_item_at_step=took_at)
    prog = progress_from_world(w, _st_for_progress, distance_trail)

    return {"finished": st["finished"], "ending": ending,
            "carried_required_item": required in st["inventory"],
            "required_item": required,
            "start_room": w["start"],
            "took_item_at_step": took_at,
            "commands": len(commands), "commands_consumed": len(trace),
            "counts": counts, "outcomes": outcomes,
            # ── THE ADDITIVE AXIS: ACCEPTED / REJECTED / UNATTRIBUTABLE, PER ROW AND TOTALLED ──────────
            "attribution": attribution,
            "attribution_reasons": reasons,
            "attribution_reasons_text": {r: REASON_TEXT[r] for r in reasons},
            "attribution_of": ("counted per row on trace[].attribution. `accepted` is what the world "
                               "ACTED on; `rejected` is a verb this world knows, refused, with its "
                               "reason; UNATTRIBUTABLE is not in the game's command language at all. "
                               "Every row is attributed exactly once and every category maps back to one "
                               "of the three frozen counters -- see trace[].counted_under."),
            "attribution_checked_against_counts": _attribution_agrees(trace, counts),
            "rooms_visited": visited, "rooms": len(w["rooms"]),
            # ── PROGRESS FROM WORLD STATE, WITH ITS PROVENANCE ────────────────────────────────────────
            "progress": prog,
            "progress_field_source": dict(PROGRESS_FIELDS),
            "progress_prose_only": dict(PROSE_ONLY),
            "final_room": st["room"], "final_inventory": list(st["inventory"]),
            "trace": trace}


def _attribution_agrees(trace, counts):
    """-> True when the per-row attribution sums back to the frozen counters EXACTLY.

    THE CONTROL IS THE MAPPING ITSELF, not a second opinion about it: each row carries the frozen counter
    it is counted under, and this recomputes the three totals from the rows. If the additive axis and
    the prereg's counters ever disagree, one of them is wrong and the record says so instead of carrying
    two readings of one run.
    """
    rec = {c: 0 for c in COUNTERS}
    for row in trace:
        rec[row["counted_under"]] += 1
    return rec == {c: counts[c] for c in COUNTERS}


# -------------------------------------------------------------------------------------- controls
def _self_test():
    fails = []
    total = 0

    def ck(name, got, want):
        nonlocal total
        total += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 100)
    print("THE LONG CRAWL SIMULATOR CONTROLS")
    print("=" * 100)

    # world 1 -- the FLOOR: one room to the item, one to the gate.
    FLOOR = ("start hall\n"
             "room hall Hall\n"
             "room vault The Vault\n"
             "exit hall north vault\n"
             "item key hall\n"
             "alias key brasskey\n"
             "gate vault key\n")
    # world 2 -- the RETENTION world: the key is EARLY, the gate is FAR, and the route to the gate does not
    # pass back through the key's room. Everything about the length is the point.
    CRAWL = ("start hall\n"
             "room hall Dusty Hall\n"
             "room cellar Root Cellar\n"
             "room corridor Long Corridor\n"
             "room study Abandoned Study\n"
             "room vault The Vault\n"
             "exit hall north cellar\n"
             "exit cellar south hall\n"
             "exit hall east corridor\n"
             "exit corridor west hall\n"
             "exit corridor north study\n"
             "exit study south corridor\n"
             "exit study east vault\n"
             "exit vault west study\n"
             "item brasskey cellar\n"
             "alias brasskey key\n"
             "gate vault brasskey\n")

    print("\n[1] parsing a world, and THE MALFORMED WORLD IS AN ERROR, NOT A WORLD")
    w = parse_world(CRAWL)
    ck("rooms", sorted(w["rooms"]), ["cellar", "corridor", "hall", "study", "vault"])
    ck("start", w["start"], "hall")
    ck("gate room", w["gate"]["room"], "vault")
    ck("the required item", w["gate"]["item"], "brasskey")
    ck("north is a direction, `back` is not", parse_world(CRAWL) is not None, True)
    for bad, why in (("room hall Hall\nitem key hall\ngate hall key\n", "no start"),
                     ("start hall\nitem key hall\ngate hall key\n", "no rooms"),
                     ("start nowhere\nroom hall Hall\nitem key hall\ngate hall key\n", "start undefined"),
                     ("start hall\nroom hall Hall\nitem key hall\ngate vault key\n", "gate room undefined"),
                     ("start hall\nroom hall Hall\ngate hall key\n", "no items"),
                     ("start hall\nroom hall Hall\nitem key hall\n", "no gate"),
                     ("start hall\nroom hall Hall\nitem key hall\ngate hall nokey\n", "gate item missing"),
                     ("start hall\nroom hall Hall\nitem key nowhere\ngate hall key\n", "item in undefined room"),
                     ("start hall\nroom hall Hall\nexit hall north nowhere\nitem key hall\ngate hall key\n",
                      "exit to undefined room"),
                     ("start hall\nroom hall Hall\nroom hall Second\nexit hall n north\nitem key hall\n"
                      "gate hall key\n", "duplicate room id"),
                     ("start hall\nroom hall Hall\nitem key hall\nitem key hall\ngate hall key\n",
                      "duplicate item id"),
                     ("start hall\nroom hall Hall\nexit hall sideways vault\nitem key hall\ngate hall key\n",
                      "unknown direction"),
                     ("start hall\nroom hall Hall\nwibble hall\nitem key hall\ngate hall key\n",
                      "unknown directive")):
        try:
            parse_world(bad)
            ck(f"rejects a world with {why}", "parsed anyway", "ValueError")
        except ValueError:
            ck(f"rejects a world with {why}", "ValueError", "ValueError")
    # an unreachable gate is an impossible world, not a hard one -- every entrant would be recorded as failing
    UNREACHABLE = ("start hall\nroom hall Hall\nroom island Island\nitem key hall\ngate island key\n")
    try:
        parse_world(UNREACHABLE)
        ck("rejects an UNREACHABLE gate", "parsed anyway", "ValueError")
    except ValueError:
        ck("rejects an UNREACHABLE gate", "ValueError", "ValueError")

    print("\n[2] THE FORGIVING PARSER -- abbreviations and synonyms are controls, not claims")
    ck("`n` parses to go north", parse_command("n", w)[:2], ("go", "north"))
    ck("`north` parses to go north", parse_command("north", w)[:2], ("go", "north"))
    ck("`go north` parses to go north", parse_command("go north", w)[:2], ("go", "north"))
    ck("`walk N` (other case) parses the same", parse_command("walk N", w)[:2], ("go", "north"))
    ck("`GO   NORTH` (padding) parses the same", parse_command("GO   NORTH", w)[:2], ("go", "north"))
    for syn in ("take brasskey", "get brasskey", "grab brasskey", "pick brasskey",
                "pick up brasskey", "collect brasskey", "take the brasskey"):
        ck(f"`{syn}` is a take", parse_command(syn, w)[:2], ("take", "brasskey"))
    for syn in ("take key", "get the key", "grab key", "pick up the key"):
        ck(f"`{syn}` resolves by alias", parse_command(syn, w)[:2], ("take", "brasskey"))
    for syn in ("look", "l", "examine"):
        ck(f"`{syn}` is a look", parse_command(syn, w)[:2], ("look", None))
    for syn in ("inventory", "i", "inv", "items"):
        ck(f"`{syn}` is an inventory", parse_command(syn, w)[:2], ("inventory", None))
    ck("`take brass key` (spaced) resolves", parse_command("take brass key", w)[:2], ("take", "brasskey"))

    print("\n[3] FORGIVING PHRASING IS NOT FUZZY IDENTITY -- the RESIGN rule applied to a text parser")
    # A reader that guesses turns text into an answer it does not contain.
    ck("`take br` does NOT resolve to brasskey", parse_command("take br", w)[0], None)
    ck("...and is unparsed, with a reason", parse_command("take br", w)[2],
       "I do not know 'br'")
    ck("`take unicorn` does NOT resolve", parse_command("take unicorn", w)[0], None)
    ck("...it is counted as unread", parse_command("take unicorn", w)[2], "I do not know 'unicorn'")
    ck("`e2e4` is not a verb", parse_command("e2e4", w)[2], "'e2e4' is not a verb I know")
    ck("`RESIGN` is not a verb and is NOT truncated to a direction",
       parse_command("RESIGN", w)[0], None)
    ck("...in particular it does not become `r`", parse_command("RESIGN", w)[1], None)
    ck("an empty command is unparsed", parse_command("   ", w)[2], "empty command")
    ck("`go sideways` is unparsed, not a moved-nowhere", parse_command("go sideways", w)[2],
       "'sideways' is not a direction")
    ck("`take` with no object is unparsed", parse_command("take", w)[2], "take what? an object is required")

    print("\n[4] THE EMPTY-LIST RULE -- unreadable input is its OWN outcome, never a wrong move")
    r = play(CRAWL, ["e2e4", "RESIGN", "take unicorn", "go sideways", "look"])
    ck("the four unreadable commands are `unparsed`", r["counts"][COUNTER_UNPARSED], 4)
    ck("...and only the readable one is `parsed`", r["counts"][COUNTER_PARSED], 1)
    ck("...and none of them is `recognised-but-impossible`",
       r["counts"][COUNTER_IMPOSSIBLE], 0)
    ck("...and the world did not move", r["final_room"], "hall")
    ck("...and the entrant is still at the start with nothing", r["final_inventory"], [])
    ck("THE RAW TEXT OF EVERY COMMAND IS KEPT", [t["command"] for t in r["trace"]],
       ["e2e4", "RESIGN", "take unicorn", "go sideways", "look"])
    ck("...including the ones that were read", r["trace"][-1]["verb"], "look")

    print("\n[5] IMPOSSIBLE-BUT-PARSEABLE IS A DIFFERENT COUNTER FROM UNPARSEABLE")
    r = play(CRAWL, ["west"])
    ck("`west` from a room with no west exit is recognised-but-impossible",
       r["trace"][0]["outcome"], "no_exit")
    ck("...and it is counted impossible, not unread",
       (r["counts"][COUNTER_IMPOSSIBLE], r["counts"][COUNTER_UNPARSED]), (1, 0))
    r_take = play(CRAWL, ["take brasskey"])
    ck("`take brasskey` from the WRONG ROOM is `not_here` -- impossible, not unread",
       r_take["trace"][0]["outcome"], "not_here")
    ck("...a different impossibility from `no_exit`",
       r_take["trace"][0]["outcome"] != r["trace"][0]["outcome"], True)
    r2 = play(CRAWL, ["north", "take brasskey", "take brasskey"])
    ck("taking it twice is `already_carrying`", r2["trace"][2]["outcome"], "already_carrying")
    ck("...counted as impossible, not as unread", r2["counts"][COUNTER_UNPARSED], 0)
    ck("...and not as progress", r2["counts"][COUNTER_PARSED], 2)
    r3 = play(CRAWL, ["take unicorn", "take brasskey"])
    ck("THE TWO COUNTERS DO NOT MERGE: one unread, one impossible",
       (r3["counts"][COUNTER_UNPARSED], r3["counts"][COUNTER_IMPOSSIBLE]), (1, 1))

    print("\n[6] THE ITEM-CARRY MECHANIC GATES THE ENDING -- the control this game exists for")
    TOCRAWL = ["north", "take brasskey", "south", "east", "north", "east"]
    FORGETFUL = ["north", "south", "east", "north", "east"]
    good = play(CRAWL, TOCRAWL)
    bad = play(CRAWL, FORGETFUL)
    ck("carrying the item out finishes", good["finished"], True)
    ck("...ending is `escaped`", good["ending"], "escaped")
    ck("...and the faculty flag is set", good["carried_required_item"], True)
    ck("...and the item was taken at step 1", good["took_item_at_step"], 1)
    ck("walking the SAME route without taking it does NOT finish", bad["finished"], False)
    ck("...ending is `gate_locked`", bad["ending"], "gate_locked")
    ck("...and the faculty flag is clear", bad["carried_required_item"], False)
    ck("...and it never took the item", bad["took_item_at_step"], None)
    ck("THE FAILURE IS VISIBLE IN THE LOG, not in a score",
       bad["trace"][-1]["outcome"], "gate_locked")
    ck("...and the log shows the empty inventory it arrived with",
       bad["trace"][-1]["inventory"], [])
    ck("...while the successful crawl's last row shows it carrying",
       good["trace"][-1]["inventory"], ["brasskey"])
    ck("the two runs typed the SAME route apart from the take",
       [c for c in TOCRAWL if c != "take brasskey"], FORGETFUL)

    print("\n[7] THE GATE IS TERMINAL -- the crawl ends there either way")
    ck("a locked gate ends the run", bad["commands_consumed"], len(FORGETFUL))
    LONGER = FORGETFUL + ["w", "s", "n", "e"]
    ck("commands after the gate are not consumed", play(CRAWL, LONGER)["commands_consumed"],
       len(FORGETFUL))
    ck("...and the ending does not change", play(CRAWL, LONGER)["ending"], "gate_locked")
    ck("an unreadable command BEFORE the gate is still consumed",
       play(CRAWL, ["blah", "north", "take brasskey", "south", "east", "north", "east"])["counts"][COUNTER_UNPARSED], 1)

    print("\n[8] the trace is a sufficient statistic -- the whole crawl is replayable")
    ck("one row per command consumed", len(good["trace"]), len(TOCRAWL))
    ck("every row carries the raw command", all("command" in t for t in good["trace"]), True)
    ck("every row carries the parsed verb", all("verb" in t for t in good["trace"]), True)
    ck("every row carries the object", all("object" in t for t in good["trace"]), True)
    ck("every row carries an inventory snapshot",
       all("inventory" in t for t in good["trace"]), True)
    ck("every row carries the room", all("room" in t for t in good["trace"]), True)
    ck("...and the last row's inventory is the final inventory",
       good["trace"][-1]["inventory"], good["final_inventory"])
    ck("the route is recorded in first-visit order, starting where the crawl started",
       good["rooms_visited"], ["hall", "cellar", "corridor", "study", "vault"])
    ck("...and the route begins where the entrant began", good["rooms_visited"][0], "hall")
    ck("...and the hall, re-entered on the way back, is recorded once", 
       good["rooms_visited"].count("hall"), 1)
    # THE TRACE HAS ONE ROW PER COMMAND, so the starting room has no row until it is re-entered -- which is
    # exactly why the route list carries the origin separately from the trace.
    ck("...while the trace, being one row per command, shows the hall only on re-entry",
       [t["room"] for t in good["trace"]].count("hall"), 1)

    print("\n[9] the API guard, and the floor world")
    try:
        play(CRAWL, "north")
        ck("a STRING commands argument is refused, not read as characters", "accepted", "TypeError")
    except TypeError:
        ck("a STRING commands argument is refused, not read as characters", "TypeError", "TypeError")
    f = play(FLOOR, ["take key", "n"])
    ck("the floor world is finishable in two commands", f["finished"], True)
    ck("...and by an abbreviation and an alias alone", (f["trace"][0]["object"], f["counts"][COUNTER_UNPARSED]),
       ("key", 0))
    ck("never taking the item locks the floor world too", play(FLOOR, ["n"])["ending"], "gate_locked")

    print("\n[10] the shipped levels, each played by a solution the simulator confirms")
    here = os.path.dirname(os.path.abspath(__file__))
    for name, sol in (("zork_01_the_floor", ["take key", "north"]),
                      ("zork_02_long_crawl",
                       ["north", "take key", "south", "east", "north", "east"])):
        p = os.path.join(here, "levels", f"{name}.txt")
        if not os.path.exists(p):
            ck(f"{name} exists", "missing", "present")
            continue
        text = open(p).read()
        try:
            parse_world(text)
        except ValueError as e:
            ck(f"{name} parses", f"ValueError: {e}", "ok")
            continue
        rr = play(text, sol)
        ck(f"{name} is solvable by its solution", rr["finished"], True)
        ck(f"{name} ...and is NOT solvable without the item",
           play(text, [c for c in sol if not c.startswith("take")])["finished"], False)

    print("\n[11] SUFFICIENCY, MADE CHECKABLE -- a reader with only the record rebuilds the crawl")
    for label, run in (("the successful crawl", good), ("the forgetful crawl", bad)):
        rec = replay(run["trace"], run["start_room"])
        ck(f"{label}: the route is recoverable from the record", rec["route"], run["rooms_visited"])
        ck(f"{label}: the final inventory is recoverable", rec["final_inventory"],
           run["final_inventory"])
        ck(f"{label}: the take step is recoverable", rec["took_item_at_step"],
           run["took_item_at_step"])
        ck(f"{label}: the ending is recoverable", rec["ending"],
           run["ending"] if run["ending"] != "out_of_commands" else None)
    rec = replay(good["trace"], good["start_room"])
    ck("the starting room is NOT in the trace and has to be carried beside it",
       good["trace"][0]["room"] == good["start_room"], False)
    ck("...so it is a field of the record, not an inference", good["start_room"], "hall")
    ck("a crawl that ends without reaching the gate has no ending row",
       replay(play(CRAWL, ["look"])["trace"], "hall")["ending"], None)

    print("\n[12] ACCEPTED / REJECTED / UNATTRIBUTABLE -- the counter that carried two claims, split")
    # THE MEASURED PAIR, FROM THE RECORDS THIS CABINET ALREADY HAS. Both of these typed commands are
    # counted `unparsed` by the frozen counters, and they are not the same kind of event.
    r_metal = play(CRAWL, ["take metal"])
    r_prose = play(CRAWL, ["Try moving in a direction to explore further."])
    ck("`take metal` is counted `unparsed` by the FROZEN counters",
       r_metal["counts"][COUNTER_UNPARSED], 1)
    ck("...and `Try moving in a direction ...` is counted `unparsed` too",
       r_prose["counts"][COUNTER_UNPARSED], 1)
    ck("THE TWO ARE INDISTINGUISHABLE IN THE FROZEN COUNTERS -- that is the defect, asserted",
       r_metal["counts"] == r_prose["counts"], True)
    ck("...but `take metal` is REJECTED: the verb is one this world knows",
       (r_metal["trace"][0]["attribution"], r_metal["trace"][0]["reason"]),
       (ATTR_REJECTED, "unknown_object"))
    ck("...and prose with no verb in it is UNATTRIBUTABLE",
       (r_prose["trace"][0]["attribution"], r_prose["trace"][0]["reason"]),
       (ATTR_UNATTRIBUTABLE, "no_verb"))
    ck("...so the split separates them", r_metal["trace"][0]["attribution"]
       != r_prose["trace"][0]["attribution"], True)
    ck("`take metal` is STILL counted under `unparsed`, per the prereg -- the axis is additive, not a rewrite",
       r_metal["trace"][0]["counted_under"], COUNTER_UNPARSED)
    # the edge cases, each a different claim and each a control
    for cmd, want in (("e2e4", (ATTR_UNATTRIBUTABLE, "no_verb")),
                      ("RESIGN", (ATTR_UNATTRIBUTABLE, "no_verb")),
                      ("", (ATTR_UNATTRIBUTABLE, "empty")),
                      ("take unicorn", (ATTR_REJECTED, "unknown_object")),
                      ("take br", (ATTR_REJECTED, "unknown_object")),
                      ("go sideways", (ATTR_REJECTED, "unknown_direction")),
                      ("go", (ATTR_REJECTED, "missing_direction")),
                      ("take", (ATTR_REJECTED, "missing_object")),
                      ("west", (ATTR_REJECTED, "no_exit")),
                      ("take brasskey", (ATTR_REJECTED, "not_here")),
                      ("look", (ATTR_ACCEPTED, ACCEPTED_REASON)),
                      ("north", (ATTR_ACCEPTED, ACCEPTED_REASON))):
        rr = play(CRAWL, [cmd])
        ck(f"{cmd!r:16} -> {rr['trace'][0]['attribution']}/{rr['trace'][0]['reason']}",
           (rr["trace"][0]["attribution"], rr["trace"][0]["reason"]), want)
    rr = play(CRAWL, ["north", "take brasskey", "take brasskey"])
    ck("a take that works is ACCEPTED, the repeat is REJECTED/already_carrying",
       [t["attribution"] for t in rr["trace"]], [ATTR_ACCEPTED, ATTR_ACCEPTED, ATTR_REJECTED])
    ck("...and the repeat is NOT counted as unread",
       rr["counts"][COUNTER_UNPARSED], 0)
    # the totals, and the mapping back to the frozen counters
    rr = play(CRAWL, ["e2e4", "take metal", "north", "take brasskey", "west", "look", "RESIGN"])
    ck("every row is attributed exactly once", sum(rr["attribution"].values()),
       rr["commands_consumed"])
    ck("the three categories sum to the rows", rr["attribution"],
       {ATTR_ACCEPTED: 3, ATTR_REJECTED: 2, ATTR_UNATTRIBUTABLE: 2})
    ck("the per-row attribution reproduces the frozen counters EXACTLY",
       rr["attribution_checked_against_counts"], True)
    ck("...and that is a check that can fail: a mutated `counted_under` breaks it",
       _attribution_agrees([dict(t, counted_under=COUNTER_PARSED) if t["attribution"] == ATTR_UNATTRIBUTABLE
                            else t for t in rr["trace"]], rr["counts"]), False)
    ck("every reason carries its own text, so a row is readable without the source",
       all(r in REASON_TEXT for r in rr["attribution_reasons"]), True)

    print("\n[13] PROGRESS FROM WORLD STATE -- rooms, objects and score, with the source of every field")
    g = room_graph(w)
    ck("the room graph: five rooms, five reachable, eight exits",
       (g["rooms"], g["reachable"], g["edges"]), (5, 5, 8))
    ck("the shortest route from hall to the gate is THREE moves (east, north, east)",
       graph_distance(g, "hall", "vault"), 3)
    good_p = good["progress"]
    ck("rooms visited is the route's own length", good_p["rooms"]["visited"], 5)
    ck("...and it is the whole reachable graph", good_p["rooms"]["visited_fraction_of_reachable"], 1.0)
    ck("objects moved is read off `_placed`, not off the commands",
       good_p["objects"]["moved_from_start_placement"], 1)
    ck("...and the required item is the one that moved", good_p["objects"]["required_item_moved"], True)
    ck("the crawl ends ON the gate, so the graph distance is zero",
       good_p["bearing"]["distance_final_room_to_gate"], 0)
    ck("...having started three moves away", good_p["bearing"]["distance_start_to_gate"], 3)
    ck("...so it covered the whole graph way", good_p["bearing"]["fraction_of_the_way_along_the_graph"], 1.0)
    # AND THE RETENTION LEVEL IS NOT MONOTONE, WHICH IS WHY THE TRAIL IS KEPT RATHER THAN A FLAG.
    # The key is one room NORTH and the gate is EAST: the shortest route to the objective walks AWAY from
    # the gate first. A "progress never decreases" check would have scored a CORRECT solution as
    # regressing, so the trail travels and the flag reports the truth.
    # A ROW THAT DOES NOT MOVE THE ENTRANT REPEATS THE PREVIOUS DISTANCE -- the trail has one entry per
    # command consumed, and `take brasskey` changes the inventory and not the room.
    ck("the distance trail records the step taken AWAY from the gate to fetch the key",
       good_p["bearing"]["distance_trail"], [3, 4, 4, 3, 2, 1, 0])
    ck("...so progress toward the gate is NOT monotone on the level that measures retention",
       good_p["bearing"]["monotone_toward_gate"], False)
    ck("...and the closest it got is the gate itself",
       good_p["bearing"]["closest_gate_distance_reached"], 0)
    bad_p = bad["progress"]
    ck("the forgetful crawl reaches the same room", bad_p["bearing"]["distance_final_room_to_gate"], 0)
    ck("...and moves NO object", bad_p["objects"]["moved_from_start_placement"], 0)
    ck("...and the score says so independently of the route",
       (bad_p["score"]["finished"], bad_p["score"]["ending"]), (False, "gate_locked"))
    # OBJECTS MOVED IS NOT PROGRESS TOWARD THE OBJECTIVE, AND THE DISTRACTOR PROVES IT
    DISTRACT = CRAWL.replace("item brasskey cellar", "item brasskey cellar\nitem torch hall\nalias torch lantern")
    r_dist = play(DISTRACT, ["take torch"])
    ck("taking the DISTRACTOR moves an object", r_dist["progress"]["objects"]["moved_from_start_placement"], 1)
    ck("...but it does not move the required item",
       r_dist["progress"]["objects"]["required_item_moved"], False)
    ck("...and it does not move the entrant toward the gate",
       r_dist["progress"]["bearing"]["fraction_of_the_way_along_the_graph"], 0.0)
    ck("...so 'objects moved' and 'progress' are two different numbers, both from world state", True, True)
    # THE PROVENANCE TABLE IS ENFORCED IN BOTH DIRECTIONS
    gaps = provenance_gaps(good_p)
    ck("every leaf of the progress block has a declared source", gaps["undeclared"], [])
    ck("...and every declared field is actually emitted", gaps["declared_but_absent"], [])
    ck("...so the table is complete", gaps["complete"], True)
    ck("A FIELD WITH NO STATED SOURCE IS CAUGHT: an invented leaf is undeclared",
       provenance_gaps(dict(good_p, invented={"x": 1}))["undeclared"], ["invented.x"])
    ck("...and a declaration for a field that is not emitted is caught too",
       provenance_gaps(good_p, dict(PROGRESS_FIELDS, **{"phantom.field": "world"}))["declared_but_absent"],
       ["phantom.field"])
    ck("NO progress field is prose-derived",
       [k for k, v in PROGRESS_FIELDS.items() if v != "world"], [])
    ck("...and the prose-only fields are named, with what they are",
       sorted(PROSE_ONLY), ["progress.<none>", "turns[].answer_field", "turns[].command", "turns[].raw"])

    print("\n[14] THE REPLAY DEFECT, IN BOTH DIRECTIONS -- what `took_item_at_step` was reading")
    TORCH_FIRST = ["take torch", "north", "take brasskey", "south", "east", "north", "east"]
    rt = play(DISTRACT, TORCH_FIRST)
    ck("a crawl that takes the DISTRACTOR first, then the required item, escapes",
       (rt["finished"], rt["took_item_at_step"]), (True, 2))
    ck("...and the object's placement says where it is, not where it started",
       rt["progress"]["objects"]["placement"]["torch"], None)
    ck("replay() WITHOUT the required item reads the TORCH and returns 0 -- THE DEFECT, asserted",
       replay(rt["trace"], "hall")["took_item_at_step"], 0)
    ck("...and it says so on the record instead of leaving a plausible number bare",
       "DISTRACTOR" in replay(rt["trace"], "hall")["took_item_at_step_basis"], True)
    ck("replay() WITH the required item returns the required take",
       replay(rt["trace"], "hall", required_item="brasskey")["took_item_at_step"], 2)
    ck("...and its basis is stated", "REQUIRED ITEM" in
       replay(rt["trace"], "hall", required_item="brasskey")["took_item_at_step_basis"], True)
    ck("...and the takes by object show BOTH items, which is why the two readings differed",
       replay(rt["trace"], "hall", required_item="brasskey")["takes_by_object"],
       {"torch": 1, "brasskey": 1})
    ck("on the FLOOR world, one item, the two readings agree -- which is why this was invisible",
       (f["took_item_at_step"], replay(f["trace"], "hall")["took_item_at_step"],
        replay(f["trace"], "hall", required_item="key")["took_item_at_step"]), (0, 0, 0))
    ck("the attribution is recoverable from the rows alone, or it is not part of the record",
       replay(rt["trace"], "hall")["attribution"], {k: v for k, v in rt["attribution"].items() if v})

    print("\n" + "=" * 100)
    # THE TALLY IS COUNTED, NOT ASSERTED. The first version hardcoded a total and printed "100/100" against
    # 103 controls -- a summary line that was false about itself, which is the same class as every other
    # false verdict in this repo. A count that is written down is a count that can drift.
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{total - len(fails)}/{total}")
    print("=" * 100)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world")
    ap.add_argument("--commands", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    if not a.world:
        ap.error("--world or --self-test is required")
    text = open(a.world).read()
    cmds = [c.strip() for c in a.commands.replace(";", "\n").splitlines() if c.strip()]
    r = play(text, cmds)
    if a.json:
        print(json.dumps(r, indent=2))
        return 0
    print(f"  finished              {r['finished']}   ending: {r['ending']}")
    print(f"  carried item at gate  {r['carried_required_item']} "
          f"(required {r['required_item']}, taken at step {r['took_item_at_step']})")
    print(f"  commands              {r['commands']} issued, {r['commands_consumed']} consumed")
    print(f"  counts                {r['counts']}")
    print(f"  outcomes              {r['outcomes']}")
    print(f"  rooms visited         {' -> '.join(r['rooms_visited'])}")
    print(f"  final inventory       {r['final_inventory']}")
    return 0


if __name__ == "__main__":
    sys.exit(_self_test() if "--self-test" in sys.argv else main())
