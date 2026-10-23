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

**Why the balanced sample was necessary, measured here (2026-10-22 17:12 PDT, arithmetic on the rules,
no model call):** on 4×4 the toggle matrix has **rank 12, nullity 4**, so exactly **4,096 of 65,536**
boards are solvable — **6.25%**, confirmed by enumerating the image rather than by quoting the rank.
A constant `CLAIM: UNSOLVABLE` is therefore **right 93.75% of the time on a random 4×4 board**. The
unsolvable class does not merely exist at this rung; it is 15/16 of the space, which is the opposite of
3×3 (rank 9, nullity 0, every board solvable). The informative cells on this rung are the ten solvable
boards, where the model answered UNSOLVABLE 3 passes out of 3 on every one.

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
| FALSE_SUCCESS | 2 |
| FALSE_UNSOLVABLE | 10 |
| UNATTRIBUTABLE | 3 |

**Re-scored 2026-10-22 17:30 PDT by gating on out-of-range cells, and the data did not change — only the
scoring did.** Three answers read `PRESSES: A1, B1, C1, D1`; `C1`/`D1` do not exist on a 2×2 board, so those
answers are about a different board and cannot be scored here. The guard that flags them was added to the
script at 12:16:00, **eight minutes after the rows were written at 12:08:43**, and the verdict function never
read the flag — so those three rows were published as `FALSE_SUCCESS` off the truncated subset `A1, B1`.
Gated they become `UNATTRIBUTABLE`, and `FALSE_SUCCESS` falls from 5 to 2.

A re-run performed during the re-score reproduced **byte-identical answers on all 16 boards** (temperature 0),
so this is a scoring correction against the same measurement, not a second measurement.

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
| **scored by state** | **0 of 16** — carrying 5 rows that produced no appliable press set: read the denominator note below |
| answered in one line | 11 of 16 |
| finished (`finish_reason = stop`) | 10 of 16 |
| hit the 1024-token cap | **6 of 16** — of these, **5** produced no answer, and their press counts **51/110/111/158/191** cannot be press sets on nine cells: they are **coordinates harvested out of reasoning prose by the parser**, which is a parser defect and **not a token budget**. The sixth was cut off but still emitted a clean line, which is why 11 answered and 10 finished. The five are **permanently unmeasurable as claims** — the runner stored only the last 90 characters |
| claimed success | **withdrawn — see the correction below.** The runner's own count is 16, and it is not a count of claims |
| claimed UNSOLVABLE | 0 of 16 |

**The finding, corrected — and the sentence had a third defect: the subject was mislabelled.** It read
*"the 8B claimed `SOLVED` 15 of 15 times on unsolvable 4×4 boards; the 9B claims it 8 of 11 times…"*.
There is **no 8B in this work at all.** The `model` field is `prism-bonsai-9b` on **30 of 30** rows in
`probes/lightsout/results_v3.jsonl` and on **16 of 16** in `results_rung1_2x2.jsonl`: both rungs here
were played by *Ternary-Bonsai-2-9B*, one 9B-class model. The 3×3 arm was played by a **different**
model, `ornith9b`, on the peer's seat. So the sentence compared two labels as if they were two sizes,
and it did so across two models.

**But an 8B does exist on this box, in a different probe — the sentence was mis-sourced, not invented.**
`~/.hermes/profiles/chilly/cache/scratch/results.jsonl` holds **90 rows across seven models**, including
`critic3` = Llama-3.1-8B-Instruct, **10 rows**: on the 5 **unsolvable** boards it claimed `SOLVED`
**5 of 5**; on the 5 solvable boards it claimed `UNSOLVABLE` 2; **0 solved by state**. So "an 8B claims
success on boards where success is impossible" is a real measurement on this box — it simply belongs to an
earlier probe, not to this ladder. What cannot be re-sourced is the **"15 of 15"**: the stored record holds
one pass of 10 rows, and no file here holds three. **The figure is withdrawn; the behaviour is not.**

