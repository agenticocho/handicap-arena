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

---

## AMENDMENT Z1 — 2026-10-26 · THE PAIRING OF RECORD IS A TRIPLE, AND THE SIMULATOR IS RE-FROZEN AT 175

**This is a dated amendment appended below the frozen text, and nothing above it is edited.** The heading
THE SIMULATOR — zork.py, controls 114/114 at line 35, the `NEW zork.py ... controls 114/114` line in
WHAT WAS BUILT, and the `## FROZEN` paragraph all stand exactly as they were written before the first entrant
moved. They are history. Where they disagree with this section, this section is what a reader applies.

**Authority:** Local Chair ruling of 2026-10-26 —
`governance/rulings/2026-10-26-the-certified-pairing-is-a-triple-and-a-freeze-does-not-outrank-a-working-instrument.md`
(R1: re-freeze by dated amendment, never by editing the frozen text; R3: the unit of certification is a
triple). Filed from card `t_0c7829a8`.

**THE REASON, ON THE LINE:** the simulator gained controls in `6c426e5` — 114 → 175 — so the freeze above
names an instrument that no longer exists. That commit moved **both halves** of the pairing at once
(`zork.py` +633, `zork_controls.py` new 443 lines, `zork_run.py` +198), and the driver it ships calls
`replay(..., required_item=...)`. Run against the frozen `ff35ec83` simulator, that driver's own control [3]
dies — reproduced in an isolated tree rather than relayed, and quoted in
`ZORK_PREREG_AMENDMENT_2026-10-26.txt`:

```
TypeError: replay() got an unexpected keyword argument 'required_item'
  File "zork_run.py", line 716, in sufficiency_check
      rec = Z.replay(record["trace"], record["start_room"], required_item=record.get("required_item"))
  exit status 1, at control [3] of [6]
```

Pinning the driver back to the frozen simulator would preserve a **citation** at the cost of a pairing whose
own control cannot pass. **The freeze now names an instrument that exists.**

### Z1.1 — THE TRIPLE (R3), AND THE AMENDMENT'S OWN REFERENCE

```
driver     b26b2cfc42a0a91520e9e3b9753ad3871b8d79657628e986186c5f3de9948d19   zork_run.py     81,096 B
simulator  b9701007d6e186d5f27dc0e359a9c834b76a28ef8aedc362acf1c85bb6022d21   zork.py         75,338 B
PREREG     03b96c98bd39733b8ef64ec22e701efa3a330ad068b49c3efa9a57333f35a710   PREREG_zork.md  13,623 B

amendment  Z1 · 2026-10-26 · card t_0c7829a8
```

**THE PREREG DIGEST IN THE TRIPLE IS THE FILE AS FROZEN, NOT AS AMENDED, AND THAT IS THE ONLY READING THAT
IS NOT A FALSEHOOD.** `03b96c98…` is the `sha256` of this text *before* this section was appended — the plan
that was fixed before the first entrant moved, which is the thing a run's criteria are fixed against.
Appending this section changes the file's `sha256`; a reader who hashes the file now will get a different
number and **must not conclude the triple is wrong.** The frozen body is recoverable byte-for-byte:

```
git show fa2011f:PREREG_zork.md | sha256sum   ->  03b96c98bd39733b8ef64ec22e701efa3a330ad068b49c3efa9a57333f35a710
```

**THE AMENDMENT'S OWN DIGEST CANNOT BE WRITTEN INSIDE THE AMENDMENT.** It would change the bytes it
digests — a fixed point that does not exist — and a number that is recomputed until it is true is the
defect R2 names, one layer up. It is therefore recorded **outside** the text it identifies: in the message
of the commit that lands this section, and in `ZORK_PREREG_AMENDMENT_2026-10-26.txt`, with the recipe
`git show <landing-commit>:PREREG_zork.md | sha256sum`.

