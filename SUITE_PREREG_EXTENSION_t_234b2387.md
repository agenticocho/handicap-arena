# PREREG EXTENSION — multi-model cabinet suite, second sitting (t_234b2387), 2026-10-25

Extends `PREREG_multi_model_suite_20261025.md` (commit `86aaa24`) to the five cabinets the first
sitting did not run: **Sokoban, Zork, Snake, Labyrinth, Chess**. Committed **before the first model
call of this sitting**. Nothing in the earlier document is re-opened: entrants, binaries, tenancy
rules V1–V5, and instrument lessons (a)–(d) carry over verbatim.

This document does three things the first one did not have to: it names the **fixtures and budgets**
for five cabinets, it records **one instrument amendment** and why it is a compute-path amendment
rather than a prompt amendment, and it fixes **what each cabinet cannot separate** before any number
exists.

---

## 1. Why the four driver-owned cabinets needed a compute-path parameter

Sokoban, Zork, Snake and Chess are *driver-owned* cabinets: the driver launches its own `llama-server`
(`sokoban_run.py`, `zork_run.py`, `snake_run.py`, `chess_game.py`) and each hard-coded its launch as
`-ngl 0` (CPU) at `ctx 4096` (Snake at `ctx 65536`). Labyrinth already takes `--base-url`, so the suite
serves it itself and no amendment is needed there.

Read literally, `-ngl 0` is the **registered** launch of those four instruments. Read against this
window's card (`--n-gpu-layers 99`, one entrant at a time, GPU rows), leaving it at 0 would have
produced four CPU cabinets — and at the measured 6.32 tok/s a single 30-ply chess game is hours, so
"run them as registered" is not a slower path to the same rows, it is no rows at all.

**Amendment (this sitting only, recorded per row):** each of the four drivers gained
`--ngl INT` (default = its registered value, `0`), Snake additionally `--ctx INT` (default = its
registered `65536`), and Chess additionally `--llama-server PATH` (its siblings already had one; the
Bonsai ternary seat needs the PrismML fork and would otherwise emit token salad).

What is **not** changed: no prompt string, no parser, no scorer, no fixture, no oracle, no cap, no
observation channel. The defaults reproduce every previously published launch byte for byte, so no
existing record is re-scored or invalidated. The flag only travels into the argv handed to `exec`, the
argv is written into the row, and the row states the path it ran on. This is the same variable class
as `--llama-server` (already a flag on three of these drivers) and as `/props model_ftype`: a
**compute-path field**, which I2 requires every row to record.

Instrument identity is pinned by **file sha256 at the commit that introduced the flag**:

| instrument | sha256 (at this commit) |
|---|---|
| `sokoban_run.py` | `f484ddc5651158ac3807b6bae3520300e455d9dc38dd68adad49a6c0f01e8862` |
| `zork_run.py` | `9314edab344513ae13dd4795741e3d4967f4b00587d8147617a1893e3b775e90` |
| `snake_run.py` | `bacf6c954a1ccdbf7bcecd2ee165fe436779d79232aa74820c0547ad5af9ad0c` |
| `chess_game.py` | `b240c93415cef79d8ae23b5e0aa50bda05a657bcb308865c3e9e32744357271e` |
| `labyrinth_run.py` (unmodified) | `22caa22e8f30cd498a09fbc244a80f023cd514fdbd72885464f5b63ce496d7cb` |
| `suite/suite.py` (unmodified, imported by the wrapper) | `8a427ec990e5bb2ea0109b046c59d50744f652fcfe3c53640962c9f073ba1132` |

Each run header prints the prompt digest **taken from the artifact the run wrote**, not from this
document (lesson (d)): a changed prompt is a new registration, and the check must be mechanical.

## 2. Cabinets, fixtures, budgets — all fixed now