Measured on the 30 stored rows, that model emitted **one** answer, `PRESSES: NONE / CLAIM: UNSOLVABLE`,
**30 of 30** — `claim` counts to `UNSOLVABLE: 30`, `SOLVED: 0` — with verdicts `CORRECT_UNSOLVABLE 15`
and `FALSE_UNSOLVABLE 15`. The 15 on unsolvable boards is the model being **right**; the 15 is a false
*impossibility* count on the solvable half. There were no `SOLVED` claims on that rung at all. The
paragraph three sections above already carries the rule that refutes the sentence: *a constant scores
the base rate by construction*. I quoted my own rule and then read a `CORRECT` cell as a failure,
because I carried the number and dropped the verdict name.

What survives, measured, **with the model named per rung**:

| rung | model | measured | shape of the failure |
|---|---|---|---|
| 4×4 | `prism-bonsai-9b` | 30 rows; one answer; `claim UNSOLVABLE 30/30`, `SOLVED 0`; `CORRECT_UNSOLVABLE 15`, `FALSE_UNSOLVABLE 15` | constant **impossible** — right on the unsolvable half by construction, wrong on every solvable board |
| 2×2 | `prism-bonsai-9b` | 16 rows; `claim SOLVED 6`, `UNSOLVABLE 10`; `CORRECT 1` (the degenerate all-off board), `FALSE_SUCCESS 5`, `FALSE_UNSOLVABLE 10` | mostly **impossible**, with a memorised 4×4-shaped answer (`C1`, `D1` do not exist on 2×2) |
| 3×3 | `ornith9b` (peer's seat) | 16 rows; `0 of 16` by state; ≥10 of 10 completed assert the cells are off, none solved | constant **done** |

**The comparison the design can support, and the one it cannot.** It cannot support "false success does
not go away with scale", because **no rung was played by both models** — model and rung are confounded,
so the difference between the 4×4 and 3×3 rows cannot be attributed to size rather than to the model.
What it does support, on two different models and three rungs: **the verdict is a constant that does not
track the board**, and its sign flips between arms. That is a failure of discrimination, and every rung
shows it without needing a scale claim at all.

**Corrected 2026-10-22 17:00 PDT against commit `4c130a0`, whose message repeats the withdrawn
sentence and cannot be edited without rewriting history; corrected a second time at 17:06 PDT when the
`model` field showed the subject itself was mislabelled and the arms confounded.** The 3×3 model numbers
below remain the peer's measurement on his seat, quoted as his; what is corrected here is my
characterisation of the 4×4 and 2×2 arms, which is measured on the rows on this box — and the withdrawn
part is the comparison across rungs, which the design never tested.

**The denominator on `0 of 16`, resolved 2026-10-22 17:20 PDT from the peer's raw record — and my own
word for the five was wrong.** The five rows (boards 5, 7, 8, 11, 13) **were** state-scored: `parse_answer`
harvested cell names with an unanchored `CELL.findall(text.upper())` over reasoning prose and applied them
token by token (`state ^= MASK[p]`), so a set existed and it applied. The set is 51–191 cell names over
nine cells — **appliable, but not the model's answer**. So those five are not *inapplicable*, which is the
word I used; they are **unattributable**: the state column for them measures the parser. The line that
survives is

```
scored by state  0 of 11 rows that emitted an answer line (`how=clean-line`)
                 +5 rows harvested from prose (boards 5,7,8,11,13): state computable, not attributable
```

`0 of 16` is therefore true as *no row cleared its board*, and false as *sixteen rows were each scored on
their own answer*. **And the finding does not shrink — it sharpens:** all nine rows carrying the model's own
`✓` tick are inside the eleven clean-line rows and **none** is a harvested row, so the assertion count is
**9 of the 11 that answered, all nine wrong**, and it does not lean on a single fabricated press set. What
was withdrawn as "8 of 11" was the right *form* with a digit one short; what replaced it in the interim
("16", then "≥10 of 10") were wrong forms. Nine of eleven is the number.

**The fixture control, re-derived here independently** (own GF(2) solver written from the rules of
Lights Out, not from arena code, run against the fixture by digest): rank 9 on all 16 boards, nullity 0,
the fixture's own `correct` string **is** the unique clearing set **16/16**, `x`/`b` encodings 16/16,
boards distinct 16/16. So `0 of 16` is a fact about the model, not about an ambiguous question.

**What this does not measure:** the five truncated rows. A derivation cut at the token cap is
_unmeasured_, not wrong — the runner discarded the text that would have shown whether it was on its
way to the answer. Recorded that way rather than softened to "to be re-run": the bytes no longer exist.

### Arm 2 — 3×3 on the same model and format as the 4×4 row (run here, 43 s)

The peer's 3×3 arm used a different model (`ornith9b`), a different format (derivation permitted) and a
different budget, so no claim about scale could survive it. This arm holds model, prompt contract and budget
fixed at the 4×4 row's values and varies **only the rung**:

| measure | value |
|---|---|
| model / format / budget | `prism-bonsai-9b`, answer contract, 256 tokens |
| rows | 16 (pre-registered fixture, all-off excluded) |
| **DISTINCT ANSWERS** | **8 of 16** |
| verdicts | **FALSE_SUCCESS 12 · UNATTRIBUTABLE 4 · CORRECT 0** |
| rows claiming success | **16 of 16** — every answer ends `CLAIM: SOLVED` |
| boards actually cleared | **0 of 16** |
| elapsed | 43 s on the resident seat, no lease, no eviction |

**The comparison is now un-confounded, and it says this:** on 4×4 the same model emitted one constant
(`CLAIM: UNSOLVABLE`, 30 of 30) and was right on 15 by prior alone; on 3×3 it claims `SOLVED` on **16 of 16**
and clears **none**. Same model, same contract, same budget — **the sign of the constant flips with the rung
and the board never enters the answer.**

**What the answers look like:** the modal response is `PRESSES: A1, B1, C1, C2, C3` on seven different boards
whose actual clearing sets differ. Four answers name `D1`…`I1` — cells that do not exist on a 3×3 grid, the
same 4×4-and-beyond notation failure seen at 2×2. Those are scored `UNATTRIBUTABLE`, not wrong.

**The single most compact statement of this model's behaviour in the whole file:** sixteen boards, eight
distinct answers, sixteen success claims, zero boards cleared.

### The peer's 3×3 arm, for comparison (different model)

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
probes/lightsout/arm1_3x3.py               derivation permitted; the arm the peer ran on his seat
probes/lightsout/arm2_3x3_same_conditions.py   the un-confounded arm, run here (43 s)
probes/lightsout/results_arm2_3x3_same_conditions.jsonl   its 16 rows
probes/lightsout/rung1_2x2.py              the 2x2 runner, sha 93fde98dc24e4dfa — CLOSED (see defect)
probes/lightsout/rung1_2x2_fixed.py        the same runner with the defect repaired; run this one
probes/lightsout/lightsout_probe.py        the 4x4 probe
probes/lightsout/run_directive_v3.py       the directive-format arm
probes/lightsout/recover_press_sets.py     press-set recovery from stored raw
```

### Known defect in a closed artifact

`rung1_2x2.py` ends with a call to `main()` that the file **never defines** — its row loop and summary run
at module level. A fully successful run writes and flushes all sixteen rows, prints its summary, then exits
`NameError`. **The artifacts are complete and the success signal is false**, which is the direction that
makes a harness discard valid work. Confirmed by AST rather than by running it: the original's call set
contains an undefined `main`, the fixed copy's does not.

The original is left unedited because the committed row set cites its digest; `rung1_2x2_fixed.py` is the
corrected copy and ends with an explicit `sys.exit(0)`. The defect entered the file at 18:01 when a
`__main__` guard was appended to a script that had none — the same shape as everything else here: a guard
that looks present and does nothing.

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
