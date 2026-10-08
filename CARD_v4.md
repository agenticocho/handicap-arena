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

**C3 — the parser is honest, and EVERY failure class is STORED — including failures that never reached
scoring.** For every item scored `unparseable`, its stored raw contains **no** balanced JSON object. Any
item whose raw yields an object must not be scored `unparseable`, and any item scored `unparseable` must
carry the raw that justifies it. **And every failure carries a `failure_class` written by the path that
actually failed** — never inferred afterwards from `reason`, which a later branch can overwrite.
*(FINDING 009: the v3 verdict was conditional on the scope of its own correction precisely because the
class had to be inferred from a reason string that had been overwritten. `Cloudflare_clef :: R1.5` also
stands at 0.0 with no raw and no reason at all.)* **AND WIDENED — this covers PRE-SCORING failures too:**
a bundle whose `results` list is empty never reached a scoring path, so the item-level fix cannot apply
to it and the runner writes the class instead. Chilly measured four of the first 33 v4 bundles shipping
`results: []` with the reason present in the **log** and absent from the **artifact**, and the same four
in v3 — so the version built to fix the class would otherwise have shipped the class one level up.
**This criterion is a conformance test, not a capability test** — it measures the instrument, which is
where every failure of the last two days has lived.

**C4 — no pooling, no re-scoring of v3.** v3's criterion 2 stands failed. v4's aggregate is not
comparable to v3's — different item set, different parser. A v4 number quoted beside a v3 number
without both `card_version` and the parser identity is a number with no meaning.

**AND THE NAMING RULE, which v3→v4 made necessary: an item's canonical citation is `<card>:<slot>
<name>`, never the slot alone.** Every R1 label was rewritten between the two cards and **none refers to
the same item** — `v3:R1.6 array_exact_and_ordered` (39.5%) and `v4:R1.6 exact_scalar_types` (96.6%) are
unrelated, and the worst pair is `v3:R1.5 enum_nearest_is_wrong` (86.8%) against `v4:R1.5
exact_key_set_under_a_bribe` (86.2%): **two unrelated items with near-identical rates, which is exactly
the shape that survives review, because a change is visible and a coincidence is not.**
A slot that survives a change keeps its authority and loses its referent — the same defect as a seat
alias naming a retired model, and as `_EMPTY_` in a filename.

**None of C1–C4 may be softened after the fact.** If v4 fails C1 or C2, the correct response is v5.

---

## TWO FORWARD-ONLY FIXES, AND THEIR STATUS IS **UNEXERCISED**

C3's pre-scoring half (the `failure` record) and the per-item clock (`secs`, `gen_tokens`) are **in
`arena.py` and have no instance on disk.** Measured, not assumed:

```
bundles carrying a failure record      :   0
v4 item records                        : 174
of those carrying secs or gen_tokens   :   0
```

The running v4 process **imported its code before both changes**, and no empty bundle has been produced
since. **So these are statements about the code, not about any artifact, and they must not be presented as
capabilities until a bundle carries them.** Chilly's wording is exact: *unexercised rather than wrong —
and I would not put it in front of a builder as a capability until a bundle carries it.*

**THE EXERCISE, planned rather than assumed.** When the field finishes, run **one entrant** under the
current code and check two things: its item records carry `secs`/`gen_tokens`, and an empty bundle writes
a `failure` record carrying `secs`. **One entrant is enough** — the claim is about whether the writer runs,
not about any model. Running concurrently would contend for VRAM and slow the field, so it waits.

**THE EXACT COMMAND, recorded so it is run rather than improvised:**

```
arena.py --card v4 --model /home/chilly1/moltbook_pipeline/models/LFM2-350M-Extract-Q4_K_M.gguf \
         --trials 1 --out results/EXERCISE_fix2.json
```

**Why this works and what each half exercises:**

- **`run_card.py` has no single-entrant option** — it takes `--card` and nothing else — so the exercise
  goes at `arena.py` directly, which is exactly how `run_card.py` invokes it internally.
- **Fix 2 (the per-item clock) is written by `arena.py`**, so a direct run exercises it fully: the item
  records must carry `secs` and `gen_tokens`.
- **Fix 1 (the `failure` record) is written by `run_card.py`**, so a direct `arena.py` run does **not**
  exercise it — and it does not need to, because **it is already EXERCISED**: six empty bundles under the
  resume run, all six carrying `{class: empty, rc: 0, secs, written_by}`.
- **A small known-good model** (`LFM2-350M-Extract`, a v1 9/9 sweeper) is chosen so the run **completes
  and writes item records** — the failure mode of the tail is emptying at load, and an empty bundle has no
  item records to carry a clock. **The choice of entrant is part of the exercise, not incidental to it.**
- **`--trials 1`** because one trial is enough to prove the writer runs.

**An unexercised claim is a claim with no carrier.**

**STATUS OF THE TWO, MEASURED (resume run `arena-v4b`):**

```
FIX 1  the failure record     EXERCISED -- 6 empty bundles under current code, all 6 carry
                              {class: empty, rc: 0, secs: 19.2/15.9/21.3, written_by: pre-scoring path}
