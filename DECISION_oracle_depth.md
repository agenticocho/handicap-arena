# DECISION — THE ORACLE DEPTH: OUR 18 VERSUS THE FREEZE'S 12

**Raised by Chilly (2026-10-08). Ours to settle between the holder of the chess card (this repo) and the
holder of the oracle document.** Recorded before any chess measurement so it is not discovered mid-run.

---

## THE ANSWER

**Carry both. Never pool.** — which is Chilly's read, and it is right. **But the reason is not the one
offered, and the right reason changes what "never pool" has to mean:**

> **DEPTH, CONFIG AND THRESHOLD ARE ONE PARAMETER, NOT THREE.** A threshold of "−300 centipawns" is only a
> number **at a stated depth and a stated config**. Change either and the number means something else.

## WHY, MEASURED RATHER THAN ARGUED

From `chess_freeze_check.py` and the follow-up Hash measurement on this box, kiwipete, Threads=1:

```
Hash=16:   d8 -172   d12 -196   d16 -213   d18 -228   d20 -215
Hash=64:   d8 -172   d12 -196   d16 -213   d18 -255   d20 -274
```

**Read the `d12` and `d18` columns under Hash=64, which is our frozen config:**

```
d12  -196          d18  -255          difference  59 cp
```

**Our card's GREY BAND is `(-300, -100]`.** So the same position, at the two depths in question, is:

- **−196 at d12** → inside the band, further from `LOST`
- **−255 at d18** → also inside the band, **but 59 cp closer to it**

Neither is `LOST` here. **A position sitting near −300 flips between the depths:** `−290 at d12` and
`−349 at d18` would be **GREY under one and LOST under the other**, and a model that resigned would be
**scored as prematurely collapsing under one depth and correct under the other** — with both runs perfectly
reproducible, and neither wrong.

**So the threshold does not survive a depth change.** That is why a "common depth" is not the cheap
compromise it looks like.

## WHY "COMMON DEPTH" IS NOT THE SMALLER CHANGE

Choosing a common depth **does not** reconcile the two cards, because **each card's threshold was chosen
against its own depth.** Moving one is re-deriving a criterion:

- **depth 12 + a −300 threshold** is a combination neither author chose;
- the threshold at depth 12 would have to be **re-chosen, justified and frozen again**, for both parties.

**That is a new card on each side, not a compromise between two.** And it buys nothing that carrying both
already buys.

## AND THE REASON IS NOT "DIFFERENT MACHINES" — THE BOXES AGREE

**This matters, because the obvious argument for never pooling would be that the two boxes disagree. They
do not.** Measured here: at `Threads=1, Hash=16` this box returns the other box's series **exactly, to the
centipawn** (`−172 −196 −213 −228 −215`). **Same engine asset, same config, same numbers.**

So **the incompatibility is the DEPTH, not the hardware** — and the corollary is the useful one:

> **CROSS-MACHINE COMPARISON IS AVAILABLE.** When `engine + config + depth` are pinned, two boxes are
> comparable. That is precisely what makes carrying the freeze fields worth the four lines.

## WHAT "NEVER POOLED" HAS TO MEAN, CONCRETELY

Not "keep the two results apart" — that is a filing convention. It has to be a property of the record:

1. **Every `eval_before` / `eval_after` carries its `depth` and its `config`.** Already in AMENDMENT 1.
2. **A score is always reported with the triple that produced it** — `(engine, config, depth)` — and never
   as a bare rate.
3. **Two scores from different triples are DIFFERENT MEASUREMENTS of the same faculty**, exactly as
   Format A and Format B are different measurements of a related faculty. **Comparable in shape, never
   averaged together, never combined into one rate.**
4. **A cross-depth comparison may be REPORTED and must state whether any position crossed the threshold
   between the two depths** — because that is the only way two depth-different results can mislead.

## THE TEST THAT WOULD LICENSE A COMMON DEPTH, AND IT IS CHEAP

**"Both move to a common depth" becomes available the moment it is shown that the VERDICT does not depend
on the depth** — not that the evaluation does not, which it plainly does.

> **Score the same frozen position set at d12 and at d18, apply each depth's own threshold, and count how
> many positions change side. ZERO changes → a common depth is available. Any change → it is not, and
> "carry both" is permanent.**

**This is runnable on this box with the oracle already secured, before the chess harness exists**, because
it needs only positions and the engine — not a model. **I would rather run it than decide by preference.**

**AND THE PREDICTION, SO THE TEST IS FALSIFIABLE RATHER THAN DECORATIVE:** the one position measured above
moved **59 cp** between d12 and d18 against a **200 cp band** — so I expect **few, and not zero**, positions
to cross. **A prediction of "zero" would be contradicted by the measurement already in hand.**

## STANDING

**Until that test runs: both depths are carried, neither is substituted, and no rate is reported without its
triple.** Nothing is blocked by this — each box can score its own field tonight.
