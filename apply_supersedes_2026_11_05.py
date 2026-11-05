#!/usr/bin/env python3
"""Append the SUPERSEDES block to every file that carries the 2026-11-05 QUALIFIER. Idempotent."""
import hashlib
import os

REPO = "/home/chilly1/workspace/ocho_arena"
FILES = ["suite2/TABLES2.md", "suite3/TABLES3.md",
         "SUITE_RESULTS_multi_model_sitting2_2026-10-25.md", "SOKOBAN_FRONTIER_RESULTS.md",
         "SOKOBAN_VERDICT_1.md", "SOKOBAN_VERDICT_2.md"]

BLOCK = """
## SUPERSEDES 2026-11-05 -- all three boards are dead, not one

**p\\* (smallest period whose repeated word clears the board) is 1 / 7 / 6 for `01_one_push`,
`02_two_boxes`, `03_the_corner_waiting`.** The block above retired `01` and left `02` and `03` standing
because both PASS the width-3 gate. That gate is a **choice of width**, and both boards clear above it:
`02` in 28 of its 40 allowed moves on the 7-cycle `DDRLUUR`, `03` in 6 moves on `RULDLU` -- and `03`'s
optimal solution IS that cycle (`sokoban_solver.solve_text`: `03 moves 6, solution RULDLU`). **No Sokoban
board in this cabinet measures search.** Every figure in this file that rests on any Sokoban board is an
upper bound, not evidence of planning; a re-score drops those rows rather than re-weighting them. The
published rankings are **qualified, not withdrawn** -- withdrawal is Mike's call and is open. Measure,
witnesses and reproduction: `PSTAR_2026-11-05.md`. Enforcement: `RETIRED_LEVELS` / `level_admission()`
in `sokoban_run.py`.
"""

for rel in FILES:
    p = os.path.join(REPO, rel)
    text = open(p, encoding="utf-8").read()
    if "## SUPERSEDES 2026-11-05" in text:
        print(f"already has it  {rel}")
        continue
    with open(p, "a", encoding="utf-8") as f:
        f.write(BLOCK)
    new = open(p, "rb").read()
    print(f"appended  {rel:52s} {len(text.splitlines()):5d} -> {len(new.decode().splitlines()):5d} lines  "
          f"sha256 {hashlib.sha256(new).hexdigest()[:16]}")
