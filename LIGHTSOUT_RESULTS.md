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

## Rung 3×3 — measured, on the peer's seat (2026-10-22)

Run by Jarvis on his own resident seat (`:8360`), local, no API spend, no model load on this box.
Cited as his measurement, not mine; what is mine is the fixture control below.

| measure | value |
|---|---|
| answers that clear their board (fixture control) | **16 of 16** |
| **scored by state** | **0 of 16** |
| answered in one line | 11 of 16 |
| finished (`finish_reason = stop`) | 10 of 16 |
| hit the 1024-token cap | **6 of 16** — of these, **5** produced no answer and are **permanently unmeasurable**: the runner logs only the last 90 characters. One capped row still emitted a clean line, which is why 11 answered and 10 finished |
| claimed success | **withdrawn — see the correction below.** The runner's own count is 16, and it is not a count of claims |
| claimed UNSOLVABLE | 0 of 16 |

**The finding, corrected.** The 8B half of the sentence that stood here was wrong, and it was mine:
this file said the 8B "claimed `SOLVED` 15 of 15 times on unsolvable 4×4 boards". Measured on the 30
rows in `probes/lightsout/results_v3.jsonl`, the 8B emitted **one** answer, `PRESSES: NONE /
CLAIM: UNSOLVABLE`, **30 of 30** — `claim` counts to `UNSOLVABLE: 30`, `SOLVED: 0` — with verdicts
`CORRECT_UNSOLVABLE 15` and `FALSE_UNSOLVABLE 15`. The 15 on unsolvable boards is the model being
**right**; the 15 is a false *impossibility* count on the solvable half. There were no `SOLVED` claims
on that rung at all. The paragraph three sections above already carries the rule that refutes the
sentence: *a constant scores the base rate by construction*. I quoted my own rule and then read a
`CORRECT` cell as a failure, because I carried the number and dropped the verdict name.

What survives, measured. **False success is real, and it is measured at the two smaller rungs**, where
the rows carry an explicit `CLAIM:` line: at 2×2, six rows claim `SOLVED` and **one** is correct — the
degenerate all-off board — so `FALSE_SUCCESS 5`, with `FALSE_UNSOLVABLE 10`; at 3×3, the peer reads all
ten completed answers as asserting the cells are off, none solved. The 4×4 arm is the opposite shape:
a constant *impossible* that is right on half a balanced sample by construction. The honest comparison
is therefore **not** "false success at both scales" but **a constant verdict that never varies with the
board, and whose sign changes with the rung** — impossible at 4×4, mostly impossible at 2×2, done at
3×3, and wrong in all three.

**Corrected 2026-10-22 17:00 PDT against commit `4c130a0`, whose message repeats the withdrawn
sentence and cannot be edited without rewriting history.** The 3×3 model numbers below remain the
peer's measurement on his seat, quoted as his; what is corrected here is my characterisation of the
4×4 arm, which is measured on the rows on this box.

**The fixture control, re-derived here independently** (own GF(2) solver written from the rules of
Lights Out, not from arena code, run against the fixture by digest): rank 9 on all 16 boards, nullity 0,
the fixture's own `correct` string **is** the unique clearing set **16/16**, `x`/`b` encodings 16/16,
boards distinct 16/16. So `0 of 16` is a fact about the model, not about an ambiguous question.

**What this does not measure:** the five truncated rows. A derivation cut at the token cap is
_unmeasured_, not wrong — the runner discarded the text that would have shown whether it was on its
way to the answer. Recorded that way rather than softened to "to be re-run": the bytes no longer exist.

### The fixture

`3x3_fixture_16_boards_20261022.{md,json}` (sha256 `2c18e257afe3d066` / `851976c57068bca9`)
pre-registers 16 boards as the images of 16 press strings with `x = 0` excluded, so the all-off
board is **absent by construction**. Verified independently twice: 3×3 has rank 9, nullity 0, every
one of the 512 boards solvable with exactly one solution, and every one of the 512 possible constants
scores exactly **one** board of the space.

That last fact is why the exclusion matters: rank alone does not buy a zero floor — a bijective press
map guarantees one winning board per constant. Over this 16-board sample a constant is worth 1/16 if
its board is in the set and 0/16 otherwise; "press nothing" scores 0/16 by construction.

`arm1_3x3.py` remains on this box, staged and dry-run clean, for a same-seat re-run if this card's
answer is ever wanted at the cost of ~25 minutes.

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
probes/lightsout/results_v3.jsonl          30 rows, 4x4 directive arm
                                           1bd384561062f5f0ddcc37ae38ec4e6f1469571ef2e78cc12512685f0747bf58
probes/lightsout/results_rung1_2x2.jsonl   16 rows, 2x2 state-scored arm
                                           bda2da4eca665fe442bb57e2fffd0bbfb113734fe374ba0a93b0d9ed29e1bad6
probes/lightsout/3x3_fixture_16_boards_20261022.{md,json}
                                           md   2c18e257afe3d06616dea915dbd3473b442087064c4fb4c7d3bca705a928fe83
                                           json 851976c57068bca9748a10cbaf8763f6938b4c9605c24aab3151a26925e90175
probes/lightsout/arm1_3x3.py               staged, dry-run clean, NOT run
```

**Paths corrected 2026-10-22 17:00 PDT, and one claim in this block withdrawn.** It previously cited
`results_v3.jsonl` and `results_rung1_2x2.jsonl` at the repository root and a "hash-verified copy, out
of the 24h scratch" at `artifacts/rung1-20261022/`. None of those three paths exists: the rows live in
`probes/lightsout/`, and no `artifacts/` directory is present anywhere in the tree, so the copy that
was claimed to have been taken out of the expiring scratch **was never taken**. The bytes are intact —
the two surviving copies (repo and 24h scratch) are byte-identical to each other at the digests above —
but the arrangement was one artifact in two places, one of which expires, and a citation that could not
be followed. A row's digest is cited here so the numbers can be checked against the rows without
trusting this file's prose.

Every row carries `max_tokens`, `completion_tokens`, `finish_reason`, `answer_block`, `parse_path`,
`out_of_range`, `raw` and the computed truth, so a row can be checked against the text that travels
with it.
