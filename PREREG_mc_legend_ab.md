# PRE-REGISTRATION — THE LEGEND A/B (`example` vs `plain`), MISSILE COMMAND

**Written BEFORE the second arm was run.** The arm it proposes does not exist on disk as a measurement
until this file is committed; the prediction below is the whole point of writing it first.

**Status:** an INSTRUMENT experiment on THIS CABINET's own driver. **No frozen criterion moves** — the
simulator, its 34 controls, the two states, the criteria and the outcome rows in
`PREREG_missile_command.md` are untouched, and its digest is recorded in every artifact.

---

## WHAT WAS MEASURED, AND WHY THIS FILE EXISTS

The cabinet's entrant path was driven for the first time on 2026-10-17 (three entrants, four states, all
under `scripts/run_guarded.sh`). **Every cell that loaded produced zero cities, and the reason is visible
in the tokens:**

| entrant | arm | state | tokens | `fired` | `unknown` | score |
|---|---|---|---|---|---|---|
| Ternary-Bonsai-2-4B (prism fork) | example | mc_01 | `PASS PASS PASS` | 0 | 0 | 0/1 |
| Ternary-Bonsai-2-4B (prism fork) | example | mc_02 | `PASS`×6 | 0 | 0 | 0/4 |
| granite-3.3-2b (default binary) | example | mc_01 | `PASS PASS PASS` | 0 | 0 | 0/1 |
| granite-3.3-2b (default binary) | example | mc_02 | `PASS PASS 3W 3W 3W 3W` | 0 | 4 | 0/4 |
| Qwen3.5-2B (default binary) | example | mc_01 | `3P 3P 3P` | 0 | 3 | 0/1 |
| Qwen3.5-2B (default binary) | example | mc_02 | `3X 3X 3X 3Q 3P 3T` | 0 | 6 | 0/4 |

**The silo digit in every firing token is `3`, and `3` is the legend's own format example** —
*"3W would mean fire from silo 3 at a threat called W -- no silo 3 and no threat W exist here, that is only
the shape of an answer."* The example was chosen from **outside both frozen states** precisely so it could
not be read as an answer. **The threat letters, by contrast, are read correctly from the state**
(`X`, `Q`, `P`, `T` are real threats; `W` is the legend's). So one half of the answer is being read and the
other half is being copied.

**THE CLAIM UNDER TEST:** *the legend's example does not teach the shape only — it supplies the silo value*,
and a legend with no concrete example in it will move the firing tokens' silo number onto the state.

## THE TWO ARMS, BOTH KEPT VERBATIM

```
example   the recorded instrument, unchanged: ... "3W would mean fire from silo 3 at a threat called W
          -- no silo 3 and no threat W exist here, that is only the shape of an answer." ...
          digest ec59f2dc5fd35518
plain     byte-identical EXCEPT that clause, which becomes: "Answer with exactly two characters: the
          number of the silo you are firing from first, then the letter of the threat you are firing at.
          Those two values are in the state above -- use the silo numbers and the threat letters exactly
          as they are written there."   (no digit, no letter of its own)
```

**The old arm is restored VERBATIM, and the two arms are identical in every other byte** — different
legends that share a tidied paraphrase would measure the tidying. **`example` REMAINS THE RECORDED
ARM**: the default does not move because an experiment ran, and every record already taken keeps the
instrument it was taken under.

## THE PREDICTION, RECORDED BEFORE THE SECOND ARM RAN

**If the example is the carrier, the `plain` arm will:**

1. **move `unknown` DOWN** — no firing token will name a silo that does not exist;
2. **move `fired` UP** — at least one token will name a silo the state actually has (`1` or `2`), so at
   least one interceptor is launched;
3. **and score above zero on at least one state**, since a launched interceptor at a city-bound threat is
   the whole of the play this cabinet measures.

**AND THE BRANCHES, so a result cannot be read as support for the claim whatever it shows:**

```
BRANCH 1  unknown DOWN and fired UP      THE EXAMPLE WAS THE CARRIER. The legend was handing over one
                                         cell of the answer set, and the repaired legend is the fix.
BRANCH 2  no movement at all             THE EXPLANATION IS WRONG. The echo has another cause -- a model
                                         that cannot map the silo lines to an answer is the live candidate
                                         -- and the example is not what supplies the value.
BRANCH 3  unknown UP or fired DOWN       THE EXAMPLE WAS LOAD-BEARING FOR FORMAT COMPLIANCE: removing it
                                         costs the shape, and the defect is the price of the format.
```

## SCOPE, STATED SO THE RESULT CANNOT BE READ AS MORE THAN IT IS

**One entrant, two states, n=1 per cell, two arms, ONE clause apart.** This is a demonstration, not a
field; a second entrant is a second measurement, not a population. **The population questions (the gate,
coverage, C1–C3, whether the scores SPREAD) belong to Ocho and the Chair and are not answered here** — this
cabinet does not score its own event. **What this establishes is narrower and it is checkable:** whether
*this legend* supplies the silo value to *this entrant*, with both arms on disk and both digests in the
artifact.