| cabinet | fixture (frozen) | sha256 | rung / budget | max_tokens |
|---|---|---|---|---|
| **Sokoban** | `levels/01_one_push.txt`, `02_two_boxes.txt`, `03_the_corner_waiting.txt` | `db6ca596…`, `7549657f…`, `77d18407…` | 3 levels × cap **40** moves | per driver (MAX_TOKENS declared) |
| **Zork** | `levels/zork_01_the_floor.txt`, `zork_02_long_crawl.txt` | `699ef17b…`, `c1d33b94…` | 2 levels × cap **20** commands | per driver |
| **Snake** | `snake/seeds.txt` = **1, 7** (two of the frozen four) × **120** ticks | `faade9b2…` | 2 seeds × 120 ticks = 240 turns | 64 |
| **Labyrinth** | cell 01: `ged_matrix.json` `fe44d4cf…`, sym `min`, K 12, rune `Fehu`, cap **40**, seed 0, no-think | spec `6df7437a…` | 1 cell × 40 plies | per cell |
| **Chess** | `STARTPOS`, one entrant both sides, cap **30** plies | prompt digest carried per record | 30 plies | 2048 |

**Why Snake is two seeds and not four.** The published record (SNAKE_HARNESS.md §"The seed list")
measured that the seed reaches the game *only* through apple respawn, and that episodes which never
eat an apple produce **identical state chains across seeds and across sizes**. Two seeds therefore
test the second-seed question ("was the first luck?") at half the cost; a four-seed table would add
duplicate rows, not a measurement. The cost is stated: this sitting reads 2 of the frozen 4.

**Why Chess is 30 plies and not 60.** At the measured rates a 60-ply game is 2–3× the wall clock of
every other cabinet in this sitting combined, per entrant. 30 plies is enough for the quantity the
cabinet measures in both directions (premature collapse / miscalibrated persistence) to be *observed*;
it is **not** enough to estimate a rate, which §5 says out loud.

