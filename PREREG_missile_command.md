# PRE-REGISTRATION — MISSILE COMMAND, EVENT 2 OF THE FAN-OUT

**Frozen before the first entrant moves.** Reported as SIMULATOR + FROZEN CRITERIA, per the fan-out rule.

---

## WHY THIS GAME, AND WHY IT SURVIVES THE MENU LESSON

**Format A: ALLOCATION UNDER SCARCITY — the second event in the order whose oracle is the game itself.**

```
1  NO LEGAL-MOVE GENERATION   the action space is SILOS x THREATS, two characters: `2Q`
2  NO EXTERNAL ORACLE         the simulator resolves the volley; THE SCORE IS A COUNT of cities surviving
3  SHORT ANSWERS              two characters cannot be deliberated into a token cap
4  FORMAT A                   allocation under scarcity -- total ammo is LESS than the incoming threats
```

**AND IT SURVIVES THE MENU LESSON FOR A REASON WORTH STATING: THE INCOMING MISSILES *ARE* THE STATE.**
Chess failed because the entrant had to derive legal moves from a position and the move list had to be
supplied — after which the task became "choose from a menu". **Here naming a threat IS playing the game:
there is no derivation step, so there is no menu to hand over and nothing to remove.** The distinction
matters because it means this event cannot acquire chess's defect.

## THE SIMULATOR — `missile_command.py`, controls 34/34

```
STATE   line-oriented text, travels in a message and diffs in git:
          city A at 2 · silo 1 at 0 ammo 2 · threat P impact 2 tick 5
ACTION  <silo><threat> -- TWO CHARACTERS, nothing more. `PASS` is legal and spends nothing.
OUTCOME the volley is resolved, city-bound threats hit, decoys land on empty ground.
SCORE   cities surviving -- a count
```

**THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE**, same shape as the chess `rows` and the Sokoban
trace: **every tick carries its action, its outcome, the cities alive, the ammo remaining and the threats
remaining**, so a later reader can replay the whole volley.

**AND SEVEN OUTCOMES THAT MUST NEVER BE MERGED INTO ONE ANOTHER:**

```
fired  passed  no_ammo  out_of_range  unknown  malformed  late  |  hit  spared
```

**`malformed` IS THE EMPTY-LIST RULE AND IT IS COUNTED, NEVER SCORED AS A WRONG MOVE.** A parser that
folds its own failures into the entrant's score is reporting on itself. `no_ammo` (the silo was empty),
`out_of_range` (the silo cannot reach that far), `unknown` (no such silo or threat) and `late` (already
impacted) are four different claims, and the first version of the controls conflated two of them.

**AND THE ANSWER IS EXACTLY TWO CHARACTERS OR `PASS`, NEVER TRUNCATED** — for the same reason `RESIGN`
must not become `R`: a reader broad enough to find an action in text that does not contain one manufactures
its own results. `1PP` is malformed; it is not silo 1 engaging threat P with a stray character.

**AND THE SIMULATOR REFUSES A STRING WHERE A SEQUENCE BELONGS.** `play(state, "1P")` iterates into `'1'` and
`'P'` — **two malformed actions that scored a perfect play as a total loss.** Caught by the controls; it is
now a `TypeError` with the reason, and a named control.

## THE STATES — AND STATE 02 IS THE INSTRUMENT

```
mc_01_one_shot   1 city, 1 threat, 1 round. THE FLOOR: a population that cannot engage a single threat
                 cannot play this event at all.
mc_02_scarcity   4 cities, 8 threats, 4 rounds -- AND PERFECTION IS IMPOSSIBLE BY CONSTRUCTION.
```

**State 02 is the whole faculty in one board, and the spread was measured before freezing:**

```
passive           PASS every tick                       0 / 4 cities
fire-at-cities    read the impacts, spend on the cities 4 / 4 cities
fire-at-decoys    spend on the empty-ground threats     0 / 4 cities
```

**Three threats (X, Y, Z) impact EMPTY GROUND. Z at coordinate 9 is OUT OF RANGE of every silo, so it
cannot be engaged even by mistake.** A model that fires at everything runs out of ammo and loses cities it
could have saved. **THE DECOYS ARE NOT DECORATION — they are the thing that makes the score a measurement
of reading rather than of reflexes.**

## THE CRITERIA, FROZEN BEFORE THE FIRST NUMBER

```
C1  THE FLOOR     at least one entrant engages the single threat in mc_01. A population that cannot parse
                  a two-character action cannot play this event.
C2  THE FACULTY   the scores on mc_02 SPREAD. If every entrant scores the same, the state is not
                  discriminating and that is a finding about the STATE, not about the entrants.
C3  DECOYS ARE READ  at least one entrant finishes mc_02 with a higher city count than a
                  spend-on-everything line would. An entrant that fires at the decoys is not doing the
                  task, and the count shows it.
```

### THE OUTCOME ROWS, WRITTEN DOWN BEFORE THE RUN

**1. GATE UNMET** → `NO VERDICT — THE FIELD DID NOT COMPLETE.` Name which ratio failed.
**2. GATE MET, criteria evaluated** → a verdict, each number quoted with the set it was computed over.
**3. GATE MET, a criterion fails, population a candidate cause** → `FAILED ON THIS POPULATION` as a scope.
   **Declared here so it cannot be a hedge added after a result. It may attach to a FAIL, never excuse one.**
**4. INSUFFICIENT / BLOCKED** → if the population cannot parse a two-character action, or no entrant can
   load, or no state separates anyone, **THAT IS THE RESULT, reported with the population named and the
   rates attached, and the event is NOT re-scoped until something fits.**
**5. NO MEASURED ENTRANTS** → `ERROR`, exit non-zero, not a verdict.

## THE GATE, AND THE POPULATION — CARRIED FROM THE CHESS FIXES, NOT RE-DERIVED

```
COVERAGE   attempted / planned    >= 0.95     ATTEMPTED IS COUNTED, NOT COMPUTED; never_started subtracted
YIELD      measured  / attempted  >= 0.85
```
**A ZERO-MEASURED RUN IS AN ERROR AND EXITS NON-ZERO.** Measured today: a run that never started against
ANY entrant reported `COVERAGE 1.000`, because every entrant was "attempted" and none was measured.
**COVERAGE CANNOT TELL "ATTEMPTED" FROM "STARTED" AND TOTAL FAILURE IS ITS PASSING CONDITION.**

**THE POPULATION IS DERIVED FROM `ARENA_MODELS`** at a spread across the size range, `mmproj` excluded —
**the third time today the one-definition repair has been needed, and the reason it is written here rather
than re-derived in code.** And **the entrant must LOAD**: an entrant is not a result until it can load.

**RUNS GO THROUGH `scripts/run_guarded.sh`** — ceiling 24G/32G/1G, and the script is what makes it real
rather than aspirational.

## FROZEN

**The simulator, its 34 controls, the two states, the criteria and the outcome rows are fixed at this
commit.** No number below this line may move in response to an entrant's result. **And the coordinate
rule: no time limit. The cap is the budget, not the clock.**
