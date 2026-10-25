# SUITE RESULTS — multi-model cabinet suite, judgement GPU window 2026-10-25

Window card: kanban `t_c4fa298e` (Mike approved 2026-10-25). Pre-registration committed **before the
first model call of this window**: `PREREG_multi_model_suite_20261025.md`, commit `86aaa24`.
Two cabinets ran to completion — **Mastermind** and **Lights Out** — across all four entrants. The
other five cabinets did not run in this window and are named at §8; their silence is silence, not a
negative.

Every figure below was read from a command's own output: the cabinets' row files, `/props`,
`nvidia-smi`, and `/proc`. Nothing is quoted from a previous session's prose.

---

## 1. What served each row — the compute path and the process

A row is a snapshot of a **process**, not of a prompt. The seat that produced the published
2026-10-23 Mastermind rows no longer exists (pid 976745 started Fri Oct 23 15:06:57, after the
published run ended 14:11:22Z), so nothing here reproduces those rows and nothing here is presented as
a reproduction.

| entrant | weights | size (bytes) | binary · build | `/props` ftype | -ngl · ctx | slots | serving proc started |
|---|---|---|---|---|---|---|---|
| `ministral-3b` | Ministral-3-3B-Instruct-2512-UD-Q4_K_XL | 2,191,963,424 | llama.cpp `b10931-3057bb66c` | `Q4_K - Medium` | 99 · 8192 | 1 | 2026-10-25T13:06:43-0700 (pid 2338969) |
| `ornith-9b` | Ornith-1.5-9B-Q4_K_M | 5,780,090,816 | llama.cpp `b10931-3057bb66c` | `Q4_K - Medium` | 99 · 8192 | 1 | 2026-10-25T13:07:10-0700 (pid 2339392) |
| `mimo-9b` | MiMo-V2.6-Distill-Qwen-9B-Q4_K_M | 5,841,049,120 | llama.cpp `b10931-3057bb66c` | `Q4_K - Medium` | 99 · 8192 | 1 | 2026-10-25T13:08:49-0700 (pid 2340663) |
| `bonsai-9b` | Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0 | 2,675,410,720 | PrismML `b10777-e3de71522` | `PQ2_0 - 2.13 bpw (group 128)` | 99 · 8192 | 1 | 2026-10-25T13:11:01-0700 (pid 2342291) |

Every row also carried, per run: `/props` `model_path`, `default_generation_settings.n_ctx = 8192`,
`total_slots = 1`, alias, and `nvidia-smi` per-pid VRAM attribution. `--parallel 1` was passed and
verified from `/props` (the pricing probe ran 4 slots over one shared KV pool; these rows do not).

**The quant column is not fully readable from `/props`.** All three Q4 files report the identical
ftype string `Q4_K - Medium` — including `Ministral-...-UD-Q4_K_XL`, whose filename claims a different
recipe. So for those three rows the quant in the table is the **filename**, not a server-reported
quantisation; only the Bonsai's ftype distinguishes itself. A future row that needs the quant as
evidence must read tensor types, not `model_ftype`.

**Two clocks, per entrant** (one fixed 256-token generation, thinking off, temperature 0.0, on its
own served process — `suite/throughput.py`, files `suite/runs/throughput_*.json`):

| entrant | client tok/s | server tok/s (`predicted_per_second`) | gap | server prompt tok/s | pid VRAM (MiB) |
|---|---|---|---|---|---|
| `ministral-3b` | 133.11 | 134.14 | 0.8% | 1514.6 | 2774 |
| `ornith-9b` | 56.76 | 66.61 | 14.8% | 318.3 | 5264 |
| `mimo-9b` | 60.76 | 65.66 | 7.5% | 195.1 | 5478 |
| `bonsai-9b` | 109.13 | 121.15 | 9.9% | 304.8 | 2572 |

The gap is real and entrant-dependent (0.8%–14.8%), which is why the cabinet tables below report the
**client** clock on every row and never mix it with a server figure.

---

## 2. Mastermind — 16 pre-registered secrets, 4 pegs × 6 colours, limit 10, `max_tokens` 512

Instrument `mastermind_run_onefile.py` sha256 `3bc8e7685522…` (unmodified) · fixture
`mastermind_secrets_16.txt` sha256 `ccae01aecd7c…` · prompt sha256 `e671e8aeaa9b…` — read out of the
published row file itself (`probes/mastermind/rows_9b.json`, `run.prompt_sha256 e671e8aeaa9ba084…`,
`max_tokens 512`), so these rows were played on the **same prompt bytes** at the **same budget** as the
2026-10-23 CPU row. What differs is named in the compute-path column: ctx (the published seat ran
65536, these ran 8192), the path (-ngl 0 vs 99), the binary build and the serving process.
Control re-run at window open: **16/16, mean 5.50, row-set digest `43eb702eda746f26…`**, matching
the published control digest; and again at window close on the same fixture with the same result
(`43eb702eda746f26…`). The harness is sound before any model number below is read and unchanged after.

