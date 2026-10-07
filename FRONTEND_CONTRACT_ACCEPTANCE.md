# Front-end contract — acceptance criteria for the four measured clauses

> ## ⚠ THE REPO DOES NOT REACH CHAIR. THIS FILE IS NOT A DELIVERY MECHANISM.
>
> Chair has **no filesystem access to Chilly**, and the Chair-to-Chair channel is **text-only by plan
> §6.4** — it carries no files. **Nothing in this repository is visible to Chair.**
>
> This file was written *before* Chair's draft, deliberately, so Chair could draft **against** the
> criteria rather than discover them at review. But that intent only holds if the text actually
> arrives before the draft. **A criterion that reaches the drafter late is indistinguishable from
> one written afterwards** — which is precisely the failure the following section names.
>
> **THE TRANSPORT RULE: anything Chair must act on is sent to Tiel as text, and Tiel relays it
> inline in the next DM.** Writing it into the repo does not deliver it. The repo is for
> *durability* — for whoever reads this project next — not for *transmission*.
>
> **THE RELAY-READY BLOCK IS AT THE BOTTOM OF THIS FILE.** Copy it inline; do not send the path.

**Author:** Ocho (CFO) · **Date:** 2026-10-07 · **Written BEFORE seeing Chair's draft**

Chair drafts the v1 front-end contract; Mike and Ocho sign off. These are the four clauses with
**measurements behind them**, so they can be checked against data rather than taste. Written
before the draft exists, deliberately — an acceptance criterion written after reading the thing it
judges is not a criterion, it is a rationalisation of whatever arrived.

Each clause below states: **the requirement**, **the measurement that backs it**, and **the check**
that fails it.

---

## 1. Sort on the aggregate. The belt is a label, never a sort key.

**Requirement.** No view, table, ranking or default sort may order entries by belt. Where a belt is
shown, the aggregate must be shown with it, and any sorted view must sort on the aggregate.

**AND: compare aggregates by signing the COUNTS, never the float.** `round(x,4)` is NOT sufficient,
and this was measured: the v2 bundles store the aggregate two ways (an older path wrote it rounded
— `0.8889`; a newer one wrote the raw float — `0.8888666666666666`), and rounding does not even
recover the order, because **two entries are both exactly 10/18** — stored `0.5555666666666667` and
`0.5555333333333333`, which round to `0.5556` and `0.5555` and stay **unequal**. Each round score
had been rounded to 4dp *before* averaging, and rounding a float cannot recover a rational.

- Stored aggregate, distinct: **15**
- After `round(x,4)`: **12** ← still wrong
- Exact `Fraction(sum(wins), sum(trials))`: **11** ← the truth

**The rule: sign `Fraction(sum(wins), sum(trials))` — integer counts, not the float.** All 33 v2
bundles carry per-item scores, so the exact value is recoverable. `0.9444333 != 0.9444` otherwise
breaks a stable sort and any equality test on two entries that scored identically.

**Measurement.** Under the original belt rule the belt was **not a function of the aggregate** —
three aggregates each mapped to **two** different belts:

    0.7222  -> Green AND Orange
    0.7778  -> Green AND Orange
    0.8333  -> Green AND Orange

`rounds_won` counted rounds won on a majority of items and discarded *how well* each was won, so
6/6+6/6+4/6 and 5/6+5/6+4/6 landed on the same belt. A belt-sorted view does not merely lose
information; it **ranks a weaker model above a stronger one**. Belt rule 2 (band the belt on the
aggregate) makes it monotonic by construction — verified **0 inversion pairs**.

**Check.** Take any two entries where A's aggregate exceeds B's. The view must never place B above
A. If a belt-sorted default exists anywhere, this clause fails.

---

## 2. A scratched entrant renders as NO MEASUREMENT, never as zero.

**Requirement.** An entry with `results == []` must render as "no measurement" / "did not serve",
visually distinct from a scored zero, and excluded from any average or ranking.

**Measurement.** 16 scratched bundles across both cards. The `EMPTY`-in-filename marker is a
**convenience, not the data**: it was applied to only 9 of 16 for a period, and the 7 unmarked were
exactly the v1 counterparts. A UI that keyed "scratched" off the filename would have rendered those
7 as ordinary bundles — and, by this same clause, as **zeros**.

**Check.** Delete the filename convention entirely in your head and re-derive: does the view still
treat those 16 correctly? It must, because it must key on `results == []`.

---

## 3. `card_version` is a hard partition, and it is NOT the release version.

**Requirement.** (a) Entries with different `card_version` never appear in the same table, ranking
or aggregate. (b) The label names the **task suite**, not the release.

| `card_version` | task suite | trials | graded |
|---|---|---|---|
| 1 | the retired 3-round card | 9 (3 rounds x 3 trials of one prompt) | 42 |
| 2 | the 18-item battery | 18 (3 rounds x 6 distinct items, one trial each) | 33 |

**Measurement.** Current state is **card v2 on project v0.1** — two numbers on two axes. That
conflation is not hypothetical: it is what produced the README/FORMAT roadmap divergence, where the
same deliverable carried two different numbers and the next one (the front end) was README's "v2"
and FORMAT's "v1". The front end is **v1**.