### Z1.2 — THE SUPERSET PROOF · THE CONDITION ON THIS AMENDMENT, PRINTED

A count cannot tell *grew* from *grew and lost ten*, so the left-hand set is the frozen file's own
`--self-test` output and the right-hand set is the current one. Both were run on **the same** unchanged
`levels/` tree (`git diff 4e0eb43 HEAD -- levels/` is empty), so the only thing that differs is the
simulator.

```
git show 4e0eb43:zork.py > F/zork.py       sha256 ff35ec83b340fbf0…  40,254 B
cd F && python3 zork.py --self-test          114 PASS lines, 0 FAIL, exit 0
                                             "ALL CONTROLS PASS -- 114/114"
python3 zork.py --self-test  (HEAD)          175 PASS lines, 0 FAIL, exit 0
                                             "ALL CONTROLS PASS -- 175/175"
```

**On the count in the card and in the ruling: the frozen file prints 114 PASS lines, not 110.** `114/114`
is what the prereg froze and what the file says when run; the `110` in the card body does not reproduce
here. The left-hand set below is therefore the same 114 the frozen line names, which is what the proof
needs.

**THE FROZEN SET — the 114 control names, printed in full (this is set A):**

```
  1  ...a different impossibility from `no_exit`
  2  ...and by an abbreviation and an alias alone
  3  ...and is unparsed, with a reason
  4  ...and it is counted impossible, not unread
  5  ...and it never took the item
  6  ...and none of them is `recognised-but-impossible`
  7  ...and not as progress
  8  ...and only the readable one is `parsed`
  9  ...and the ending does not change
 10  ...and the entrant is still at the start with nothing
 11  ...and the faculty flag is clear
 12  ...and the faculty flag is set
 13  ...and the hall, re-entered on the way back, is recorded once
 14  ...and the item was taken at step 1
 15  ...and the last row's inventory is the final inventory
 16  ...and the log shows the empty inventory it arrived with
 17  ...and the route begins where the entrant began
 18  ...and the world did not move
 19  ...counted as impossible, not as unread
 20  ...ending is `escaped`
 21  ...ending is `gate_locked`
 22  ...in particular it does not become `r`
 23  ...including the ones that were read
 24  ...it is counted as unread
 25  ...so it is a field of the record, not an inference
 26  ...while the successful crawl's last row shows it carrying
 27  ...while the trace, being one row per command, shows the hall only on re-entry
 28  THE FAILURE IS VISIBLE IN THE LOG, not in a score
 29  THE RAW TEXT OF EVERY COMMAND IS KEPT
 30  THE TWO COUNTERS DO NOT MERGE: one unread, one impossible
 31  `GO   NORTH` (padding) parses the same
 32  `RESIGN` is not a verb and is NOT truncated to a direction
 33  `collect brasskey` is a take
 34  `e2e4` is not a verb
 35  `examine` is a look
 36  `get brasskey` is a take
 37  `get the key` resolves by alias
 38  `go north` parses to go north
 39  `go sideways` is unparsed, not a moved-nowhere
 40  `grab brasskey` is a take
 41  `grab key` resolves by alias
 42  `i` is an inventory
 43  `inv` is an inventory
 44  `inventory` is an inventory
 45  `items` is an inventory
 46  `l` is a look
 47  `look` is a look
 48  `n` parses to go north
 49  `north` parses to go north
 50  `pick brasskey` is a take
 51  `pick up brasskey` is a take
 52  `pick up the key` resolves by alias
 53  `take br` does NOT resolve to brasskey
 54  `take brass key` (spaced) resolves
 55  `take brasskey` from the WRONG ROOM is `not_here` -- impossible, not unread
 56  `take brasskey` is a take
 57  `take key` resolves by alias
 58  `take the brasskey` is a take
 59  `take unicorn` does NOT resolve
 60  `take` with no object is unparsed
 61  `walk N` (other case) parses the same
 62  `west` from a room with no west exit is recognised-but-impossible
 63  a STRING commands argument is refused, not read as characters
 64  a crawl that ends without reaching the gate has no ending row
 65  a locked gate ends the run
 66  an empty command is unparsed
 67  an unreadable command BEFORE the gate is still consumed
 68  carrying the item out finishes
 69  commands after the gate are not consumed
 70  every row carries an inventory snapshot
 71  every row carries the object
 72  every row carries the parsed verb
 73  every row carries the raw command
 74  every row carries the room
 75  gate room
 76  never taking the item locks the floor world too
 77  north is a direction, `back` is not
 78  one row per command consumed
 79  rejects a world with duplicate item id
 80  rejects a world with duplicate room id
 81  rejects a world with exit to undefined room
 82  rejects a world with gate item missing
 83  rejects a world with gate room undefined
 84  rejects a world with item in undefined room
 85  rejects a world with no gate
 86  rejects a world with no items
 87  rejects a world with no rooms
 88  rejects a world with no start
 89  rejects a world with start undefined
 90  rejects a world with unknown direction
 91  rejects a world with unknown directive
 92  rejects an UNREACHABLE gate
 93  rooms
 94  start
 95  taking it twice is `already_carrying`
 96  the floor world is finishable in two commands
 97  the forgetful crawl: the ending is recoverable
 98  the forgetful crawl: the final inventory is recoverable
 99  the forgetful crawl: the route is recoverable from the record
100  the forgetful crawl: the take step is recoverable
101  the four unreadable commands are `unparsed`
102  the required item
103  the route is recorded in first-visit order, starting where the crawl started
104  the starting room is NOT in the trace and has to be carried beside it
105  the successful crawl: the ending is recoverable
106  the successful crawl: the final inventory is recoverable
107  the successful crawl: the route is recoverable from the record
108  the successful crawl: the take step is recoverable
109  the two runs typed the SAME route apart from the take
110  walking the SAME route without taking it does NOT finish
111  zork_01_the_floor ...and is NOT solvable without the item
112  zork_01_the_floor is solvable by its solution
113  zork_02_long_crawl ...and is NOT solvable without the item
114  zork_02_long_crawl is solvable by its solution
```