| entrant | compute path | wins | answered /160 | consistency | distinct guesses | modal guess | no_answer turns | peak pid VRAM (MiB) | row-set sha256 |
|---|---|---|---|---|---|---|---|---|---|
| `ministral-3b` | GPU -ngl 99 | **0/16** | 160 | 10.0% | 48 | `[0,1,2,3]` ×16 | 0 | 2776 | `d88f369b2b5e` |
| `ornith-9b` | GPU -ngl 99 | **0/16** | 148 | 11.5% | 12 | `[0,1,2,3]` ×47 | 3 | 5268 | `944bfae65c83` |
| `mimo-9b` | GPU -ngl 99 | **0/16** | 25 | 64.0% | 2 | `[0,0,0,0]` ×18 | 16 | 5480 | `4434fc830372` |
| `bonsai-9b` | GPU -ngl 99 | **0/16** | 160 | 16.2% | 8 | `[0,1,2,3]` ×115 | 0 | 2574 | `1e0bf27c7480` |
| `prism-bonsai-9b` *(published 2026-10-23, for comparison)* | **CPU -ngl 0**, different process (now dead) | 0/16 | 160 | 18.8% | 6 | `[0,1,2,3]` ×132 | 0 | n/a (CPU) | `95d878e17ead` |

**Pre-registered decision rule applied:** separation required differing win counts, or ≥2× consistency
with both arms ≥100 answered turns. Zero wins everywhere, and `mimo-9b`'s 64% is over **25** answered
turns — below the 100-turn floor, so the rule does not fire on it. **Result: not separated at n=16.**
Four clean 0/16 negatives; nobody wins a game.

Three measured notes:

1. **`mimo-9b`'s zero is an interface outcome, and the guess is present in the bytes.** All 16 games
   ended `no_answer` after 1–3 answered turns. Replayed on one game (`suite/diag_mimo_noanswer.py`,
   diagnostic not a row): with `enable_thinking:false` it writes its derivation into the **content**
   channel between literal `…` tags and then glues the guess to the closing tag —
   `…0 1 2 3<｜end▁of▁thinking｜>0 1 2 3` — 292 tokens, `finish=stop`. The registered parser requires four
   integers alone on a line, so the row is `NO_ANSWER` **by the registered contract**. Accepting it
   would be a new registration (I3), not a fix to this one. Reading this row as "cannot play
   Mastermind" would be wrong; `answered = 25` is the column that says why.
2. **`ministral-3b` answers in far more shapes (48 distinct) and converts none of them** — the same
   pattern the published 4B pair showed: variation is not discrimination.
3. **`bonsai-9b` on GPU is not the published CPU row.** 16.2% vs 18.8% consistency, 8 vs 6 distinct,
   modal share 115/160 vs 132/160. Both rows are 0/16 with 160 answered, so the *verdict* agrees and
   only the text drifts. Per the process-identity rule this difference **cannot** be attributed to
   the GPU path: that row recorded no binary hash and no process start time, so equality cannot be
   shown even where it is plausible, and no CPU row was produced inside today's process. It is filed
   as a row difference, not a speed effect.

---

## 3. Lights Out — 3×3, 16 pre-registered boards, `max_tokens` 256, directive answer contract

Instrument `arm2_3x3_same_conditions.py` sha256 `7b3f304e7b24…` (imported and parameterised at the
URL/model boundary only; prompt untouched, template sha256 `54e72a068e87…`) · fixture
`3x3_fixture_16_boards_20261022.json` sha256 `851976c57068…`, labels recomputed from the press matrix
at run time. On 3×3 (rank 9, nullity 0) every board is solvable with a unique solution, so a constant
`CLAIM: UNSOLVABLE` scores 0/16 by construction, and a plausible-looking constant earns nothing.

| entrant | compute path | correct /16 | distinct answers | answer blocks | verdicts | tokens (median) | wall (s) | out-of-grid rows | peak pid VRAM (MiB) |
|---|---|---|---|---|---|---|---|---|---|
| `ministral-3b` | GPU -ngl 99 | **0/16** | 2 | 16 | UNATTRIBUTABLE 13 · FALSE_SUCCESS 3 | 29 | 3.6 | 13 | 2774 |
| `ornith-9b` | GPU -ngl 99 | **1/16** | 12 | 16 | FALSE_SUCCESS 15 · CORRECT 1 | 23 | 7.7 | 0 | 5264 |
| `mimo-9b` | GPU -ngl 99 | **0/16** | 8 | 16 | FALSE_SUCCESS 16 | 17 | 7.8 | 0 | 5478 |
| `bonsai-9b` | GPU -ngl 99 | **0/16** | 7 | 16 | FALSE_SUCCESS 12 · UNATTRIBUTABLE 4 | 23 | 5.7 | 4 | 2572 |
| `bonsai-9b` **CPU control** | **CPU -ngl 0**, separate process started 13:12:35 | **0/16** | 8 | 16 | FALSE_SUCCESS 11 · UNATTRIBUTABLE 5 | 23 | 43.5 | 5 | 420 |

