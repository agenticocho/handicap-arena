# PRE-REGISTRATION — THE LONG CRAWL (ZORK), EVENT 3 OF THE FAN-OUT

**Frozen before the first entrant moves.** Reported as SIMULATOR + FROZEN CRITERIA, per the fan-out rule.

---

## WHY THIS GAME, AND WHY IT IS THE RISKIEST OF THE THREE

**Format A: LONG-HORIZON STATE RETENTION — the one faculty nothing else in the set touches.** The two events
before it constrain the answer by construction: Sokoban's action space is four symbols, Missile Command's is
two characters. **This one hands the entrant an OPEN TEXT FIELD and asks for a command, which is the chess
failure in a new place.** Chess died because the entrant could not derive a legal move from a position; an
open command line has the same hazard one layer earlier — the entrant may produce English that is not a
command at all. It is stated first because it is the reason the parser rules below are not negotiable.

```
1  NO LEGAL-MOVE GENERATION   the parser accepts a COMMAND, and the world decides what it means
2  NO EXTERNAL ORACLE         the simulator decides escaped or locked; the score is a boolean and the reason
3  SHORT ANSWERS              a two-to-four word command cannot be deliberated into a token cap
4  FORMAT A                   LONG-HORIZON STATE RETENTION -- a required item found early, needed much later
```

**AND THE OPEN-TEXT RISK IS ANSWERED IN THE TWO PLACES IT CAN APPEAR**, which is the whole design:

```
THE PARSER IS FORGIVING ABOUT PHRASING   `n` / `north` / `go north` are one command.
                                         `take lamp` / `get lamp` / `grab lamp` / `pick up lamp` are one
                                         command. A parser that accepts one phrasing measures PHRASING,
                                         not planning.
A PARSE FAILURE HAS ITS OWN COUNTER       it is never scored as a wrong move. There is a filed defect for
                                         exactly this: a parser that folds its own failures into the
                                         entrant's score is reporting on itself.
```

## THE SIMULATOR — `zork.py`, controls 114/114

```
WORLD   line-oriented text, travels in a message and diffs in git:
          room hall Dusty Hall · exit hall north cellar · item brasskey cellar · gate vault brasskey
COMMAND free text: n / north / go north · take|get|grab|pick up <item> · drop <item> · look · inventory
SCORE   finished -- escaped carrying the required item, or did not. AND THE REASON IT DID NOT.
```

**THE GATE IS TERMINAL, AND THAT IS A DESIGN CHOICE STATED RATHER THAN DERIVED.** Arriving at the gate ends the
run, either `escaped` (carrying the required item) or `gate_locked` (not carrying it). It is terminal so that
failing to carry the item is a **RECORDED ENDING** rather than an indefinitely recoverable state. A gate you
can walk away from and retry measures whether the entrant eventually stumbled back, not whether it retained a
requirement across the crawl. **THE FAILURE IS THEREFORE IN THE MOVE LOG, NOT IN A SCORE**, which is what the
event was asked for.

## THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE — AND THE CLAIM IS CHECKABLE, NOT ASSERTED

Every command carries **the text as typed, the parsed verb and object, the outcome, the room, and an
inventory snapshot**, so a later reader can replay the whole crawl. **And a `replay()` function rebuilds the
route, the final inventory, the take step and the ending FROM THE RECORD ALONE**, with controls asserting that
what it recovers equals what `play()` reported — for the successful crawl and for the failed one. If a reader
cannot reconstruct the run from the record, the record is not finished; that is now a control rather than a
claim.

**EXACTLY ONE FIELD CANNOT BE DERIVED FROM THE TRACE, AND IT IS NAMED RATHER THAN LEFT IMPLICIT:** the starting
room has no command row, because there is no command. It is therefore a field of the record (`start_room`),
not an inference, and there is a control asserting it is absent from the trace for that reason.

## THE THREE COUNTERS, KEPT SEPARATE — THIS IS THE FILED DEFECT

```
parsed                      a verb was read, an object resolved, and the world executed it
unparsed                    NO command could be read -- and it changes NOTHING and is never a wrong move
recognised-but-impossible   a verb was read AND its object resolved to a real thing, and the world refused
```

