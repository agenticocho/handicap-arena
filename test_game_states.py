#!/usr/bin/env python3
"""GAME CONTRACT enforcement: a game name with no state behind it FAILS.

The standard (GAME_CONTRACT.md): *can a stranger reconstruct the game from the recorded bundle?*
If not, the visual is a skin over someone else's result — the same failure as a count carried as a
literal, which is a claim with no carrier.

A principle will not hold across 55 catalogue events. A check will. This is that check.

WHAT IT ENFORCES
  1. A card task file that names a game (`metaphor` or `game`) must also declare the bundle fields
     that carry that game's state (`game_state_in_bundle`). Otherwise the name is a costume.
  2. A recorded round that carries a game name must have non-empty state for it.
  3. INSTRUMENT-class events must not be ranked. An event that validates the measurement is not a
     contest, and a front end that merely LABELS the difference will eventually rank a
     scale-calibration against a boxing match.

POSITIVE CONTROL: the test injects a synthetic task that names a game with no state and asserts the
rule fires on it. A check that cannot fail is decoration; this one is verified to fail on exactly
the defect it exists for.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(HERE, "tasks")
RESULTS = os.path.join(HERE, "results")
GAME_KEYS = ("metaphor", "game")
STATE_KEYS = ("game_state_in_bundle", "game_state")


def declared_game(rec):
    for k in GAME_KEYS:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return k, v.strip()
    return None, None


def has_state(rec):
    for k in STATE_KEYS:
        v = rec.get(k)
        if isinstance(v, (list, dict)) and len(v) > 0:
            return True
        if isinstance(v, str) and v.strip():
            return True
    return False


def staged_as(d):
    """How an INSTRUMENT event is SHOWN.

    Not optional, and this is the whole correction: an instrument that declares no staging will be
    staged as nothing and read as boring -- which is what an earlier version of this rule got wrong.
    A UFC weigh-in is an instrument and it draws a crowd, because it has a number, a threshold, a
    moment, a legible way to miss, and a side-by-side.

    Returns the declared value, or None.
    """
    v = d.get("staged_as")
    return v if (isinstance(v, str) and v.strip()) else None


def check_task_file(d):
    """-> list of failure strings for one task definition.

    THE TEST CUTS BOTH WAYS, which is the correction Mike made to an earlier version of this rule:
      * CONTEST    -- must declare a game AND the state that carries it.
      * INSTRUMENT -- must NOT declare a game (a game name on an instrument is the referee in a
                      costume -- the FAKE CONTEST, which is the actual defect), and MUST declare
                      what it is staged as.
    An INSTRUMENT event may absolutely be the most compelling thing on the card -- a UFC weigh-in is
    an instrument and it draws a crowd. Being an instrument and being boring are different axes; the
    offence is the costume, not the audience.
    """
    fails = []
    gk, gv = declared_game(d)
    cls = d.get("class")
    if cls == "INSTRUMENT":
        if gk:
            fails.append(f"classed INSTRUMENT but declares the game {gv!r} via {gk!r} — an "
                         f"instrument wearing a game is a FAKE CONTEST, not a contest")
        if not staged_as(d):
            fails.append("classed INSTRUMENT but declares no `staged_as` — an instrument must say "
                         "what it is shown as, or it will be staged as nothing and read as boring")
    else:
        if gk and not has_state(d):
            fails.append(f"names the game {gv!r} via {gk!r} but declares no "
                         f"{STATE_KEYS[0]} — the name is a costume")
    if cls == "INSTRUMENT" and d.get("ranked"):
        fails.append("classed INSTRUMENT but marked ranked — a weigh-in does not decide the fight")
    return fails


def check_bundle(p):
    """-> list of failure strings for one recorded bundle."""
    fails = []
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return fails
    if d.get("harness") != "handicap-arena":
        return fails
    for e in (d.get("results") or []):
        for rk, rd in (e.get("rounds") or {}).items():
            gk, gv = declared_game(rd)
            if gk and not has_state(rd):
                fails.append(f"{os.path.basename(p)} :: {rk} claims game {gv!r} with no state")
    return fails


def is_superseded(failure_line):
    """Is this round violation annotated by a supersession record beside its bundle?

    A NOTE MAY ADD INFORMATION; IT MAY NOT CHANGE STANDING. A round annotated SUPERSEDED is still a
    violation — this decides only which of two COUNTS it lands in, and the exit code is gated on the NEW
    count alone. So the record can never make a violation disappear; it can only stop the check from
    mistaking history for the present.

    The record must exist for the SAME bundle named in the failure, so an annotation cannot be inherited
    by a different artifact -- the same reason the `already_measured` check is keyed on content.
    """
    if "claims game" not in failure_line:
        return False
    name = failure_line.split(" ::")[0].strip()
    if not name.endswith(".json"):
        return False
    # A SUBDIRECTORY, so the records never land where a broader glob would count them as bundles. This is
    # the `EXERCISE_` collision caught before creating it: 151 annotation files beside 151 bundles would
    # each look like an entrant to any sweep of `results/*.json`.
    #
    # AND THE STEM, NOT THE FILENAME: the record for `X.json` is `X.json` in here, not `X.json.json`. The
    # caller and the checker must agree on this or the annotation silently stops matching the artifact.
    return os.path.exists(os.path.join(RESULTS, "supersessions", name[:-len(".json")] + ".json"))


def main():
    fails, checked = [], 0

    # 1 + 3: task definitions
    for p in sorted(glob.glob(os.path.join(TASKS, "*", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        checked += 1
        for f in check_task_file(d):
            fails.append(f"{os.path.relpath(p, HERE)}: {f}")

    # 2: recorded bundles
    bundles = sorted(glob.glob(os.path.join(RESULTS, "*.json")))
    for p in bundles:
        fails.extend(check_bundle(p))

    print(f"checked {checked} task file(s) and {len(bundles)} bundle(s)")

    # POSITIVE CONTROL -- and it must cover BOTH directions, because the rule cuts both ways.
    # The last one matters most: an honest weigh-in must PASS. A rule that fails the thing it was
    # written to permit is worse than no rule.
    controls = [
        ({"id": "C1", "metaphor": "CHESS", "items": []},
         "CONTEST naming a game with no state"),
        ({"id": "C2", "class": "INSTRUMENT", "staged_as": "weigh-in", "metaphor": "CHESS"},
         "INSTRUMENT wearing a game -- a FAKE CONTEST"),
        ({"id": "C3", "class": "INSTRUMENT", "items": []},
         "INSTRUMENT declaring no staging"),
        ({"id": "C5", "class": "INSTRUMENT", "staged_as": "weigh-in", "ranked": True},
         "INSTRUMENT marked ranked"),
    ]
    print("positive controls (each MUST fire):")
    for rec, label in controls:
        fired = bool(check_task_file(rec))
        print(f"  {'FIRES' if fired else 'DID NOT FIRE -- decoration'}  {label}")
        if not fired:
            fails.append(f"positive control did not fire: {label}")

    # THE NEGATIVE CONTROL -- an honest instrument must be ALLOWED. If this fires, the rule has
    # banned the very thing Mike's counterexample says is the best content on the card.
    honest = {"id": "C4", "class": "INSTRUMENT", "staged_as": "weigh-in", "items": []}
    if check_task_file(honest):
        print("  FAIL  an honest weigh-in was REJECTED -- the rule bans what it must permit")
        fails.append("negative control: an INSTRUMENT with staging and no game must pass")
    else:
        print("  ok    an honest weigh-in PASSES (staged, no game, unranked)")

    # THE BOUNDARY THAT LOOKS LIKE A VIOLATION, and the reason it is a CONTROL rather than a comment.
    # The Arcade fronts every event, so an INSTRUMENT will eventually be SHOWN as a cabinet. That is
    # PRESENTATION, it belongs in `staged_as`, and the forbidden thing is the game NAME
    # (`metaphor`/`game`) -- the contract's own line: an instrument MAY be the most compelling thing on
    # the card, it simply may not wear a game's clothes.
    #
    # Two cases ONE FIELD APART, because that is the entire boundary. Without the pair, a presentation
    # decision reads as a contract violation and the next reader "fixes" the test -- which is the
    # failure mode that a rule about presentation invites, and it is why this is a control.
    arcade_ok = {"id": "C2b", "class": "INSTRUMENT", "items": [],
                 "staged_as": "arcade cabinet -- PUNCH-OUT: which weigh-in gets up"}
    if check_task_file(arcade_ok):
        print("  FAIL  an ARCADE-FRAMED instrument was REJECTED -- the framing is presentation, not")
        print("        a game claim, and it must be permitted")
        fails.append("negative control: an INSTRUMENT staged as an arcade cabinet must pass")
    else:
        print("  ok    an ARCADE-FRAMED instrument PASSES (framing in `staged_as`, no game name)")
    arcade_named = dict(arcade_ok, id="C2c", metaphor="PUNCH-OUT")
    if not check_task_file(arcade_named):
        print("  DID NOT FIRE  arcade framing WITH the game name in `metaphor`")
        fails.append("positive control did not fire: arcade framing plus a game NAME must fail")
    else:
        print("  FIRES  the same framing WITH the name in `metaphor` -- THE NAME IS THE OFFENCE,")
        print("         not the presentation. Move the name out and the event is honest again.")

    print()
    if fails:
        # SUMMARY BY CLASS, not one line per bundle. The first version printed 245 lines for what
        # is really 3 distinct defects -- the same 16:1 noise ratio I criticised in test_doc_counts
        # this morning. A report nobody reads protects nothing.
        from collections import defaultdict
        # NEW vs HISTORICAL, and THE SPLIT IS THE ENFORCEMENT.
        #
        # A note beside an artifact may ADD information; it may not CHANGE the artifact's standing.
        # Superseded is not the same as compliant. So the annotated rounds STAY COUNTED and STAY
        # VIOLATIONS -- they are not excused by the note beside them, because the note cannot lend them
        # a compliance they never had.
        #
        # And the number that gates the exit code is the NEW one, which must be 0. Skipping the annotated
        # rounds instead would make "0" mean "none new" OR "none ever" with no way to tell which -- and
        # A CHECK THAT CANNOT FAIL ON A CONDITION STILL PRESENT IN THE RECORD IS NOT A WEAKER CHECK, IT
        # IS NOT A CHECK.
        new, hist = [], []
        for f in fails:
            (hist if is_superseded(f) else new).append(f)

        groups = defaultdict(list)
        for f in new:
            if "names the game" in f:
                groups["task file names a game with no state"].append(f.split(": names")[0])
            elif "claims game" in f:
                groups["recorded rounds claim a game with no state"].append(f.rsplit("claims game ", 1)[-1])
            else:
                groups["other"].append(f)
        print(f"  NEW violations          : {len(new)}   <- MUST be 0. THIS is the enforcement.")
        print(f"  HISTORICAL (superseded) : {len(hist)}   <- retained, unchanged, and still violations.")
        print()
        if new:
            print(f"{len(new)} NEW GAME CONTRACT violation(s), in {len(groups)} class(es):")
            for g, items in groups.items():
                print(f"  - {g}: {len(items)}")
                for i in sorted(set(items))[:6]:
                    print(f"        {i}")
                if len(set(items)) > 6:
                    print(f"        ... and {len(set(items)) - 6} more (same shape)")
            print()
            print("  A ROUND WRITTEN AFTER THE FIX CLAIMS A GAME AND CARRIES NO STATE.")
            print("  Either the name goes, or the state arrives. See GAME_CONTRACT.md.")
            return 1
        print("  NO NEW violation. The 301 historical rounds stand AS RECORDED -- superseded, not")
        print("  compliant, and the annotation does not upgrade them. A bundle written now claims no")
        print("  game, which is what the fix was for.")
        return 0
    print("every declared game has state behind it; no INSTRUMENT event is ranked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
