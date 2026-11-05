# RETIRED BOARDS -- what was retired, on what measurement, and where its old numbers still stand

> **STANDING CHANGED 2026-11-05:** the retired-board finding widened to the whole Sokoban set (all three
> boards are cleared by a fixed schedule, p\* = 1 / 7 / 6), so **the published Sokoban rankings are now
> WITHDRAWN — VOID as evidence of search**, not merely qualified. Nothing was deleted; six files carry a
> `## WITHDRAWN 2026-11-05` block. Full record and rebuild condition:
> **`WITHDRAWN_RANKINGS_2026-11-05.md`**. Decided by Mike on the Chair's recommendation.

**Filed 2026-11-05 by Chilly (Local Chair).** State, not a comment: the retirement is enforced by
`RETIRED_LEVELS` in `sokoban_run.py`, checked by `level_admission()` at ADMISSION, before the entrant is
resolved and before any server is spawned. Exit code **5** (distinct from 2 bad argument, 3 did not load,
4 this pair must not run).

## 1. What is retired

| Board | Level text sha256 | Verdict |
|---|---|---|
| `levels/01_one_push.txt` | `db6ca59655f0d7d1f1ce48e36e0b0c90a3bca5158b96a31a7a4fe37006a6a313` | **RETIRED** — not scorable, not loadable by this driver |

The key is the **level's text digest, not its name**: a copy renamed to `innocuous.txt` is the same board
and is refused identically (measured; see §4).

## 2. Why — the measurement, with its command

```
$ python3 degenerate_gate.py --json --event sokoban --board levels/01_one_push.txt
 "class": "periodic words of period <= 3 over sorted(sokoban.ACTIONS) = U D L R, repeated to the cap 40",
 "verdict": "DEGENERATE",
 "why": "the fixed stream 'R' (period 1) clears the board",
 "streams_evaluated": 84,
 "n_hits": 45,
```

* The constant stream **`R` clears the board in ONE move**, and `moves` = 1 on that hit.
* **The board's optimal solution IS that same single action.** A stream that never observed the board
  reaches the same state as the best play. That is why this is a retirement and not a caveat: the board
  was never a puzzle.
* **45 of 84** periodic words of period ≤ 3 clear it (the class played to the registered cap 40).
  The cabinet's report said 46 of 84; the difference is the class, not the board — 46 is what you get
  with short words played ONCE, 45 with each word repeated to the cap. **A gate must publish its class
  or its count means nothing**; this file's count is the repeated-to-cap one, and `degenerate_gate.py`
  prints the class beside every number.
* The two other boards pass **at the declared width 3** (`02_two_boxes` and `03_the_corner_waiting`:
  **PASS**, control fired, 0 hits of 84). **They do not survive a wider class — §7, which is the
  larger finding and the reason this file is not just about one board.**

## 3. What was NOT done, on purpose

* **Nothing was deleted.** The level file stays in the tree because it is `degenerate_gate.py`'s
  **positive control** — the one object that proves the detector still fires. An archived control would
  make every later PASS a claim about a detector nobody can exercise.
* **No results were rewritten.** Stored rows are annotated, not edited; §5.
* **No replacement board was added.** A new board needs its own oracle, a measured freeze, and a passing
  gate run before it can rank anyone. A proposal is a proposal; it is not a board.

## 4. The refusal, exercised rather than described

```
$ python3 sokoban_run.py --entrant /nonexistent.gguf --level levels/01_one_push.txt
  BOARD RETIRED: levels/01_one_push.txt is levels/01_one_push.txt (sha256 db6ca59655f0d7d1...) and cannot be played.
      ... rc=5
$ python3 sokoban_run.py --entrant /nonexistent.gguf --level <copy of the same bytes under another name>
  BOARD RETIRED: .../innocuous.txt is levels/01_one_push.txt (sha256 db6ca59655f0d7d1...) ... rc=5
$ python3 sokoban_run.py --entrant /nonexistent.gguf --level levels/02_two_boxes.txt
  ENTRANT ABSENT: /nonexistent.gguf                                    rc=2   <- the gate does not block a live board
$ python3 sokoban.py --self-test
  ALL CONTROLS PASS   --  49/49
```

## 5. Where the old numbers still stand — QUALIFIER, annotate-don't-delete

These published artifacts contain rows on `01_one_push`. **Their numbers are not withdrawn**; they are
qualified: any rate, table or ranking that pools `01_one_push` includes a board that a single constant
key clears, so that pooled figure is an **upper bound on nothing** — it must not be read as evidence of
planning, and a re-score must drop those rows rather than re-weight them.

Each of these files carries a `## QUALIFIER 2026-11-05` block appended at its end naming this file:

