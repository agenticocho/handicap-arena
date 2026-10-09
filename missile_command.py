#!/usr/bin/env python3
"""MISSILE COMMAND -- event N of THE ORDER. Allocation under scarcity. Simulator, and nothing else.

BUILT TO THE FOUR CONSTRAINTS THE CHESS FAILURE PRODUCED, because they filter by construction rather than
by hope:

  1. NO LEGAL-MOVE GENERATION. THE INCOMING MISSILES ARE THE STATE. Naming one is PLAYING THE GAME, not
     choosing from a supplied menu -- which is the distinction that mattered: chess failed because the move
     list had to be handed over, and this game cannot have that problem because the threats ARE the board.
  2. NO EXTERNAL ORACLE. The simulator resolves the volley and scores it. The score is a COUNT.
  3. SHORT ANSWERS. ONE ACTION IS TWO CHARACTERS -- a silo and a threat, e.g. `2Q`. A two-character answer
     cannot be deliberated into a token cap, which is how Ornith burned 2314 tokens and never committed.
  4. FORMAT A. Allocation under scarcity: total interceptor ammo is LESS than the number of threats, so the
     entrant must spend on what matters. THE FACULTY IS THE CHOICE, and the choice is only visible because
     some threats are aimed at cities and some are aimed at empty ground.

WHAT THE ENTRANT MUST READ TO PLAY: a threat's impact coordinate. A threat landing on a city kills it; one
landing on empty ground does nothing. Ammo is scarce, so the correct play is to let the harmless ones
through -- WHICH IS THE WHOLE MEASUREMENT. An entrant that fires at everything runs out and loses cities.

STATE FORMAT -- line-oriented text, so a state travels in a message and diffs in git:

    tick 0
    city A at 2
    city B at 5
    silo 1 at 0 ammo 2
    silo 2 at 9 ammo 2
    threat P impact 2 tick 5
    threat Q impact 7 tick 3

ACTION FORMAT -- `<silo><threat>`, two characters, nothing more: `2Q` means silo 2 engages threat Q.
`PASS` is a legal action and means spend nothing this tick.

    python3 missile_command.py --self-test
    python3 missile_command.py --state levels/mc_01.txt --actions "1P 2Q"
"""
import sys

# A SILO CAN ONLY REACH SO FAR. This is what makes it allocation rather than bookkeeping: without range,
# every threat is equally engageable and scarcity alone would make the problem trivial.
RANGE = 4


def parse_state(text):
    """Text -> state. A malformed state is an ERROR, not a board whose measurements are about something
    else -- the same rule the Sokoban parser follows and for the same reason."""
    st = {"tick": 0, "cities": {}, "silos": {}, "threats": {}}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        f = line.split()
        k = f[0].lower()
        try:
            if k == "tick":
                st["tick"] = int(f[1])
            elif k == "city":
                # city A at 2
                st["cities"][f[1]] = int(f[3])
            elif k == "silo":
                # silo 1 at 0 ammo 2
                st["silos"][f[1]] = {"at": int(f[3]), "ammo": int(f[5])}
            elif k == "threat":
                # threat P impact 2 tick 5
                st["threats"][f[1]] = {"impact": int(f[3]), "tick": int(f[5])}
            else:
                raise ValueError(f"unknown state line {line!r}")
        except (IndexError, ValueError) as e:
            raise ValueError(f"malformed state line {line!r}: {e}") from None
    if not st["cities"]:
        raise ValueError("state has no cities")
    if not st["silos"]:
        raise ValueError("state has no silos")
    if not st["threats"]:
        raise ValueError("state has no threats")
    dup = {c for c in st["cities"].values()}
    if len(dup) != len(st["cities"]):
        raise ValueError("two cities share a coordinate -- one hit would be scored as two")
    for t in st["threats"].values():
        if t["tick"] <= st["tick"]:
            raise ValueError("a threat impacts at or before the current tick -- already landed, or the "
                             "state is inconsistent and its result would be about the state, not the play")
    return st


def engageable(st, silo, threat):
    """A silo reaches a threat if the impact coordinate is within RANGE of the silo's position."""
    s, t = st["silos"].get(silo), st["threats"].get(threat)
    return bool(s and t and abs(s["at"] - t["impact"]) <= RANGE)