**`no_exit`, `not_here`, `already_carrying`, `not_carrying`, `nothing_to_open` and `gate_locked` are six
different claims and none of them is `unparsed`.** The last is the one that matters here: **an entrant that
walks the right route and arrives without the item has not made a parsing error and has not made a movement
error — it has failed to retain a requirement, and that is the only thing this event is measuring.**

**THE BOUNDARY RULE, STATED BECAUSE IT IS THE ONE A READER WILL ARGUE WITH:** `take unicorn` is `unparsed`,
not `recognised-but-impossible`, because the object does NOT resolve — there is no unicorn — and claiming to
have "recognised" it would be the parser finding an answer in text that does not contain one. Unknown nouns
are a failure to READ and are counted as one.

## FORGIVING PHRASING IS NOT FUZZY IDENTITY — THE `RESIGN` RULE APPLIED TO A TEXT PARSER

The parser accepts the item id, the id with its separators removed, and any declared alias. **It does not
accept prefixes, substrings, or the first word of a longer name.** `take br` does not resolve to `brasskey`.

This is the project's filed `token[:1]` defect, aimed at the exact place the open-text risk lives: **taking
the first character of `RESIGN` turned a six-letter word into the action *Right*.** A reader broad enough to
find an answer in text that does not contain one manufactures its own results. Forgiving about HOW you say it;
strict about WHAT you said. Both halves are controls, in both directions, including the three negative cases.

## THE LEVELS — AND EACH CARRIES A SOLUTION THE SIMULATOR CONFIRMED, AND ITS NEGATIVE

**A WORLD WHOSE SOLVABILITY NOBODY CHECKED IS NOT A WORLD.** Both levels are played by a solution and by the
same route *without the take*, and the controls assert the first finishes and the second does not.

```
zork_01_the_floor    2 commands   THE FLOOR. Key in the room you start in, gate one move north. A population
                                  that cannot take an item it is standing on and walk north cannot play.
zork_02_long_crawl   6 commands   THE INSTRUMENT. Key ONE room from the start; gate FOUR rooms away; and the
                                  route to the gate does not pass back through the key's room.
```

**AND THE SPREAD WAS MEASURED BEFORE FREEZING, on `zork_02`, by `scripts/zork_reference_lines.py`:**

```
line                 finished  ending           took_at  parsed  unparsed  impossible
carries it           True      escaped          1        6       0         0
forgets the take     False     gate_locked      None     4       0         1
takes then drops     False     gate_locked      1        6       0         1
passive              False     out_of_commands  None     3       0         0
never moves          False     out_of_commands  None     2       0         0
parses nothing       False     out_of_commands  None     0       3         0
wrong way            False     out_of_commands  None     4       0         0
```

**`takes then drops` IS THE SHARPEST REFERENCE LINE IN THE TABLE: it takes the key at step 1 and still ends
`gate_locked`.** Taking the item is NOT the faculty — CARRYING it forward is. The two are reported separately
below for that reason.

**AND `parses nothing` IS THE INSUFFICIENT SIGNATURE**: 0 parsed, 3 unparsed. A population that produces that
row has not been measured on retention at all, and outcome row 4 exists so that it is reported as a result
rather than re-scoped.

## THE CRITERIA, FROZEN BEFORE THE FIRST NUMBER

```
C1  THE FLOOR        at least one entrant finishes zork_01_the_floor. A population that cannot take an item
                     it is standing on and walk north cannot play this event, and that is the Sokoban C2
                     finding in a new game.
C2  THE FACULTY IS   at least one entrant REACHES THE GATE, either ending -- `escaped` or `gate_locked` --
    OBSERVED         on zork_02. Reaching the gate is the PRECONDITION for measuring retention: a population
                     that never gets there has failed NAVIGATION, which is a different claim, and can say
                     nothing about retention in either direction. THIS IS NOT A BAR THE ENTRANTS MUST CLEAR
                     TO PASS -- it is the condition under which a retention number exists at all. If it is
                     not met, the result is INSUFFICIENT (row 4), not a low score.
C3  THE COUNTERS     `parsed` / `unparsed` / `recognised-but-impossible` are reported per entrant, separately,
    STAY SEPARATE    and `unparsed` is never folded into a wrong-move count or a score. AND IF `unparsed` IS
                     HIGH ACROSS THE POPULATION THAT IS A FINDING ABOUT THE PARSER'S COVERAGE, REPORTED AS
                     THAT, BEFORE ANY CLAIM ABOUT RETENTION IS MADE. The parser is the instrument; an
                     instrument that cannot read its subjects reports on itself and not on them.
C4  TAKING IS NOT    `took_item_at_step` and `carried_required_item` are reported as two separate quantities.
    CARRYING         The `takes then drops` reference line exists to make the distinction visible in advance:
                     an entrant can take the item early, drop it, and finish the crawl without it. A single
                     "got the item" boolean would score that run as a retention success.
```

