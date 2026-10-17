# MISSILE COMMAND — POPULATION RUN ONE: THE VERDICT

**Run of record:** `probes/MC_POPULATION_20261017-184752.json` (run id `20261017-184752`)
**Population run under:** `scripts/run_guarded.sh mc-population` (ceiling 24G/32G/1G) — never a bare run
**Pre-registration:** `PREREG_mc_population.md`, digest `a999788483656143`, **committed at `70f8077` BEFORE the
run**; the runner `missile_command_population.py` at `c0dbe28`. *(`a999788483656143` is the file AS THE RUNNER
READ IT. The correction note appended after the run moved it to `34d5d6042b017bfa` — same file, two moments,
and every number below was computed under the first one.)*
**Frozen artifacts, untouched:** `missile_command.py` `eb5ed36591b300e6`, `PREREG_missile_command.md`
`01548e9a866df03e`, `levels/mc_01_one_shot.txt` `ab101ca955c1c853`, `levels/mc_02_scarcity.txt`
`327d2157bd0b8a83`. **No frozen criterion moved, and no shared file was touched.**
**Instrument carried in the record:** declaration `MC_DECLARATION.md` `c7a60f1d6b4e4030`; the reader of record
(`answer_reader.py`, digest `450050761099e93c`) **imported, never reimplemented** (RULING 79); the default
binary `0d5393431782ddf8` for five entrants and the prism fork `3c7090fb24b84615` for the ternary one.

---

## THE VERDICT

```
GATE        MET.  coverage 1.000 (12/12), yield 1.000 (12/12), never_started 0 -- ON BOTH ARMS.
C1 FLOOR    MET   on the arm of record, BY EXACTLY ONE CELL: MiMo-V2.6 `1P` -> 1/1 cities on mc_01.
C2 FACULTY  FAILED  on the arm of record: SIX mc_02 cells, scores 0,0,0,0,0,0 -- distinct scores [0].
                    In the criterion's own words: the state is not discriminating, "and that is a
                    finding about the STATE, not about the entrants".
C3 DECOYS   FAILED  on the arm of record: no cell above the comparison line. Best mc_02 score 0/4,
                    the blind spender's line is 2/4.

THE EVENT FAILS, AND IT FAILS ON THE INSTRUMENT STATE: a population of six could not beat a line that
spends blindly, and on the recorded instrument the instrument's own state separated nobody.
```

**The scope statement the frozen PREREG declared in advance for exactly this shape attaches:**
**`FAILED ON THIS POPULATION`** — six entrants, one state set, one model per cell (n=1), **and the upper tail
of the size range is not in this run** (see SCOPE). It attaches to the two FAILs as a scope, and it excuses
neither.

**Row 4 (INSUFFICIENT) does NOT fire**, and the reason is a number rather than an impression: the population
**can** parse a two-character action (8 `fired` tokens and 7 `passed` tokens across the arm of record; 4 of 6
mc_01 cells fire in the comparison arm), **no entrant failed to load** (0 load failures, 0 `never_started`),
and **mc_01 separates** (1/1 against 0/1 in both arms). What fails is mc_02's spread on one arm and C3 on
both — findings about the state and the population, not a null field.

---

## THE GATE, AND THE PORTION OF IT THAT IS ADOPTED RATHER THAN RE-RUN

```
arm of record (`example`)   planned 12   never_started 0   attempted 12   measured 12
                            coverage 1.000   yield 1.000   GATE MET
comparison arm (`plain`)    planned 12   never_started 0   attempted 12   measured 12
                            coverage 1.000   yield 1.000   GATE MET
```

**2 of the 12 cells of the arm of record were ADOPTED, not re-run** — `Qwen3.5-2B-UD-Q4_K_XL`'s two
`example`-arm cells, whose published coordinates already held records taken under **this run's own identity**
(binary `0d5393431782ddf8`, legend `ec59f2dc5fd35518`, reasoning `off`, compared by
`carried_identity()`/`run_identity()`). Their file digest and mtime travel in the artifact. **A cell whose
coordinate held another instrument would have been `never_started` with the difference named; none was.**
The other 22 cells were taken by this run, in 22 spawns on one card, all inside the guard.

