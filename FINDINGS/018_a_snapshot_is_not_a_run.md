# FINDING 018 — I ASTERISKED A RUNNING ARTIFACT, AND MY SUMMARY COUNTED CELLS WHERE IT SHOULD HAVE SUMMED

Both are my own, both are reporting defects rather than measurement defects, and both are the same shape as
everything else this week: **a second copy of the truth that disagreed with the first.**

---

## 1. THE PRESERVED "FIRST RUN" IS A 2-CELL SNAPSHOT OF A 10-CELL RUN

**When the re-run launched, the first run was STILL RUNNING.** I preserved `probes/SOKOBAN_FIRST_RUN.json` at
that moment, renamed it `..._INSTRUMENT_SUSPECT.json`, and REMOVED the live copy so the re-run would write a
fresh file. **That reasoning was right. The artifact I captured was not a run.**

```
preserved "first run"   2 played cells     <- a mid-flight snapshot, presented as a run
re-run                  7 played cells
CELLS IN BOTH           2                  <- the entire basis for the before/after comparison
```

**AND THE TWO CELLS IN BOTH ARE BOTH THE SAME ENTRANT** — so the only controlled comparison the whole
exercise supports is one entrant on two levels. **A SNAPSHOT OF AN IN-FLIGHT PROCESS PRESENTED AS A RUN IS A
READING WITH NO TIME**, which is the rule already filed: *a reading with no time is indistinguishable from a
live one.* **It applies to artifacts as much as to unit properties.**

**THE FIX, FOR NEXT TIME: asterisk a run by COPYING IT AFTER IT HAS EXITED, and record the exit state with
the copy.** A preserved artifact should carry the unit's terminal state, not the state of a process that was
still writing to it.

## 2. AND MY SUMMARY LINE COUNTED CELLS WHERE IT SHOULD HAVE SUMMED

**The run printed its own summary, and the summary disagreed with the record it summarised:**

```
printed   not_an_action  2      <- A COUNT OF CELLS WITH A NONZERO COUNTER
true                    80      <- THE SUM OF THE COUNTER
printed   solved         1      <- supported by NO ROW in the artifact
true                     0
```

**Two errors in one line. The first is a UNIT error — `sum(1 for r in sub if r['not_an_action'])` counts
ENTRIES, not VALUES**, and it was printed under a column name that reads as a total. *A count of entries is
not the sum of values*, the same axis as *a byte count is not a character count.* **The second is worse: a
number no row supports, which a reader would have quoted.**

**THE STRUCTURAL FIX, and it is the point: THE RUN NO LONGER PRINTS A VERDICT.** `sokoban_report.py` computes
the table **from the artifact at read time**, and prints the counter names next to the sums so the unit is
visible. **A summary accumulated during a run is a SECOND COPY of the truth, and every one of this week's
defects has been a second copy disagreeing with the first** — the card registry, the gate ratios, the hand
typed population, the slot namespace, the contract's own marker block.

**AND IT IS THE SAME SHAPE AS THE OTHER THREE CARRIERS:**

```
the shell       substituted a backtick       -> the commit message's content, decided by bash
the path        was overwritten by the next  -> the artifact's content, decided by the next run
git add -A      staged whatever was loose    -> the commit's content, decided by the tree
the summary     counted cells, not values    -> the report's content, decided by the run
```

**THE CONTENT OF A RECORD MUST NOT BE SUBJECT TO THE PROCESS THAT CARRIES IT.** Four carriers, one defect.
**The fix in every case is the same: DERIVE AT READ TIME, FROM THE THING ITSELF.**
