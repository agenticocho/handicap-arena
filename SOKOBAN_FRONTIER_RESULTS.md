# SOKOBAN FRONTIER — RESULTS (8 of 8 cells measured)

Card `t_efd6df81`. Pre-registration: `PREREG_sokoban_frontier.md`, commit `368c166`, **written and committed
before the first command ran** (no probe for any of the four entrants existed then; checked).
Instrument: `sokoban_run.py` 62 271 B sha256 `80259a15…`, levels `02`/`03` at `7549657f…`/`77d18407…`,
declared default binary, `--cap 40` on every cell, `--llama-server` on none. Re-hashed after the last cell and
unchanged (62 271 B, `80259a1549e12a50`): **no instrument edit is part of this card.**

**This table is COMPLETE: eight cells, eight rows.** It was reported twice as a partial — 6 of 8, then 7 of 8 —
and that history is kept rather than tidied away. Cell 4 was terminated at 16 of 40 plies in the first run
window and is named in `DISCARDED-MANIFEST.txt` (D1); it was then **re-run to completion** in the second window
(`535059d`) and its row is a real cap-40 measurement. **Cell 8 was taken by the Chair** after the card
escalated to `triage` on `block_loop_detected`: a third unblock/re-block cycle would have cost the box more
than one background run, so the Chair ran the cell and appended its row here. Nothing else in this document
was rewritten.

## THE TABLE

| cell | entrant | level | solved | moves | ended | plies>=1 (moves>=2) | any board change | any box push | load_s | wall_s | record | record sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M | 02_two_boxes | false | 0 | commands_exhausted | no | 0 | 0 | 3.0 | 121 | `probes/SOKOBAN_Mellum2.1-12B-A2.5B-Thinking-Q4_K_M_02_two_boxes.json` | `59fdcad94f46353f` |
| 2 | I | 02_two_boxes | false | 1 | commands_exhausted | no | 1 | 0 | 3.0 | 376 | `probes/SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_02_two_boxes.json` | `c9a7f5d98a212d68` |
| 3 | Q | 02_two_boxes | false | 4 | commands_exhausted | **yes** | 4 | **2 (one crate delivered, ply 4)** | 15.2 | 282 | `probes/SOKOBAN_Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M_02_two_boxes.json` | `730a826596ee21db` |
| 4 | T | 02_two_boxes | false | 4 | commands_exhausted | **yes** | 4 | **3 (one crate delivered, ply 26)** | 12.1 | **3 961** | `probes/SOKOBAN_Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M_02_two_boxes.json` | `d1f21c0c4cf25edc` |
| 5 | M | 03_the_corner_waiting | false | 1 | commands_exhausted | no | 1 | 0 | 3.0 | 119 | `probes/SOKOBAN_Mellum2.1-12B-A2.5B-Thinking-Q4_K_M_03_the_corner_waiting.json` | `fc895de435cf7261` |
| 6 | I | 03_the_corner_waiting | false | 3 | commands_exhausted | **yes** | 3 | 0 | 3.0 | 363 | `probes/SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_03_the_corner_waiting.json` | `de563a646433bbf3` |
| 7 | Q | 03_the_corner_waiting | false | 3 | commands_exhausted | **yes** | 3 | 0 | 12.2 | 274 | `probes/SOKOBAN_Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M_03_the_corner_waiting.json` | `1d7cd885c8ed6396` |
| 8 | T | 03_the_corner_waiting | false | 3 | commands_exhausted | **yes** | 3 | 0 | 6.0 | ~129* | `probes/SOKOBAN_Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M_03_the_corner_waiting.json` | `591b93a102b8ff43` |

Entrants: M = `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M`, I = `MiMo-V2.6-Distill-Qwen-9B-Q4_K_M`,
Q = `Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M`, T = `Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M`.
The digest column is **the row's own sha256, truncated to 16 hex**; the full value is in each committed record
and in the commit that carried it. `moves` is the driver's own count of **board-changing** moves, not of
commands consumed (`attempted = 40` on every row). `wall_s` includes the model load and is not a clean speed
measurement — these cells ran while other llama-servers were resident and load average sat between 0.4 and 11.

\* Cell 8's wall time is **derived from the record's mtime and the launch time, not measured by the driver**:
this instrument records `load_s` but not `wall_s`. It is the only row where that is true, and it is marked for
that reason rather than presented beside the others as if it came from the same instrument.

## COUNT OF CELLS AT EACH END STATE

```
solved                 0
commands_exhausted     8   (all eight measured cells; give_up = 0 in every one)
load failure           0
terminated by card     0   (cell 4's termination, D1, was superseded by its own completed retake)
not started            0
```

**C1 is confirmed across all eight cells: 0 of 8 at `solved: true`. No entrant solved either level, and no
record shows a `give_up` — every measured cell spent its entire 40-command budget instead of resigning.**
That is itself a difference from the size curve, where the 9B Bonsai resigned at ply 10 on level 02
(`2e23325`): these four do not resign, they repeat a failing action until the budget ends.

## THE ONE SENTENCE THE CARD ASKED FOR

**Five of the eight measured cells got past ply 1, and two of them — independently — pushed a crate onto a
target: Qwythos on `02_two_boxes` at ply 4, and Triumvirate on the same level at ply 26, so C2's prediction
that no entrant would push a box is FALSE twice over and the answer to the card's surprise question is not
zero.**