| Artifact | Lines mentioning `01_one_push` |
|---|---|
| `suite2/TABLES2.md` | 4 |
| `suite3/TABLES3.md` | 4 (two of them `solved=True`) |
| `SUITE_RESULTS_multi_model_sitting2_2026-10-25.md` | 4 |
| `SOKOBAN_FRONTIER_RESULTS.md` | 1 |
| `SOKOBAN_VERDICT_1.md` | 2 |
| `SOKOBAN_VERDICT_2.md` | 6 |

Counts are `grep -c '01_one_push' <file>` at the time of filing. The two `solved=True` rows in
`suite3/TABLES3.md` are the Ministral (plan_len 1) and Ornith (plan_len 2) rows — the same two rows
`grep -c "solved=True" suite3/TABLES3.md` → `2` returns, which is also every solved row in that table.
**A plan of length 1 on this board is the board's own optimum, so those two rows measure emission, not
search.**

## 6. What the gate does for the other events, and what it cannot yet say

| Event | Class | Verdict on its boards |
|---|---|---|
| sokoban | periodic words, period ≤ 3, cap 40 | `01` DEGENERATE (control, **p\*=1**) · `02` PASS at width 3, **p\*=7** · `03` PASS at width 3, **p\*=6** |
| zork | periodic streams, period ≤ 2, over the world's own vocabulary, budget 24 | `zork_01` **DEGENERATE** at period 2 · `zork_02` **PASS** |
| chess | **policy** class: always the first / always the last legal move | **UNDETERMINED** — class named, probe not built |

`zork_01` is the finding Jarvis predicted the mechanism of and got wrong in the detail worth having: **`north` alone does not escape** — it walks into the gate without the key and the crawl ends
`gate_locked`. The clearing stream is the **two-command cycle `take key ; north`** (period 2), and the
alias form `take brasskey ; n` clears it in 2 commands too. So the degenerate class for a word-alphabet
event is *periodic*, not *constant*: a gate that only tried constant commands would have passed the very
board that fails.

## 7. THE SET-WIDE FINDING — retiring board 01 is necessary and not sufficient

A boolean verdict at a chosen width invites exactly the defect it is meant to catch: a board passes
because the width was set below the period that clears it. So the gate also reports **p\*, the board's
periodic clearance index** — the smallest period p for which SOME word of length p, repeated to the
registered cap 40, clears the board. p\* does not depend on anyone's choice of width, and it is printed
beside the board's own optimal solution length.

```
$ python3 degenerate_gate.py --event sokoban --board levels/<board>.txt --max-period 8
```

| Board | p\* | clearing word (fixed schedule) | moves it takes | optimal solution (solver) | optimal moves |
|---|---|---|---|---|---|
| `01_one_push` | **1** | `R` | 1 | `R` | 1 |
| `03_the_corner_waiting` | **6** | `RULDLU` | 6 | `RULDLU` | 6 |
| `02_two_boxes` | **7** | `DDRLUUR` | 28 | `DDRRRRULLURR` | 12 |

Optimal lengths are `sokoban_solver.solve_text` on the same files (`01` → `moves 1, solution R`; `03` →
`moves 6, solution RULDLU`; `02` → `moves 12, solution DDRRRRULLURR`).

Three consequences, in order of how much they cost:

1. **`03_the_corner_waiting` is degenerate in the STRONG form** — its optimal solution `RULDLU` IS the
   period-6 cycle the gate finds. Like board 01, it was never a puzzle. It passed the cabinet's 84
   streams only because the width (3) was set below its period (6).
2. **`02_two_boxes` is degenerate in the operative sense** — a fixed 7-cycle clears it in 28 moves,
   inside the 40-move cap, without ever reading the board. Its optimum (12) is not that cycle, so the
   board is not *designed* degenerate; it is merely *clearable* by a schedule, which is the property the
   score rewards.
3. **Therefore all three boards are cleared by fixed schedules of period ≤ 7, and the cabinet's
   rankings on this board set are void** — not just the board-01 rows. The qualifier in §5 is a floor,
   not the whole exposure: a rate pooled over any of the three pools a board a schedule clears.

**What this means for the replacement — and why no candidate is proposed here.** The third slot is not
the problem; the whole set is. A replacement board must satisfy `p*` **greater than the width the event
declares**, and that width must be justified by coverage and cost before any board is measured against
it. One candidate was built and rejected on measurement rather than on taste: a single-box detour
(`#  .  / # $   / #@    `) passes at width 3 (`0/84`) and falls at width 4 (`RULU`, 2 of 340). **A board
that passes 84 streams has been shown almost nothing about its p\*,** which is the argument for making
p\* the field that travels with a board instead of the verdict at a width someone picked.

**Where this leaves the cabinet, stated plainly:** it currently has **no board that a fixed schedule
cannot clear within the cap.** That is a set-level failure, it is measurable, and it is Jarvis's and
Mike's to price — not something a replacement invented in a letter can fix.