**THE 61 NAMES ADDED (set B \ A), printed in full.** The current set is exactly `A ∪ (B \ A)` — the 175
names are these 114 followed by these 61, **nothing elided** — so both sets are printed here without
printing the 114 twice:

```
  1  + ''               -> UNATTRIBUTABLE/empty
  2  + 'RESIGN'         -> UNATTRIBUTABLE/no_verb
  3  + 'e2e4'           -> UNATTRIBUTABLE/no_verb
  4  + 'go sideways'    -> rejected/unknown_direction
  5  + 'go'             -> rejected/missing_direction
  6  + 'look'           -> accepted/acted
  7  + 'north'          -> accepted/acted
  8  + 'take br'        -> rejected/unknown_object
  9  + 'take brasskey'  -> rejected/not_here
 10  + 'take unicorn'   -> rejected/unknown_object
 11  + 'take'           -> rejected/missing_object
 12  + 'west'           -> rejected/no_exit
 13  + ...and `Try moving in a direction ...` is counted `unparsed` too
 14  + ...and a declaration for a field that is not emitted is caught too
 15  + ...and every declared field is actually emitted
 16  + ...and it does not move the entrant toward the gate
 17  + ...and it is the whole reachable graph
 18  + ...and it says so on the record instead of leaving a plausible number bare
 19  + ...and its basis is stated
 20  + ...and moves NO object
 21  + ...and prose with no verb in it is UNATTRIBUTABLE
 22  + ...and that is a check that can fail: a mutated `counted_under` breaks it
 23  + ...and the closest it got is the gate itself
 24  + ...and the object's placement says where it is, not where it started
 25  + ...and the prose-only fields are named, with what they are
 26  + ...and the repeat is NOT counted as unread
 27  + ...and the required item is the one that moved
 28  + ...and the score says so independently of the route
 29  + ...and the takes by object show BOTH items, which is why the two readings differed
 30  + ...but `take metal` is REJECTED: the verb is one this world knows
 31  + ...but it does not move the required item
 32  + ...having started three moves away
 33  + ...so 'objects moved' and 'progress' are two different numbers, both from world state
 34  + ...so it covered the whole graph way
 35  + ...so progress toward the gate is NOT monotone on the level that measures retention
 36  + ...so the split separates them
 37  + ...so the table is complete
 38  + A FIELD WITH NO STATED SOURCE IS CAUGHT: an invented leaf is undeclared
 39  + NO progress field is prose-derived
 40  + THE TWO ARE INDISTINGUISHABLE IN THE FROZEN COUNTERS -- that is the defect, asserted
 41  + `take metal` is STILL counted under `unparsed`, per the prereg -- the axis is additive, not a rewrite
 42  + `take metal` is counted `unparsed` by the FROZEN counters
 43  + a crawl that takes the DISTRACTOR first, then the required item, escapes
 44  + a take that works is ACCEPTED, the repeat is REJECTED/already_carrying
 45  + every leaf of the progress block has a declared source
 46  + every reason carries its own text, so a row is readable without the source
 47  + every row is attributed exactly once
 48  + objects moved is read off `_placed`, not off the commands
 49  + on the FLOOR world, one item, the two readings agree -- which is why this was invisible
 50  + replay() WITH the required item returns the required take
 51  + replay() WITHOUT the required item reads the TORCH and returns 0 -- THE DEFECT, asserted
 52  + rooms visited is the route's own length
 53  + taking the DISTRACTOR moves an object
 54  + the attribution is recoverable from the rows alone, or it is not part of the record
 55  + the crawl ends ON the gate, so the graph distance is zero
 56  + the distance trail records the step taken AWAY from the gate to fetch the key
 57  + the forgetful crawl reaches the same room
 58  + the per-row attribution reproduces the frozen counters EXACTLY
 59  + the room graph: five rooms, five reachable, eight exits
 60  + the shortest route from hall to the gate is THREE moves (east, north, east)
 61  + the three categories sum to the rows
```

