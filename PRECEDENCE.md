# PRECEDENCE — when two records of the same event disagree, which one wins

**Declared now, while every answer is still unknown.** Chilly's rule, and the reason this file exists:

> A gap closes when you look. A contradiction does not close by looking at all — both records exist, both are
> well-formed, and one has to be declared authoritative. **Precedence has to be established while the answer
> is still unknown, or the choice gets made by whoever is holding the result.**

Every row below came from a contradiction found in this repo. Each one was settled in the moment it was
found, by whoever was nearest it. That is the wrong way to settle them: **the rule is written before the
instance, or the instance sets the rule.**

---

## The table

| when these two disagree | the winner | why |
|---|---|---|
| **a bundle's contents vs its filename label** | **the contents** | the label is a *rename* applied afterwards — in this repo it has already contradicted the contents, in 18 cases where `_EMPTY_` sat on a file whose log line said `scored=True` |
| **`wins`/`trials` vs `aggregate`** | **the primitives** | the aggregate is stored **rounded to 4dp**; 15 of 29 v4 values differ from the ratio they stand for. A display is not a record. |
| **a failure class written by the failing path vs the `reason` string** | **the field written by the path that failed** | `reason` can be overwritten by a later branch — measured: a later branch rewrote it to `TRUNCATED` when `npass == 0`, which is how a verdict became conditional on the scope of its own correction |
| **an item's slot name vs the item** | **`<card>:<slot> <name>`** | a slot survives a card change and loses its referent: `v3:R1.6 array_exact_and_ordered` (39.5%) and `v4:R1.6 exact_scalar_types` (96.6%) are unrelated items sharing a label |
| **the run log vs the artifact** | **the artifact** | the log is discarded relative to it, and it is **append-only across runs with colliding stems**, so a line naming a stem may belong to a different run. It cannot assign provenance. |
| **the model's raw output vs an extractor's reading of it** | **the raw** | an extraction is a claim *about* the output; the greedy `{.*}` was wrong on 14 of 15 failing raws, and the only reason it was detectable is that the raw survived |

**And when the disagreement is a MISSING record** — no log line, no raw, no field at all — the winner is
**nothing**: silence is not evidence for either side. That is not a row in the table, it is the absence of
one, and it is why an unexercised claim is a claim with no carrier.

---

## The three principles underneath

**1. Prefer the PRIMITIVE to the rendering.** `wins`/`trials`; the raw; the contents.

**2. Prefer the WRITER to the summariser.** The path that failed over the string a later branch wrote; the
run that wrote the file over a log written by many runs.

**3. Prefer the CARRIER to the claim.** A record in the artifact beats a statement about it — including a
statement in a message, including this file.

---

## What this file is NOT

**It is not a licence to ignore the loser.** Every loser in this table is still evidence, and two of them
were *right* about something: the log was right that a `scored=True` run happened — just not the one that
left the file. The filename was right that a run renamed it — just not that the rename's reason still held.

**A contradiction is a signal that one of the two records is about a different event.** The table says which
one to trust for the event in hand; it does not say the other is noise.

---

## The test before adding a row

**Can a reader recompute the winner from what is in the record?** If yes, the row is safe. If no — if
choosing the winner requires something that is not in the artifact — then neither record is sufficient and
the answer is a new field, not a new row.
