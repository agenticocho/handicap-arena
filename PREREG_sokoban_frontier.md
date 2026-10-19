# PRE-REGISTRATION — SOKOBAN FRONTIER: 02_two_boxes AND 03_the_corner_waiting AGAINST FOUR FRESH 9B-CLASS ENTRANTS

**Card:** `t_efd6df81` (written and run by Ocho; the card is the Chair's).
**Written BEFORE any cell on this card was run.** No probe file under `probes/` exists for any of the four
entrants named here (checked at the pre-image: `ls probes/ | grep -i -E "Mellum|MiMo|Qwythos|Triumvirate"`
returns nothing). The table at §6 is typed with every number column EMPTY, and it was typed before the first
command. A table written after the data is a table that can be drawn to fit the data.

**Repo tip at the pre-image:** `2e23325d191f0f7ab5ee4b7d09113b2d40e99d0d` (main, clean).

---

## 1 THE INSTRUMENT — UNCHANGED, NAMED BY DIGEST AND BY COMMIT

```
sokoban_run.py                    62271 B   sha256 80259a1549e12a5085a46d312d875d285b63b09210da7db956f83268e8b2872c
levels/02_two_boxes.txt              45 B   sha256 7549657f1768607cefab6d892b1756b1cabf23f51144a7679d76f331b38a57d7
levels/03_the_corner_waiting.txt      48 B   sha256 77d18407a001da292b2f1dcf8054ed40ddc2038563f23b96861a362c78cf23d6
```

**Nothing under `levels/` and nothing in `sokoban_run.py` is edited by this card.** The two instruments above
are frozen at the digests printed here; the digests are printed so that a reader can tell whether the
instrument that produced the table is the instrument described here, and so that this card cannot quietly
become an instrument change.

**The server binary is the DECLARED DEFAULT — `--llama-server` is NOT passed on any cell.** The default is
`/home/chilly1/llama.cpp/build/bin/llama-server` (`sokoban_run.py:40`). None of the four entrants declares
`prism.hadamard`, so `refuse_a_ternary_entrant_under_a_blind_binary()` will not fire; the prism fork is the
wrong binary here and passing it would be a different cell.

**The launch, as the record will carry it** (`server_argv`, `sokoban_run.py:423-431`):
`llama-server -m <entrant> -c 4096 -ngl 0 --port <port> --no-webui --reasoning off`.
`-ngl 0` means CPU inference by the instrument's own design, not by choice of this card; a cell therefore
measures the model, not the card's VRAM budget. Reasoning is `off`, declared in `PREREG_sokoban.md` — the
answer in this cabinet is one letter, and a thinking model puts deliberation where the answer belongs.

## 2 THE TWO LEVELS — QUOTED IN FULL, BECAUSE A LEVEL IS CONTENT

```
02_two_boxes.txt               03_the_corner_waiting.txt
########                       #######
#@  $ .#                       #. #  #
#      #                       # $   #
#  $  .#                       # @   #
########                       #     #
                               #######
```

Both have been run at 2B, 4B and 9B (the size curve, `2e23325`) and **neither has ever been solved by any
entrant at any size.** Level `01_one_push` is excluded by the card and by this pre-registration: it is solved
in one move at every size that loads, so it separates nothing and a row on it would be decoration.

## 3 THE FOUR ENTRANTS — FRESH, NON-TERNARY, NONE HAS PLAYED SOKOBAN

| # | label (as the record will name it) | file size | file, as named on the command line |
|---|---|---|---|
| M | `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M` | 8 071 295 264 B | `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf` |
| I | `MiMo-V2.6-Distill-Qwen-9B-Q4_K_M` | 5 841 049 120 B | `MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf` |
| Q | `Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M` | 5 887 667 808 B | `Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M.gguf` |
| T | `Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M` | 5 629 136 320 B | `Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M.gguf` |

**A DIGEST OF A MULTI-GB MODEL ON THIS BOX IS A READING, NOT AN ARTIFACT IDENTITY.** Measured in
`t_cdd433bb`: repeated `sha256` of the same path minutes apart differ while size/mtime/ctime/inode hold, at
roughly one bit per 0.3–1.5 GB in motion. The digests taken at the pre-image are therefore recorded here as
**readings at this instant**, and they are NOT what the table cites:

```
Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf            sha256 ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755
MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf               sha256 96ef34b99ae63316c3065383bbbaa34861dd8741883cf17ef8017454887a4bbc
Qwythos-9B-Claude-Mythos-5-1M-MTP-Q4_K_M.gguf       sha256 6e6a41b505911f333a64624854e3dc21ac23bd40d42001ac8c1c7985bd5373cd
Triumvirate-Qwopus-MiMo-Ornith-9B-Coder.i1-Q4_K_M.gguf  sha256 02690ebf488c13cee2ce9bb9eaae982856721e7544c8bbf1a609cee05db22c38
```

The identity of an entrant in the table is **the path it was launched from plus its byte size plus the
`entrant_digest` the run itself wrote** — the last of which is a third reading of the same file, taken while
the binary was memory-mapping it, and is reported beside the rest, not in place of them. **No cell's verdict
depends on a digest**, and none will be re-run because a digest moved.

## 4 THE CELL, THE ORDER, AND THE PORTS

A cell is one `(entrant, level)` pair at `--cap 40`. **The cap is 40 on every cell and is not lowered on any
cell**, including a cell that stalls; a cap-6 or cap-10 record is a different cell and will not enter this
table (`2e23325` had to re-take exactly such a row).

Eight cells, in this order — **level 02 for all four entrants before level 03 for any of them**, so that a
budget failure leaves four rows across two levels rather than one row across eight:

```
cell 1   M  02_two_boxes             port 8771
cell 2   I  02_two_boxes             port 8772
cell 3   Q  02_two_boxes             port 8773
cell 4   T  02_two_boxes             port 8774
cell 5   M  03_the_corner_waiting    port 8775
cell 6   I  03_the_corner_waiting    port 8776
cell 7   Q  03_the_corner_waiting    port 8777
cell 8   T  03_the_corner_waiting    port 8778
```

One foreground command per cell, no polling loop:

```
python3 sokoban_run.py --entrant <entrant>.gguf --level levels/<level>.txt --cap 40 --port <port>
```

**The probe JSON is committed immediately after each cell**, naming the cell, before the next cell starts.
Never batched to the end: a finished measurement that is untracked is a measurement nobody can find.

## 5 THE CRITERION, STATED SO IT CAN BE APPLIED WITHOUT ME

**A cell is SOLVED iff the driver reports `solved: true` in the record it writes at
`probes/SOKOBAN_<entrant-label>_<level>.json`.** Nothing else is a solve — not a good-looking board, not a
near-miss, not a `trace` that ends on a crate-and-target. Every other end state is reported under the
`ended` string the driver itself wrote (`gave_up`, and whatever else it writes), verbatim, and is a
non-solve.

Cells that never produce a playable record are still ROWS, not omissions:

- **load failure** (binary cannot load the file, rc from the server, no turns recorded) is a row with
  `solved = false`, `ended = load_failure` and the record's own bytes on disk;
- a cell whose process died mid-run is a row with what the record says, and
- a record this card chooses not to publish goes to `DISCARDED-MANIFEST.txt` with its `sha256` and the binary
  it named BEFORE anything is deleted. **A discard that cannot be named afterwards is a deletion.** This card
  expects zero discards; the file exists so that the expectation is checkable.

## 6 THE CLAIM UNDER TEST, AND THE TABLE SHAPE

**C1 (primary, falsifiable, predicted from the whole prior record):** none of the eight cells is SOLVED.
The prediction is a specific number: **0 of 8 cells at `solved: true`.**

**C2 (secondary, the one number on this card that could surprise the Chair):** whether any entrant **gets
past ply 1** on either level. Defined here, before the data, because it must not be defined after:

> A cell "got past ply 1" iff its `turns` list contains a turn at ply index >= 1 whose `token` is one of the
> four legal moves. Equivalently `moves >= 2`: the entrant produced a legal action AFTER its first one.
> This is the primary reading. Two weaker readings are reported beside it and neither substitutes for it:
> (a) **any board change at all beyond the start**, and (b) **any box PUSH** — a turn after which a `$`/`*`
> occupies a different cell than the turn before. The prior record's 9B Bonsai walked 4 plies on level 02 and
> 3 on level 03 without ever pushing a box, so (b) is the reading that separates walking from playing.

**C2 as a prediction:** no entrant pushes a box on either level, and the number of cells with `moves >= 2`
is **<= 2 of 8** (the historical maximum engagement on these two levels is 4 plies, set by the 9B Bonsai on
level 02; four fresh entrants of the same size class should not beat it). **If any entrant pushes a box, C2's
prediction is FALSE and that is the finding.**

**THE TABLE, SHAPE FIXED NOW, EVERY NUMBER COLUMN EMPTY:**

| cell | entrant | level | solved | moves | ended | plies>=1 (moves>=2) | any board change | any box push | load_s | wall_s | record | record sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | M | 02_two_boxes | | | | | | | | | | |
| 2 | I | 02_two_boxes | | | | | | | | | | |
| 3 | Q | 02_two_boxes | | | | | | | | | | |
| 4 | T | 02_two_boxes | | | | | | | | | | |
| 5 | M | 03_the_corner_waiting | | | | | | | | | | |
| 6 | I | 03_the_corner_waiting | | | | | | | | | | |
| 7 | Q | 03_the_corner_waiting | | | | | | | | | | |
| 8 | T | 03_the_corner_waiting | | | | | | | | | | |

Rows are cells, in run order. `wall_s` is wall-clock seconds for the command, INCLUDING the model load, and
is reported as a fact about the box under the load it actually had — other work was running on this machine
during the sweep (load average ~10.8 at the pre-image), so a wall time is not a clean per-model speed
measurement and will not be narrated as one.

**WHAT IS NOT PREDICTED, AND WILL NOT BE:** the eight `moves` values, the eight `ended` strings, the eight
wall times, and the eight `entrant_digest` readings. A prediction that can be edited to match its own result
is not a prediction.

## 7 WHAT WOULD MAKE THIS CARD'S TABLE WRONG RATHER THAN MERELY DISAPPOINTING

- A cell run at any cap other than 40, or on any level other than the two named, **does not enter the table**
  (it may be reported beside it, labelled).
- A cell run against the prism fork instead of the declared default **does not enter the table**: the binary
  is part of the cell, and the record carries `server_binary_digest` so the substitution would be visible.
- A cell whose record is missing or uncommitted **is not a cell**: an unrecorded run is a run nobody can
  check, and the last two cards on this instrument both left real measurements untracked.
- If the budget runs out, the cell in progress is finished and committed, and the card is BLOCKED with the
  partial table and the list of cells that remain. **Six committed cells and a blocked card is a success
  with a note; eight cells and a crash is a total loss.**
