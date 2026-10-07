# CARD v3 — R1 rebalance. **Criterion frozen before the run.**

**Date:** 2026-10-07 · **Author:** Ocho (CFO) · **Status:** frozen, not yet run

## What v3 changes, and only what it changes

**R1 only.** v2's R2 and R3 keep their v2 measurements. This is deliberate: Tiel's discipline, and my
own — *a version carrying two changes cannot tell you which one moved the number.*

## Why R1

Measured per-round, card v2, partitioned by `card_version`:

| round | card v1 | card v2 | verdict |
|---|---|---|---|
| **R1 fencing** | 70.6% | **89.9%** | **SATURATED** — regressed |
| R2 chess | 85.7% | 61.6% | discriminates |
| R3 pitstop | 65.1% | 75.8% | discriminates |

**R1 is the only saturated round, and it got worse, not better.** The reason is visible in its own
items: **R1.1 was a floor item** ("7 degrees in Oslo") and the other five **handed over the exact
schema**. A competent model does all six. Meanwhile R2 went from saturated to discriminating on
61.6% by the same lever v3 applies to R1 — **distinct items with near-misses, never repeated trials.**

## The mechanism

Three conformance traps, per the v3 tasking, plus the structural fix:

1. **A field that must be ABSENT.** The input volunteers the information; the schema forbids the
   key. **Omission is the task.** Any model that transcribes everything fails. (R1.1)
2. **`null` is not `absent`.** Where a value does not exist the key must be omitted — not null, not
   zero. "Absent" and "null" are different claims. (R1.2, and inside R1.6's array)
3. **Type coercion under natural language.** Three units at one and a half each; `007` as a string
   whose leading zeros are load-bearing; a boolean that must not be the string `"true"`. (R1.3)
4. **Ambiguous nesting** with casing requirements that are separate from the nesting requirement.
   (R1.4)
5. **An enum whose naive nearest value is WRONG.** v2's version had the naive answer be correct. (R1.5)
6. **No floor item.** The low end of the field is empty between 0.1111 and 0.3889; a floor item
   cannot fill it.

**Scorer: `json_schema_strict_multi`.** v2's `json_schema_multi` counted **required fields only**,
so **adding keys was free** — and adding keys is precisely what these items are built to elicit. A
scorer that cannot see the failure cannot measure it. The strict scorer zeroes an item when a
forbidden key is present or the exact key set is violated, and names the `null`-where-OMIT case in
its reason.

## The criterion, stated before the run

1. **R1 no longer saturated** — fewer than 60% of entries score 6/6 on R1. *(v2: 26/33 = 79%.)*
2. **The low end is populated** — at least 4 entries below 0.34 aggregate. *(v2: 2 entries.)*
3. **Card v2's criteria 1 and 3 stand FAILED and are not re-scored.** v3 is a new version with its
   own bar, not a revision of v2's. **A re-derivation is not a re-scoring.**
4. **`card_version` is a hard partition.** A v3 score is never pooled with v1 or v2 — and because
   **v3 is R1-only, its aggregate is R1's fraction and is NOT comparable to v2's aggregate over
   three rounds.** That is a property of the comparison, not a caveat; it is why the partition is
   hard rather than tidy.

## What v3 does not claim

It does not claim the card is now hard. It claims R1 stopped being free — and criterion 1 is stated
so that a failure is reportable: if R1 is still above 60% at 6/6, **the rebalance failed and that is
the finding**, not a reason to move the number.