FIX 2  the per-item clock     EXERCISED -- BTL-4-IQ2_XXS (written by the resume process) carries
                              `secs` on ALL 6 item records; every pre-fix bundle carries 0 of 6
```

**BOTH FIXES NOW HAVE CARRIERS, AND FIX 2'S CAME FROM THE FIELD RATHER THAN FROM THE PLANNED EXTRA RUN.**
The pre-registered exercise said *one entrant is enough — the claim is about whether the writer runs, not
about any model.* **The field produced one: `BTL-4-IQ2_XXS` scored under the resume process, so its item
records carry the clock.** The distinction that made it recognisable is the same one that made it
necessary — **the boundary is exactly the process boundary**, and it shows in the data:

```
BTL-4-IQ2_XXS    (resume process)   items=6   carrying secs=6
Qwen3.5-9B       (pre-fix)          items=6   carrying secs=0
Qwythos-9B       (pre-fix)          items=6   carrying secs=0
MiMo-V2.6-9B     (pre-fix)          items=6   carrying secs=0
```

**So the extra run is NOT owed, and the exercise is closed by an artifact instead of by a plan.** The
recorded command remains above because it is still the way to exercise the writer in isolation if a future
change needs it — an exercise is retired by its carrier arriving, not by deleting its instructions.

**AND THE REASON IT WAS WORTH PRE-REGISTERING RATHER THAN ASSUMING:** an exercise whose conditions nobody
checks gets marked done when the CODE ships. This one was checked twice — once when the resume produced no
item records at all (so it read NOT YET), and again when the field produced a scored bundle (so it read
EXERCISED). **Both readings came from the artifact.**

---

## THE POPULATION, STATED BEFORE THE VERDICT RATHER THAN DISCOVERED IN IT

The field will close at roughly **30 measured of 46**, against v3's 38. **A materially thinner field, and
the criteria are computed on it. That has to be stated rather than found.**

**It is acceptable, and the reason is the shape of the missing twelve rather than their number.** They are
**not a random twelve**: they are the **largest entrants**, failing **at load**. The field therefore
systematically excludes the biggest models — **which is not noise, it is the Arena's own thesis measured
on its own field.** `VRAM is the absolute bottleneck for the democratisation of AI`, and the entrants
missing from this card are the evidence for it.

**So the verdict is stated with three parts, and none of them is optional:**

1. **the criteria, computed on the entrants that could run** — C1 and C2 as frozen;
2. **the population, named** — 30 measured of 46, with the twelve identified as serving failures rather
   than capability results;
3. **the direction of the bias** — the exclusions are size-correlated, so the field's measured set is
   biased *toward* models that fit, and a criterion computed on it is **noisier, not wrong.**

**And a thinner field makes C2 harder, not easier** — the floor criterion needs five entrants below 0.34,
and every entrant that fails to load is one that cannot land on the floor. **A serving limit pushes against
the criterion rather than for it, which is the direction that does not need defending.**

---

## THE OOM PROTECTION: THE MECHANISM I DESCRIBED WAS WRONG

I claimed *"oomd kills the largest cgroup that is above its limit"*. **That is not what the documentation
says, and I asserted it without reading them** — the day's own class, in a resource decision.

The documented form is a purpose-built property:

```
ManagedOOMPreference=none|avoid|omit
    Allows deprioritizing or omitting this unit's cgroup as a candidate
    when systemd-oomd needs to act.
```

**That removes the unit from the candidate set rather than leaving it under a number — strictly stronger
than a ceiling above the peak.** Caveats, all of which hold here: it needs xattr support; for **swap**
candidates oomd respects it only for root-owned cgroups; for **memory-pressure** candidates it is respected
when the cgroup owner matches the monitored ancestor — **which holds, since this is a user unit under the
same user slice** — and the trigger was pressure, not swap (swap peak 26.3M).

**So the next launch carries `ManagedOOMPreference=omit` as well as the ceiling.** The three lines are not
alternatives: the ceiling bounds the box, and the property excludes the arena from selection.

**An unexercised claim is a claim with no carrier.**

---

## AND WHAT THE THREE RECORDS OF ONE EVENT CAN EACH DO

Chilly's finding, and the distinction is one we had not drawn:

| record | says | can it assign provenance? |
|---|---|---|
| the bundle's contents | `results: []` | **right, every time** |
| the filename's label | `_EMPTY_` | **contradicts the log in 18 cases** |
| the run log | `scored=True` | **cannot distinguish two runs** |

**Earlier findings were labels with NOTHING behind them. These are labels with a DIFFERENT fact behind
them. A gap invites a check; a contradiction invites a choice.** And the general rule: **a record that
cannot distinguish its own cases is not a weaker source for provenance — it is not a source.**

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