**A zero-measured run would have exited non-zero.** It did not, and that is reported as a fact about this run
rather than as a property of the gate.

---

## THE CRITERIA, AS THE PRE-REGISTRATION MADE THEM OPERATIONAL

**Every number below is quoted with the set it was computed over. Nothing here is a rate over a denominator
an entrant can shrink — the counts are the result and the rates are the index.**

### ARM OF RECORD (`example`, digest `ec59f2dc5fd35518`) — the arm the declaration names

| entrant | mc_01 | mc_02 |
|---|---|---|
| LFM2-350M-Extract-Q4_K_M | 0/1 (`{`×3, `malformed` 3) | 0/4 (`{`×6, `malformed` 6) |
| Qwen3.5-2B-UD-Q4_K_XL *(adopted)* | 0/1 (`3P`×3, `unknown` 3) | 0/4 (`3X 3X 3X 3Q 3P 3T`, `unknown` 6) |
| Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0 | 0/1 (`PASS`×3) | 0/4 (`PASS 2X 2Z PASS PASS PASS`) |
| OculusMind-ToolCall-8B-v2.i1-Q4_K_M | 0/1 (`2P`×3, `unknown` 3) | 0/4 (`0X 0X 0P 0P 0P 0W`, `unknown` 6) |
| MiMo-V2.6-Distill-Qwen-9B-Q4_K_M | **1/1** (`1P`, `fired` 1) | 0/4 (`Silo`×6, `malformed` 6) |
| Mellum2.1-12B-A2.5B-Thinking | 0/1 (`We`×3, `unknown` 3) | 0/4 (`We`×6, `unknown` 6) |

```
C1 over the 6 measured mc_01 cells   cells with fired >= 1: 1  ->  MET, by ONE CELL
C2 over the 6 measured mc_02 cells   scores [0,0,0,0,0,0]  distinct [0]  ->  FAILED
C3 over the 6 measured mc_02 cells   comparison line 2/4   cells above it: none  ->  FAILED
```

### THE DECLARED COMPARISON ARM (`plain`, digest `d8ee3da099c1a0c2`) — reported, not substituted

| entrant | mc_01 | mc_02 |
|---|---|---|
| LFM2-350M-Extract-Q4_K_M | 0/1 (`{`×3) | 0/4 (`{`×6) |
| Qwen3.5-2B-UD-Q4_K_XL | **1/1** (`1P`) | 0/4 (`1X 1X 1X 1Q 1S 1T`) |
| Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0 | **1/1** (`1P`) | 0/4 (`2X 2Y 1R 1R 1T`) |
| OculusMind-ToolCall-8B-v2.i1-Q4_K_M | **1/1** (`1P`) | **1/4** (`1X 1X 2X 1P 1S 1T`) |
| MiMo-V2.6-Distill-Qwen-9B-Q4_K_M | 0/1 (`Silo Silo The`) | 0/4 (`Let Let's Let Let Silo Silo`) |
| Mellum2.1-12B-A2.5B-Thinking | **1/1** (`1A 1P`, `fired` 1) | 0/4 (`We`×6) |

```
C1  4 of 6 mc_01 cells fire (Qwen3.5-2B, Bonsai-9B, OculusMind, Mellum)  ->  MET
C2  scores [0,0,0,1,0,0]  distinct [0,1]  ->  MET, and the spread is ONE CELL WIDE
C3  best mc_02 1/4 against the line's 2/4  ->  FAILED, exactly as on the arm of record
```

**C3 FAILS ON BOTH ARMS, so the arm does not decide this verdict's bottom line.** C2's outcome *does* differ
between the arms, and that difference is reported here as a difference and is **not** used to re-score the
arm of record. *A criterion change after the number is a file, not a criterion.*

---

## WHAT THE RUN MEASURED ABOUT THE LEGEND ITSELF — THE A/B, AT POPULATION SCALE