**THE SET DIFFERENCE:**

```
kept in both A ∩ B : 114
added     B \ A    :  61
removed   A \ B    :   0

removed: none
```

```
ARITHMETIC   114 kept + 61 added = 175  == current set size 175   TRUE
             114 kept +  0 removed = 114  == frozen set size 114   TRUE
NO DUPLICATE NAMES in either set: 0 in the frozen transcript, 0 in the current one -- a set difference
over a list with repeats would be a difference of the wrong thing.
```

**AND ONE LEVEL DEEPER, BECAUSE A NAME IS NOT AN ASSERTION.** A control can keep its name and have what it
compares weakened, which no membership test can see. So the `ck(name, got, want)` call sites were compared
between the two revisions as source text, by `ast`, with looped and f-string names matched as templates:

```
frozen 4e0eb43  ck() call sites:  87   HEAD 137
frozen sites ABSENT from HEAD (name template + compared expressions as a unit): 0
frozen sites whose multiplicity changed                                   : 0
-> removed: none, at call-site level as well as name level.

The 30 deletions in `git diff 4e0eb43 HEAD -- zork.py` are confined to two function bodies --
`parse_command` (its return signature now carries the rejection reason) and `replay` (it now takes
`required_item`) -- and contain no control-name literal. 71 of the 114 printed names come from literal
ck("…") calls and all 71 are assertion-identical; the other 43 are printed from loops over the synonym,
malformed-world and level-solution tables, which the call-site multiset covers.
```

**RE-RUN IT YOURSELF — the proof is a script in this repository, not a transcript in a report:**