## THE OUTCOME ROWS, WRITTEN DOWN BEFORE THE RUN

**1. GATE UNMET** → `NO VERDICT — THE FIELD DID NOT COMPLETE.` Name which ratio failed. Call nothing a pass
   or a fail.
**2. GATE MET, criteria evaluated** → a verdict, each number quoted with the set it was computed over.
**3. GATE MET, a criterion fails, population a candidate cause** → `FAILED ON THIS POPULATION` as a scope.
   **Declared here so it cannot be a hedge added after a result. It may attach to a FAIL, never excuse one.**
**4. INSUFFICIENT / BLOCKED** → **IF THE POPULATION CANNOT PARSE A SINGLE COMMAND, THAT IS THE RESULT.** So is
   a population that cannot load, or one where nobody reaches the gate, or one where every entrant produces
   the identical record. It is reported as `INSUFFICIENT` with **the population named and the rates attached**
   — and in the parse case the finding is *"this event's command grammar was not available to this
   population"*, which is a finding about **the parser and the entrants together**, reported as such. **THE
   EVENT IS NOT RE-SCOPED AND THE CRITERIA ARE NOT RELAXED UNTIL SOMETHING FITS.** This row exists so a null
   result cannot be quietly converted into a positive one by changing the question — and it is written here,
   before any entrant runs, precisely so it cannot be added afterwards.
**5. NO MEASURED ENTRANTS** → `ERROR`, exit non-zero, not a verdict.
**6. A HIGH `unparsed` RATE** → reported as its own finding in the verdict, **with the raw command text of
   every unread command quoted**, before any retention claim. It is not a footnote, because a parser that
   reads half its population is measuring its own coverage.

## THE GATE, AND THE POPULATION — CARRIED FROM THE CHESS FIXES, NOT RE-DERIVED

```
COVERAGE   attempted / planned    >= 0.95     ATTEMPTED IS COUNTED, NOT COMPUTED; never_started subtracted
YIELD      measured  / attempted  >= 0.85
```

**A ZERO-MEASURED RUN IS AN ERROR AND EXITS NON-ZERO.** A run that never started against ANY entrant reported
`COVERAGE 1.000`, because every entrant was "attempted" and none was measured. **COVERAGE CANNOT TELL
"ATTEMPTED" FROM "STARTED" AND TOTAL FAILURE IS ITS PASSING CONDITION.**

**THE POPULATION IS DERIVED FROM `ARENA_MODELS`**, at a spread across the size range, `mmproj` excluded — the
same resolution `run_card.py` uses. **A population named twice is a population that can disagree with itself.**
And **the entrant must LOAD**: an entrant is not a result until it can load.

**RUNS GO THROUGH `scripts/run_guarded.sh`** — ceiling 24G/32G/1G, which is what makes it real rather than
aspirational.

## WHAT WAS BUILT, AND WHAT WAS NOT TOUCHED

```
NEW   zork.py                              the simulator, controls 114/114
NEW   levels/zork_01_the_floor.txt         the floor
NEW   levels/zork_02_long_crawl.txt        the instrument
NEW   scripts/zork_reference_lines.py      the spread table above, reproducible
NEW   PREREG_zork.md                       this document
```

**NO SHARED FILE WAS TOUCHED. `arena.py`, `run_card.py`, `evaluate_v5.py`, every `CARD_*.md`, every existing
level file, the record format, the runner, the gate, the evaluator and the card registry are untouched. No
registration line was needed, exactly as for `sokoban.py` and `missile_command.py`.**

## FROZEN

**The simulator, its 114 controls, the two levels with their verified solutions and their verified negatives,
the three counters, the boundary rule, the criteria and the outcome rows are fixed at this commit.** No number
below this line may move in response to an entrant's result. **And the rule carried from both prior events: no
time limit. The cap is the budget, not the clock.** **And the lesson carried intact: fixing an instrument can
invalidate the evidence taken under it, and that is the correct cost of fixing it.**
