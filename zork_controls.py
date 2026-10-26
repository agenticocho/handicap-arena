#!/usr/bin/env python3
"""ZORK'S CONTROLS THAT CAN FIRE -- a scripted walker, a scripted non-parser, and the archived rows.

CPU ONLY. No model, no server, no GPU, no network. Everything here is a function of a world file and a
list of strings, so it runs anywhere the simulator runs.

WHY THIS FILE EXISTS SEPARATELY FROM `zork.py --self-test`

`zork.py`'s controls prove the SIMULATOR's functions do what they say. They do not prove that a player
that plays well gets the objective and a player that types nonsense gets nothing -- those are claims
about a WHOLE RUN, and a run is a stream of commands through a world. So this file drives two scripted
agents, neither of which is a model:

    THE WALKER        derives its route from the ROOM GRAPH (BFS: start -> required item -> gate),
                      plays it, and MUST finish `escaped`. It is not a hardcoded solution list: it is
                      given a world and no answer, and the route it emits is checked against the
                      solution the level file documents.
    THE NON-PARSER    emits strings whose first word is neither a verb nor a direction this world knows,
                      and MUST produce ZERO accepted commands while changing NO world state.

AND BOTH ARE SHOWN ABLE TO FAIL, because a control that cannot fail is a decoration. The walker is run
three ways that must not reach the objective; the non-parser has one real command injected into its
stream and must then report exactly one acceptance. THE FAILING DIRECTIONS ARE THE POINT: without them,
`escaped` and `accepted == 0` are two numbers nobody has ever seen move.

    python3 zork_controls.py                    the walker, the non-parser, the near-misses, the archive
    python3 zork_controls.py --json OUT.json    the same, with a machine-readable artifact written
    python3 zork_controls.py --no-archive       skip the eight recorded rows (they are read, never written)

THE ARCHIVE IS READ-ONLY HERE. `probes/ZORK_*.json` are records of runs that actually happened; this
file re-attributes their commands THROUGH THE FIXED PARSER and asserts two things about every one of
them: that the FROZEN counters are reproduced EXACTLY (the additive axis is additive, not a rewrite),
and what the old `unreadable` number was actually made of.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zork as Z                                                          # noqa: E402

LEVELS = ("zork_01_the_floor", "zork_02_long_crawl")
# THE SOLUTIONS THE LEVEL FILES DOCUMENT, in their own comment blocks. The walker is NOT given these;
# it is given the world. They are here so the route it DERIVES can be checked against the route a reader
# was told, and a mismatch is a finding about one of the two.
DOCUMENTED = {"zork_01_the_floor": ["take key", "north"],
              "zork_02_long_crawl": ["north", "take key", "south", "east", "north", "east"]}


# ──────────────────────────────────────────────────────────────────────────────── the scripted walker
def route_between(w, src, dst):
    """BFS over the room graph -> the list of DIRECTIONS walking `src` to `dst`, or None.

    THE WALKER'S ONLY INTELLIGENCE, and it is a search of the world's own exits. It knows where the
    required item starts and where the gate is -- both are fields of the world, not answers whispered to
    it -- and it knows nothing about what a model would guess.
    """
    if src == dst:
        return []
    seen, frontier, back = {src}, [src], {}
    while frontier:
        nxt = []
        for room in frontier:
            for d, to in sorted(w["exits"].get(room, {}).items()):
                if to in seen:
                    continue
                seen.add(to)
                back[to] = (room, d)
                if to == dst:
                    path, cur = [], dst
                    while cur != src:
                        prev, dd = back[cur]
                        path.append(dd)
                        cur = prev
                    return list(reversed(path))
                nxt.append(to)
        frontier = nxt
    return None


def walker_plan(w):
    """-> the command list a walker emits: go to the required item, take it, go to the gate.

    Derived from the graph. Returns (commands, provenance) so a reader can see the two legs rather than
    a flat list that might have been typed by hand.
    """
    item = w["gate"]["item"]
    item_room = w["items"][item]["start"]
    to_item = route_between(w, w["start"], item_room)
    to_gate = route_between(w, item_room, w["gate"]["room"])
    if to_item is None or to_gate is None:
        return None, {"why": "the world has no route"}
    cmds = list(to_item) + [f"take {item}"] + list(to_gate)
    return cmds, {"legs": {"start_room": w["start"], "item": item, "item_room": item_room,
                           "gate_room": w["gate"]["room"]},
                  "to_item": to_item, "take": f"take {item}", "to_gate": to_gate}


# ─────────────────────────────────────────────────────────────────────────── the scripted non-parser
# EVERY ONE OF THESE HAS A FIRST WORD THAT IS NEITHER A VERB NOR A DIRECTION THIS WORLD KNOWS. The
# generator asserts that property of its own output below, because a gibberish generator that happens to
# emit `go` would be measuring the parser against a command.
GIBBERISH = [
    "e2e4", "RESIGN", "xyzzy", "flarb", "quux", "zzz", "hello", "and then", "yes please", "ok",
    "what now", "hmm", "perhaps", "42", "!!!", "0x1f", "%%%", "&&&", "...", "no idea",
    "the", "a", "to", "with", "toward", "some", "into", "on", "in", "at",
    "Try moving in a direction to explore further.",
    "Not sure what to do next.",
    "Let me consider the situation.",
    "proceed", "continue", "advance", "explore", "search", "think", "wonder",
]
# AND ONE SENTENCE IS DELIBERATELY NOT IN THAT LIST, BECAUSE THE WORLD ITSELF WOULD READ IT.
#
#     `I am not sure what to do next.`
#
# `i` is a DECLARED abbreviation for inventory (VERBS, zork.py), so the parser reads that sentence as a
# command -- and it is RIGHT to, by its own frozen vocabulary. A non-parser that opened with `I` would be
# measuring the parser's synonym list, not the absence of a command, and the first version of this file
# did exactly that: it produced 195 unattributable commands and 5 acceptances, one per cycle of the list.
#
# SO THE EXCLUSION IS A MEASURED PROPERTY AND IT IS ASSERTED IN BOTH DIRECTIONS BELOW: the `I` sentence is
# shown being ACCEPTED (in [E], as one of the shapes real entrants produced), and the generator is shown
# emitting nothing that any verb or direction in the world matches. A test that quietly drops the cases it
# fails is the same defect as a counter that quietly folds two claims into one.
I_SENTENCE = "I am not sure what to do next."


def gibberish_stream(n):
    """-> exactly `n` strings, cycling the list, each asserted to be outside the world's vocabulary."""
    out = [GIBBERISH[i % len(GIBBERISH)] for i in range(n)]
    return out