def play(state_text, actions):
    """A state plus an action stream -> the measurement. THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE:

        cities_surviving   THE SCORE -- a count, and the reason this event needs no engine
        trace[] per tick   action, outcome, threats remaining, ammo remaining, cities alive
                           so a later reader can REPLAY the volley

    OUTCOMES, and the last three are DIFFERENT CLAIMS that must never be merged into one another:

        fired        an interceptor launched and the threat destroyed
        passed       PASS -- a legal action that spends nothing
        no_ammo      the silo had none left
        out_of_range the silo cannot reach that threat
        unknown      no such silo or no such threat
        malformed    the token was not an action at all -- COUNTED, NEVER SCORED AS A WRONG MOVE
        late         the threat had already hit before this tick

    AN UNREADABLE ANSWER IS COUNTED AS ITS OWN OUTCOME. That is the empty-list rule: a parser that folds
    its own failures into the entrant's score is reporting on itself. `malformed` is a fact about the
    output; the board is unchanged and the tick still advances.
    """
    st = parse_state(state_text)
    # A STRING IS ITERABLE, SO A CALLER THAT PASSES ONE GETS CHARACTERS -- SILENTLY. `play(state, "1P")`
    # produced two malformed actions ('1' and 'P') and scored a perfect play as a total loss. The same
    # shape as every other defect here: a reader broad enough to accept the wrong thing. It is an ERROR
    # now, because a caller that means one action and passes a string must be told, not interpreted.
    if isinstance(actions, str):
        raise TypeError("actions must be a SEQUENCE of tokens, not a string -- a string iterates into "
                        "characters, so '1P' would be read as two actions. Pass ['1P'].")
    alive = dict(st["cities"])
    threats = dict(st["threats"])
    ammo = {k: v["ammo"] for k, v in st["silos"].items()}
    pos = {k: v["at"] for k, v in st["silos"].items()}

    horizon = max(t["tick"] for t in threats.values())
    trace = []
    counts = {k: 0 for k in ("fired", "passed", "no_ammo", "out_of_range", "unknown",
                             "malformed", "late", "hit", "spared")}

    for i, tok in enumerate(actions):
        tick = st["tick"] + i
        raw = (tok or "").strip().upper()
        outcome, note = None, ""

        if raw == "PASS":
            outcome = "passed"
        elif len(raw) < 2:
            outcome = "malformed"
            note = f"{tok!r} is not an action (a silo letter and a threat letter, or PASS)"
        else:
            silo, threat = raw[0], raw[1] if len(raw) == 2 else raw[2:]
            if len(raw) != 2:
                # A TWO-CHARACTER ANSWER OR IT IS NOT AN ANSWER -- never truncated, for the same reason
                # `RESIGN` must not become `R`: a reader broad enough to find an action in text that does
                # not contain one manufactures its own results.
                outcome = "malformed"
                note = f"{tok!r} is {len(raw)} characters; an action is exactly two, or PASS"
            elif silo not in ammo or threat not in threats:
                outcome = "unknown"
                note = f"no silo {silo!r} or no threat {threat!r}"
            elif threats[threat]["tick"] <= tick:
                outcome = "late"
                note = f"threat {threat} impacted at tick {threats[threat]['tick']}"
            elif abs(pos[silo] - threats[threat]["impact"]) > RANGE:
                outcome = "out_of_range"
                note = f"silo {silo} at {pos[silo]} cannot reach impact {threats[threat]['impact']} (range {RANGE})"
            elif ammo[silo] <= 0:
                outcome = "no_ammo"
                note = f"silo {silo} is empty"
            else:
                ammo[silo] -= 1
                del threats[threat]
                outcome = "fired"
                note = f"{threat} destroyed"

        if outcome:
            counts[outcome] += 1

        # RESOLVE IMPACTS AT THIS TICK, after the action -- the volley is resolved, then the tick ends.
        for name, t in list(threats.items()):
            if t["tick"] <= tick:
                del threats[name]
                victim = next((c for c, x in alive.items() if x == t["impact"]), None)
                if victim:
                    del alive[victim]
                    counts["hit"] += 1
                    note = (note + "; " if note else "") + f"{name} hit {victim}"
                else:
                    counts["spared"] += 1
                    note = (note + "; " if note else "") + f"{name} hit empty ground"

        trace.append({"tick": tick, "token": tok, "outcome": outcome, "note": note,
                      "cities_alive": sorted(alive), "ammo": dict(ammo),
                      "threats_remaining": sorted(threats)})

    # anything still airborne at the end of the stream. BOTH OUTCOMES ARE COUNTED HERE: the first version
    # counted only `hit`, so a decoy that landed on empty ground after the last action was dropped from the
    # tally entirely -- and `spared` is the count that shows an entrant correctly IGNORED something, which
    # is the whole allocation faculty. A resolution path that reports only one of its two outcomes is the
    # same defect as a duration that measures the cap.
    for name, t in list(threats.items()):
        victim = next((c for c, x in alive.items() if x == t["impact"]), None)
        if victim:
            del alive[victim]
            counts["hit"] += 1
        else:
            counts["spared"] += 1

    return {"cities_surviving": len(alive), "cities_alive": sorted(alive), "score": len(alive),
            "cities_total": len(st["cities"]), "actions": len(actions), "counts": counts,
            "trace": trace}


