# Per-Game Constant-Reply Candidates

## The principle

A constant-reply attack is a stream of identical tokens that clears a board without the model reading it.
For each event: what could a player emit on every turn, without ever looking at the state?

## Candidates by event

### Sokoban (irreversible planning)
- **`R` forever** — right. If no wall blocks, the player slides right every turn.
  **46 of 84 constant streams solve Board 01 (`00996929` freeze).** 46/84 = 54.8%.
  **The optimal solution to Board 01 is itself a constant cycle of length 1** — the board was
  never a puzzle. A constant that matches the optimal path isn't a degenerate that happens to
  clear; it's the correct answer wearing a degenerate's clothes.
- **`D` forever** — down. Same shape, different axis.
- **Control:** generate constant streams of `R`, `D`, `L`, `U` and check if any clears a board.
  If `R` clears >50% of boards, the board is not discriminating.

### Chess (calibration gate)
- **`RESIGN` every turn** — always legal, always terminates. A model that always resigns
  passes the "logical conclusion" gate but fails the calibration measurement (premature collapse).
- **`e2e4` every turn** — only legal from the start position. Becomes illegal after move 1.
  Not a viable constant for more than one ply.
- **No true constant.** Chess has no "always legal, always advances" move. The gate is binary
  (concluded or not), so the constant-reply attack is "always resign" — which the gate catches
  as premature collapse. **Chess is the one event where the constant-reply gate may be moot.**

### Zork (long-horizon state retention)
- **`north` / `n` forever** — the prediction. Reasoning below.
- **`look` forever** — always legal, never advances. Produces `out_of_commands` (never reaches gate).
  Not a winning constant, but a "safe" one that never crashes.
- **`wait` forever** — same as `look`: always legal, never advances.

**Why `north` specifically:** Three reasons.
1. It is the first movement in the reference solution for `zork_02_long_crawl` (north → cellar → key).
   If the game's topology favours north-south corridors, `north` forever advances through at least
   the first room transition.
2. In text adventure design, north is the default "forward" direction. A model that has never read
   the board but knows the genre would emit `north` as its first guess.
3. `look` and `wait` are always legal but never change state — they produce `out_of_commands`
   (never reaches the gate). `north` is the only constant that both (a) is usually legal and
   (b) advances the state. If `north` is legal in >50% of rooms, it clears more boards than any
   other constant.

**Test:** Generate constant streams of `north`, `south`, `east`, `west`, `look`, `wait`, `inventory`.
If any clears the gate, the board is retired.

### Missile Command (allocation under scarcity)
- **`PASS` forever** — always legal, spends nothing. Scores 0 cities (all threats hit).
  Not a winning constant, but a "safe" one.
- **`1P` forever** — legal on turn 1, becomes `unknown` on turn 2 (P destroyed). Not viable.
- **`1X` forever** (if X is a decoy) — legal on turn 1, becomes `unknown` on turn 2.
  Not viable past the first press.
- **No true constant that wins.** Missile Command's action space is SILO × THREAT; once a threat
  is destroyed, the same action becomes `unknown`. The only always-legal action is `PASS`, which
  scores zero. **Missile Command may be inherently resistant to constant-reply attacks.**

### Fencing (structured output)
- **`{}` forever** — always parses, always fails content requirements. Null baseline.
  Not a winning constant, but a "safe" one.
- **A fixed valid JSON** — e.g. `{"station":"RENO-04","readings":[0,0,0,0],"status":"nominal","sensor_count":4}`.
  Passes schema, fails content (readings out of range? depends on schema). If the schema doesn't
  change between runs, a fixed valid JSON might pass every time.
- **Control:** Generate constant streams of `{}` and one fixed valid JSON. If the fixed JSON
  passes >50% of boards, the schema is not discriminating.

