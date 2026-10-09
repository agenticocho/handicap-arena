# FINDING 014 — TWO SOURCE FAILURES IN A ROW, AND THE COMPOSITION CHECK CAUGHT BOTH

**Test 2 returned `INADMISSIBLE`.** Not a partial result, not a sensitivity — **a refusal**, exactly as
`PREREG_depth_sensitivity.md` (49ef665) specified. The pre-registration did its job twice tonight.

---

## THE RESULT, AS THE TEST REPORTED IT

```
candidates generated    64        (target >= 60)
reproducible at d18     64        <- the ORACLE is stable on these positions; that part is sound
d18 side distribution   {'HOLDABLE': 64}
ADMISSIBILITY           at-risk near -300: 0   need >= 5
                        at-risk near -100: 0   need >= 5
                        *** INADMISSIBLE -- NOT ADMISSIBLE ***
```

**No sensitivity is reported, and no conclusion about either edge follows in either direction.**

## DEFECT 1 — A CONSTANT SIDE TO MOVE, FROM MY OWN MOVE LIST

**Material was removed from BLACK, and White moves first in the start position. `MOVES` was
`[0, 2, 4, 6, 8, 10, 12, 14]` — ALL EVEN.** So the side to move was **White at every candidate**, the
evaluation is taken **from the side to move**, and White was ahead in all of them. **64 positions, one
sign, one band.**

```
even move counts only  ->  side to move never alternates  ->  every eval positive  ->  all HOLDABLE
```

**The fix is one line — include ODD move counts — and it works:** with `[0,1,2,3]` the distribution becomes
**HOLDABLE 16, GREY 2, LOST 14**, because an odd count leaves Black to move and the sign flips.

## DEFECT 2 — THE LADDER'S RUNGS STRADDLE THE WINDOWS, WHICH DEFECT 1 WAS HIDING

With the sign fixed, **the at-risk counts were STILL zero**, and this one is structural:

```
the at-risk windows           near -100: [-160, -40]      near -300: [-360, -240]
                                    width 120 cp                  width 120 cp

the material ladder's rungs   pawn       ~181      two-pawns  ~459
                              knight     ~764      bishop     ~803
                              -> ONE RUNG IS ~200 cp. THE RUNGS ARE WIDER THAN THE WINDOWS.
```

**The rungs do not land in the windows — they step over them.** Measured: a pawn handicap gives −189, the
window tops out at −160; two pawns gives −400, the window starts at −360. **A material ladder cannot
populate a 120 cp window when its spacing is 200 cp.**

## AND A LONGER WALK REACHES *ONE* EDGE, MEASURED RATHER THAN CLAIMED

Walking each rung further, evaluating every position:

```
two-pawns  moves 11  d18 -344   NEAR -300
two-pawns  moves 13  d18 -351   NEAR -300

pawn       moves  9  d18 -161   just outside [-160,-40] -- by ONE centipawn
pawn       moves  3  d18 -177   outside
pawn       moves 15  d18 -176   outside
```

**So extended walking reaches the `-300` edge and does NOT reach `-100`.** The smallest material deficit
this ladder can make is ~180 cp, and the `-100` window ends at 160. **Material alone cannot get there.**

## THE RESOLUTION, AND IT IS THE TWO SOURCES COMBINED

**Test 1's source and test 2's source fail in OPPOSITE directions, and each reaches the edge the other
misses:**

```
test 1  balanced legal-move walk       reached -100 (3 at-risk: -60, -110, -122)      NOT -300
test 2  material handicap ladder       reaches -300 (-344, -351 measured)             NOT -100
```

**A balanced walk sits near zero, so it drifts through the `-100` window; a material ladder sits far from
zero, so its walk drifts through the `-300` window.** Neither reaches both. **Test 3's source is both
generators, pooled — and the reach is verified per edge before the crossing count is read.**

## THE META-FINDING, AND IT IS THE ONE WORTH KEEPING

**"Both edges are reachable by construction" was written into the pre-registration as an assertion, and it
was FALSE — twice, for two different reasons, in one test.** The construction was never constructed; the
claim was a hope wearing the clothes of a derivation.

> **A SOURCE'S REACH IS A MEASUREMENT, NOT A PROPERTY OF ITS DESIGN.** The composition check is what made
> the difference: it refused to report a sensitivity over a sample that could not answer the question —
> **twice** — and **both refusals were correct.**

**CONSEQUENCE FOR TEST 3, AND IT IS A REQUIREMENT RATHER THAN A NOTE:** the pre-registration must carry a
**MEASURED REACH** for each edge — the number of at-risk positions found near `-300` and near `-100`, in a
stated probe, **recorded before the test runs.** "By construction" is not admissible as an argument;
**only the pre-test probe is.** Two failures of exactly that claim is enough to fix the practice rather
than restate the claim.

**AND THE CHEAP PART: the probe costs one evaluation per position and caught both defects in minutes.**
Neither was findable by re-reading the design.