The pre-registered prediction (`PREREG_mc_population.md`, written before the second arm ran) was that the
`example` clause supplies the silo value, so the `plain` arm would move `unknown` DOWN and `fired` UP.
**It did, and the branch is selected by the counters:**

```
unknown   27 (example)  ->  7  (plain)
 fired     2 (example)  ->  8  (plain)
mc_01 scores  1 (example) -> 4  (plain)      mc_02 score total  0 -> 1
BRANCH 1 -- the example IS the carrier, at population scale, exactly as pre-registered.
```

**AND THE MECHANISM IS VISIBLE IN THE TOKENS, WHICH IS WHERE IT HAS TO BE.** In the arm of record, three
entrants name a silo the state does not have, and one of them names **the legend's own example digit**:

```
Qwen3.5-2B    names '3' in all NINE of its firing tokens (state has silo 1; mc_02 has 1 and 2)
OculusMind    names '2' on mc_01 (state has 1) and '0' on mc_02
Mellum        names 'W' -- the head of the word "We", which is where its answer was cut
```

**And the honest qualifier, because the aggregate would otherwise over-claim:** 7 of the 12 entrant×state
pairs carry a ceiling caveat in at least one arm, so part of the movement is the 64-token ceiling moving
rather than the legend (MiMo's mc_01 goes 1/1 -> 0/1 with the ceiling involved; Mellum's mc_01 improves
partly because its `example`-arm answer was cut at every turn). **Restricted to the 5 pairs where NO arm was
cut at all, 4 of 5 improve** — Qwen3.5-2B mc_01 0/1 -> 1/1 and mc_02 `unknown` 6 -> 0; OculusMind mc_01
0/1 -> 1/1 and mc_02 0/4 -> 1/4; Bonsai-9B mc_01 0/1 -> 1/1 (its `example`-arm answer was three PASSes).

---

## THE CONTROLS THAT RAN BESIDE THE NUMBERS

```
per cell, every token produces exactly one outcome, and every threat is destroyed/hit/spared
      -> ALL 24 cells pass, both equalities                                     (carried per cell)
sufficiency: the score and EVERY screen re-derive from (state_text, tokens)
      -> "THE RECORD IS SUFFICIENT" in all 24 cells                              (carried per cell)
missing values          0 across all 24 cells -- an empty the harness produced is never a token
ended                   threats_resolved in all 24 cells (nothing was cut off by the command cap)
C3's comparison line    pre-registered 2/4, re-derived at run time 2/4 -- MATCH
replication control     4 cells of this run are also in `probes/MC_LEGEND_AB.json`; ALL 4 reproduced
                        TOKEN-FOR-TOKEN (including both arms of Qwen3.5-2B) -- the entrant path is
                        deterministic here, and a disagreement would have been the finding
budget signature        5 cells BUDGET-CONFOUNDED (every turn cut at the ceiling), 7 with some turns cut,
                        12 clean -- PER THE DRIVER'S OWN RULE, a `malformed` count is not a capability
                        result until this has been read, and it is read here rather than discovered later
```

---

## THE POPULATION, AND THE ONE PLACE THE DERIVATION RULE HAD TO BE WIDENED

**Derived, never typed**: 75 `*.gguf` in `ARENA_MODELS`, **58 kept, 17 removed**, and the artifact carries
the removal list with **the reason that removed each file**: 11 by `mmproj`, 4 by `-vl-`, 1 by `audio`, 1 by
`qwen-image`. `step = 58 // 6 = 9` over the size-sorted list gives six entrants spanning **0.229 GB to
8.071 GB** (a 35× spread):

```
0.229 GB  LFM2-350M-Extract-Q4_K_M                      64408023877317d4   the floor of the field
1.340 GB  Qwen3.5-2B-UD-Q4_K_XL                         0d5cb2e1b6c4e484
2.675 GB  Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0            c79fcdfaf6b7bf47   ternary -> the prism fork
5.198 GB  OculusMind-ToolCall-8B-v2.i1-Q4_K_M           d1af691a3d294be7
5.841 GB  MiMo-V2.6-Distill-Qwen-9B-Q4_K_M              2ae136739925024f
8.071 GB  Mellum2.1-A2.5B-12B-Thinking-Q4_K_M           a4a0393a2e6e5487
```

