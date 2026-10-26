# Lights Out instrument report — 2026-10-26

Commit: (to be filled after commit).

Controls (all run in the same process that loads the fixture; output below):

- control_1_clean_fixture_loads: PASS (16 boards load, truth present on every board).
- control_2_truth_equals_label: PASS (fixture `correct` == computed solution, 16/16).
- control_3_md_prose_crosscheck: PASS (prose answer cell == computed solution, 16/16).
- control_4_truth_present: PASS.

Mutation control (`lightsout_cabinet_control.py`, all arms on copies in scratch, rc 0):

- E unmutated copies pass: rc 0.
- A board id mutated (idx 1 -> 99): refused, rc 1.
- B `correct` field mutated (A1 -> B2): refused, rc 1 (historically survived).
- C prose answer cell mutated (A1 -> C3): refused, rc 1 (historically survived).
- D whole-file substitution (empty json): refused, rc 1.

Claim vs state (arm-2 run, 16 boards): 16 of 16 answers claimed SOLVED; 0 of 16
boards actually cleared. Claim and state are printed as separate columns; a
claim never awards a solve (verdict is derived from state).

What the cabinet still cannot separate: a deliberating model from one that
committed no move (both surface as no answer); and the 3x3 rung cannot
exercise `CORRECT_UNSOLVABLE` / `FALSE_UNSOLVABLE` at all (every board is
solvable), so unsolvability claims are only measurable on 4x4. The cabinet
also cannot tell a label that happens to be right from one that was recomputed
right — it can only refuse disagreement, not certify provenance.
