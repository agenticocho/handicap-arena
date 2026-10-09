# PRE-REGISTRATION — THE DEPTH TEST

**Written and committed BEFORE any position is drawn or evaluated.** Chilly's design requirement, and it is
the correct one: **a zero change-count over a sample drawn from the middle of the evaluation mass would be a
property of the SAMPLE, not of the instruments.** So the sampling rule is fixed first.

---

## THE QUESTION

**Our card freezes depth 18. The other oracle document freezes depth 12.** Can results from the two be
pooled, or must they be carried separately forever?

**The mechanism that would forbid pooling is already measured:** one position (kiwipete) reads **−196 at
d12 and −255 at d18** — a **59 cp** shift against a **200 cp** band. So a position near a threshold could
change side. **This test asks how often, over positions rather than over one.**

## THE FROZEN CONFIG — IDENTICAL AT BOTH DEPTHS

```
engine      Stockfish 19, linux-x86-64-universal, sf_19
config      Threads=1   Hash=64   MultiPV=1
depths      d18 (our card) and d12 (the other document) -- THE ONLY FIELD THAT VARIES
box         AMD Ryzen 5 5600, 12 logical CPUs, 60.7 GiB RAM, RTX 3060 Ti / 580.178.04
```

**Everything except the depth is held constant.** If any other field moved, the test would measure the
wrong thing — and the Hash measurement earlier today is the proof that one field suffices to move the
answer by 27 cp and flip a monotonicity.

## THE THRESHOLDS UNDER TEST — THE CARD'S OWN, UNCHANGED

```
LOST       eval <= -300
HOLDABLE   eval >= -100
GREY       (-300, -100) exclusive      NOT SCORED
```

## THE SAMPLING RULE — PRE-REGISTERED, BEFORE DRAWING

**1. THE CANDIDATE SET.** Positions are produced by a **legal-move walk** from the standard start, using
Stockfish's own depth-1 choice with a deterministic variation rule to reach different branches. **No position
is chosen or rejected by eye** — this is the card's own rule (positions vetted by the oracle, never by the
author's judgement).

**2. THE REFERENCE LABEL.** Every candidate is evaluated **twice** at **d18 / the frozen config**. A
candidate whose two evaluations disagree is **DISCARDED** — it is not a fact. The surviving evaluation is
the candidate's **reference value**.

**3. "NEAR THE EDGE" IS DEFINED AS: within ±60 cp of EITHER threshold** — i.e. `|eval + 300| <= 60` or
`|eval + 100| <= 60`.

**Why 60:** it is **the one measured d12→d18 shift** (59 cp on kiwipete), rounded to a round number **before
the draw**. **A position can only be expected to cross if the distance to a threshold is within the
instrument's own measured depth-sensitivity.** Choosing the window after seeing the shift distribution would
be selecting the sample to produce the answer.

**4. THE MEASURE.** Each selected position is evaluated at **d12 / the frozen config** and its **SIDE**
recorded: `LOST`, `GREY`, or `HOLDABLE`. **A CROSSING is a position whose side differs between d12 and
d18.**

**5. THE SECONDARY MEASURE, AND IT GUARDS THE SELECTION.** The same d12 evaluation is taken for **every**
candidate, including those far from the edges, so the report can show **the shift distribution across the
whole set** and not only where crossings were looked for. **If the far-from-edge positions also cross, the
selection is not doing the work and the finding is about the depths. If only the near-edge ones cross, the
finding is about the thresholds. Those are different findings and the test must be able to tell them apart.**

## THE PREDICTION — FALSIFIABLE, RECORDED NOW

> **CROSSINGS AMONG THE AT-RISK SET: at least 1, and a substantial fraction** — because the window is one
> measured shift wide, so a position sitting inside it is inside the instrument's own depth-noise.
>
> **CROSSINGS AMONG THE FAR-FROM-EDGE SET: expect ZERO or near-zero** — because the mechanism identified is
> specifically *near a threshold*, and a position 200 cp from both edges would need a shift four times the
> measured one.
>
> **THE PREDICTION OF "ZERO CROSSINGS OVERALL" IS ALREADY CONTRADICTED** by the 59 cp shift in hand, and is
> not an available answer.

## WHAT EACH OUTCOME MEANS — DECIDED NOW, SO IT CANNOT BE READ AFTER THE FACT

| result | conclusion |
|---|---|
| **crossings > 0, and concentrated at the edges** | **pooling is FORBIDDEN.** The two depths are different instruments at the thresholds, and "carry both, never pool" is permanent and empirically grounded. |
| **crossings > 0, spread across the whole range** | **worse: the depths differ everywhere**, not only at the edges. Pooling forbidden, and the 200 cp band is too narrow for a depth change of this size. |
| **crossings = 0 over a genuinely at-risk set** | **a common depth becomes AVAILABLE** — and the at-risk set's composition is then the thing to scrutinise, per Chilly's point. |
| **the at-risk set is EMPTY or tiny** | **the test is INCONCLUSIVE and that is itself the finding**: it would mean positions near a threshold are rare, so the risk is small in practice and the rule should be stated as a probability rather than a prohibition. |

## FROZEN

**This rule is fixed at this commit.** Any change after the first position is evaluated **is a new test, not
a revision to this one.**