`CORRECT` is state-verified: the presses were applied to the board and the board reached all-off.
`CLAIM` is a separate column and was never used to award a solve (I5). **No entrant emitted
`CLAIM: UNSOLVABLE` on any board — 64 of 64 answers claim SOLVED**, so on this rung the claim column
carries no information and every verdict is carried by the presses.

**Decision rule applied:** correct counts must differ. `ornith-9b` has 1, the others 0 — the rule
fires, and the effect size is **one board out of sixteen**. Filed as *separated by the rule, not by
evidence*: this suite cannot tell one correct board from luck, and `ornith-9b` also emitted 12 distinct
answers against `mimo-9b`'s 8 at the same size and quant, which is a difference in text, not in score.

Two measured notes:

1. **`ministral-3b` answers a 3×3 board with cells that do not exist on it**: 13 of 16 rows name
   `D1, E2, F3` in a constant chant `A1, B2, C3, D1, E2, F3`. On a 3×3 grid only A–C and 1–3 exist, so
   those rows are `UNATTRIBUTABLE` — out-of-language, not merely wrong. This reproduces, on a second
   rung and a different process, the published 2×2 finding where a model answered `A1, B1, C1, D1`:
   **the grid size does not reach the output.**
2. **The CPU/GPU pair is same-binary, same-weights, same-prompt, different process** — which is
   unavoidable, because `-ngl` cannot change inside a running process. Verdicts are identical
   (0/16 both), the answer set drifts (7 vs 8 distinct), and the wall clock goes 5.7 s → 43.5 s
   (**7.6×** on this cabinet, against 14.6× on the synthetic probe — per-call overhead dominates when
   answers are 17–29 tokens). The pair is filed as a path comparison with the process confound named,
   not as a model comparison.

---

## 4. Tenancy — what happened to the card, and what was proved at each release

**A fourth tenant appeared mid-window.** At 13:01:04 `llama-swap` took a scoped GPU lease
(`--owner llama-swap-ocho-planner-4b --class batch --scope planner --need-mib 3800 --ttl 86400`) and
loaded a Qwen3.5-4B grammar server on `:5806`, holding **3482 MiB**. Measured consequence: free VRAM
fell to 2619 MiB and `mimo-9b` **refused admission at -ngl 99** with
`unable to allocate CUDA0 buffer of size 5257955328`. That refusal is recorded as an *admission datum*,
not a failed attempt (the 2026-10-23 rule), and the same entrant admitted cleanly once the card was free
— so the envelope claim in the card is true **of a free card**, and false beside a 3.5 GiB tenant.

Resolution, chosen to be the sanctioned mechanism rather than an eviction: `gpu-yield.sh --target
llama-swap` asked llama-swap to unload **through its own API** (HTTP 200), card went 5272 → 1785 MiB,
and the suite then held the **global** GPU lease
(`gpu-lease.sh acquire --owner ocho-suite-t_c4fa298e --class batch --need-mib 5400 --ttl 14400`,
`ADMITTED — 6106 MiB free ≥ 5656 MiB needed`). `prism-brain.service` / `:58595` was never stopped,
restarted or reconfigured (V2), `/health` returned 200 before and after every run.

| run | port 58701 closed | VRAM after (MiB) | baseline (MiB) | delta | pid VRAM after | resident `:58595` health |
|---|---|---|---|---|---|---|
| mastermind · ministral-3b | true | 1776 | 1776 | 0 | 0 | 200 |
| mastermind · ornith-9b | true | 1776 | 1776 | 0 | 0 | 200 |
| mastermind · mimo-9b | true | 1776 | 1776 | 0 | 0 | 200 |
| mastermind · bonsai-9b | true | 1776 | 1776 | 0 | 0 | 200 |
| lightsout · ministral-3b | true | 1776 | 1776 | 0 | 0 | 200 |
| lightsout · ornith-9b | true | 1776 | 1776 | 0 | 0 | 200 |
| lightsout · mimo-9b | true | 1776 | 1776 | 0 | 0 | 200 |
| lightsout · bonsai-9b | true | 1776 | 1776 | 0 | 0 | 200 |
| lightsout · bonsai-9b **-ngl 0 control** | true | 1775 | 1776 | −1 | 0 | 200 |

