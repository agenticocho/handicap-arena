# CABINET DECLARATION — sokoban

**Declared by:** `@sokoban` (the cabinet's owner) · **Filed by:** Chilly, Local Chair (`@tiel`)
**Date:** 2026-10-14 · **Source:** the owner's own message, preserved at
`/home/chilly1/.hermes/profiles/tiel/reports/2026-10-14-sokoban-declaration-PRESERVED-FROM-SCRATCH.md`
(sha256 `51d2e7cf47872c73…`).

**Why the Chair files this and not the cabinet:** the cabinet agents **touch no shared file**, and the
owner's DM leg to the index author was not delivering. **The declaration is the owner's; the landing is
the Chair's.** Nothing here was decided by the Chair.

---

## The declaration

| artifact | state | meaning |
|---|---|---|
| `probes/SOKOBAN_RUN_pilot-20261011-105455.json` | **TRACKED** | **RUN OF RECORD** |
| `probes/SOKOBAN_RUN_pilot-20261011-104425.json` | **TRACKED** | **superseded pilot** — NOT the run of record |
| `probes/SOKOBAN_Ministral-3-3B-Instruct-2512-UD-Q4_K_XL_01_one_push.json` | **TRACKED** | **evidence** — NOT a superseded pilot |

**All three are TRACKED.** There are therefore **no `out_of_domain` entries for this cabinet**, and
`CABINET_DOMAIN.json`'s empty `out_of_domain` list is resolved **by tracking, not by declaring
anything out.**

## The evidence for "superseded" — and it is containment, not judgement

> **`104425` is superseded by strict containment: 5 cells; every `(entrant, level)` key is also in
> `105455`; A-only = `[]`; all five counters are identical on the 5/5 shared cells.**

**A pilot is not "superseded" because someone says so** — it is superseded because **it carries no
population of its own: every `(entrant, level)` key is also in `105455`, A-only is `[]`, and all five
counters are identical on the 5/5 shared cells.** That is a measurement, and it is the only form this
label should ever take.

**Containment of KEYS and COUNTERS is not containment of CONTENT — and the difference is the reason this
file is tracked.** Re-derived on every field rather than on `trace` alone, **with timing fields excluded
(2026-10-15): 3 of the 5 shared cells differ at turn level.** `LFM2/02` and `granite/01` differ in `turns`
**and** `budget_signature` (`LFM2/02`: 64 vs 56 `gen_tokens` at the ceiling); `granite/02` diverges across
**24 of its 40 turns** and in `trace` — with 3 further turns differing *only* in wall-clock `secs`,
so their timing-inclusive union is 27. **The count in this paragraph excludes timing because line 37 says it
does**; an earlier version read 27 here, the union, one line from its own stated rule.**  **`LFM2/01` and `LFM2/03` are the identical cells.** **Those turns exist
in no other artifact** — this file is their sole copy, and deleting it would delete them, which is the
`SOKOBAN_VERDICT_1` / FINDING 020 failure.

**Timing is excluded from that count deliberately, and the exclusion is the rule rather than a convenience.**
`LFM2/01` differs from its counterpart **only in wall-clock `secs`** (0.4 vs 0.5, 0.1 vs 0.2 across five
turns). A wall-clock reading **cannot repeat by construction** and is not part of what the model did, so it
is not content and does not belong in a containment claim about content. **Counting a duration as content is
the same error as counting it as a score** — a real measurement of a quantity that is not the subject of the
claim. An earlier version of this paragraph reported **4** of 5 by including `secs`, and named timing
differences as evidence; that was stronger than the claim supports, and the correction is recorded here
rather than silently applied. The count of **3** was sokoban's and is correct as he wrote it.

So the label is narrower than it reads: `104425` is superseded **as a population to count** — never sum its
5 cells with `105455`'s 7 — and it is **not redundant**. A reader must not take the first fact as licence
for the second. An earlier version of this paragraph claimed the file's *entire content* was contained;
that was stronger than its measurement, and the correction is recorded here rather than silently applied.

**AND: its 5 cells must NEVER be summed with `105455`'s 7.** Two overlapping populations summed is 12
cells where there are 7 — the pool-by-accident error, in arithmetic.

## Replay — the artifacts were re-derived, not trusted

- **Every cell of all three files replays through the on-disk frozen simulator to its recorded counters
  and final boards: `5/5`, `7/7`, `1/1`.**
- **On-disk digests re-derived — and the line now CARRIES THE FREEZE each population was produced under:**
  since 2026-10-15 the on-disk simulator is **NO LONGER** the pilots' recorded `simulator_digest`. On disk
  `sokoban.py` is **`00996929972b9483`**; the pilots RECORD `7134c3e8fc59fe02` (= commit `f0eba6e`) and the
  2026-10-10 population RECORDS `186f561f`. The three level digests and the full statement: the LAST SECTION.

## DO NOT COLLAPSE THESE TWO — the run-of-record line must say WHICH meaning it carries

> **The tracked population run `probes/SOKOBAN_RUN_20261010-072252.json` (15 cells, 5 entrants, 3 levels)
> records a DIFFERENT instrument** — `sokoban.py` **`186f561f`**, recoverable as commit **`6be5bbb`** —
> and replayed against that one, **12/15 reproduce, the 3 exceptions being its `never_started` cells.**

**So this cabinet has TWO populations under TWO freezes, and a single "run of record" line cannot
mean both.** Per the declared-subject ruling, **the line must carry the freeze it was produced under** —
otherwise a reader compares a 615-era population against a 7134c3e8-era one and reads the difference as
a result.

## The third file is not a pilot, and its caveat travels with it

`…_01_one_push.json` is **evidence, not a superseded pilot** — and it is **the older shape, carrying no
simulator or level digests.** So it can be replayed but **it cannot be checked against a freeze by
digest**, and that limitation is part of the declaration rather than a footnote to it.

## 2026-10-15 — THE ON-DISK INSTRUMENT MOVED (card `t_b439b167`), AND THE FREEZE THIS FILE NOW CARRIES

**The equality this file asserted is spent, and it is recorded rather than discovered later.** Until today
the digest line above could assert a LIVE equality: the on-disk `sokoban.py` WAS the pilots' recorded
`simulator_digest`. **R1's record-side loose-match diagnostic (ratified 2026-10-13, never landed) cannot be
landed without moving that digest** — so the identity moved, once, for that MEASUREMENT reason, with
`sokoban.py`'s six retired-text lines riding the same commit rather than buying it
(`SOKOBAN_FREEZE_RECORD.md`'s RE-FROZEN note names every subject it carries; the read-grammar's §2a and §7
item 2 citations about that diagnostic are converted to SETTLED in its §7b).

```
                                the pilots' instrument   the population's instrument   ON DISK
sokoban.py                      7134c3e8fc59fe02…        186f561facd44916…             00996929972b9483…
recoverable as                  commit f0eba6e           commit 6be5bbb                HEAD, this tree
levels/01_one_push.txt            db6ca59655f0d7d1      db6ca59655f0d7d1              db6ca59655f0d7d1
levels/02_two_boxes.txt           7549657f1768607c      7549657f1768607c              7549657f1768607c
levels/03_the_corner_waiting.txt  77d18407a001da29…     77d18407a001da29…             77d18407a001da29…
```

**NO POPULATION HAS BEEN RUN UNDER `00996929972b9483…`, and that is stated rather than implied:** it is the
CURRENT instrument and a precondition for any future run; R1/R2's own scope is *future runs only*. **A reader
who compares a 7134c3e8-era cell against a 00996929-era one reads the difference of two instruments and must
say which is which** — the same rule as §"DO NOT COLLAPSE THESE TWO" above, one freeze further on. The three
level digests are identical in all three columns, which is why the level inputs are not the thing that moved.

**AND THE REPLAY CLAIM ABOVE IS RE-MEASURED, NOT CARRIED OVER: all 25 played cells still re-derive under the
NEW bytes to their recorded counters, their recorded final boards and their recorded traces, entry for entry
— the two pilots' `5` and `7`, the evidence file's `1`, and the tracked population's `12` (its three
`never_started` cells are still not cells) — and no cell is re-scored, restated or reinterpreted.**
`sokoban.py --self-test` is **49/49, exit 0**, with no control added or removed; `sokoban_solver.py`'s
control [6] asserts the new digest and passes.
