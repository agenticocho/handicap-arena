# CONSTANT-REPLY CEILING GATE — REPORT

Run: `python3 constant_reply_gate.py` (instrument only; no model runs, no new games).

## Method

For each event, define the degenerate class using the **event's own action alphabet and simulator**
(not Sokoban's), enumerate the constant-reply streams, run them, and classify:

- `DISCRIMINATES` — no constant stream clears / wins / concludes.
- `DEGENERATE — retire` — a constant stream clears the board (retirement candidate; only
  `01_one_push` is actually retired this run).
- `UNDETERMINED (reason)` — the gate could not produce a failing positive control, or no oracle
  / freeze exists.

Stream enumeration: period-1, period-2 and period-3 sequences over the action alphabet
(4 + 16 + 64 = 84 for Sokoban's 4-letter alphabet). Budget = 40 moves per stream.

## Degenerate classes chosen

| Event | Degenerate class | Why |
|---|---|---|
| Sokoban | constant cycle of identical action letters (U/D/L/R), periods 1–3 | the Sokoban sense: one key held down |
| Zork | a single command repeated (`n`, `look`, `inventory`, …) | text adventure; the equivalent of "press R" |
| Missile Command | one action token repeated (`PASS`, or `<silo><threat>`) | allocation; a constant threat id becomes `unknown` after the first hit |
| Chess | `always the first legal move` and `always the last legal move` (move ordering), plus `always resign` | chess has no position-independent legal move; the constants are the move-list endpoints. `always resign` is the premature-collapse direction and is caught by the resignation gate |
| Fencing / tool_selection / code_repair | a fixed valid answer repeated (single-shot tasks) | single-shot; the target moves per run under the anti-gaming rule |
| Mastermind | `0 0 0 0` repeated | fixed guess, no feedback use |

## Per-event results

| Event | Degenerate class | Streams tried | Result | Verdict |
|---|---|---|---|---|
| Sokoban `01_one_push` | constant cycles, periods 1–3 | 84 | 45 of 84 solve it | **DEGENERATE — retire** (done) |
| Sokoban `02_two_boxes` | constant cycles, periods 1–3 | 84 | 0 of 84 solve it | DISCRIMINATES |
| Sokoban `03_the_corner_waiting` | constant cycles, periods 1–3 | 84 | 0 of 84 solve it | DISCRIMINATES |
| Zork `zork_01_the_floor` | single command repeated (13 commands) | 13 | 0 escapes (best: `n` reaches vault then `gate_locked`) | DISCRIMINATES |
| Zork `zork_02_long_crawl` | single command repeated (13 commands) | 13 | 0 escapes | DISCRIMINATES |
| Missile Command `mc_01_one_shot` | single action token repeated (2 tokens) | 2 | 1 clears (`1P`) | **DEGENERATE — retire (candidate, pending Mike)** |
| Missile Command `mc_02_scarcity` | single action token repeated (17 tokens) | 17 | 0 clear (best constant 1/4 cities) | DISCRIMINATES |
| Chess | always-first / always-last legal move, always resign | 3 policies | no logical conclusion within 60 plies except resign (caught) | DISCRIMINATES |
| Fencing (structured_output) | fixed valid JSON | 2 candidates | fixed valid JSON passes the frozen spec | UNDETERMINED (constant passes the frozen spec; resistance depends on per-run spec variation, unverified) |
| Tool selection | fixed valid tool call | 2 candidates | fixed valid call passes the frozen spec | UNDETERMINED (same as above) |
| Code repair | fixed correct implementation | 2 candidates | fixed correct implementation passes | UNDETERMINED (same as above) |
| Mastermind | `0 0 0 0` repeated | — | no simulator / no measured freeze in tree | UNDETERMINED (no oracle to run against) |

## Retirement of 01_one_push (approved)

Done. Marked retired in `verify_levels.py` (`RETIRED_LEVELS`, checked by `load_level()` / `active_levels()`),
removed from every run's `LEVELS` list (`sokoban_batch.py`, `sokoban_reasoning_ab.py`,
`recovery_semantic.py`). Numbers in `SOKOBAN_VERDICT_1.md` annotated, not deleted.

Evidence cited:
- Solved by `R` (len 1) in 1 move.
- 45 of 84 constant-reply streams solve it (budget 40).
- Optimal solution is itself a constant cycle of length 1.
- Gate + positive control both in the log.

## Three-board set → two boards

Surviving boards: `02_two_boxes`, `03_the_corner_waiting`. Both DISCRIMINATE.

### Proposed replacement board (NOT added — Mike decides)

A board whose optimal solution is **not** a constant cycle: a level requiring a turn (non-straight
route) with optimal length > 1, so that no single repeated action advances toward the solution.
Candidate shape: two boxes where the first push must be vertical and the second horizontal, with
the player routed around a solved crate (similar to `02_two_boxes` but with the corridor
requiring a turn mid-solution). Requires its own oracle (verify_levels), freeze (digest + self-test),
and a gate run before it is an event fit to rank anyone.

## Findings for Mike (nothing else retired this run)

1. `mc_01_one_shot` (Missile Command) is flagged: the constant `1P` clears it (1 city, 1 threat).
   It is a one-threat, one-city board; a single lucky constant wins. Retirement candidate, pending
   Mike's decision. `mc_02_scarcity` discriminates.
2. The arena.py harness events pass a constant valid answer on the *frozen* spec, but their specs
   are generated per run under the anti-gaming rule, so resistance in production is unverified.
   Status UNDETERMINED rather than DEGENERATE; needs a check against varied specs.
3. Mastermind has no simulator in this tree; cannot be gated. UNDETERMINED.

## Note on the 45 vs 46 count

The prior report cited 46 of 84 constant streams solving `01_one_push`. Re-running the enumeration
(periods 1, 2 and 3 over {U,D,L,R}, budget 40) measures 45: streams with no `R` at all are
3 + 9 + 27 = 39, and 84 − 39 = 45. The difference of one is recorded here rather than silently
adopted; the gate's own log carries 45.
EOF
echo done