# CARD v2 — design, and the criterion frozen BEFORE the run

**Status:** designed, not yet run. **v1 evidence stays valid and stays labelled v1.**
**Author:** Ocho (CFO) · 2026-10-07

---

## 1. What the v1 field actually measured

42 graded models. Belt distribution White 4 · Yellow 4 · Orange 12 · **Green 22**.

    R1_fencing    29/42 at 3/3   (70.6%)   SATURATED
    R2_chess      36/42 at 3/3   (85.7%)   SATURATED
    R3_pitstop    26/42 at 3/3   (65.1%)   SATURATED

    win distribution across the whole field:  0/3 -> 32   1/3 -> 0   2/3 -> 3   3/3 -> 91

**Almost nothing lands between zero and full marks.** That is the defect, and it is not primarily
that the tasks are easy.

## 2. The structural cause

Each round runs **three trials of the same prompt at `temperature: 0.0`**. At temperature zero a
model's output is deterministic, so the three trials are **three copies of one measurement**. The
trial count contributes no information; a round is effectively a single binary question.

42 models × 3 binary questions = **8 possible outcomes**, and the field landed in a handful of
them. Bimodality is not a property of the models; it is a property of the instrument.

I hypothesised R1 fencing was the capping round. **The data says otherwise** — of the ten models
stuck at 6/9, six zeroed R3 pitstop and only three zeroed R1. Recording the wrong hypothesis and
its refutation, because the refutation is the useful part.

## 3. The fix: a battery, not a repetition

Each round becomes **6 distinct items**, one trial each, at temperature 0.0. The round score is
**items passed / 6** — 7 levels instead of 2. The aggregate stays the mean of the three rounds,
so it gains 19 distinguishable values where it had ~4.

The items are built on **near-miss families** (GAMES.md League I / I3): each targets a
surface-form shortcut that a model can take instead of solving the problem.

| round | item | the near-miss it targets |
|---|---|---|
| R1 fencing | 6 structured-output items | field-name near-misses, enum exactness, nested types, per-item partial credit |
| R2 chess | 6 tool-selection items | near-duplicate tools, a constraint-violating option, **a case where no tool is correct**, unit transformation, genuine ambiguity |
| R3 pitstop | 6 code-repair items | fix-must-not-break-others, silent mutation, empty input, **the bug is in the caller**, **the code is already correct** |

Two items exist specifically to punish the "always produce something" reflex: **no tool is
correct** and **change nothing**. A model that always answers fails both. Those are the two most
informative items in the set.

**Partial credit** applies inside R1 items (fraction of required fields correct) so that a
near-miss scores above a blank.

## 4. Instrument changes

- `card_version: 2` recorded in **every bundle**. v1 bundles keep saying 1. **They are never
  silently mixed** — a v2 score and a v1 score are different measurements, and the same rule as
  server_flags applies: if it changes the outcome, it belongs in the record.
- **Truncation is classified, not scored.** A trial that stops on the token cap is recorded as
  `truncated` and excluded from the item total with the item marked `unscored` — so "ran out of
  room" can never be read as "answered wrongly" (FINDING 001's family, one level down).
- `run_card.py` gains a `--card v2` path; the skip check keys on card version too, so a v2 run
  cannot be mistaken for an already-done v1 model.

## 5. SUCCESS CRITERION — frozen here, before the run

The v2 field passes only if **all four** hold. Stated in advance because a criterion chosen after
seeing the results is not a criterion.

1. **Saturation falls**: Green drops from 22/42 (**52%**) to **under 25%**.
2. **The gradient exists**: the aggregate takes **at least 6 distinct values** across the field
   (v1 had 4), and **no single value holds more than 40%** of the field (v1's top value held 50%).
3. **The zero-side survives**: at least **4 models** still score below 0.34. A card that
   discriminates only by making everything hard is a different failure.
4. **The trap items bite**: **at least 3 models** fail the *no-tool-is-correct* item and **at
   least 3** fail the *already-correct* item. If nobody fails them, the traps are not traps and
   League I needs rethinking rather than more items.

**If criterion 4 fails while 1–3 pass**, the honest reading is that the hardening worked by
difficulty rather than by discrimination — and that gets reported as such, not buried.

## 6. Cost

6 items × 3 rounds = 18 calls per model, one trial each, versus 9 today. Roughly double the wall
clock: the v1 field took 167.6 minutes, so expect **5–6 hours**, run in the background,
resumable, smallest model first so results land progressively.
