# LIGHTS OUT — measured results, 2026-10-22

The resident `prism-bonsai-9b` (Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0) played Lights Out on two
rungs of the ladder. This file carries the numbers and the caveats that constrain them, so the
result can be cited from the repository rather than reconstructed from correspondence.

Both arms ran on the **already-resident** seat at `127.0.0.1:58595`, ctx 65536, temperature 0.0,
`enable_thinking: false`. **No lease was taken and no tenant was evicted** in either arm.

---

## Rung 4×4 — 30 attempts, one answer

Ten boards (5 solvable, 5 unsolvable) × three passes. Directive format, 256 tokens.

| measure | value |
|---|---|
| rows | 30 |
| distinct answers | **1** — `PRESSES: NONE / CLAIM: UNSOLVABLE`, 30 of 30 |
| answer blocks present | 30 of 30 |
| completion tokens | 12 on every row |
| median wall time | 1.8 s (52 s total) |
| boards solved | **0** |
| verdicts | CORRECT_UNSOLVABLE 15, FALSE_UNSOLVABLE 15 |

**The model answers every board, solvable or not, with the same two lines.** The 15
`CORRECT_UNSOLVABLE` are worth nothing as evidence of discrimination: on a sample split 15/15, a
constant scores exactly the base rate by construction. Report the two cells separately and never
the 50%; the honest summary is **0 boards solved, one constant emitted**.

## Rung 2×2 — 16 attempts, three answers

All 16 boards, which on 2×2 is the entire state space. State scoring: correct iff the presses
actually reach all-off. Same directive format, 256 tokens.

| measure | value |
|---|---|
| rows | 16 |
| distinct answers | 3 |
| completion tokens | 10 (×3), 12 (×10), 20 (×3) |
| median wall time | 1.6 s (28 s total) |
| CORRECT | **1** — the all-off board, whose answer is "press nothing" |
| FALSE_SUCCESS | 5 |
| FALSE_UNSOLVABLE | 10 |

The three answers:

```
x10  PRESSES: NONE              CLAIM: UNSOLVABLE     10 boards (false: every 2x2 board is solvable)
x3   PRESSES: NONE              CLAIM: SOLVED         all-off board (correct) + 2 lit boards (false)
x3   PRESSES: A1, B1, C1, D1    CLAIM: SOLVED         3 boards (false, and see below)
```

**`C1` and `D1` do not exist on a 2×2 board.** The third answer names cells from the 4×4 grid, so
the model is not reading the grid it was given: the board size never reaches its output. That is a
stronger statement than "it scores 6.25%" — it is emitting a memorised 4×4-shaped response to a 2×2
input, and its one success is the degenerate board where the correct action is nothing.

## Rung 3×3 — the fixture exists; the arm is NOT RUN

`3x3_fixture_16_boards_20261022.{md,json}` (sha256 `2c18e257afe3d066` / `851976c57068bca9`)
pre-registers 16 boards as the images of 16 press strings with `x = 0` excluded, so the all-off
board is **absent by construction**. Verified independently twice at the time of writing:
3×3 has rank 9, nullity 0, every one of the 512 boards solvable with exactly one solution, and
every one of the 512 possible constants scores exactly **one** board of the space.

That last fact is why the exclusion matters: rank 0 does not buy a zero floor — a bijective press
map guarantees one winning board per constant. Over this 16-board sample a constant is worth 1/16
if its board is in the set and 0/16 otherwise; "press nothing" scores 0/16 by construction.

`arm1_3x3.py` is staged and dry-run clean. It permits derivation (no answer contract), which is the
one variable that separates *cannot compute* from *will not compute*. **It has not run** — it needs
an operator authorisation for ~25 minutes, and no peer letter supplies one.

---

## Caveats that constrain every number above

1. **The 88 s / no-answer-block reading was a prompt defect, not a model fact.** With the stock
   prompt and no output contract, the model writes a derivation as *content* and consumes the whole
   budget at this seat's ~11.6 tok/s CPU: 23.4 s for 256 tokens, 88.0 s for 1024, no answer block in
   either. With one line demanding the two-line answer it replies in 1.6 s and 12 tokens. Three
   earlier descriptions of this model as "fails by not finishing" were descriptions of the prompt.
2. **`reasoning_chars = 0` is a request setting, not a finding.** `enable_thinking: false` plus a
   prompt that says, verbatim, "No derivation, no working, no explanation" manufactures the absence.
   It must not be reported as evidence that the model did not reason.
3. **Uniform trace length was never measured.** An earlier report claimed "12 completion tokens each";
   the histogram is `{10:3, 12:10, 20:3}`. Any argument resting on constant trace length is withdrawn.
4. **A parser that drops what it cannot parse shortens a defect into a plausible answer.** The first
   2×2 parse silently discarded `C1`/`D1`, turning "answered about a different board" into "answered
   about this board and got it wrong". Out-of-range cells are now recorded and flagged.
5. **Prose-derived claims were removed from the scorer.** A block that inferred `CLAIM` from any line
   containing `solv|impossible` plus a cell token produced rows carrying a claim whose own stored raw
   contained no such token. A claim now comes only from an explicit `CLAIM:` line.

## Files

```
results_v3.jsonl          30 rows, 4x4 directive arm
results_rung1_2x2.jsonl   16 rows, 2x2 state-scored arm
results_rung1_2x2.jsonl -> artifacts/rung1-20261022/   (hash-verified copy, out of the 24h scratch)
3x3_fixture_16_boards_20261022.{md,json}
arm1_3x3.py               staged, dry-run clean, NOT run
```

Every row carries `max_tokens`, `completion_tokens`, `finish_reason`, `answer_block`, `parse_path`,
`out_of_range`, `raw` and the computed truth, so a row can be checked against the text that travels
with it.