```
python3 scripts/zork_superset_proof.py            # 4e0eb43 -> HEAD, both sets, both levels of proof
python3 scripts/zork_superset_proof.py 4e0eb43 6c426e5
```

It runs each revision's own `--self-test` against this repository's `levels/`, extracts the printed
names, differences the sets, compares the `ck()` call sites by `ast`, and **refuses to print a proof at
all if either revision has a failing control or a duplicated name** — a proof over a red or ambiguous
instrument is not a proof.

**WHAT THIS PROOF DOES NOT ESTABLISH, SAID RATHER THAN LEFT TO BE DISCOVERED:** it establishes that no
control was removed, renamed away, or re-pointed at a different comparison. It does **not** establish that
the *thing a kept control measures* did not change underneath it -- `parse_command`'s contract did change,
and a control asserting on its return value is asserting on new code that still satisfies the same
expression. That is a claim about the instrument's behaviour, and the 175/175 run is evidence for it, not a
proof.

### Z1.3 — WHAT THE CLIMB BOUGHT: 114 → 175 IS 61 CONTROLS, IN THREE CLASSES

These are the classes the 61 fall into by the section they print under. Every one of the 61 is accounted for
by one of the three; nothing is padding and the counts are checkable from the list above.

**1 · THE THREE-WAY AXIS — 26 controls, printed under `[12] ACCEPTED / REJECTED / UNATTRIBUTABLE`.**
Each row is attributed exactly once as accepted, rejected (with its reason) or UNATTRIBUTABLE, the three
categories are asserted to sum to the rows, and the per-row attribution is asserted to reproduce the
prereg's three frozen counters **exactly** — so `unparsed` still means what this document says it means
while a reader can tell an entrant that used the language badly from one that did not use it at all. This
is the axis filed as *"`unparsed` carried two claims"*: Bonsai's `take metal` is now REJECTED/unknown_object
and Ministral's prose is UNATTRIBUTABLE, and a control asserts the FROZEN counter is unmoved by the split.

**2 · PROGRESS FROM WORLD STATE, WITH A DECLARED SOURCE FOR EVERY LEAF — 26 controls, printed under
`[13] PROGRESS FROM WORLD STATE`.** Rooms visited are the route's own length and the reachable set is the
whole graph, objects moved is read off the world's `_placed` state rather than off the commands, and the
bearing to the gate is a shortest-path distance — each with a control for the case that separates it from
the others (the torch distractor moves an object without moving the required item; the retention level's
distance trail is asserted **not** monotone). Every leaf of the block carries a declared source, and two
controls fail when a leaf appears without one or when a declaration names a field that is never emitted.

**3 · THE REPLAY DEFECT, ASSERTED IN BOTH DIRECTIONS — 9 controls, printed under `[14] THE REPLAY
DEFECT`.** `took_item_at_step` is asserted to come from the first take of **the required item**, with the
crawl that takes the torch first shown returning `0` under the old reading and the first take of the key
under the new one -- and with the floor world, where there is one item and the two readings agree, asserted
so that the reason the defect was invisible on the easy level is on the record too.

### Z1.4 — CONTROL STATUS AS MEASURED, AND WHAT THIS AMENDMENT DOES NOT CLAIM

The triple is **the pairing of record**: the three digests a row must carry to be placed against this
preregistration. It is not a claim that every control of every member is green, so the status is printed
rather than implied, measured at HEAD `13b161a` on 2026-10-26:

```
zork.py    --self-test                          175 PASS,   0 FAIL, exit 0    175/175
zork_controls.py  (the separate non-parser)      93 PASS,   0 FAIL, exit 0     93/93
zork_run.py --self-test, probes/ as at 6c426e5   64 PASS,   0 FAIL, exit 0     64/64
zork_run.py --self-test, probes/ at HEAD         62 PASS,   2 FAIL, exit 1     62/64
```

**THE TWO RED CONTROLS, NAMED, WITH WHAT THEY READ:**

