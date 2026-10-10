# DIGDUG_DECISIONS.md — every clause the paragraph left open, and what was done about it

The Tier-3 brief's instruction is not "decide sensibly". It is: a clause the
prose does not settle must be (a) marked in the frozen contract, (b) argued
here, and (c) carried into every bundle so a reader of one record does not have
to open three files to know what was decided. All three are done for all
fourteen engine clauses plus the reader's; `contract.decisions_index` in a bundle
is generated from `digdug.DECISIONS`, so this document cannot drift from the code
without a control noticing.

Two habits in the entries below are deliberate:

* **the rejected alternative is named**, because a decision whose alternative is
  not written down is indistinguishable from a default that was never chosen; and
* **`MEASURED:` cites the number** from `digdug_readings.py` (the shadow table and
  the four probes). Where the measurement says "inert", it says "inert" — a table
  that found a difference in every row would be measuring something else, most
  likely the act of running it.


## 1. THE FOURTEEN

### `[D-ADJ]` — clause `resolve_order`

- **frozen:** `player_first`
- **rejected:** `simultaneous`
- **why this one:** 'adjacent cells, whose turn resolves first' is undecided; player-then-hazard, with the winning ply ending the run BEFORE hazard motion, is what makes level 05 a WIN and not a death
- MEASURED: `shadow:resolve-simultaneous` changes 02's OPTIMUM from 7 to 5 -- not merely who dies, how short the shortest plan is. An ordering clause is not a display convention.

### `[D-BLOCK]` — clause `player_into_hazard`

- **frozen:** `blocked`
- **rejected:** `killed`
- **why this one:** moving into the cell a hazard stands on is undecided; blocked makes a hazard a living wall, which is the ONLY mechanism in this contract that destroys the player's route -- see 4F1
- MEASURED inert on the item set AND on the optimum-level table -- and P1 shows why that is a theorem and not a gap: to step onto a hazard you must first stand next to one, and a hazard next to a tunnel has a road and resolves onto you the same ply. It becomes measurable only under a SECOND rejected clause (`clock2:blocked` ends `WALLED_IN_ONLY`, `clock2:kills` ends `KILLED_BY_HAZARD`). The clauses are not independent, and that is the finding.

### `[D-BLOCKED-TURN]` — clause `blocked_legal_letter`

- **frozen:** `costs_a_turn`
- **rejected:** `costs_nothing`
- **why this one:** a legal letter aimed at rock is CONSUMED: `moves` does not advance, the turn count does, and a hazard already on a road steps closer. The rejected reading -- 'only a successful move is a turn' -- makes waiting safe by walking into a wall, which is the same rule as [D-STOP] wearing a costume; the two are decided together and reported separately because `blocked` and `waited` are different counters and the record must be able to tell which one a run filled
- MEASURED on `wall-bumper`: 43 answers, 42 of them blocked, 1 turn of ground -- the turns that went into rock are counted as turns spent, and the level it does buy a move on is 04, where `_` is diggable ground next to the start. The record shows the exception instead of the control being bent to keep the story clean.

### `[D-BOUNDS]` — clause `bounds`

- **frozen:** `blocked`
- **rejected:** `raises`
- **why this one:** B2: bounds are checked in the transition function; walking off the board is impossible, and an unbounded walk is an error only in the sense that it never happens
- MEASURED at P3: on an UNFRAMED board `bounds=blocked` walks the player into the wall twice and never solves, `wrap=True` wraps into the pearl and WINS, and `bounds=raises` puts an `IndexError` out of the transition function. On every framed level in the item set all three are identical, which is why `enclosed_measured` is in the record.

### `[D-CLOCK]` — clause `hazard_clock`

- **frozen:** `per_player_turn`
- **rejected:** `every_2_player_turns`
- **why this one:** the paragraph says a hazard 'can arrive' through tunnels and never says when it moves; per-player-turn is the only reading that makes the run a pure function of the answer stream
- MEASURED: `shadow:clock2` separates on 04 only (a greedy run that dies under the frozen clock survives there), and `shadow:clock-never` moves 02's optimum from 7 to 5 and drops its proof grade to `bounded:13`. The clause is load-bearing in the ENDS and in the PROOFS, and inert in the optima of 01/03/05 -- which is why the frozen value had to be chosen rather than derived.

### `[D-END]` — clause `end_on_solve_first`

- **frozen:** `True`
- **rejected:** `False`
- **why this one:** does a run that collects the last pearl on the ply a hazard would step onto it count?  Decided YES.  Level 05 exists to exercise exactly this clause
- MEASURED: `shadow:end-on-solve-last` makes 01 (the FLOOR of the scale, one letter long) and 05 (the photo finish) UNWINNABLE, and 01's frozen plan ends `KILLED_BY_HAZARD`. The rejected reading also splits INTERNALLY: with `death_beats_solve=False` the whole row collapses back onto the frozen one, INERT on all five levels. A rejected clause with an accepted half is the reason both are named in the contract.

### `[D-HAZCOLL]` — clause `hazard_blocks_hazard`

- **frozen:** `True`
- **rejected:** `False`
- **why this one:** two hazards in one cell is not expressible in the prose and is decided: they block each other, which makes a junction into a thing a plan can use
- MEASURED inert on P4, and the probe says why in one line: the player has to survive beside two hazards for a collision to be observable at all.

### `[D-NEIGHBOUR]` — clause `neighbour_rule`

