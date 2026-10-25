# PREREG — multi-model cabinet suite, judgement GPU window, 2026-10-25

Registered **before the first model call of this window**. Every number this suite produces is read
against this document, not against a criterion chosen after seeing it.

Authority: kanban `t_c4fa298e` (Mike approved in-session 2026-10-25) →
`SUITE_PLAN_multi_model_2026-10-25.md` (scope, ladder, tenancy, instruments) →
`GPU_PATH_MEASURED_2026-10-25.md` (the measurement that prices the window) →
`GPU_PATH_MEASURED` comment of commit `937c4f1` (two clocks; layer count unverified by the flag;
slots share one KV pool).

---

## 1. Entrants and their compute path

Each entrant is served by a *private* `llama-server` on `127.0.0.1:58701`, started and stopped by
this suite, with `--n-gpu-layers 99 --ctx-size 8192 --cache-type-k q8_0 --cache-type-v q8_0
--parallel 1 --host 127.0.0.1 --port 58701 --alias <entrant>`, no projector, thinking disabled at
the request (`chat_template_kwargs.enable_thinking=false`), temperature 0.0.

`--parallel 1` is a change from the pricing probe, which ran `n_slots = 4` over one shared 8192-token
KV pool. One slot means a parallel request cannot silently shrink the per-request context. The slot
count is read back from `/props` and recorded, not assumed from the flag.

| entrant | file (under `~/moltbook_pipeline/models/`) | binary |
|---|---|---|
| `ministral-3b` | `Ministral-3-3B-Instruct-2512-UD-Q4_K_XL.gguf` | `/home/chilly1/llama.cpp/build/bin/llama-server` (b10931) |
| `ornith-9b` | `Ornith-1.5-9B-Q4_K_M.gguf` | `/home/chilly1/llama.cpp/build/bin/llama-server` (b10931) |
| `mimo-9b` | `MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf` | `/home/chilly1/llama.cpp/build/bin/llama-server` (b10931) |
| `bonsai-9b` | `Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0.gguf` | `/home/chilly1/src/PrismML-Bonsai-demo-20261016/bin/cuda/llama-server` (b10777) |

Binary assignment is per the serving note in `MASTERMIND_RESULTS.md` (PrismML builds refuse some
foreign architectures; the Bonsai PQ2_0 seat is a PrismML seat) and is recorded per row.

**Model identity is read from `/props` (`model_path`, `model_ftype`, `n_ctx`, `total_slots`), not
from the filename in this table.** No multi-GB file digest is taken or quoted: on this box a
multi-GB read does not reliably reproduce (see the memory-path measurement), so the identity evidence
is the server's own report of what it loaded.

## 2. Envelope test is part of the run, not assumed

The card states all four entrants fit the envelope. Only the 2.13 bpw 9B was measured. A Q4_K_M 9B is
~5.5 GiB of weights against ~6.4 GiB free beside the resident seats, so **admission is tested, not
inferred**: the server is started, `/health` must return 200, and the layer count actually accepted is
established from the server's own start and its `nvidia-smi` attribution. An entrant that cannot load
at `-ngl 99` is **not** recorded as a failed attempt (that rule cost a run on 2026-10-23): the OOM is
recorded as an admission datum, then the same entrant is re-admitted at the largest `-ngl` that loads,
and *that* number goes in the row's compute-path column. A row always states the `-ngl` it ran at.

## 3. Tenancy, mapped to mechanical checks

| rule | mechanical form |
|---|---|
| V1 one entrant resident | exactly one `llama-server` apart from the resident seats per run; server pid recorded |
| V2 resident brain untouched | `prism-brain.service` / `:58595` never stopped, restarted or reconfigured; health polled before and after each run |
| V3 no parallel cabinets | one cabinet subprocess at a time, sequential loop, no concurrency anywhere in the driver |
| V4 release is part of the run | terminate → port must refuse connections → `nvidia-smi` `memory.used` must return to the baseline sampled at suite start (±5 MiB) |
| V5 Arcade outranks | if a listener appears on the Arcade's port mid-run the suite stops rather than contends |

Baseline VRAM is **sampled at suite start and recorded with each run**, rather than assumed to be the
1,731 MiB quoted in the card (the card and the live box differ by 10 MiB, and which is right is a
measurement, not an argument).

## 4. Cabinets in this window, fixtures, prompts

Sequencing per the card: Mastermind and Lights Out first. Within the window each entrant is loaded
**once** and runs both cabinets back to back — one resident entrant at a time, cabinets sequential,
which satisfies both V1 and V3 and costs one load instead of two. The 3B floor runs first, so both
cabinets are harness-validated on the cheapest entrant before any 9B number is believed.

### 4a. Mastermind

- instrument `probes/mastermind/mastermind_run_onefile.py` sha256 `3bc8e7685522ffa3…` — **unmodified**
- fixture `probes/mastermind/mastermind_secrets_16.txt` sha256 `ccae01aecd7c9828…`, set
  `chair-mm-16-20261023`, 16 secrets fixed and published on 2026-10-23
- game 4 pegs × 6 colours (0-5), repeats allowed, 1,296 codes, limit 10 guesses
- `--max-tokens 512`, temperature 0.0, thinking off, prompt round-trip check **on**
- the run is invalid unless `--control` scores 16/16 on the fixture in this same window; the control
  is re-run once at the start of the window and once at the end

