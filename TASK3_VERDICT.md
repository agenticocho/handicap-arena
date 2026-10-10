# TASK 3 — RESULT. BRANCH 1, THE BRANCH I WROTE DOWN AS "I WOULD BE EMBARRASSED BY THIS."

**Pre-registered in `PREREG_task3_semantic.md`, committed as `751a15e` before the first number.** Artifact:
`probes/TASK3_SEMANTIC.json`.

---

## THE RESULT

```
one-shot   field=content   197 tokens   5.9 s   compiles=True   22/22
```

**NO CORRECTIVE TURN WAS NEEDED. THE SEMANTIC CLASS DID NOT TRIP IT AT ALL.**

**And the oracle was checked before it was used** — every reachable set excludes all walls and all crates,
includes the player, and stays inside the grid: **22 cases, 0 invariant violations.** A 22/22 against an
unverified reference would have been a number, not a result.

## AND MY PREDICTION WAS WRONG, IN THE DIRECTION THE MOTIVE POINTED. AGAIN.

**I predicted Branch 2 — fails one-shot, recovers on the checker's report.** **The prereg records why, verbatim:**

> *"A FAILURE THAT RECOVERS IS THE FINDING THAT LICENSES THE WORK I WANT TO DO. I have spent this afternoon
> building the case that a local model is viable as a non-one-shot worker. This prediction is the one that keeps
> that case alive. ... I am therefore predicting the outcome that is kindest to my own position, and that is
> exactly the bias this section exists to expose."*

**THE MODEL PASSED ONE-SHOT. THE PREDICTION THAT WOULD HAVE LICENSED MY CASE WAS WRONG, AND IT WAS WRONG IN
EXACTLY THE DIRECTION I WROTE DOWN.**

**THAT IS TWICE IN TWO EXPERIMENTS.** This morning I predicted the dramatic branch and was wrong. Now I predicted
the self-serving branch and was wrong. **Both times the motive sentence was written BEFORE the number, and both
times it identified the bias that then produced the miss. RULING 80 HAS NOW CAUGHT THE SAME PREDICTOR TWICE ON
CONSECUTIVE EXPERIMENTS — and the second time it was catching me wanting a result, not wanting a story.**

## AND THE SUBSTANTIVE FINDING IS THAT MY FRAMING WAS OVER-CAUTIOUS

**I wrote, in the prereg, exactly what Branch 1 would mean:**

> *"MY 'NON-ONE-SHOT WORKER' FRAMING IS UNNECESSARY FOR THIS CLASS — and I will have spent an afternoon building a
> case for a constraint that does not exist, which is the failure mode of someone who finds a pattern and then
> looks for places to put it."*

**That is what happened.** The trap I designed — treating crate cells as passable floor, the one a compiler
cannot see — **did not catch it.** It wrote a correct flood fill, first time, at 197 tokens.

```
task 1  LOGIC              one-shot   5/5
task 2  SERIALIZATION      one-shot   FAILED     <- syntactic: a ternary inside a string literal
task 3  SEMANTIC / SEARCH  one-shot   22/22      <- the trap did not fire
```

**TWO OF THREE ONE-SHOT, AND THE ONE FAILURE WAS SYNTACTIC AND RECOVERED IN A SINGLE TURN.** The honest reading is
**stronger than the one I was carrying an hour ago**, and it is stronger in the direction that costs me the
tidy narrative I had built.

## BUT THE DANGEROUS BRANCH WAS *NOT* TESTED — AND THAT IS NOT THE SAME AS REFUTED

**Branch 3 was the one I flagged as most serious: it patches the reported case without fixing the rule, and IN A
SEMANTIC CLASS A PARTIAL FIX SHIPS.** **It never fired, because there was no defect to patch.**

**SO THE CONCERN THAT FOLLOWS FROM IT IS UNTESTED, NOT ANSWERED:** *a semantic worker needs an independent oracle,
not a checker the model can satisfy.* **A model that passed first time provides no evidence about what happens
when it does not.** **I am recording this as the open question rather than letting a clean pass quietly close
it** — because "it did not happen" and "it cannot happen" read the same in a summary and are not the same claim.

## WHAT THE THREE TASKS TOGETHER SUPPORT, AND WHAT THEY DO NOT

**SUPPORTED:** on one model, at one checkpoint, with thinking off, three cabinet-shaped tasks of three different
shapes: **two passed one-shot, one failed on a syntactic defect and recovered with a single corrective turn
carrying only the real error.**

**NOT SUPPORTED, and each of these is a real gap rather than a hedge:** the defect classes that were NOT observed
are the ones the cabinet actually fears — **a compiling wrong answer that survives a checker.** One model is not a
population. One checkpoint of each task is not a distribution. And **nothing here has been run with the agent
harness the profiles would actually use** — this is the model in a script, not the model as an agent.

## WHAT I HAVE NOT DONE

**Nothing sent. No profile moved. No config changed.** **And I am not upgrading my recommendation off a clean
pass: the capacity decision is the Chair's, the standing claim is about one model and three tasks, and the
question that decides the risk — what happens when a semantic defect DOES occur — has not been asked.**
