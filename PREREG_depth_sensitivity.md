# PRE-REGISTRATION — THE DEPTH SENSITIVITY TEST (test 2)

**Supersedes `PREREG_depth_test.md`.** That one's SOURCE is refuted (a legal-move walk reached no LOST
position), so this is **a new test with a new source, not a re-run.** Written and committed before any
position is drawn.

---

## WHAT THIS TEST IS FOR — REFRAMED, AND THE REFRAME IS THE POINT

**NOT to license a common depth.** That decision is already closed: each card's threshold was derived
against its own depth, so a common depth would require re-deriving a criterion on both sides. **A test
cannot rescue a decision already shown to be undesirable — and running it for that purpose would be a test
with no admissible outcome.**

**IT IS TO QUANTIFY THE INSTRUMENT'S SENSITIVITY, so the record can state its own dependence:**

> **"These verdicts are depth-relative. Moving the depth from 18 to 12 moves a decisive position's
> evaluation by a median of X cp and flips the band on Y% of decisive positions."**

**That sentence is the deliverable.** It is what a reader of the card needs, and it is what makes *carry
both, never pool* a documented posture rather than an awkwardness.

**AND THE FIRST PASS ALREADY SUGGESTS THE ANSWER IS UNCOMFORTABLE:** shifts min −135, **median +52**,
max +646 cp, against a **200 cp** band. **That is not a sensitivity — that is a sensitivity that swamps the
instrument**, and it is worth saying so with a decisive sample behind it rather than an at-risk set of 3.

## THE FROZEN CONFIG — IDENTICAL AT BOTH DEPTHS

```
engine      Stockfish 19, linux-x86-64-universal, sf_19
config      Threads=1   Hash=64   MultiPV=1
depths      d18 and d12 -- THE ONLY FIELD THAT VARIES
box         AMD Ryzen 5 5600, 12 logical CPUs, 60.7 GiB RAM, RTX 3060 Ti / 580.178.04
thresholds  LOST <= -300 ; HOLDABLE >= -100 ; GREY (-300,-100) exclusive
```

**The Hash measurement is why this list exists:** changing one config field moved d18 by **27 cp** and
flipped a monotonicity. **Any field left unpinned is a candidate explanation for whatever this test finds.**

## THE SOURCE — THE PART THAT HAS TO CHANGE

**A legal-move walk CANNOT reach material imbalance**, structurally: random legal play has neither side
pursuing an advantage, so a −300 evaluation essentially never accumulates. **Measured: 30 positions, none
below −198.** The property that makes the walk unbiased makes it useless here.

**THE SOURCE FOR THIS TEST: positions from DECISIVE play** — lines in which one side has converted an
advantage, so both edges of the band are reachable by construction. Concretely: seed from a small set of
known-imbalanced positions and extend with **engine-directed** moves (the engine's own choice, not a random
one) until the evaluation is stably inside the region of interest.

**NO POSITION IS ACCEPTED OR REJECTED BY EYE.** Labelling is by the oracle at the frozen config, twice, with
disagreements discarded — exactly as before.

## THE BOTH-EDGES REQUIREMENT — AND THE ROW THE FIRST TEST LACKED

**The sample MUST reach BOTH edges.** "Near the edge" is `|eval + 300| <= 60` **or** `|eval + 100| <= 60`,
and **the test is only admissible if the at-risk set contains positions near BOTH thresholds.**

> **NEW ROW, and it is the one the first test was missing:**
>
> **A SAMPLE THAT REACHES ONE EDGE AND NOT THE OTHER IS THE SAME DEFECT AS A SAMPLE THAT REACHES
> NEITHER.**
>
> `ONE-EDGED — NOT ADMISSIBLE.` The test reports which edge was reached, reports the shifts it did
> measure, and **states that no conclusion about the unreached edge follows** — in either direction.
> **It does not report a sensitivity for the instrument, because the unreached edge is where the
> instrument's primary failure mode lives** (LOST is where a resignation is scored correct).

**That row exists because the first test failed exactly this way and nothing in its pre-registration could
have caught a partial failure.** Row four caught the TOTAL failure; nothing would have caught the partial
one. **A rule that only names the total failure is a rule with a hole in it.**

## THE MEASURES

**PRIMARY.** For every at-risk position: its **SIDE** at d18 and at d12. A **CROSSING** is a side change.

**SECONDARY.** d12 for **every** candidate, including far-from-edge ones, so the report can distinguish
**"the depths differ everywhere"** from **"the thresholds differ at the edges."** Those are different
findings and the test must be able to tell them apart.

**THE DELIVERABLE NUMBERS.** Median and range of the d12→d18 shift; the crossing count and **rate** among
at-risk positions; and **the band width (200 cp) stated alongside them**, so a reader can see the ratio
rather than only the numbers.

## THE ADMISSIBILITY CHECK — BEFORE ANY CROSSING IS READ

```
at-risk positions near -300  >= 5      FIXED NOW, NOT AFTER SEEING THE SAMPLE
at-risk positions near -100  >= 5      FIXED NOW, NOT AFTER SEEING THE SAMPLE
```

**Five per edge, chosen before the draw, because a rate over fewer than five positions is not a rate.**
The first test had **3 near −100 and 0 near −300** and reported a crossing rate anyway; that is the number
this floor exists to refuse.

**If either count is below 5, the test is `ONE-EDGED` or `INADMISSIBLE`, and the crossing count is NOT
reported as a sensitivity.** **The composition check comes FIRST, because a crossing rate over a one-sided
sample is a property of the sample.**

**AND THE SAMPLE SIZE IS STATED HERE TOO, because the first pre-registration omitted it and I had to
declare it afterwards:** target **≥60 candidates drawn**, so that ≥5 per edge is reachable rather than
hoped for. **If 60 candidates cannot produce 5 per edge, the SOURCE is refuted again and that is the
result** — reported as a source finding, not as a sensitivity.

## THE PREDICTION — FALSIFIABLE, RECORDED NOW

> **Shift median: 40–70 cp** (the first pass gave +52 over 28 positions; the reference figure is 59).
> **Crossing rate among at-risk positions: NON-ZERO, and I expect it to be substantial** — the at-risk
> window is **60 cp** and the median shift is **~52 cp**, so the window is narrower than the typical
> movement. **A crossing rate near zero over a genuinely both-edged sample would refute the mechanism** and
> would mean the band absorbs the shift for a reason I have not identified.
> **Crossings far from the edges: zero or near-zero.**

## FROZEN

**This rule is fixed at this commit.** Any change after the first position is evaluated **is a new test.**
