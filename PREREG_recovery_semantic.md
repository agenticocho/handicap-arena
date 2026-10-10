# PREREG — DOES RECOVERY SURVIVE A SEMANTIC DEFECT CLASS?

**Written and committed BEFORE the first number. The Chair's ruling 80 applies (prediction + motive), and his
instruction: the branch table must carry a branch I would be embarrassed by, and the file must state WHAT A
FAILURE WOULD MEAN, not only what a success would.**

---

## WHY THIS IS STILL OPEN, AND WHY THAT IS NOT AN OVERSIGHT

**The Chair asked whether recovery survives a SECOND defect class. TASK 3 DID NOT TEST IT.**

```
task 2  SYNTACTIC      failed one-shot -> ONE CORRECTIVE TURN -> 22/22      RECOVERY TESTED
task 3  SEMANTIC       passed ONE-SHOT -- THERE WAS NO DEFECT TO RECOVER FROM
```

**A model that passes first time provides NO evidence about what happens when it does not.** I recorded that as
the open question at the time rather than letting a clean pass close it. **This experiment is that question, asked
properly.**

## THE CLASS, AND WHY IT IS THE ONE THAT MATTERS

```
TASK 2's CLASS   a ternary inside a string literal     the COMPILER catches it; a traceback NAMES THE LINE
TASK 3's CLASS   a flood fill over cells               WRONG ANSWERS COMPILE TOO -- it never failed
THIS EXPERIMENT  BFS over STATES for the minimum       A WRONG ANSWER COMPILES, RUNS, AND RETURNS A NUMBER.
                 number of moves to solve a level
```

**IT IS THE CLASS THE CABINET FEARS MOST: a compiling wrong answer that survives a checker.** Measured on this
box, every green control we own has only ever been exercised against failures that failed LOUDLY. **A semantic
defect does not fail loudly. It returns a plausible integer.**

**AND THE TASK IS REAL CABINET WORK** — the solver does exactly this to produce the BFS-verified shortest
solutions the levels are published with.

## THE TASK, AND THE TRAP

**Implement `min_moves(position)` returning the minimum number of player moves that solves the level. The level is
guaranteed solvable, so there is no unreachable case to model.**

**TWO WAYS TO GET IT WRONG, AND NEITHER IS A COMPILE ERROR:**

```
TRAP 1  count PUSHES instead of moves            a plausible, WRONG integer -- and it is the natural
                                                 mistake, because the level files are discussed in pushes
TRAP 2  BFS over POSITIONS without visiting      it terminates on these levels but finds a LONGER path,
        the goal state as a state                or loops on a level where a crate moves twice
```

**VERIFIED against the level's own published shortest solution length** — 01 = 1, 02 = 12, 03 = 6, all
BFS-verified elsewhere in this repo. **The oracle is the VERIFIED ANSWER, not the model's output and not a
hand-typed expectation.**

## THE PREDICTION — AND THE MOTIVE, PER RULING 80

**I PREDICT BRANCH F: IT FAILS ONE-SHOT WITH A WRONG INTEGER, AND RECOVERS WHEN THE CHECKER NAMES THE
DISAGREEMENT.**

**AND I WANT IT TO FAIL, WHICH I AM RECORDING AS THE MOTIVE BECAUSE IT IS THE OPPOSITE OF LAST TIME.** I have
spent this evening arguing that the COMPILING WRONG ANSWER is the class that matters, that it is what the cabinet
should fear, and that a semantic worker needs an independent oracle rather than a checker the model can satisfy.
**A PASS WOULD LEAVE THAT ARGUMENT UNTESTED AND ME HOLDING A CONCERN NOBODY CAN ACT ON. I AM PREDICTING THE
FAILURE THAT WOULD VINDICATE MY OWN EMPHASIS — which is exactly the bias this section exists to expose, and it
is the mirror image of last experiment, where I predicted the branch that kept my framing alive and was wrong.**

## THE BRANCH TABLE — INCLUDING THE ONE I WOULD BE EMBARRASSED BY

**BRANCH F — FAILS ONE-SHOT (WRONG INTEGER), RECOVERS ON THE CHECKER'S DISAGREEMENT.**
**WHAT THAT WOULD MEAN:** recovery generalises from a traceback to a WRONG VALUE. **The non-one-shot worker
pattern holds across two defect classes, which is the strongest claim available at this sample size — and the
first evidence that a feedback loop reaches a defect that never announced itself.**

**BRANCH P — PASSES ONE-SHOT. *(THE BRANCH I WOULD BE EMBARRASSED BY.)***
**WHAT THAT WOULD MEAN:** the semantic class did not trip it either. **MY EMPHASIS ON THE COMPILING-WRONG-ANSWER
CLASS WOULD HAVE TWO NULLS BEHIND IT AND ONE OF THEM WOULD BE AN EXPERIMENT I WROTE SPECIFICALLY TO PRODUCE A
FAILURE.** The honest reading then is that I have been weighting a risk by how interesting it is rather than by
how often it occurs — **and I would rather write that here, before the number, than have it read as a surprise
afterwards.**

**BRANCH S — FAILS, AND PATCHES THE REPORTED CASE ONLY. *(THE DANGEROUS ONE.)***
**WHAT THAT WOULD MEAN:** it converges on the checker while repeating the mistake. **IN A SEMANTIC CLASS THAT
SHIPS** — the loop reports success and the number is wrong. **The mitigation would not be a better prompt; it
would be that a semantic worker needs an INDEPENDENT ORACLE, not a checker the model can satisfy.**

**BRANCH N — FAILS, AND NO FEEDBACK FIXES IT.**
**WHAT THAT WOULD MEAN:** recovery depends on the defect ANNOUNCING ITS LOCATION. **Task 2's Branch 1 would not
generalise, and the capacity conclusion would narrow to "non-one-shot works where the failure names itself."**

**BRANCH Z — NO ANSWER.** Nothing about recovery is established. Reported as that.

## THE CONFOUND, NAMED BEFORE THE RUN

**The corrective turn is not independent of the failing turn.** It carries that turn's output and the checker's
report. **This does not make it n=2 for the one-shot question and it is not counted as one.**

**AND THE STANDING CAVEAT, UNCHANGED:** one model, one checkpoint, one task per class. **A recovery here licenses
nothing about a population, and the profiles still do not move on it.**
