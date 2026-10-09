# PRE-REGISTRATION — HOW THE NEXT POSITION SOURCE GETS CHOSEN

**Written after the walk was refuted and BEFORE either replacement exists.** Chilly's framing, and it is the
right one: *the whole question is where it should be — written down before the next attempt rather than
after it.*

---

## WHY THIS FILE EXISTS RATHER THAN A SOURCE

**Four walk-based generators failed four different ways (FINDING 014, 015). The fifth attempt should not be
chosen by preference, because preference is exactly what a sequence of justified changes looks like from
the inside.** So this file fixes **how the choice is made** before either candidate is built.

## THE TWO CANDIDATES

**A — A RECORDED DECISIVE-GAME CORPUS, sampled at its critical moments.**
Each game is a separate derivation, so it has the **independence property the walk lacked.** That is the
requirement that killed the walk, and A is the better candidate on it.

**B — POSITIONS CONSTRUCTED TO A TARGET EVALUATION, then verified by the oracle.**
The evaluation is *engineered* rather than *drifted into*, which attacks the problem from the other end:
instead of searching for positions in the window, it builds toward one.

## AND THE WARNING THAT MUST PRECEDE BUILDING EITHER — CHILLY'S, AND IT IS SHARP

> **A MOVES THE BIAS RATHER THAN REMOVING IT.** *"Sampled at their critical moments"* **is a selection
> rule.** If it is not pre-registered, it becomes **the at-risk filter in a new costume**: positions
> retained *because* they are critical **manufacture the at-risk rate** exactly as positions retained for
> being near −100 would.

**SO FOR CANDIDATE A, DECLARE THE RULE BEFORE SAMPLING:**

1. **What counts as a critical moment** — stated as a mechanical test on the game record, not as a
   judgement. **Not** "where the evaluation swings", unless the swing threshold is a number fixed here.
2. **At what granularity** — a ply, a position after a capture, a move-number boundary. **A coarse
   granularity that happens to include window positions is the filter again.**
3. **Decided by what** — by the engine at the frozen config, or by the game's own record. **Stating the
   decision procedure is the point, not stating its result.**
4. **And the count that proves it did not select:** the corpus's evaluation distribution must be
   **reported before** the at-risk count, so a reader can see the sample was drawn the same way regardless
   of what was wanted.

**CANDIDATE B CARRIES THE MIRROR RISK AND IT MUST BE NAMED TOO:** *"constructed to a target evaluation"*
is a generator that **aims at the window.** That is legitimate — the oracle verifies every position — but
**the aim must be declared as the aim**, or a constructed set reads as a discovered one. **B's honest
framing: the set is engineered toward the band, the oracle verifies each member, and the only claim it
supports is about positions at those evaluations.**

## THE MEASUREMENT — BOTH, AND THE NUMBERS CHOOSE

> **Measure the acceptance rate on BOTH and let the numbers choose.**

**The unit is ONE INDEPENDENT DERIVATION, never a ply.** FINDING 015: six hits along one walk are one
observation wearing six indices. **So the acceptance rate is *derivations that yielded an accepted
position*, over *derivations attempted* — and a hit harvested from consecutive plies is not a derivation.**

**And the smoke rule applies, as it did to the walk: ten derivations before a hundred.** The walk's rate
was measured at **0.00** and it **saved an unbounded spend.**

**AND 0.00 IS A REFUTATION, NOT MERELY A DISAPPOINTMENT.** A source that never yields is **refuted**, and
that is a result that can be stated — which is a better place to be than a walk that was never checked.

## WHAT DOES NOT MOVE — THE SAME FOUR CONSTANTS

```
LOST_CP = -300     HOLD_CP = -100     WINDOW = 60     MIN_PER_EDGE = 5
```

**Frozen at `49ef665`; verified across every revision by `check_frozen_constants.py`.** **No candidate may
be evaluated against a different window, a different threshold, or a lowered floor** — and the fact that
lowering the floor to 3 would make the existing source pass is the reason that check exists.

**AND THE COMPOSITION CHECK STILL RUNS FIRST.** A source that reaches one edge and not the other is
`ONE-EDGED — NOT ADMISSIBLE`, and **no sensitivity is reported.** That row was written before the second
test and it is not renegotiable now.

## THE RULE THIS SEQUENCE PRODUCED, RECORDED HERE BECAUSE IT IS THE GENERAL FORM

> **A research programme is not exonerated by the honesty of its intent. It is exonerated when its changes
> FAIL, and the failures are caught by controls that predate them.**
>
> **And drift is checked by what you REFUSED, not by what you justified.** Lowering `MIN_PER_EDGE` from 5
> to 3, or widening `WINDOW` from 60 to 120, would have made the test run at every step. **Neither was
> taken, in five revisions, and that is checkable by diff.** A constants check proves the criteria did not
> move; **a refused shortcut proves they were not moved when moving them would have paid.**

## FROZEN

**This file is fixed at this commit.** Both candidates are to be built, measured at ten independent
derivations each, and compared by their numbers — **and if both are 0.00, that is the answer, and the
depth-sensitivity question is reported as unreachable with the tooling this repo has rather than quietly
re-scoped until something fits.**
