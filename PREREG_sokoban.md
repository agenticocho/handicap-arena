# PRE-REGISTRATION — SOKOBAN, EVENT 2 OF THE ORDER

**Frozen before the first entrant moves.** Chilly's requirement: *bring me the simulator and the frozen
criteria before the first entrant moves.* Everything below is fixed at this commit.

---

## WHY THIS GAME, AND WHY IT IS NOT A CONSOLATION PRIZE

**Chess is blocked on population.** Every entrant tried could not derive a legal move unaided — `e3`
justified with a hallucinated board, 2314-token deliberations with no commitment, a 350M model that
returned 78 tokens and no move. **Sokoban is position 2, chosen by the criterion already written down, and
it satisfies by CONSTRUCTION the four constraints chess failed by hope:**

```
1  NO LEGAL-MOVE GENERATION   the action space is FOUR SYMBOLS -- U D L R. The model SELECTS; it does not
                              generate. This is the exact thing that killed chess.
2  NO EXTERNAL ORACLE         the simulator decides solved or unsolved and the score is the move counter.
                              Chess carried the third reorder case -- an oracle binary absent from the box.
3  SHORT ANSWERS              a one-letter answer cannot be deliberated into the token cap. The second
                              measured failure mode was deliberation without commitment.
4  FORMAT A, THE ORDER'S OWN  IRREVERSIBLE PLANNING -- dead-end recognition, asked once, at the boundary.
   REASON                     Boxes push and never pull, so one wrong push kills a level permanently.
```

**AND THE FOUR-FIELD FREEZE COLLAPSES INTO THE RECORD ITSELF**, which is what makes a cross-machine
comparison exist cheaply: no oracle binary to resolve, no engine freeze, no Threads/Hash pinning, no
depth. **Jarvis's first external test becomes a text grid rather than a chess engine.**

## THE SIMULATOR — `sokoban.py`, controls 30/30

```
level   ASCII: # wall  . target  $ box  @ player  * box-on-target  + player-on-target
        So A LEVEL IS A TEXT BLOB that travels in a message and diffs in git.
play()  level + move stream -> solved, moves, attempted, blocked, unrecognised, final_board, trace[]
```

**THE RECORD IS A SUFFICIENT STATISTIC FOR THE SCORE, the same shape as the chess `rows`:** every ply
carries its token, its action, its outcome and **the board after it**, so a later reader can replay the
whole game. Same as chess and for the same reason.

**AND AN ILLEGAL PUSH IS A NO-OP THAT IS RECORDED ANYWAY — THEY ARE TWO DIFFERENT CLAIMS:**

```
moves          SUCCESSFUL actions -- THE SCORE, comparable across entrants
attempted      every token emitted, legal or not
blocked        attempts that could not be made; a wall-bumper's signature
unrecognised   tokens that were not a single action letter
```

**A model that bumps a wall forever has 0 moves and 1000 attempts, and a naive counter would call it a
long game.** Measured in the controls: 50 wall bumps = 0 moves, 50 attempted, 50 blocked, UNSOLVED.

**AND THE ANSWER IS EXACTLY ONE LETTER, SO ANYTHING ELSE IS UNRECOGNISED, NEVER TRUNCATED.** The first
version took `token[:1]`, which read `RESIGN` as `R` — **a six-letter word became the action *Right* by
accident.** Same class as every false verdict this project has filed: a reader broad enough to find an
answer in text that does not contain one. Caught by the controls; it is now a named control.

**NO SOLVER, NO OPTIMISER, NO RENDERER, AND NO TIME LIMIT.** Dead-end detection is a LATER measurement and
needs a solver that does not exist yet; blocking version one on it would be the third-reorder defect
committed on purpose. **THE CAP IS THE BUDGET, NOT THE CLOCK** — the think-pause is the point, and the
eight-minute debate in the promo is about deliberation being legitimate.

## THE LEVELS — AND EVERY ONE CARRIES A SOLUTION THE SIMULATOR CONFIRMED

**A LEVEL WHOSE SOLVABILITY NOBODY CHECKED IS NOT A LEVEL.** `verify_levels.py` requires a solution per
level and plays it; an entrant failing on an impossible grid would be recorded as a fact about the entrant.

