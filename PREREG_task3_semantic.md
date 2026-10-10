# PREREG — TASK 3: A *SEMANTIC* DEFECT CLASS

**Written and committed before the first number. Ruling 80 applies: the prediction AND the reason I want it to
be true. And ruling 81's spirit applies: this file contains A BRANCH I WOULD BE EMBARRASSED BY.**

---

## WHAT MAKES THIS A DIFFERENT DEFECT CLASS — AND WHY THAT IS THE POINT

```
TASK 2's DEFECT   ternary inside a string literal      SYNTACTIC
                  the COMPILER caught it                feedback: a traceback with a line number
                  it could not run at all

TASK 3's DEFECT   a search that treats crates as        SEMANTIC
                  passable floor                        THE COMPILER CANNOT CATCH IT
                                                        feedback: "case X: got 9 cells, want 6"
```

**THAT IS THE DISTINCTION THAT MATTERS, AND IT IS THE CABINET'S OWN NIGHTMARE.** A syntactic defect cannot
survive — nothing runs. **A semantic defect COMPILES, RUNS, and produces a NUMBER that is wrong**, and every
downstream artefact inherits it silently. **It is the same failure the cabinet has spent this week hunting in its
own instruments: a wrong number that looks like a right one.**

**SO THE QUESTION IS NOT "can the model write code". IT IS: WHEN THE FEEDBACK IS A WRONG VALUE RATHER THAN AN
ERROR, DOES RECOVERY STILL WORK?**

**Recovery from a traceback may depend on the error naming the line. Here nothing names anything — the checker
says what is WRONG but not WHERE.** If recovery depends on the defect being localised for the model, **task 2's
Branch 1 does not generalise, and the "non-one-shot worker" pattern is weaker than it looked an hour ago.**

## THE TASK

**Implement `reachable_cells(position)`: the set of cells the player can reach by walking, WITHOUT moving any
crate.**

**Chosen because it is REAL CABINET WORK — the dead-end mapper does exactly this to decide whether a crate is
irrecoverable — and because it carries one genuine semantic trap that a compiler cannot see:**

**TWO WAYS TO GET IT WRONG, BOTH INVISIBLE TO PYTHON**

```
TRAP 1   treat CRATE cells as passable floor        the player appears to walk THROUGH a crate.
                                                    Compiles. Runs. Returns too many cells.
TRAP 2   treat TARGET/WALL/FLOOR identically         the board's glyphs and its collision map are
         or walk off the grid edge                   DIFFERENT THINGS, and both errors compile.
```

**VERIFIED against an INDEPENDENT reference computed by the checker from the frozen walls and boxes — never from
the model's output, and never from a hand-typed expectation.** 22 goldens: the initial state of all three levels
plus every intermediate state of their verified solutions.

## THE PREDICTION

**I PREDICT BRANCH 1-with-feedback: it fails ONE-SHOT on the semantic trap, and RECOVERS when the checker reports
which case disagrees.**

**AND HERE IS THE REASON I WANT IT TO BE TRUE, per ruling 80: A FAILURE THAT RECOVERS IS THE FINDING THAT LICENSES
THE WORK I WANT TO DO.** I have spent this afternoon building the case that a local model is viable as a
non-one-shot worker. **This prediction is the one that keeps that case alive.** If the model passes one-shot, my
framing was unnecessary. **If it fails and does NOT recover, my framing is wrong.** **I am therefore predicting the
outcome that is kindest to my own position, and that is exactly the bias this section exists to expose.**

## THE BRANCHES

**BRANCH 1 — PASSES ONE-SHOT. *(THE BRANCH I WOULD BE EMBARRASSED BY.)***
**READING:** the semantic class is no harder than the syntactic one for this model. **MY "NON-ONE-SHOT WORKER"
FRAMING IS UNNECESSARY FOR THIS CLASS** — and I will have spent an afternoon building a case for a constraint
that does not exist, which is the failure mode of someone who finds a pattern and then looks for places to put
it. **Stated plainly because a branch nobody wants to land is the only kind that tests the predictor.**

**BRANCH 2 — FAILS ONE-SHOT, RECOVERS ON THE CHECKER'S REPORT.**
**READING:** recovery generalises from a traceback to a WRONG VALUE. **The non-one-shot worker pattern holds
across both defect classes, which is the strongest version of the claim available at this sample size.** Still
one model, one task each.

**BRANCH 3 — FAILS, AND PATCHES THE REPORTED CASE ONLY. *(THE DANGEROUS BRANCH — AND NOW IT COMPILES.)***
**READING:** it makes the named case pass without fixing the rule. **In a syntactic class that failure is
self-limiting — you cannot ship code that does not run. IN A SEMANTIC CLASS IT SHIPS.** A model that converges on
the checker while repeating the mistake **is more dangerous in a loop than one that fails cleanly**, because the
loop reports success. **If this lands, the mitigation is not a better prompt — it is that a semantic worker needs
an INDEPENDENT ORACLE, not a checker the model can satisfy.**

**BRANCH 4 — FAILS, AND NO AMOUNT OF FEEDBACK FIXES IT.**
**READING:** recovery depends on the defect being localised. **Task 2's Branch 1 does not generalise, and the
capacity conclusion narrows to "non-one-shot works only where the failure announces its own location."**

**BRANCH 5 — NO ANSWER.** Nothing about recovery is established. Reported as that, not as a model failure.

## WHAT WOULD FALSIFY THIS LATER, STATED NOW

**A single recovery in this class does not license the move either. Two tasks, two defect classes, one model,
n=1 each. THE STANDING CLAIM AFTER THIS EXPERIMENT IS AT MOST: "recovery observed in two defect classes on one
model and one checkpoint of one task each."** **Anything stronger is a claim about a population that has not
been sampled.**

## THE CONFOUND, AGAIN NAMED BEFORE THE RUN

**The corrective turn is not independent of the failing turn** — it carries that turn's output and the checker's
report. **This does not make it n=2 for the one-shot question and it must not be counted as one.**
