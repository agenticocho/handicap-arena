# FINDING 015 — THE DEPTH-SENSITIVITY QUESTION IS BLOCKED ON POSITION TOOLING, AND THE FLOOR DOES NOT MOVE

**Test 3 cannot be pre-registered.** Its source does not reach the floor, and the floor is frozen. This is
the correct outcome and it is written down rather than worked around.

---

## WHAT WAS MEASURED

```
-100 edge (window [-160, -40])   6 hits   pawn mv19..29     MET
-300 edge (window [-360, -240])  3 hits   two-pawns mv11,13,17   SHORT against a floor of 5
```

Reached after four source iterations: test 1's legal-move walk (0 LOST in 30), test 2's material ladder
(all HOLDABLE — a constant side to move), a sparse combined probe (3 and 2), dense every-ply sampling
(6 and 3), and a focused heavy-rung probe (3).

## AND THE COUNTS ARE WORSE THAN THEY LOOK: THE HITS ARE AUTOCORRELATED

**The 6 hits near `-100` are plies 19 to 29 of ONE walk. The 3 hits near `-300` are plies 11, 13 and 17 of
ONE walk.** A walk that enters a window *stays in it for several plies* — that is what "passing through a
120 cp window over a few moves" means mechanically.

> **SIX HITS ALONG ONE WALK ARE NOT SIX INDEPENDENT OBSERVATIONS.** They are one crossing, sampled six
> times. **The effective sample is closer to ONE PER EDGE than to six and three.**