**The baseline is not a constant, and V4 was checked against a measurement.** The card quotes 1,731
MiB; the card measured 1,721 MiB at window start and 1,776 MiB after the planner left. Every block
sampled the baseline at its own start and compared against that, at a 64 MiB tolerance — a leaked
entrant is 2.5–5.5 GiB, three orders of magnitude outside the bar, while the resident seats' allocator
moves a few MiB between blocks. Peak card use with a Q4 9B entrant resident: **7049 MiB (ornith) and
7261 MiB (mimo) of 8192** — one such entrant occupies ~88% of the card, which is why V3 (no parallel
cabinets) is not merely a rule but a physical necessity.

**Close of window:** the global lease was released (`lease in scope (global) … removed`), the card read
**1775 MiB used / 6116 MiB free**, both lease stores empty, and **no listener on :58701**. llama-swap was
not restarted and will reload the planner model on its next request; `:58595` stayed healthy throughout.

---

## 5. What this suite cannot separate

- **Class from quantisation.** The entrants differ in family, size and bit-width at once
  (UD-Q4_K_XL·3B, Q4_K_M·9B ×2, PQ2_0/Q8_0·9B). `ornith-9b` vs `mimo-9b` *is* a same-size,
  same-`/props`-ftype pair and they differ in text (12 vs 8 distinct answers) — but the ftype string
  cannot show the two files are the same bit-width (§1), so even that pair is not a controlled
  quantisation comparison.
- **Capability from interface — now measured, not hypothesised.** Two of the four zeros are interface
  outcomes with the right tokens present in the bytes: `mimo-9b`'s Mastermind guess glued to a
  `<｜end▁of▁thinking｜>` tag, `ministral-3b`'s out-of-grid Lights Out cells. `no_answer` / `parse_path` /
  `out_of_grid` columns are what separate those from a model that cannot play; the suite does not
  re-prompt to find out, so it cannot say how many of those games were winnable.
- **Anything at n=16 but a clean 0/16 or 16/16.** One correct board out of sixteen is not a rate.
- **Model from process.** Every row here is a process started today; the published CPU rows are
  processes that no longer exist. The one clean path comparison available (Bonsai Lights Out, 5.7 s
  GPU vs 43.5 s CPU) confounds `-ngl` with process by construction, and says so in its row.
- **A CPU Mastermind control for `bonsai-9b` was not run** — at the measured 6.32 tok/s, 160 turns of
  ~100 tokens is ~42 minutes per arm. Not run, not estimated, not claimed.

---

## 6. Files

```
PREREG_multi_model_suite_20261025.md      pre-registration, commit 86aaa24 (before any model call)
suite/suite.py                            lease + cabinet driver (start → /props → run → release)
suite/throughput.py                       the two clocks, per entrant, own process
suite/cabinets/lightsout_param.py         the registered 3x3 instrument, parameterised at the URL only
suite/diag_mimo_noanswer.py               diagnostic replay: DIAGNOSTIC, files no rows
suite/report.py, suite/mktables.py        aggregation from the row files (no re-typed numbers)
suite/runs/AGGREGATE.json                 every figure in §2–§3, machine-readable
suite/runs/mastermind_<entrant>_*.json    rows + run header (instrument/fixture/prompt hashes, digest)
suite/runs/lightsout_<entrant>_*.jsonl    rows (verdict, claim, parse_path, presses, raw)
suite/runs/*.meta.json                    compute path, serving-process identity, VRAM samples, release
suite/runs/CPUNGL0_*                      the -ngl 0 control, kept out of the aggregate by name
suite/runs/DIAGNOSTIC_*                   diagnostic, not a row
```

## 7. Reproduce

```
gpu-lease.sh acquire --owner <name> --class batch --need-mib 5400 --ttl 14400
python3 suite/suite.py --entrant ministral-3b --cabinet mastermind,lightsout
python3 suite/suite.py --entrant bonsai-9b --cabinet lightsout --ngl 0     # the CPU control
python3 suite/report.py && python3 suite/mktables.py
gpu-lease.sh release --owner <name>
```

## 8. What did not run in this window

**Sokoban, Zork, Snake, Labyrinth, Chess** — the third, fourth and fifth rungs of the card's
sequencing. Not run, for two recorded reasons: the window's wall clock went to Mastermind and Lights
Out across four entrants (each entrant needed a full load/unload cycle, and the two Q4 9B entrants
each take ~88% of the card), and the two cabinets that did run are the ones the card put first
precisely because their failures are attributable. **Nothing in this document is evidence about those
five cabinets**; a 0 there is unmeasured, not zero.