**THE FINDING IN THE RULE, AND IT IS A REPAIR TO A STANDING ONE:** `mmproj` has to be excluded as a
**substring**, not as a prefix. Measured in this directory: a prefix test (`startswith("mmproj")`, the shape
carried in `sokoban_batch.population()`) lets **five PROJECTOR files into a text population** —
`Ternary-Bonsai-2-{2B,4B,9B,27B}-mmproj-Q8_0.gguf` and `AesCode-8B.mmproj-Q8_0.gguf` — because their names
do not begin with it. The frozen PREREG says "`mmproj` excluded" and names `run_card.py`'s resolution, which
is that substring test; **the rendered rule now matches the named resolution, and the removal list makes it
checkable instead of assertable.**

**AND ONE ARITHMETIC SLIP OF MY OWN PRE-REGISTRATION, RECORDED RATHER THAN QUIETLY FIXED:** the file's
breakdown line says *"12 by `mmproj`, 4 by `-vl-`, 1 by `qwen-image`"*. The artifact's own list counts
**11 + 4 + 1 + 1** (the `audio` file was folded into `mmproj` in the sentence). **The total (17), the kept
count (58), the rule the runner applied and the central claim (five projectors survive a prefix test) are
unchanged**; the sentence's split was off by one and is corrected here, from the artifact, where the reader
can also check it.

---

## SCOPE — WHAT THIS RUN DOES NOT SAY

* **The upper tail is NOT in it.** `ARENA_MODELS` holds files to 24.9 GB; this population's largest entrant
  is 8.071 GB. Fifteen files between 12.1 GB and 24.9 GB are OUT BY THE n=6 RULE, and the verdict is scoped
  to the population that ran. **No re-scoping happened after the numbers, and none is proposed here.**
* **n = 1 per cell.** Counts are the result; the rates above are indexes over a twelve-cell field.
* **One state set, two states.** mc_01 (the floor) and mc_02 (the instrument) and nothing else.
* **The arm effect is confounded by the ceiling in 7 of 12 pairs**, and said so above rather than left to a
  reader to find in the budget signatures.
* **The population's failure modes are not one thing**: `malformed` first-words (LFM2-350M's `{`, MiMo's
  `Silo`/`Let`), invented silo identifiers (`3`, `2`, `0`, `W`), out-of-reach shots (`out_of_range` 5 in the
  plain arm), and PASS-every-turn. **A verdict that merged these would report a capability failure where the
  record shows four different ones** — which is why the seven outcomes are never merged into a score.

## THE OUTCOME ROWS, APPLIED AS WRITTEN

```
1  GATE UNMET                                   does NOT fire -- coverage 1.000, yield 1.000, both arms
2  GATE MET, criteria evaluated                  FIRES -- this document is the verdict
3  GATE MET, a criterion fails, population a
   candidate cause -> `FAILED ON THIS POPULATION`  ATTACHES to C2 and C3, as a scope, excusing nothing
4  INSUFFICIENT / BLOCKED                        does NOT fire -- see the reasons and the numbers above
5  NO MEASURED ENTRANTS -> ERROR                 does NOT fire -- 12 measured cells per arm
```

## AND THE ARM: THIS RUN SUPPLIES THE REASON, IT DOES NOT TAKE THE DECISION

**The recorded arm has not moved by this work.** What this run adds is a population-scale reason for the
separate act the cabinet named: `unknown` 27 -> 7, `fired` 2 -> 8, mc_01 scores 1 -> 4, **BRANCH 1 as
pre-registered**, with the mechanism audited per entrant and the ceiling confound stated. **The decision is
taken separately, dated, with its own reason and its own record of the declaration's digest drift** — see
`DECISION_mc_legend_arm.md`, landed in the next commit, and `MC_DECLARATION.md` after it.
