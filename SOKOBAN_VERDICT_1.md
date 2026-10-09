# SOKOBAN — FIRST POPULATION RUN, ASTERISKED, WITH A6 APPLIED

**Run of record:** `probes/SOKOBAN_RUN_20261009-1247_NEW_LEGEND_RECOVERED_FROM_LOG.json`
**Status:** INSTRUMENT-HISTORY-CONFOUNDED. Read the asterisk before the numbers.

---

## THE ASTERISK

```
~12:45  FIRST RUN launched, OLD legend      -> its artifact is SOKOBAN_RUN_20261009-1245_OLD_LEGEND_IS_FIRST_RUN
~12:46  legend FIXED (prose symbols, no pseudo-field labels)
~12:47  RE-RUN launched, NEW legend          -> artifacts OVERWRITTEN; numbers survive only in logs/
~14:05  the FIRST run finished LAST and won the shared path
```

**TWO RUNS, ONE ARTIFACT PATH, AND A RUNNING PROCESS DOES NOT RE-READ ITS MODULE.** The first run kept the
prompt I had already declared defective, for its whole life. **The re-run's per-turn traces are LOST** — a log
is not a record format — and its counters are recovered verbatim from its own output. **FINDING 020.**

**AND THE CONSEQUENCE FOR READING THIS PAGE: the two runs are DIFFERENT INSTRUMENTS.** The old-legend run is
**not** a low score; it is a run of a **different game** (`Fill In The Form`). **The controlled comparison
between them exists and is the A/B, not these population numbers.**

## THE NUMBERS — A6 APPLIED

**UNREADABLE IS CARRIED INSIDE THE DENOMINATOR** as a non-pass; `never_started` is outside and separate;
`zero measured` would be an ERROR, and did not occur.

```
cells 10   PLAYED 7   NEVER STARTED 3 (all "server exited rc=1")

level          played  solved  moves  attempted  blocked  not_an_action  give_up
01_one_push         3       1      1         82        1             80        0
02_two_boxes        4       0      4        123       36             83        0
```

**PER ENTRANT — the five counters, NEVER MERGED, taken from the record and not from memory:**

```
LFM2-350M-Extract-Q4_K_M       01  attempted 40  blocked  0  not_an_action 40   give_up 0   moves 0
LFM2-350M-Extract-Q4_K_M       02  attempted 40  blocked  0  not_an_action 40   give_up 0   moves 0
granite-3.3-2b-instruct        01  attempted  2  blocked  1  not_an_action  0   give_up 0   moves 1  SOLVED
granite-3.3-2b-instruct        02  attempted 40  blocked 36  not_an_action  0   give_up 0   moves 4
Qwen3.5-4B-UD-Q4_K_XL          01  attempted 40  blocked  0  not_an_action 40   give_up 0   moves 0
Qwen3.5-4B-UD-Q4_K_XL          02  attempted  3  blocked  0  not_an_action  3   give_up 0   moves 0
Qwen3.5-9B-Q4_K_M              01  NEVER STARTED -- server exited rc=1
Qwen3.5-9B-Q4_K_M              02  attempted 40  blocked  0  not_an_action 40   give_up 0   moves 0
Ternary-Bonsai-2-27B-PQ2_0     01  NEVER STARTED -- server exited rc=1
Ternary-Bonsai-2-27B-PQ2_0     02  NEVER STARTED -- server exited rc=1
```

**A NOTE ON HOW THESE NUMBERS GOT HERE, BECAUSE THE FIRST DRAFT OF THIS TABLE DID NOT MATCH THE FILE.**
The draft was written from memory of the recovery output and it had **four errors**: it put NEVER STARTED on
`Qwen3.5-4B/01` when it belongs to `Qwen3.5-9B/01`, recorded `Qwen3.5-4B/02` as attempted 43 when the record
says **3**, and carried level totals of 4 and 77 where the record says **82** and **123**. **Every number above
is now read out of the artifact.** *A table written from memory of a file is a second copy of the truth, and
this document exists because of what second copies do.*

**REASON COUNTS SEPARATE FROM EVERY TOTAL: 7 played, 3 never started.** *A population that never ran is not
evidence about the population*, and a merged `0 of 10` is not a result.

## OUTCOME ROW 4, APPLIED AS WRITTEN

**`PREREG_sokoban.md` row 4: if the population cannot push a single crate, that IS the result, reported with
the population named, not re-scoped.** **The population made FIVE successful moves across two levels — one
entrant, `granite-3.3-2b`, on both — and ONE CELL SOLVED.** So row 4 does not fire as a clean null and the
event is not re-scoped either way.

**AND THE FIVE MOVES ARE THE FINDING: `granite-3.3-2b` solved `01_one_push` in ONE MOVE after TWO attempts,
and made four moves on `02_two_boxes`.** Under the old legend the same entrant made **zero moves in eighty
attempts** across the same two levels. **That contrast is the A/B's, measured properly and repeated 3/3.**

**AND THE OTHER THREE ENTRANTS MADE ZERO MOVES BETWEEN THEM** — `LFM2-350M-Extract`, `Qwen3.5-4B` and
`Qwen3.5-9B`, across five of the seven played cells, all on `not_an_action` (unreadable). **Five moves by one
entrant out of seven played cells is not a population result; it is one entrant's result inside a population
that otherwise could not act at all.**

## AND A RATE OVER ATTEMPTED CAN BE GAMED BY EXITING EARLY — A6 ONE TURN FURTHER OUT

> **COUNTS ARE THE RESULT. RATES ARE THE INDEX.**

**`not_an_action / attempted` is A6-compliant for the answer the ruling asked about, and it carries the same
defect one level up: an entrant that gives up after three commands has a denominator of three.** An early
exit can therefore *improve* a rate. **That is the same defect A6 removed from `planned`, arriving in the
other denominator — and the fix is the same: the quantity that cannot be improved by leaving is the one that
reports.**

**So the counts are printed beside the rates and are the load-bearing numbers.** `give_up` is 0 everywhere,
**which is itself informative and not an absence: no entrant resigned, because none of the failing entrants
realised there was a game to resign from.** That is the same fact as `not_an_action 40`, seen from the other
side — and it is only visible because `give_up` was split out of `unrecognised`.

## SCOPE

**Two levels, five entrants, one instrument history, n=1 per cell for the population run.** The A/B is
n=3 per arm and is the controlled evidence. **This is not a Sokoban score and it is not a population rate.**
The third level is **ABSENT** and is reported as absent: a level nobody can solve needs a solver to PROVE
it, and one that merely LOOKS lost is a trap for the reader rather than a control for the entrant.
