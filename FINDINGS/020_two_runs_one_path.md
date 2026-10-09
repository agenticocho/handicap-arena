# FINDING 020 — TWO RUNS, ONE ARTIFACT PATH, AND A RUNNING PROCESS DOES NOT RE-READ ITS MODULE

This is the load-bearing finding of the Sokoban work, and it was caught by a contradiction rather than by a
test: **the population run's behaviour did not match the prompt it was supposed to have used.**

---

## WHAT HAPPENED

```
12:44  commit 6be5bbb   sokoban_run.py created, carrying the OLD legend (key-value pairs, `FIRST LINE:`)
~12:45 FIRST RUN launched against probes/SOKOBAN_FIRST_RUN.json, ports 8751+
12:46  commit b6a8231   the legend FIXED -- symbols described in prose, pseudo-field labels removed
~12:47 SECOND RUN launched ("the re-run") against THE SAME PATH, THE SAME PORT RANGE
~12:47 I took a 2-cell snapshot of the first run's artifact and DELETED the live copy
~14:05 FIRST RUN completes all 10 cells and writes probes/SOKOBAN_FIRST_RUN.json LAST
       -> THE RE-RUN'S ARTIFACT IS GONE. The file on disk is the FIRST run's, written under the OLD legend.
```

**TWO DEFECTS, EACH SUFFICIENT TO DESTROY THE RESULT:**

**1. A RUNNING PROCESS DOES NOT RE-READ ITS MODULE.** The first run imported `sokoban_run` at ~12:45 and kept
that copy for its whole life. **Patching the file at 12:46 changed the NEXT process, not the running one.**
So the first run finished at 14:05 still sending the prompt I had already declared defective. **The fix was
committed ninety seconds after the process that needed it had started, and nothing anywhere said so.**

**2. TWO RUNS SHARED ONE ARTIFACT PATH, AND THE LAST WRITER WON.** Both wrote
`probes/SOKOBAN_FIRST_RUN.json` on every cell. The re-run finished first and its file was then overwritten
by the first run. **The only reason the re-run's numbers exist at all is that its STDOUT was redirected to a
different file.** A log is not a record format, and this result survived by luck.

**AND THE SECOND IS WHY I DELETED THE LIVE COPY AND THOUGHT I HAD SOLVED IT.** I removed the first run's
artifact so the re-run would write a fresh file — **which is exactly backwards: the FIRST RUN kept writing,
because it was still alive, and I had no handle on it.** *The protected copy was the one I had no control
over.*

## AND THE ERROR I MADE BECAUSE OF IT

**The re-run's log says `01_one_push: played 3, solved 1`. The artifact on disk says no cell is solved. I
compared them and concluded MY SUMMARY CODE HAD PRODUCED AN UNTRACEABLE NUMBER.**

**I was wrong, and the numbers were both right.** The log was the re-run's; the artifact was the first run's.
*They disagreed with each other because there were two of them.* **I filed a defect against my own arithmetic
that was really a defect in run identity — which is the worse error, because it was a false accusation that
would have hidden the real cause.** The unit error in the summary was real and separate; the untraceable
number was an artifact of comparing two runs.

## THE RULES

**THE IDENTITY OF A RUN IS NOT ITS PATH. IT IS THE INPUTS IT WAS PRODUCED UNDER.** A path is a location; two
runs at one location are one file. **What makes a record a record is that it names the instrument that
produced it** — and that is precisely what the A/B patch had to add: every cell now carries `legend` and
`legend_digest`. **Had that been there from the start, this contradiction would have been visible in ten
seconds instead of needing an A/B and a repeat test to find.**

```
a record must carry the digest of every frozen input it was produced under
a run must OWN its artifact path -- one run, one file, named for the run
launching a second run against a live path is not a retry, it is an OVERWRITE
```

**AND A COROLLARY THAT COST REAL WORK: A PATCH TO A RUNNING SYSTEM IS NOT IN EFFECT FOR THAT SYSTEM.** The
distinction between *the file now says X* and *the process is doing X* is the same one as *a reading with no
time* — **a running process is a snapshot of its own start, and its outputs must be read against the code as
it was AT START, not as it is now.** The prompt digest in the record is the mechanical fix: it makes the
question answerable from the artifact instead of from a timeline reconstruction.

## WHAT ACTUALLY SETTLED IT — AND WHY IT WASN'T A TEST

**No test was aimed at this.** It surfaced because the population result **contradicted the A/B**, and the
contradiction was too large to ignore: granite locked on `U` in the population run and varied to a solve in
the A/B's new arm. **The thing that made the contradiction visible was the CONTROL ON THE A/B ITSELF** — the
assertion, before any model loaded, that the two arms were provably different, with both digests printed.
**When the arms are provably different, a result that behaves like the other arm is a red flag rather than a
noise level.**

**AND THE REPEAT TEST TURNED THE CONTRADICTION INTO A MEASUREMENT:**

```
new legend   n=3   varied 3/3   solved 3/3      <- a mechanism, not a sample
old legend   n=3   varied 0/3   solved 0/3
```

**A single new-arm solve would have been a lucky sample and the finding would have had to be withdrawn. The
repeat is what makes the claim safe to make — and the rule that produced it is the same one that produced
the four-branch table: MEASURE THE SAMPLE BEFORE PUBLISHING THE RATE.**