# -------------------------------------------------------------------------------------- controls
def _self_test():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            print(f"          got  {got!r}\n          want {want!r}")
            fails.append(name)

    print("=" * 96)
    print("MISSILE COMMAND SIMULATOR CONTROLS")
    print("=" * 96)

    # two cities, two silos, three threats: one city-bound (impact 2), one city-bound (impact 5), one decoy
    LAYOUT = ("tick 0\ncity A at 2\ncity B at 5\nsilo 1 at 0 ammo 1\nsilo 2 at 9 ammo 1\n"
              "threat P impact 2 tick 3\nthreat Q impact 5 tick 3\nthreat R impact 8 tick 3\n")

    print("\n[1] parsing and the malformed-state rule")
    st = parse_state(LAYOUT)
    ck("cities", sorted(st["cities"]), ["A", "B"])
    ck("silos", sorted(st["silos"]), ["1", "2"])
    ck("threats", sorted(st["threats"]), ["P", "Q", "R"])
    ck("comments and blank lines are ignored", parse_state(LAYOUT + "# a comment\n\n")["tick"], 0)
    for bad, why in ((("tick 0\nsilo 1 at 0 ammo 1\nthreat P impact 2 tick 3\n"), "no cities"),
                     (("tick 0\ncity A at 2\nthreat P impact 2 tick 3\n"), "no silos"),
                     (("tick 0\ncity A at 2\nsilo 1 at 0 ammo 1\n"), "no threats"),
                     (("tick 0\ncity A at 2\ncity B at 2\nsilo 1 at 0 ammo 1\nthreat P impact 9 tick 3\n"),
                      "two cities on one coordinate"),
                     (("tick 0\ncity A at 2\nsilo 1 at 0 ammo 1\nthreat P impact 9 tick 0\n"),
                      "a threat already landed")):
        try:
            parse_state(bad)
            ck(f"rejects a state with {why}", "parsed anyway", "ValueError")
        except ValueError:
            ck(f"rejects a state with {why}", "ValueError", "ValueError")

    print("\n[2] firing -- the score is a count")
    r = play(LAYOUT, ["1P", "2Q"])
    ck("both city-bound threats destroyed", r["cities_surviving"], 2)
    ck("...and the decoy is left alone", r["counts"]["fired"], 2)
    ck("...and the decoy lands on empty ground, sparing a city", r["counts"]["spared"], 1)
    ck("a PASS spends nothing", play(LAYOUT, ["PASS", "PASS", "PASS"])["counts"]["passed"], 3)

    print("\n[3] ALLOCATION UNDER SCARCITY -- the whole faculty")
    # one silo, one round, two city-bound threats: A CITY MUST BE LOST. There is no play that saves both.
    HARD = ("tick 0\ncity A at 2\ncity B at 5\nsilo 1 at 2 ammo 1\n"
            "threat P impact 2 tick 2\nthreat Q impact 5 tick 2\n")
    best = max(play(HARD, [a])["cities_surviving"] for a in ("1P", "1Q", "PASS"))
    ck("with one round and two city-bound threats, the best play saves exactly one", best, 1)
    ck("...and it is not the fault of the play", play(HARD, ["1P"])["cities_surviving"], 1)
    # AND THE API GUARD ITSELF IS A CONTROL: a string where a sequence belongs used to be read as
    # characters, scoring a perfect play as a total loss.
    try:
        play(HARD, "1P")
        ck("a STRING actions argument is refused, not read as characters", "accepted", "TypeError")
    except TypeError:
        ck("a STRING actions argument is refused, not read as characters", "TypeError", "TypeError")

    print("\n[4] the decoy trap -- firing at everything is the losing line")
    DECOY = ("tick 0\ncity A at 2\nsilo 1 at 2 ammo 1\n"
             "threat P impact 2 tick 2\nthreat R impact 9 tick 2\n")
    ck("spending the only round on the decoy loses the city",
       play(DECOY, ["1R"])["cities_surviving"], 0)
    ck("...and spending it on the threat saves it", play(DECOY, ["1P"])["cities_surviving"], 1)

    print("\n[5] range -- a silo cannot reach the whole board")
    ck("out of range is its own outcome",
       play(LAYOUT, ["1R"])["trace"][0]["outcome"], "out_of_range")
    ck("...and it does not consume ammo", play(LAYOUT, ["1R", "1P"])["counts"]["fired"], 1)
    ck("in range fires", play(LAYOUT, ["2R"])["trace"][0]["outcome"], "fired")

    print("\n[6] AMMO IS A REAL CONSTRAINT")
    # TWO DISTINCT in-range threats against one round: the second shot finds an empty silo, not a missing
    # threat. (The first version reused `1P`, whose target the first shot had already destroyed, so it
    # measured `unknown` -- a different claim about a different thing.)
    AMMO = ("tick 0\ncity A at 2\ncity B at 5\nsilo 1 at 2 ammo 1\n"
            "threat P impact 2 tick 3\nthreat Q impact 3 tick 3\n")
    r = play(AMMO, ["1P", "1Q"])
    ck("the second shot from an empty silo is `no_ammo`", r["trace"][1]["outcome"], "no_ammo")
    ck("...and the threat it failed to stop is NOT counted as a fired shot", r["counts"]["fired"], 1)
    ck("...and a destroyed threat makes a later shot at IT `unknown`, a different claim",
       play(LAYOUT, ["1P", "1P"])["trace"][1]["outcome"], "unknown")

    print("\n[7] THE EMPTY-LIST RULE -- unreadable answers are counted, never scored as wrong moves")
    r = play(LAYOUT, ["e2e4", "RESIGN", "1", "1PP", "1P"])
    ck("the four junk tokens are `malformed`, and the real one is not", r["counts"]["malformed"], 4)
    ck("...and the board still resolves normally around them", r["counts"]["spared"], 1)
    ck("RESIGN is NOT truncated into an action", play(LAYOUT, ["RESIGN"])["counts"]["malformed"], 1)
    ck("an unknown silo/threat is `unknown`, a different claim from malformed",
       play(LAYOUT, ["9P"])["trace"][0]["outcome"], "unknown")

    print("\n[8] the trace is a sufficient statistic -- every tick can be replayed")
    r = play(LAYOUT, ["1P", "2Q", "PASS"])
    ck("one row per action", len(r["trace"]), 3)
    ck("...each carrying cities alive", all("cities_alive" in t for t in r["trace"]), True)
    ck("...and ammo", all("ammo" in t for t in r["trace"]), True)
    ck("...and threats remaining", all("threats_remaining" in t for t in r["trace"]), True)
    ck("and the last row agrees with the final score",
       len(r["trace"][-1]["cities_alive"]), r["cities_surviving"])

    print("\n" + "=" * 96)
    n = 34 - len(fails)
    print(f"{'ALL CONTROLS PASS' if not fails else str(len(fails)) + ' FAILED'}   --  {n}/34")
    print("=" * 96)
    return 1 if fails else 0


def main():
    if "--self-test" in sys.argv:
        return _self_test()
    args = sys.argv[1:]
    if "--state" not in args:
        print(__doc__)
        return 2
    text = open(args[args.index("--state") + 1]).read()
    acts = []
    if "--actions" in args:
        acts = [a for a in args[args.index("--actions") + 1].replace(",", " ").split() if a]
    r = play(text, acts)
    print(f"  cities surviving  {r['cities_surviving']} / {r['cities_total']}")
    print(f"  actions           {r['actions']}")
    print(f"  counts            {r['counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(_self_test() if "--self-test" in sys.argv else main())