def _first_word(s):
    words = [t for t in "".join(c if c.isalnum() else " " for c in s.lower()).split() if t]
    return words[0] if words else None


def outside_the_language(w, cmds):
    """-> the commands whose first word is not a verb or a direction this world knows. THE GENERATOR'S
    OWN CONTROL: if this is not every one of them, the stream is not a non-parser."""
    return [c for c in cmds if _first_word(c) not in Z.VERBS and _first_word(c) not in Z.DIRECTIONS]


# ───────────────────────────────────────────────────────────────────── the shapes real models produced
# TAKEN VERBATIM FROM THE EIGHT RECORDED ROWS. This is not a synthetic edge-case list: it is what the
# entrants actually typed, and every one of these shapes appears in `probes/ZORK_*.json`.
NEAR_MISSES = [
    # (command, world, expected attribution, expected reason, why this one is here)
    ("Look.", "floor", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "Ministral's shape: a capitalised word with a full stop. Punctuation is stripped, the verb is read."),
    ("Take the key.", "floor", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "Ministral: `the` is noise, `key` is a declared alias."),
    ("North.", "crawl", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "Ministral: a direction with a full stop. Run on the CRAWL level, because on the FLOOR a bare "
     "`north` arrives at the gate and is REJECTED/gate_locked -- which [E] asserts as its own case."),
    ("take metal", "crawl", Z.ATTR_REJECTED, "unknown_object",
     "Bonsai, zork_02 ply 4. The room's own prose says 'something metal on a shelf' and the noun list "
     "has no `metal`. THE COMMAND IS IN THE LANGUAGE; THE NOUN IS NOT."),
    ("Try moving in a direction to explore further.", "crawl", Z.ATTR_UNATTRIBUTABLE, "no_verb",
     "Ministral, zork_02 plies 6-7. `try` is not a verb. NOT A COMMAND AT ALL."),
    ("Inspect the torch.", "crawl", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "Ministral: `inspect` is a declared synonym for look, so this is read and does nothing."),
    ("I will take the key", "floor", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "THE MEASURED PARSER PROPERTY: `i` is a declared abbreviation for inventory, so a SENTENCE "
     "opening with `I` is read as a command. The parser finds a command in text that is not one -- and "
     "this is why the non-parser's word list cannot contain an `I` sentence (see GIBBERISH)."),
    (I_SENTENCE, "crawl", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "the same property in a longer sentence: read as `inventory`. NOT unattributable, by the world's "
     "own declared vocabulary, which is why the generator excludes it rather than being scored against it."),
    ("take the key and walk north", "floor", Z.ATTR_REJECTED, "unknown_object",
     "the other measured property: a command with a trailing sentence is refused AS A WHOLE."),
    ("> Open brasskey.", "crawl", Z.ATTR_REJECTED, "nothing_to_open",
     "Ministral: `>` is stripped, `open` is a verb, and there is no gate here. An entrant trying to use "
     "the key on a door gets `nothing_to_open` -- a rejection whose reason name reads like a world fact."),
    ("take unicorn", "crawl", Z.ATTR_REJECTED, "unknown_object",
     "the prereg's own boundary case. REJECTED here, UNATTRIBUTABLE would be wrong: `take` is known."),
    ("north pole", "crawl", Z.ATTR_ACCEPTED, Z.ACCEPTED_REASON,
     "a direction read from the HEAD; the trailing word is not part of it."),
    ("go sideways", "crawl", Z.ATTR_REJECTED, "unknown_direction",
     "a verb read, an argument this world has no word for."),
    ("north", "floor", Z.ATTR_REJECTED, "gate_locked",
     "Ministral's `North.` on the FLOOR level: `north` walks INTO the gate, and the gate is TERMINAL. A "
     "correct direction that does not finish is a REJECTION, not an acceptance, and this is the row where "
     "the word 'accepted' would otherwise overstate what happened."),
]


