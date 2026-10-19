# SOKOBAN FRONTIER — RESULTS, PARTIAL (6 of 8 cells measured)

Card `t_efd6df81`. Pre-registration: `PREREG_sokoban_frontier.md`, commit `368c166`, **written and committed
before the first command ran** (no probe for any of the four entrants existed then; checked).
Instrument: `sokoban_run.py` 62 271 B sha256 `80259a15…`, levels `02`/`03` at `7549657f…`/`77d18407…`,
declared default binary, `--cap 40` on every cell, `--llama-server` on none.

**This is a PARTIAL table and it is being reported as one.** Six cells are committed; cell 4 was terminated at
16 of 40 plies because it could not finish inside the run budget and is named in `DISCARDED-MANIFEST.txt` (D1);
cell 8 was not started. The card is blocked, not completed, so the two missing cells are visible on the board
rather than implied by a finished card.

## THE TABLE

| cell | entrant | level | solved | moves | ended | plies>=1 (moves>=2) | any board change | any box push | load_s | wall_s | record | record sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M | 02_two_boxes | false | 0 | commands_exhausted | no | 0 | 0 | 3.0 | 121 | `probes/SOKOBAN_Mellum2.1-12B-A2.5B-Thinking-Q4_K_M_02_two_boxes.json` | `59fdcad94f46353f` |
| 2 | I | 02_two_boxes | false | 1 | commands_exhausted | no | 1 | 0 | 3.0 | 376 | `probes/SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_02_two_boxes.json` | `c9a7f5d98a212d68` |
| 3 | Q | 02_two_boxes | false | 4 | commands_exhausted | **yes** | 4 | **2 (one crate delivered)** | 15.2 | 282 | `probes/SOKOBAN_Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M_02_two_boxes.json` | `730a826596ee21db` |
| 4 | T | 02_two_boxes | — | — | **TERMINATED at 16/40 plies** | — | — | — | — | ~1 700 | **no record written**; log `910379dc2e036b7c`, see DISCARDED-MANIFEST D1 | — |
| 5 | M | 03_the_corner_waiting | false | 1 | commands_exhausted | no | 1 | 0 | 3.0 | 119 | `probes/SOKOBAN_Mellum2.1-12B-A2.5B-Thinking-Q4_K_M_03_the_corner_waiting.json` | `fc895de435cf7261` |
| 6 | I | 03_the_corner_waiting | false | 3 | commands_exhausted | **yes** | 3 | 0 | 3.0 | 363 | `probes/SOKOBAN_MiMo-V2.6-Distill-Qwen-9B-Q4_K_M_03_the_corner_waiting.json` | `de563a646433bbf3` |
| 7 | Q | 03_the_corner_waiting | false | 3 | commands_exhausted | **yes** | 3 | 0 | 12.2 | 274 | `probes/SOKOBAN_Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M_03_the_corner_waiting.json` | `1d7cd885c8ed6396` |
| 8 | T | 03_the_corner_waiting | — | — | **NOT STARTED** | — | — | — | — | — | — | — |

Entrants: M = `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M`, I = `MiMo-V2.6-Distill-Qwen-9B-Q4_K_M`,
Q = `Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M`, T = `Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M`.
The digest column is **the row's own sha256, truncated to 16 hex**; the full value is in each committed record
and in the commit that carried it. `wall_s` includes the model load and is not a clean speed measurement —
another llama-server was resident and load average sat at 5–11 throughout.

## COUNT OF CELLS AT EACH END STATE

```
solved                 0
commands_exhausted     6   (all six measured cells; give_up = 0 in every one)
load failure           0
terminated by card     1   (cell 4, DISCARDED-MANIFEST D1)
not started            1   (cell 8)
```

**C1 is confirmed for the six cells measured and untested for the two not measured: 0 of 6 at
`solved: true`. No entrant solved either level, and no record shows a `give_up` — every measured cell spent
its entire 40-command budget instead of resigning.** That is itself a difference from the size curve, where the
9B Bonsai resigned at ply 10 on level 02 (`2e23325`): these four do not resign, they repeat a failing action
until the budget ends.

## THE ONE SENTENCE THE CARD ASKED FOR

**Three of the six measured cells got past ply 1, and one of them pushed a box: Qwythos walked four plies on
`02_two_boxes` and delivered one of the two crates onto its target at ply 4, then spent the remaining 36 turns
walking into the wall (blocked = 36) without ever turning — so C2's prediction that no entrant would push a
box is FALSE, and the surprise the card was looking for is in cell 3.**

Detail, because the shape matters more than the number: after ply 4 the board is

```
########
#    @*#      * = the first crate, delivered
#      #
#  $  .#      the second crate and its target are one row down, four columns left of the player
########
```

The player is in the top-right corner facing the wall. The second crate sits one row below the player's own
row, with its target three columns to the right of it — reaching the pushing square takes eight plies
(`D`, `L`, `L`, `L`, `D`, `R`, `R`, `R`), and the entrant emitted no `D` and no `L` in its 36 remaining turns:
it emitted the same blocked `R` 36 times. It is not a solve and it is not close — but it is **box contact**,
showed, and it is the first time on this instrument that an entrant has moved a crate onto a target before
running out of commands.

## WHAT THIS TABLE SAYS ABOUT SEPARATION

- **Level 01 is not represented here at all** and must not be: it is solved in one move at every size that
  loads, so it separates nothing.
- **Within this sample, level 02 separates the four entrants by box contact (Q yes, M and I no) and level 03
  separates them by nothing but prose style**: M emits `We` 39 times, I and Q walk into the wall. Neither
  level produces a solve, so neither is a capability test yet — they are an engagement test, and on engagement
  the ordering is Q > I > M on both levels.
- **The two missing cells are the fourth entrant's**, and they are missing for a measured reason, not a
  convenient one: that entrant generated at ~0.56 tok/s (≈110 s per ply against 6–9 s for the others), which
  is roughly 4 400 s for a cap-40 cell. Until those two cells are run, **no statement about
  Triumvirate on this instrument is supported by anything**, and none is made here.

## CELLS THAT REMAIN

```
cell 4   Triumvirate  02_two_boxes            -- re-run needed (no artifact exists; the gate will admit it)
cell 8   Triumvirate  03_the_corner_waiting   -- not started
```

Both are ordinary cap-40 cells on the unchanged instrument; re-running them needs no `--overwrite-artifact`
because no record exists at either path. The budget that stopped cell 4 was the card's own 5 400 s run budget,
and the 110 s-per-ply rate is a property of that entrant on this box under this load, not of the instrument.
