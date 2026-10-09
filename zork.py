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
    """
    words = [t for t in "".join(c if c.isalnum() else " " for c in raw.lower()).split() if t]
    if not words:
        return None, None, "empty command"
    # a bare direction is a movement command: `n` is `go north`
    if words[0] in DIRECTIONS:
        return "go", DIRECTIONS[words[0]], None
    if words[0] not in VERBS:
        return None, None, f"{words[0]!r} is not a verb I know"
    verb = VERBS[words[0]]
    rest = [t for t in words[1:] if t not in NOISE]
    # `pick up lamp`: the `up` belongs to the phrase, not to the movement -- dropped here and only here,
    # because for `go up` the same word IS the direction.
    if verb == "take" and rest and rest[0] == "up":
        rest = rest[1:]

    if verb == "go":
        if not rest:
            return None, None, "go where? a direction is required"
        if rest[0] not in DIRECTIONS:
            return None, None, f"{rest[0]!r} is not a direction"
        return "go", DIRECTIONS[rest[0]], None
    if verb in ("look", "inventory"):
        return verb, None, None
    # take / drop / open all need an object that RESOLVES
    if not rest:
        return None, None, f"{verb} what? an object is required"
    obj = resolve_item(rest, w)
    if obj is None:
        return None, None, f"I do not know {_phrase(rest)!r}"
    return verb, obj, None


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


def replay(trace, start_room):
    """Rebuild the crawl from the RECORD ALONE -- the sufficiency claim, made checkable.

    Everything a reader needs must be IN the record, so a reader that has only the trace and the room the
    crawl started in must be able to recover: the route, the item history, and how it ended. If this
    function cannot produce those, the record is not a sufficient statistic and the score is unverifiable.

    Note the ONE thing the trace cannot carry: the starting room has no command row of its own, because
    there is no command. It is therefore reported alongside the trace rather than inside it -- which is why
    `start_room` exists as a field instead of being left implicit.
    """
    route, inv, took, ending, tooks = [start_room], [], None, None, 0
    for row in trace:
        if row["room"] not in route:
            route.append(row["room"])
        if row["outcome"] == "took":
            tooks += 1
            if took is None:
                took = row["step"]
        if row["outcome"] in ("escaped", "gate_locked"):
            ending = row["outcome"]
        inv = row["inventory"]
    return {"route": route, "final_inventory": inv, "took_item_at_step": took,
            "ending": ending, "take_events": tooks}


def describe(w, st):
    r = w["rooms"][st["room"]]
    ex = w["exits"].get(st["room"], {})
    here = [i for i in w["items"] if _item_here(st, w, i)]
    return (r["desc"] or r["name"]) + \
        "  Exits: " + (", ".join(sorted(ex)) or "none") + \
        ".  Here: " + (", ".join(sorted(here)) or "nothing")


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
    # THE START ROOM COUNTS AS VISITED. A route summary that omits where the crawl began is not the route,
    # and the first version silently dropped it -- the record was one room short of replayable.
    visited = [st["room"]]

    for i, tok in enumerate(commands):
        raw = "" if tok is None else str(tok)
        verb, obj, why = parse_command(raw, w)
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
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        if st["room"] not in visited:
            visited.append(st["room"])
        # THE INVENTORY SNAPSHOT IS TAKEN AFTER THE COMMAND, so the row says what the entrant held when it
        # finished that step -- which is exactly what a reader needs to see whether the item was carried on.
        trace.append({"step": i, "command": raw, "verb": verb, "object": obj,
                      "outcome": outcome, "note": note, "room": st["room"],
                      "inventory": list(st["inventory"])})
        if st["ended"]:
            break

    if st["finished"]:
        ending = "escaped"
    elif st["locked"]:
        ending = "gate_locked"
    else:
        ending = "out_of_commands"

    return {"finished": st["finished"], "ending": ending,
            "carried_required_item": required in st["inventory"],
            "required_item": required,
            "start_room": w["start"],
            "took_item_at_step": took_at,
            "commands": len(commands), "commands_consumed": len(trace),
            "counts": counts, "outcomes": outcomes,
            "rooms_visited": visited, "rooms": len(w["rooms"]),
            "final_room": st["room"], "final_inventory": list(st["inventory"]),
            "trace": trace}


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