def world_of(name):
    path = os.path.join(HERE, "levels", f"{name}.txt")
    return open(path).read(), Z.parse_world(open(path).read())


# ───────────────────────────────────────────────────────────────────────────────────────── the checks
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="write a machine-readable artifact here")
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args()

    fails, total = [], 0
    report = {}

    def ck(group, name, got, want):
        nonlocal total
        total += 1
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(f"{group}: {name}")
        report.setdefault(group, []).append({"check": name, "got": got, "want": want, "pass": ok})

    print("=" * 100)
    print("ZORK CONTROLS THAT CAN FIRE -- scripted walker, scripted non-parser, archived rows")
    print("=" * 100)
    print(f"  interpreter  python {sys.version.split()[0]}")
    print("  compute path CPU ONLY -- no model, no server, no GPU, no network")

    # ── [A] THE WALKER MUST REACH THE OBJECTIVE ────────────────────────────────────────────────────
    print("\n[A] THE SCRIPTED WALKER -- a route DERIVED FROM THE ROOM GRAPH, and it must finish")
    for name in LEVELS:
        text, w = world_of(name)
        cmds, prov = walker_plan(w)
        ck("A", f"{name}: the walker derives a plan from the graph", cmds is not None, True)
        if cmds is None:
            continue
        r = Z.play(text, cmds)
        ck("A", f"{name}: it FINISHES", (r["finished"], r["ending"]), (True, "escaped"))
        ck("A", f"{name}: it carries the required item", r["carried_required_item"], True)
        ck("A", f"{name}: zero commands were rejected", r["attribution"][Z.ATTR_REJECTED], 0)
        ck("A", f"{name}: zero commands were unattributable", r["attribution"][Z.ATTR_UNATTRIBUTABLE], 0)
        ck("A", f"{name}: every command it typed was ACCEPTED",
           r["attribution"][Z.ATTR_ACCEPTED], len(cmds))
        ck("A", f"{name}: it ends on the gate, so the graph distance is zero",
           r["progress"]["bearing"]["distance_final_room_to_gate"], 0)
        ck("A", f"{name}: it moved exactly one object -- the required one",
           r["progress"]["objects"]["moved_from_start_placement"], 1)
        # THE ROUTE THE GRAPH GAVE IS THE ROUTE THE LEVEL FILE DOCUMENTS.
        ck("A", f"{name}: the derived route == the documented solution, up to the alias",
           [c.replace("brasskey", "key") for c in cmds], DOCUMENTED[name])
        print(f"        plan: {' ; '.join(cmds)}")
        print(f"        legs: {prov['to_item']} -> {prov['take']} -> {prov['to_gate']}")
        ck("A", f"{name}: the counters agree with the attribution on this run too",
           r["attribution_checked_against_counts"], True)

    # ── [B] AND THE WALKER MUST BE ABLE TO FAIL ────────────────────────────────────────────────────
    print("\n[B] THE SAME WALKER, THREE WAYS THAT MUST NOT FINISH -- the control is not a decoration")
    text, w = world_of("zork_02_long_crawl")
    good, _prov = walker_plan(w)
    no_take = [c for c in good if not c.startswith("take")]
    r = Z.play(text, no_take)
    ck("B", "the walker WITHOUT the take reaches the gate and is LOCKED", r["ending"], "gate_locked")
    ck("B", "...and does not finish", r["finished"], False)
    ck("B", "...and moved NO object", r["progress"]["objects"]["moved_from_start_placement"], 0)
    truncated = good[:-1]
    r = Z.play(text, truncated)
    ck("B", "the walker with its LAST move cut off does not finish", (r["finished"], r["ending"]),
       (False, "out_of_commands"))
    ck("B", "...and is one room short of the gate",
       r["progress"]["bearing"]["distance_final_room_to_gate"], 1)
    backwards = list(reversed([c for c in good if c in ("north", "south", "east", "west")]))
    r = Z.play(text, backwards)
    ck("B", "the walker walking its route BACKWARDS does not finish", r["finished"], False)
    # A WORLD WHOSE GATE NOBODY CAN REACH IS NOT A HARD WORLD
    unreachable = text.replace("exit corridor north study", "exit corridor north cellar")
    try:
        Z.parse_world(unreachable)
        ck("B", "a world whose gate is unreachable is REFUSED, not silently played", "parsed", "ValueError")
    except ValueError:
        ck("B", "a world whose gate is unreachable is REFUSED, not silently played",
           "ValueError", "ValueError")

    # ── [C] THE NON-PARSER MUST PRODUCE ZERO ACCEPTED COMMANDS ─────────────────────────────────────
    print("\n[C] THE SCRIPTED NON-PARSER -- gibberish, and it must produce ZERO accepted commands")
    N = 200
    stream = gibberish_stream(N)
    ck("C", f"the generator emitted {N} commands", len(stream), N)
    ck("C", "EVERY one of them is outside this world's vocabulary -- the generator's own control",
       len(outside_the_language(w, stream)), N)
    # THE EXCLUSION IS MEASURED, NOT A CONVENIENCE. The one sentence left out of the word list is left
    # out because THIS parser reads it as a command, and that is asserted here rather than believed.
    r_i = Z.play(open(os.path.join(HERE, "levels", "zork_02_long_crawl.txt")).read(), [I_SENTENCE])
    ck("C", "the excluded `I ...` sentence IS read as a command by this world, which is why it is excluded",
       (r_i["trace"][0]["attribution"], r_i["trace"][0]["verb"]), (Z.ATTR_ACCEPTED, "inventory"))
    ck("C", "...so a non-parser built on it would be measuring the synonym list, not the language",
       r_i["attribution"][Z.ATTR_UNATTRIBUTABLE], 0)
    for name in LEVELS:
        text2, w2 = world_of(name)
        r = Z.play(text2, stream)
        ck("C", f"{name}: ZERO accepted commands", r["attribution"][Z.ATTR_ACCEPTED], 0)
        ck("C", f"{name}: every command is UNATTRIBUTABLE", r["attribution"][Z.ATTR_UNATTRIBUTABLE], N)
        ck("C", f"{name}: the frozen counter says `unparsed == {N}` too", r["counts"][Z.COUNTER_UNPARSED], N)
        ck("C", f"{name}: it did not finish", r["finished"], False)
        ck("C", f"{name}: THE WORLD DID NOT MOVE -- same room",
           r["final_room"], Z.parse_world(text2)["start"])
        ck("C", f"{name}: ...same inventory", r["final_inventory"], [])
        ck("C", f"{name}: ...zero objects moved",
           r["progress"]["objects"]["moved_from_start_placement"], 0)
        ck("C", f"{name}: ...and the distance to the gate never changed",
           r["progress"]["bearing"]["fraction_of_the_way_along_the_graph"], 0.0)

    # ── [D] AND THAT ASSERTION MUST BE ABLE TO MOVE ────────────────────────────────────────────────
    print("\n[D] ONE REAL COMMAND IN THE GIBBERISH STREAM -- the counter must move by exactly one")
    text, w = world_of("zork_02_long_crawl")
    injected = stream[:100] + ["north"] + stream[100:]
    r = Z.play(text, injected)
    ck("D", "the stream is one command longer", r["commands_consumed"], N + 1)
    ck("D", "EXACTLY ONE command is accepted", r["attribution"][Z.ATTR_ACCEPTED], 1)
    ck("D", "...and it is the one that was injected", r["trace"][100]["command"], "north")
    ck("D", "...which is the only row whose attribution is not UNATTRIBUTABLE",
       [i for i, t in enumerate(r["trace"]) if t["attribution"] != Z.ATTR_UNATTRIBUTABLE], [100])
    ck("D", "...and the world moved by that one command", r["final_room"], "cellar")
    ck("D", "...so `accepted == 0` above was not a counter stuck at zero", r["attribution"][Z.ATTR_ACCEPTED] > 0,
       True)
    # A LOOK-ONLY STREAM ALSO MOVES IT, so acceptance is not a property of movement alone
    r = Z.play(text, ["look"] * 5)
    ck("D", "five looks are five accepted commands that move nothing",
       (r["attribution"][Z.ATTR_ACCEPTED], r["final_room"]), (5, "hall"))

    # ── [E] THE SHAPES REAL ENTRANTS PRODUCED ──────────────────────────────────────────────────────
    print("\n[E] THE SHAPES THE EIGHT RECORDED ROWS ACTUALLY CONTAIN -- attributed, one by one")
    worlds = {k: world_of(v)[1] for k, v in (("floor", "zork_01_the_floor"),
                                            ("crawl", "zork_02_long_crawl"))}
    for cmd, wh, want_attr, want_reason, why in NEAR_MISSES:
        r = Z.play({"floor": open(os.path.join(HERE, "levels", "zork_01_the_floor.txt")).read(),
                    "crawl": open(os.path.join(HERE, "levels", "zork_02_long_crawl.txt")).read()}[wh], [cmd])
        got = (r["trace"][0]["attribution"], r["trace"][0]["reason"])
        ck("E", f"{cmd!r:48} -> {got[0]}/{got[1]}", got, (want_attr, want_reason))
        print(f"        {why}")

    # ── [F] THE EIGHT ARCHIVED ROWS, RE-ATTRIBUTED -- READ ONLY ────────────────────────────────────
    if not a.no_archive:
        print("\n[F] THE EIGHT RECORDED ROWS, RE-ATTRIBUTED THROUGH THE FIXED PARSER (read-only)")
        print("    The frozen counters must be reproduced EXACTLY. The additive axis must not move them.")
        rows = archive_rows()
        ck("F", "eight recorded rows were found", len(rows), 8)
        for rec in rows:
            key = f"{rec['entrant']} / {rec['level']}"
            again = Z.play(rec["level_text"], [t["command"] for t in rec["trace"]])
            ck("F", f"{key}: the FROZEN counters are reproduced exactly", again["counts"], rec["counts"])
            ck("F", f"{key}: the per-row attribution sums back to them",
               again["attribution_checked_against_counts"], True)
            ck("F", f"{key}: the score is reproduced", (again["finished"], again["ending"]),
               (rec["finished"], rec["ending"]))
        print()
        table = archive_table(rows)
        print(table)
        report["archive"] = archive_json(rows)

    print("\n" + "=" * 100)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  "
          f"{total - len(fails)}/{total}")
    print("=" * 100)
    report["summary"] = {"total": total, "failed": fails, "pass": not fails,
                         "cpu_only": True, "model_runs": 0}
    if a.json:
        with open(a.json, "w") as f:
            json.dump(report, f, indent=1)
        print(f"  artifact  {a.json}")
    return 1 if fails else 0