```
01_one_push     1 move       THE FLOOR OF THE SCALE. A model that cannot do this cannot play at all.
02_two_boxes    12 moves     requires routing the player around a solved crate, so a model that pushes
                             in one direction only cannot finish.
```

**AND THE THIRD LEVEL IS NOT WRITTEN YET, WHICH IS A GAP I AM NAMING RATHER THAN PAPERING.** Chilly asked
for a level *nobody can solve* so the scale is visible from run one. **Designing one that is BOTH hard AND
verified-by-solution is not something to fake: my first attempt at a corner-routing level was UNSOLVABLE,
which the simulator told me and a hand-wave would not have.** The gap is named in the outcome rows below.

## THE GATE — AS FRACTIONS, AND WITH TODAY'S TWO FIXES BAKED IN

```
COVERAGE   attempted / planned    >= 0.95
YIELD      measured  / attempted  >= 0.85
```

**ATTEMPTED IS COUNTED, NOT COMPUTED.** An entrant that returned a NONZERO code in under 5 s never
reached a model; it is `never_started` and it is subtracted. **Measured today: a run that never started
against ANY entrant reported COVERAGE 1.000**, because every entrant was "attempted" and none was measured.

**AND A RUN WHOSE MEASURED COUNT IS ZERO IS AN ERROR, NOT A VERDICT.** An empty field is not a measurement
of an empty field; it is a broken runner, and it exits non-zero. **COVERAGE CANNOT TELL "ATTEMPTED" FROM
"STARTED" AND TOTAL FAILURE IS ITS PASSING CONDITION.**

## THE POPULATION — DERIVED FROM `ARENA_MODELS`, NOT TYPED

**The same resolution `run_card.py` uses, at a spread across the size range.** Typed names produced five
ABSENT entrants in one attempt today, and a second directory produced a probe against eight models while
the arena holds fifty-three. **A population named twice is a population that can disagree with itself.**
`mmproj*` are vision projectors and are excluded explicitly.

**AND THE ENTRANT MUST LOAD.** The population rule, unchanged: an entrant is not a result until it can load.

## THE CRITERIA, FROZEN BEFORE THE FIRST NUMBER

```
C1  SCALE IS VISIBLE   at least one level solved by at least one entrant, AND at least one level solved
                       by NONE. A suite every entrant solves and a suite none solves are both failures of
                       the instrument; the point of run one is that the range exists.
C2  THE FLOOR          at least one entrant solves 01_one_push (1 move). A population that cannot push a
                       single crate one square is the Sokoban version of the chess finding.
C3  MOVES ARE A NUMBER  the move count is reported per entrant per level, with `blocked` and
                       `unrecognised` beside it -- a score is not a score if a wall-bumper and a solver
                       can produce the same row.
```

### THE OUTCOME ROWS, WRITTEN DOWN BEFORE THE RUN

**1. GATE UNMET** → `NO VERDICT — THE FIELD DID NOT COMPLETE.` Name which ratio failed. Call nothing a pass
   or a fail.
**2. GATE MET, criteria evaluated** → a verdict, each number quoted with the set it was computed over.
**3. GATE MET, a criterion fails, population remains a candidate cause** → `FAILED ON THIS POPULATION` as a
   scope. **Declared here, so it cannot be a hedge added after a result. It may attach to a FAIL and never
   excuses one.**
**4. INSUFFICIENT / BLOCKED** → **if the population cannot push a single crate, or no entrant can load, or
   no level separates anyone, THAT IS THE RESULT.** It is reported as `INSUFFICIENT` with the population
   named and the rates attached, **and the event is NOT re-scoped until something fits.** This row is the
   reason it is written in advance: it is the row that exists so a null result cannot be quietly converted
   into a positive one by changing the question.
**5. NO MEASURED ENTRANTS** → `ERROR`, exit non-zero, not a verdict.
**6. THE THIRD LEVEL IS ABSENT** → `C1 SCALE IS VISIBLE` cannot be evaluated as written; it is scored on
   the levels that exist and **the level set is named as incomplete in the verdict itself.**

## FROZEN

**The simulator, its controls, the level set with its verified solutions, the gate, the population rule and
the outcome rows above are fixed at this commit.** No number below this line may move in response to an
entrant's result. **The chess lesson carried here intact: fixing an instrument can invalidate the evidence
taken under it, and that is the correct cost of fixing it.**
