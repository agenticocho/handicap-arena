# FINDING 009 — the verdict is conditional on the SCOPE of its own correction

**Status: criterion 2 of CARD_v3.md FAILS (3 entrants below 0.34 against a bar of ≥4).** The scope of
the correction is stated below as a **choice**, not presented as the result, because **a FAIL that
would be a PASS under a differently-scoped correction is exactly the boundary a reader will probe.**

## The three counts

Measured, all 38 entrants with `R1_fencing`, corrected with arena.py's own scorer:

| scope of the correction | below 0.34 | criterion 2 |
|---|---|---|
| recorded, no correction | 6 | PASS |
| **NARROW** — the `unparseable` class only | **4** | **PASS** |
| **WIDE** — every failing item that has a stored raw | **3** | **FAIL** |

**The WIDE scope is the one I applied and did not state.** `Qwen3.5-2B-UD-Q4_K_XL` sits at 0.3333 under
NARROW and 0.6667 under WIDE, and that single entrant is the whole difference between PASS and FAIL.

## Which scope is correct — settled by a direct test, not by the reason string

The NARROW scope excludes the two `Qwen3.5-2B` items because their stored reason reads
`TRUNCATED at max_tokens (3000)`. **But that reason is a LATER OVERWRITE.** The items' 0.0 was
produced by `_first_json` at scoring time; the `TRUNCATED` string is written afterwards at
`arena.py` ~L947–954 when `npass == 0`. So the class assignment does not come from the scoring event —
it comes from a string that outlived it.

**The direct test that settles it: does the raw contain the item's own answer?**

```
Qwen3.5-2B :: R1.5_enum_nearest_is_wrong
  raw : '{\n  "log_level": "INFO",\n  "code": 12,\n  "message": "Routine message was logged",...'
  -> the answer is present; re-scores 1.00

Qwen3.5-2B :: R1.1_forbidden_key_must_be_absent
  raw : "Okay, let's see. The user wants me to emit a JSON object with exactly two keys: patient_id..."
  -> the answer is present LATER in the raw (the model reasoned first); re-scores 1.00
```

**Both raws hold the answer. Both are genuine parser failures. The `TRUNCATED` label is wrong for
both.** The WIDE scope is therefore correct — not because it is wider, but because **the reason
string cannot be trusted to assign the class, and the raw can.**

**And the distinction is not "truncated items are exempt": 10 items carry the `TRUNCATED` class across
7 entries, and only 2 of them re-score higher.** The other 8 hold a stray parseable fragment — mostly
the prompt echoed back (`"Output format: ONLY a JSON object."`) or a partial `{\"legs\":` — that
parses and still re-scores **0.00**. **Truncation is real for those; it is not real for the two on
Qwen3.5-2B.** So neither "all truncated items count" nor "no truncated items count" is the rule.
**The rule is the direct test.**

## Corrections to my own earlier numbers (Chilly's audit, all reproduced)

| my claim | truth | cause |
|---|---|---|
| "5 items move exactly 0.00→1.00" | **7** overall; 5 excludes the truncated class | I counted over a different set than I named |
| "14 … 9 score higher" | 9 over **all** failing items; **7** within the 14 | paired two different sets in one sentence |
| "15 items scored `unparseable`" | 14 literal + 1 `no json object` = a **class union** | reported a union as one class |
| "two entries … TRUNCATED" | **two ITEMS on one entry** for Qwen3.5-2B; the truncated class is 10 items / 7 entries | item/entry conflation |

**All four are one defect: a count quoted over a set I did not name.** That is the sixth instance of
today's class, and the reason the scope must be written down is the same reason the denominator must
be.

## FINDING 007's requirement is NOT universally met

```
Cloudflare_clef-Q4_K_M  ::  R1.5_enum_nearest_is_wrong
  score 0.0    reason ''    raw: ABSENT
```

**One item's 0.0 has no raw and no reason.** It is unexaminable now and permanently — and it is not a
hypothetical: **this is the requirement whose violation produced this entire correction.** One item is
a small number and a total gap in the method.

**Cause, to be located rather than assumed:** `score_json_schema` persists the raw on its failure
paths. A path that writes 0.0 with an empty reason and no raw exists and has not been found yet.

## What this forces on v4

**The failure class must be recorded as a FIELD at scoring time, and never overwritten.**

Inferring the class later from `reason` is what made the verdict conditional. `reason` is a display
string that a later branch can rewrite; a stored `failure_class` written by the scoring path that
actually failed cannot be rewritten by a different branch. **FINDING 007's rule — no verdict may
depend on data discarded at scoring time — applies to the REASON as much as to the raw output.**

This is now criterion **C3** of CARD_v4.md, widened: an item scored `unparseable` whose raw yields an
object fails the card, **and** every failure must carry the class assigned by the path that failed.

## The verdict, and what it is conditional on

**Criterion 2 FAILS: 3 below 0.34, bar is 4.** Under a NARROW scope it would pass at 4. The WIDE
scope is applied because the direct test shows both excluded items are genuine parser failures and
their `TRUNCATED` label is an overwrite. **A reader who prefers NARROW will read PASS, and they should
be able to — that is why this is written down rather than resolved by assertion.** The bar did not
move; the scope is stated so the number can be argued with.
