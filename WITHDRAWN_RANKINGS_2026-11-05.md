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

No board enters a scored set until **all three** hold:

1. `python3 degenerate_gate.py --json --event <event> --board <path>` returns a verdict that is not
   `DEGENERATE`;
2. the witness it reports is **replayed into that board's own simulator and reproduces**
   (`verify_pstar.py`, `4 witnesses replayed, 0 did not reproduce`);
3. **`p* > gate width`**, with both numbers written beside the row in
   `probes/PSTAR_TABLE_2026-11-05.json`. *"p\* > bound" is not "not degenerate"* — the bound has to be
   stated or the comparison is decoration.

## 4. Scope — this is not a Sokoban defect

Seven of the eight arena boards are cleared by a fixed schedule: missile `mc_01` **1**, `mc_02` **4** (one
period above its width-3 gate, with the four tokens forced by four city-bound threats), zork `zork_01` **2**,
`zork_02` **5** (which *passed* a width-2 gate two days ago). Snake is the only survivor, and only for
periodic words of period ≤ 4 at 120 ticks — the cabinet ships a Hamiltonian-cycle baseline that is a fixed
*non-periodic* route and scores well, so "snake is not degenerate" must never be quoted without that bound.

## 5. Falsifier

If any board above is re-derived with a shortest clearing period **above** its gate width, its withdrawal is
wrong and should be reversed in the file that recorded it — the same discipline `RETIRED_BOARDS.md` carries.