**AND THIS IS A RULE THIS PROJECT ALREADY HAS, ARRIVING ON A NEW AXIS.** It filed: *"agreement under a
shared rule is not confirmation — independence is a property of the DERIVATION, not of the executables."*
That was about two checkers sharing a wrong `.json.json` naming rule. **This is the same rule on SAMPLES
rather than on CHECKS:** the six hits share a derivation — the walk — so they are **one observation
wearing six indices.** *The count was never the sample size.* **The relevant number is walks, and it was
one.** *(Chilly's sentence, adopted verbatim because it is the finding in one line.)*

**So the reach is not marginally short. It is short by the ratio between "hits" and "independent walks",
which the count does not show.** A reach statistic that counts plies inherits exactly the defect this
project keeps finding: **a count quoted over a set that is not the set the reader assumes.**

**CONSEQUENCE, AND IT IS A REQUIREMENT FOR ANY FUTURE SOURCE:** reach must be reported as **independent
walks that entered the window**, not as ply-hits. A generator that walks one game per rung cannot meet a
floor of five no matter how finely it is sampled.

## WHAT THE FLOOR DOES NOT DO

**`MIN_PER_EDGE = 5` is frozen, and it was not touched.** The sequence of source changes was:

| iteration | change | justified by | floor |
|---|---|---|---|
| test 1 | legal-move walk | — | 5 |
| test 2 | material ladder | test 1 reached no LOST position | 5 |
| probe 3 | both pooled | test 1 reached −100 only, test 2 −300 only | 5 |
| probe 4 | every ply, denser | probe 3 was sparse | 5 |
| focused | heavy rungs only | probe 4 filled one edge | 5 |

**Four source changes, four measurements that preceded them, and `MIN_PER_EDGE` unchanged in all five
rows.** `check_frozen_constants.py` verifies this mechanically: **NO DRIFT**, all four constants
`-300 / -100 / 60 / 5` in every revision.

**AND THE DIRECTION OF TRAVEL WAS ALWAYS AVAILABLE AND WAS NOT TAKEN.** The cheap way to make this test
run is to lower the floor to 3 — the number the source already produces. **It was not lowered.** That is
the answer to the question I asked Chilly to watch for, and it is answerable by diff rather than by
promise, which is the only kind of answer that counts.

## THE ACCEPTANCE RATE, MEASURED — AND THE SAMPLER IS INFEASIBLE AS DESIGNED

**FINDING 015's own prescription was a rejection sampler over many walks, with the cost "roughly one walk
per accepted position". That was a DERIVATION. It is now a measurement, on ten walks before anyone budgets
on a hundred — the four-ply rule applied to money instead of to a loop body.**

```
10 independent walks (fresh rung, fresh ply length, fresh seed -- one derivation each)

  rook    50 plies  d18   719          queen   58 plies  d18   889
  pawn    56 plies  d18  -484          bishop  11 plies  d18  -828
  rook    22 plies  d18   602          queen   29 plies  d18  -945
  queen   43 plies  d18 -1066          knight   8 plies  d18   810
  rook    14 plies  d18   736

  ACCEPTED near -300 : 0 of 9        near -100 : 0 of 9
  ACCEPTANCE RATE    : 0.00 per walk        BUDGET: UNBOUNDED on this evidence
```

**THE SAMPLER IS INFEASIBLE AS DESIGNED.** An independent random endpoint essentially never lands in a
120 cp window, and the reason is structural rather than unlucky:

> **A WALK DOES NOT DWELL IN A WINDOW — IT TRANSITS IT.** The hits that exist are found at *particular
> plies* (two-pawns mv 11, 13, 17 at −344, −351, −332), which is the signature of a value passing through
> a narrow band, not of a position set living in one. **A random endpoint samples the distribution of
> evaluations, and that distribution is concentrated far from the band** — a handicap of a pawn or more
> puts the evaluation at ±180 or beyond, and a few dozen plies of engine play does not bring it back.

## AND THE TENSION THAT MAKES THIS HARD RATHER THAN MERELY UNLUCKY

```
sampling EVERY PLY along a walk      finds the windows      but the hits share ONE derivation
sampling ONE ENDPOINT per walk       independent            but accepts ~0
```

**Those are the only two cheap options, and each fails a different requirement — the first on
independence (FINDING 015's autocorrelation), the second on rate. That is why four source iterations did
not converge: they were all walk-based, and a walk-based generator cannot be both dense in the windows and
independent.**

**SO THE UNBLOCK IS NOT A BETTER SAMPLER. IT IS A DIFFERENT KIND OF SOURCE** — one that produces positions
whose evaluation is *engineered* rather than *drifted into*: a corpus of recorded decisive games sampled at
their own critical moments, or positions constructed to a target evaluation and then verified by the
oracle. **Both are harder than a walk and both are the honest next step; neither is reachable by tuning the
thing that has already failed four times.**

## AND THE META-RESULT, WHICH IS THE ACTUAL YIELD OF THE LAST THREE HOURS

**Every attempt to make this test runnable by changing the generator failed, and every failure was caught
by a check built before it:**

- **test 1**: 0 LOST in 30 positions — caught by the composition check.
- **test 2**: all HOLDABLE from a constant side to move — caught by the composition check.
- **probe 3/4**: reach short, and the hits autocorrelated — caught by reading the plies rather than the count.
- **acceptance smoke**: rate 0.00 — caught by measuring the rate before budgeting on it.

**The cheap way to make the test run was available at every step — lower `MIN_PER_EDGE` from 5 to 3, or
widen `WINDOW` from 60 to 120 — and neither was taken, in five revisions.** `check_frozen_constants.py`
proves that mechanically rather than by assurance. **The test is blocked, and the criteria never moved.**

**AND THE GENERAL FORM OF THAT META-RESULT, filed because it is worth more than the test:**

> **A research programme is not exonerated by the honesty of its intent. It is exonerated when its
> changes FAIL, and the failures are caught by controls that predate them.**
>
> **AND DRIFT IS CHECKED BY WHAT YOU REFUSED, NOT BY WHAT YOU JUSTIFIED.** Lowering `MIN_PER_EDGE` from 5
> to 3, or widening `WINDOW` from 60 to 120, would have made the test run at every step. **Neither was
> taken, in five revisions, and that is checkable by diff.** A constants check proves the criteria did not
> move; **a refused shortcut proves they were not moved when moving them would have paid.**

**The next source is chosen under exactly those rules — `PREREG_source_selection.md`, written before either
candidate exists.**

## AND A SECOND, SMALLER INSTANCE OF THE SAME FAMILY

**The dense probe stopped after one rung and I could not tell why.** Its output shows the pawn rung
complete, **no `BUDGET REACHED` line, zero errors, and nothing after** — and the process record had been
recycled, so there was no exit code to read. **"Completed" and "killed quietly" were indistinguishable
from the artifacts available.** Same shape as the crashed probe reported as running: *a reading that
cannot tell presence from absence.* The lesson is the one already learned and not yet applied everywhere:
**a harness that can stop without saying so needs to say so — write an explicit terminal line at the end
of every run, so absence of it IS the signal.**

## STANDING

- **Test 3 is NOT pre-registered**, because its source does not reach the frozen floor.
- **`MIN_PER_EDGE` is NOT lowered**, and `check_frozen_constants.py` proves it mechanically.
- **The sensitivity statement remains open**, blocked on a position generator rather than on a decision.
- **The next step is a rejection sampler counting independent walks**, and its acceptance rate is the
  thing to measure first.