**Why there is no dangerous constant:** Fencing is single-shot — one prompt, one JSON object. The schema is
generated per run (anti-gaming rule), so a constant that worked on run N will fail on run N+1
(different required keys, different enums, different content constraints). The null baseline
`{}` always fails content requirements. A fixed valid JSON only works if the schema is identical
across runs, which the anti-gaming rule prevents. **Fencing is inherently resistant to
constant-reply attacks because the target moves every run.**

### Pit Stop (code repair)
- **Return the buggy function unchanged** — null baseline. Passes type checks, fails tests.
- **Return a fixed "correct" function** — if the bug is always the same (touching intervals),
  a fixed patch passes every time.
- **Control:** Generate constant streams of "return input unchanged" and "apply the known patch."
  If the known patch passes >50% of boards, the test suite is not discriminating.

**Why there is no dangerous constant:** Pit Stop is also single-shot — one prompt, one function.
The bug and test suite are generated per run. A fixed patch only works if the bug is identical
across runs, which the anti-gaming rule prevents (hidden tests, varied defects). The null
baseline (return input unchanged) fails the new cases by construction. **Pit Stop is
inherently resistant because the defect changes every run.**

### Mastermind (feedback use)
- **`0 0 0 0` forever** — always a valid guess, never uses feedback.
- **`0 1 2 3` forever** — always valid, never uses feedback.
- **Control:** Generate constant streams of `0 0 0 0` and `0 1 2 3`. If either wins >1%, the
  code space is too small or the feedback is not discriminating.

## Summary table

| Event | Most dangerous constant | Always legal? | Advances state? | Likely clears boards? |
|-------|------------------------|---------------|-----------------|----------------------|
| Sokoban | `R` forever | No (wall) | Yes | **Yes (46/84 = 54.8%, optimal = constant)** |
| Chess | `RESIGN` every turn | Yes | No (terminates) | No (gate catches it) |
| Zork | `north` / `n` | Usually | Yes | **Possibly** |
| Missile Command | `PASS` forever | Yes | No | No (scores 0) |
| Fencing | A fixed valid JSON | Yes | N/A (single shot) | **No — and here's why** |
| Pit Stop | Known patch | Yes | N/A (single shot) | **No — and here's why** |
| Mastermind | `0 0 0 0` | Yes | N/A (single shot) | Unlikely (1/1296) |

## The zork-bench reference (Jarvis's finding)

Jarvis noted that `mnky9800n/zork-bench` (30★) enforces the split between assistance and scoring:
- Scores off the interpreter's own status line (oracle-scores-itself)
- Ships human baseline sessions
- Separates difficulty by assist mode (easy/medium/hard)

This is the same shape as our SENSOR standard: a sensor that can pass alone is a second entrant.
zork-bench is the first implementation seen that actually enforces the split.

**Key takeaway:** The constant-reply gate should be a standard check for every event. Generate
N constant streams per event, run them, and retire any board that a constant clears. This is
Arm B's failure mode (oracle and metric are the same function) applied to the board set itself.
---

## RETIREMENT — 01_one_push (2026-11-05)

Retired by Mike's decision. Marked retired in `verify_levels.py` (`RETIRED_LEVELS`, checked by
`load_level()` / `active_levels()`), removed from every run's `LEVELS` list
(`sokoban_batch.py`, `sokoban_reasoning_ab.py`, `recovery_semantic.py`).

Evidence (gate + control, both in the log):
- Solved by `R` (len 1) in 1 move.
- 45 of 84 constant-reply streams solve it (budget 40; period-1/2/3 over {U,D,L,R}).
- Optimal solution is itself a constant cycle of length 1.
- The board was never a puzzle; a constant that matches the optimal path is the correct
  answer wearing a degenerate's clothes.

The three-board set is now two boards (02_two_boxes, 03_the_corner_waiting).
Replacement board: PROPOSED but NOT added. A new board needs its own oracle, freeze, and
gate run before it is an event fit to rank anyone. Proposal: a board whose solution is NOT
a constant cycle — e.g. a 2-box level requiring a non-straight route (turning), with
optimal length > 1 and no single action that advances toward the solution. Mike decides.
