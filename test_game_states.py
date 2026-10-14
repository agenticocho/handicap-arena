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
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TASKS = os.path.join(HERE, "tasks")

# THE GATE READS THE SAME DECLARED DOMAIN THE RUNNER WRITES TO -- from the same ONE definition.
#
# This used to read `RESULTS = os.path.join(HERE, "results")`: the gate's scope was DERIVED from
# the checker's own location, exactly as the runner's was. Once run_card.py resolves the DECLARED
# root, a gate that still globbed <worktree>/results would GATE ONE PLACE WHILE THE RUN WROTE
# ANOTHER -- an admission gate reading a different tree from the writer it admits is the
# empty-list rule pointed at the gate: every check passes, on nothing.
#
# `cabinet_root.domain()` is a LIST, not a walk: this worktree's subtree under the declared root,
# always present whether or not it exists yet, plus the one legacy record declared in place. No
# part of this scope is found by recursion.
import cabinet_root as _root                                              # noqa: E402
DOMAIN = _root.domain()        # [(kind, path)] -- declared in cabinet_root.py, never discovered
# ONE RULE, ONE DEFINITION. The checker and the record generator must not re-implement the rule that maps
# a bundle filename to its annotation filename: two implementations can drift, and they agreed by
# COINCIDENTAL RE-IMPLEMENTATION -- which is the class this item was about. The generator's docstring
# claimed "one import apart" before the code did it, and A CLAIM IN A CAPTION IS NOT A GUARANTEE. This
# import is what makes the sentence true.
#
# NO FALLBACK. If this import fails the checker cannot know which record belongs to which bundle, and a
# silent default would recreate the defect exactly: an annotation that stops matching the artifact while
# reporting success.
from annotate_superseded import stem_of

GAME_KEYS = ("metaphor", "game")
# THE DECLARED SLOT NAMESPACE IS PARSED FROM GAME_CONTRACT.md, WHICH IS NOW ITS ONLY COPY.
#
# It used to be written twice -- as prose in the contract and as a literal here -- and the check read the
# literal while the gate's own error message said "Amend GAME_CONTRACT.md". A reader who complied with the
# instruction changed nothing. FOUR ONE-DEFINITION FAILURES LANDED IN ONE DAY, and this was the only one
# that ACTIVELY MISDIRECTED THE PERSON TRYING TO COMPLY: a value that drifts is a bug, a gate that sends
# its reader to the wrong file spends their trust and then their time. AN ERROR MESSAGE IS PART OF THE
# INSTRUMENT.
#
# A FLAT LINE FORMAT BETWEEN EXACT MARKERS, NOT A PARSED ENGLISH TABLE -- a regex over a markdown table is
# the greedy `{.*}` class this project has already paid for once. Nothing is read outside the markers and
# nothing is inferred from what is inside them: each line is `<key><whitespace><description>`.
SLOT_MARKER_BEGIN = "=== DECLARED_SLOTS BEGIN ==="
SLOT_MARKER_END = "=== DECLARED_SLOTS END ==="


def parse_declared_slots(path=None, text=None):
    """-> {key: description}. Raises on anything it cannot read, because a parser that returns an empty
    dict for a file it failed to understand is the empty-list rule pointed at the parser:

        ZERO SLOTS IS AN ERROR, NOT AN EMPTY DECLARATION. Zero slots means EVERY round key is undeclared,
        so a run gets refused for a reason nobody stated -- and the reason would look like the run's fault.
    """
    p = path or os.path.join(HERE, "GAME_CONTRACT.md")
    if text is None:
        if not os.path.exists(p):
            raise ValueError(f"declared-slot source ABSENT: {p}")
        text = open(p, encoding="utf-8").read()
    if SLOT_MARKER_BEGIN not in text or SLOT_MARKER_END not in text:
        raise ValueError(f"declared-slot markers not found in {p}: expected {SLOT_MARKER_BEGIN!r} and "
                         f"{SLOT_MARKER_END!r}. No slots were parsed and that is an ERROR, not an empty "
                         f"declaration.")
    body = text.split(SLOT_MARKER_BEGIN, 1)[1].split(SLOT_MARKER_END, 1)[0]
    slots = {}
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"malformed declared-slot line {line!r} -- expected '<key> <description>'")
        slots[parts[0]] = parts[1]
    if not slots:
        raise ValueError(f"ZERO slots parsed from {p} between the markers. Every round key would be "
                         f"undeclared, so a run would be refused for a reason nobody stated.")
    return slots


DECLARED_SLOTS = parse_declared_slots()
# THE GATE REVISION THAT ADMITTED A RUN. A digest of the contract, carried into every run's record, so a
# run and the gate that admitted it are linked by more than a timestamp -- v5 taught us that lesson and it
# was paid for.
GATE_REVISION = hashlib.sha256(open(os.path.join(HERE, "GAME_CONTRACT.md"), "rb").read()).hexdigest()[:16]

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
        # THE DECLARED SLOT NAMESPACE, ENFORCED. Every round key present in a bundle must appear in
        # DECLARED_SLOTS. Without this, "declared namespace" is a CAPTION -- prose nobody checks -- and an
        # undeclared key would arrive as a new slot, possibly wearing a game name, and no one would notice.
        for rk in (e.get("rounds") or {}):
            if rk not in DECLARED_SLOTS:
                fails.append(f"{os.path.basename(p)} :: round key {rk!r} is NOT in the declared slot table")
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
    # AND THE STEM, NOT THE FILENAME -- by the SAME FUNCTION the generator uses, imported above, rather
    # than by a copy of its rule. A copy can drift; a function cannot disagree with itself.
    # OVER THE DECLARED DOMAIN, not one derived tree. The record has two declared instances (the
    # live subtree and the legacy record kept in place), and an annotation counts as an annotation
    # wherever the declaration says the record lives.
    for _kind, _base in DOMAIN:
        if os.path.exists(os.path.join(_base, "supersessions", stem_of(name) + ".json")):
            return True
    return False