# ─────────────────────────────────────────────────────────────────────────────── the archived rows
def archive_rows():
    """The eight `probes/ZORK_*.json` records, READ AND NEVER WRITTEN.

    A record is a measurement that happened. This file reads it to re-attribute its commands; it does
    not repair it, rewrite it or replace it, and `--no-archive` exits without touching the directory.
    """
    import glob
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "probes", "ZORK_*.json"))):
        try:
            d = json.load(open(p))
        except ValueError:
            continue
        if "level_text" not in d or "trace" not in d:
            continue
        d["_path"] = os.path.basename(p)
        d["_sha256"] = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        out.append(d)
    return out


def attribute_row(d):
    """-> (accepted, rejected_by_reason, unattributable, detail) for one archived record."""
    again = Z.play(d["level_text"], [t["command"] for t in d["trace"]])
    reasons = {k: v for k, v in again["attribution_reasons"].items()
               if k not in Z.UNATTRIBUTABLE_REASONS and k != Z.ACCEPTED_REASON}
    return (again["attribution"][Z.ATTR_ACCEPTED], reasons,
            again["attribution"][Z.ATTR_UNATTRIBUTABLE], again)


def archive_table(rows):
    """THE TABLE THE REPORT QUOTES -- one line per recorded row, with what the old number was made of."""
    head = (f"{'entrant':34} {'level':21} {'acc':>4} {'rej':>4} {'UNATT':>5} "
            f"{'old unparsed':>12}  rejected_by_reason")
    lines = [head, "-" * len(head)]
    for d in rows:
        acc, rej, unatt, again = attribute_row(d)
        old = d["counts"].get("unparsed", 0)
        rr = ", ".join(f"{k}={v}" for k, v in sorted(rej.items())) or "-"
        lines.append(f"{d.get('entrant', '?'):34} {d.get('level', '?'):21} {acc:>4} {sum(rej.values()):>4} "
                     f"{unatt:>5} {old:>12}  {rr}")
        # THE TWO CLAIMS THE OLD NUMBER MADE, NAMED PER ROW
        unatt_rows = [t["command"] for t in again["trace"] if t["attribution"] == Z.ATTR_UNATTRIBUTABLE]
        rej_rows = [(t["command"], t["reason"]) for t in again["trace"] if t["attribution"] == Z.ATTR_REJECTED]
        if unatt_rows:
            lines.append(f"{'':34} {'':21}   not in the language: "
                         + " | ".join(repr(c)[:60] for c in unatt_rows))
        if rej_rows:
            lines.append(f"{'':34} {'':21}   rejected:           "
                         + " | ".join(f"{c!r} ({r})" for c, r in rej_rows))
    return "\n".join(lines)


def archive_json(rows):
    out = []
    for d in rows:
        acc, rej, unatt, again = attribute_row(d)
        out.append({"record": d["_path"], "record_sha256": d["_sha256"],
                    "entrant": d.get("entrant"), "level": d.get("level"),
                    "recorded_counts": d["counts"], "recomputed_counts": again["counts"],
                    "counts_reproduced": again["counts"] == d["counts"],
                    "accepted": acc, "rejected": sum(rej.values()), "rejected_by_reason": rej,
                    "unattributable": unatt,
                    "old_unreadable": d.get("unreadable"),
                    "sufficiency_ok_as_recorded": d.get("sufficiency_ok"),
                    "sufficiency_mismatched": (d.get("sufficiency") or {}).get("simulator_replay_mismatched"),
                    "progress": again["progress"],
                    "unattributable_commands": [t["command"] for t in again["trace"]
                                                if t["attribution"] == Z.ATTR_UNATTRIBUTABLE],
                    "rejected_commands": [{"command": t["command"], "reason": t["reason"]}
                                          for t in again["trace"] if t["attribution"] == Z.ATTR_REJECTED]})
    return out


if __name__ == "__main__":
    sys.exit(main())
