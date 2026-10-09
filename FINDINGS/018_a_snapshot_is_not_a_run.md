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

**The run printed its own summary, and one line of it was read against the wrong file:**

```
printed   not_an_action  2      <- A COUNT OF CELLS WITH A NONZERO COUNTER
true                    80      <- THE SUM OF THE COUNTER
printed   solved         1      <- supported by NO ROW in the artifact
true                     0
```

**THE UNIT ERROR IS REAL AND STANDS.** `sum(1 for r in sub if r['not_an_action'])` counts **ENTRIES**, not
**VALUES**, and it was printed under a column name that reads as a total. *A count of entries is not the sum
of values* — the same axis as *a byte count is not a character count.*

**BUT MY SECOND ACCUSATION WAS WRONG, AND THE WAY IT WAS WRONG IS THE MORE USEFUL FINDING.** I wrote that
`solved 1` was *"supported by NO ROW in the artifact"* and treated it as an untraceable number produced by a
defective summary. **It was traceable. It was the RE-RUN's number** — its `granite/01_one_push` cell reads
`ended=solved` — **and I read it against the FIRST RUN's artifact, which is a different run's record.**

```
logs/sokoban_rerun.out      summary says solved 1     <- TRUE of the re-run
probes/SOKOBAN_FIRST_RUN.json  no row is solved        <- TRUE of the first run
BOTH ARE CORRECT. THEY ARE DIFFERENT RUNS.
```

**SO THE DEFECT WAS NOT AN ARITHMETIC BUG. IT WAS THAT TWO RUNS SHARED ONE ARTIFACT PATH, AND I THEN
COMPARED ONE RUN'S LOG TO THE OTHER RUN'S RECORD AND CALLED THE DISAGREEMENT A COMPUTATION ERROR.** *The
numbers never disagreed with their own records. They disagreed with each other, because there were two.*

**WHICH MEANS MY FIX ADDRESSED THE LESSER HALF.** Deriving the report from the artifact at read time is
right **and does not help at all when two runs write the artifact.** The load-bearing repair is
**ONE RUN, ONE PATH** — see FINDING 020.

**THE STRUCTURAL FIX THAT DOES STAND: the run no longer prints a verdict.** `sokoban_report.py` computes the
table **from the artifact at read time**, with the counter names beside the sums so the unit is visible. **A
summary accumulated during a run is a SECOND COPY of the truth** — and every defect this week has been a
copy disagreeing with the thing it copied.