**Chess instrument pass, run before any chess entrant number is read** (the card's sequencing rule):
(a) the frozen prompt was checked and carries **no legal-move list** — the menu defect named in the
card is not present in `PROMPT_TEMPLATE`; (b) each row carries `prompt_digest`; (c) `--probe` is run
once on the 3B floor to confirm the reader and the oracle agree about a legal move before the four
rows are taken. A chess position that arrives with its legal moves listed is not a chess position; this
one does not.

**Published CPU rows are preserved, never overwritten in place.** Four cells already hold published
CPU artifacts (`SOKOBAN_MiMo-…_02`, `_03`, `SOKOBAN_Ministral-…_01_one_push`,
`SOKOBAN_Ternary-Bonsai-2-9B-…_01/02/03`, `ZORK_Ministral-…_zork_01`, `CHESS_GAME_Ornith-…`). Before a
GPU row is written at any such cell, the existing artifact's bytes are copied to
`suite/runs/published_cpu/` with its sha256 recorded, and the driver's own `--overwrite-artifact` gate
is given that reason. The CPU record therefore survives, at a stated coordinate, and the GPU row is a
**new row beside it**, never a replacement for it.

## 3. Criteria and decision rules (pre-registered)

Per cabinet, per entrant, primary = the cabinet's **own** state check; the model's claim is a separate
column and never awards a point (I5). Secondary reported per row: `answered` / `no_answer` /
`parse_path` (or the cabinet's equivalent), turns used, tokens, wall seconds, compute path.

- **Sokoban** — primary `levels_solved / 3`, solved only when the simulator's own `play()` says the
  board is solved; `RESIGN` recorded separately (premature collapse is provable where the level's
  solution is verified). Secondary: moves, `blocked`, `not_an_action`, `give_up`, per-level trace.
  *Separation:* solved counts must differ. Equal vectors are **not separated**.
- **Zork** — primary `finished / 2` (`escaped` carrying the required item, or `gate_locked`), the
  simulator deciding; secondary `parsed` / `unparsed` / `recognised-but-impossible` and
  `took_item_at_step` vs `carried_required_item` kept apart.
  *Separation:* finished counts must differ.
- **Snake** — primary `apples eaten` over 2 seeds × 120 ticks, read from the page's own state chain;
  secondary `deaths`, `turns accepted`, distinct moves, state-chain digest per episode. The
  deterministic baselines published at 120 ticks are quoted beside, labelled as baselines, not as
  entrants. *Separation:* apples must differ; identical state chains are **not separated**.
- **Labyrinth** — primary the cell's own predicate outcome per ply (the cell's `visited_unique`
  count-basis is *positions*, per CELL_01 v3); secondary abstentions and parse path.
  *Separation:* outcomes must differ.
- **Chess** — primary the two directions of the one quantity, reported separately: `premature
  collapse` (resigned while the frozen engine at depth 18 called it holdable) and `miscalibrated
  persistence` (played on while lost). Secondary plies, illegal-move count, terminations.
  *Separation:* the two counters must differ in direction, not just in size.

**Rows are filed as they land**, one row file per (cabinet, entrant), so a window that closes early
leaves usable rows. A cabinet with rows for only some entrants is reported as exactly that.

## 4. Tenancy for this sitting

Unchanged from the earlier document, plus one addition:

1. `gpu-lease.sh acquire --owner ocho2-suite-t_234b2387 --class batch --need-mib 5400 --ttl 14400`
   before the first load; released at the end.
2. One entrant resident; no parallel cabinets (V3); `prism-brain` / `:58595` never restarted,
   health polled before and after every block.
3. **Release bar per load (V4):** after the process exits, the cabinet's port must refuse connections
   and `nvidia-smi memory.used` must return to the baseline sampled at that block's start, tolerance
   64 MiB. The delta is recorded, never absorbed.
4. **New for driver-owned cabinets:** the driver owns its server's lifetime, so the wrapper samples
   the card and the port *during* the block and verifies the port is closed after the driver exits.
   A driver that leaves a server behind fails its own release check and the block is reported as
   `RELEASE_FAILED`, not as a row.
5. `:58595/health` is polled before and after every block; the resident brain is not evicted.

## 5. What each cabinet cannot separate — fixed before the numbers

- **Sokoban** cannot separate *cannot play* from *cannot parse* on a level where `not_an_action`
  dominates, and at 3 levels it cannot order two entrants that each solve 1. It also cannot separate
  the legend arms: only one legend is run here.
- **Zork** cannot separate a model that cannot *understand* the world from one that cannot *type a
  command*: `unparsed` is counted separately, but the driver does not re-prompt to find out which one
  it was. Two levels cannot order two entrants that both reach the gate.
- **Snake** cannot separate skill from interface at single-letter answers, and 120 ticks with deaths
  that reset the board means two identical apple counts may be different episodes. Two seeds cannot
  separate a seed effect from noise, and the 4-seed list is not fully read here.
- **Labyrinth** is one cell: one graph, one rune, one K, one symmetrisation. It says nothing about
  another graph, and the cell's own §7 refusal table governs what the predicate means.
- **Chess** at 30 plies cannot estimate a rate for either counter; it can only show that a direction
  was observed. It also cannot separate chess skill from prompt compliance — a model that answers in
  prose without a first-line move is `no_move`, which is an interface outcome, not a lost position.
- **Across this sitting:** class cannot be separated from quantisation (unchanged from the earlier
  document), and GPU rows here cannot be compared with published CPU rows as if the path were the only
  difference — the binary, ctx and process all differ, and every such comparison is filed as a *row
  difference with named confounds*.

## 6. Acceptance for this sitting

1. rows per cabinet per entrant, each carrying compute path (`-ngl`, ctx, binary, `/props` ftype,
   slots) and serving-process identity (pid, start epoch from `/proc/<pid>/stat` field 22 + `btime`,
   binary and weights size/mtime);
2. every load's release verified with the port and the card, delta recorded;
3. one results table per cabinet with the CPU/GPU provenance column present, published CPU rows
   visible beside the GPU rows and never merged into them;
4. §5 stated in the results, not in a footnote.