```
[5] THE COMPUTE PATH, zork_run.py:1163 and :1165
  FAIL  EVERY recorded GPU row contradicts itself: config.n_gpu_layers vs config.server_argv -ngl
          got  0        want 8
  FAIL  ...and the contradiction is 0 against 99, on all eight
          got  []       want [(0, '99')]
```

**THE CAUSE IS OUTSIDE THE PAIRING, AND IT IS MEASURED.** These two controls assert a property of the
**live archive**: that all eight `probes/ZORK_*.json` rows say `config.n_gpu_layers = 0` while their
`server_argv` says `-ngl 99`. Commit `13b161a` (a GPU window card, not this cabinet's) **replaced all eight
rows with a re-measurement** under this very simulator, whose writer reads `n_gpu_layers` out of the argv —
so no live row contradicts itself any more, and a control written to assert the defect now reads `0` where
it requires `8`. The same driver and simulator give **64/64** in a tree carrying the eight rows as they
stood at `6c426e5`; the originals are byte-identical to the pre-commit blobs and are preserved at
`suite3/preserved/20261026-14…/`. Nothing about `replay()`, the axis or the progress block is involved.

**THEREFORE BOTH DIRECTIONS OF THIS PAIRING ARE RED, FOR DIFFERENT REASONS, AND THIS AMENDMENT DOES NOT
PRETEND OTHERWISE.** Pinned back, control [3] dies (`TypeError`, above). Going forward, the two archive
controls die because the archive was fixed underneath them. What would clear it, named so the Chair can
choose rather than discover:

```
A  restore the eight preserved rows to probes/ (they carry ff35ec83 and the 0-vs-99 contradiction),
   moving the 13b161a re-measurements into preservation with their digests   -> driver returns to 64/64
B  keep the re-measurement and change those two controls to assert the defect against the PRESERVED rows
   and agreement on newly written rows  -> zork_run.py changes, driver digest changes, THIS TRIPLE IS VOID
   and the amendment must be re-frozen against the new driver
C  change nothing; record the pairing at 62/64 with these two controls red, and cite no row as evidence
   on their account  <- THIS AMENDMENT RECORDS C, the state at the date of writing
```

**AND WHAT IS NOT CERTIFIED HERE, AT ALL:** no entrant row is certified by this amendment; no cross-box
row is certified from this card — the cross-box row needs Mike's own words — and no row of `probes/` is
cited as pairing evidence, both because the restore is another card's and because two boxes cannot be
separated by a record whose `host_block()` carries no hostname.

### Z1.5 — WHAT DID NOT MOVE, AND THE ONE THING THIS AMENDMENT CANNOT HIDE

```
UNMOVED  C1 / C2 / C3 / C4 -- all four criteria, word for word
UNMOVED  the three frozen counters and the boundary rule (`take unicorn` is still `unparsed`)
UNMOVED  the six outcome rows 1-6, including INSUFFICIENT / BLOCKED and the no-re-scoping rule
UNMOVED  the gate: COVERAGE >= 0.95, YIELD >= 0.85
UNMOVED  both levels and their digests -- `git diff 4e0eb43 HEAD -- levels/` is EMPTY
         zork_01_the_floor 699ef17bfe26521b · zork_02_long_crawl c1d33b940fd842ed
```

**AND THE ONE THING IT CANNOT HIDE, STATED RATHER THAN LEFT FOR A READER TO FIND:** this amendment is
dated **after** eight rows were recorded under the new instrument (`13b161a`), so it is not a pre-data
freeze and does not pretend to be one. What makes it legitimate is what it *moves*: the instrument only.
No criterion, counter, level, boundary rule or outcome row moved, and none moved in response to any
entrant's result. The 114 → 175 climb happened in `6c426e5` because the instrument was wrong, not because a
result was inconvenient — `[12]` asserts that the split leaves the frozen counters exactly where they
were.

