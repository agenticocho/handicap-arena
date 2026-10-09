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

## WHAT WOULD ACTUALLY UNBLOCK IT

**A generator that produces INDEPENDENT positions inside the windows**, which means a **rejection sampler
over many walks** rather than one walk per rung:

1. Draw a rung and a random legal continuation, deterministically seeded.
2. Evaluate the resulting position at the frozen config.
3. **Keep it if it is in a window; discard it otherwise.**
4. **Count independent positions accepted, and walk again from a fresh start each time** — never
   harvesting consecutive plies.
5. Stop at the floor or at a stated budget, and **report which**.

**The acceptance rate is knowable in advance from this finding:** a walk passes through a 120 cp window
over a few plies out of ~70, so the rate is low and the cost is roughly *one full walk per accepted
position*. **Five per edge is therefore tens of walks per edge, not one** — which is why one walk per rung
could never reach it, and why the earlier "candidate counts" of 60 and 105 were never the relevant number.
**The relevant number is walks, and it was one.**

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