- **frozen:** `one_shared_function`
- **rejected:** `six_copies_of_two_lines`
- **why this one:** the boundary is one rule, so it is ONE function: `neighbour(state, cell, delta)` applies wrap and nothing else decides where a coordinate is.  It is recorded as a decision because it was found as a bug: a copy of these two lines in `reachable_cells()` reduced the coordinate AFTER adding it to `seen`, so on any `wrap=True` reading the mobility flood fill expanded off the edge forever and the process died.  The frozen reading cannot reach it (wrap is off), which is why it survived review -- and why [B2]'s rule is not only 'check the bounds in the transition function' but 'there is one place that knows the bounds'
- Found as a bug, recorded as a decision. See the docstring on `neighbour()`: a copy of the two-line boundary rule in `reachable_cells()` reduced the coordinate AFTER adding it to `seen`, so any `wrap=True` reading sent the mobility flood fill off the edge forever and the process was killed for memory. The frozen reading cannot reach it. That is what a shadow clause finds that a unit test does not.

### `[D-OBJ]` — clause `objective`

- **frozen:** `all_targets`
- **rejected:** `survive_n`
- **why this one:** 'solved' is not defined by the paragraph; collecting every target is the only reading that uses the sentence it does provide ('a target is collected by moving into its cell')
- Refused by the solver, and that is the measurement: `shadow:objective-survive` returns `NOT PROVEN` on all five levels because the state key carries no clock. A reading the instrument cannot prove is reported as unprovable, not as a zero.

### `[D-STOP]` — clause `wait_legal`

- **frozen:** `True`
- **rejected:** `False`
- **why this one:** the paragraph never says the player may stop; WAIT is in the ALPHABET anyway, because R3 puts the answer shape in the grammar and a game that permits a pause the grammar forbids makes a correct answer a failure
- MEASURED: `waiter` is consumed `.` 42 times across the item set and dies on 04 with `waited` counted; no optimal plan on any level contains `.` (measured: 01 `R`, 02 `URLDDRR`, 03 `DRULUUR`, 05 `URRR`). Probe P2 shows the same single `.` killing a run under the frozen clock and surviving it under `hazard_clock=never`.

### `[D-T0]` — clause `hazard_terrain`

- **frozen:** `tunnels_only`
- **rejected:** `soil_too`
- **why this one:** the paragraph says a hazard cannot reach the player except through tunnels, so its route does NOT exist through UNDIGGED soil. Measured scope, stated here because the first draft of this sentence said 'at time zero nothing moves' and level 04 refutes it: `_` is ground the level AUTHOR dug, so 04 has a hazard armed at distance 2 before the entrant has typed anything. A new level cannot arm a hazard; an authored tunnel run can -- which is the difference between this clause and [D-TIEBREAK]'s determinism, and why the item set contains one of each
- MEASURED and the largest single number in the cabinet: `shadow:hazard-in-soil` turns 03 (opt 7) and 05 (opt 4) into PROVEN LOSSES and costs 02 its exhaustive grade. One clause about what a hazard stands on moves two items from 'won in 7' to 'nobody can win this'.

### `[D-TARGET]` — clause `target_persistence`

- **frozen:** `removed`
- **rejected:** `persists_as_marker`
- **why this one:** 'collected' has no stated consequence; removal is the reading under which the word means something
- Also refused by the solver, for the same reason in the other direction: `objective_met()` advances while `targets` stops shrinking, so the key the proof is built on is no longer complete. Both refusals are the guard working; neither is a result about the levels.

### `[D-TIEBREAK]` — clause `hazard_tiebreak`

- **frozen:** `reading_order`
- **rejected:** `reverse_reading_order`
- **why this one:** the paragraph permits more than one hazard and never says what two hazards wanting the same cell do. Frozen to reading order because the EXHAUSTIVE PROOF depends on it: a randomised tie-break makes the state key incomplete and every number in this cabinet unreplayable. The choice costs nothing on any of the five levels (measured: 4F item 6) and buys determinism with no seed -- which is why it is in the contract and not in a comment
- MEASURED inert on all five levels and on P4. A clause that costs nothing and buys determinism for the exhaustive proof is the best kind of decision and the worst kind of finding; the table keeps the two apart instead of claiming credit.

### `[D-WRAP]` — clause `wrap`

- **frozen:** `False`
- **rejected:** `True`
- **why this one:** the grid is bounded, it does not wrap; 'a grid of soil' with no torus language is a bounded grid, and wrapping would make the enclosure measurement meaningless
- Same measurement as D-BOUNDS: wrap is a no-op on a rock frame and a different game without one. Deciding it costs nothing on five framed levels; not deciding it would have left a hole a level file could fall through.

## 2. THE READER'S DECISIONS (they belong to the grammar, so they live in the grammar's file)

`[D-WASD]`, `[D-TOKENS]`, `[D-STOP]`'s alphabet half, `[D-ORDER]`,
`[D-STEP-SCOPE]`, `[D-WORDS]`, `[D-RETRIES]`, `[D-PROMPT-TOKEN]` and
`[D-SIGHT]` are argued at the head of `digdug_reader.py` and in `build_prompt`'s
docstring, and they are exported into every bundle by `grammar_as_record()`.
They are listed here so one document answers "what was decided", which is the
question a bundle reader actually asks.

The one worth restating is `[D-SIGHT]`: the prompt shows `min_hazard_distance`
and never `completable`. The instrument KNOWS, at every ply, whether the level is
still winnable inside the budget — that is what the exhaustive search is for —
and telling the entrant would convert the faculty under test into a display.
The value is in the record, per ply, for the reader of the record.

## 3. WHAT IS NOT DECIDED HERE

`hazard_terrain` under a hazard that has already been walked through, whether a
hazard can dig (it can, under `soil_too`, and the counter `hazard_digs` exists
only to make that visible), and whether a run that neither dies nor finishes by
the cap is a loss or a draw. The first two have no effect on any item in this
set; the third is decided by the budget, not by the rules, and `BUDGET_EXHAUSTED`
is named that way in the record so it is never read as a verdict about the level.

