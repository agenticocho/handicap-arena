# WITHDRAWN 2026-11-05 — the Sokoban rankings are VOID, not qualified

**Decided:** 2026-11-05 by Mike (principal) on the Local Chair's recommendation.
**Reversibility:** nothing is deleted. Every artifact, row and digest in the six qualified files is retained
byte-for-byte; what changes is the standing of the numbers, which is now **VOID as evidence of search**.
**Ruling:** `governance/rulings/2026-11-05-pstar-is-the-admission-test-and-the-width-is-the-finding.md`.

## 1. Why withdrawal and not qualification

The earlier qualification said *one* board was degenerate and that any figure pooling it was an upper bound.
**That ground has widened past the qualification:** all three boards are cleared by a fixed schedule.

| board | p\* | witness | optimal solution |
|---|---|---|---|
| `levels/01_one_push.txt` | **1** | `R` | `R` — the cycle *is* the optimum |
| `levels/02_two_boxes.txt` | **7** | `DDRLUUR` | 28 moves, inside the 40 allowed |
| `levels/03_the_corner_waiting.txt` | **6** | `RULDLU` | `RULDLU` — the cycle *is* the optimum |

`p*` is the smallest period whose repeated word clears the board. With **no board left that rewards
search**, a ranking over this set is not a guarded measurement — it is a number a reader will still cite as
a ranking. A qualified ranking is still a ranking; an unsupported one should be withdrawn.

## 2. What stays true

- **Every row, counter and digest stays.** Rows are annotated, never deleted — the rule this project has
  applied all day, and it applies to a withdrawal too.
- **The scores still say something, and it is not nothing:** they are a valid test of *emission*. A pipeline
  that cannot clear a one-move board is broken, and several entrants here are exactly that. That reading
  survives; the planning reading does not.
- **The qualification blocks stay in place.** They are the record of how the finding was reached; this
  document supersedes their conclusion, not their evidence.

## 3. Rebuild condition — the gate for any future board

No board enters a scored set until **all four** hold:

1. **`p*` is measured with a search bound strictly greater than the claimed `p*`.** A measure that
   saturates its bound is a *lower bound* on p\*, not p\*. Two of the eight rows in
   `probes/PSTAR_TABLE_2026-11-05.json` sit exactly at the edge — `zork_02` p\*=5 with bound 5, `mc_02`
   p\*=4 with bound 4 — so as published they cannot exclude a period one longer.
2. **`degenerate_gate.py` is run with `--max-period` at or above the claimed p\***. Its defaults are
   `SOKOBAN_MAX_PERIOD = 3` and `ZORK_MAX_PERIOD = 2`, so at default settings it returns `PASS` for
   `02_two_boxes` (p\*=7) and `03_the_corner_waiting` (p\*=6). *A verdict from a bounded instrument is a
   statement about the bound.* **Missile is not a supported event in the gate at all**
   (`--event {sokoban,zork,chess}`), so no missile board may be admitted until one exists.
3. **The clearing condition is the floor's, verbatim:** `finished` / `escaped`. For `zork_02` the p\* table's
   `cleared: true` is reached at `out_of_commands` with the item carried — the schedule never escapes. A
   weaker terminal condition makes "p\* = 5" and "optimum = 6" incomparable, and the row that compares them
   is arithmetic dressed as a finding.
4. **`p* > gate width`**, with both numbers beside the row. *"p\* > bound" is not "not degenerate".*

## 4. Scope — this is not a Sokoban defect, and the count is smaller than the first claim

The earlier "7 of 8 boards are cleared by a fixed schedule" was assembled from two artifacts with
different bounds and does not survive being checked row by row. What the floor and the p\* table support:

| verdict | boards | on what |
|---|---|---|
| **COLLAPSED** (schedule *is* the optimum) | sokoban `01` (1/1), `03` (6/6), zork `zork_01` (2/2), missile `mc_01` (1/1) | floor headroom **0**, replay-verified |
| **SEPARATED** (real headroom) | sokoban `02` — schedule 28, optimum **12** | headroom **16** |
| **AT ITS BOUND — unproven** | zork `zork_02` (p\*=5 at bound 5), missile `mc_02` (p\*=4 at bound 4) | a saturating search cannot exclude a longer period |
| **NOT COMPARABLE** | zork `zork_02` again: `cleared: true` at `out_of_commands`, never `escaped` | p\*'s terminal condition is weaker than the floor's |
| **SCORE-TYPED** | snake seeds 1/7/13/42 (8–9 apples; p\* 2/2/2/4 at bound 4) | a count, never pooled with a win floor |

**Snake keeps its earlier caveat:** the cabinet ships a Hamiltonian-cycle baseline, a fixed *non-periodic*
route that scores well, so "not degenerate" would have to mean "for periodic words of period ≤ 4 at 120
ticks" and nothing wider.

So: **four boards proven degenerate, one separated, three unproven or incomparable.** The Sokoban
withdrawal does not depend on any of them — it rests on all three Sokoban boards having headroom 0/16/0
against schedules of period 1/7/6 — but no reader should carry away "seven of eight".

## 5. Falsifier

If any board above is re-derived with a shortest clearing period **above** its gate width, its withdrawal is
wrong and should be reversed in the file that recorded it — the same discipline `RETIRED_BOARDS.md` carries.

## NOTE 2026-11-05T15:03:38Z — one column of the table above is not what its heading says

The `02_two_boxes` row's third column is headed **optimal solution** and reads `28 moves, inside the 40 allowed`.
**28 is the cost of the schedule `DDRLUUR` repeated to the 40-move cap, not the optimal solution.** Measured in
this tick with `python3 sokoban_solver.py --level levels/02_two_boxes.txt` (breadth-first, complete, nothing
exhausted by a budget):

```
  verdict      SOLVABLE
  moves        12
  solution     DDRRRRULLURR
  pushes       5
  verified     sokoban.play(): solved=True moves=12 blocked=0
```

So board `02` is **separated by 16 moves**, not collapsed: the optimum is 12, a schedule costs 28, and the
difference is search a player can be paid for. **The withdrawal itself stands** — a fixed schedule does clear
`02` inside the registered cap, which is exactly what `p*` = 7 says, and that is the ground this document
withdrew the ranking on. What does not stand is the closing sentence's scope: *"with no board left that
rewards search"* is **withdrawn for `02` only**, and the reason is this measurement. `01` and `03` are
unaffected — 1 and 6, and in both the optimal play **is** the cycle (measured again here).

Both numbers for every board, in one table with the gap between them: `probes/FLOOR_TABLE_2026-11-05.json`,
produced by `winnability_floor.py` (`14 passed, 0 failed`).

