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
| **COLLAPSED** (schedule *is* the optimum) | sokoban `01` (1/1), `03` (6/6), zork `zork_01` (2/2), missile `mc_01` (1/1), missile `mc_02` (4/4) | floor headroom **0**, replay-verified; `mc_02` also exact by exhaustion (cities saved 1/2/3/4 at periods 1/2/3/4) |
| **SEPARATED** (real headroom) | sokoban `02` — schedule 28, optimum **12** | headroom **16** |
| **DEGENERACY LIKELY, COMPARISON UNTRUSTWORTHY** | zork `zork_02` (p\*=5 at bound 5, headroom 1) | its `best_by_period` is `null`, so the exhaustion cannot be shown, **and** its `cleared: true` is reached at `out_of_commands` with the item carried — never `escaped`. The period is probably right; the "headroom 1" row compares two different terminal conditions. |
| **SCORE-TYPED** | snake seeds 1/7/13/42 (8–9 apples; p\* 2/2/2/4 at bound 4) | a count, never pooled with a win floor |

**Snake keeps its earlier caveat:** the cabinet ships a Hamiltonian-cycle baseline, a fixed *non-periodic*
route that scores well, so "not degenerate" would have to mean "for periodic words of period ≤ 4 at 120
ticks" and nothing wider.

So: **five boards proven degenerate by measurement, one separated, one whose degeneracy is likely but whose
headroom comparison is not trustworthy, four score-typed.** Your approval's scope withdrew **four** of them —
`02_two_boxes` is kept — and the fifth (`mc_02`) enters no scored set in any case, because missile has no
gate in `degenerate_gate.py` at all. The Sokoban withdrawal does not depend on the count: it rests on all
three Sokoban boards having headroom 0/16/0 against schedules of period 1/7/6.

**One correction the count earned, against the Chair.** An earlier draft called `mc_02` *"at its bound —
unproven"* on the reasoning that a p\* measured at its search bound is only a lower bound. **That reasoning
is backwards:** `p*` is a **minimum**, so a saturated bound risks *missing* a short period, never inventing
one — and `best_by_period` shows periods 1/2/3 failing and 4 clearing, so `p* = 4` is exact.

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

## NOTE 2026-11-05T15:17:26Z — Mike's word, couriered; and one row of §4 is labelled against its own instrument

**The decision.** Mike's answer reached this box relayed by Jarvis (Local Chair, `jarvis`) in CHAIR LINK arrival
`6ce60e14273d91566618a575e746a8c7f82499dbe10765ff4a9dd5a3ff39ddd4`, dated `2026-11-05T15:10:45Z`. His word,
verbatim and complete: **"approved"**. The recommendation it approves, as the courier restated it: *"keep
`02_two_boxes`; withdraw the four collapsed boards."* **It is recorded here as a COURIERED decision, not as the
principal's word to this box** (`governance/rulings/2026-11-02-a-relay-is-not-an-authorisation-and-a-refusal-names-the-input.md`
R1 stands, and the peer names himself courier and invites the refusal). Nothing irreversible rests on it: this
document deletes nothing, and every row, digest and `## QUALIFIER` block above is unchanged by it.

**What it settles, applied:**

- `02_two_boxes` — **KEPT**, as the one SEPARATED board: p\* 7, schedule 28, floor 12, **headroom 16**. A fixed
  schedule does clear it inside the 40-move cap, so the §1 ground ("no board left that rewards search") never
  applied to it; the NOTE above withdrew that sentence for `02` on measurement, and this note makes it a decision.
- **Withdrawn from scored sets** — `01_one_push`, `03_the_corner_waiting`, `mc_01_one_shot`, `zork_01_the_floor`,
  unchanged from §4.
- `zork_02_long_crawl` — **kept, labelled**: schedule 7, floor 6, **headroom 1**. Not a ranking board; the headroom
  travels beside the score.
- snake — **kept**, with §4's caveat verbatim: its PASS is scoped to periodic words of period ≤ 4 at 120 ticks, not
  to fixed schedules in general, because the cabinet ships a Hamiltonian-cycle baseline.
- chess — **kept visible**, `UNDETERMINED`, never blank and never `UNWINNABLE`.

**The correction — `mc_02` is COLLAPSED, and §4 says otherwise.** §4 lists `mc_02_scarcity` under *"AT ITS BOUND —
unproven"*. That sentence was written against `p*`'s search bound and reads as a statement about degeneracy, which
is not what the bound measures. The instrument's own verdict, from the table §4 draws on:

```
jq -r '.rows[] | "\(.board)\t\(.p_star)\t\(.schedule.commands)\t\(.floor.commands // .floor.score // "-")\t\(.headroom)\t\(.verdict_pair)"' probes/FLOOR_TABLE_2026-11-05.json
levels/mc_01_one_shot.txt	1	1	1	0	COLLAPSED
levels/mc_02_scarcity.txt	4	4	4	0	COLLAPSED
levels/zork_01_the_floor.txt	2	2	2	0	COLLAPSED
levels/zork_02_long_crawl.txt	5	7	6	1	NARROW
```

And the bound objection is measurably wrong for this row, because `p*` is a **minimum** and every shorter period
was exhausted — `probes/PSTAR_TABLE_2026-11-05.json`, `mc_02`: `"search_bound": 4`, `"best_by_period": {"1": [1,
"1P"], "2": [2, "1P 1Q"], "3": [3, "1P 1Q 2R"], "4": [4, "1P 1Q 2R 2S"]}` — cities saved by the best word of each
period are 1/2/3/4, so no period < 4 clears all four and period 4 does. `p* = 4` is exact, not a lower bound.
**Rule (MIRROR ON ME): a minimum that sits at its search bound is exact when a witness exists inside the bound and
every smaller value was exhausted; saturation is a defect only when nothing clears within the bound, which is the
string "p\* > bound".** `zork_02` is **not** corrected here — its row carries `"best_by_period": null`, so the same
exhaustion cannot be shown from the artifact, and its NARROW verdict of headroom 1 is untouched.

**So the count, with its basis named:** **five** boards are COLLAPSED by the floor instrument — `01`, `03`, `mc_01`,
`mc_02`, `zork_01`; one SEPARATED (`02`, headroom 16); one NARROW (`zork_02`, headroom 1); snake score-typed; chess
unmeasured. Mike's sentence says **four**, and four is what this document withdraws — `mc_02` is **not** folded into
that approval, and it does not need to be: **no missile board is admissible at all** until `degenerate_gate.py`
supports the event (§3.2), so it enters no scored set by either route. *Four withdrawn* and *five collapsed* are
both true and neither number travels without the other: four is a scope, five is a measurement.

