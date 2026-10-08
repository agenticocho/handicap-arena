# CARD v4 — the parser fix, and items built like the one that worked

**Card version: v4. Project version: v0.1.** `card_version` is a separate axis from the project line
and is a **hard partition** — a v4 aggregate is never pooled or compared with a v1, v2 or v3 number.

**v4 is not a repair of v3.** v3's criterion 2 **STANDS FAILED** (3 entrants below 0.34 against a bar
of 4) and is not re-scored, relaxed, or explained. v4 is the next version with its own bar, written
before its own run.

---

## Why there is a v4 — the two measured reasons

### 1. The parser was the failure, and it is fixed here

`_first_json` in arena.py parses with a **greedy** `\{.*\}` — first brace to last. A model that
reasons first and emits JSON second is therefore scored `unparseable` when it is not. This was
measured, not suspected, once the raw output was stored in the bundle (FINDING 007 made FINDING 008
possible):

```
15 items scored `unparseable`
14 of those raws contain a JSON object a strict extractor finds
 9 score HIGHER on the arena's own scorer -- five go 0.00 -> 1.00 outright
 2 were recorded "TRUNCATED at max_tokens (3000)" whose raw holds a COMPLETE object
```

**On two entrants the parser accounted for the ENTIRE score.** `LFM2.5-1.2B-Thinking-BF16` was
recorded at **0.0000** and answers at **0.5833**. That is not a rounding correction: it is the
difference between *"this model cannot do the task"* and *"this model does the task inconsistently,"*
which is the most misleading thing a benchmark can say about a model — and it was said about an
entrant that lands mid-field.

**v4 parses strictly**: code fences stripped, then the **first balanced `{...}`** found by depth
tracking with string and escape awareness. The v3 scorer is **left in place** — a scoring-method
change belongs to its own version, and deleting the greedy path would retire the evidence that it
ever existed.

**And the strict parse is not trusted on its own:** v4 stores, **per item**, both the raw the model
produced and the extracted object. FINDING 007's rule, applied to the fix: *no verdict may depend on
data discarded at scoring time* — including the fix's own decisions.

### 2. Four of six items measure nothing — and CORRECTING made it worse

The corrected pass rate per item, over 38 measured entrants:

| item | corrected | verdict |
|---|---|---|
| R1.1 forbidden key must be absent | 89.5% | SATURATED |
| R1.3 type under natural language | 94.7% | SATURATED |
| R1.4 ambiguous nesting | 89.5% | SATURATED |
| R1.5 enum nearest-is-wrong | 86.8% | SATURATED |
| R1.2 null means absent | 60.5% | DISCRIMINATES |
| R1.6 array exact and ordered | 39.5% | **discriminates hardest** |

**Recorded, this read as three saturated of six. Corrected, it is four** — because fixing the
understatement lifted weak entrants too, so items that appeared to spread now saturate. **The
correction made the card look worse, not better**, and that is the honest direction for a fix.

A round whose items all sit at the top measures *"who is good."* All at the bottom measures *"who is
bad."* **Only the middle separates, and criterion 2 was the middle's absence.** v4's item set is
therefore built from the one item that discriminated: **exactness under a hard rule set** (R1.6:
array, exact, ordered — 39.5%), supported by **presence/absence semantics** (R1.2: null is not absent —
60.5%). Both are *conformance* tasks where a near-miss is wrong for a stateable reason, not
*capability* tasks where being nearly right is being right.

---

## The criteria — FROZEN BEFORE THE RUN

These are written now, before v4 has run, and they do not move afterwards. An acceptance criterion
written after reading the thing it judges is not a criterion.

**C1 — the item set discriminates.** At least **4 of 6** items fall in the **15%–85%** corrected
pass-rate band. *(v3 corrected: 2 of 6. FAIL.)*

**C2 — the floor is populated.** At least **5** entrants score below **0.34** aggregate. *(v3
corrected: 3 of 38. FAIL.)*

**C3 — the parser is honest.** For every item scored `unparseable`, its stored raw contains **no**
balanced JSON object. Any item whose raw yields an object must not be scored `unparseable`, and any
item scored `unparseable` must carry the raw that justifies it. **This criterion is a conformance
test, not a capability test** — it measures the instrument, which is where every failure of the last
two days has lived.

**C4 — no pooling, no re-scoring of v3.** v3's criterion 2 stands failed. v4's aggregate is not
comparable to v3's — different item set, different parser. A v4 number quoted beside a v3 number
without both `card_version` and the parser identity is a number with no meaning.

**None of C1–C4 may be softened after the fact.** If v4 fails C1 or C2, the correct response is v5.

---

## What v4 does NOT change

- **The round is still `R1_fencing`**, and the name still carries R1's meaning: near-miss
  discrimination under a hard rule set.
- **The conformance traps stay**: a forbidden key that must be ABSENT (not null), null is not absent,
  and type coercion under natural language (`"three"`→3, `"1 1/2"`→1.5, `"true"`→true, `007` with
  load-bearing leading zeros).
- **`trials` records the item count.** v3's `trials=6.0` for 6 items × 1 trial was correct and the
  driver's `trials=3` line was the driver's own constant — the bundle is the record.
- **The bar is not moved because the author moved the measurement.** No agent self-certifies the gate
  that admits its own work, including when the agent is correcting itself.

---

## Criterion-bearing statement, written last and unedited

If v4's corrected pass rates put at least four items in the middle band and at least five entrants
below 0.34, the card discriminates and the instrument is trustworthy enough to build a league on.
If not, the honest conclusion is not that the models failed — it is that **the item set has not been
shown to measure anything**, which is a statement about the card, not about the field.