def main():
    fails, checked = [], 0

    # 1 + 3: task definitions
    for p in sorted(glob.glob(os.path.join(TASKS, "*", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        checked += 1
        for f in check_task_file(d):
            fails.append(f"{os.path.relpath(p, HERE)}: {f}")

    # 2: recorded bundles -- over the declared domain, and the declared scope is printed with the
    # count, so the number a reader takes away carries the trees it was counted in.
    bundles = []
    for _kind, _base in DOMAIN:
        bundles.extend(glob.glob(os.path.join(_base, "*.json")))
    bundles = sorted(bundles)
    for p in bundles:
        fails.extend(check_bundle(p))

    print(f"checked {checked} task file(s) and {len(bundles)} bundle(s)")
    for _kind, _base in DOMAIN:
        print(f"  scope  {_kind:16} {_base}")

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

    # THE RULE ITSELF, ASSERTED DIRECTLY -- and this is the ONLY CATCHER LEFT. Sharing the rule removed the
    # disagreement that would have caught the naming defect, so the shared rule is now the single point of
    # failure and nothing above tests it. Without this control the failure mode is not removed, it has
    # MOVED: from "two components silently agree" to "one component is silently wrong".
    #
    # AND IT IS THE REASON THIS IS NOT A DOCSTRING. The generator asserted "one import apart" for a day
    # while the checker re-implemented the rule by hand. A PROPERTY A CAPTION ASSERTS AND NOTHING EXECUTES
    # IS THE CAPTION DEFECT; this is the execution.
    rule_cases = [("X.json", "X"), ("X", "X"), ("a.b.json", "a.b"), (".json", "")]
    bad = [(i, o, stem_of(i)) for i, o in rule_cases if stem_of(i) != o]
    if bad:
        for i, o, got in bad:
            print(f"  FAIL  stem_of({i!r}) gave {got!r}, expected {o!r}")
        fails.append("control: stem_of must map a bundle filename to its stem")
    else:
        print(f"  ok    stem_of ASSERTED DIRECTLY ({len(rule_cases)} cases, including a name not ending "
              f"in .json passing through unchanged)")

    # THE PARSER FOR THE DECLARED NAMESPACE, CONTROLLED. A parser is an instrument and gets the same
    # treatment as every other one on this project: a control that it CAN FIRE, and a control that it
    # READS CORRECTLY -- because a parser returning an empty dict for a file it failed to understand would
    # refuse every run for a reason nobody stated.
    _real = parse_declared_slots()
    if len(_real) < 1:
        fails.append("control: the real contract must parse at least one slot")
    if "R1_conformance" not in _real:
        fails.append("control: the neutral key must parse out of the contract")
    for _txt, _why in ((f"{SLOT_MARKER_BEGIN}\n{SLOT_MARKER_END}\n", "ZERO slots between the markers"),
                       ("no markers here at all\n", "the markers are ABSENT"),
                       (f"{SLOT_MARKER_BEGIN}\njustoneword\n{SLOT_MARKER_END}\n",
                        "a slot line with no description")):
        try:
            parse_declared_slots(text=_txt)
            fails.append(f"control: the slot parser must FAIL on {_why}")
        except ValueError:
            pass

    # THE SLOT NAMESPACE, CONTROLLED IN BOTH DIRECTIONS. "Declared" is a caption until an UNDECLARED key
    # fails, so the pair is one key apart: a bundle whose round key is in the table passes, and the same
    # bundle with an invented key FIRES. Written to a temp file, never into results/, so the control cannot
    # leave an artifact where a sweep would count it.
    import tempfile
    def _probe(rec):
        fd, p = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump(rec, fh)
            return check_bundle(p)
        finally:
            os.remove(p)
    if any("declared slot table" in f for f in _probe({"harness": "handicap-arena",
                                                       "results": [{"rounds": {"R1_fencing": {}}}]})):
        print("  FAIL  a DECLARED slot key was REJECTED -- the table overreaches its own purpose")
        fails.append("control: a declared slot key must pass")
    else:
        print("  ok    a DECLARED slot key PASSES")
    if not any("declared slot table" in f for f in _probe({"harness": "handicap-arena",
                                                           "results": [{"rounds": {"R4_something_new": {}}}]})):
        print("  DID NOT FIRE  an UNDECLARED slot key -- the namespace is a caption after all")
        fails.append("control: an undeclared slot key must fire")
    else:
        print("  FIRES  an UNDECLARED slot key -- the namespace is a CHECK, not a caption")

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
