# FINDING 006 — the v2 card's fix worked on R2 and R3; R1 is the round that resisted

**Date:** 2026-10-07 · **Instrument:** `analyse_card.py`, now partitioned by `card_version`
**Status:** measured, not inferred — and it corrects the plan I had for card v3

## What was being asked

Nothing in v2 could be answered per-round until `analyse_card.py` stopped pooling the cards. It
was written for v1, assumed 3 items per round, and now that both cards' bundles coexist it printed
a win rate of **118.7%** for R1. That number is what forced the investigation.

## The measurement

Run partitioned by `card_version`, each round against its own denominator:

| round | card v1 (3 items) | verdict | card v2 (6 items) | verdict |
|---|---|---|---|---|
| R1 fencing | 70.6% | SATURATED | **89.9%** | **SATURATED** |
| R2 chess | 85.7% | SATURATED | **61.6%** | **discriminates** |
| R3 pitstop | 65.1% | SATURATED | **75.8%** | **discriminates** |

Aggregate spread: v1 had **6 distinct values across 42 entries**, 21 of them at exactly 1.0000
(**50%**). v2 has **12 distinct values across 33**, the largest bucket being 6 entries
(**18%**). No value exceeds 40%.

## Three conclusions

**1. R2 and R3 were fixed by the right mechanism, and it is visible.** R2 went 85.7% → 61.6% by
replacing three trials of one prompt with six *distinct* items — 28 of 33 entries land on partial
credit rather than either extreme. That is a round that measures instead of sorts.

**2. R1 did not just resist — it got WORSE.** 70.6% → **89.9%**, with 26 of 33 entries scoring
6/6. R1 is now the single saturated round in the card, and it is the one whose items are JSON
schema extraction: the most mechanical of the three, and the one a model either can or cannot do.

**3. Therefore card v3's target is R1, not "the item mix" in general.** The plan I had —
*"drop a floor item, add a harder near-miss"* — was written from the v2 pilot, before any per-round
measurement existed. It is now superseded by a measurement: **two of three criteria are met and
R1 is the entire remaining problem.**

## Criterion status, now that all four are measurable

| # | criterion (frozen before the run) | status |
|---|---|---|
| 1 | Green under 25% | **FAILED** — 57.6% pre-Rule-2, 24.2% post. The bar does not move. |
| 2 | ≥6 distinct aggregate values, none >40% | **PASSES** — 12 distinct, max 18% |
| 3 | ≥4 models below 0.34 | **FAILED** — three floor items lifted the bottom |
| 4 | ≥3 models fail each trap item | **not yet measured** |

## And the part that is about the instrument, not the card

My first diagnosis of the 118.7% was **"pooling two cards"** — and it was **wrong**. Pooling the
cards measures **82.4%**, which is under 100%. The real cause was a **hardcoded denominator**: the
line was `sum(k*v) / (3*n)`, wins divided by 3, applied to v2 rounds carrying 6 items.

The corollary matters more than the bug: **my first guard tested `rate > 100%` and would not have
caught the defect it was written for.** A guard that cannot fail on its own bug is decoration —
it makes a run *look* verified. It is now replaced by the invariant that actually holds — **one
items-per-round within a card, asserted** — verified by feeding it a deliberately mixed table,
which it refuses.

This is the fourth time in two days that the same shape has appeared: **a check answering a
different question than the one asked.** The difference here is only that it was mine, in the tool
I had just written to fix an earlier instance of it.