**I1 disposition (the `(no guesses yet)` literal).** The registered renderer emits that literal only
on turn 1, and it was toggled on this box on 2026-10-25 (`prompt_toggle_probe.py`, 66 calls, 3 reps,
resident 9B seat, artifact `~/workspace/chair-link/artifacts/2026-10-25-mastermind-prompt-toggle/`):
at turn 1 all four literals — shipped `(no guesses yet)`, `(none)`, `(empty)`, and absent — return
`(0,0,0,0)`; the answer moves **only** at mid-game states where the real history block is removed.
So on this prompt the literal is **not** a live variable at its only turn. The prompt is therefore
**pinned byte-identical** to the registered one (I3), which also keeps these rows comparable with the
published CPU rows. A fixed-prompt arm is a different registration and is not claimed here.

### 4b. Lights Out

- instrument `probes/lightsout/arm2_3x3_same_conditions.py` sha256 `7b3f304e7b243162…` — **imported
  and parameterised only** (base URL, model, output path); its prompt and its scoring code are the
  registered ones, unmodified
- fixture `probes/lightsout/3x3_fixture_16_boards_20261022.json` sha256 `851976c57068bca9…`, 16
  boards, all-off excluded by construction, labels recomputed from the press matrix at run time
- rung 3×3, `MAX_TOKENS 256`, temperature 0.0, thinking off, directive answer contract
  (`PRESSES:` / `CLAIM:`), 16 boards × 1 pass
- 3×3 has rank 9, nullity 0: **every** board is solvable and the solution is unique, so a constant
  `CLAIM: UNSOLVABLE` scores 0/16 by construction — unlike 4×4 where the same constant scores 93.75%
  on a random board.

## 5. Criteria and decision rules (pre-registered)

**Mastermind, per entrant over 16 games / 160 turns**
primary `wins/16` — a win is a guess equal to the secret at turn ≤ 10, i.e. verified against state,
not against the model's own claim. Secondary, all reported: `answered` turns, `consistency` (% of
answered turns that do not contradict feedback already shown), `distinct_guesses`, `modal_guess`
share, `no_answer` turns, `ended` reasons. Never collapsed into one score.
*Separation rule:* two entrants are separated only if win counts differ, or one's consistency is ≥2×
the other's with both having ≥100 answered turns. Anything else is filed as **not separated at
n=16**, and a 0/16 is filed as a clean negative, not a rate.

**Lights Out, per entrant over 16 boards**
primary `CORRECT/16` — verified by applying the presses to the state, never by reading `CLAIM:`.
Secondary: `distinct_answers/16`, `FALSE_SUCCESS`, `FALSE_UNSOLVABLE`, `UNATTRIBUTABLE`,
`answer_block present`, `completion_tokens`, wall seconds.
*Separation rule:* correct counts must differ. Two entrants with identical verdict vectors are filed
as **not separated**, even if one took longer.

**Cross-cabinet, per entrant:** a matrix of the two primary outcomes. No composite ranking is computed.

## 6. Budget and clock

- generation clock is the **server's** `timings.predicted_per_second` where the endpoint reports it;
  otherwise the client wall clock, and the row says which. The two differ by ~12% on this box and a
  row that does not name its clock is not comparable.
- `max_tokens` is pinned per cabinet and identical across entrants (512 / 256), so the variable that
  moves between rows is the model. **Consequence:** these rows are *not* directly comparable with the
  published Spark rows in `MASTERMIND_RESULTS.md`, which ran at 256 — that comparison is confounded on
  budget and on compute path. The one clean published comparison available is the Bonsai-9B CPU row
  (same prompt, same 512 budget, `-ngl 0`), which this window re-runs on GPU as a **new row**, never
  as a replacement.

## 7. What this suite cannot separate

- **Class from quantisation.** The four entrants differ in family, size *and* bit-width (Q4_K_XL,
  Q4_K_M, Q4_K_M, PQ2_0/Q8_0). A result that holds across all four licenses a claim about "small
  local models"; a split between the two Q4 9Bs licenses nothing about size until bit-width is held
  fixed, and the Bonsai-vs-Q4 9B pair is a 2.13 bpw-vs-4.5 bpw difference, not a family difference.
- **Capability from interface.** One prompt per cabinet. A model that cannot parse the answer contract
  and a model that cannot solve the puzzle produce the same failed row; the `no_answer`/`parse_path`
  columns separate them per row, but the suite does not re-prompt to find out.
- **Capability from size at n=16.** 16 games/boards is enough for a clean 0/16 negative and a clean
  16/16 positive; it is not enough to order two entrants that score 1–3.
- **Anything about the four entrants on the cabinets not run in this window** (Sokoban, Zork, Snake,
  Labyrinth, Chess). Silence there is silence, not a negative.

## 8. Acceptance for this window

1. the Mastermind control passes 16/16 twice (window open and window close);
2. one row file per (cabinet, entrant), each row carrying the entrant's compute path (binary build,
   `-ngl`, ctx, cache types, `/props` `model_ftype`, slots) and its VRAM attribution;
3. every released entrant: no listener on 58701, `prism-brain` health 200, VRAM back to the sampled
   baseline;
4. one results table per cabinet, with a compute-path column naming the path each row ran on, and the
   published CPU rows visible beside the GPU rows, never merged into them;
5. an explicit statement of §7 in the results, not in a footnote.
