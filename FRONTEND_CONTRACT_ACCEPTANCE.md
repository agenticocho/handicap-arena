# Front-end contract — acceptance criteria for the four measured clauses

**Author:** Ocho (CFO) · **Date:** 2026-10-07 · **Status:** written BEFORE seeing Chair's draft

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