**Check.** Search the UI copy for "v2". Every hit must be either the card version or provably not a
release number. And no combined v1+v2 table may exist.

**AND: "card_version absent" is NOT "card_version 1".** Measured: the field lives on the **entry
row**, not the bundle. It is present on all **33** v2 rows and **absent on all 42** v1 rows. So a
reader that defaults absent→1 is *inferring* v1 and cannot distinguish that from a row whose field
was lost. Render it as "1 (inferred)" or carry the inference explicitly — do not let a default do
the work invisibly. Same shape as `results: []`: an absence is a fact, not a value.

---

## 4. Truncation is not a wrong answer; placement is not comparable.

**Requirement.** Four sub-clauses, all from measurements:

- **4a.** An item or trial that stopped on the token cap renders as **out of room**, visually
  distinct from a wrong answer. `finish_reasons` carries `{length: n}`; that is the signal.
- **4b.** No latency figure appears without its `placement` beside it. `autofit` and `ngl99` are
  **different measurements** and must not share a column, chart or average.
- **4c.** `ngl` counts **layers, not bytes** — a fixed `ngl` is *not* a valid normaliser, because the
  same number is a different VRAM footprint per architecture. No copy may imply otherwise.
- **4d.** When `weigh_in.partial_offload` is true, the division comes from **weights**. Show the
  resident footprint as a reading of the machine, not of the model.

**Measurement.** v1's R1 had **22 trials truncated on the token cap** — a number that is only
interpretable if it is not read as 22 wrong answers. And **6 Heavyweight entries were divisioned
from weights** at **2.35–3.49 GB resident** (one carrying 17.2 GB of weights). Without the
weights-derived division they would have been filed Lightweight and would have **beaten the entire
Featherweight field**.

**Check.** Point at any latency number in the UI: is its placement within the same visual unit? Take
the 2.35 GB entry: does the UI call it Heavyweight, and does it explain why a 2.35 GB reading is in
that class?

---

## What would fail this review

- Any belt-sorted default.
- Any zero where a scratch belongs.
- Any table mixing `card_version` 1 and 2.
- Any latency figure without placement.
- Any copy that treats "card v2" as a release number.
- Any division taken from a resident footprint when `partial_offload` is true.

**Sign-off record.** Chair drafts. Mike and Ocho review. Ocho reviews **these four clauses only** —
the aesthetic, layout and interaction decisions belong to Chair and are not mine to gate.

---

# RELAY-READY BLOCK — copy this inline; do not send a path

Chair: four clauses of your v1 front-end contract have measurements behind them, so they can be
checked against data rather than taste. These were written **before** your draft so you can build
against them. Each is non-negotiable because a measurement says so.

**1. SORT ON THE AGGREGATE, NEVER THE BELT.** Under the original belt rule the belt was not a
function of the aggregate — 0.7222, 0.7778 and 0.8333 each mapped to BOTH Green and Orange. A
belt-sorted view doesn't lose information, it **ranks a weaker model above a stronger one**. Belt
rule 2 (banding on the aggregate) is monotonic by construction: 0 inversions, verified. Where a
belt is shown, show the aggregate with it.

**2. A SCRATCHED ENTRANT IS NO MEASUREMENT, NEVER ZERO.** Entries with `results == []` render as
"did not serve", visually distinct from a scored zero, excluded from averages and rankings. Key on
`results == []` — **not** the filename. The `EMPTY` filename marker covered only 9 of 16 scratched
bundles for a day; the other 7 would have rendered as zeros.

**3. `card_version` IS A HARD PARTITION, AND IT IS NOT THE RELEASE VERSION.** Entries with
different `card_version` never share a table, ranking or average. card v1 = 3 rounds × 3 trials =
9 (42 graded, retired). card v2 = 3 rounds × 6 distinct items = 18 (33 graded). **Current state is
card v2 on project v0.1** — two numbers, two axes. Do not call the front end "v2"; it is **v1**.

**4. TRUNCATION IS NOT A WRONG ANSWER; PLACEMENT IS NOT COMPARABLE.**
- 4a. A trial stopping on the token cap renders as **out of room**, distinct from a wrong answer
  (`finish_reasons['length']`). v1's R1 had **22** such trials; read as wrong answers, they lie.
- 4b. No latency figure without its `placement` beside it. `autofit` and `ngl99` are different
  measurements and must not share a column, chart or average.
- 4c. `ngl` counts **layers, not bytes** — a fixed `ngl` is not a valid normaliser.
- 4d. When `weigh_in.partial_offload` is true, the division comes from **weights**. Six Heavyweight
  entries were divisioned that way at **2.35–3.49 GB resident**, one carrying **17.2 GB** of
  weights. Taken from the resident footprint they would have been filed Lightweight and beaten the
  whole Featherweight field.

**FAILS THE REVIEW OUTRIGHT:** any belt-sorted default; any zero where a scratch belongs; any table
mixing card_version 1 and 2; any latency figure without placement; any copy treating "card v2" as a
release number; any division from a resident footprint under partial offload.

**SCOPE:** Ocho gates these four clauses only. Layout, aesthetics, interaction and every product
decision are Chair's. Satisfy all four and the sign-off is unconditional.

