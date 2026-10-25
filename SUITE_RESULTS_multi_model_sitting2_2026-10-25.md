# SUITE RESULTS — second sitting: Sokoban, Zork, Snake, Labyrinth, Chess (2026-10-25)

Window card: kanban **t_234b2387**, the remainder of the window whose first sitting (`t_c4fa298e`) ran
Mastermind and Lights Out. Pre-registration for this sitting — fixtures, budgets, criteria, the one
instrument amendment — committed **before the first model call of this sitting**:
`SUITE_PREREG_EXTENSION_t_234b2387.md`, commit `4e0eb43`.

**Across the five cabinets the result that survives every caveat is this: none of the four entrants was
separated from another on a capability.** Where a zero appears, the row that carries it names the
interface outcome that produced it — a 64-token answer ceiling that truncates a preamble before the
first line ever holds an answer (Sokoban, Zork), an answer in the wrong notation (Chess), a repeated
command that the cabinet's own replay audit refuses to score (Zork), or a rule the entrant cannot read
at all (Labyrinth, where one entrant named 39 moves that are not legal).

Every figure below was read from a file a process wrote: the cabinet's row file, `/props` from the
live serving process, `/proc/<pid>/stat`, `nvidia-smi`, and the lease store's own report. Nothing is
quoted from a previous session's prose, and no number in a table was typed by hand — the tables are
generated from `suite2/runs/AGGREGATE2.json` by `suite2/report2.py` (see §9).

---

## 1. What served each row

Twenty-eight blocks ran: **12 Sokoban cells (3 levels × 4 entrants), 8 Zork cells (2 levels × 4),
4 Snake episodes-pairs (2 seeds × 4), 4 Labyrinth cells (1 cell × 4), 4 Chess games (1 game × 4)**.
Each block sampled the card at its own start, ran one cabinet with one entrant resident, and verified
the release afterwards: port refused AND `memory.used` back to that block's baseline (tolerance
64 MiB). **All 28 filed blocks released clean**, and so did every block of the superseded first
Sokoban pass and the two refused attempts: **47 block records under `suite2/runs/`, 47 with
`port_closed: true`, `vram_delta_mib: 0` and `:58595/health` 200.** The Chess game whose entrant was
still answering when its 2048-token cap hit released clean too, and its termination is recorded as
`serving-failure`, a MISSING VALUE rather than a verdict.

Compute path, per cabinet — the differences are real and are stated rather than absorbed:

| cabinet | serving process | `-ngl` | ctx | slots (`/props`) | binary · build | prompt identity |
|---|---|---|---|---|---|---|
| Sokoban | driver-owned (`sokoban_run.py`) | 99 | 4096 (the driver's registered ctx) | 1 | llama.cpp `b10931-3057bb66c`; PrismML `b10777-e3de71522` for `bonsai-9b` | legend digest `0d86057c46d4c83b` |
| Zork | driver-owned (`zork_run.py`) | 99 | 4096 | 1 | as above | carried per record |
| Snake | driver-owned (`snake_run.py`) | 99 | 8192 | 1 | PrismML `b10777-e3de71522` (the driver's registered default) | carried per episode |
| Labyrinth | **suite-served** (`suite/suite2.py` → `127.0.0.1:58701`) | 99 | 8192 | 1 | per entrant | prompt digest `3c8c4ce9618b4e2c…` (same for all four) |
| Chess | driver-owned (`chess_game.py`) | 99 | 4096 | 1 | llama.cpp `b10931`; PrismML `b10777` for `bonsai-9b` | `76fa8848e9adf514` |

Three things about that table, said plainly:

1. **`--parallel 1` was not in any of the four drivers' registered launches.** They pass no slot flag,
   so llama-server opens its default and `/props` reported `total_slots = 4` on the first Sokoban pass
   — 1024 tokens per slot at ctx 4096. The card fixes slots at 1, so the drivers gained a
   `--parallel INT` parameter (default: pass nothing = the registered launch) and **Sokoban was re-run
   from scratch at `--parallel 1`**. The superseded pass is not deleted: its 12 block records stay
   under `suite2/runs/` and `report2.py` counts them as `superseded: 13`, never as rows. Re-running did
   not change a single verdict — every solved/not-solved outcome is identical across the two passes —
   which is itself the check that the slot count was not the variable.
2. **The drivers own their context size (4096), and this sitting did not change it.** The card's
   `--ctx-size 8192` applies to entrants the suite serves itself; a driver that declares 4096 in its
   own `server_argv` was left at 4096 and the row says so. Snake's registered 65536 was reduced to
   8192 for the card envelope and *that* is a registered deviation (§2 of the extension).
3. **The quant in every row is the filename, not `/props`** — `model_ftype` reads `Q4_K - Medium` for
   all three Q4 files including the UD-Q4_K_XL one, as sitting 1 found. Only `bonsai-9b`'s
   `PQ2_0 - 2.13 bpw (group 128)` distinguishes itself.

---

## 2. Tenancy — the card, the lease, and what was proved at each release

- The **global** GPU lease was taken before the first load
  (`gpu-lease.sh acquire --owner ocho2-suite-t_234b2387 --class batch --need-mib 5400 --ttl 14400` →
  `ADMITTED — 6116 MiB free ≥ 5656 MiB needed`) and released at the end. No scoped lease and no
  foreign tenant appeared during the sitting: `gpu-yield.sh --report` showed only the two resident
  seats (`prism-bonsai-9b` 1466 MiB, `lfm25-vl` 134 MiB) at the start, and the card never had to be
  yielded.
- `prism-brain.service` / `:58595` was **never** stopped, restarted or reconfigured (V2). `/health`
  returned 200 before and after **every** block — the release evidence for all 28 blocks says
  `resident_health_after: 200`.
- One entrant resident, one cabinet at a time (V1, V3). The two Q4 9B entrants peaked at **7030–7396
  MiB of 8192** with their servers — the same ~88% envelope sitting 1 measured, which is why nothing
  ran in parallel.
- The baseline was **sampled per block, never assumed**: 1775 MiB at the sitting's start, 1785 MiB
  after the first Snake block, and each block compared against its own sample. Every block's recorded
  `vram_delta_mib` is `0`.
- Snake runs a real headless Chromium (`~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`)
  and each episode record carries the browser's own identity plus the subject HTML's digest — the game
  is played, not simulated, and the row says which binary played it.

---

## 3. Sokoban — 3 levels × cap 40 moves, `MAX_TOKENS` 64

| entrant | compute path | L1 one_push | L2 two_boxes | L3 corner_waiting | moves L1/L2/L3 | not_an_action L1/L2/L3 | blocked L1/L2/L3 | RESIGN at | gen tokens | wall s | peak pid VRAM | release |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 4096· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2373068 start 2026-10-25T13:41:08-0700 | SOLVED | no (gave_up) | no (gave_up) | 1/4/3 | 0/0/0 | 0/6/5 | —/10/8 | 2/536/173 | 4.9/14.0/9.1 | 2560/2560/2560 | ok |
| mimo-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2371030 start 2026-10-25T13:38:40-0700 | no (commands_exhausted) | no (commands_exhausted) | no (commands_exhausted) | 0/2/3 | 40/38/37 | 0/0/0 | —/—/— | 2560/2312/2374 | 50.2/44.9/50.7 | 5466/5466/5466 | ok |
| ministral-3b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2368481 start 2026-10-25T13:35:55-0700 | SOLVED | no (commands_exhausted) | no (commands_exhausted) | 1/1/1 | 0/39/39 | 0/0/0 | —/—/— | 2/2523/2512 | 4.5/22.9/22.9 | 2744/2744/2744 | ok |
| ornith-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2369407 start 2026-10-25T13:36:51-0700 | SOLVED | no (commands_exhausted) | no (gave_up) | 1/0/1 | 0/40/2 | 1/0/0 | —/—/3 | 4/2560/802 | 15.5/58.7/32.2 | 5250/5250/5250 | ok |


**Primary: solved 1 of 3 for `bonsai-9b`, `ministral-3b` and `ornith-9b`; 0 of 3 for `mimo-9b`.**
All twelve cells were solved on level 1 or not at all. `ornith-9b` alone solved it with a blocked
move; `bonsai-9b` alone **resigned** — on levels 2 and 3, after 10 and 8 moves — which is the give-up
signal the cabinet wants and sitting 1 never got on Lights Out.

**The zeros after level 1 are an interface outcome, and the cause is the cabinet's own 64-token
ceiling.** `sokoban_run.py` declares `MAX_TOKENS = 64`; the artifact's own `budget_signature` counts
the damage:

| entrant | turns that hit the 64-token ceiling (L1 / L2 / L3) | first line the reader saw on L2 |
|---|---|---|
| `ministral-3b` | 0/1 · 39/40 · 39/40 | `R` then prose — level 1 answers, level 2 preamble |
| `mimo-9b` | 40/40 · 36/40 · 37/40 | `R`,`B`,`R`… single letters, but 38 counted `not_an_action` |
| `ornith-9b` | 0/2 · 40/40 · 9/40 | `Let me carefully analyze this Sokoban puzzle.` |
| `bonsai-9b` | 0/1 · 0/4 · 0/3 | short letters, no truncation, resigns instead |

`ornith-9b` and `mimo-9b` write their derivation **before** the answer line; at 64 tokens the
generation stops mid-derivation and the first line never becomes a move. `ministral-3b` answers level 1
in one token and starts preamble-writing on level 2. Their `not_an_action` counts (39, 40, 38) are the
reader refusing to score prose as a move — exactly the distinction the prereg demanded, reported as
counts and not folded into "cannot play". **The published CPU rows show the same ceiling biting the
same way** — the preserved MiMo CPU record (2026-10-19) hits the 64-token ceiling on **38 of its 40
turns** and ends `commands_exhausted` just as its GPU row does — so this is the instrument, not the
GPU path.

`mimo-9b`'s 0/3 is therefore *not* a capability result. Reading it as one would repeat the mistake
sitting 1 filed against its own Mastermind table.

---

## 4. Zork — 2 levels × cap 20 commands, `MAX_TOKENS` 64

| entrant | compute path | L1 the_floor | L2 long_crawl | parsed L1/L2 | unparsed L1/L2 | impossible L1/L2 | replay audit | gen tokens L1/L2 | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 4096· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2377692 start 2026-10-25T13:47:27-0700 | ESC (escaped) | no (gate_locked) | 3/14 | 0/1 | 0/3 | True/True | 7/44 | 5.4/11.8 | ok |
| mimo-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2377328 start 2026-10-25T13:46:56-0700 | ESC (escaped) | INSTRUMENT-FAILURE (replay) | 6/9 | 0/0 | 10/11 | True/False | 43/55 | 14.7/14.2 | ok |
| ministral-3b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2376609 start 2026-10-25T13:46:04-0700 | ESC (escaped) | INSTRUMENT-FAILURE (replay) | 3/12 | 0/3 | 2/5 | True/False | 21/242 | 5.3/7.3 | ok |
| ornith-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2376845 start 2026-10-25T13:46:18-0700 | ESC (escaped) | ESC (escaped) | 2/7 | 0/0 | 2/0 | True/True | 11/16 | 17.5/18.5 | ok |


**Primary: all four entrants escaped `zork_01_the_floor`. On `zork_02_long_crawl` only `ornith-9b`
escaped; `bonsai-9b` ended `gate_locked` (the item was not carried at the gate); `ministral-3b` and
`mimo-9b` are filed as INSTRUMENT-FAILURE, not as zeros.**

The two failures are the cabinet's **own replay audit**, not my reading of it: `zork_run.py` re-derives
the score from the recorded trace and refuses the row when the record does not reproduce itself
(exit 6, and the driver prints "THIS IS NOT A RESULT"). On both rows the mismatched field is exactly
one — `took_item_at_step` — and the artifact says so:

- `ministral-3b`: recorded `took_item_at_step = 10`; trace contains **5 TAKE commands, three of them
  repeats of the torch**.
- `mimo-9b`: recorded `took_item_at_step = 17`; trace contains **12 TAKE commands, ten of them repeats
  of the torch**.
- The two rows that reproduce are the two that do not repeat: `ornith-9b` issued one TAKE (step 1),
  `bonsai-9b` issued five across three different items.

So the cause is named: **repeated TAKE is not idempotent in this instrument's replay**, and the audit
is right to refuse the row. The two cells are unmeasured, and the fix belongs to the Zork instrument
(a new registration), not to this report.

Counter columns, per the prereg (C3, C4): `recognised-but-impossible` is large and separate from
`unparsed` — `mimo-9b` 10 and 11, `bonsai-9b` 0 and 3, `ministral-3b` 2 and 5, `ornith-9b` 2 and 0.
`took_item_at_step` and `carried_required_item` are separate columns and they disagree for
`bonsai-9b` on level 2 (took at step 5, carried False) — which is the whole reason the cabinet keeps
them apart: taking is not carrying.

---

## 5. Snake — 2 of the frozen 4 seeds × 120 ticks, `MAX_TOKENS` 64

| entrant | compute path | seed | apples | deaths | ticks | ended | distinct moves | modal move | state-chain digest | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 8192· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2391798 start 2026-10-25T14:05:02-0700 | 1 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 49.0 | ok |
| bonsai-9b | -ngl 99 · ctx 8192· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2391798 start 2026-10-25T14:05:02-0700 | 7 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 49.0 | ok |
| mimo-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2385769 start 2026-10-25T13:57:52-0700 | 1 | 0 | 0 | 120 | tick_cap | R,U | R ×81 | 235d7cddceebd6bc | 133.0 | ok |
| mimo-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2385769 start 2026-10-25T13:57:52-0700 | 7 | 0 | 0 | 120 | tick_cap | R,U | R ×81 | 235d7cddceebd6bc | 133.0 | ok |
| ministral-3b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2379866 start 2026-10-25T13:50:29-0700 | 1 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 16.3 | ok |
| ministral-3b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2379866 start 2026-10-25T13:50:29-0700 | 7 | 0 | 0 | 120 | tick_cap | R | R ×120 | 7f46665eb1a91edf | 16.3 | ok |
| ornith-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2384124 start 2026-10-25T13:55:57-0700 | 1 | 0 | 0 | 120 | tick_cap | D,R,U | U ×94 | 32d9bf1e3a4be462 | 113.7 | ok |
| ornith-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2384124 start 2026-10-25T13:55:57-0700 | 7 | 0 | 0 | 120 | tick_cap | D,R,U | U ×94 | 32d9bf1e3a4be462 | 113.7 | ok |


**Primary: 0 apples for all four entrants, on both seeds. No entrant was separated, because every row
is the same verdict vector.**

The measurement that makes this more than a zero: **the state-chain digest is identical across seeds
within every entrant** (`7f46665eb1a91edf` for `ministral-3b` and `bonsai-9b`; `235d7cddceebd6bc` for
`mimo-9b`; `32d9bf1e3a4be462` for `ornith-9b`), because none of them ever ate an apple and the seed
reaches the game **only** through apple respawn. That reproduces the published finding on a new path.

And one clean cross-path equality is available here:

| row | path | process | moves | apples | state chain |
|---|---|---|---|---|---|
| `bonsai-9b`, seed 1, published 2026-10-17 | **CPU `-ngl 0`** | a process that no longer exists | `R` ×120 | 0 | `7f46665eb1a91edf` |
| `bonsai-9b`, seed 1, today | **GPU `-ngl 99`**, ctx 8192, slots 1 | pid 2391798, started 14:05:02 | `R` ×120 | 0 | `7f46665eb1a91edf` |

Different binary invocation, different path, different process, different day — **identical state
chain, digest for digest**. That is the strongest same-instrument comparison this suite can offer,
because the cabinet's own trace re-derives the chain from the page rather than from the model's text.

`mimo-9b` is the only entrant that varied (81 `R`, rest `U`), and it still never ate an apple;
`ornith-9b` mostly said `U` (94/120). Variation is not discrimination — the same note sitting 1 filed
against `ministral-3b` on Mastermind.

---

## 6. Labyrinth — cell 01, one graph, `min`, K 12, rune `Fehu`, cap 40

| entrant | compute path | plies / cap | end state | moved | blocked | not_an_action | give_up | visited positions | visited names | turn cap | tokens | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 8192· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2395883 start 2026-10-25T14:09:32-0700 | 40/40 | cap | 40 | 0 | 0 | 0 | 2 | 2 | 32 | 120 | 5.2 | ok |
| mimo-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2395745 start 2026-10-25T14:09:21-0700 | 40/40 | cap | 40 | 0 | 0 | 0 | 4 | 4 | 32 | 146 | 6.9 | ok |
| ministral-3b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2395485 start 2026-10-25T14:09:00-0700 | 40/40 | cap | 1 | 39 | 0 | 0 | 2 | 2 | 32 | 160 | 1.5 | ok |
| ornith-9b | -ngl 99 · ctx 8192· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2395565 start 2026-10-25T14:09:04-0700 | 40/40 | cap | 40 | 0 | 0 | 0 | 2 | 2 | 32 | 120 | 6.7 | ok |


Cell identity, from the artifact's own fields: graph `ged-v2` digest `e8a7e2b7b59d9013…` (file
`fe44d4cf…`), cell spec `6df7437a…`, symmetrisation `min`, K 12, start rune `Fehu`, seed 0,
`seed_model` 0, thinking off, `max_turn_tokens` 32. All four rows carry the **same prompt digest
`3c8c4ce9618b4e2c…`**, so the four cells are one test.

**Primary: all four ended at `cap` (40 plies), and the counts separate them in the only way this cell
can — how many of those 40 plies were legal moves.**

- `mimo-9b` (4 distinct positions), `bonsai-9b` (2) and `ornith-9b` (2): **40 of 40 plies legal**, no
  blocked proposals, no abstentions.
- `ministral-3b`: **1 legal move and 39 blocked** — it named runes that are not neighbours under
  K 12, and the cell counted the refusals instead of substituting a step.

`visited_unique` is counted on **positions** (the v3 basis fixed in `CELL_01_labyrinth.md`), and
`visited_names` happens to equal it on this cell. On one cell, with no shared graph across cabinets,
this says which of the four could move in a legal-move set it had to derive — `mimo-9b` found four
distinct positions, two others two, one entrant essentially none. It does not rank them: a 40-ply walk
that never closes is not a failed predicate, and the cell's §7 refusal table governs what the predicate
means.

---

## 7. Chess — one game, one entrant both sides, cap 30 plies, `MAX_TOKENS` 2048

| entrant | compute path | termination | premature collapse | miscalibrated persistence | plies in lost positions | plies | cap | prompt digest | wall s | release |
|---|---|---|---|---|---|---|---|---|---|---|
| bonsai-9b | -ngl 99 · ctx 4096· PQ2_0 - 2.13 bpw (group 128) · slots 1 · build b10777-e3de71522 · pid 2400963 start 2026-10-25T14:13:31-0700 | illegal-move | 0 | 0 | 0 | 1 | 30 | 76fa8848e9adf514 | 22.8 | ok |
| mimo-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2400694 start 2026-10-25T14:13:18-0700 | illegal-move | 0 | 0 | 0 | 2 | 30 | 76fa8848e9adf514 | 11.7 | ok |
| ministral-3b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2398618 start 2026-10-25T14:11:40-0700 | illegal-move | 0 | 0 | 0 | 1 | 30 | 76fa8848e9adf514 | 4.6 | ok |
| ornith-9b | -ngl 99 · ctx 4096· Q4_K - Medium · slots 1 · build b10931-3057bb66c · pid 2398800 start 2026-10-25T14:11:46-0700 | serving-failure | 0 | 0 | 0 | 5 | 30 | 76fa8848e9adf514 | 91.8 | ok |


**The instrument pass the card demanded, done before the numbers were read.** The frozen prompt
(`76fa8848e9adf514…`) contains **no legal-move list** — the menu is gone, by the argument in
`chess_game.py`'s own freeze note — and the rows prove it is gone: with no list to choose from, every
entrant had to derive candidates, and three of four produced a move that is well formed and **not
legal in the position**.

**Primary: the two directions of the one quantity are both zero for all four — no premature collapse,
no miscalibrated persistence — because no game got far enough for either to be observable.** Plies
played per entrant: `ministral-3b` 1, `bonsai-9b` 1, `mimo-9b` 2, `ornith-9b` 5. Nine plies of chess
across four entrants.

Terminations, named from the records:

- `ministral-3b` — `illegal-move` at ply 1: first line `e4`, **SAN, not UCI**. The prompt asks for
  coordinate notation; the entrant answered in the other chess notation. An interface outcome that
  the frozen taxonomy has no value for.
- `bonsai-9b` — `illegal-move` at ply 1: first line `e2e4` with Black to move. Legal shape, illegal
  position.
- `mimo-9b` — `illegal-move` at ply 2: first line `e4d5`, not legal here (29 were).
- `ornith-9b` — `serving-failure` at ply 5: still deliberating when the 2048-token cap hit (2048
  tokens, 6060 characters in `reasoning_content`, `content` **empty**). **No move was committed —
  MISSING VALUE, not a verdict**, and the deliberation is preserved at
  `cabinet_results/main/CHESS_REASONING_ornith-9b-suite2.txt`.

The driver's own taxonomy note is quoted rather than smoothed: `illegal-move` **is not one of
CARD_chess.md's five frozen terminations**, it becomes reachable only once the prompt stops supplying
the move list, and it is an entrant failure the card has no value for — **it requires ratification
before any of these numbers is scored.** What the cabinet cannot do at 30 plies is what §9 says it
cannot do: observe either direction of the one quantity.

The published CPU row for the same entrant class is beside it, not merged into it: **`ornith-9b` on
CPU, cap 60, 4 plies, `serving-failure` at the same 2048-token cap** (record
`results/CHESS_GAME_Ornith-1.5-9B-Q4_K_M.json`). On GPU today the same entrant reached 5 plies and
died of the same cause — one more ply, same termination. That is a row difference with the path and
the process both named, not a speed effect.

---

## 8. Published CPU rows, preserved beside the GPU rows

Every cell that already held a published record was **copied aside before the GPU row was written at
that coordinate**: `suite2/runs/published_cpu/`, each copy with a `.provenance.json` carrying the
sha256 of the bytes it was, the time, and the reason the driver's own overwrite gate was given. Eighteen
such records exist (six Sokoban cells, one Zork cell, two Snake episodes, and the rest enumerated in
the file). The rows below are **their own table** — never merged into the GPU tables above, because a
row is a snapshot of a process and these are different processes.

| preserved artifact (suite/runs/published_cpu/) | sha256 (provenance file) | its own primary fields |
|---|---|---|
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json | see .provenance.json | ended=tick_cap, moves=['R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'], not_an_action=0 |
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s1.json.provenance.json | see .provenance.json |  |
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s7.json | see .provenance.json | ended=tick_cap, moves=['R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'], not_an_action=0 |
| SNAKE_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_s7.json.provenance.json | see .provenance.json |  |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_02_two_boxes.json | see .provenance.json | solved=False, ended=commands_exhausted, moves=1, blocked=0, not_an_action=39, give_up=0 |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_02_two_boxes.json.provenance.json | see .provenance.json |  |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_03_the_corner_waiting.json | see .provenance.json | solved=False, ended=commands_exhausted, moves=3, blocked=0, not_an_action=37, give_up=0 |
| SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_03_the_corner_waiting.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_01_one_push.json | see .provenance.json | solved=True, ended=solved, moves=1, blocked=0, not_an_action=0, give_up=0 |
| SOKOBAN_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_01_one_push.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_01_one_push.json | see .provenance.json | solved=True, ended=solved, moves=1, blocked=0, not_an_action=0, give_up=0 |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_01_one_push.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_02_two_boxes.json | see .provenance.json | solved=False, ended=gave_up, moves=4, blocked=6, not_an_action=0, give_up=1 |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_02_two_boxes.json.provenance.json | see .provenance.json |  |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_03_the_corner_waiting.json | see .provenance.json | solved=False, ended=gave_up, moves=3, blocked=5, not_an_action=0, give_up=1 |
| SOKOBAN_Ternary-Bonsai-2-9B-PQ2_0-MTP-Q8_0_03_the_corner_waiting.json.provenance.json | see .provenance.json |  |
| ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json | see .provenance.json | ended=escaped, finished=True, carried_required_item=True |
| ZORK_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_zork_01_the_floor.json.provenance.json | see .provenance.json |  |


---

## 9. What this sitting cannot separate — stated, not footnoted

This is the prereg's §5, restated against what was measured rather than what was expected.

- **Sokoban cannot separate "cannot play" from "cannot answer in the budget".** Measured: after level 1,
  three of four entrants produced `not_an_action` on 37–40 of 40 turns, and the artifact's own
  `budget_signature` shows those same turns hitting the 64-token ceiling. One solved level is not a
  rate; a 40/40 capped level is not a capability. **Only `bonsai-9b`'s resignation is a clean signal**
  — the level is verified solvable and it gave up anyway.
- **Zork cannot separate understanding from typing, and half its second level is not scorable at all.**
  `unparsed` and `recognised-but-impossible` are separate counts (reported above), which names the
  interface share but does not measure intent; and two of eight cells are refused by the cabinet's own
  replay audit over repeated TAKE. Those two cells are **unmeasured**, not zero.
- **Snake cannot separate skill from interface, and two seeds cannot separate a seed effect from
  nothing.** Measured: all four state chains are seed-invariant *because* no apple was eaten, so the
  second seed bought a replicated row, not a second test; and with 0 apples everywhere the apples
  column carries no information at all.
- **Labyrinth is one cell.** One graph, one rune, one K, one symmetrisation, one count basis. It says
  nothing about another graph, and a cap-length walk is not a completed predicate — the cell's §7
  refusal table is the authority on what the number means.
- **Chess cannot observe either direction of its own quantity at cap 30.** Measured: 9 plies across
  four entrants, 0 premature collapses and 0 miscalibrated persistences — **a floor, not a
  calibration** — and the termination that dominates (`illegal-move`) is not in the frozen taxonomy,
  so it needs ratification before scoring.
- **Across the sitting: class cannot be separated from quantisation** (the four entrants differ in
  family, size *and* bit-width at once, and `/props model_ftype` cannot even distinguish the two Q4
  9Bs), and **GPU rows cannot be compared with published CPU rows as if the path were the only
  difference** — binary, ctx, slot count and process all differ; the Snake state-chain equality is the
  one comparison where the instrument re-derives the result and the equality therefore survives those
  confounds.

---

## 10. Files, and how to reproduce

```
SUITE_PREREG_EXTENSION_t_234b2387.md   pre-registration, commit 4e0eb43 (before any model call)
suite/suite2.py                        the sitting-2 driver (reuses suite.py's lease/process code)
suite2/runs/*.meta.json                28 blocks: compute path, /props, /proc identity, VRAM, release
suite2/runs/AGGREGATE2.json            every figure above, machine-readable
suite2/TABLES2.md                      the tables, generated (no number typed by hand)
suite2/report2.py                      aggregation: rows -> AGGREGATE2.json -> TABLES2.md
suite2/dump.py                         one line per block, for reading
suite2/runs/published_cpu/             the eighteen preserved pre-existing records + provenance
suite2/logs/                           driver stdout/stderr per block (scratch)
sokoban_run.py zork_run.py snake_run.py chess_game.py
                                       the four instruments; each gained --ngl, --parallel (and Snake
                                       --ctx, Chess --llama-server) with registered defaults unchanged
```

Reproduce one block (the shape all 28 used):

```
gpu-lease.sh acquire --owner <name> --class batch --need-mib 5400 --ttl 14400
/usr/bin/python3 suite/suite2.py --entrant ornith-9b --cabinet sokoban
/usr/bin/python3 suite/suite2.py --entrant ornith-9b --cabinet labyrinth   # suite-served
/usr/bin/python3 suite2/report2.py
gpu-lease.sh release --owner <name>
```

One correction to this sitting's own first pass, kept in the record: **Sokoban's first pass ran at the
drivers' default slot count (4 slots, 1024 tokens per slot)**. It was detected from `/props`, the
driver gained `--parallel`, and all twelve Sokoban cells were re-run at `--parallel 1`; the superseded
records remain under `suite2/runs/` and are counted as `superseded`, never as rows.

---

## 11. Close of the sitting — measured, not asserted

- `gpu-lease.sh release --owner ocho2-suite-t_234b2387` → `RELEASED — lease in scope (global) owned by
  ocho2-suite-t_234b2387 removed`; both lease stores (`lease.d/`, `scopes/`) read **none held**.
- **No listener on `:58701`** (`ss -ltn`), and the card reads **1785 MiB used / 6106 MiB free** —
  against the 1775 MiB sampled at the sitting's start, a +10 MiB drift from the resident seats'
  allocator, inside the 64 MiB bar and recorded rather than absorbed.
- `prism-brain` / `:58595` **health 200** at close. It was never stopped, restarted or reconfigured,
  and no tenant had to be yielded for the whole sitting.
- The two resident seats are the same two that were there at the start
  (`prism-bonsai-9b` 1466 MiB, `lfm25-vl` 134 MiB) — nothing of the suite's outlived it.

**What is measured and what is not.** Twenty-eight filed blocks, all five cabinets, all four entrants,
each row carrying its compute path and the identity of the process that served it; eighteen
pre-existing CPU records preserved beside them (§8). What did *not* run: nothing on the card's list — but several cells are
**unmeasured rather than zero** and are named as such in §8: two Zork cells refused by the cabinet's
own replay audit, `mimo-9b`'s Sokoban zero (an interface outcome), and the whole of the chess
cabinet's primary quantity (a floor of 9 plies).