Detail on the two box contacts, because they are different in kind:

- **Qwythos (cell 3)** walks four plies, delivers the upper crate, and then emits the same blocked `R` 36 times
  (`blocked = 36`, `not_an_action = 0`): 40 commands parsed, 4 board changes. Delivery at ply 4; no plan after it.
- **Triumvirate (cell 4)** — the low-rate entrant from D1 — does the same thing more slowly and with most of its
  budget spent on prose instead of commands: `not_an_action = 31` (31 of 40 turns hit the 64-token ceiling and
  opened with the literal word `Let's`, never emitting a command), `blocked = 5`, **9 commands parsed**, of which
  4 changed the board: `R` (ply 2), `R` (ply 14), `R` (ply 15), and the delivery `R` (ply 26). Final board:

```
########
#    @*#      * = the first crate, delivered
#      #
#  $  .#      the second crate and its target are one row down
########
```

Both stop in the top-right corner with the same geometry left: reaching the second crate's pushing square takes
eight plies (`D`, `L`, `L`, `L`, `D`, `R`, `R`, `R`) and neither entrant ever emits a `D` or an `L`. It is not a
solve and it is not close — but it is **box contact from two different weights**, which is more than one
entrant's accident, and it is the first time on this instrument that an entrant has moved a crate onto a target
before running out of commands.

**Cell 8 delivered nothing.** Its final board carries no `*` — three board changes, no crate on a target:

```
#######
#. #  #
# $   #
#    @#
#     #
#######
```

## THE RATE FINDING, AND WHY IT IS A ROW RATHER THAN AN EXCUSE

Cell 4 in the first window could not finish inside that window (~110 s/ply under load; 16 plies in ~1 700 s).
Re-run alone in the second window it **did** finish: 40 plies, 3 961 s wall, 12.1 s load, ~99 s/ply, returning
`commands_exhausted` rather than being killed. So the first termination was a **budget** statement, not a
capability one. The per-ply rate did not improve when the box quieted (0.52 tok/s decode in both windows), and
the cost is structural: Triumvirate burns **64 tokens on 31 of its 40 turns** on prose, where Qwythos burns 2.
That is the sharpest per-entrant number on this card, and it is orthogonal to solved:

```
entrant (02_two_boxes)   turns capped at 64 tokens   commands parsed   board changes
Mellum                          40 of 40                   0                0
MiMo                            38 of 40                   1                1
Qwythos                          0 of 40                  40                4
Triumvirate                     31 of 40                   9                4
```

Read it as a budget-attribution split: Mellum spends 100 % of the cap on talk, MiMo ~95 %, Triumvirate ~78 %,
Qwythos 0 %. Talking less is not sufficient — Qwythos never solves — but on this level it is necessary for
contact, and it is the only axis on which these four separate cleanly.

**Cell 8 is the control for that claim, and it holds.** The same entrant that spent 31 of 40 turns on prose on
level 02 spent **9 of 40** on level 03 (`not_an_action = 9`, `blocked = 28`, 3 board changes) — and its wall
time fell from **3 961 s to ~129 s** for the identical 40-command budget. So the prose leak is not a fixed
property of the weight: it moves with the level, and it is what the wall clock is actually measuring. Anyone
reading wall times on this card as a capability signal is reading prose volume.

## WHAT THIS TABLE SAYS ABOUT SEPARATION

- **Level 01 is not represented here at all** and must not be: it is solved in one move at every size that
  loads, so it separates nothing.
- **Level 02 separates the four entrants into two groups by box contact** (Q and T deliver a crate; M and I
  never touch one) and further separates them by rate and by command economy (Q at ply 4 with 40/40 commands
  parsed; T at ply 26 with 9/40).
- **Level 03 separates them by nothing but prose style** on contact — M emits `We`, I and Q walk into the wall,
  and T changes the board three times without delivering. Its value is as the control above.
- **Neither level produces a solve, so neither is a capability test yet** — they are an engagement test, and on
  engagement the ordering is Q > T > I > M, carried by level 02 alone.

## CELLS THAT REMAIN

None. Eight of eight are measured, committed, and on this table. The two cells this card reported as missing at
various points were both closed inside the card's own life: cell 4 by its completed retake (`535059d`), cell 8
by a Chair-taken background run after the `block_loop_detected` escalation. The reason cell 8 was ever judged
unaffordable is worth keeping, because it was WRONG in a way that matters: the card's budget model priced it
at ~4 000 s by extrapolating cell 4's wall time, when the actual cost on that level was ~129 s. The
extrapolation carried cell 4's prose volume into a level that does not produce it.

## ONE HOUSEKEEPING FACT THIS CARD MUST NOT BURY

`sokoban_run.py` derives the server-log path from the **cell** (entrant × level × reasoning setting), not from
the run. The cell-4 retake therefore **truncated D1's log at the same path** at 11:11:16 — the bytes named in
`DISCARDED-MANIFEST` D1 (16 007 B, sha256 `910379dc…`) no longer exist on disk. The retake's own log is preserved
under a run-specific name and hashed in that manifest (D1a). Nothing was deleted deliberately: the driver's
naming is the cause, and any future retake of a cell will overwrite that cell's log again.
