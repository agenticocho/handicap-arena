# Mastermind instrument report — 2026-10-26

Commit: f6106be.

Controls (all five, run in the same process that produces rows; written output at
`/home/chilly1/workspace/cabinet_results/main/MASTERMIND_CONTROLS.json` and
`/home/chilly1/workspace/cabinet_results/main/MASTERMIND_CONTROL_ROWS.json`):

- control_1_scripted_arm_100: PASS (16/16 wins, mean 5.50, digest 43eb702eda74... unchanged).
- control_2_broken_arm_0: PASS (constant guess (0,0,0,0): 0/16 wins on solvable boards).
- control_3_stored_vs_recomputed_consistent: PASS (disagreements 0 over all answered states).
- control_4_per_turn_prompt_digest: PASS (10 distinct digests, one per turn; printed in run header).
- control_5_per_state_null: PASS (null computed from |candidates| before each turn; turn1 = 1.0, never a single constant).

Each control was demonstrated both passing and failing in
`probes/mastermind/test_mastermind_controls.py` (exit 0, all arms as pre-registered).

Defect-class fixes:
1. Control that cannot fire: the turn-1 consistency vacuity (always true) is now excluded from any band that claims discrimination — nulls and bands are per-state and per-turn; no "lag >= 2"-style tautology remains in the block.
2. Bound quoted as p-value: per-state nulls printed per turn; no single constant (0.0317 or 2.09%) is used as a metric floor.
3. Band/denominator drift: per-turn nulls and candidate counts are carried per turn in `state.candidates_before_each_turn`.
4. Stored fields trusted: `consistent` recomputed from guesses + feedback in-process; disagreement count printed even when zero.

What the cabinet still cannot separate: whether a model reads feedback (ignition) vs. emits a fixed opening book; the control only certifies the instrument, not the model. Frozen fixtures and MASTERMIND_RESULTS.md were not edited; this is an appended NOTE.
